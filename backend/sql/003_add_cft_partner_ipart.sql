-- Run once if cft_partner already exists without `ipart` (manual migration).
-- Adjust schema/database name if needed.

ALTER TABLE migration_db.cft_partner
ADD COLUMN ipart VARCHAR(100) DEFAULT NULL AFTER nrpart;
