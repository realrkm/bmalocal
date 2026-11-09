-- Checklist records no longer persist staff identity.
ALTER TABLE `tbl_technicianinspectionchecklist`
    DROP COLUMN `PreparedByStaff`;
