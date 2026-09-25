"""
End-to-End Test Suite for BMALocal Contact Management & Vehicle Profile Linking (E2E-04).
Covers the core CRM and vehicle registry workflow:
1. Creating client contacts in tbl_clientcontacts with full contact and narrative profiles.
2. Duplicate phone number detection using check_duplicate_contact.
3. Client search by name keywords and telephone numbers.
4. Editing and updating client contact information.
5. Linking vehicle profiles (Make/Model, Registration, VIN/Chassis) to clients via Job Cards.
6. Multi-dimensional search across vehicles by RegNo, ChassisNo, Phone, and Client Name.
7. Query performance validation verifying index utilization (idx_clientcontacts_phone).
8. Security gate verification enforcing authentication across all contact callables.
"""
import datetime
import time
from unittest.mock import patch
import pytest

import server_code.BMALocal as bma


@pytest.fixture
def auth_contact_user():
    """Simulate an active Service Advisor / Back Office session."""
    with patch("anvil.users.get_user") as mock_user:
        mock_user.return_value = {
            "email": "service.advisor@bmaauto.com",
            "role_id": 1,
            "role_name": "Admin",
        }
        yield mock_user


@pytest.fixture
def managed_client_contact(auth_contact_user):
    """
    Fixture that creates a unique client contact in tbl_clientcontacts
    and guarantees complete cleanup of the contact and any dependent rows in teardown.
    """
    timestamp = int(time.time() * 1000)
    test_phone = f"+2547{timestamp % 100000000:08d}"
    test_name = f"Jane Mutua {timestamp % 1000}"
    test_address = "Karen Plains Road, Nairobi"
    test_email = f"jane.mutua.{timestamp % 1000}@bma-client.com"
    test_narration = "Corporate account - priority servicing"

    bma.save_client_data(
        name=test_name,
        phone=test_phone,
        address=test_address,
        email=test_email,
        narration=test_narration,
    )

    # Retrieve created ID
    results = bma.getClientNameAndPhoneNumber(test_phone)
    assert len(results) > 0, f"Failed to retrieve created contact with phone {test_phone}"
    client_id = results[0][1]

    client_context = {
        "id": client_id,
        "name": test_name,
        "phone": test_phone,
        "address": test_address,
        "email": test_email,
        "narration": test_narration,
        "created_job_ids": [],
    }

    yield client_context

    # Teardown: clean up any linked job cards first, then the contact
    with bma.db_cursor() as cur:
        for jid in client_context["created_job_ids"]:
            cur.execute("DELETE FROM tbl_completedjobcards WHERE AssignedJobCardID = %s", (jid,))
            cur.execute("DELETE FROM tbl_payments WHERE JobCardRefID = %s", (jid,))
            cur.execute("DELETE FROM tbl_invoices WHERE AssignedJobID = %s", (jid,))
            cur.execute("DELETE FROM tbl_workdoneinjobcard WHERE JobCardRefID = %s", (jid,))
            cur.execute("DELETE FROM tbl_pendingassignedjobs WHERE JobCardRefID = %s", (jid,))
            cur.execute("DELETE FROM tbl_technician_portal_notifications WHERE jobcard IN (SELECT JobCardRef FROM tbl_jobcarddetails WHERE ID = %s)", (jid,))
            cur.execute("DELETE FROM tbl_jobcarddetails WHERE ID = %s", (jid,))

        cur.execute("DELETE FROM tbl_clientcontacts WHERE ID = %s", (client_id,))


