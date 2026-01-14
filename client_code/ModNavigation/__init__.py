import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import *
from ..Client import Client
from ..JobCard import JobCard
from ..Workflow import Workflow
from ..Payment import Payment
from ..Report import Report
from ..Settings import Settings
from ..Contacts import Contacts
from ..Revision import Revision
from ..ProgressTracker import ProgressTracker
from ..ProgressTrackerMobileView import ProgressTrackerMobileView
from ..Inventory import Inventory
from ..PartsHub import PartsHub
from ..Main import Main

home_form = None

def get_form():
    if home_form is None:
        raise Exception("You must set the home form first.")
    return home_form
    
# ******************************** Load Forms in Main Form ***************************

#Load Client Form
def go_Contact(permissions):
    form = get_form()
    form.load_component(Contacts(permissions))

#Load Job Card Form
def go_JobCard():
    form = get_form()
    form.load_component(JobCard())

#Load Workflowt Form
def go_Workflow(permissions):
    form = get_form()
    form.load_component(Workflow(permissions))

#Load Progress Tracker Form
def go_Tracker():
    form = get_form()
    if anvil.js.window.innerWidth <= 768:
        # Mobile device
        form.load_component(ProgressTrackerMobileView())
    else:
        #Desktop device
        form.load_component(ProgressTracker())

#Load Revision Form
def go_Revision(permissions):
    form = get_form()
    form.load_component(Revision(permissions))
    
#Load Payment Form
def go_Payment():
    form = get_form()
    form.load_component(Payment())

#Load Inventory Form
def go_Inventory(permissions):
    form = get_form()
    form.load_component(Inventory(permissions))
    
  
#Load Report Form
def go_Report(permissions):
    form = get_form()
    form.load_component(Report(permissions))

#Load PartsHub Form
def go_PartsHub(permissions):
    form = get_form()
    form.load_component(PartsHub(permissions))

#Load Settings Form
def go_Settings(permissions):
    form = get_form()
    form.load_component(Settings(permissions))

#************************************************* Notification Section *******************************
def showNotification(JobCardID, message):
    jobcard = anvil.server.call_s("getNotificationJobCardRef", JobCardID)

    n = Notification(f"{jobcard} {message}",style="success",timeout=None)

    def delayed_show():
        n.show()

    # Delay showing the notification by 10 seconds (10000 ms)
    anvil.js.window.setTimeout(delayed_show, 10000)

    return n