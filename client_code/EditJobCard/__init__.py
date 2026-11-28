from ._anvil_designer import EditJobCardTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
from .. import ModGetData
import datetime
import anvil.js

class EditJobCard(EditJobCardTemplate):
    def __init__(self, jobcard_data=None, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        self.label_ID.text = jobcard_data["ID"] #Store Job Card ID, to be used when updating job card details
        
        self.populateForm(jobcard_data) #Populate Job Card data
        
        # Attach the event that fetches technicians
        self.search_keyword_1.set_event_handler(
            "x-get-search-keys", self.getTechnicianName
        )
        self.search_keyword_1.text_box_search.placeholder = "Search Technician's Name *"

        # Attach the event that fetches checked in by details
        self.search_keyword_4.set_event_handler(
            "x-get-search-keys", self.getStaffDetails
        )
        self.search_keyword_4.text_box_search.placeholder = "Checked In By *"
        

    def _needs_hydration(self, jobcard_data):
        required_keys = (
            "AssignedTechnicianID",
            "AssignedTechnician",
            "ClientFullname",
            "ClientPhone",
            "ClientAddress",
            "ClientEmail",
            "CheckedInByName",
            "WorkDone",
        )
        return any(k not in jobcard_data for k in required_keys)

    def populateForm(self, jobcard_data, **event_args):
        """Populate EditJobCard using preloaded jobcard_data (0 RPCs) or a single bundled fetch."""
        result = jobcard_data or {}
        if self._needs_hydration(result) and result.get("ID"):
            hydrated = anvil.server.call_s("get_jobcard_form_data", result["ID"])
            if hydrated:
                result = hydrated

        # Set technician (with fallback to cached list if server worker hasn't restarted yet)
        tech_id = result.get("AssignedTechnicianID")
        tech_name = result.get("AssignedTechnician")
        if tech_id is None and tech_name and "AssignedTechnicianID" not in result:
            tech_id = next(
                (t["ID"] for t in ModGetData.getTechniciansCached() if t.get("Fullname") == tech_name),
                None,
            )
        if tech_id is not None and tech_name:
            self.search_keyword_1.set_result(
                {"entry": tech_name, "ID": tech_id}
            )

        # Populate client details without extra round-trips
        client_id = result.get("ClientDetails")
        if "ClientFullname" in result:
            client_name = result.get("ClientFullname") or ""
            client_phone = result.get("ClientPhone") or ""
            client_address = result.get("ClientAddress") or ""
            client_email = result.get("ClientEmail") or ""
        elif client_id is not None:
            legacy_client = ModGetData.getClientNameWithID(client_id) or {}
            client_name = legacy_client.get("Fullname") or ""
            client_phone = legacy_client.get("Phone") or ""
            client_address = legacy_client.get("Address") or ""
            client_email = legacy_client.get("Email") or ""
        else:
            client_name = client_phone = client_address = client_email = ""

        self.txt_ClientName.text = client_name
        self.drop_down_selectCustomer.include_placeholder = False
        if client_id is not None and client_name:
            self.drop_down_selectCustomer.items = [(client_name, client_id)]
            self.drop_down_selectCustomer.selected_value = client_id
        else:
            self.drop_down_selectCustomer.items = []
        self.txt_PhoneNo.text = client_phone
        self.txt_Address.text = client_address
        self.txt_Email.text = client_email

        self.txt_JobCardRef.text = result["JobCardRef"]
        self.txtDueDate.date = result["DueDate"]
        self.txtReceivedDate.date = result["ReceivedDate"]
        self.txtExpDate.date = result["ExpDate"]

        # Set checked-in-by staff
        staff_id = result.get("CheckedInBy")
        staff_name = result.get("CheckedInByName")
        if staff_id is not None and staff_name:
            self.search_keyword_4.set_result(
                {"entry": staff_name, "ID": staff_id}
            )

        self.chkComp.checked = result["Comprehensive"]
        self.chkTPO.checked = result["ThirdParty"]
        self.chkSpare.checked = result["Spare"]
        self.chkJack.checked = result["Jack"]
        self.chkBrace.checked = result["Brace"]
        self.text_area_other_items.text = result["OtherItems"]
        self.txtRegNo.text = result["RegNo"]
        self.txtMakeAndModel.text = result["MakeAndModel"]
        self.txtChassisNo.text = result["ChassisNo"]
        self.txtEngineCC.text = result["EngineCC"]
        self.txtMileage.text = result["Mileage"]
        self.txtEngineNo.text = result["EngineNo"]
        self.txtEngineCode.text = result["EngineCode"]
        self.txtPaintCode.text = result["PaintCode"]
        self.chkManual.checked = result["Manual"]
        self.chkAuto.checked = result["Auto"]
        self.chkEmpty.checked = result["Empty"]
        self.chkQuarter.checked = result["Quarter"]
        self.chkHalf.checked = result["Half"]
        self.chkThreeQuarter.checked = result["ThreeQuarter"]
        self.chkFull.checked = result["Full"]
        self.txtInstructions.text = result["ClientInstruction"]
        self.txtTechNotes.text = result["Notes"]
        self.text_area_work_done.text = result.get("WorkDone") or ""
        
    def btn_Search_click(self, **event_args):
        """This method is called when the text in this text box is edited"""
        t=self.text_box_1.text
        results = anvil.server.call("getJobCardRefEditDetails")
        
        filtered_items = [item for item in results if t in item[0].lower()]  # item[0] is JobCardRef
        self.drop_down_1.items = filtered_items
    
        
    def getTechnicianName(self, **event_args):
        """Return technician records to SearchKeyword."""
        results = ModGetData.getTechniciansCached()
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
        """Return staff records to SearchKeyword."""
        results = ModGetData.getStaffCached()
        return [{"entry": r["Staff"], "ID": r["ID"]} for r in results]

    
    def populateClientDetails(self, result, **event_args):
        """This method is called when an item is selected"""
        x = anvil.server.call("getClientNameWithID", result["ID"])
        self.txt_PhoneNo.text = x["Phone"]
        self.txt_Address.text = x["Address"]
        self.txt_Email.text = x["Email"]

    def btn_SearchCustomer_click(self, **event_args):
        """This method is called when the button is clicked"""
        valueCustomer = self.txt_ClientName.text
        if valueCustomer is None:
            Notification("Enter Customer's name to proceed", title="Blank Field Found", style="warning", timeout=3).show()
            return
        else:
            result = anvil.server.call("getClientFullnameFromSearchWord", valueCustomer)
            self.drop_down_selectCustomer.items = result
            

    def drop_down_selectCustomer_change(self, **event_args):
        """This method is called when an item is selected"""
        selected = self.drop_down_selectCustomer.selected_value
        if not selected:
            self.txt_PhoneNo.text = ""
            self.txt_Address.text = ""
            self.txt_Email.text = ""
            return
        self.getClientDetailsWithoutCarDetails(selected)
        
    def getClientDetailsWithoutCarDetails(self, result, **event_args):
        """This method is called when an item is selected"""
        x = anvil.server.call("getClientNameWithID", result)
        self.txt_PhoneNo.text = x["Phone"]
        self.txt_Address.text = x["Address"]
        self.txt_Email.text = x["Email"]


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

        if not self.drop_down_selectCustomer.selected_value:
            Notification("Sorry, please select the client's name.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txt_ClientName.focus()
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
            Notification("Sorry, please select due date to proceed.", title="Due Date Missing", style="danger", timeout=3).show()
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
            Notification("Sorry, please enter received date.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtReceivedDate.focus()
            self.btn_Update.enabled = True
            return
            
        if not self.txtDueDate.date:  # Assuming this is an Anvil DatePicker component
            Notification("Sorry, please enter due date.", title="Blank Field(s) Found", style="warning", timeout=3).show()
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

        if not self.txtChassisNo.text:
            Notification("Sorry, please enter Chassis No.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtChassisNo.focus()
            self.btn_Update.enabled = True
            return
            
        if not self.txtMakeAndModel.text:
            Notification("Sorry, please enter make and model.", title="Blank Field(s) Found", style="warning", timeout=3).show()
            self.txtMakeAndModel.focus()
            self.btn_Update.enabled = True
            return

        if not self.txtMileage.text:
            Notification("Sorry, please enter mileage.", title="Blank Field(s) Found", style="warning", timeout=3).show()
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
        ClientDetails= self.drop_down_selectCustomer.selected_value
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
        OtherItems = self.text_area_other_items.text
        RegNo = self.txtRegNo.text
        Chassis=self.txtChassisNo.text
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
        workDone = self.text_area_work_done.text
        
        # Call a server-side function to update the data
        # This function updates an existing row in 'tbl_jobcarddetails' and 'tbl_pendingassignedjobs' tables
        anvil.server.call("update_job_card_details",jobcardID, technicianDetails, ClientDetails, JobCardRef, ReceivedDate, DueDate, ExpDate,
                          CheckedInBy,Ins, Comp, TPO, Spare, Jack, Brace, OtherItems, RegNo, Chassis, MakeAndModel, EngineCC, Mileage, EngineNo, 
                          EngineCode,Manual,Auto, Empty, Quarter, Half,ThreeQuarter, Full,PaintCode,ClientInstruction, Notes, workDone)
        
        Notification("Job card details updated successfully", title="Success", style="success", timeout=3).show()
        
        # Close modal signalling an update occurred
        self.raise_event("x-close-alert", value="updated")

        form = get_open_form()
        progress_tracker = self.find_progress_tracker(form)
        if not progress_tracker:
            return

        # Save current dropdown value, refresh dropdown label (in case RegNo/Mileage changed), and refresh tracker once
        value = progress_tracker.drop_down_JobCardRefDetails.selected_value
        progress_tracker.btn_SearchCustomer_click()
        progress_tracker.drop_down_JobCardRefDetails.selected_value = value
        progress_tracker.drop_down_JobCardRefDetails_change()

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event('x-close-alert', value=False)

    def find_progress_tracker(self, component, level=0):
        # Step 1: Found ProgressTracker — return it directly
        if component.__class__.__name__ == "ProgressTracker" or component.__class__.__name__ == "ProgressTrackerMobileView":
            return component  # ← was returning dd (the dropdown) before
    
        # Step 2: Recurse into children
        if hasattr(component, "get_components"):
            for child in component.get_components():
                result = self.find_progress_tracker(child, level + 1)
                if result is not None:
                    return result

        return None
        
    
    
