-- Restore the legacy column names while preserving saved image paths.
ALTER TABLE `tbl_vehicleinspectionimages`
    DROP FOREIGN KEY `tbl_vehicleinspectionimages_ibfk_1`,
    DROP INDEX `uq_vehicle_inspection_image`,
    DROP COLUMN `ImageCode`,
    DROP COLUMN `UpdatedAt`,
    CHANGE COLUMN `JobCardRefID` `jobcardref_id` INT NOT NULL,
    CHANGE COLUMN `ImagePath` `image_url` VARCHAR(1024) NOT NULL;
