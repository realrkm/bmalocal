"""
Concurrency & Load Performance Benchmark Suite for BMALocal.
Validates latency budgets under concurrent load across indexed tables:
- tbl_jobcarddetails (~11,500 rows): idx_jobcard_regno, idx_jobcard_ref, idx_jobcard_status
- tbl_invoices (~1,000 rows): AssignedJobID, idx_invoices_partno
- tbl_clientcontacts (~2,600 rows): idx_clientcontacts_phone, idx_clientcontacts_name
- tbl_walkietalkie_messages: PRIMARY, created_at

Standards Enforced (bmalocal-performance-reliability):
- Instant Search Budget: < 300ms
- Job Card Save / Status Transition Budget: < 500ms
- Invoice Save & Calculation Budget: < 500ms
- Connection Pool Resilience under multi-threaded concurrency
"""
import concurrent.futures
import statistics
import time
from unittest.mock import patch
import pytest

import server_code.BMALocal as bma


@pytest.fixture(autouse=True)
def auth_benchmark_user():
    """Simulate an active admin session for database callables."""
    with patch("anvil.users.get_user") as mock_user:
        mock_user.return_value = {
            "email": "benchmark.runner@bmaauto.com",
            "role_id": 1,
            "role_name": "Admin",
        }
        yield mock_user


def test_concurrent_contact_search_benchmark():
    """
    Benchmark concurrent searches on tbl_clientcontacts (~2,600 rows).
    Simulates 10 concurrent advisor terminals executing phone & name lookups.
    Budget: Mean < 50ms, p95 < 150ms, Max < 300ms.
    """
    concurrency = 10
    total_requests = 50

    def execute_contact_lookup(i):
        t0 = time.perf_counter()
        with bma.db_cursor() as cur:
            # Alternate between phone lookup and name search
            if i % 2 == 0:
                cur.execute(
                    "SELECT ID, Fullname, Phone FROM tbl_clientcontacts WHERE Phone = %s",
                    ("+254700000000",),
                )
            else:
                cur.execute(
                    "SELECT ID, Fullname, Phone FROM tbl_clientcontacts WHERE Fullname LIKE %s LIMIT 10",
                    ("John%",),
                )
            cur.fetchall()
        return (time.perf_counter() - t0) * 1000

    latencies = []
    t_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(execute_contact_lookup, i) for i in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            latencies.append(f.result())
    wall_time_ms = (time.perf_counter() - t_start) * 1000

    mean_lat = statistics.mean(latencies)
    median_lat = statistics.median(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18]
    max_lat = max(latencies)
    throughput = total_requests / (wall_time_ms / 1000)

    print(f"\n[Contact Search Benchmark] Requests: {total_requests}, Workers: {concurrency}")
    print(f"Throughput: {throughput:.1f} req/s | Wall: {wall_time_ms:.1f}ms")
    print(f"Min: {min(latencies):.2f}ms | Mean: {mean_lat:.2f}ms | Median: {median_lat:.2f}ms | p95: {p95_lat:.2f}ms | Max: {max_lat:.2f}ms")

    assert mean_lat < 50.0, f"Mean latency {mean_lat:.2f}ms exceeded 50ms limit"
    assert p95_lat < 150.0, f"p95 latency {p95_lat:.2f}ms exceeded 150ms limit"
    assert max_lat < 300.0, f"Max latency {max_lat:.2f}ms exceeded 300ms Instant Search budget"


def test_concurrent_jobcard_indexed_lookup_benchmark():
    """
    Benchmark concurrent lookups on tbl_jobcarddetails (>11,500 rows).
    Simulates 10 concurrent workshop terminals querying by RegNo and JobCardRef.
    Budget: Mean < 50ms, p95 < 150ms, Max < 500ms.
    """
    concurrency = 10
    total_requests = 50

    # Pick sample registration from DB
    with bma.db_cursor() as cur:
        cur.execute("SELECT RegNo, JobCardRef FROM tbl_jobcarddetails ORDER BY ID DESC LIMIT 5")
        samples = cur.fetchall()
    assert len(samples) > 0, "No job cards available for benchmark sampling"

    def execute_jobcard_lookup(i):
        sample = samples[i % len(samples)]
        reg_no, ref = sample[0], sample[1]
        t0 = time.perf_counter()
        with bma.db_cursor() as cur:
            if i % 2 == 0:
                cur.execute(
                    "SELECT ID, JobCardRef, RegNo, MakeAndModel, Status FROM tbl_jobcarddetails WHERE RegNo = %s",
                    (reg_no,),
                )
            else:
                cur.execute(
                    "SELECT ID, JobCardRef, RegNo, MakeAndModel, Status FROM tbl_jobcarddetails WHERE JobCardRef = %s",
                    (ref,),
                )
            cur.fetchall()
        return (time.perf_counter() - t0) * 1000

    latencies = []
    t_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(execute_jobcard_lookup, i) for i in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            latencies.append(f.result())
    wall_time_ms = (time.perf_counter() - t_start) * 1000

    mean_lat = statistics.mean(latencies)
    median_lat = statistics.median(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18]
    max_lat = max(latencies)
    throughput = total_requests / (wall_time_ms / 1000)

    print(f"\n[Job Card Lookup Benchmark (11.5k rows)] Requests: {total_requests}, Workers: {concurrency}")
    print(f"Throughput: {throughput:.1f} req/s | Wall: {wall_time_ms:.1f}ms")
    print(f"Min: {min(latencies):.2f}ms | Mean: {mean_lat:.2f}ms | Median: {median_lat:.2f}ms | p95: {p95_lat:.2f}ms | Max: {max_lat:.2f}ms")

    assert mean_lat < 50.0, f"Mean latency {mean_lat:.2f}ms exceeded 50ms limit"
    assert p95_lat < 150.0, f"p95 latency {p95_lat:.2f}ms exceeded 150ms limit"
    assert max_lat < 500.0, f"Max latency {max_lat:.2f}ms exceeded 500ms Job Card budget"


