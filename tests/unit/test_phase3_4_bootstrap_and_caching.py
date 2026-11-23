from unittest.mock import MagicMock, patch
import pytest

import server_code.BMALocal as bma
from server_code import _common, inventory, people, users


def test_get_part_edit_details_happy_path_single_cursor():
    cursor = MagicMock()
    cursor.fetchone.side_effect = [
        (7, "Brake Pad Set", "BP-007", 5, 2),
        ("2026-09-01", 20, 4500.0, 3),
        ("2026-09-02", 6000.0, 5500.0),
    ]

    with patch.object(inventory, "_get_current_user"), \
         patch.object(inventory, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        result = bma.get_part_edit_details(7)

    assert db_ctx.call_count == 1
    assert result["id"] == 7
    assert result["part_name"] == "Brake Pad Set"
    assert result["part_no"] == "BP-007"
    assert result["stock_part"]["NoOfUnits"] == 20
    assert result["stock_part"]["CarPartsSupplierID"] == 3
    assert result["selling_details"]["Amount"] == 6000.0


def test_get_part_edit_details_invalid_and_unauthorized():
    with patch.object(inventory, "_get_current_user"):
        with pytest.raises(ValueError, match="Invalid part_id"):
            bma.get_part_edit_details(None)

    with patch.object(inventory, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.get_part_edit_details(7)


def test_get_assigned_jobcards_bootstrap_combines_jobs_and_technicians():
    with patch.object(inventory, "_get_current_user"), \
         patch.object(inventory, "get_assigned_jobs", return_value=[{"ID": 1}]) as mock_jobs, \
         patch.object(inventory, "getTechnicianInJobCard", return_value=[("Alice", 1)]) as mock_techs:
        res = bma.get_assigned_jobcards_bootstrap()

    assert res == {"jobs": [{"ID": 1}], "technicians": [("Alice", 1)]}
    mock_jobs.assert_called_once_with(None, None, None)
    mock_techs.assert_called_once_with()

    with patch.object(inventory, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.get_assigned_jobcards_bootstrap()


def test_search_car_parts_paginated_happy_invalid_and_unauth():
    cursor = MagicMock()
    cursor.fetchone.return_value = (120,)
    cursor.fetchall.return_value = [
        (1, "BP-01", "Brake Pad", 5, 1),
        (2, "BP-02", "Brake Rotor", 3, 2),
    ]

    with patch.object(inventory, "_get_current_user"), \
         patch.object(inventory, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        res = bma.search_car_parts_paginated("Brake", limit=25, offset=50)

    assert res["total"] == 120
    assert res["limit"] == 25
    assert res["offset"] == 50
    assert len(res["items"]) == 2
    assert res["items"][0]["PartNo"] == "BP-01"

    with patch.object(inventory, "_get_current_user"):
        with pytest.raises(ValueError, match="limit"):
            bma.search_car_parts_paginated("Brake", limit=0, offset=0)
        with pytest.raises(ValueError, match="limit"):
            bma.search_car_parts_paginated("Brake", limit=500, offset=0)
        with pytest.raises(ValueError, match="offset"):
            bma.search_car_parts_paginated("Brake", limit=10, offset=-1)

    with patch.object(inventory, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.search_car_parts_paginated("Brake")


def test_server_lookup_cache_caches_and_invalidates_on_write():
    _common.invalidate_lookup_cache()
    cursor = MagicMock()
    cursor.fetchall.return_value = [(1, "Shelf A"), (2, "Shelf B")]

    with patch.object(inventory, "_get_current_user"), \
         patch.object(inventory, "db_cursor") as db_ctx, \
         patch.object(inventory, "publish_realtime_event") as mock_pub:
        db_ctx.return_value.__enter__.return_value = cursor

        first = inventory.getLocation()
        second = inventory.getLocation()
        assert first == [("Shelf A", 1), ("Shelf B", 2)]
        assert second == first
        # Second call served from server TTL cache -> only 1 DB query!
        assert cursor.execute.call_count == 1

        # Writing a new location invalidates cache & publishes WS event
        inventory.addLocation("Shelf C")
        mock_pub.assert_called_once_with("inventory", "location_added")

        inventory.getLocation()
        assert cursor.execute.call_count == 3  # 1 initial + 1 INSERT + 1 fresh SELECT

    _common.invalidate_lookup_cache()


def test_get_client_report_paginated_happy_invalid_unauth():
    cursor = MagicMock()
    cursor.fetchone.return_value = (125,)
    cursor.fetchall.return_value = [
        (51, "Alice Smith", "0711111111", "Nairobi", "a@b.com", ""),
        (52, "Bob Jones", "0722222222", "Mombasa", "b@b.com", "VIP"),
    ]

    with patch.object(people, "_get_current_user"), \
         patch.object(people, "db_cursor") as db_ctx:
        db_ctx.return_value.__enter__.return_value = cursor
        res = bma.get_client_report_paginated(None, limit=50, offset=50)

    assert res["total"] == 125
    assert res["limit"] == 50
    assert res["offset"] == 50
    assert len(res["items"]) == 2
    assert res["items"][0]["No"] == 51
    assert res["items"][1]["No"] == 52

    with patch.object(people, "_get_current_user"):
        with pytest.raises(ValueError, match="limit"):
            bma.get_client_report_paginated(None, limit=0, offset=0)
        with pytest.raises(ValueError, match="offset"):
            bma.get_client_report_paginated(None, limit=50, offset=-5)

    with patch.object(people, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.get_client_report_paginated(None)


def test_price_catalogue_and_stock_balance_paginated_cache_and_invalidation():
    _common.invalidate_lookup_cache()
    sample_rows = [{"No": i + 1, "Name": f"Part {i}", "PartNo": f"P-{i}"} for i in range(75)]

    with patch.object(inventory, "_get_current_user"), \
         patch.object(inventory, "get_filtered_parts", return_value=sample_rows) as mock_fp, \
         patch.object(inventory, "get_car_parts_summary", return_value=sample_rows) as mock_sb:
        p1 = bma.get_filtered_parts_paginated("", limit=50, offset=0)
        p2 = bma.get_filtered_parts_paginated("", limit=50, offset=50)
        assert p1["total"] == 75 and len(p1["items"]) == 50
        assert p2["total"] == 75 and len(p2["items"]) == 25
        # Page 2 served from cache without recomputing CTE!
        assert mock_fp.call_count == 1

        s1 = bma.get_car_parts_summary_paginated("", limit=50, offset=0)
        s2 = bma.get_car_parts_summary_paginated("", limit=50, offset=50)
        assert s1["total"] == 75 and len(s1["items"]) == 50
        assert s2["total"] == 75 and len(s2["items"]) == 25
        assert mock_sb.call_count == 1

        # Prefix invalidation clears both
        _common.invalidate_lookup_cache_prefix("price_catalogue:", "stock_balance:")
        bma.get_filtered_parts_paginated("", limit=50, offset=0)
        assert mock_fp.call_count == 2

    _common.invalidate_lookup_cache()


def test_self_service_bootstrap_and_inspection_by_ref():
    from server_code import technician_portal

    with patch.object(technician_portal, "_get_current_user"), \
         patch.object(technician_portal, "getCarPartNamesAndCategory", return_value={"Brakes": ["Pads"]}), \
         patch.object(technician_portal, "get_technician_jobcards_by_status", return_value={"In Service": []}), \
         patch.object(technician_portal, "get_technicians_list", return_value=["Tech A"]):
        boot = bma.get_self_service_bootstrap()
    assert boot["parts_taxonomy"] == {"Brakes": ["Pads"]}
    assert boot["technicians"] == ["Tech A"]

    with patch.object(technician_portal, "_get_current_user"), \
         patch.object(technician_portal, "getJobCardID", return_value=99), \
         patch.object(technician_portal, "get_vehicle_inspection_data", return_value={"images": {}, "checklist": {}}):
        insp = bma.get_vehicle_inspection_by_ref("JC-099")
    assert insp == {"images": {}, "checklist": {}}

    with patch.object(technician_portal, "_get_current_user"):
        with pytest.raises(ValueError, match="Invalid jobcard_ref"):
            bma.get_vehicle_inspection_by_ref("  ")

    with patch.object(technician_portal, "_get_current_user", side_effect=Exception("Authentication required.")):
        with pytest.raises(Exception, match="Authentication required"):
            bma.get_self_service_bootstrap()
