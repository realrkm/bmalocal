-- ==============================================================================
-- Migration: V001__optimize_high_volume_indexes.sql
-- Description: Add missing indexes on high-volume search and filter columns
-- Target Tables: tbl_jobcarddetails, tbl_clientcontacts, tbl_invoices
-- Database: bmaautoaccessories2017
-- ==============================================================================

-- 1. tbl_jobcarddetails: Eliminate full table scans on search & status workflows
ALTER TABLE tbl_jobcarddetails
    ADD INDEX idx_jobcard_regno (RegNo),
    ADD INDEX idx_jobcard_chassis (ChassisNo),
    ADD INDEX idx_jobcard_ref (JobCardRef),
    ADD INDEX idx_jobcard_status (Status),
    ADD INDEX idx_jobcard_iscomplete (IsComplete);

-- 2. tbl_clientcontacts: Accelerate client search by phone number and full name
ALTER TABLE tbl_clientcontacts
    ADD INDEX idx_clientcontacts_phone (Phone),
    ADD INDEX idx_clientcontacts_name (Fullname(50));

-- 3. tbl_invoices: Accelerate invoice part lookups
ALTER TABLE tbl_invoices
    ADD INDEX idx_invoices_partno (Part_No);
