# BMALocal MySQL Database Schema Reference

**Database Name**: `bmaautoaccessories2017`  
**Total Tables**: 67 | **Total Columns**: 401 | **Foreign Keys**: 30  
**Primary Engine**: InnoDB | **Default Collation**: `utf8mb4_general_ci` / `latin1_swedish_ci`  
**Verified Timestamp**: 2026-09-24 via `information_schema` live query

---

## 1. Foreign Key Entity-Relationship Map (30 Constraints)

| Source Table | Foreign Key Column | Target Table | Target Column | Constraint Name |
| :--- | :--- | :--- | :--- | :--- |
| `tbl_additionalservices` | `ServiceProviderID` | `tbl_serviceprovider` | `ID` | `tbl_additionalservices_ibfk_1` |
| `tbl_appointmentbooking` | `ClientID` | `tbl_clientcontacts` | `ID` | `tbl_appointmentbooking_ibfk_1` |
| `tbl_arrearspayment` | `JobCardRefID` | `tbl_jobcarddetails` | `ID` | `tbl_arrearspayment_ibfk_1` |
| `tbl_assignedcarparts` | `AssignedJobID` | `tbl_jobcarddetails` | `ID` | `tbl_assignedcarparts_ibfk_1` |
| `tbl_assignedcarparts` | `CarPartID` | `tbl_carpartnames` | `ID` | `tbl_assignedcarparts_ibfk_2` |
| `tbl_assignedservices` | `CompletedJobCardID` | `tbl_jobcarddetails` | `ID` | `tbl_assignedservices_ibfk_2` |
| `tbl_assignedservices` | `ServiceNameID` | `tbl_additionalservices` | `ID` | `tbl_assignedservices_ibfk_1` |
| `tbl_assignedspecialtool` | `SpecialToolID` | `tbl_specialtools` | `ID` | `tbl_assignedspecialtool_ibfk_1` |
| `tbl_assignedspecialtool` | `TechnicianID` | `tbl_technicians` | `ID` | `tbl_assignedspecialtool_ibfk_3` |
| `tbl_cancelledjobcards` | `AssignedJobID` | `tbl_jobcarddetails` | `ID` | `tbl_cancelledjobcards_ibfk_1` |
| `tbl_carpartnames` | `Location` | `tbl_carpartslocation` | `ID` | `tbl_carpartnames_ibfk_2` |
| `tbl_clientquotationfeedback` | `AssignedJobID` | `tbl_jobcarddetails` | `ID` | `tbl_clientquotationfeedback_ibfk_1` |
| `tbl_completedjobcards` | `AssignedJobCardID` | `tbl_jobcarddetails` | `ID` | `tbl_completedjobcards_ibfk_1` |
| `tbl_deposits` | `JobCardRefID` | `tbl_jobcarddetails` | `ID` | `tbl_deposits_ibfk_1` |
| `tbl_importordertracking` | `ClientID` | `tbl_clientcontacts` | `ID` | `tbl_importordertracking_ibfk_1` |
| `tbl_invoices` | `AssignedJobID` | `tbl_jobcarddetails` | `ID` | `tbl_invoices_ibfk_1` |
| `tbl_jobcarddetails` | `CheckedInBy` | `tbl_checkstaff` | `ID` | `tbl_jobcarddetails_ibfk_2` |
| `tbl_jobcarddetails` | `ClientDetails` | `tbl_clientcontacts` | `ID` | `tbl_jobcarddetails_ibfk_1` |
| `tbl_monthlyschedule` | `AssignedJobID` | `tbl_jobcarddetails` | `ID` | `tbl_monthlyschedule_ibfk_1` |
| `tbl_payments` | `JobCardRefID` | `tbl_jobcarddetails` | `ID` | `tbl_payments_ibfk_1` |
| `tbl_pendingassignedjobs` | `JobCardRefID` | `tbl_jobcarddetails` | `ID` | `tbl_pendingassignedjobs_ibfk_1` |
| `tbl_pendingassignedjobs` | `TechnicianID` | `tbl_technicians` | `ID` | `tbl_pendingassignedjobs_ibfk_2` |
| `tbl_quotation` | `AssignedJobID` | `tbl_jobcarddetails` | `ID` | `tbl_quotation_ibfk_1` |
| `tbl_quotationpartsandservicesfeedback` | `AssignedJobID` | `tbl_jobcarddetails` | `ID` | `tbl_quotationpartsandservicesfeedback_ibfk_1` |
| `tbl_quotationpartsandservicesfeedback` | `ClientQuotationFeedbackID` | `tbl_clientquotationfeedback` | `ID` | `tbl_quotationpartsandservicesfeedback_ibfk_2` |
| `tbl_signedjobcards` | `AssignedJobID` | `tbl_jobcarddetails` | `ID` | `fk_signedjobcards_jobcard` |
| `tbl_stockparts` | `CarPart` | `tbl_carpartnames` | `ID` | `tbl_stockparts_ibfk_1` |
| `tbl_stockparts` | `CarPartsSupplierID` | `tbl_carpartssupplier` | `ID` | `fk_stockparts_supplier` |
| `tbl_techniciandefectsandrequestedparts` | `JobCardRefID` | `tbl_jobcarddetails` | `ID` | `tbl_techniciandefectsandrequestedparts_ibfk_1` |
| `tbl_userpermissions` | `RoleID` | `tbl_roles` | `ID` | `tbl_userpermissions_ibfk_1` |

