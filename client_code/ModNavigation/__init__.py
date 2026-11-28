import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import *

home_form = None
_revision_instance = None
_revision_perms_snapshot = None
_inventory_instance = None
_inventory_perms_snapshot = None
_settings_instance = None
_settings_perms_snapshot = None


def clear_cached_forms():
    global _revision_instance, _revision_perms_snapshot
    global _inventory_instance, _inventory_perms_snapshot
    global _settings_instance, _settings_perms_snapshot
    _revision_instance = None
    _revision_perms_snapshot = None
    _inventory_instance = None
    _inventory_perms_snapshot = None
    _settings_instance = None
    _settings_perms_snapshot = None


def prewarm_Revision(permissions):
    global _revision_instance, _revision_perms_snapshot
    rev_perms = (permissions or {}).get("REVISION")
    if _revision_instance is not None and _revision_perms_snapshot == rev_perms:
        return _revision_instance
    from ..Revision import Revision
    _revision_instance = Revision(permissions)
    _revision_perms_snapshot = rev_perms
    return _revision_instance


def prewarm_Inventory(permissions):
    global _inventory_instance, _inventory_perms_snapshot
    inv_perms = (permissions or {}).get("INVENTORY")
    if _inventory_instance is not None and _inventory_perms_snapshot == inv_perms:
        return _inventory_instance
    from ..Inventory import Inventory
    _inventory_instance = Inventory(permissions)
    _inventory_perms_snapshot = inv_perms
    return _inventory_instance


def prewarm_Settings(permissions):
    global _settings_instance, _settings_perms_snapshot
    set_perms = (permissions or {}).get("SETTINGS")
    if _settings_instance is not None and _settings_perms_snapshot == set_perms:
        return _settings_instance
    from ..Settings import Settings
    _settings_instance = Settings(permissions)
    _settings_perms_snapshot = set_perms
    return _settings_instance

def get_form():
    if home_form is None:
        raise Exception("You must set the home form first.")
    return home_form
    
# ******************************** Load Forms in Main Form ***************************

#Load Client Form
def go_Contact(permissions):
    from ..Contacts import Contacts
    form = get_form()
    form.load_component(Contacts(permissions))

#Load Job Card Form
def go_JobCard():
    from ..JobCard import JobCard
    form = get_form()
    form.load_component(JobCard())

#Load Booking Form
def go_Booking():
    from ..Booking import Booking
    form = get_form()
    form.load_component(Booking())
    
#Load Workflowt Form
def go_Workflow(permissions):
    from ..Workflow import Workflow
    form = get_form()
    form.load_component(Workflow(permissions))

#Load Progress Tracker Form
def go_Tracker():
    form = get_form()
    if anvil.js.window.innerWidth <= 768:
        # Mobile device
        from ..ProgressTrackerMobileView import ProgressTrackerMobileView
        form.load_component(ProgressTrackerMobileView())
    else:
        #Desktop device
        from ..ProgressTracker import ProgressTracker
        form.load_component(ProgressTracker())

#Load Revision Form
def go_Revision(permissions):
    form = get_form()
    rev_form = prewarm_Revision(permissions)
    form.load_component(rev_form)
    
#Load Payment Form
def go_Payment():
    from ..Payment import Payment
    form = get_form()
    form.load_component(Payment())

#Load Inventory Form
def go_Inventory(permissions):
    form = get_form()
    inv_form = prewarm_Inventory(permissions)
    form.load_component(inv_form)
    
  
#Load Report Form
def go_Report(permissions):
    from ..Report import Report
    form = get_form()
    form.load_component(Report(permissions))

#Load PartsHub Form
def go_PartsHub(permissions):
    from ..PartsHub import PartsHub
    form = get_form()
    form.load_component(PartsHub(permissions))

#Load Settings Form
def go_Settings(permissions):
    form = get_form()
    settings_form = prewarm_Settings(permissions)
    form.load_component(settings_form)

#Load FAQs Form
def go_FAQs():
    from ..FAQ import FAQ
    form = get_form()
    form.load_component(FAQ())
    
