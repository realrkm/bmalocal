-- Restore the column schema; values removed by the up migration cannot be recovered.
ALTER TABLE `tbl_technicianinspectionchecklist`
    ADD COLUMN `PreparedByStaff` VARCHAR(255) DEFAULT NULL AFTER `FieldsJSON`;