---

## 2. Core Operational Domains & Table Definitions

## Job Cards & Workshop Lifecycle

### `tbl_jobcarddetails`
**Rows**: 11,723 | **Engine**: InnoDB | **Collation**: utf8mb3_general_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `ClientDetails` | `int` | NO | MUL | NULL |  | `tbl_clientcontacts.ID` |
| 3 | `JobCardRef` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `ReceivedDate` | `date` | NO |  | NULL |  |  |
| 5 | `DueDate` | `date` | NO |  | NULL |  |  |
| 6 | `ExpDate` | `date` | YES |  | NULL |  |  |
| 7 | `CheckedInBy` | `int` | NO | MUL | NULL |  | `tbl_checkstaff.ID` |
| 8 | `Ins` | `bit(1)` | NO |  | NULL |  |  |
| 9 | `Comp` | `bit(1)` | YES |  | NULL |  |  |
| 10 | `TPO` | `bit(1)` | YES |  | NULL |  |  |
| 11 | `Spare` | `bit(1)` | YES |  | NULL |  |  |
| 12 | `Jack` | `bit(1)` | YES |  | NULL |  |  |
| 13 | `Brace` | `bit(1)` | YES |  | NULL |  |  |
| 14 | `RegNo` | `varchar(255)` | NO |  | NULL |  |  |
| 15 | `MakeAndModel` | `varchar(255)` | NO |  | NULL |  |  |
| 16 | `ChassisNo` | `varchar(255)` | YES |  | NULL |  |  |
| 17 | `EngineCC` | `varchar(255)` | YES |  | NULL |  |  |
| 18 | `Mileage` | `int` | YES |  | NULL |  |  |
| 19 | `EngineNo` | `varchar(255)` | YES | MUL | NULL |  |  |
| 20 | `EngineCode` | `varchar(255)` | YES |  | NULL |  |  |
| 21 | `Manual` | `bit(1)` | YES |  | NULL |  |  |
| 22 | `Auto` | `bit(1)` | YES |  | NULL |  |  |
| 23 | `Empty` | `bit(1)` | YES |  | NULL |  |  |
| 24 | `Quarter` | `bit(1)` | YES |  | NULL |  |  |
| 25 | `Half` | `bit(1)` | YES |  | NULL |  |  |
| 26 | `ThreeQuarter` | `bit(1)` | YES |  | NULL |  |  |
| 27 | `Full` | `bit(1)` | YES |  | NULL |  |  |
| 28 | `PaintCode` | `varchar(255)` | YES |  | NULL |  |  |
| 29 | `ClientInstruction` | `text` | NO |  | NULL |  |  |
| 30 | `Notes` | `text` | NO |  | NULL |  |  |
| 31 | `IsComplete` | `bit(1)` | YES |  | NULL |  |  |
| 32 | `Status` | `varchar(255)` | YES |  | NULL |  |  |

### `tbl_completedjobcards`
**Rows**: 131 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `AssignedJobCardID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 3 | `Remarks` | `text` | NO |  | NULL |  |  |
| 4 | `Signature` | `blob` | NO |  | NULL |  |  |
| 5 | `DateCompleted` | `datetime` | NO |  | NULL |  |  |

### `tbl_cancelledjobcards`
**Rows**: 4 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `AssignedJobID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 3 | `Reason` | `text` | NO |  | NULL |  |  |
| 4 | `CreatedAt` | `datetime` | NO |  | NULL |  |  |

### `tbl_signedjobcards`
**Rows**: 8 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `AssignedJobID` | `int` | NO | UNI | NULL |  | `tbl_jobcarddetails.ID` |
| 3 | `Signature` | `longblob` | NO |  | NULL |  |  |
| 4 | `CreatedAt` | `timestamp` | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |  |

### `tbl_workdoneinjobcard`
**Rows**: 41 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `JobCardRefID` | `int` | NO | MUL | NULL |  |  |
| 3 | `WorkDone` | `text` | NO |  | NULL |  |  |

### `tbl_techniciandefectsandrequestedparts`
**Rows**: 289 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `JobCardRefID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 3 | `TechnicianPortalRequestedParts` | `text` | YES |  | NULL |  |  |
| 4 | `Defects` | `text` | NO |  | NULL |  |  |
| 5 | `PricedDefectsList` | `text` | YES |  | NULL |  |  |
| 6 | `RequestedParts` | `text` | YES |  | NULL |  |  |
| 7 | `PreparedByStaff` | `varchar(255)` | NO |  | NULL |  |  |
| 8 | `Signature` | `longblob` | YES |  | NULL |  |  |

### `tbl_incomplete_defects`
**Rows**: 44 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `id` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `jobcard` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `message` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `role` | `int` | NO | MUL | NULL |  |  |
| 5 | `created_at` | `datetime` | NO | MUL | NULL |  |  |
| 6 | `active` | `tinyint(1)` | NO | MUL | 1 |  |  |

### `tbl_repairpriorities`
**Rows**: 30 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Date` | `date` | NO |  | NULL |  |  |
| 3 | `RegNo` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `PartName` | `varchar(255)` | NO |  | NULL |  |  |
| 5 | `PartNumber` | `varchar(255)` | YES |  | NULL |  |  |
| 6 | `Quantity` | `int` | YES |  | NULL |  |  |
| 7 | `Amount` | `decimal(10,2)` | NO |  | NULL |  |  |
| 8 | `Priority` | `varchar(255)` | NO |  | NULL |  |  |

