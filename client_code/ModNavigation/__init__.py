import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import *

home_form = None

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
    from ..Revision import Revision
    form = get_form()
    form.load_component(Revision(permissions))
    
#Load Payment Form
def go_Payment():
    from ..Payment import Payment
    form = get_form()
    form.load_component(Payment())

#Load Inventory Form
def go_Inventory(permissions):
    from ..Inventory import Inventory
    form = get_form()
    form.load_component(Inventory(permissions))
    
  
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
    from ..Settings import Settings
    form = get_form()
    form.load_component(Settings(permissions))

#Load FAQs Form
def go_FAQs():
    from ..FAQ import FAQ
    form = get_form()
    form.load_component(FAQ())
    
