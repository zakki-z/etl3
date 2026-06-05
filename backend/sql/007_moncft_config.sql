-- Run once in DBeaver before next pipeline run.
-- Creates the moncft_config table linking each "[Repertoire : N]" entry of
-- a C2I_MonCft<XXX>.ini file to the matching transfer row.

USE migration_db;

CREATE TABLE IF NOT EXISTS moncft_config (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  transfer_id  BIGINT UNSIGNED NULL,
  fname        VARCHAR(500) NULL,
  filtre       VARCHAR(255) NULL,
  parm         VARCHAR(255) NULL,
  nfname       VARCHAR(255) NULL,
  sappl        VARCHAR(100) NULL,
  rappl        VARCHAR(100) NULL,
  suser        VARCHAR(100) NULL,
  PRIMARY KEY (id),
  KEY idx_moncft_transfer (transfer_id),
  CONSTRAINT fk_moncft_transfer FOREIGN KEY (transfer_id)
    REFERENCES transfer(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