## Billing, Quotations & Financials

### `tbl_invoices`
**Rows**: 1,014 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Date` | `date` | NO |  | NULL |  |  |
| 3 | `AssignedJobID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 4 | `Item` | `text` | NO |  | NULL |  |  |
| 5 | `Part_No` | `varchar(255)` | YES |  | NULL |  |  |
| 6 | `QuantityIssued` | `float` | YES |  | NULL |  |  |
| 7 | `Amount` | `decimal(10,2)` | NO |  | NULL |  |  |
| 8 | `Status` | `text` | NO |  | NULL |  |  |

### `tbl_quotation`
**Rows**: 1,233 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Date` | `date` | NO |  | NULL |  |  |
| 3 | `AssignedJobID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 4 | `Item` | `text` | NO |  | NULL |  |  |
| 5 | `Part_No` | `varchar(255)` | YES |  | NULL |  |  |
| 6 | `QuantityIssued` | `float` | YES |  | NULL |  |  |
| 7 | `Amount` | `decimal(10,0)` | NO |  | NULL |  |  |

### `tbl_quotationpartsandservicesfeedback`
**Rows**: 1,018 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Date` | `date` | NO |  | NULL |  |  |
| 3 | `AssignedJobID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 4 | `Item` | `text` | NO |  | NULL |  |  |
| 5 | `Part_No` | `varchar(255)` | YES |  | NULL |  |  |
| 6 | `QuantityIssued` | `float` | YES |  | NULL |  |  |
| 7 | `Amount` | `decimal(10,2)` | NO |  | NULL |  |  |
| 8 | `ClientQuotationFeedbackID` | `int` | NO | MUL | NULL |  | `tbl_clientquotationfeedback.ID` |

### `tbl_clientquotationfeedback`
**Rows**: 263 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `AssignedJobID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 3 | `Remarks` | `text` | NO |  | NULL |  |  |

### `tbl_payments`
**Rows**: 186 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Date` | `date` | NO |  | NULL |  |  |
| 3 | `JobCardRefID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 4 | `PaymentMode` | `text` | NO |  | NULL |  |  |
| 5 | `AmountPaid` | `decimal(10,0)` | NO |  | NULL |  |  |
| 6 | `Discount` | `decimal(10,0)` | YES |  | NULL |  |  |
| 7 | `Balance` | `decimal(10,0)` | NO |  | NULL |  |  |

### `tbl_arrearspayment`
**Rows**: 2 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `ArrearsDate` | `date` | NO |  | NULL |  |  |
| 3 | `JobCardRefID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 4 | `OutstandingAmount` | `int` | NO |  | NULL |  |  |
| 5 | `DateArrearsPaid` | `date` | YES |  | NULL |  |  |
| 6 | `FinalArrearsAmountPaid` | `int` | YES |  | NULL |  |  |

### `tbl_deposits`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `DepositDate` | `date` | NO |  | NULL |  |  |
| 3 | `JobCardRefID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 4 | `Amount` | `int` | NO |  | NULL |  |  |

### `tbl_sales`
**Rows**: 2 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `SaleDate` | `date` | NO |  | NULL |  |  |
| 3 | `CompletedJobCardID` | `int` | NO | MUL | NULL |  |  |
| 4 | `TotalDues` | `int` | NO |  | NULL |  |  |
| 5 | `TotalPaid` | `int` | NO |  | NULL |  |  |
| 6 | `ArrearsComments` | `varchar(20)` | NO |  | NULL |  |  |

### `tbl_salesitemsbilled`
**Rows**: 11 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Item` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `Quantity` | `int` | YES |  | NULL |  |  |
| 4 | `Rate` | `int` | YES |  | NULL |  |  |
| 5 | `Total` | `int` | YES |  | NULL |  |  |
| 6 | `JobCardRefID` | `int` | NO | MUL | NULL |  |  |

### `tbl_saleitemsbilledtotals`
**Rows**: 3 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `JobCardRefID` | `int` | NO | MUL | NULL |  |  |
| 3 | `InvoiceDate` | `date` | NO |  | NULL |  |  |
| 4 | `Total` | `int` | NO |  | NULL |  |  |
| 5 | `Payment` | `int` | NO |  | NULL |  |  |
| 6 | `Balance` | `int` | NO |  | NULL |  |  |

## Clients & Booking Management

