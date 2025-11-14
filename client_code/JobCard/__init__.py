from ._anvil_designer import JobCardTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from .. import ModGetData
import datetime
import anvil.js
from ..DownloadSignedJobCard import DownloadSignedJobCard

class JobCard(JobCardTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors) #Set global server error handler

        #Set focus into technician
        self.search_keyword_1.text_box_search.focus()

        # Attach the event that fetches technicians
        self.search_keyword_1.set_event_handler('x-get-search-keys', self.getTechnicianName)
        self.search_keyword_1.text_box_search.placeholder = "Search Technician's Name *"

        # Attach the event that fetches checked in by details
        self.search_keyword_4.set_event_handler('x-get-search-keys', self.getStaffDetails)
        self.search_keyword_4.text_box_search.placeholder = "Checked In By *"


    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)   
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)


    def getTechnicianName(self,  **event_args):
        """Return technician records to SearchKeyword."""
        results = anvil.server.call("getTechnicians")
        return [{'entry': r['Fullname'], 'ID': r['ID']} for r in results]

    def getStaffDetails(self,  **event_args):
        """Return customer records to SearchKeyword."""
        results = anvil.server.call('getStaff')
        return [{'entry': r['Staff'], 'ID': r['ID']} for r in results]

    def populateClientAndCarDetails(self, result, **event_args):
        """Do something when a result is selected from search hints."""
        jobcardID = result['ID']
        jobCardDetails = anvil.server.call_s('getJobCardRow', jobcardID)
        clientDetails = ModGetData.getClientNameWithID(jobCardDetails['ClientDetails'])

        #Populate client details
        self.txt_ClientName.text = clientDetails['Fullname']
        self.drop_down_selectCustomer.include_placeholder = False
        self.btn_SearchCustomer_click()
        self.drop_down_selectCustomer_change()
        
        
        #Populate car details
        self.chkComp.checked = jobCardDetails['Comprehensive']
        self.chkTPO.checked = jobCardDetails['ThirdParty']
        self.txtRegNo.text = jobCardDetails['RegNo']
        self.txtMakeAndModel.text= jobCardDetails['MakeAndModel']
        self.txtChassisNo.text= jobCardDetails['ChassisNo']
        self.txtEngineCC.text= jobCardDetails['EngineCC']
        self.txtEngineNo.text= jobCardDetails['EngineNo']
        self.txtEngineCode.text= jobCardDetails['EngineCode']
        self.txtPaintCode.text= jobCardDetails['PaintCode']
        self.chkAuto.checked = jobCardDetails['Auto']
        self.chkManual.checked = jobCardDetails['Manual']


    def getClientDetailsWithoutCarDetails(self, result, **event_args):
        """This method is called when an item is selected"""
        x = anvil.server.call('getClientNameWithID', result)
        self.txt_PhoneNo.text = x['Phone']
        self.txt_Address.text = x['Address']
        self.txt_Email.text = x['Email']

        #Resset car details
        self.chkComp.checked = 0
        self.chkTPO.checked = 0
        self.txtRegNo.text = ""
        self.txtMakeAndModel.text= ""
        self.txtChassisNo.text= ""
        self.txtEngineCC.text= ""
        self.txtEngineNo.text= ""
        self.txtEngineCode.text= ""
        self.txtPaintCode.text= ""
        self.chkAuto.checked = ""
        self.chkManual.checked = ""

    def chkComp_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        self.chkTPO.checked = 0

    def chkTPO_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        self.chkComp.checked = 0

    def chkManual_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        self.chkAuto.checked = 0

    def chkAuto_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        self.chkManual.checked = 0

    def chkEmpty_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        self.chkQuarter.checked = 0
        self.chkHalf.checked = 0
        self.chkThreeQuarter.checked = 0
        self.chkFull.checked = 0

    def chkQuarter_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        self.chkEmpty.checked = 0
        self.chkHalf.checked = 0
        self.chkThreeQuarter.checked = 0
        self.chkFull.checked = 0

    def chkHalf_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        self.chkEmpty.checked = 0
        self.chkQuarter.checked = 0
        self.chkThreeQuarter.checked = 0
        self.chkFull.checked = 0

    def chkThreeQuarter_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        self.chkEmpty.checked = 0
        self.chkQuarter.checked = 0
        self.chkHalf.checked = 0
        self.chkFull.checked = 0

    def chkFull_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        self.chkEmpty.checked = 0
        self.chkQuarter.checked = 0
        self.chkHalf.checked = 0
        self.chkThreeQuarter.checked = 0

    def txtRegNo_change(self, **event_args):
        """This method is called when the text in this text box is edited"""
        if self.txtRegNo.text and self.txtMileage.text:
            self.txt_JobCardRef.text = self.txtRegNo.text + "-" + str(self.txtMileage.text)

    def txtMileage_change(self, **event_args):
        """This method is called when the text in this text box is edited"""
        if self.txtRegNo.text and self.txtMileage.text:
            regNoCaps = self.txtRegNo.text
            regNoCaps = regNoCaps.upper()
            self.txt_JobCardRef.text = regNoCaps + "-" + str(self.txtMileage.text)

    def btn_SearchRegNo_click(self, **event_args):
        """This method is called when the button is clicked"""
        valueReg = self.txt_RegNo.text
        if valueReg is None:
            alert("Enter RegNo to proceed", title="Blank Field Found")
            return
        else:
            self.drop_down_selectRegNo.items = anvil.server.call("getCarRegistrationWithPartlyDetails", valueReg)

    def drop_down_selectRegNo_change(self, **event_args):
        """This method is called when an item is selected"""
        jobcardID = self.drop_down_selectRegNo.selected_value
        jobCardDetails = anvil.server.call_s('getJobCardRow', jobcardID)
        clientDetails = ModGetData.getClientNameWithID(jobCardDetails['ClientDetails'])
        
        #Populate client details
        self.txt_ClientName.text = clientDetails['Fullname']
        self.drop_down_selectCustomer.include_placeholder = False
        self.btn_SearchCustomer_click()
        self.drop_down_selectCustomer_change()
        

        #Populate car details
        self.chkComp.checked = jobCardDetails['Comprehensive']
        self.chkTPO.checked = jobCardDetails['ThirdParty']
        self.txtRegNo.text = jobCardDetails['RegNo']
        self.txtMakeAndModel.text= jobCardDetails['MakeAndModel']
        self.txtChassisNo.text= jobCardDetails['ChassisNo']
        self.txtEngineCC.text= jobCardDetails['EngineCC']
        self.txtEngineNo.text= jobCardDetails['EngineNo']
        self.txtEngineCode.text= jobCardDetails['EngineCode']
        self.txtPaintCode.text= jobCardDetails['PaintCode']
        self.chkAuto.checked = jobCardDetails['Auto']
        self.chkManual.checked = jobCardDetails['Manual']

    def btn_SignJobCard_click(self, **event_args):
        """This method is called when the button is clicked"""
        alert(content=DownloadSignedJobCard(), buttons=[], dismissible=False, large=True)

    def btn_SearchCustomer_click(self, **event_args):
        """This method is called when the button is clicked"""
        valueCustomer = self.txt_ClientName.text
        if valueCustomer is None:
            alert("Enter Customer's name to proceed", title="Blank Field Found")
            return
        else:
            result = anvil.server.call("getClientFullnameFromSearchWord", valueCustomer)
            self.drop_down_selectCustomer.items = result
            

    def drop_down_selectCustomer_change(self, **event_args):
        """This method is called when an item is selected"""
        self.getClientDetailsWithoutCarDetails(self.drop_down_selectCustomer.selected_value)

    def btn_Save_click(self, **event_args):

        """This method is called when the Save and New button is clicked""" 
        self.btn_Save.enabled = False #Disable button to prevent multiple clicks 

        if not self.search_keyword_1.text_box_search.text:
            alert("Sorry, please select a technician to assign the job card.", title="Blank Field(s) Found")
            self.search_keyword_1.text_box_search.focus()
            self.btn_Save.enabled = True
            return

        if not self.search_keyword_1.selected_result:
            alert("Please select an existing technician to proceed.", title="Select Option From List", large=False)
            self.search_keyword_1.text_box_search.focus()
            self.btn_Save.enabled = True
            return

        if not self.drop_down_selectCustomer.selected_value:
            alert("Sorry, please select the client's name.", title="Blank Field(s) Found")
            self.txt_ClientName.focus()
            self.btn_Save.enabled = True
            return

        if self.txtDueDate.date is None:
            alert("Sorry, please select due date to proceed.", title="Due Date Missing")
            self.txtDueDate.focus()
            self.btn_Save.enabled = True
            return

        if self.txtReceivedDate.date is None:
            alert("Sorry, please select received date to proceed.", title="Received Date Missing")
            self.txtReceivedDate.focus()
            self.btn_Save.enabled = True
            return

        if self.txtDueDate.date < self.txtReceivedDate.date:
            alert("Sorry, due date should be greater or equal to received date", title="Date Mismatch")
            self.txtDueDate.date = None
            self.txtDueDate.focus()
            self.btn_Save.enabled = True
            return

            # txtJobCard is derived from txtRegNo and txtMileage,
        if not self.txtRegNo.text or not self.txtMileage.text:
            alert("Sorry, please enter the registration number and mileage to get job card ref.", title="Blank Field(s) Found")
            self.txtRegNo.focus()
            self.btn_Save.enabled = True
            return
    
        if not self.txtReceivedDate.date: # Assuming this is an Anvil DatePicker component
            alert("Sorry, please enter received date.", title="Blank Field(s) Found")
            self.txtReceivedDate.focus()
            self.btn_Save.enabled = True
            return
    
        if not self.txtDueDate.date: # Assuming this is an Anvil DatePicker component
            alert("Sorry, please enter due date.", title="Blank Field(s) Found")
            self.txtDueDate.focus()
            self.btn_Save.enabled = True
            return
    
        if not self.search_keyword_4.text_box_search.text:
            alert("Sorry, please select checked in by to proceed.", title="Blank Field(s) Found")
            self.search_keyword_4.text_box_search.focus()
            self.btn_Save.enabled = True
            return

        if not self.search_keyword_4.selected_result:
            alert("Please select an existing staff to proceed.", title="Select Option From List", large=False)
            self.search_keyword_4.text_box_search.focus()
            self.btn_Save.enabled = True
            return
    
        if not self.chkComp.checked and not self.chkTPO.checked:
            alert("Sorry, please select insurance type, either comprehensive(Comp) or third party only(T.P.O).", title="Blank Field(s) Found")
            self.chkComp.focus() # Or self.chkTPO.focus()
            self.btn_Save.enabled = True
            return
    
        if not self.txtRegNo.text:
            alert("Sorry, please enter car registration number.", title="Blank Field(s) Found")
            self.txtRegNo.focus()
            self.btn_Save.enabled = True
            return
    
        if not self.txtMakeAndModel.text:
            alert("Sorry, please enter make and model.", title="Blank Field(s) Found")
            self.txtMakeAndModel.focus()
            self.btn_Save.enabled = True
            return
    
        if not self.txtMileage.text:
            alert("Sorry, please enter mileage.", title="Blank Field(s) Found")
            self.txtMileage.focus()
            self.btn_Save.enabled = True
            return
    
            # Check for transmission: either Manual or Auto must be selected
        if not self.chkManual.checked and not self.chkAuto.checked:
            alert("Sorry, please select one option for transmission.", title="Blank Field(s) Found")
            self.chkManual.focus()
            self.btn_Save.enabled = True
            return
    
            # Check for tank level: at least one option must be selected
        if not (self.chkEmpty.checked or self.chkQuarter.checked or self.chkHalf.checked or self.chkThreeQuarter.checked or self.chkFull.checked):
            alert("Sorry, please select one option for tank level.", title="Blank Field(s) Found")
            self.chkFull.focus() # Or any of the tank level checkboxes
            self.btn_Save.enabled = True
            return
    
        if not self.txtInstructions.text:
            alert("Sorry, please enter client's instructions.", title="Blank Field Found")
            self.txtInstructions.focus()
            self.btn_Save.enabled = True
            return
            
        if not self.cmbWorkflow.selected_value:
            alert("Sorry, please select workflow status to proceed.", title="Blank Field Found")
            self.cmbWorkflow.focus()
            self.btn_Save.enabled = True
            return
            
            # --- Duplicate Check (Server Call) ---
        job_card_ref = self.txt_JobCardRef.text # Assuming txtJobCard holds the reference
    
        # Call a server-side function to check for duplicates
        # This function should query database table (e.g., 'tbl_jobcarddetails')
        # and return True if a duplicate JobCardRef is found, False otherwise.

        is_duplicate = anvil.server.call_s('check_job_card_duplicate', job_card_ref)

        if is_duplicate:
            alert("Sorry, that job card reference number exists. Please enter another one.", title="Identical Number Found.")
            self.txt_JobCardRef.text = "" # Clear the job card field
            self.txtRegNo.text = ""
            self.txtMileage.text=""
            self.txtRegNo.focus() # Set focus to registration number 
            self.btn_Save.enabled = True
            return
        else:
            # --- Save Entries (Server Call) ---
            # Collect all data from the form into a dictionary

            technicianDetails = self.search_keyword_1.selected_result['ID']
            ClientDetails= self.drop_down_selectCustomer.selected_value
            JobCardRef= self.txt_JobCardRef.text
            ReceivedDate= self.txtReceivedDate.date
            DueDate= self.txtDueDate.date
            ExpDate= self.txtExpDate.date
            CheckedInBy= self.search_keyword_4.selected_result['ID']
            Comp= self.chkComp.checked                    
            Ins= True #Not in UI but required in tbl_jobcarddetails
            TPO= self.chkTPO.checked
            Spare= self.chkSpare.checked
            Jack= self.chkJack.checked
            Brace= self.chkBrace.checked
            RegNo= self.txtRegNo.text.upper()
            MakeAndModel= self.txtMakeAndModel.text
            ChassisNo= self.txtChassisNo.text
            EngineCC= self.txtEngineCC.text
            Mileage= self.txtMileage.text   
            EngineNo= self.txtEngineNo.text
            EngineCode= self.txtEngineCode.text
            Manual= self.chkManual.checked
            Auto= self.chkAuto.checked
            Empty= self.chkEmpty.checked
            Quarter= self.chkQuarter.checked
            Half= self.chkHalf.checked
            ThreeQuarter= self.chkThreeQuarter.checked
            Full= self.chkFull.checked
            PaintCode= self.txtPaintCode.text
            ClientInstruction= self.txtInstructions.text
            Notes= self.txtTechNotes.text
            IsComplete= False #Not in UI but exists in tbl_jobcarddetails 
            Status = self.cmbWorkflow.selected_value

            # Call a server-side function to save the data
            # This function should insert a new row into 'tbl_jobcarddetails' and 'tbl_pendingassignedjobs' tables

            anvil.server.call('save_job_card_details', technicianDetails, ClientDetails, JobCardRef, ReceivedDate, DueDate, ExpDate, CheckedInBy, Ins, Comp, TPO,
                              Spare, Jack, Brace, RegNo, MakeAndModel, ChassisNo, EngineCC, Mileage, EngineNo, EngineCode, Manual, Auto,
                              Empty, Quarter, Half, ThreeQuarter, Full, PaintCode, ClientInstruction, Notes, IsComplete, Status)


            alert("Job card details saved successfully", title="Success")

            # Clear form
            self.clear_form_fields()                     

    def clear_form_fields(self):
        """Helper function to clear all form fields after saving"""
        get_open_form().btn_JobCard_click()

    

    
   

   
    


    



    



    
    