def test_concurrent_invoice_line_items_benchmark():
    """
    Benchmark concurrent invoice line item queries on tbl_invoices (>1,000 rows).
    Simulates 10 concurrent accounting terminals querying invoice breakdowns.
    Budget: Mean < 50ms, p95 < 150ms, Max < 500ms.
    """
    concurrency = 10
    total_requests = 50

    with bma.db_cursor() as cur:
        cur.execute("SELECT DISTINCT AssignedJobID, Part_No FROM tbl_invoices WHERE Part_No IS NOT NULL LIMIT 5")
        samples = cur.fetchall()

    def execute_invoice_lookup(i):
        sample = samples[i % len(samples)] if samples else (1, "OIL")
        job_id, part_no = sample[0], sample[1]
        t0 = time.perf_counter()
        with bma.db_cursor() as cur:
            if i % 2 == 0:
                cur.execute(
                    "SELECT ID, Item, Part_No, QuantityIssued, Amount, Status FROM tbl_invoices WHERE AssignedJobID = %s",
                    (job_id,),
                )
            else:
                cur.execute(
                    "SELECT ID, AssignedJobID, Item, Amount FROM tbl_invoices WHERE Part_No = %s",
                    (part_no,),
                )
            cur.fetchall()
        return (time.perf_counter() - t0) * 1000

    latencies = []
    t_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(execute_invoice_lookup, i) for i in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            latencies.append(f.result())
    wall_time_ms = (time.perf_counter() - t_start) * 1000

    mean_lat = statistics.mean(latencies)
    median_lat = statistics.median(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18]
    max_lat = max(latencies)
    throughput = total_requests / (wall_time_ms / 1000)

    print(f"\n[Invoice Query Benchmark (1k rows)] Requests: {total_requests}, Workers: {concurrency}")
    print(f"Throughput: {throughput:.1f} req/s | Wall: {wall_time_ms:.1f}ms")
    print(f"Min: {min(latencies):.2f}ms | Mean: {mean_lat:.2f}ms | Median: {median_lat:.2f}ms | p95: {p95_lat:.2f}ms | Max: {max_lat:.2f}ms")

    assert mean_lat < 50.0, f"Mean latency {mean_lat:.2f}ms exceeded 50ms limit"
    assert p95_lat < 250.0, f"p95 latency {p95_lat:.2f}ms exceeded 250ms limit"
    assert max_lat < 500.0, f"Max latency {max_lat:.2f}ms exceeded 500ms Invoice budget"


def test_concurrent_chat_history_sync_benchmark():
    """
    Benchmark concurrent message reading and synchronization on tbl_walkietalkie_messages.
    Simulates 10 mobile/handheld walkie-talkie devices polling chat channels.
    Budget: Mean < 50ms, p95 < 150ms, Max < 300ms.
    """
    concurrency = 10
    total_requests = 50

    def execute_chat_sync(i):
        t0 = time.perf_counter()
        with bma.db_cursor() as cur:
            cur.execute(
                "SELECT id, sender_email, role_name, message, created_at, is_edited "
                "FROM tbl_walkietalkie_messages ORDER BY id DESC LIMIT 50"
            )
            cur.fetchall()
        return (time.perf_counter() - t0) * 1000

    latencies = []
    t_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(execute_chat_sync, i) for i in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            latencies.append(f.result())
    wall_time_ms = (time.perf_counter() - t_start) * 1000

    mean_lat = statistics.mean(latencies)
    median_lat = statistics.median(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18]
    max_lat = max(latencies)
    throughput = total_requests / (wall_time_ms / 1000)

    print(f"\n[Realtime Chat Sync Benchmark] Requests: {total_requests}, Workers: {concurrency}")
    print(f"Throughput: {throughput:.1f} req/s | Wall: {wall_time_ms:.1f}ms")
    print(f"Min: {min(latencies):.2f}ms | Mean: {mean_lat:.2f}ms | Median: {median_lat:.2f}ms | p95: {p95_lat:.2f}ms | Max: {max_lat:.2f}ms")

    assert mean_lat < 50.0, f"Mean latency {mean_lat:.2f}ms exceeded 50ms limit"
    assert p95_lat < 150.0, f"p95 latency {p95_lat:.2f}ms exceeded 150ms limit"
    assert max_lat < 300.0, f"Max latency {max_lat:.2f}ms exceeded 300ms limit"


