import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import *

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
    print(f"The Id Is {id}")
    return anvil.server.call_s('getJobCardDefects', id)
        
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