### `tbl_clientcontacts`
**Rows**: 2,658 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Fullname` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `Phone` | `varchar(20)` | NO |  | NULL |  |  |
| 4 | `Address` | `varchar(255)` | NO |  | NULL |  |  |
| 5 | `Email` | `varchar(255)` | NO |  | NULL |  |  |
| 6 | `Narration` | `varchar(255)` | NO |  | NULL |  |  |

### `tbl_appointmentbooking`
**Rows**: 12 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `ClientID` | `int` | NO | MUL | NULL |  | `tbl_clientcontacts.ID` |
| 3 | `RegNo` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `Period` | `datetime` | NO |  | NULL |  |  |
| 5 | `Details` | `text` | NO |  | NULL |  |  |
| 6 | `IsSent` | `bit(1)` | NO |  | NULL |  |  |

### `tbl_importordertracking`
**Rows**: 8 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `OrderDate` | `date` | NO |  | NULL |  |  |
| 3 | `ClientID` | `int` | NO | MUL | NULL |  | `tbl_clientcontacts.ID` |
| 4 | `PartName` | `varchar(255)` | NO |  | NULL |  |  |
| 5 | `PartNumber` | `varchar(255)` | NO |  | NULL |  |  |
| 6 | `Quantity` | `float` | NO |  | NULL |  |  |
| 7 | `Brand` | `varchar(255)` | NO |  | NULL |  |  |
| 8 | `Status` | `varchar(30)` | NO |  | NULL |  |  |

## Inventory, Spare Parts & Warehousing

### `tbl_stockparts`
**Rows**: 12,938 | **Engine**: InnoDB | **Collation**: utf8mb3_general_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Date` | `date` | NO | MUL | NULL |  |  |
| 3 | `CarPart` | `int` | NO | MUL | NULL |  | `tbl_carpartnames.ID` |
| 4 | `CarPartsSupplierID` | `int` | YES | MUL | NULL |  | `tbl_carpartssupplier.ID` |
| 5 | `NoOfUnits` | `double` | YES |  | NULL |  |  |
| 6 | `UnitCost` | `int` | NO |  | NULL |  |  |
| 7 | `Narration` | `varchar(255)` | NO |  | NULL |  |  |

### `tbl_assignedcarparts`
**Rows**: 16,060 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Date` | `date` | NO | MUL | NULL |  |  |
| 3 | `AssignedJobID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 4 | `CarPartID` | `int` | NO | MUL | NULL |  | `tbl_carpartnames.ID` |
| 5 | `QuantityIssued` | `double` | NO |  | NULL |  |  |

### `tbl_carpartnames`
**Rows**: 3,003 | **Engine**: InnoDB | **Collation**: utf8mb3_general_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Name` | `varchar(100)` | NO | MUL | NULL |  |  |
| 3 | `PartNo` | `varchar(100)` | NO | MUL | NULL |  |  |
| 4 | `OrderLevel` | `int` | NO |  | NULL |  |  |
| 5 | `Location` | `int` | YES | MUL | NULL |  | `tbl_carpartslocation.ID` |
| 6 | `Category` | `varchar(100)` | YES |  | NULL |  |  |

### `tbl_carpartslocation`
**Rows**: 43 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Location` | `varchar(255)` | NO | MUL | NULL |  |  |

### `tbl_carpartssupplier`
**Rows**: 52 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Name` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `Phone` | `varchar(20)` | NO |  | NULL |  |  |

### `tbl_partssellingprice`
**Rows**: 1,373 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `SetPriceDate` | `date` | NO |  | NULL |  |  |
| 3 | `CarPartsNamesID` | `int` | NO | UNI | NULL |  |  |
| 4 | `Amount` | `int` | NO |  | NULL |  |  |
| 5 | `SaleDiscount` | `int` | YES |  | NULL |  |  |

### `tbl_barcodepartnomapping`
**Rows**: 11 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Barcode` | `varchar(255)` | NO | MUL | NULL |  |  |
| 3 | `PartNo` | `varchar(255)` | NO |  | NULL |  |  |

### `tbl_brandcomparison`
**Rows**: 54 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Date` | `date` | NO |  | NULL |  |  |
| 3 | `RegNo` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `PartName` | `varchar(255)` | NO |  | NULL |  |  |
| 5 | `PartNumber` | `varchar(255)` | YES |  | NULL |  |  |
| 6 | `Quantity` | `float` | YES |  | NULL |  |  |
| 7 | `Amount` | `decimal(10,2)` | NO |  | NULL |  |  |
| 8 | `GroupID` | `varchar(255)` | NO |  | NULL |  |  |

### `tbl_finalcapturedstocktaking`
**Rows**: 6,358 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `CountingDate` | `date` | NO |  | NULL |  |  |
| 3 | `CarPart` | `varchar(255)` | NO | MUL | NULL |  |  |
| 4 | `PartNumber` | `varchar(255)` | NO |  | NULL |  |  |
| 5 | `ReorderLevel` | `int` | NO |  | NULL |  |  |
| 6 | `Location` | `varchar(255)` | YES |  | NULL |  |  |
| 7 | `Balance` | `decimal(10,2)` | NO |  | NULL |  |  |
| 8 | `CapturedQuantity` | `decimal(10,2)` | YES |  | NULL |  |  |
| 9 | `Variance` | `decimal(10,2)` | YES |  | NULL |  |  |
| 10 | `Comment` | `varchar(255)` | YES |  | NULL |  |  |

### `tbl_tempstockharmonized`
**Rows**: 34 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Location` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `CarPartID` | `int` | YES | MUL | NULL |  |  |
| 4 | `CarPart` | `text` | NO |  | NULL |  |  |
| 5 | `PartNumber` | `text` | NO |  | NULL |  |  |
| 6 | `HarmonizedValue` | `decimal(10,2)` | YES |  | NULL |  |  |

### `tbl_stocktakeharmonized`
**Rows**: 176 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `StockTakeDate` | `date` | YES | MUL | NULL |  |  |
| 3 | `CarPartNameID` | `int` | YES | MUL | NULL |  |  |
| 4 | `HarmornizedValue` | `decimal(10,2)` | NO |  | NULL |  |  |
| 5 | `AuthorizedByID` | `int` | YES |  | NULL |  |  |

## Staff, Technicians & Toolkits

