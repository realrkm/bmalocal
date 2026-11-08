-- Migration: Store vehicle inspection photo paths separately from checklist values
CREATE TABLE IF NOT EXISTS `tbl_vehicleinspectionimages` (
    `ID` INT NOT NULL AUTO_INCREMENT,
    `JobCardRefID` INT NOT NULL,
    `ImageCode` VARCHAR(20) NOT NULL COMMENT 'image_1, image_2, or image_3',
    `ImagePath` VARCHAR(1024) NOT NULL,
    `UpdatedAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`ID`),
    UNIQUE KEY `uq_vehicle_inspection_image` (`JobCardRefID`, `ImageCode`),
    CONSTRAINT `tbl_vehicleinspectionimages_ibfk_1`
        FOREIGN KEY (`JobCardRefID`) REFERENCES `tbl_jobcarddetails` (`ID`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
