from ._anvil_designer import ItemTemplate1Template
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...TechnicianDefectsAndRequestedParts import TechnicianDefectsAndRequestedParts
from ...Quote import Quote
from ...ConfirmQuote import ConfirmQuote
from ...InServiceForm import InServiceForm
from ...VerifyTask import VerifyTask
from ...Invoice import Invoice

class ItemTemplate1(ItemTemplate1Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        left = self.item.get("left")
        middle = self.item.get("middle")
        right = self.item.get("right")
    
        if left:
            self.id.text=f"{left['id']}"
            self.label_make.text = f"Make: {left['make']}"
            self.label_owner.text = f"Job Card Ref: {left['jobcardref']}"
            self.label_plate.text = f"Plate: {left['plate']}"
            self.label_chassis.text = f"Chassis: {left['chassis']}"
            self.label_instruction.text = f"Instruction: {left['instruction']}"
            self.label_date.text = f"Due Date: {left['date'].strftime('%b %d, %Y')}"
            self.label_status.text = left['status']
            self.label_technician.text = left['technician']
            

                # Optional: Color code the status
            status = left['status']
            self.label_status.foreground = "#6AA84F"
            self.label_technician.foreground = "#6AA84F"
            
            if status == "Checked In":
                self.button_details.text = "TECHNICIAN REVIEW"
            elif status == "Create Quote":
                self.button_details.text = "CREATE QUOTE"
            elif status == "Confirm Quote":
                self.button_details.text = "CONFIRM QUOTE"                
            elif status == "In Service":
                self.button_details.text = "IN SERVICE"
            elif status == "Verify Task":
                self.button_details.text = "VERIFY TASK"
            elif status == "Issue Invoice":
                self.button_details.text = "ISSUE INVOICE"
            else:
                self.button_details.visible = False
        else:
            self.left_card_panel.visible = False

        if middle:
            self.id_1.text=f"{middle['id']}"
            self.label_make_1.text = f"Make: {middle['make']}"
            self.label_owner_1.text = f"Job Card Ref: {middle['jobcardref']}"
            self.label_plate_1.text = f"Plate: {middle['plate']}"
            self.label_chassis_1.text = f"Chassis: {middle['chassis']}"
            self.label_instruction_1.text = f"Instruction: {middle['instruction']}"
            self.label_date_1.text = f"Due Date: {middle['date'].strftime('%b %d, %Y')}"
            self.label_status_1.text = middle['status']
            self.label_technician_1.text = middle['technician']
            
                # Optional: Color code the status
            status = middle['status']
            self.label_status_1.foreground = "#6AA84F"
            self.label_technician_1.foreground = "#6AA84F"
            
            if status == "Checked In":
                self.button_details_1.text = "TECHNICIAN REVIEW"
            elif status == "Create Quote":
                self.button_details_1.text = "CREATE QUOTE"
            elif status == "Confirm Quote":
                self.button_details_1.text = "CONFIRM QUOTE"
            elif status == "In Service":
                self.button_details_1.text = "IN SERVICE"
            elif status == "Verify Task":
                self.button_details_1.text = "VERIFY TASK"               
            elif status == "Issue Invoice":
                self.button_details_1.text = "ISSUE INVOICE"
            else:
                self.button_details_1.visible = False

        else:
            self.middle_card_panel.visible = False
            
        if right:
            self.id_2.text=f"{right['id']}"
            self.label_make_2.text = f"Make: {right['make']}"
            self.label_owner_2.text = f"Job Card Ref: {right['jobcardref']}"
            self.label_plate_2.text = f"Plate: {right['plate']}"
            self.label_chassis_2.text = f"Chassis: {right['chassis']}"
            self.label_instruction_2.text = f"Instruction: {right['instruction']}"
            self.label_date_2.text = f"Due Date: {right['date'].strftime('%b %d, %Y')}"
            self.label_status_2.text = right['status']
            self.label_technician_2.text = right['technician']
            
                # Optional: Color code the status
            status = right['status']
            self.label_status_2.foreground = "#6AA84F"
            self.label_technician_2.foreground = "#6AA84F"
            
            if status == "Checked In":
                self.button_details_2.text = "TECHNICIAN REVIEW"
            elif status == "Create Quote":
                self.button_details_2.text = "CREATE QUOTE"
            elif status == "Confirm Quote":
                self.button_details_2.text = "CONFIRM QUOTE"
            elif status == "In Service":
                self.button_details_2.text = "IN SERVICE"
            elif status == "Verify Task":
                self.button_details_2.text = "VERIFY TASK"
            elif status == "Issue Invoice":
                self.button_details_2.text = "ISSUE INVOICE"
            else:
                self.button_details_2.visible = False
                
        else:
            self.right_card_panel.visible = False

    def button_details_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.button_details.enabled = False #Prevent multiple button clicks
        
        if self.button_details.text == "TECHNICIAN REVIEW":
            get_open_form().btn_Workflow_click() #Reload the page to prevent multiple button clicks in other card group
            alert(content=TechnicianDefectsAndRequestedParts(self.id.text), buttons=[], dismissible=False,large=True)
        elif self.button_details.text == "CREATE QUOTE":
            get_open_form().btn_Workflow_click()
            alert(content=Quote(self.id.text), buttons=[], dismissible=False,large=True)   
        elif self.button_details.text == "CONFIRM QUOTE":
            get_open_form().btn_Workflow_click()
            alert(content=ConfirmQuote(self.id.text), buttons=[], dismissible=False,large=True)  
        elif self.button_details.text == "IN SERVICE":
            get_open_form().btn_Workflow_click()
            alert(content=InServiceForm(self.id.text), buttons=[], dismissible=False,large=True)
        elif self.button_details.text == "VERIFY TASK":
            get_open_form().btn_Workflow_click()
            alert(content=VerifyTask(self.id.text), buttons=[], dismissible=False,large=True)
        elif self.button_details.text == "ISSUE INVOICE":
            get_open_form().btn_Workflow_click()
            alert(content=Invoice(self.id.text), buttons=[], dismissible=False,large=True)

    def button_details_1_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.button_details_1.enabled = False #Prevent multiple button clicks
        
        if self.button_details_1.text == "TECHNICIAN REVIEW":
            get_open_form().btn_Workflow_click() #Reload the page to prevent multiple button clicks in other card group
            alert(content=TechnicianDefectsAndRequestedParts(self.id_1.text), buttons=[], dismissible=False,large=True)
        elif self.button_details_1.text == "CREATE QUOTE":
            get_open_form().btn_Workflow_click()
            alert(content=Quote(self.id_1.text), buttons=[], dismissible=False,large=True)
        elif self.button_details_1.text == "CONFIRM QUOTE":
            get_open_form().btn_Workflow_click()
            alert(content=ConfirmQuote(self.id_1.text), buttons=[], dismissible=False,large=True)
        elif self.button_details_1.text == "IN SERVICE":
            get_open_form().btn_Workflow_click()
            alert(content=InServiceForm(self.id_1.text), buttons=[], dismissible=False,large=True)
        elif self.button_details_1.text == "VERIFY TASK":
            get_open_form().btn_Workflow_click()
            alert(content=VerifyTask(self.id_1.text), buttons=[], dismissible=False,large=True)
        elif self.button_details_1.text == "ISSUE INVOICE":
            get_open_form().btn_Workflow_click()
            alert(content=Invoice(self.id_1.text), buttons=[], dismissible=False,large=True)
        
        
    def button_details_2_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.button_details_2.enabled = False #Prevent multiple button clicks
        
        if self.button_details_2.text == "TECHNICIAN REVIEW":
            get_open_form().btn_Workflow_click() #Reload the page to prevent multiple button clicks in other card group
            alert(content=TechnicianDefectsAndRequestedParts(self.id_2.text), buttons=[], dismissible=False,large=True)
        elif self.button_details_2.text == "CREATE QUOTE":
            get_open_form().btn_Workflow_click()
            alert(content=Quote(self.id_2.text), buttons=[], dismissible=False,large=True)
        elif self.button_details_2.text == "CONFIRM QUOTE":
            get_open_form().btn_Workflow_click()
            alert(content=ConfirmQuote(self.id_2.text), buttons=[], dismissible=False,large=True)
        elif self.button_details_2.text == "IN SERVICE":
            get_open_form().btn_Workflow_click()
            alert(content=InServiceForm(self.id_2.text), buttons=[], dismissible=False,large=True)
        elif self.button_details_2.text == "VERIFY TASK":
            get_open_form().btn_Workflow_click()
            alert(content=VerifyTask(self.id_2.text), buttons=[], dismissible=False,large=True)
        elif self.button_details_2.text == "ISSUE INVOICE":
            get_open_form().btn_Workflow_click()
            alert(content=Invoice(self.id_2.text), buttons=[], dismissible=False,large=True)