### `tbl_technicians`
**Rows**: 50 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Fullname` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `Phone` | `varchar(20)` | NO |  | NULL |  |  |
| 4 | `ToolkitID` | `int` | NO | MUL | NULL |  |  |
| 5 | `IsArchived` | `bit(1)` | NO |  | NULL |  |  |

### `tbl_checkstaff`
**Rows**: 16 | **Engine**: InnoDB | **Collation**: utf8mb3_general_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Staff` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `Phone` | `varchar(20)` | NO |  | NULL |  |  |
| 4 | `IsArchived` | `bit(1)` | NO |  | NULL |  |  |

### `tbl_toolkits`
**Rows**: 5 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `ToolkitName` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `Cost` | `int` | NO |  | NULL |  |  |

### `tbl_assignedspecialtool`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `AssignedDate` | `date` | NO |  | NULL |  |  |
| 3 | `SpecialToolID` | `int` | NO | MUL | NULL |  | `tbl_specialtools.ID` |
| 4 | `TechnicianID` | `int` | NO | MUL | NULL |  | `tbl_technicians.ID` |
| 5 | `QuantityIssued` | `int` | NO |  | NULL |  |  |
| 6 | `QuantityReturned` | `int` | YES |  | NULL |  |  |
| 7 | `ReturnedDate` | `date` | YES |  | NULL |  |  |

### `tbl_specialtools`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `ToolName` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `Cost` | `int` | NO |  | NULL |  |  |
| 4 | `Quantity` | `int` | NO |  | NULL |  |  |

### `tbl_serviceprovider`
**Rows**: 7 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Name` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `Phone` | `varchar(20)` | NO |  | NULL |  |  |

### `tbl_additionalservices`
**Rows**: 21 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `ServiceName` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `ServiceProviderID` | `int` | NO | MUL | NULL |  | `tbl_serviceprovider.ID` |

### `tbl_assignedservices`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `ServiceNameID` | `int` | NO | MUL | NULL |  | `tbl_additionalservices.ID` |
| 3 | `CompletedJobCardID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 4 | `Amount` | `int` | NO |  | NULL |  |  |

## Users, Roles, Audit & Security

### `tbl_users`
**Rows**: 7 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `FirstName` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `LastName` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `Username` | `varchar(255)` | NO |  | NULL |  |  |
| 5 | `Password` | `text` | NO |  | NULL |  |  |
| 6 | `Role` | `int` | NO |  | NULL |  |  |
| 7 | `DateCreated` | `datetime` | NO |  | NULL |  |  |
| 8 | `IsActive` | `bit(1)` | NO |  | NULL |  |  |
| 9 | `CreatedBy` | `varchar(255)` | NO |  | NULL |  |  |
| 10 | `PasswordSetPeriod` | `datetime` | NO |  | NULL |  |  |

### `tbl_roles`
**Rows**: 8 | **Engine**: InnoDB | **Collation**: utf8mb3_general_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Roles` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `Description` | `varchar(255)` | NO |  | NULL |  |  |

### `tbl_userpermissions`
**Rows**: 214 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `RoleID` | `int` | NO | MUL | NULL |  | `tbl_roles.ID` |
| 3 | `Section` | `varchar(50)` | NO |  | NULL |  |  |
| 4 | `SubSection` | `varchar(50)` | YES |  | NULL |  |  |
| 5 | `Allowed` | `tinyint(1)` | NO |  | NULL |  |  |

### `tbl_functionalities`
**Rows**: 194 | **Engine**: InnoDB | **Collation**: utf8mb3_general_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `RoleID` | `int` | NO | MUL | NULL |  |  |
| 3 | `AccessModule` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `AllowedAccess` | `varchar(3)` | NO |  | NULL |  |  |

### `tbl_usersaudit`
**Rows**: 4,261 | **Engine**: InnoDB | **Collation**: utf8mb3_general_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `LoggedInUser` | `int` | NO | MUL | NULL |  |  |
| 3 | `TimeLoggedIn` | `datetime(6)` | NO |  | NULL |  |  |
| 4 | `TimeLoggedOut` | `datetime(6)` | YES |  | NULL |  |  |
| 5 | `IsLoggedIn` | `tinyint(1)` | NO |  | NULL |  |  |
| 6 | `ComputerAccount` | `varchar(255)` | NO |  | NULL |  |  |
| 7 | `LoggedOutBy` | `varchar(255)` | YES |  | NULL |  |  |

### `tbl_rolefunctionalitiesaudit`
**Rows**: 194 | **Engine**: InnoDB | **Collation**: utf8mb3_general_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `RoleID` | `int` | NO | MUL | NULL |  |  |
| 3 | `AccessModule` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `AllowedAccess` | `varchar(3)` | NO |  | NULL |  |  |
| 5 | `EmpoweredBy` | `varchar(255)` | NO |  | NULL |  |  |
| 6 | `DateEmpowered` | `datetime(6)` | NO |  | NULL |  |  |

### `tbl_logfailedattempts`
**Rows**: 15 | **Engine**: InnoDB | **Collation**: utf8mb3_general_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Username` | `int` | NO | MUL | NULL |  |  |
| 3 | `FailedAttemptedWhen` | `datetime` | NO |  | NULL |  |  |
| 4 | `WaitingMinutes` | `smallint` | NO |  | NULL |  |  |
| 5 | `WaitExpired` | `tinyint(1)` | NO |  | NULL |  |  |

