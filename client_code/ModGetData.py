import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import *
import anvil.js

# ************************************************* Error Handling Section *******************************

_notification_shown_at = {}  # title -> JS timestamp

def _show_error(label, message, title="", timeout=5):
    """
    Displays an error message in a label and clears it after timeout seconds.
    
    :param label:   The Anvil Label component to display the message in.
    :param message: The error message text.
    :param title:   Optional title prefix shown before the message.
    :param timeout: Seconds before the label is cleared (default: 5).
    """
    now = anvil.js.window.Date.now()
    last_shown = _notification_shown_at.get(title, 0)

    if (now - last_shown) < (timeout * 1000):
        return  # Still within timeout window, skip

    _notification_shown_at[title] = now

    # Show message in label
    label.text = f"{title}: {message}" if title else message
    label.visible = True

    # Clear the label after timeout using JS setTimeout
    def clear_label():
        label.text = ""
        label.visible = False
        _notification_shown_at.pop(title, None)  # Reset the lock

    anvil.js.window.setTimeout(clear_label, timeout * 1000)


def handle_server_errors(exc, label):
    if isinstance(exc, anvil.server.UplinkDisconnectedError):
        _show_error(
            label=label,
            message="Connection via anvil uplink is lost. Please check your internet or try again later.",
            title="Disconnected"
        )
    elif isinstance(exc, anvil.server.SessionExpiredError):
        anvil.js.window.location.reload()
    elif isinstance(exc, anvil.server.AppOfflineError):
        _show_error(
            label=label,
            message="Please ensure the server is up and running.",
            title="Lost connection"
        )
    else:
        _show_error(
            label=label,
            message=f"Unexpected error: {exc}",
            title="Error"
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

