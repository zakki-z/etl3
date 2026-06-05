-- Run once if cft_flow already exists without exec/exece (manual migration).
-- `exec` is quoted because it can be treated as reserved in MySQL.

ALTER TABLE migration_db.cft_flow
ADD COLUMN `exec` VARCHAR(1000) DEFAULT NULL AFTER xlate,
ADD COLUMN exece VARCHAR(1000) DEFAULT NULL AFTER `exec`;
