"""
End-to-End Test Suite for BMALocal Invoice Generation & PDF Engine Verification (E2E-03).
Covers the core billing and document generation workflow:
1. Converting completed Job Cards to Invoices in tbl_invoices with parts and labor line items.
2. Validating line items, quantities, unit prices, line item totals, and foreign key linkage.
3. Testing financial breakdown calculations: subtotals, multi-tier discounts, and 16% VAT.
4. Verifying wkhtmltopdf headless rendering pipeline producing valid %PDF binary documents.
5. Verifying server-side cleanup of temporary PDF artifacts (deleteFile).
6. Testing payment recording in tbl_payments and invoice status transition: Pending -> Paid.
7. Enforcing authentication security gates across all invoicing and billing endpoints.
"""
import datetime
import os
import time
from unittest.mock import patch
import pytest

import server_code.BMALocal as bma
from tests.helpers import calculate_invoice_breakdown


@pytest.fixture
def auth_billing_user():
    """Simulate an active Accounts / Billing Manager session."""
    with patch("anvil.users.get_user") as mock_user:
        mock_user.return_value = {
            "email": "billing.accounts@bmaauto.com",
            "role_id": 1,
            "role_name": "Admin",
        }
        yield mock_user


@pytest.fixture
def completed_job_card_for_invoice(auth_billing_user):
    """
    Fixture that creates a completed Job Card linked to a valid client contact in MySQL,
    and guarantees complete teardown of all related invoice, payment, and job card records.
    """
    with bma.db_cursor() as cur:
        cur.execute("SELECT ID FROM tbl_clientcontacts LIMIT 1")
        row = cur.fetchone()
        if row:
            client_id = row[0]
        else:
            cur.execute(
                "INSERT INTO tbl_clientcontacts (Fullname, PhoneNumber, Email) "
                "VALUES ('E2E Test Client', '+254700123456', 'e2e.client@test.com')"
            )
            client_id = cur.lastrowid

    timestamp = int(time.time() * 1000)
    test_ref = f"JC-INV-{timestamp}"
    test_reg = f"KDC{timestamp % 1000:03d}Y"
    test_vin = f"WBAJC{timestamp % 1000000:06d}"

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
        MakeAndModel="BMW 520d Touring",
        ChassisNo=test_vin,
        EngineCC="2000",
        Mileage=74200,
        EngineNo="B47D20A",
        EngineCode="B47",
        Manual=0,
        Auto=1,
        Empty=0,
        Quarter=0,
        Half=1,
        ThreeQuarter=0,
        Full=0,
        PaintCode="475",
        ClientInstruction="E2E Test: Routine inspection and complete service",
        Notes="E2E automation test for invoice and PDF engine",
        IsComplete=1,
        Status="Completed",
    )

    job_id = bma.getJobCardID(test_ref)
    assert job_id is not None, f"Failed to retrieve created job card ID for {test_ref}"

    expected_pdf_path = f"{test_ref} Invoice"

    yield {
        "id": job_id,
        "ref": test_ref,
        "reg": test_reg,
        "vin": test_vin,
        "client_id": client_id,
        "expected_pdf_path": expected_pdf_path,
    }

    # Teardown: clean up file artifacts and all dependent MySQL rows
    if os.path.exists(expected_pdf_path):
        try:
            os.remove(expected_pdf_path)
        except OSError:
            pass

    with bma.db_cursor() as cur:
        cur.execute("DELETE FROM tbl_payments WHERE JobCardRefID = %s", (job_id,))
        cur.execute("DELETE FROM tbl_assignedcarparts WHERE AssignedJobID = %s", (job_id,))
        cur.execute("DELETE FROM tbl_invoices WHERE AssignedJobID = %s", (job_id,))
        cur.execute("DELETE FROM tbl_pendingassignedjobs WHERE JobCardRefID = %s", (job_id,))
        cur.execute("DELETE FROM tbl_technician_portal_notifications WHERE jobcard = %s", (test_ref,))
        cur.execute("DELETE FROM tbl_jobcarddetails WHERE ID = %s", (job_id,))


