-- Migration: Create tbl_technicianinspectionchecklist for Vehicle Inspection Checklist
CREATE TABLE IF NOT EXISTS `tbl_technicianinspectionchecklist` (
    `ID` INT NOT NULL AUTO_INCREMENT,
    `JobCardRefID` INT NOT NULL,
    `ItemCode` VARCHAR(10) NOT NULL COMMENT 'e.g. A1, B1, C6, E1',
    `SectionCode` CHAR(1) NOT NULL COMMENT 'A, B, C, D, or E',
    `SectionTitle` VARCHAR(255) NOT NULL,
    `ItemDescription` TEXT NOT NULL,
    `IsChecked` TINYINT(1) NOT NULL DEFAULT 0,
    `FieldsJSON` JSON DEFAULT NULL COMMENT 'Array of {name, label, value} objects for inline inputs',
    `PreparedByStaff` VARCHAR(255) DEFAULT NULL,
    `UpdatedAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`ID`),
    UNIQUE KEY `uq_jobcard_item` (`JobCardRefID`, `ItemCode`),
    KEY `idx_checklist_jobcard` (`JobCardRefID`),
    CONSTRAINT `tbl_technicianinspectionchecklist_ibfk_1`
        FOREIGN KEY (`JobCardRefID`) REFERENCES `tbl_jobcarddetails` (`ID`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

