from ._anvil_designer import MonthlyPerformanceScheduleTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js


class MonthlyPerformanceSchedule(MonthlyPerformanceScheduleTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._rt_tokens = []
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)

    def _unsubscribe_realtime(self):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                for tok in self._rt_tokens:
                    rt.unsubscribe(tok)
        except Exception:
            pass
        self._rt_tokens = []

    def form_show(self, **event_args):
        self._unsubscribe_realtime()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_tokens = [
                    rt.subscribe("payments", self._on_data_changed),
                    rt.subscribe("jobcards", self._on_data_changed),
                ]
        except Exception:
            pass

    def form_hide(self, **event_args):
        self._unsubscribe_realtime()

    def _apply_invoice_bundle(self, bundle):
        if not isinstance(bundle, dict):
            return
        self.repeating_panel_1.items = bundle.get("invoices", [])
        result = bundle.get("summary")
        if result:
            self.lbl_ClientName.text = result["Fullname"]
            self.lbl_TotalInvoiceAmount.text = result["TotalInvoiceAmount"]
            self.lbl_TotalAmountPaid.text = result["TotalAmountPaid"]
            self.lbl_TotalDiscount.text = result["TotalDiscount"]
            self.lbl_PaymentBalance.text = result["Balance"]

    def _on_data_changed(self, evt=None):
        start_date = self.date_picker_start.date
        end_date = self.date_picker_end.date
        jobcardref_id = self.drop_down_1.selected_value
        if not (start_date and end_date and jobcardref_id):
            return
        with anvil.server.no_loading_indicator:
            bundle = anvil.server.call("get_periodic_invoices_with_summary", start_date, end_date, jobcardref_id)
            self._apply_invoice_bundle(bundle)

    def searchInvoices(self, **event_args):
        """This method is called when the button is clicked"""
        startDate = self.date_picker_start.date
        endDate = self.date_picker_end.date

        if startDate and endDate is None:
            pass
        elif startDate is None and endDate is None:
            Notification("Sorry, please enter date period to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            return
        elif startDate is None and endDate:
            Notification("Sorry, please enter start date to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            return
        elif startDate > endDate:
            Notification("Sorry, start date cannot be greater than end date", title="Mismatch Dates", style="warning", timeout=3).show()
            return
        else:
            self.drop_down_1.items = anvil.server.call("getMonthlyJobcardRef", startDate, endDate)

    def drop_down_1_change(self, **event_args):
        """This method is called when an item is selected"""
        startDate = self.date_picker_start.date
        endDate = self.date_picker_end.date
        jobcardrefID = self.drop_down_1.selected_value
        if not jobcardrefID:
            return

        if startDate is None and endDate is None:
            Notification("Sorry, please enter date period to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            return
        elif startDate is None and endDate:
            Notification("Sorry, please enter start date to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
            return
        elif startDate > endDate:
            Notification("Sorry, start date cannot be greater than end date", title="Mismatch Dates", style="warning", timeout=3).show()
            return
        else:
            bundle = anvil.server.call("get_periodic_invoices_with_summary", startDate, endDate, jobcardrefID)
            self._apply_invoice_bundle(bundle)

    def btn_SaveAndNew_click(self, **event_args):
        """Save all categorized schedule rows in a single atomic batch RPC."""
        self.btn_SaveAndNew.enabled = False
        try:
            startDate = self.date_picker_start.date
            endDate = self.date_picker_end.date
            jobcardrefID = self.drop_down_1.selected_value
            fullname = self.lbl_ClientName.text
            invoiceTotal = self.lbl_TotalInvoiceAmount.text
            totalPaid = self.lbl_TotalAmountPaid.text
            totalDiscount = self.lbl_TotalDiscount.text
            balance = self.lbl_PaymentBalance.text
            rows = self.repeating_panel_1.items or []

            if startDate is None and endDate is None:
                Notification("Sorry, please enter date period to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
                return
            elif startDate is None and endDate:
                Notification("Sorry, please enter start date to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
                return
            elif startDate > endDate:
                Notification("Sorry, start date cannot be greater than end date", title="Mismatch Dates", style="warning", timeout=3).show()
                return
            elif jobcardrefID is None:
                Notification("Sorry, please select the jobcard ref to proceed", title="Blank Field(s) Found", style="warning", timeout=3).show()
                return
            elif not rows:
                Notification("Sorry, ensure jobcard ref has parts or services associated with it", title="Missing Assigned Parts or Service", style="danger", timeout=3).show()
                return

            for i, row in enumerate(rows, start=1):
                category = row.get('Category', None)
                if not category or str(category).strip() == "":
                    item_name = row.get('Item', 'Unknown Item')
                    alert(f"Missing category for item #{i}: {item_name}", title="Missing Category")
                    return

            inv_numeric = float(str(invoiceTotal).replace(",", "") or 0)
            for r in rows:
                if r.get('Category') == "Prev Bal":
                    raw_string = str(r.get('Amount') or 0).replace(",", "")
                    inv_numeric -= int(float(raw_string))

            anvil.server.call(
                "save_monthly_schedule_batch",
                jobcardrefID,
                fullname,
                inv_numeric,
                totalPaid,
                totalDiscount,
                balance,
                list(rows),
            )

            Notification("Categorized invoice details saved successfully", title="Success", style="success", timeout=3).show()
            self.clearForm()
        finally:
            self.btn_SaveAndNew.enabled = True

    def clearForm(self, **event_args):
        self.date_picker_start.date = None
        self.date_picker_end.date = None
        self.drop_down_1.items = []
        self.lbl_ClientName.text = ""
        self.lbl_TotalInvoiceAmount.text = ""
        self.lbl_TotalAmountPaid.text = ""
        self.lbl_TotalDiscount.text = ""
        self.lbl_PaymentBalance.text = ""
        self.repeating_panel_1.items = []

    def btn_ViewSchedule_click(self, **event_args):
        from ..ViewSchedule import ViewSchedule
        alert(content=ViewSchedule(), buttons=[], dismissible=False, large=True)
        
       