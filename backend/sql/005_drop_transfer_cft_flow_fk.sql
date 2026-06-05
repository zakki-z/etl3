-- Remove FK from transfer to cft_flow (direct / idf no longer enforced as FK).
-- Run after you have confirmed the constraint name in your DB:
--   SHOW CREATE TABLE migration_db.transfer;
--
-- If the constraint name differs, replace transfer_cft_flow_FK below.

ALTER TABLE migration_db.transfer
DROP FOREIGN KEY transfer_cft_flow_FK;
