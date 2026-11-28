import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import *
import anvil.js
from . import ModCache

# ************************************************* Error Handling Section *******************************

_notification_shown_at = {}  # title -> JS timestamp


def _call_silent(fn_name, *args):
    import anvil.server as _srv
    caller = getattr(_srv, "call_s", None) or _srv.call
    no_spinner = getattr(_srv, "no_loading_indicator", None)
    if no_spinner is not None:
        with no_spinner:
            return caller(fn_name, *args)
    return caller(fn_name, *args)


def getLocationAndSupplier(force_refresh=False):
    return ModCache.get_or_fetch(
        "locations_and_suppliers",
        lambda: _call_silent("getLocationAndSupplier"),
        topic="inventory",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getTechniciansCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "technicians_list",
        lambda: _call_silent("getTechnicians"),
        topic="contacts",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getStaffCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "staff_list",
        lambda: _call_silent("getStaff"),
        topic="contacts",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getInterimStaffCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "interim_staff",
        lambda: _call_silent("getInterimQuoteAndAmendedInvoiceStaff"),
        topic="contacts",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getRolesCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "roles_dropdown",
        lambda: _call_silent("getRoles"),
        topic="permissions",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getRolesListCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "roles_list",
        lambda: _call_silent("listRoles"),
        topic="permissions",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getRolesPermissionsHtmlCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "roles_permissions_html",
        lambda: _call_silent("get_roles_permissions_html"),
        topic="permissions",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getUsersCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "users_list",
        lambda: _call_silent("getUsers"),
        topic="users",
        ttl_seconds=180,
        force_refresh=force_refresh,
    )


def warmSettingsCaches(force_refresh=False):
    if not force_refresh and (
        ModCache.get_cached("roles_dropdown") is not None
        and ModCache.get_cached("users_list") is not None
    ):
        return
    bundle = _call_silent("get_settings_bootstrap")
    if not bundle:
        return
    if bundle.get("roles") is not None:
        ModCache.set_cached("roles_dropdown", bundle["roles"], topic="permissions", ttl_seconds=300)
    if bundle.get("roles_list") is not None:
        ModCache.set_cached("roles_list", bundle["roles_list"], topic="permissions", ttl_seconds=300)
    if bundle.get("roles_html") is not None:
        ModCache.set_cached("roles_permissions_html", bundle["roles_html"], topic="permissions", ttl_seconds=300)
    if bundle.get("users") is not None:
        ModCache.set_cached("users_list", bundle["users"], topic="users", ttl_seconds=180)


def peekClientReportCached():
    return ModCache.get_cached("report_clients")


def getClientReportCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "report_clients",
        lambda: _call_silent("getClientReport", None),
        topic="contacts",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getClientFullnameCached(force_refresh=False):
    if not force_refresh:
        clients = ModCache.get_cached("report_clients")
        if clients is not None:
            return clients
    return ModCache.get_or_fetch(
        "client_fullnames",
        lambda: _call_silent("getClientFullname"),
        topic="contacts",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def peekCarDetailsCached():
    return ModCache.get_cached("report_car_details")


def getCarDetailsCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "report_car_details",
        lambda: _call_silent("get_car_details", None),
        topic="jobcards",
        ttl_seconds=180,
        force_refresh=force_refresh,
    )


def peekTechnicianReportCached():
    return ModCache.get_cached("report_technicians")


def getTechnicianReportCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "report_technicians",
        lambda: _call_silent("getTechnicianReport", None),
        topic="contacts",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def peekAssignedJobcardsBootstrapCached():
    return ModCache.get_cached("report_assigned_jobcards")


def getAssignedJobcardsBootstrapCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "report_assigned_jobcards",
        lambda: _call_silent("get_assigned_jobcards_bootstrap"),
        topic="jobcards",
        ttl_seconds=180,
        force_refresh=force_refresh,
    )


def peekStaffReportCached():
    return ModCache.get_cached("report_staffs")


def getStaffReportCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "report_staffs",
        lambda: _call_silent("getStaffReport", None),
        topic="contacts",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def peekPriceCatalogueCached():
    return ModCache.get_cached("report_price_catalogue")


def getPriceCatalogueCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "report_price_catalogue",
        lambda: _call_silent("get_filtered_parts"),
        topic="inventory",
        ttl_seconds=180,
        force_refresh=force_refresh,
    )


def peekStockLocationCached():
    return ModCache.get_cached("report_stock_location")


def getStockLocationCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "report_stock_location",
        lambda: _call_silent("search_car_parts_location"),
        topic="inventory",
        ttl_seconds=180,
        force_refresh=force_refresh,
    )


def peekStockBalanceCached():
    return ModCache.get_cached("report_stock_balance")


def getStockBalanceCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "report_stock_balance",
        lambda: _call_silent("get_car_parts_summary", ""),
        topic="inventory",
        ttl_seconds=180,
        force_refresh=force_refresh,
    )


def peekQuoteInvoiceTotalsCached():
    return ModCache.get_cached("report_quote_invoice_totals")


def getQuoteInvoiceTotalsCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "report_quote_invoice_totals",
        lambda: _call_silent("get_jobcard_quote_invoice_totals"),
        topic="jobcards",
        ttl_seconds=180,
        force_refresh=force_refresh,
    )


def peekPaymentSummaryCached():
    return ModCache.get_cached("report_payment_summary")


def getPaymentSummaryCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "report_payment_summary",
        lambda: _call_silent("get_client_payment_summary"),
        topic="payments",
        ttl_seconds=180,
        force_refresh=force_refresh,
    )


def warmReportsCaches(permissions=None, force_refresh=False):
    """Warm initial report datasets in one atomic server bootstrap call."""
    perm_to_section = (
        ("Client Report", "clients", ("report_clients",)),
        ("Car Details Report", "car_details", ("report_car_details",)),
        ("Technicians Report", "technicians", ("report_technicians", "report_assigned_jobcards")),
        ("Staffs Report", "staffs", ("report_staffs",)),
        ("Inventory Report", "inventory", ("report_price_catalogue", "report_stock_location", "report_stock_balance")),
        ("Quote And Invoice Report", "quote_invoice", ("report_quote_invoice_totals",)),
        ("Payment Report", "payments", ("report_payment_summary",)),
    )
    subs = ((permissions or {}).get("REPORTS") or {}).get("subs") if permissions is not None else None
    requested_sections = []
    for perm_name, section_key, cache_keys in perm_to_section:
        if subs is not None and subs and not subs.get(perm_name):
            continue
        if not force_refresh and all(ModCache.get_cached(k) is not None for k in cache_keys):
            continue
        requested_sections.append(section_key)

    if not requested_sections:
        return

    bundle = _call_silent("get_reports_bootstrap", requested_sections)
    if not isinstance(bundle, dict):
        return
    if bundle.get("clients") is not None:
        ModCache.set_cached("report_clients", bundle["clients"], topic="contacts", ttl_seconds=300)
        ModCache.set_cached("client_fullnames", bundle["clients"], topic="contacts", ttl_seconds=300)
    if bundle.get("car_details") is not None:
        ModCache.set_cached("report_car_details", bundle["car_details"], topic="jobcards", ttl_seconds=180)
    if bundle.get("technicians_report") is not None:
        ModCache.set_cached("report_technicians", bundle["technicians_report"], topic="contacts", ttl_seconds=300)
    if bundle.get("assigned_jobcards") is not None:
        ModCache.set_cached("report_assigned_jobcards", bundle["assigned_jobcards"], topic="jobcards", ttl_seconds=180)
    if bundle.get("staffs_report") is not None:
        ModCache.set_cached("report_staffs", bundle["staffs_report"], topic="contacts", ttl_seconds=300)
    if bundle.get("price_catalogue") is not None:
        ModCache.set_cached("report_price_catalogue", bundle["price_catalogue"], topic="inventory", ttl_seconds=180)
    if bundle.get("stock_location") is not None:
        ModCache.set_cached("report_stock_location", bundle["stock_location"], topic="inventory", ttl_seconds=180)
    if bundle.get("stock_balance") is not None:
        ModCache.set_cached("report_stock_balance", bundle["stock_balance"], topic="inventory", ttl_seconds=180)
    if bundle.get("quote_invoice_totals") is not None:
        ModCache.set_cached("report_quote_invoice_totals", bundle["quote_invoice_totals"], topic="jobcards", ttl_seconds=180)
    if bundle.get("payment_summary") is not None:
        ModCache.set_cached("report_payment_summary", bundle["payment_summary"], topic="payments", ttl_seconds=180)