## Communications, Walkie-Talkie & Notifications

### `tbl_walkietalkie_messages`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `id` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `sender_email` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `role_name` | `varchar(100)` | YES |  |  |  |  |
| 4 | `message` | `text` | NO |  | NULL |  |  |
| 5 | `created_at` | `datetime` | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |  |
| 6 | `is_edited` | `tinyint(1)` | NO |  | 0 |  |  |

### `tbl_walkietalkie_reads`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `user_email` | `varchar(255)` | NO | PRI | NULL |  |  |
| 2 | `last_read_id` | `int` | NO |  | 0 |  |  |
| 3 | `last_read_at` | `datetime` | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |  |

### `tbl_notifications`
**Rows**: 54 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `id` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `jobcard` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `message` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `role` | `int` | NO | MUL | NULL |  |  |
| 5 | `created_at` | `datetime` | NO | MUL | NULL |  |  |
| 6 | `active` | `tinyint(1)` | NO | MUL | 1 |  |  |

### `tbl_technician_portal_notifications`
**Rows**: 67 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `id` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `jobcard` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `message` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `role` | `int` | NO | MUL | NULL |  |  |
| 5 | `created_at` | `datetime` | NO | MUL | NULL |  |  |
| 6 | `active` | `tinyint(1)` | NO | MUL | 1 |  |  |

### `tbl_sms`
**Rows**: 22 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `id` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `fullname` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `phone` | `varchar(20)` | NO |  | NULL |  |  |
| 4 | `message` | `text` | NO |  | NULL |  |  |
| 5 | `jobcardrefID` | `int` | NO |  | NULL |  |  |
| 6 | `document` | `varchar(20)` | NO |  | NULL |  |  |
| 7 | `flag` | `tinyint(1)` | YES |  | 1 |  |  |
| 8 | `created_at` | `timestamp` | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |  |

### `tbl_faqs`
**Rows**: 13 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Question` | `text` | NO |  | NULL |  |  |
| 3 | `Answer` | `text` | NO |  | NULL |  |  |

## Auxiliary & Temporary Tables

### `tbl_archiveduplicatecarpart`
**Rows**: 1 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `CapturedRowID` | `int` | NO |  | NULL |  |  |
| 3 | `CarPartName` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `PartNo` | `varchar(255)` | NO |  | NULL |  |  |
| 5 | `Supplier` | `varchar(255)` | NO |  | NULL |  |  |
| 6 | `OrderLevel` | `int` | NO |  | NULL |  |  |
| 7 | `Location` | `varchar(20)` | NO |  | NULL |  |  |

### `tbl_backuplink`
**Rows**: 1 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Link` | `varchar(255)` | YES |  | NULL |  |  |
| 3 | `Comments` | `varchar(50)` | NO |  | NULL |  |  |

### `tbl_carpart_taxonomy`
**Rows**: 9 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Category` | `varchar(100)` | NO |  | NULL |  |  |
| 3 | `Patterns` | `text` | NO |  | NULL |  |  |

### `tbl_importexcelstockcount`
**Rows**: 2,967 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Location` | `varchar(255)` | YES |  | NULL |  |  |
| 3 | `CarPart` | `varchar(255)` | YES |  | NULL |  |  |
| 4 | `PartNumber` | `varchar(255)` | YES |  | NULL |  |  |
| 5 | `ReorderLevel` | `int` | YES |  | NULL |  |  |
| 6 | `CapturedQuantity` | `float` | YES |  | NULL |  |  |

### `tbl_importexcelstockharmonized`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `CarPart` | `text` | NO |  | NULL |  |  |
| 3 | `PartNumber` | `text` | NO |  | NULL |  |  |
| 4 | `HarmonizedValue` | `decimal(10,2)` | YES |  | NULL |  |  |

### `tbl_monthlyschedule`
**Rows**: 26 | **Engine**: InnoDB | **Collation**: utf8mb4_0900_ai_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Date` | `date` | NO |  | NULL |  |  |
| 3 | `AssignedJobID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 4 | `ClientName` | `varchar(255)` | NO |  | NULL |  |  |
| 5 | `TotalInvoiceAmount` | `float` | NO |  | NULL |  |  |
| 6 | `TotalAmountPaid` | `float` | NO |  | NULL |  |  |
| 7 | `TotalDiscount` | `float` | NO |  | NULL |  |  |
| 8 | `PaymentBalance` | `float` | NO |  | NULL |  |  |
| 9 | `Item` | `text` | NO |  | NULL |  |  |
| 10 | `Part_No` | `varchar(255)` | YES |  | NULL |  |  |
| 11 | `QuantityIssued` | `float` | YES |  | NULL |  |  |
| 12 | `Amount` | `decimal(10,2)` | NO |  | NULL |  |  |
| 13 | `Category` | `text` | NO |  | NULL |  |  |

### `tbl_pendingassignedjobs`
**Rows**: 9,158 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `JobCardRefID` | `int` | NO | MUL | NULL |  | `tbl_jobcarddetails.ID` |
| 3 | `TechnicianID` | `int` | NO | MUL | NULL |  | `tbl_technicians.ID` |
| 4 | `DateAssigned` | `datetime` | NO |  | NULL |  |  |

