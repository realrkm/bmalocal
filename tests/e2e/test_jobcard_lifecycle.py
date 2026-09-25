"""
End-to-End Test Suite for BMALocal Job Card Lifecycle (E2E-02).
Automates the workshop core workflow:
1. Creating a Job Card with vehicle VIN / Registration
2. Assigning a technician via tbl_pendingassignedjobs
3. Advancing status machine: Checked In -> In Service -> Ready for Pickup -> Completed
4. Logging work done in tbl_workdoneinjobcard
5. Signing off and verifying binary signature in tbl_completedjobcards
6. Validating high-volume index utilization on tbl_jobcarddetails
7. Verifying authentication security gate
"""
import datetime
import time
from unittest.mock import patch
import pytest
import anvil
import server_code.BMALocal as bma


@pytest.fixture
def auth_workshop_user():
    """Simulate an active Workshop Manager session."""
    with patch("anvil.users.get_user") as mock_user:
        mock_user.return_value = {
            "email": "workshop.manager@bmaauto.com",
            "role_id": 1,
            "role_name": "Admin"
        }
        yield mock_user


@pytest.fixture
def sample_job_card(auth_workshop_user):
    """
    Fixture that creates a unique Job Card in MySQL and guarantees
    complete teardown of all related records after the test finishes.
    """
    timestamp = int(time.time() * 1000)
    test_ref = f"JC-E2E-{timestamp}"
    test_reg = f"KDA{timestamp % 1000:03d}Z"
    test_vin = f"1HGCR2F83HA{timestamp % 1000000:06d}"

    bma.save_job_card_details(
        technicianDetails=1,
        ClientDetails=1,
        JobCardRef=test_ref,
        ReceivedDate=datetime.date.today(),
        DueDate=datetime.date.today() + datetime.timedelta(days=2),
        ExpDate=None,
        CheckedInBy=1,
        Ins=1,
        Comp=1,
        TPO=0,
        Spare=1,
        Jack=1,
        Brace=1,
        RegNo=test_reg,
        MakeAndModel="BMW 320i",
        ChassisNo=test_vin,
        EngineCC="2000",
        Mileage=82500,
        EngineNo="N20B20",
        EngineCode="N20",
        Manual=0,
        Auto=1,
        Empty=0,
        Quarter=0,
        Half=1,
        ThreeQuarter=0,
        Full=0,
        PaintCode="A83",
        ClientInstruction="E2E Test: Routine inspection and front brake overhaul",
        Notes="E2E automation test vehicle",
        IsComplete=0,
        Status="Checked In",
    )

    job_id = bma.getJobCardID(test_ref)
    assert job_id is not None, f"Failed to retrieve created job card ID for {test_ref}"

    yield {
        "id": job_id,
        "ref": test_ref,
        "reg": test_reg,
        "vin": test_vin,
        "tech_id": 1,
    }

    # Teardown: clean up all foreign key dependents then the job card
    with bma.db_cursor() as cur:
        cur.execute("DELETE FROM tbl_completedjobcards WHERE AssignedJobCardID = %s", (job_id,))
        cur.execute("DELETE FROM tbl_workdoneinjobcard WHERE JobCardRefID = %s", (job_id,))
        cur.execute("DELETE FROM tbl_pendingassignedjobs WHERE JobCardRefID = %s", (job_id,))
        cur.execute("DELETE FROM tbl_technician_portal_notifications WHERE jobcard = %s", (test_ref,))
        cur.execute("DELETE FROM tbl_jobcarddetails WHERE ID = %s", (job_id,))


def test_job_card_creation_and_technician_assignment(sample_job_card):
    """Verify Job Card is created in tbl_jobcarddetails and technician is linked in tbl_pendingassignedjobs."""
    job_id = sample_job_card["id"]

    with bma.db_cursor() as cur:
        # Check job card details table
        cur.execute("""
            SELECT RegNo, ChassisNo, JobCardRef, Status, IsComplete, Mileage
            FROM tbl_jobcarddetails
            WHERE ID = %s
        """, (job_id,))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == sample_job_card["reg"]
        assert row[1] == sample_job_card["vin"]
        assert row[2] == sample_job_card["ref"]
        assert row[3] == "Checked In"
        assert bool(row[4]) is False
        assert row[5] == 82500

        # Check pending technician assignment table
        cur.execute("""
            SELECT TechnicianID, JobCardRefID
            FROM tbl_pendingassignedjobs
            WHERE JobCardRefID = %s
        """, (job_id,))
        assign_row = cur.fetchone()
        assert assign_row is not None
        assert assign_row[0] == sample_job_card["tech_id"]
        assert assign_row[1] == job_id