def _show_error(message, title="", timeout=5):
    """
    Displays an error notification and suppresses duplicates until it expires.
    
    :param message: The error message text.
    :param title:   Optional title prefix shown before the message.
    :param timeout: Seconds before another notification with this title is shown.
    """
    now = anvil.js.window.Date.now()
    last_shown = _notification_shown_at.get(title, 0)

    if (now - last_shown) < (timeout * 1000):
        return  # Still within timeout window, skip

    _notification_shown_at[title] = now

    Notification(
        message,
        title=title or None,
        style="danger",
        timeout=timeout,
    ).show()

    def clear_notification_lock():
        _notification_shown_at.pop(title, None)  # Reset the lock

    anvil.js.window.setTimeout(clear_notification_lock, timeout * 1000)


def handle_server_errors(exc):
    if isinstance(exc, anvil.server.UplinkDisconnectedError):
        _show_error(
            message="Connection via anvil uplink is lost. Please check your internet or try again later.",
            title="Disconnected"
        )
    elif isinstance(exc, anvil.server.SessionExpiredError):
        anvil.js.window.location.reload()
    elif isinstance(exc, anvil.server.AppOfflineError):
        _show_error(
            message="Please ensure the server is up and running.",
            title="Lost connection"
        )
    else:
        _show_error(
            message=f"{exc}",
            title="Issue Detected"
        )

#************************************************* Client Details Section *******************************
def getClientName(self):
    return anvil.server.call_s("getClientFullname")
      
def getClientNameWithID(valueID):
    return anvil.server.call_s("getClientNameWithID", valueID)
            
#************************************************* Job Card Details Section *******************************
def getJobCardRef(valueID):
    jobcardref_list = []
    for row in anvil.server.call_s("getJobCardRef", valueID):
        jobcardref_list.append((row["JobCardRef"], row))
    return jobcardref_list
               
def getJobCardInstructions(id):
    return anvil.server.call_s('getJobCardInstructions', id)

def getJobCardTechNotes(id):
    return anvil.server.call_s('getJobCardTechNotes', id)
    
#************************************************* Technician Section *******************************
def getTechnicianJobCards(status, regNo):
    return anvil.server.call_s('getTechnicianJobCards', status, regNo)
     
def getJobCardDefects(id):
    return anvil.server.call_s('getJobCardDefects', id)

def getJobCardPricedDefects(id):
    return anvil.server.call_s('getJobCardPricedDefects', id)
   
def getRequestedParts(id):
    return anvil.server.call_s('getRequestedParts', id)

def getAssignedTechnician(id):
    return anvil.server.call_s('getAssignedTechnician', id)
    
#************************************************* Car Parts Section *******************************
def getCarPartNames(force_refresh=False):
    return ModCache.get_or_fetch(
        "car_part_names",
        lambda: [(row['Name'], row) for row in anvil.server.call_s('getCarPartNames')],
        topic="inventory",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )

def getCarPartNumber(name):
    carpartnumber_list = []
    for row in anvil.server.call_s('getCarPartNumber', name):
        carpartnumber_list.append((row['PartNo'], row))
    return carpartnumber_list

#************************************************* Selling Price Tracking Section *******************************
_missing_price_ids = {}  # {part_id: manually_entered_price | None}

def trackMissingPrice(part_id):
    """Call this when getSellingPrice returns None for a part."""
    _missing_price_ids[part_id] = None

def recordManualPrice(part_id, price):
    """Call this when a user manually enters a price for a previously unpriced part."""
    if part_id in _missing_price_ids:
        _missing_price_ids[part_id] = float(price)

def insertMissingSellingPrice():
    """
    Fires a server update for every part that had no DB price but received
    a manual price from the user. Clears the tracker afterwards.
    """
    for part_id, price in _missing_price_ids.items():
        if price is not None:
            anvil.server.call_s('insertMissingSellingPrice', part_id, price)
    _missing_price_ids.clear()

def getSellingPrice(id):
    sellingPrice = anvil.server.call_s('getSellingPrice', id)
    if sellingPrice is None:
        trackMissingPrice(id)
        Notification("Sorry, please enter selling price to proceed.", title="Blank Field(s) Found", style="warning", timeout=3).show()
        return None
    else:
        return sellingPrice[0]
                        
#************************************************* Client Quotation Feedback Section *******************************
def getClientQuotationFeedback(JobCardID):
    return anvil.server.call_s('getClientQuotationFeedback', JobCardID)

def getQuotationConfirmationFeedback(JobCardID):
    return anvil.server.call_s('getQuotationConfirmationFeedback', JobCardID)