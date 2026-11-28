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


def getLocationAndSupplier(force_refresh=False):
    return ModCache.get_or_fetch(
        "locations_and_suppliers",
        lambda: anvil.server.call_s("getLocationAndSupplier"),
        topic="inventory",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getTechniciansCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "technicians_list",
        lambda: anvil.server.call_s("getTechnicians"),
        topic="contacts",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getStaffCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "staff_list",
        lambda: anvil.server.call_s("getStaff"),
        topic="contacts",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getInterimStaffCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "interim_staff",
        lambda: anvil.server.call_s("getInterimQuoteAndAmendedInvoiceStaff"),
        topic="contacts",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getRolesCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "roles_dropdown",
        lambda: anvil.server.call_s("getRoles"),
        topic="permissions",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getRolesListCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "roles_list",
        lambda: anvil.server.call_s("listRoles"),
        topic="permissions",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getRolesPermissionsHtmlCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "roles_permissions_html",
        lambda: anvil.server.call_s("get_roles_permissions_html"),
        topic="permissions",
        ttl_seconds=300,
        force_refresh=force_refresh,
    )


def getUsersCached(force_refresh=False):
    return ModCache.get_or_fetch(
        "users_list",
        lambda: anvil.server.call_s("getUsers"),
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
    bundle = anvil.server.call_s("get_settings_bootstrap")
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