def test_job_card_status_transitions_and_work_logging(auth_workshop_user, sample_job_card):
    """
    Verify status transition state machine:
    Checked In -> In Service -> (Log Work) -> Ready for Pickup
    """
    job_id = sample_job_card["id"]

    # 1. Advance to 'In Service'
    bma.updateJobCardStatus(job_id, "In Service")
    with bma.db_cursor() as cur:
        cur.execute("SELECT Status FROM tbl_jobcarddetails WHERE ID = %s", (job_id,))
        assert cur.fetchone()[0] == "In Service"

    # 2. Log work done by technician
    work_text = "Replaced front brake pads, brake fluid flushed, 50-point inspection passed."
    bma.saveWorkDoneInJobCard(job_id, work_text)

    with bma.db_cursor() as cur:
        cur.execute("SELECT WorkDone FROM tbl_workdoneinjobcard WHERE JobCardRefID = %s", (job_id,))
        work_row = cur.fetchone()
        assert work_row is not None
        assert work_row[0] == work_text

    # 3. Advance to 'Ready for Pickup'
    bma.updateJobCardStatus(job_id, "Ready for Pickup")
    with bma.db_cursor() as cur:
        cur.execute("SELECT Status FROM tbl_jobcarddetails WHERE ID = %s", (job_id,))
        assert cur.fetchone()[0] == "Ready for Pickup"


def test_job_card_signoff_and_completion(auth_workshop_user, sample_job_card):
    """Verify workshop sign-off with binary signature and completion status update."""
    job_id = sample_job_card["id"]

    # Advance to Ready for Pickup first
    bma.updateJobCardStatus(job_id, "Ready for Pickup")

    # Sign off with client/manager confirmation
    signature_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRTEST_SIGNATURE_STREAM"
    signature_blob = anvil.BlobMedia("image/png", signature_content)
    completion_time = datetime.datetime.now()
    remarks_text = "Vehicle road tested. Brakes performing within factory tolerance. Client approved."

    bma.saveConfirmationDetails(
        jobCardId=job_id,
        remarks=remarks_text,
        signature=signature_blob,
        dateCompleted=completion_time
    )
    bma.updateJobCardStatus(job_id, "Completed")

    with bma.db_cursor() as cur:
        # Check completion table
        cur.execute("""
            SELECT AssignedJobCardID, Remarks, Signature
            FROM tbl_completedjobcards
            WHERE AssignedJobCardID = %s
        """, (job_id,))
        comp_row = cur.fetchone()
        assert comp_row is not None
        assert comp_row[0] == job_id
        assert comp_row[1] == remarks_text
        assert bytes(comp_row[2]) == signature_content

        # Check jobcard details table
        cur.execute("SELECT IsComplete, Status FROM tbl_jobcarddetails WHERE ID = %s", (job_id,))
        final_row = cur.fetchone()
        assert bool(final_row[0]) is True
        assert final_row[1] == "Completed"


def test_high_volume_index_utilization(sample_job_card):
    """
    Verify that query planner utilizes Migration V001 indexes
    (idx_jobcard_regno, idx_jobcard_ref, idx_jobcard_status)
    to perform single-row lookups against 11,700+ rows.
    """
    with bma.db_cursor() as cur:
        # 1. Registration lookup
        cur.execute(
            "EXPLAIN SELECT ID, RegNo, Status FROM tbl_jobcarddetails WHERE RegNo = %s",
            (sample_job_card["reg"],)
        )
        plan_reg = cur.fetchone()
        # plan format: (id, select_type, table, partitions, type, possible_keys, key, ...)
        used_key_reg = plan_reg[6]
        rows_reg = plan_reg[9]
        assert "idx_jobcard_regno" in str(used_key_reg), f"Expected idx_jobcard_regno, got {used_key_reg}"
        assert rows_reg <= 2, f"Expected single-row index lookup, got {rows_reg}"

        # 2. JobCardRef lookup
        cur.execute(
            "EXPLAIN SELECT ID, JobCardRef FROM tbl_jobcarddetails WHERE JobCardRef = %s",
            (sample_job_card["ref"],)
        )
        plan_ref = cur.fetchone()
        used_key_ref = plan_ref[6]
        rows_ref = plan_ref[9]
        assert "idx_jobcard_ref" in str(used_key_ref), f"Expected idx_jobcard_ref, got {used_key_ref}"
        assert rows_ref <= 2, f"Expected single-row index lookup, got {rows_ref}"


def test_unauthenticated_job_card_access_rejection(sample_job_card):
    """Verify security boundary: unauthenticated callers are rejected with Authentication required."""
    with patch("anvil.users.get_user", return_value=None):
        with pytest.raises(Exception, match="Authentication required"):
            bma.updateJobCardStatus(sample_job_card["id"], "In Service")

        with pytest.raises(Exception, match="Authentication required"):
            bma.getJobCardID(sample_job_card["ref"])
