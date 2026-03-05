import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import *
import anvil.js

# ************************************************* Error Handling Section *******************************

_active_notification = None  # Module-level lock — shared across all forms

def _show_notification(message, title="", style="danger", timeout=3):
    global _active_notification
    if _active_notification == title:
        return  # Already showing this notification, skip

    _active_notification = title

    notif = Notification(
        message,
        title=title,
        style=style,
        timeout=timeout,
    )
    notif.show()

    # Clear the lock after timeout using JavaScript's setTimeout
    # timeout is in seconds, setTimeout expects milliseconds
    def clear_notification():
        global _active_notification
        _active_notification = None

    anvil.js.window.setTimeout(clear_notification, timeout * 1000)


def handle_server_errors(exc):
    if isinstance(exc, anvil.server.UplinkDisconnectedError):
        _show_notification(
            message="Connection to server lost. Please check your internet or try again later.",
            title="Disconnected",
            style="danger"
        )
    elif isinstance(exc, anvil.server.SessionExpiredError):
        anvil.js.window.location.reload()
    elif isinstance(exc, anvil.server.AppOfflineError):
        _show_notification(
            message="Please connect to the internet to proceed.",
            title="No Internet",
            style="warning"
        )
    else:
        _show_notification(
            message=f"Unexpected error: {exc}",
            title="Error",
            style="danger"
        )

#************************************************* Client Details Section *******************************
def getClientName(self):
    name_list = []
    for row in anvil.server.call_s("getClientFullname"):
        name_list.append((row["Fullname"], row))
    return name_list # Continue using data
      
def getClientNameWithID(valueID):
    result =  anvil.server.call_s("getClientNameWithID", valueID)
    return result
            
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
def getCarPartNames():
    carpartname_list = []
    for row in anvil.server.call_s('getCarPartNames'):
        carpartname_list.append((row['Name'], row))
    return carpartname_list
        
    
def getCarPartNumber(name):
    carpartnumber_list = []
    for row in anvil.server.call_s('getCarPartNumber', name):
        carpartnumber_list.append((row['PartNo'], row))
    return carpartnumber_list

def getSellingPrice(id):
    sellingPrice = anvil.server.call_s('getSellingPrice', id)
    if sellingPrice is None:
        alert("Sorry, please enter selling price to proceed.", title="Blank Field(s) Found", large=False)
        return
    else:
        return sellingPrice[0]
                        
#************************************************* Client Quotation Feedback Section *******************************
def getClientQuotationFeedback(JobCardID):
    return anvil.server.call_s('getClientQuotationFeedback', JobCardID)

def getQuotationConfirmationFeedback(JobCardID):
    return anvil.server.call_s('getQuotationConfirmationFeedback', JobCardID)

