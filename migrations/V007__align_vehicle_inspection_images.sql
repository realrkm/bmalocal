-- Align the legacy image table with the columns used by save_update_vehicle_inspection.
ALTER TABLE `tbl_vehicleinspectionimages`
    CHANGE COLUMN `jobcardref_id` `JobCardRefID` INT NOT NULL,
    CHANGE COLUMN `image_url` `ImagePath` VARCHAR(1024) NOT NULL,
    ADD COLUMN `ImageCode` VARCHAR(20) NULL AFTER `JobCardRefID`,
    ADD COLUMN `UpdatedAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP;

UPDATE `tbl_vehicleinspectionimages` AS image
JOIN (
    SELECT
        `ID`,
        CONCAT(
            'image_',
            ROW_NUMBER() OVER (PARTITION BY `JobCardRefID` ORDER BY `ID`)
        ) AS `ImageCode`
    FROM `tbl_vehicleinspectionimages`
) AS ranked ON ranked.`ID` = image.`ID`
SET image.`ImageCode` = ranked.`ImageCode`;

ALTER TABLE `tbl_vehicleinspectionimages`
    MODIFY COLUMN `ImageCode` VARCHAR(20) NOT NULL,
    ADD UNIQUE KEY `uq_vehicle_inspection_image` (`JobCardRefID`, `ImageCode`),
    ADD CONSTRAINT `tbl_vehicleinspectionimages_ibfk_1`
        FOREIGN KEY (`JobCardRefID`) REFERENCES `tbl_jobcarddetails` (`ID`)
        ON DELETE CASCADE ON UPDATE CASCADE;
