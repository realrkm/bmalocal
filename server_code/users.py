from ._common import *

# *************************************************** Users Section ************************************


@anvil.server.callable()
def getUsers():
    _require_role("Administrator")
    with db_cursor() as cursor:
        rows = app_tables.users.search()
        result = []
        for i, row in enumerate(rows, start=1):

            def fmt_date(val):
                if val:
                    if (
                        hasattr(val, "tzinfo") and val.tzinfo
                    ):  # remove timezone if exists
                        val = val.replace(tzinfo=None)
                    return val.strftime("%Y-%m-%d %H:%M:%S")
                return None

            cursor.execute(
                "SELECT Roles FROM tbl_roles WHERE ID = %s", (row["role_id"],)
            )
            role = cursor.fetchone()

            result.append(
                {
                    "No": i,
                    "email": row["email"],
                    "last_login": fmt_date(row["last_login"]),
                    "signed_up": fmt_date(row["signed_up"]),
                    "role": role[0] if role else None,
                    "enabled": "Yes" if row["enabled"] else "No",
                    "loginattempts": row["n_password_failures"],
                }
            )
        return result


# *************************************************** Roles Section ************************************


@anvil.server.callable()
def listRoles():
    _get_current_user()
    with db_cursor() as cursor:
        query = "SELECT Roles, Description FROM tbl_roles ORDER BY Roles"
        cursor.execute(query)
        rows = cursor.fetchall()
        result = [{"Roles": row[0], "Description": row[1]} for row in rows]
        return result


@anvil.server.callable()
def duplicateRole(role, description):
    _get_current_user()
    with db_cursor() as cursor:
        # Check if a role with the same name already exists
        cursor.execute(
            "SELECT ID, Roles, Description FROM tbl_roles WHERE Roles = %s", (role,)
        )
        existing = cursor.fetchone()

        if existing:
            # Duplicate exists → don’t insert
            return {
                "status": "duplicate",
                "id": existing[0],
                "role": existing[1],
                "description": existing[2],
            }

        # If not found, insert new
        query = "INSERT INTO tbl_roles (Roles, Description) VALUES (%s, %s)"
        cursor.execute(query, (role, description))
        return {
            "status": "inserted",
            "id": cursor.lastrowid,
            "role": role,
            "description": description,
        }


@anvil.server.callable()
def getRoles():
    _get_current_user()
    with db_cursor() as cursor:
        query = "SELECT ID, Roles FROM tbl_roles ORDER BY Roles"
        cursor.execute(query)
        rows = cursor.fetchall()
        result = [(row[1], row[0]) for row in rows]
        return result


