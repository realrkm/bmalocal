from ._anvil_designer import VehicleInspectionChecklistTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class VehicleInspectionChecklist(VehicleInspectionChecklistTemplate):
    def __init__(self, jobcardid, **properties):
        # Set Form properties and Data Bindings.
        super().__init__(**properties)

        # Any code you write here will run before the form opens.

    def btn_Close_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.raise_event("x-close-alert", value=True)

    def chk_safety_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_safety.checked:
            self.chk_jack.checked = True
            self.chk_chock.checked = True
            self.chk_ppe.checked = True
            self.chk_valuables.checked = True
        else:
            self.chk_jack.checked = False
            self.chk_chock.checked = False
            self.chk_ppe.checked = False
            self.chk_valuables.checked = False

   
    def chk_complain_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_complain.checked:
            self.chk_test_drive.checked=True
            self.chk_scan.checked=True
            self.chk_mpesa.checked=True
        else:
            self.chk_test_drive.checked=False
            self.chk_scan.checked=False
            self.chk_mpesa.checked=False

    def chk_service_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_service.checked:
            self.chk_oil_level.checked=True
            self.chk_oil_filter.checked=True
            self.chk_air_filter.checked=True
            self.chk_coolant.checked=True
            self.chk_belt.checked=True
            self.chk_battery.checked=True
        else:
            self.chk_oil_level.checked=False
            self.chk_oil_filter.checked=False
            self.chk_air_filter.checked=False
            self.chk_coolant.checked=False
            self.chk_belt.checked=False
            self.chk_battery.checked=False

    def chk_carriage_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_carriage.checked:
            self.chk_front_arms.checked=True
            self.chk_rear_diff.checked=True
            self.chk_shocks.checked=True
            self.chk_exhaust.checked=True
            self.chk_shaft.checked=True
            self.chk_oil_leaks.checked=True
        else:
            self.chk_front_arms.checked=False
            self.chk_rear_diff.checked=False
            self.chk_shocks.checked=False
            self.chk_exhaust.checked=False
            self.chk_shaft.checked=False
            self.chk_oil_leaks.checked=False

    def chk_brakes_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_brakes.checked:
            self.chk_front_pads.checked=True
            self.chk_rear_pads.checked=True
            self.chk_brake_fluid.checked=True
            self.chk_tyre_pressure.checked=True
            
        else:
            self.chk_front_pads.checked=False
            self.chk_rear_pads.checked=False
            self.chk_brake_fluid.checked=False
            self.chk_tyre_pressure.checked=False

    def chk_final_change(self, **event_args):
        """This method is called when this checkbox is checked or unchecked"""
        if self.chk_final.checked:
            self.chk_torque.checked=True
            self.chk_road_test.checked=True
            self.chk_engine_clean.checked=True
            self.chk_old_parts.checked=True
            self.chk_invoice_explain.checked=True 
        else:
            self.chk_torque.checked=False
            self.chk_road_test.checked=False
            self.chk_engine_clean.checked=False
            self.chk_old_parts.checked=False
            self.chk_invoice_explain.checked=False

    def btn_Update_click(self, **event_args):
        """This method is called when the button is clicked"""
        pass  # Write Code Here
           
        
        
