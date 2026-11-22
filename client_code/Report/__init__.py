from ._anvil_designer import ReportTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.js
from .. import ModGetData

class Report(ReportTemplate):
    def __init__(self, permissions, **properties):
        self.init_components(**properties)
        
        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        self.card_panel.visible = False
        
        self.cmbReport.focus()

        # Attach the event that fetches searched values
        self.search_keyword_1.set_event_handler('x-get-search-keys', self.getValue)

        # Handle what happens when a user selects a result
        self.search_keyword_1.set_event_handler('x-search-hints-result', self.searchValue)

        #Load permissions
        self.permissions = permissions
        self._report_load_seq = 0

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

            elif subsection == "Service History":
                if value and first_visible is None:
                    first_visible = "Service History"
                    self.add_item(first_visible)
                    first_visible = None


    def add_item(self, new_item):
        items = list(self.cmbReport.items or [])
        items.append(new_item)
        items.sort()  # Sort the items alphabetically
        self.cmbReport.items = items


    def refresh(self, **event_args):
        self.set_event_handler("x-refresh", self.refresh)

    def _mount_report(self, load_seq, expected_report, component):
        """Mount a report component only if it still matches the latest combobox selection."""
        if load_seq != self._report_load_seq or self.cmbReport.selected_value != expected_report:
            return
        self.card_panel.clear()
        self.card_panel.add_component(component, full_width_row=True)
        self.card_panel.visible = True

    def cmbReport_change(self, **event_args):
        """This method is called when an item is selected"""
        selected = self.cmbReport.selected_value
        self._report_load_seq += 1
        load_seq = self._report_load_seq

        self.card_panel.clear()
        if not selected:
            self.card_panel.visible = False
            return

        if selected == "Clients":
            from ..ClientContactReport import ClientContactReport
            self.search_keyword_1.text_box_search.visible = True
            self.search_keyword_1.repeating_panel_results.visible = True
            self.search_keyword_1.text_box_search.text = ""
            self.search_keyword_1.text_box_search.placeholder = "Search Client's Name"
            self.search_keyword_1.text_box_search.focus()
            comp = ClientContactReport(None)
            self._mount_report(load_seq, selected, comp)

        elif selected == "Car Details":
            from ..CarDetailsReport import CarDetailsReport
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            comp = CarDetailsReport()
            self._mount_report(load_seq, selected, comp)

        elif selected == "Technicians":
            from ..TechnicianJobCardDetails import TechnicianJobCardDetails
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            comp = TechnicianJobCardDetails("Technician")
            self._mount_report(load_seq, selected, comp)

        elif selected == "Staffs":
            from ..StaffDetailsReport import StaffDetailsReport
            self.search_keyword_1.text_box_search.visible = True
            self.search_keyword_1.repeating_panel_results.visible = True
            self.search_keyword_1.text_box_search.text = ""
            self.search_keyword_1.text_box_search.placeholder = "Search Staff's Name"
            self.search_keyword_1.text_box_search.focus()
            comp = StaffDetailsReport(None)
            self._mount_report(load_seq, selected, comp)

        elif selected == "Inventory":
            from ..InventoryReport import InventoryReport
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            comp = InventoryReport("Catalogue")
            self._mount_report(load_seq, selected, comp)

        elif selected == "Periodic Quote And Invoice":
            from ..PeriodicQuoteVsInvoice import PeriodicQuoteVsInvoice
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            comp = PeriodicQuoteVsInvoice()
            self._mount_report(load_seq, selected, comp)

        elif selected == "Periodic Payment Details":
            from ..PeriodicPayment import PeriodicPayment
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            comp = PeriodicPayment()
            self._mount_report(load_seq, selected, comp)

        elif selected == "Monthly Performance Schedule":
            from ..MonthlyPerformanceSchedule import MonthlyPerformanceSchedule
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            comp = MonthlyPerformanceSchedule()
            self._mount_report(load_seq, selected, comp)

        elif selected == "Service History":
            from ..ServiceHistory import ServiceHistory
            self.search_keyword_1.text_box_search.visible = False
            self.search_keyword_1.repeating_panel_results.visible = False
            comp = ServiceHistory()
            self._mount_report(load_seq, selected, comp)

    def getValue(self, **event_args):
        """This method is called when the text in this text box is edited"""
        selectedReport = self.cmbReport.selected_value 
       
        if selectedReport == "Clients":
            results = anvil.server.call("getClientFullname")
            return [{'entry': r['Fullname'], 'ID': r['ID']} for r in results]
       
        elif selectedReport =="Technicians":
            results = ModGetData.getTechniciansCached()
            return [{'entry': r['Fullname'], 'ID': r['ID']} for r in results]

        elif selectedReport =="Staffs":
            results = ModGetData.getStaffCached()
            return [{'entry': r['Staff'], 'ID': r['ID']} for r in results]

        else:
            pass

    def searchValue(self, result, **event_args):
        """Do something when a result is selected from search hints."""
        jobCardID = result['ID']
        selected = self.cmbReport.selected_value
        self._report_load_seq += 1
        load_seq = self._report_load_seq
        
        if selected == "Clients":
            if jobCardID is None:
                Notification("Client is not found. Enter correct name of the client", title="Missing Client Details", style="danger", timeout=3).show()
                self.card_panel.clear()
                self.card_panel.visible = False
            else:
                from ..ClientContactReport import ClientContactReport
                comp = ClientContactReport(self.search_keyword_1.selected_result["ID"])
                self._mount_report(load_seq, selected, comp)

        elif selected == "Technicians":
            if jobCardID is None:
                Notification("Technician is not found. Enter correct name of the technician", title="Missing Technician Details", style="danger", timeout=3).show()
                self.card_panel.clear()
                self.card_panel.visible = False
            else:
                from ..TechnicianJobCardDetails import TechnicianJobCardDetails
                comp = TechnicianJobCardDetails()
                self._mount_report(load_seq, selected, comp)

        elif selected == "Staffs":
            if jobCardID is None:
                Notification("Staff is not found. Enter correct name of the staff", title="Missing Staff Details", style="danger", timeout=3).show()
                self.card_panel.clear()
                self.card_panel.visible = False
            else:
                from ..StaffDetailsReport import StaffDetailsReport
                comp = StaffDetailsReport(self.search_keyword_1.selected_result["ID"])
                self._mount_report(load_seq, selected, comp)
                
       