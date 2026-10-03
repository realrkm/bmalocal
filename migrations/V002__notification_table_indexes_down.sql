-- ==============================================================================
-- Rollback Migration: V002__notification_table_indexes_down.sql
-- Description: Drop indexes added in V002
-- Target Tables: tbl_notifications, tbl_incomplete_defects, tbl_technician_portal_notifications
-- Database: bmaautoaccessories2017
-- ==============================================================================

ALTER TABLE tbl_notifications
    DROP INDEX idx_notifications_active_created,
    DROP INDEX idx_notifications_jobcard_created;

ALTER TABLE tbl_incomplete_defects
    DROP INDEX idx_incomp_defects_active_created,
    DROP INDEX idx_incomp_defects_jobcard_created;

ALTER TABLE tbl_technician_portal_notifications
    DROP INDEX idx_technotif_active_created,
    DROP INDEX idx_technotif_jobcard_created;
