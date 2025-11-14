from ._anvil_designer import ReportTemplate
from ..QuoteForm import QuoteForm
from anvil import *
import anvil.server
import anvil.js
from ..ClientContactReport import ClientContactReport
from ..CarDetailsReport import CarDetailsReport
from ..StaffDetailsReport import StaffDetailsReport
from ..TechnicianJobCardDetails import TechnicianJobCardDetails
from ..InventoryReport import InventoryReport
from ..PeriodicQuoteVsInvoice import PeriodicQuoteVsInvoice
from ..PeriodicPayment import PeriodicPayment
from ..MonthlyPerformanceSchedule import MonthlyPerformanceSchedule
from .. import ModGetData

class Report(ReportTemplate):
    def __init__(self, permissions, **properties):
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        while anvil.users.get_user() is None:
            anvil.users.login_with_form()
        set_default_error_handling(self.handle_server_errors) #Set global server error handler

        self.card_panel.visible = False
        
        self.cmbReport.focus()

        # Attach the event that fetches searched values
        self.search_keyword_1.set_event_handler('x-get-search-keys', self.getValue)

        # Handle what happens when a user selects a result
        self.search_keyword_1.set_event_handler('x-search-hints-result', self.searchValue)

        #Load permissions
        self.permissions = permissions

        # Apply permissions to buttons and load the first available subform
        self.apply_permissions()

    def apply_permissions(self):
        """Apply only REPORT-related permissions and load the first available subform."""
        report_perms = self.permissions.get("REPORTS", {"main": False, "subs": {}})

        first_visible = None  # track which dropdown item to load first

        for subsection, value in report_perms["subs"].items():
            if subsection == "Client Report":
                if value and first_visible is None:
                    first_visible = "Clients"
                    self.add_item(first_visible)
                    first_visible = None #Reset to None to enable addition of other items in the dropdown

            elif subsection == "Car Details Report":
                if value and first_visible is None:
                    first_visible = "Car Details"
                    self.add_item(first_visible)
                    first_visible = None


            elif subsection == "Technicians Report":
                if value and first_visible is None:
                    first_visible = "Technicians"
                    self.add_item(first_visible)
                    first_visible = None

            elif subsection == "Staffs Report":
                if value and first_visible is None:
                    first_visible = "Staffs"
                    self.add_item(first_visible)
                    first_visible = None

            elif subsection == "Inventory Report":
                if value and first_visible is None:
                    first_visible = "Inventory"
                    self.add_item(first_visible)
                    first_visible = None

            elif subsection == "Quote And Invoice Report":
                if value and first_visible is None:
                    first_visible = "Periodic Quote And Invoice"
                    self.add_item(first_visible)
                    first_visible = None

            elif subsection == "Payment Report":
                if value and first_visible is None:
                    first_visible = "Periodic Payment Details"
                    self.add_item(first_visible)
                    first_visible = None

            elif subsection == "Monthly Schedule":
                if value and first_visible is None:
                    first_visible = "Monthly Performance Schedule"
                    self.add_item(first_visible)
                    first_visible = None


    def add_item(self, new_item):
        items = list(self.cmbReport.items or [])
        items.append(new_item)
        self.cmbReport.items = items

    def handle_server_errors(self, exc):
        if isinstance(exc, anvil.server.UplinkDisconnectedError):
            anvil.alert("Connection to server lost. Please check your internet or try again later.", title="Disconnected", large=False)
        elif isinstance(exc, anvil.server.SessionExpiredError):
            anvil.js.window.location.reload() #Reload the app on session timeout
        elif isinstance(exc, anvil.server.AppOfflineError):
            anvil.alert("Please connect to the internet to proceed.", title="No Internet", large=False)
        else:
            anvil.alert(f"Unexpected error: {exc}", title="Error", large=False)

    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def cmbReport_change(self, **event_args):
        """This method is called when an item is selected"""
        if self.cmbReport.selected_value == "Clients":
            self.search_keyword_1.text_box_search.visible = True
            self.search_keyword_1.repeating_panel_results.visible = True
            self.search_keyword_1.text_box_search.text=""
            self.search_keyword_1.text_box_search.placeholder = "Search Client's Name"
            self.search_keyword_1.text_box_search.focus()
            self.card_panel.clear()
            self.card_panel.add_component(ClientContactReport(None))
            self.card_panel.visible = True

        elif self.cmbReport.selected_value == "Car Details":
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            self.card_panel.clear()
            self.card_panel.add_component(CarDetailsReport())
            self.card_panel.visible = True
        
        elif self.cmbReport.selected_value == "Technicians":
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            self.card_panel.clear()
            self.card_panel.add_component(TechnicianJobCardDetails("Technician"))
            self.card_panel.visible = True

        elif self.cmbReport.selected_value == "Staffs":
            self.search_keyword_1.text_box_search.visible = True
            self.search_keyword_1.repeating_panel_results.visible = True
            self.search_keyword_1.text_box_search.text=""
            self.search_keyword_1.text_box_search.placeholder = "Search Staff's Name"
            self.search_keyword_1.text_box_search.focus()
            self.card_panel.clear()
            self.card_panel.add_component(StaffDetailsReport(None))
            self.card_panel.visible = True

        elif self.cmbReport.selected_value == "Inventory":
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            self.card_panel.clear()
            self.card_panel.add_component(InventoryReport("Catalogue"))
            self.card_panel.visible = True

        elif self.cmbReport.selected_value == "Periodic Quote And Invoice":
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            self.card_panel.clear()
            self.card_panel.add_component(PeriodicQuoteVsInvoice())
            self.card_panel.visible = True

        elif self.cmbReport.selected_value == "Periodic Payment Details":
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            self.card_panel.clear()
            self.card_panel.add_component(PeriodicPayment())
            self.card_panel.visible = True

        elif self.cmbReport.selected_value == "Monthly Performance Schedule":
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            self.card_panel.clear()
            self.card_panel.add_component(MonthlyPerformanceSchedule())
            self.card_panel.visible = True



    def getValue(self, **event_args):
        """This method is called when the text in this text box is edited"""
        selectedReport = self.cmbReport.selected_value 
       
        if selectedReport == "Clients":
            results = anvil.server.call("getClientFullname")
            return [{'entry': r['Fullname'], 'ID': r['ID']} for r in results]

            
        elif selectedReport =="Technicians":
            results = anvil.server.call("getTechnicians")
            return [{'entry': r['Fullname'], 'ID': r['ID']} for r in results]

        elif selectedReport =="Staffs":
            results = anvil.server.call("getStaff")
            return [{'entry': r['Staff'], 'ID': r['ID']} for r in results]

        else:
            pass

    def searchValue(self, result, **event_args):
        """Do something when a result is selected from search hints."""
        jobCardID = result['ID']
        
        if self.cmbReport.selected_value == "Clients":
            if jobCardID is None:
                alert("Client is not found. Enter correct name of the client", title="Missing Client Details", large=False)
                self.card_panel.clear()
                self.card_panel.visible = False
            else:
                self.card_panel.clear()
                self.card_panel.add_component(ClientContactReport(self.search_keyword_1.selected_result["ID"]))
                self.card_panel.visible = True

                
        elif self.cmbReport.selected_value == "Technicians":
            if jobCardID is None:
                alert("Technician is not found. Enter correct name of the technician", title="Missing Technician Details", large=False)
                self.card_panel.clear()
                self.card_panel.visible = False
            else:
                self.card_panel.clear()
                self.card_panel.add_component(TechnicianJobCardDetails())
                self.card_panel.visible = True

        elif self.cmbReport.selected_value == "Staffs":
            if jobCardID is None:
                alert("Staff is not found. Enter correct name of the staff", title="Missing Staff Details", large=False)
                self.card_panel.clear()
                self.card_panel.visible = False
            else:
                self.card_panel.clear()
                self.card_panel.add_component(StaffDetailsReport(self.search_keyword_1.selected_result["ID"]))
                self.card_panel.visible = True
                
       