def test_convert_completed_jobcard_to_invoice_line_items(completed_job_card_for_invoice):
    """
    Verify completed Job Card can be converted to an invoice in tbl_invoices with
    multiple parts and labor line items, computing individual totals and linking via AssignedJobID.
    """
    job_id = completed_job_card_for_invoice["id"]
    assigned_date = datetime.date.today().strftime("%Y-%m-%d")

    items = [
        {
            "name": "BMW TwinPower Turbo 5W-30 Oil (1L)",
            "number": "OIL-83212405948",
            "quantity": 5.0,
            "amount": 2200.0,
            "CarPartID": None,
        },
        {
            "name": "Oil Filter Element Set",
            "number": "OF-11428507683",
            "quantity": 1.0,
            "amount": 3500.0,
            "CarPartID": None,
        },
        {
            "name": "Standard Inspection & Scheduled Service Labor",
            "number": "LBR-SRV-001",
            "quantity": 1.0,
            "amount": 7500.0,
            "CarPartID": None,
        },
    ]

    # Save invoice line items
    bma.saveInvoice(assigned_date, job_id, items)

    # Retrieve invoice details and verify schema mapping & mathematical integrity
    invoice_rows = bma.get_invoice_details_by_job_id(job_id)
    assert len(invoice_rows) == 3, f"Expected 3 invoice rows, got {len(invoice_rows)}"

    # Validate first item (5L oil @ 2,200 = 11,000)
    oil_item = invoice_rows[0]
    assert oil_item["Item"] == "BMW TwinPower Turbo 5W-30 Oil (1L)"
    assert oil_item["PartNo"] == "OIL-83212405948"
    assert oil_item["QuantityIssued"] == 5.0
    assert oil_item["Amount"] == 2200.0
    assert oil_item["Total"] == 11000.0
    assert oil_item["AssignedJobID"] == job_id

    # Validate second item (1 Oil Filter @ 3,500 = 3,500)
    filter_item = invoice_rows[1]
    assert filter_item["Item"] == "Oil Filter Element Set"
    assert filter_item["QuantityIssued"] == 1.0
    assert filter_item["Amount"] == 3500.0
    assert filter_item["Total"] == 3500.0

    # Validate third item (Labor @ 7,500 = 7,500)
    labor_item = invoice_rows[2]
    assert labor_item["Item"] == "Standard Inspection & Scheduled Service Labor"
    assert labor_item["QuantityIssued"] == 1.0
    assert labor_item["Amount"] == 7500.0
    assert labor_item["Total"] == 7500.0

    # Verify initial status in database is 'Pending'
    with bma.db_cursor() as cur:
        cur.execute("SELECT DISTINCT Status FROM tbl_invoices WHERE AssignedJobID = %s", (job_id,))
        statuses = [r[0] for r in cur.fetchall()]
        assert statuses == ["Pending"], f"Expected initial status 'Pending', got {statuses}"


