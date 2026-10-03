-- ==============================================================================
-- Migration: V002__notification_table_indexes.sql
-- Description: Add missing indexes on notification tables polled frequently
-- Target Tables: tbl_notifications, tbl_incomplete_defects, tbl_technician_portal_notifications
-- Database: bmaautoaccessories2017
-- ==============================================================================

-- 1. tbl_notifications: Accelerate 30s background polling & status updates
ALTER TABLE tbl_notifications
    ADD INDEX idx_notifications_active_created (active, created_at DESC),
    ADD INDEX idx_notifications_jobcard_created (jobcard, created_at);

-- 2. tbl_incomplete_defects: Accelerate polling & update queries
ALTER TABLE tbl_incomplete_defects
    ADD INDEX idx_incomp_defects_active_created (active, created_at DESC),
    ADD INDEX idx_incomp_defects_jobcard_created (jobcard, created_at);

-- 3. tbl_technician_portal_notifications: Accelerate technician polling & updates
ALTER TABLE tbl_technician_portal_notifications
    ADD INDEX idx_technotif_active_created (active, created_at DESC),
    ADD INDEX idx_technotif_jobcard_created (jobcard, created_at);