def test_client_contact_lifecycle_create_read_update(auth_contact_user):
    """
    Verify complete client contact lifecycle:
    1. Duplicate check returns False for fresh number.
    2. Save client data creates contact in tbl_clientcontacts.
    3. Duplicate check returns True once contact is inserted.
    4. Retrieve full profile with getClientNameWithID and verify all fields.
    5. Update client details and verify persistence.
    """
    timestamp = int(time.time() * 1000)
    phone = f"+2547{timestamp % 100000000:08d}"
    name = f"George Omondi {timestamp % 1000}"
    address = "Kilimani, Nairobi"
    email = f"george.{timestamp % 1000}@bma-client.com"
    narration = "Initial contact test"

    # 1. Verify duplicate check returns False initially
    assert not bma.check_duplicate_contact("Client", phone), "Phone should not exist yet"

    # 2. Create contact
    bma.save_client_data(name, phone, address, email, narration)

    # 3. Duplicate check must now return True
    assert bma.check_duplicate_contact("Client", phone), "Duplicate check should detect newly created client"

    # 4. Lookup client ID
    search_res = bma.getClientNameAndPhoneNumber(phone)
    assert len(search_res) >= 1
    client_id = search_res[0][1]

    try:
        # Retrieve full profile
        profile = bma.getClientNameWithID(client_id)
        assert profile["ID"] == client_id
        assert profile["Fullname"] == name
        assert profile["Phone"] == phone
        assert profile["Address"] == address
        assert profile["Email"] == email
        assert profile["Narration"] == narration

        # 5. Update contact details
        updated_name = f"{name} (Updated)"
        updated_address = "Lavington Green, Nairobi"
        updated_email = f"george.updated.{timestamp % 1000}@bma-client.com"
        updated_narration = "Updated VIP tier"

        bma.updateClientDetails(
            client_id=client_id,
            name=updated_name,
            phone=phone,
            address=updated_address,
            email=updated_email,
            narration=updated_narration,
        )

        updated_profile = bma.getClientNameWithID(client_id)
        assert updated_profile["Fullname"] == updated_name
        assert updated_profile["Address"] == updated_address
        assert updated_profile["Email"] == updated_email
        assert updated_profile["Narration"] == updated_narration

    finally:
        # Cleanup
        with bma.db_cursor() as cur:
            cur.execute("DELETE FROM tbl_clientcontacts WHERE ID = %s", (client_id,))


def test_client_search_and_report_generation(managed_client_contact):
    """
    Verify client searching by keyword and phone, and report generation via getClientReport.
    """
    client = managed_client_contact
    client_id = client["id"]

    # Search by partial phone
    phone_snippet = client["phone"][-6:]
    search_by_phone = bma.getClientNameAndPhoneNumber(phone_snippet)
    matched_ids = [item[1] for item in search_by_phone]
    assert client_id in matched_ids, f"Expected client {client_id} in phone search results"

    # Search by first name keyword
    first_name = client["name"].split()[0]
    search_by_name = bma.getClientFullnameFromSearchWord(first_name)
    matched_name_ids = [item[1] for item in search_by_name]
    assert client_id in matched_name_ids, f"Expected client {client_id} in name search results"

    # Generate single client report
    report = bma.getClientReport(client_id)
    assert len(report) == 1, f"Expected 1 report record, got {len(report)}"
    record = report[0]
    assert record["ID"] == client_id
    assert record["Fullname"] == client["name"]
    assert record["Phone"] == client["phone"]
    assert record["Address"] == client["address"]
    assert record["Email"] == client["email"]


