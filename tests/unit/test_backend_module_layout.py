import server_code.BMALocal as bma
from server_code import invoices, people


def test_scenario_modules_and_legacy_facade_share_callable_exports():
    assert invoices.saveInvoice is bma.saveInvoice
    assert callable(invoices.saveInvoice)
    assert invoices.getClientFullname is people.getClientFullname
