import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

def apply_sub_permissions(section_name, form, subsection_map, permissions):
    """Apply subsection permissions for a given section inside its form"""
    section_perms = permissions.get(section_name, {})
    subs = subsection_map.get(section_name, {})

    for sub_tag, sub_button in subs.items():
        allowed = section_perms.get("subs", {}).get(sub_tag, False)
        sub_button.visible = allowed
        sub_button.enabled = allowed