### `tbl_periodicsalesbilled`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `SaleDate` | `date` | NO |  | NULL |  |  |
| 3 | `JobCardRef` | `int` | NO | MUL | NULL |  |  |
| 4 | `Client` | `varchar(255)` | NO |  | NULL |  |  |
| 5 | `Parts_Service` | `varchar(255)` | NO |  | NULL |  |  |
| 6 | `Cost` | `int` | NO |  | NULL |  |  |

### `tbl_returnjobsactiontaken`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `ReturnJobDate` | `date` | NO |  | NULL |  |  |
| 3 | `OldJobCard` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `Action/NewJobCard` | `varchar(255)` | NO |  | NULL |  |  |

### `tbl_temparchivetechniciantools`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `Tool` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `Cost` | `int` | NO |  | NULL |  |  |
| 4 | `QuantityIssued` | `varchar(10)` | NO |  | NULL |  |  |
| 5 | `IsReturned` | `bit(1)` | NO |  | NULL |  |  |

### `tbl_tempassignedparts`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `CarPartID` | `int` | YES | MUL | NULL |  |  |
| 3 | `QuantityIssued` | `double` | YES |  | NULL |  |  |

### `tbl_tempcapturedstocktaking`
**Rows**: 2,967 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `CarPart` | `varchar(255)` | NO |  | NULL |  |  |
| 3 | `PartNumber` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `ReorderLevel` | `int` | NO |  | NULL |  |  |
| 5 | `Location` | `varchar(255)` | YES |  | NULL |  |  |
| 6 | `CapturedQuantity` | `float` | YES |  | NULL |  |  |
| 7 | `Balance` | `float` | NO |  | NULL |  |  |
| 8 | `Variance` | `float` | YES |  | NULL |  |  |
| 9 | `Comment` | `varchar(255)` | YES |  | NULL |  |  |

### `tbl_temppartsandstockbalances`
**Rows**: 0 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `CarPartID` | `int` | YES |  | NULL |  |  |
| 3 | `QuantityIssued` | `double` | YES |  | NULL |  |  |
| 4 | `TotalStock` | `int` | YES |  | NULL |  |  |
| 5 | `ReorderLevel` | `int` | YES |  | NULL |  |  |
| 6 | `Name` | `varchar(255)` | NO |  | 0 |  |  |
| 7 | `PartNo` | `varchar(255)` | NO |  | 0 |  |  |
| 8 | `OrderLevel` | `int` | YES |  | 0 |  |  |
| 9 | `Bought` | `double` | YES |  | NULL |  |  |
| 10 | `Issued` | `double` | YES |  | NULL |  |  |
| 11 | `Balance` | `double` | NO |  | 0 |  |  |
| 12 | `Comments` | `varchar(20)` | YES |  | NULL |  |  |

### `tbl_tempsalesitemstobebilled`
**Rows**: 1 | **Engine**: InnoDB | **Collation**: latin1_swedish_ci

| # | Column Name | Type | Nullable | Key | Default | Extra | Foreign Key Ref |
| -: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | `ID` | `int` | NO | PRI | NULL | auto_increment |  |
| 2 | `CarPartID` | `int` | YES | MUL | NULL |  |  |
| 3 | `Item` | `varchar(255)` | NO |  | NULL |  |  |
| 4 | `Quantity` | `double` | YES |  | NULL |  |  |
| 5 | `Rate` | `int` | YES |  | NULL |  |  |
| 6 | `Total` | `double` | YES |  | NULL |  |  |

---
## 3. Alphabetical Master Table Index

