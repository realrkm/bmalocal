"""Compatibility exports for BMALocal server callables and shared helpers."""

import os as _os
import sys as _sys

if not __package__:
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    __package__ = "server_code"
if __name__ == "__main__":
    _sys.modules["server_code.BMALocal"] = _sys.modules[__name__]

from . import _common as _common
from ._common import *
from . import (
    people as _people,
    vehicles as _vehicles,
    job_cards as _job_cards,
    inventory as _inventory,
    quotations as _quotations,
    invoices as _invoices,
    reports as _reports,
    users as _users,
    orders as _orders,
    notifications as _notifications,
    technician_portal as _technician_portal,
    dashboard as _dashboard,
    bookings as _bookings,
    realtime as _realtime,
    vehicle_inspection as _vehicle_inspection,
)

_SCENARIO_MODULES = (
    _people,
    _vehicles,
    _job_cards,
    _inventory,
    _quotations,
    _invoices,
    _reports,
    _users,
    _orders,
    _notifications,
    _technician_portal,
    _dashboard,
    _bookings,
    _realtime,
    _vehicle_inspection,
)

__all__ = list(_common.__all__)

# Populate each scenario namespace with shared and cross-scenario dependencies.
for _module in _SCENARIO_MODULES:
    for _name in _module.__all__:
        globals()[_name] = getattr(_module, _name)
        if _name not in __all__:
            __all__.append(_name)

for _module in _SCENARIO_MODULES:
    _module.__dict__.update((_name, globals()[_name]) for _name in __all__)

if __name__ == "__main__":
    try:
        asyncio.run(main_ws())
    except KeyboardInterrupt:
        print("\n[!] Chat WebSocket server stopped.")