def test_invoice_financial_calculations_vat_and_discounts(completed_job_card_for_invoice):
    """
    Verify financial breakdown calculations using calculate_invoice_breakdown:
    subtotal aggregation, multi-tier discounts (0%, 5%, 10%), 16% standard VAT, and error handling.
    """
    job_id = completed_job_card_for_invoice["id"]
    assigned_date = datetime.date.today().strftime("%Y-%m-%d")

    items = [
        {"name": "Front Brake Pads", "number": "BP-001", "quantity": 1.0, "amount": 12000.0, "CarPartID": None},
        {"name": "Brake Sensor Cable", "number": "BS-002", "quantity": 1.0, "amount": 2500.0, "CarPartID": None},
        {"name": "Brake Service Labor", "number": "LBR-003", "quantity": 1.0, "amount": 5500.0, "CarPartID": None},
    ]
    bma.saveInvoice(assigned_date, job_id, items)

    details = bma.get_invoice_details_by_job_id(job_id)
    gross_subtotal = sum(d["Total"] for d in details)
    assert gross_subtotal == 20000.0

    # Scenario 1: Standard 16% VAT with 0% discount
    breakdown_0 = calculate_invoice_breakdown(gross_subtotal, discount_percent=0.0, tax_rate_percent=16.0)
    assert breakdown_0["subtotal"] == 20000.0
    assert breakdown_0["discount_amount"] == 0.0
    assert breakdown_0["net_subtotal"] == 20000.0
    assert breakdown_0["tax_amount"] == 3200.0  # 16% of 20,000
    assert breakdown_0["total_amount"] == 23200.0

    # Scenario 2: 5% customer loyalty discount + 16% VAT
    breakdown_5 = calculate_invoice_breakdown(gross_subtotal, discount_percent=5.0, tax_rate_percent=16.0)
    assert breakdown_5["subtotal"] == 20000.0
    assert breakdown_5["discount_amount"] == 1000.0  # 5% of 20,000
    assert breakdown_5["net_subtotal"] == 19000.0
    assert breakdown_5["tax_amount"] == 3040.0  # 16% of 19,000
    assert breakdown_5["total_amount"] == 22040.0

    # Scenario 3: 10% fleet discount + 16% VAT
    breakdown_10 = calculate_invoice_breakdown(gross_subtotal, discount_percent=10.0, tax_rate_percent=16.0)
    assert breakdown_10["discount_amount"] == 2000.0
    assert breakdown_10["net_subtotal"] == 18000.0
    assert breakdown_10["tax_amount"] == 2880.0
    assert breakdown_10["total_amount"] == 20880.0

    # Scenario 4: Error handling for invalid inputs
    with pytest.raises(ValueError, match="Subtotal cannot be negative"):
        calculate_invoice_breakdown(-100.0)
    with pytest.raises(ValueError, match="Discount percent must be between 0 and 100"):
        calculate_invoice_breakdown(1000.0, discount_percent=105.0)
    with pytest.raises(ValueError, match="Tax rate cannot be negative"):
        calculate_invoice_breakdown(1000.0, tax_rate_percent=-5.0)


