# BMALocal Database Migration Checklist & Protocol

Follow this checklist strictly whenever making schema modifications (`ALTER TABLE`, `CREATE TABLE`, `DROP COLUMN`) to the BMALocal database.

---

## 1. Pre-Migration Protocol

- [ ] **1. Create Pre-Migration Backup**:
  ```powershell
  # Run mysqldump with timestamped output
  $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
  & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe" -u root -p bmaautoaccessories2017 > "backup_pre_migration_$timestamp.sql"
  ```
- [ ] **2. Write Versioned Migration Script**:
  - Store migration SQL in `migrations/V<number>__<description>.sql` (e.g. `migrations/V004__add_priority_to_jobcards.sql`).
  - Always write an accompanying rollback script: `migrations/V<number>__<description>_down.sql`.
- [ ] **3. Test On Local Scratch / Copy Database**:
  - Apply the migration script against a test copy of `bmaautoaccessories2017`.
  - Verify that existing records retain data integrity and default values apply properly.

---

## 2. Execution Protocol

- [ ] **4. Check Server Activity**: Ensure no active long-running transactions are in flight in [logs/service_output.log](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/logs/service_output.log).
- [ ] **5. Execute Migration Script**:
  ```powershell
  Get-Content "migrations/V004__add_priority_to_jobcards.sql" | mysql -u root -p bmaautoaccessories2017
  ```
- [ ] **6. Verify Row Counts & Constraints**:
  - Run `SELECT COUNT(*) FROM <table_name>` to verify no data was lost.
  - Run `DESCRIBE <table_name>` to verify columns and data types.

---

## 3. Post-Migration Verification

- [ ] **7. Update Schema Documentation**: Update [references/schema.md](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-database-ops/references/schema.md) with the new columns, foreign keys, or indexes.
- [ ] **8. Run Automated Test Suite**:
  - Execute unit tests: `pytest tests/unit/`
  - Run Playwright E2E tests: `npx playwright test`
- [ ] **9. Commit Schema & Migration in Same PR**: Commit the migration SQL, code changes, and updated schema reference in a single commit.
