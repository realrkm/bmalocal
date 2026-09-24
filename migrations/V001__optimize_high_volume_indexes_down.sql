-- ==============================================================================
-- Rollback Migration: V001__optimize_high_volume_indexes_down.sql
-- Description: Drop indexes added in V001
-- ==============================================================================

ALTER TABLE tbl_jobcarddetails
    DROP INDEX idx_jobcard_regno,
    DROP INDEX idx_jobcard_chassis,
    DROP INDEX idx_jobcard_ref,
    DROP INDEX idx_jobcard_status,
    DROP INDEX idx_jobcard_iscomplete;

ALTER TABLE tbl_clientcontacts
    DROP INDEX idx_clientcontacts_phone,
    DROP INDEX idx_clientcontacts_name;

ALTER TABLE tbl_invoices
    DROP INDEX idx_invoices_partno;