| Table Name | Rows | Engine | Columns | Foreign Keys | Domain |
| :--- | ---: | :---: | ---: | ---: | :--- |
| `tbl_additionalservices` | 21 | InnoDB | 3 | 1 | Staff, Technicians |
| `tbl_appointmentbooking` | 12 | InnoDB | 6 | 1 | Clients |
| `tbl_archiveduplicatecarpart` | 1 | InnoDB | 7 | 0 | Auxiliary |
| `tbl_arrearspayment` | 2 | InnoDB | 6 | 1 | Billing, Quotations |
| `tbl_assignedcarparts` | 16,060 | InnoDB | 5 | 2 | Inventory, Spare Parts |
| `tbl_assignedservices` | 0 | InnoDB | 4 | 2 | Staff, Technicians |
| `tbl_assignedspecialtool` | 0 | InnoDB | 7 | 2 | Staff, Technicians |
| `tbl_backuplink` | 1 | InnoDB | 3 | 0 | Auxiliary |
| `tbl_barcodepartnomapping` | 11 | InnoDB | 3 | 0 | Inventory, Spare Parts |
| `tbl_brandcomparison` | 54 | InnoDB | 8 | 0 | Inventory, Spare Parts |
| `tbl_cancelledjobcards` | 4 | InnoDB | 4 | 1 | Job Cards |
| `tbl_carpart_taxonomy` | 9 | InnoDB | 3 | 0 | Auxiliary |
| `tbl_carpartnames` | 3,003 | InnoDB | 6 | 1 | Inventory, Spare Parts |
| `tbl_carpartslocation` | 43 | InnoDB | 2 | 0 | Inventory, Spare Parts |
| `tbl_carpartssupplier` | 52 | InnoDB | 3 | 0 | Inventory, Spare Parts |
| `tbl_checkstaff` | 16 | InnoDB | 4 | 0 | Staff, Technicians |
| `tbl_clientcontacts` | 2,658 | InnoDB | 6 | 0 | Clients |
| `tbl_clientquotationfeedback` | 263 | InnoDB | 3 | 1 | Billing, Quotations |
| `tbl_completedjobcards` | 131 | InnoDB | 5 | 1 | Job Cards |
| `tbl_deposits` | 0 | InnoDB | 4 | 1 | Billing, Quotations |
| `tbl_faqs` | 13 | InnoDB | 3 | 0 | Communications, Walkie-Talkie |
| `tbl_finalcapturedstocktaking` | 6,358 | InnoDB | 10 | 0 | Inventory, Spare Parts |
| `tbl_functionalities` | 194 | InnoDB | 4 | 0 | Users, Roles, Audit |
| `tbl_importexcelstockcount` | 2,967 | InnoDB | 6 | 0 | Auxiliary |
| `tbl_importexcelstockharmonized` | 0 | InnoDB | 4 | 0 | Auxiliary |
| `tbl_importordertracking` | 8 | InnoDB | 8 | 1 | Clients |
| `tbl_incomplete_defects` | 44 | InnoDB | 6 | 0 | Job Cards |
| `tbl_invoices` | 1,014 | InnoDB | 8 | 1 | Billing, Quotations |
| `tbl_jobcarddetails` | 11,723 | InnoDB | 32 | 2 | Job Cards |
| `tbl_logfailedattempts` | 15 | InnoDB | 5 | 0 | Users, Roles, Audit |
| `tbl_monthlyschedule` | 26 | InnoDB | 13 | 1 | Auxiliary |
| `tbl_notifications` | 54 | InnoDB | 6 | 0 | Communications, Walkie-Talkie |
| `tbl_partssellingprice` | 1,373 | InnoDB | 5 | 0 | Inventory, Spare Parts |
| `tbl_payments` | 186 | InnoDB | 7 | 1 | Billing, Quotations |
| `tbl_pendingassignedjobs` | 9,158 | InnoDB | 4 | 2 | Auxiliary |
| `tbl_periodicsalesbilled` | 0 | InnoDB | 6 | 0 | Auxiliary |
| `tbl_quotation` | 1,233 | InnoDB | 7 | 1 | Billing, Quotations |
| `tbl_quotationpartsandservicesfeedback` | 1,018 | InnoDB | 8 | 2 | Billing, Quotations |
| `tbl_repairpriorities` | 30 | InnoDB | 8 | 0 | Job Cards |
| `tbl_returnjobsactiontaken` | 0 | InnoDB | 4 | 0 | Auxiliary |
| `tbl_rolefunctionalitiesaudit` | 194 | InnoDB | 6 | 0 | Users, Roles, Audit |
| `tbl_roles` | 8 | InnoDB | 3 | 0 | Users, Roles, Audit |
| `tbl_saleitemsbilledtotals` | 3 | InnoDB | 6 | 0 | Billing, Quotations |
| `tbl_sales` | 2 | InnoDB | 6 | 0 | Billing, Quotations |
| `tbl_salesitemsbilled` | 11 | InnoDB | 6 | 0 | Billing, Quotations |
| `tbl_serviceprovider` | 7 | InnoDB | 3 | 0 | Staff, Technicians |
| `tbl_signedjobcards` | 8 | InnoDB | 4 | 1 | Job Cards |
| `tbl_sms` | 22 | InnoDB | 8 | 0 | Communications, Walkie-Talkie |
| `tbl_specialtools` | 0 | InnoDB | 4 | 0 | Staff, Technicians |
| `tbl_stockparts` | 12,938 | InnoDB | 7 | 2 | Inventory, Spare Parts |
| `tbl_stocktakeharmonized` | 176 | InnoDB | 5 | 0 | Inventory, Spare Parts |
| `tbl_technician_portal_notifications` | 67 | InnoDB | 6 | 0 | Communications, Walkie-Talkie |
| `tbl_techniciandefectsandrequestedparts` | 289 | InnoDB | 8 | 1 | Job Cards |
| `tbl_technicians` | 50 | InnoDB | 5 | 0 | Staff, Technicians |
| `tbl_temparchivetechniciantools` | 0 | InnoDB | 5 | 0 | Auxiliary |
| `tbl_tempassignedparts` | 0 | InnoDB | 3 | 0 | Auxiliary |
| `tbl_tempcapturedstocktaking` | 2,967 | InnoDB | 9 | 0 | Auxiliary |
| `tbl_temppartsandstockbalances` | 0 | InnoDB | 12 | 0 | Auxiliary |
| `tbl_tempsalesitemstobebilled` | 1 | InnoDB | 6 | 0 | Auxiliary |
| `tbl_tempstockharmonized` | 34 | InnoDB | 6 | 0 | Inventory, Spare Parts |
| `tbl_toolkits` | 5 | InnoDB | 3 | 0 | Staff, Technicians |
| `tbl_userpermissions` | 214 | InnoDB | 5 | 1 | Users, Roles, Audit |
| `tbl_users` | 7 | InnoDB | 10 | 0 | Users, Roles, Audit |
| `tbl_usersaudit` | 4,261 | InnoDB | 7 | 0 | Users, Roles, Audit |
| `tbl_walkietalkie_messages` | 0 | InnoDB | 6 | 0 | Communications, Walkie-Talkie |
| `tbl_walkietalkie_reads` | 0 | InnoDB | 3 | 0 | Communications, Walkie-Talkie |
| `tbl_workdoneinjobcard` | 41 | InnoDB | 3 | 0 | Job Cards |