-- Run once in DBeaver before the next pipeline run.
-- Creates the boscosend_config table from data/<server>/boscosend/configuration.ini.

USE migration_db;

CREATE TABLE IF NOT EXISTS boscosend_config (
  id                 BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  remote_address     VARCHAR(100) NULL,
  remote_subdir      VARCHAR(500) NULL,
  transfer_id        BIGINT UNSIGNED NULL,
  localdir           VARCHAR(500) NULL,
  backup_dir         VARCHAR(500) NULL,
  file_search_mask   VARCHAR(500) NULL,
  nom_section        VARCHAR(255) NULL,
  `Cmdb-Prestation` VARCHAR(255) NULL,
  PRIMARY KEY (id),
  KEY idx_boscosend_transfer (transfer_id),
  CONSTRAINT fk_boscosend_transfer FOREIGN KEY (transfer_id)
    REFERENCES transfer(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
