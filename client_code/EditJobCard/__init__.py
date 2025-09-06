from ._anvil_designer import EditJobCardTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from .. import ModGetData
import datetime
import anvil.js

class EditJobCard(EditJobCardTemplate):
    def __init__(self, jobcard_data=None, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(
            self.handle_server_errors
        )  # Set global server error handler
        
        self.label_ID.text = jobcard_data["ID"] #Store Job Card ID, to be used when updating job card details
        
        self.populateForm(jobcard_data) #Populate Job Card data
        
        # Attach the event that fetches technicians
        self.search_keyword_1.set_event_handler(
            "x-get-search-keys", self.getTechnicianName
        )
        self.search_keyword_1.text_box_search.placeholder = "Search Technician's Name *"

        # Attach the event that fetches customer details
        self.search_keyword_3.set_event_handler(
            "x-get-search-keys", self.getCustomerDetails
        )
        self.search_keyword_3.text_box_search.placeholder = "Search Customer Name *"

        # Attach the event that fetches checked in by details
        self.search_keyword_4.set_event_handler(
            "x-get-search-keys", self.getStaffDetails
        )
        self.search_keyword_4.text_box_search.placeholder = "Checked In By *"

        # Handle what happens when a user selects a result
        self.search_keyword_3.set_event_handler(
            "x-search-hints-result", self.getClientDetailsWithoutCarDetails
        )
     

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert(
                "Connection to server lost. Please check your internet or try again later.",
                title="Disconnected",
                large=False,
            )
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload()  # Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert(
                "Please connect to the internet to proceed.",
                title="No Internet",
                large=False,
            )
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def populateForm(self, jobcard_data, **event_args):
        """This method is called when an item is selected"""  
        technician_name = anvil.server.call_s('getAssignedTechnician',jobcard_data["ID"])
        technician_details = anvil.server.call("getTechnicianDetailsFromName", technician_name)
        
        #Set technician
        self.search_keyword_1.set_result(
            {"entry": technician_details[0]["Fullname"], "ID": technician_details[0]["ID"]}
        )
        
        # Populate client details 
        clientDetails = ModGetData.getClientNameWithID(jobcard_data["ClientDetails"])
     
        self.search_keyword_3.set_result(
            {"entry": clientDetails["Fullname"], "ID": clientDetails["ID"]}
        )
        self.populateClientDetails(clientDetails)
        
        result = jobcard_data 
        self.txt_JobCardRef.text= result["JobCardRef"]
        self.txtDueDate.date = result["DueDate"]
        self.txtReceivedDate.date = result["ReceivedDate"]
        self.txtExpDate.date = result["ExpDate"]
        
        #Get staff details
        staff= anvil.server.call_s("get_staff_details", result["CheckedInBy"])
        if staff:
            self.search_keyword_4.set_result(
                {"entry": staff[0]["Fullname"], "ID": staff[0]["ID"]}
            )
     

        self.chkComp.checked= result["Comprehensive"]
        self.chkTPO.checked=result["ThirdParty"]
        self.chkSpare.checked=result["Spare"]
        self.chkJack.checked=result["Jack"]
        self.chkBrace.checked=result["Brace"]
        self.txtRegNo.text=result["RegNo"]
        self.txtMakeAndModel.text=result["MakeAndModel"]
        self.txtChassisNo.text=result["ChassisNo"]
        self.txtEngineCC.text=result["EngineCC"]
        self.txtMileage.text= result["Mileage"]
        self.txtEngineNo.text=result["EngineNo"]
        self.txtEngineCode.text=result["EngineCode"]
        self.txtPaintCode.text=result["PaintCode"]
        self.chkManual.checked=result["Manual"]
        self.chkAuto.checked=result["Auto"]
        self.chkEmpty.checked=result["Empty"]
        self.chkQuarter.checked=result["Quarter"]
        self.chkHalf.checked=result["Half"]
        self.chkThreeQuarter.checked=result["ThreeQuarter"]
        self.chkFull.checked=result["Full"]
        self.txtInstructions.text=result["ClientInstruction"]
        self.txtTechNotes.text=result["Notes"]

    def btn_Search_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        t=self.text_box_1.text
        results = anvil.server.call("getJobCardRefEditDetails")
        
        filtered_items = [item for item in results if t in item[0].lower()]  # item[0] is JobCardRef
        self.drop_down_1.items = filtered_items
    
        
    def getTechnicianName(self, **event_args):
        """Return technician records to SearchKeyword."""
        results = anvil.server.call("getTechnicians")
        return [{"entry": r["Fullname"], "ID": r["ID"]} for r in results]

    def getCarRegistrationNumbers(self, **event_args):
        """Return full registration records to SearchKeyword."""
        results = anvil.server.call("getCarRegistration")
        return [{"entry": r["RegNo"], "ID": r["ID"]} for r in results]

    def getCustomerDetails(self, **event_args):
        """Return customer records to SearchKeyword."""
        results = anvil.server.call("getClientFullname")
        return [{"entry": r["Fullname"], "ID": r["ID"]} for r in results]

    def getStaffDetails(self, **event_args):
        """Return customer records to SearchKeyword."""
        results = anvil.server.call("getStaff")
        return [{"entry": r["Staff"], "ID": r["ID"]} for r in results]

    def getJobCardRefDetails(self, result, **event_args):
        """Do something when a result is selected from search hints."""
        jobcardID = result["ID"]
        jobCardDetails = anvil.server.call_s("getJobCardRow", jobcardID)
        clientDetails = ModGetData.getClientNameWithID(jobCardDetails["ClientDetails"])

        # Populate client details
        self.search_keyword_3.set_result(
            {"entry": clientDetails["Fullname"], "ID": clientDetails["ID"]}
        )
        self.populateClientDetails(clientDetails)

        #Populate Job Card Info, Insurance Details And Available Items Details
        self.txt_JobCardRef.text = jobCardDetails["JobCardRef"]
        self.txtDueDate.date = jobCardDetails["DueDate"]
        self.txtReceivedDate.date = jobCardDetails["ReceivedDate"]
        self.txtExpDate.date = jobCardDetails["ExpDate"]

        # Populate check-in staff details
        checkinstaff = anvil.server.call_s('getStaffByID', jobCardDetails["CheckedInBy"])
        self.search_keyword_4.set_result(
            {"entry": checkinstaff[0]["Staff"], "ID": checkinstaff[0]["ID"]}
        )

        self.chkSpare.checked = jobCardDetails["Spare"]
        self.chkBrace.checked = jobCardDetails["Brace"]
        self.chkJack.checked =jobCardDetails["Jack"]
        
        # Populate car details
        self.chkComp.checked = jobCardDetails["Comprehensive"]
        self.chkTPO.checked = jobCardDetails["ThirdParty"]
        self.txtRegNo.text = jobCardDetails["RegNo"]
        self.txtMakeAndModel.text = jobCardDetails["MakeAndModel"]
        self.txtChassisNo.text = jobCardDetails["ChassisNo"]
        self.txtEngineCC.text = jobCardDetails["EngineCC"]
        self.txtEngineNo.text = jobCardDetails["EngineNo"]
        self.txtEngineCode.text = jobCardDetails["EngineCode"]
        self.txtPaintCode.text = jobCardDetails["PaintCode"]
        self.chkAuto.checked = jobCardDetails["Auto"]
        self.chkManual.checked = jobCardDetails["Manual"]

        self.chkEmpty.checked = jobCardDetails["Empty"]
        self.chkQuarter.checked= jobCardDetails["Quarter"]
        self.chkHalf.checked= jobCardDetails["Half"]
        self.chkThreeQuarter.checked= jobCardDetails["ThreeQuarter"]
        self.chkFull.checked= jobCardDetails["Full"]
        self.txtInstructions.text = jobCardDetails["ClientInstruction"]
        self.txtTechNotes.text = jobCardDetails["Notes"]
        self.cmbWorkflow.selected_value = jobCardDetails["Status"]

    def populateClientDetails(self, result, **event_args):
        """This method is called when an item is selected"""
        x = anvil.server.call("getClientNameWithID", result["ID"])
        self.txt_PhoneNo.text = x["Phone"]
        self.txt_Address.text = x["Address"]
        self.txt_Email.text = x["Email"]

    def getClientDetailsWithoutCarDetails(self, result, **event_args):
        """This method is called when an item is selected"""
        x = anvil.server.call("getClientNameWithID", result["ID"])
        self.txt_PhoneNo.text = x["Phone"]
        self.txt_Address.text = x["Address"]
        self.txt_Email.text = x["Email"]

        # Resset car details
        self.chkComp.checked = 0
        self.chkTPO.checked = 0
        self.txtRegNo.text = ""
        self.txtMakeAndModel.text = ""
        self.txtChassisNo.text = ""
        self.txtEngineCC.text = ""
        self.txtEngineNo.text = ""
        self.txtEngineCode.text = ""
        self.txtPaintCode.text = ""
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

    def btn_Update_click(self, **event_args):
        """This method is called when the Save and New button is clicked"""
        self.btn_Update.enabled = False  # Disable button to prevent multiple clicks

        if not self.search_keyword_1.text_box_search.text:
            alert(
                "Sorry, please select a technician to assign the job card.",
                title="Blank Field(s) Found",
            )
            self.search_keyword_1.text_box_search.focus()
            self.btn_Update.enabled = True
            return

        if not self.search_keyword_1.selected_result:
            alert(
                "Please select an existing technician to proceed.",
                title="Select Option From List",
                large=False,
            )
            self.search_keyword_1.text_box_search.focus()
            self.btn_Update.enabled = True
            return

        if not self.search_keyword_3.text_box_search.text:
            alert(
                "Sorry, please select the client's name.", title="Blank Field(s) Found"
            )
            self.search_keyword_3.text_box_search.focus()
            self.btn_Update.enabled = True
            return

        if not self.search_keyword_3.selected_result:
            alert(
                "Please select an existing customer to proceed.",
                title="Select Option From List",
                large=False,
            )
            self.search_keyword_3.text_box_search.focus()
            self.btn_Update.enabled = True
            return
            
        # txtJobCard is derived from txtRegNo and txtMileage,
        if not self.txtRegNo.text or not self.txtMileage.text:
            alert(
                "Sorry, please enter the registration number and mileage to get job card ref.",
                title="Blank Field(s) Found",
            )
            self.txtRegNo.focus()
            self.btn_Update.enabled = True
            return

        if self.txtDueDate.date is None:
            alert("Sorry, please select due date to proceed.", title="Due Date Missing")
            self.txtDueDate.focus()
            self.btn_Update.enabled = True
            return

        if self.txtReceivedDate.date is None:
            alert(
                "Sorry, please select received date to proceed.",
                title="Received Date Missing",
            )
            self.txtReceivedDate.focus()
            self.btn_Update.enabled = True
            return

        if self.txtDueDate.date < self.txtReceivedDate.date:
            alert(
                "Sorry, due date should be greater or equal to received date",
                title="Date Mismatch",
            )
            self.txtDueDate.date = None
            self.txtDueDate.focus()
            self.btn_Update.enabled = True
            return

        if (
            not self.txtReceivedDate.date
        ):  # Assuming this is an Anvil DatePicker component
            alert("Sorry, please enter received date.", title="Blank Field(s) Found")
            self.txtReceivedDate.focus()
            self.btn_Update.enabled = True
            return
            
        if not self.txtDueDate.date:  # Assuming this is an Anvil DatePicker component
            alert("Sorry, please enter due date.", title="Blank Field(s) Found")
            self.txtDueDate.focus()
            self.btn_Update.enabled = True
            return

        if not self.search_keyword_4.text_box_search.text:
            alert(
                "Sorry, please select checked in by to proceed.",
                title="Blank Field(s) Found",
            )
            self.search_keyword_4.text_box_search.focus()
            self.btn_Update.enabled = True
            return

        if not self.search_keyword_4.selected_result:
            alert(
                "Please select an existing staff to proceed.",
                title="Select Option From List",
                large=False,
            )
            self.search_keyword_4.text_box_search.focus()
            self.btn_Update.enabled = True
            return

        if not self.chkComp.checked and not self.chkTPO.checked:
            alert(
                "Sorry, please select insurance type, either comprehensive(Comp) or third party only(T.P.O).",
                title="Blank Field(s) Found",
            )
            self.chkComp.focus()  # Or self.chkTPO.focus()
            self.btn_Update.enabled = True
            return

        if not self.txtRegNo.text:
            alert(
                "Sorry, please enter car registration number.",
                title="Blank Field(s) Found",
            )
            self.txtRegNo.focus()
            self.btn_Update.enabled = True
            return

        if not self.txtMakeAndModel.text:
            alert("Sorry, please enter make and model.", title="Blank Field(s) Found")
            self.txtMakeAndModel.focus()
            self.btn_Update.enabled = True
            return

        if not self.txtMileage.text:
            alert("Sorry, please enter mileage.", title="Blank Field(s) Found")
            self.txtMileage.focus()
            self.btn_Update.enabled = True
            return

            # Check for transmission: either Manual or Auto must be selected
        if not self.chkManual.checked and not self.chkAuto.checked:
            alert(
                "Sorry, please select one option for transmission.",
                title="Blank Field(s) Found",
            )
            self.chkManual.focus()
            self.btn_Update.enabled = True
            return

            # Check for tank level: at least one option must be selected
        if not (
            self.chkEmpty.checked
            or self.chkQuarter.checked
            or self.chkHalf.checked
            or self.chkThreeQuarter.checked
            or self.chkFull.checked
        ):
            alert(
                "Sorry, please select one option for tank level.",
                title="Blank Field(s) Found",
            )
            self.chkFull.focus()  # Or any of the tank level checkboxes
            self.btn_Update.enabled = True
            return

        if not self.txtInstructions.text:
            alert(
                "Sorry, please enter client's instructions.", title="Blank Field Found"
            )
            self.txtInstructions.focus()
            self.btn_Update.enabled = True
            return


        # --- Update Entries (Server Call) ---
        jobcardID = self.label_ID.text
        technicianDetails = self.search_keyword_1.selected_result["ID"]
        ClientDetails = self.search_keyword_3.selected_result["ID"]
        JobCardRef = self.txt_JobCardRef.text
        ReceivedDate = self.txtReceivedDate.date
        DueDate = self.txtDueDate.date
        ExpDate = self.txtExpDate.date
        CheckedInBy = self.search_keyword_4.selected_result["ID"]
        Comp = self.chkComp.checked
        Ins = True  # Not in UI but required in tbl_jobcarddetails
        TPO = self.chkTPO.checked
        Spare = self.chkSpare.checked
        Jack = self.chkJack.checked
        Brace = self.chkBrace.checked
        MakeAndModel = self.txtMakeAndModel.text
        EngineCC = self.txtEngineCC.text
        Mileage = self.txtMileage.text
        EngineNo = self.txtEngineNo.text
        EngineCode = self.txtEngineCode.text
        Manual = self.chkManual.checked
        Auto = self.chkAuto.checked
        Empty = self.chkEmpty.checked
        Quarter = self.chkQuarter.checked
        Half = self.chkHalf.checked
        ThreeQuarter = self.chkThreeQuarter.checked
        Full = self.chkFull.checked
        PaintCode = self.txtPaintCode.text
        ClientInstruction = self.txtInstructions.text
        Notes = self.txtTechNotes.text
        
       
        
        # Call a server-side function to update the data
        # This function updates an existing row in 'tbl_jobcarddetails' and 'tbl_pendingassignedjobs' tables
        anvil.server.call("update_job_card_details",jobcardID, technicianDetails, ClientDetails, JobCardRef, ReceivedDate, DueDate, ExpDate,
                          CheckedInBy,Ins, Comp, TPO, Spare, Jack, Brace,MakeAndModel, EngineCC, Mileage, EngineNo, 
                          EngineCode,Manual,Auto, Empty, Quarter, Half,ThreeQuarter, Full,PaintCode,ClientInstruction, Notes)
        
        alert("Job card details updated successfully", title="Success")
        
        # Close form
        self.btn_Close_click()
        get_open_form().btn_Tracker_click()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value = True)

 



   