def test_wkhtmltopdf_pdf_pipeline_generation_and_cleanup(completed_job_card_for_invoice):
    """
    Verify the wkhtmltopdf PDF rendering pipeline:
    1. Validates external binary configuration.
    2. Executes createQuotationInvoicePdf(jobCardID, 'Invoice').
    3. Confirms generated media is valid application/pdf with %PDF-1.4 header and non-empty size (>10KB).
    4. Executes deleteFile to verify server-side cleanup removes temporary file from disk.
    """
    job_id = completed_job_card_for_invoice["id"]
    assigned_date = datetime.date.today().strftime("%Y-%m-%d")

    # Seed invoice items
    items = [
        {"name": "Spark Plug Set (4 pcs)", "number": "SP-12120037582", "quantity": 1.0, "amount": 8400.0, "CarPartID": None},
        {"name": "Air Filter Element", "number": "AF-13717619267", "quantity": 1.0, "amount": 4200.0, "CarPartID": None},
        {"name": "Tune-Up Labor", "number": "LBR-TUNE-01", "quantity": 1.0, "amount": 5000.0, "CarPartID": None},
    ]
    bma.saveInvoice(assigned_date, job_id, items)

    # Verify WKHTMLTOPDF_PATH exists
    wkhtmltopdf_path = os.getenv("WKHTMLTOPDF_PATH")
    assert wkhtmltopdf_path is not None, "WKHTMLTOPDF_PATH environment variable is missing"
    assert os.path.exists(wkhtmltopdf_path), f"wkhtmltopdf binary not found at {wkhtmltopdf_path}"

    # Generate Invoice PDF via wkhtmltopdf
    media_object = bma.createQuotationInvoicePdf(job_id, "Invoice")
    assert media_object is not None, "createQuotationInvoicePdf returned None"
    assert getattr(media_object, "content_type", None) == "application/pdf"

    # Verify physical file generated on disk
    doc_name = bma.getQuotationInvoiceName(job_id)
    expected_file = f"{doc_name} Invoice"
    assert os.path.exists(expected_file), f"Expected PDF file '{expected_file}' was not found on disk"

    # Check file size (realistic invoice with logo & styling is > 10 KB)
    file_size = os.path.getsize(expected_file)
    assert file_size > 10000, f"Expected PDF size > 10,000 bytes, got {file_size}"

    # Verify PDF magic header
    with open(expected_file, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-", f"Invalid PDF header magic bytes: {header}"

    # Verify server cleanup via deleteFile
    bma.deleteFile(job_id, "Invoice")
    assert not os.path.exists(expected_file), f"Temporary PDF file '{expected_file}' was not deleted by deleteFile"


def test_invoice_payment_recording_and_status_transition(completed_job_card_for_invoice):
    """
    Verify payment details recording in tbl_payments and invoice status transition
    from 'Pending' to 'Paid' upon full settlement.
    """
    job_id = completed_job_card_for_invoice["id"]
    assigned_date = datetime.date.today().strftime("%Y-%m-%d")

    items = [
        {"name": "Coolant Fluid (1.5L)", "number": "FL-COOL-83192211191", "quantity": 2.0, "amount": 1800.0, "CarPartID": None},
        {"name": "Coolant Flush Labor", "number": "LBR-FLUSH-01", "quantity": 1.0, "amount": 3500.0, "CarPartID": None},
    ]
    bma.saveInvoice(assigned_date, job_id, items)

    # Subtotal = 2 * 1800 + 3500 = 7100
    details = bma.get_invoice_details_by_job_id(job_id)
    subtotal = sum(d["Total"] for d in details)
    assert subtotal == 7100.0

    # Record Payment in tbl_payments (e.g. M-Pesa settlement with 100 KES round-off discount)
    payment_date = datetime.date.today()
    bma.save_payment_details(
        paymentDate=payment_date,
        jobCardRefID=job_id,
        paymentMode="M-Pesa",
        amountPaid=7000.0,
        discount=100.0,
        bal=0.0,
    )

    # Verify payment queries
    prev_paid = bma.get_previous_payment(job_id)
    assert prev_paid == "7,000.00"

    disc_paid = bma.get_discount_payment(job_id)
    assert disc_paid == "100.00"

    # Transition Invoice status to 'Paid'
    bma.update_invoice_status(job_id)

    # Verify Status changed to 'Paid' in database
    with bma.db_cursor() as cur:
        cur.execute("SELECT DISTINCT Status FROM tbl_invoices WHERE AssignedJobID = %s", (job_id,))
        statuses = [r[0] for r in cur.fetchall()]
        assert statuses == ["Paid"], f"Expected invoice status 'Paid', got {statuses}"


def test_unauthenticated_invoice_operations_rejected():
    """
    Security gate verification: Ensure that all invoice, PDF, and payment operations
    reject unauthenticated calls with an 'Authentication required' exception.
    """
    with patch("anvil.users.get_user", return_value=None):
        with pytest.raises(Exception, match="Authentication required"):
            bma.saveInvoice(datetime.date.today().strftime("%Y-%m-%d"), 1, [])

        with pytest.raises(Exception, match="Authentication required"):
            bma.get_invoice_details_by_job_id(1)

        with pytest.raises(Exception, match="Authentication required"):
            bma.createQuotationInvoicePdf(1, "Invoice")

        with pytest.raises(Exception, match="Authentication required"):
            bma.save_payment_details(datetime.date.today(), 1, "Cash", 1000, 0, 0)

        with pytest.raises(Exception, match="Authentication required"):
            bma.update_invoice_status(1)
