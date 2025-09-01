import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

def apply_sub_permissions(section_name, form, subsection_map, permissions):
    """Apply subsection permissions for a given section inside its form"""
    section_perms = permissions.get(section_name, {"main": False, "subs": {}})
    subs = subsection_map.get(section_name, {})

    for sub_tag, sub_button in subs.items():
        allowed = section_perms["main"] or section_perms["subs"].get(sub_tag, False)
        sub_button.visible = allowed
        sub_button.enabled = allowed
        
def has_permission(permissions, section, subsection=None):
    """Check if user has permission for a section/subsection."""
    section_perms = permissions.get(section, {"main": False, "subs": {}})

    if section_perms["main"]:
        return True  # full section access

    if subsection:
        return section_perms["subs"].get(subsection, False)

    return False


def safe_load_subform(self, permissions, section, subsection, button_map, loader_fn_map):
    """
    Generic permission check before showing subform.
    
    Args:
        self: The form calling it
        permissions: dict of role permissions
        section: str (e.g. "CONTACT")
        subsection: str (e.g. "CLIENTS")
        button_map: dict mapping subsection keys -> button components
        loader_fn_map: dict mapping subsection keys -> loader functions
    """
    if not has_permission(permissions, section, subsection):
        anvil.alert(f"You do not have permission to access {subsection}.")
        return

    # Highlight button if it exists
    button = button_map.get(subsection)
    if button:
        # Call your highlight helper here
        self.highlight_active_button(button.text)

    # Clear the content area before loading
    self.card_2.clear()

    # Call loader function if exists
    loader_fn = loader_fn_map.get(subsection)
    if loader_fn:
        loader_fn()