@anvil.server.callable()
def save_user_permissions(role_id, permissions_dict):
    _require_role("Administrator")
    global _ROLE_PERMS_CACHE
    _ROLE_PERMS_CACHE.pop(role_id, None)
    with db_cursor() as cursor:
        # Delete old permissions first
        cursor.execute("DELETE FROM tbl_userpermissions WHERE RoleID = %s", (role_id,))

        # Insert new permissions
        for section, data in permissions_dict.items():
            # Save main section permission
            cursor.execute(
                """
                INSERT INTO tbl_userpermissions (RoleID, Section, SubSection, Allowed)
                VALUES (%s, %s, %s, %s)
                """,
                (role_id, section, None, int(data["main"])),
            )

            # Save each sub permission
            for sub, allowed in data["subs"].items():
                cursor.execute(
                    """
                    INSERT INTO tbl_userpermissions (RoleID, Section, SubSection, Allowed)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (role_id, section, sub, int(allowed)),
                )


# *************************************************** Get User Permissions Section ************************************
_ROLE_PERMS_CACHE = {}

@anvil.server.callable()
def get_user_permissions(role_id):
    """Fetch role permissions, utilizing in-memory cache to eliminate repeated MySQL queries."""
    if role_id is None:
        return {}
    global _ROLE_PERMS_CACHE
    if role_id in _ROLE_PERMS_CACHE:
        return _ROLE_PERMS_CACHE[role_id]

    with db_cursor() as cursor:
        query = """
            SELECT Section, SubSection, Allowed
            FROM tbl_userpermissions
            WHERE RoleID = %s
        """
        cursor.execute(query, (role_id,))
        rows = cursor.fetchall()

        permissions = {}

        for section, subsection, allowed in rows:
            if section not in permissions:
                permissions[section] = {"main": False, "subs": {}}

            if subsection is None or subsection == "":
                # This is a main section permission
                permissions[section]["main"] = bool(allowed)
            else:
                # This is a sub-section permission
                permissions[section]["subs"][subsection] = bool(allowed)

        _ROLE_PERMS_CACHE[role_id] = permissions
        return permissions


@anvil.server.callable()
def get_user_session_context(role_id=None, *args, **kwargs):
    """Combined bootstrap endpoint returning authenticated user and permissions in a single round-trip."""
    user = anvil.users.get_user()
    if role_id is None and user:
        try:
            role_id = user["role_id"]
        except Exception:
            role_id = None

    permissions = get_user_permissions(role_id)
    is_technician = bool(permissions.get("TECHNICIAN PORTAL", {}).get("main", False))

    return {
        "user": user,
        "permissions": permissions,
        "is_technician": is_technician,
    }


# *************************************************** Edit User Account Section ************************************
@anvil.server.callable()
def get_account_roles():
    _get_current_user()
    with db_cursor() as cursor:
        query = "SELECT ID, Roles FROM tbl_roles ORDER BY Roles ASC"
        cursor.execute(query)
        rows = cursor.fetchall()

    # Return as list of tuples (label, value) for dropdown
    return [(row[1], row[0]) for row in rows]


@anvil.server.callable()
def get_role_id(role_name: str):
    _get_current_user()
    with db_cursor() as cursor:
        query = "SELECT ID FROM tbl_roles WHERE Roles = %s"
        cursor.execute(query, (role_name,))
        row = cursor.fetchone()

    return row[0] if row else None


@anvil.server.callable()
def getFailedAttempts(email):
    _get_current_user()
    user_row = app_tables.users.get(email=email)

    if user_row:
        # Safely return the value from the 'n_password_failures' column
        return user_row["n_password_failures"]
    else:
        # No user was found with that email
        return None


@anvil.server.callable()
def update_user(email, new_email, enabled, role_id):
    _require_role("Administrator")

    user = app_tables.users.get(email=email)
    if not user:
        raise Exception("Invalid request.")

    updates = {}
    if new_email is not None:
        updates["email"] = new_email
    if enabled is not None:
        updates["enabled"] = enabled
    if role_id is not None:
        updates["role_id"] = role_id

    # Reset login attempt counter on account edit
    updates["n_password_failures"] = None

    if updates:
        user.update(**updates)

    return "User updated successfully."


# *************************************************** Reset User Password Section ************************************
def hash_password(password, salt):
    """Hash a password with bcrypt. salt must be bytes from bcrypt.gensalt()."""
    if not isinstance(password, bytes):
        password = password.encode()
    # salt from bcrypt.gensalt() is already bytes; do NOT re-encode it
    if not isinstance(salt, bytes):
        raise TypeError("salt must be bytes produced by bcrypt.gensalt()")

    result = bcrypt.hashpw(password, salt)

    if isinstance(result, bytes):
        return result.decode("utf-8")


def _validate_password_strength(password: str):
    """Raise Exception if the password does not meet minimum policy requirements."""
    if len(password) < 8:
        raise Exception("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise Exception("Password must contain at least one uppercase letter.")
    if not re.search(r"[0-9]", password):
        raise Exception("Password must contain at least one digit.")


@anvil.server.callable()
def reset_password(email, new_password):
    """Reset a user's password. Requires Admin role."""
    _require_role("Administrator")

    # Validate strength before touching the DB
    _validate_password_strength(new_password)

    user = app_tables.users.get(email=email)
    # Use a generic message to avoid user-enumeration
    if not user:
        raise Exception("Invalid request.")

    user["password_hash"] = hash_password(new_password, bcrypt.gensalt())
    return "Password reset successfully."


# *************************************************** Get Roles And Permissions In HTML Format Section ************************************


@anvil.server.callable()
def get_roles_permissions_html():
    _get_current_user()
    html = """
    <style>
      body {
        font-family: "Mozilla Headline", Arial, Helvetica, sans-serif;
        font-size: 16px;
      }
      table {
        border-collapse: collapse;
        width: 100%;
        margin-top: 10px;
      }
      td {
        padding: 6px 12px;
        vertical-align: top;
        border: 1px solid #ccc;
      }
      tr:nth-child(even) {
        background-color: #f9f9f9;
      }
      .role {
        font-weight: 700;
        font-size: 18px;
        color: #2c3e50;
        background-color: #e6f0ff;
      }
      .section {
        font-weight: 600;
        color: #34495e;
        padding-left: 20px;
        background-color: #f2f6fc;
      }
      .subsection {
        color: #555;
        padding-left: 40px;
      }
      .allowed {
        padding-left: 60px;
        font-style: italic;
      }
    </style>
    <table>
    """

    sections_without_subs = {"JOB CARD", "TRACKER", "PAYMENT", "RESET", "TECHNICIAN PORTAL"}

    with db_cursor() as cursor:
        query = """
            SELECT 
                r.Roles,
                u.Section,
                u.SubSection,
                u.Allowed,
                CASE u.Section
                    WHEN 'CONTACT'   THEN 1
                    WHEN 'JOB CARD'  THEN 2
                    WHEN 'WORKFLOW'  THEN 3
                    WHEN 'TRACKER'   THEN 4
                    WHEN 'REVISION'  THEN 5
                    WHEN 'PAYMENT'   THEN 6
                    WHEN 'INVENTORY' THEN 7
                    WHEN 'REPORTS'   THEN 8
                    WHEN 'SETTINGS'  THEN 9
                    WHEN 'RESET'  THEN 10
                    ELSE 999
                END AS section_order
            FROM tbl_roles r
            JOIN tbl_userpermissions u
              ON r.ID = u.RoleID
            ORDER BY
                r.Roles,
                section_order,
                u.SubSection
        """
        cursor.execute(query)
        rows = cursor.fetchall()

    # Build HTML hierarchy
    current_role = None
    current_section = None

    for role, section, subsection, allowed, _ in rows:
        if role != current_role:
            html += f'<tr><td class="role" colspan="2">Role: {role}</td></tr>'
            current_role = role
            current_section = None

        if section != current_section:
            html += f'<tr><td class="section" colspan="2">{section}</td></tr>'
            current_section = section

        # Handle sections without subsections
        if section in sections_without_subs:
            if int(allowed) == 1:
                html += '<tr><td class="allowed">Allowed</td><td><span style="color:green;">&#10004;</span></td></tr>'
            else:
                html += '<tr><td class="allowed">Allowed</td><td><span style="color:red;">&#10008;</span></td></tr>'
        else:
            # Normal subsection logic
            if subsection and subsection != "None":
                html += f'<tr><td class="subsection">{subsection}</td>'
                if int(allowed) == 1:
                    html += '<td><span style="color:green;">&#10004;</span></td></tr>'
                else:
                    html += '<td><span style="color:red;">&#10008;</span></td></tr>'

    html += "</table>"
    return html

__all__ = [
    'getUsers',
    'listRoles',
    'duplicateRole',
    'getRoles',
    'save_user_permissions',
    '_ROLE_PERMS_CACHE',
    'get_user_permissions',
    'get_user_session_context',
    'get_account_roles',
    'get_role_id',
    'getFailedAttempts',
    'update_user',
    'hash_password',
    '_validate_password_strength',
    'reset_password',
    'get_roles_permissions_html',
]

from . import BMALocal as _compatibility_facade