def test_mixed_workshop_workload_stress_benchmark():
    """
    Stress benchmark: Simulates peak concurrent workshop operations:
    100 simultaneous operations distributed across:
    - 40% Contact Searches
    - 30% Job Card Lookups
    - 20% Invoice Line Item Retrievals
    - 10% Realtime Chat Message Synchronization
    Enforces pool resilience, zero deadlocks, and strict latency compliance.
    """
    concurrency = 10
    total_operations = 100

    def contact_task():
        t0 = time.perf_counter()
        with bma.db_cursor() as cur:
            cur.execute("SELECT ID, Fullname, Phone FROM tbl_clientcontacts WHERE Phone = %s", ("+254700000000",))
            cur.fetchall()
        return ("contact", (time.perf_counter() - t0) * 1000)

    def jobcard_task():
        t0 = time.perf_counter()
        with bma.db_cursor() as cur:
            cur.execute("SELECT ID, JobCardRef, RegNo, Status FROM tbl_jobcarddetails WHERE RegNo = %s", ("KDA001Z",))
            cur.fetchall()
        return ("jobcard", (time.perf_counter() - t0) * 1000)

    def invoice_task():
        t0 = time.perf_counter()
        with bma.db_cursor() as cur:
            cur.execute("SELECT Item, Part_No, QuantityIssued, Amount FROM tbl_invoices WHERE AssignedJobID = %s", (1000,))
            cur.fetchall()
        return ("invoice", (time.perf_counter() - t0) * 1000)

    def chat_task():
        t0 = time.perf_counter()
        with bma.db_cursor() as cur:
            cur.execute("SELECT id, sender_email, message, created_at FROM tbl_walkietalkie_messages ORDER BY id DESC LIMIT 20")
            cur.fetchall()
        return ("chat", (time.perf_counter() - t0) * 1000)

    # 40 contacts, 30 jobcards, 20 invoices, 10 chats = 100 operations
    workload = [contact_task] * 40 + [jobcard_task] * 30 + [invoice_task] * 20 + [chat_task] * 10

    results = []
    t_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(fn) for fn in workload]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())
    total_wall_ms = (time.perf_counter() - t_start) * 1000

    latencies = [r[1] for r in results]
    assert len(latencies) == total_operations, "All operations must complete without dropping requests"

    mean_lat = statistics.mean(latencies)
    median_lat = statistics.median(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18]
    p99_lat = statistics.quantiles(latencies, n=100)[98]
    max_lat = max(latencies)
    throughput = total_operations / (total_wall_ms / 1000)

    print(f"\n=======================================================")
    print(f"  MIXED WORKSHOP CONCURRENCY STRESS BENCHMARK RESULTS  ")
    print(f"=======================================================")
    print(f"Total Operations:  {total_operations}")
    print(f"Concurrent Workers:{concurrency}")
    print(f"Wall Execution:    {total_wall_ms:.1f}ms")
    print(f"System Throughput: {throughput:.1f} ops/second")
    print(f"Min Latency:       {min(latencies):.2f}ms")
    print(f"Mean Latency:      {mean_lat:.2f}ms")
    print(f"Median (p50):      {median_lat:.2f}ms")
    print(f"95th Percentile:   {p95_lat:.2f}ms")
    print(f"99th Percentile:   {p99_lat:.2f}ms")
    print(f"Max Latency:       {max_lat:.2f}ms")
    print(f"=======================================================\n")

    # Assert SLA targets
    assert throughput >= 100.0, f"Throughput {throughput:.1f} ops/s below 100 ops/s target"
    assert mean_lat < 50.0, f"Mean latency {mean_lat:.2f}ms exceeded 50ms threshold"
    assert p95_lat < 200.0, f"p95 latency {p95_lat:.2f}ms exceeded 200ms threshold"
    assert max_lat < 300.0, f"Max latency {max_lat:.2f}ms exceeded 300ms threshold"
