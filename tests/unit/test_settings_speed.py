import importlib
import sys
import types
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import server_code.BMALocal as bma
from server_code import _common, users


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def test_get_settings_bootstrap_and_batch_save_permissions():
    _common.invalidate_lookup_cache()
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [(1, "Administrator"), (2, "Staff")],         # getRoles
        [("Administrator", "Full"), ("Staff", "Ops")], # listRoles
        [("Administrator", "SETTINGS", "User Accounts", 1, 9)],  # get_roles_permissions_html
    ]
    fake_user_row = {
        "email": "admin@bma.local",
        "last_login": None,
        "signed_up": None,
        "role_id": 1,
        "enabled": True,
        "n_password_failures": 0,
    }
    mock_app_tables = MagicMock()
    mock_app_tables.users.search.return_value = [fake_user_row]

    with patch.object(users, "_get_current_user", return_value={"role_id": 1}), \
         patch.object(users, "app_tables", mock_app_tables), \
         patch.object(users, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        bundle = bma.get_settings_bootstrap()

    assert bundle["roles"] == [("Administrator", 1), ("Staff", 2)]
    assert len(bundle["roles_list"]) == 2
    assert "Role: Administrator" in bundle["roles_html"]
    assert bundle["users"][0]["email"] == "admin@bma.local"
    assert bundle["users"][0]["role_id"] == 1
    assert bundle["users"][0]["role"] == "Administrator"

    # Unauthenticated call rejected
    with patch.object(users, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.get_settings_bootstrap()

    # save_user_permissions uses single executemany instead of N+1 execute loop
    save_cursor = MagicMock()
    perms = {
        "SETTINGS": {"main": True, "subs": {"User Accounts": True, "Roles And Permissions": False}},
        "JOB CARD": {"main": True, "subs": {}},
    }
    with patch.object(users, "_require_role"), \
         patch.object(users, "publish_realtime_event") as pub_mock, \
         patch.object(users, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = save_cursor
        bma.save_user_permissions(1, perms)

    save_cursor.execute.assert_called_once_with(
        "DELETE FROM tbl_userpermissions WHERE RoleID = %s", (1,)
    )
    save_cursor.executemany.assert_called_once()
    assert len(save_cursor.executemany.call_args.args[1]) == 4
    pub_mock.assert_called_once_with("permissions", "updated", entity_id=1)
    _common.invalidate_lookup_cache()


def test_settings_caches_and_prewarms_both_subforms_for_instant_switching(monkeypatch):
    class FakeButton:
        def __init__(self, text):
            self.text = text
            self.visible = False
            self.enabled = False
            self.background = "#0056D6"
            self.foreground = "white"

    ua_cls = MagicMock(side_effect=lambda: SimpleNamespace(name="ua", refresh_users=MagicMock()))
    rp_cls = MagicMock(side_effect=lambda: SimpleNamespace(name="rp", refresh_roles=MagicMock()))

    anvil = _module("anvil", Button=FakeButton)
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server", call=MagicMock(), call_s=MagicMock(), no_loading_indicator=nullcontext())
    anvil_users = _module("anvil.users")
    timeouts = []
    anvil_js = _module(
        "anvil.js",
        call=MagicMock(),
        get_dom_node=MagicMock(return_value=SimpleNamespace(addEventListener=MagicMock())),
        window=SimpleNamespace(setTimeout=lambda fn, _ms=0: timeouts.append(fn), bmaRealtime=None),
    )
    anvil.tables = anvil_tables
    anvil.server = anvil_server
    anvil.users = anvil_users
    anvil.js = anvil_js

    stubs = {
        "anvil": anvil,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.server": anvil_server,
        "anvil.users": anvil_users,
        "anvil.js": anvil_js,
        "client_code.UserAccounts": _module("client_code.UserAccounts", UserAccounts=ua_cls),
        "client_code.UserRolesAndPermissions": _module("client_code.UserRolesAndPermissions", UserRolesAndPermissions=rp_cls),
        "client_code.Settings._anvil_designer": _module(
            "client_code.Settings._anvil_designer",
            SettingsTemplate=type("SettingsTemplate", (), {}),
        ),
    }

    target = "client_code.Settings"
    monkeypatch.delitem(sys.modules, target, raising=False)
    for name, m in stubs.items():
        monkeypatch.setitem(sys.modules, name, m)

    mod = importlib.import_module(target)
    try:
        cls = mod.Settings
        b_ua = FakeButton("USER ACCOUNT")
        b_rp = FakeButton("ROLES AND PERMISSIONS")
        mounted = []

        form = SimpleNamespace(
            permissions={
                "SETTINGS": {
                    "main": True,
                    "subs": {
                        "User Accounts": True,
                        "Roles And Permissions": True,
                    },
                }
            },
            _initial_subform_loaded=False,
            _first_visible=None,
            _authorized_keys=[],
            _subforms={},
            _active_key=None,
            _rt_tokens=[],
            btn_AddUser=b_ua,
            btn_UserRoles=b_rp,
            card_1=SimpleNamespace(get_components=lambda: [b_ua, b_rp]),
            card_2=SimpleNamespace(
                visible=True,
                clear=lambda: mounted.clear(),
                add_component=lambda c, **_kw: mounted.append(c),
                get_components=lambda: list(mounted),
            ),
        )
        form._build_subform = lambda k: cls._build_subform(form, k)
        form._get_or_create_subform = lambda k: cls._get_or_create_subform(form, k)
        form._prewarm_single_subform = lambda k: cls._prewarm_single_subform(form, k)
        form._schedule_prewarm_subforms = lambda: cls._schedule_prewarm_subforms(form)
        form._unsubscribe_realtime = lambda: cls._unsubscribe_realtime(form)
        form._activate_subform = lambda k, b: cls._activate_subform(form, k, b)
        form.highlight_active_button = lambda t: cls.highlight_active_button(form, t)
        form.show_clicked_button = lambda n: cls.show_clicked_button(form, n)
        form.btn_AddUser_click = lambda: cls.btn_AddUser_click(form)
        form.btn_UserRoles_click = lambda: cls.btn_UserRoles_click(form)

        cls.apply_permissions(form)
        cls.form_show(form)

        while timeouts:
            timeouts.pop(0)()

        assert ua_cls.call_count == 1
        assert rp_cls.call_count == 1
        assert len(form._subforms) == 2

        # Switching back and forth reuses pre-built subforms with ZERO new instantiations!
        cls.btn_UserRoles_click(form)
        assert mounted[-1].name == "rp"
        cls.btn_AddUser_click(form)
        assert mounted[-1].name == "ua"
        assert ua_cls.call_count == 1
        assert rp_cls.call_count == 1
    finally:
        sys.modules.pop(target, None)


def test_edit_user_accounts_opens_with_zero_server_calls(monkeypatch):
    server_call = MagicMock()
    server_call_s = MagicMock()
    mod_get_data = _module(
        "client_code.ModGetData",
        getRolesCached=MagicMock(return_value=[("Administrator", 1), ("Staff", 2)]),
    )
    anvil = _module("anvil", Notification=MagicMock(), alert=MagicMock())
    anvil.__path__ = []
    anvil_tables = _module("anvil.tables", app_tables=MagicMock())
    anvil_tables.__path__ = []
    anvil_server = _module("anvil.server", call=server_call, call_s=server_call_s)
    anvil_users = _module("anvil.users")
    anvil_js = _module("anvil.js", call=MagicMock())
    anvil.tables = anvil_tables
    anvil.server = anvil_server
    anvil.users = anvil_users
    anvil.js = anvil_js

    stubs = {
        "anvil": anvil,
        "anvil.tables": anvil_tables,
        "anvil.tables.query": _module("anvil.tables.query"),
        "anvil.server": anvil_server,
        "anvil.users": anvil_users,
        "anvil.js": anvil_js,
        "client_code.ModGetData": mod_get_data,
        "client_code.EditUserAccounts._anvil_designer": _module(
            "client_code.EditUserAccounts._anvil_designer",
            EditUserAccountsTemplate=type("EditUserAccountsTemplate", (), {"init_components": lambda self, **_p: None}),
        ),
    }

    target = "client_code.EditUserAccounts"
    monkeypatch.delitem(sys.modules, target, raising=False)
    for name, m in stubs.items():
        monkeypatch.setitem(sys.modules, name, m)

    mod = importlib.import_module(target)
    try:
        cls = mod.EditUserAccounts
        inst = object.__new__(cls)
        inst.drop_down_role = SimpleNamespace(items=[], selected_value=None)
        inst.label_oldemail = SimpleNamespace(text="")
        inst.txt_email = SimpleNamespace(text="")
        inst.drop_down_active = SimpleNamespace(selected_value=None)
        inst.text_box_login_attempts = SimpleNamespace(text=None)

        cls.__init__(
            inst,
            {
                "email": "staff@bma.local",
                "role_id": 2,
                "role": "Staff",
                "enabled": "Yes",
                "loginattempts": 1,
            },
        )
        assert server_call.call_count == 0
        assert server_call_s.call_count == 0
        assert inst.drop_down_role.selected_value == 2
        assert inst.text_box_login_attempts.text == 1
    finally:
        sys.modules.pop(target, None)
