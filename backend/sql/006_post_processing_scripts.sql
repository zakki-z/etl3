-- Run once in DBeaver before next pipeline run.
-- Creates the two tables for post-transfer scripts analysis.

USE migration_db;

-- 1) Post-processing scripts catalogue (one row per .bat file per server)
CREATE TABLE IF NOT EXISTS post_processing_scripts (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  server_id    VARCHAR(19) NOT NULL,
  script_path  VARCHAR(500) NOT NULL,
  script_name  VARCHAR(255) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_script_per_server (server_id, script_path),
  CONSTRAINT fk_pps_server FOREIGN KEY (server_id)
    REFERENCES server(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2) Actions extracted from those scripts
CREATE TABLE IF NOT EXISTS flow_action (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  script_id     BIGINT UNSIGNED NOT NULL,
  scope_type    ENUM('GLOBAL','IDF','PART','IPART','IDF_SCRIPT') NOT NULL,
  idf_id        BIGINT UNSIGNED NULL,
  partner_id    VARCHAR(19)     NULL,
  ipart_value   VARCHAR(255)    NULL,
  action_order  INT NOT NULL DEFAULT 0,
  action_text   VARCHAR(2000) NOT NULL,
  PRIMARY KEY (id),
  KEY idx_scope (scope_type, idf_id, partner_id, ipart_value),
  CONSTRAINT fk_fa_script  FOREIGN KEY (script_id)
    REFERENCES post_processing_scripts(id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_fa_idf     FOREIGN KEY (idf_id)
    REFERENCES cft_flow(id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_fa_partner FOREIGN KEY (partner_id)
    REFERENCES cft_partner(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3) Helpful index for ipart joins on cft_partner
CREATE INDEX idx_cft_partner_ipart ON cft_partner(ipart);