def test_vehicle_profile_linking_and_multidimensional_search(managed_client_contact):
    """
    Verify linking a vehicle profile and Job Card to a client, then executing
    multi-dimensional searches across Registration, Chassis/VIN, Phone, and Client Name.
    """
    client = managed_client_contact
    client_id = client["id"]

    timestamp = int(time.time() * 1000)
    test_reg = f"KDF{timestamp % 1000:03d}M"
    test_vin = f"WBA3A{timestamp % 1000000:06d}"
    test_ref = f"JC-VEH-{timestamp}"
    test_model = "BMW M340i xDrive"

    # Create vehicle Job Card linked to this client
    bma.save_job_card_details(
        technicianDetails=1,
        ClientDetails=client_id,
        JobCardRef=test_ref,
        ReceivedDate=datetime.date.today(),
        DueDate=datetime.date.today(),
        ExpDate=None,
        CheckedInBy=1,
        Ins=1,
        Comp=1,
        TPO=0,
        Spare=1,
        Jack=1,
        Brace=1,
        RegNo=test_reg,
        MakeAndModel=test_model,
        ChassisNo=test_vin,
        EngineCC="3000",
        Mileage=32000,
        EngineNo="B58B30O1",
        EngineCode="B58",
        Manual=0,
        Auto=1,
        Empty=0,
        Quarter=0,
        Half=1,
        ThreeQuarter=0,
        Full=0,
        PaintCode="C31",
        ClientInstruction="Check adaptive suspension and exhaust valve",
        Notes="Vehicle linking test",
        IsComplete=0,
        Status="Checked In",
    )

    job_id = bma.getJobCardID(test_ref)
    assert job_id is not None
    client["created_job_ids"].append(job_id)

    # 1. Verify getCarRegNoFromClientID returns the vehicle's RegNo
    regs = bma.getCarRegNoFromClientID(client_id)
    assert test_reg in regs, f"Expected {test_reg} in client vehicle registrations: {regs}"

    # 2. Search vehicle profile by Registration Number
    cars_by_reg = bma.get_car_details(search_term=test_reg)
    assert len(cars_by_reg) >= 1
    reg_match = next((c for c in cars_by_reg if c["RegNo"] == test_reg), None)
    assert reg_match is not None, f"Vehicle {test_reg} not found by RegNo search"
    assert reg_match["Fullname"] == client["name"]
    assert reg_match["Phone"] == client["phone"]
    assert reg_match["MakeAndModel"] == test_model
    assert reg_match["ChassisNo"] == test_vin

    # 3. Search vehicle profile by Client Phone Number
    cars_by_phone = bma.get_car_details(search_term=client["phone"])
    assert any(c["RegNo"] == test_reg for c in cars_by_phone), "Vehicle not found by client phone search"

    # 4. Search vehicle profile by Chassis/VIN
    cars_by_vin = bma.get_car_details(search_term=test_vin)
    assert any(c["RegNo"] == test_reg for c in cars_by_vin), "Vehicle not found by VIN search"

    # 5. Search Job Card by Client Name keyword
    jc_search = bma.getJobCardDetailsWithRefOrFullnameSearch(client["name"])
    assert any(item[1] == job_id for item in jc_search), f"Job card {job_id} not found by client name search"


def test_indexed_phone_lookup_query_plan(managed_client_contact):
    """
    Verify that phone number lookups in tbl_clientcontacts utilize
    the idx_clientcontacts_phone index via MySQL EXPLAIN query plan analysis.
    """
    phone = managed_client_contact["phone"]

    with bma.db_cursor() as cur:
        start_time = time.perf_counter()
        cur.execute(
            "EXPLAIN SELECT ID FROM tbl_clientcontacts WHERE Phone = %s",
            (phone,),
        )
        plan_rows = cur.fetchall()
        duration_ms = (time.perf_counter() - start_time) * 1000

    assert len(plan_rows) > 0, "No execution plan returned"
    plan = plan_rows[0]

    # MySQL EXPLAIN columns: id, select_type, table, partitions, type, possible_keys, key, key_len, ref, rows, filtered, Extra
    table_name = plan[2]
    access_type = plan[4]
    used_key = plan[6]
    ref_type = plan[8]
    extra_info = plan[11]

    assert table_name == "tbl_clientcontacts"
    assert used_key == "idx_clientcontacts_phone", f"Expected idx_clientcontacts_phone, got {used_key}"
    assert access_type == "ref", f"Expected 'ref' access type, got {access_type}"
    assert ref_type == "const", f"Expected 'const' reference, got {ref_type}"
    assert "Using index" in extra_info, f"Expected covering index usage, got {extra_info}"
    assert duration_ms < 50.0, f"Index EXPLAIN query took too long: {duration_ms:.2f}ms"


def test_unauthenticated_contact_operations_rejected():
    """
    Security gate verification: Ensure unauthenticated calls to contact
    and vehicle registry endpoints are rejected with 'Authentication required'.
    """
    with patch("anvil.users.get_user", return_value=None):
        with pytest.raises(Exception, match="Authentication required"):
            bma.getClientFullname()

        with pytest.raises(Exception, match="Authentication required"):
            bma.getClientNameWithID(1)

        with pytest.raises(Exception, match="Authentication required"):
            bma.save_client_data("Test", "+254700000000", "Nairobi", "test@test.com", "Note")

        with pytest.raises(Exception, match="Authentication required"):
            bma.updateClientDetails(1, "Test", "+254700000000", "Nairobi", "test@test.com", "Note")

        with pytest.raises(Exception, match="Authentication required"):
            bma.check_duplicate_contact("Client", "+254700000000")

        with pytest.raises(Exception, match="Authentication required"):
            bma.get_car_details()

        with pytest.raises(Exception, match="Authentication required"):
            bma.getCarRegNoFromClientID(1)
