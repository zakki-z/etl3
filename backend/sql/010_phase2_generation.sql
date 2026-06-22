-- Phase 2: B2Bi generation engine tables
-- Run once in DBeaver before first generation run.

USE migration_db;

-- 1) Mapping rules: CFT field -> B2Bi field transformation
CREATE TABLE IF NOT EXISTS mapping_rule (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  rule_name       VARCHAR(255) NOT NULL,
  source_field    VARCHAR(255) NOT NULL COMMENT 'dot-path in PartnerContext, e.g. partner.ssl',
  target_field    VARCHAR(255) NOT NULL COMMENT 'dot-path in B2Bi payload, e.g. network.ssl_enabled',
  transform_type  ENUM('direct', 'static', 'lookup', 'template') NOT NULL DEFAULT 'direct',
  transform_params JSON NULL COMMENT 'extra params depending on transform_type',
  is_active       TINYINT(1) NOT NULL DEFAULT 1,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_mapping_rule_name (rule_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2) Generation jobs: one row per "generate all partners" run
CREATE TABLE IF NOT EXISTS generation_job (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  status          ENUM('PENDING','IN_PROGRESS','COMPLETED','FAILED') NOT NULL DEFAULT 'PENDING',
  started_at      TIMESTAMP NULL,
  finished_at     TIMESTAMP NULL,
  partners_total  INT NOT NULL DEFAULT 0,
  partners_ok     INT NOT NULL DEFAULT 0,
  partners_blocked INT NOT NULL DEFAULT 0,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3) Exception log: one row per problem detected during generation
CREATE TABLE IF NOT EXISTS exception_log (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  job_id          BIGINT UNSIGNED NOT NULL,
  partner_id      VARCHAR(100) NOT NULL,
  severity        ENUM('BLOCKING','WARNING') NOT NULL,
  exception_type  VARCHAR(100) NOT NULL COMMENT 'e.g. MISSING_HOST, INVALID_SSL, SCRIPT_BUCKET_C',
  message         VARCHAR(1000) NOT NULL,
  resolved        TINYINT(1) NOT NULL DEFAULT 0,
  resolved_at     TIMESTAMP NULL,
  resolution_note VARCHAR(500) NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_exception_job (job_id),
  KEY idx_exception_partner (partner_id),
  CONSTRAINT fk_exception_job FOREIGN KEY (job_id)
    REFERENCES generation_job(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4) B2Bi configs: generated Trading Partner payload per partner
CREATE TABLE IF NOT EXISTS b2bi_config (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  job_id          BIGINT UNSIGNED NOT NULL,
  partner_id      VARCHAR(100) NOT NULL,
  payload         JSON NOT NULL COMMENT 'full B2Bi Trading Partner JSON ready for the REST API',
  sync_status     ENUM('PENDING','APPROVED','DEPLOYED','FAILED') NOT NULL DEFAULT 'PENDING',
  generated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  approved_at     TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_b2bi_config_job_partner (job_id, partner_id),
  KEY idx_b2bi_partner (partner_id),
  CONSTRAINT fk_b2bi_config_job FOREIGN KEY (job_id)
    REFERENCES generation_job(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Seed the 7 base mapping rules
INSERT IGNORE INTO mapping_rule (rule_name, source_field, target_field, transform_type, transform_params) VALUES
  ('partner_name',    'partner.nspart',  'trading_partner.name',           'direct',   NULL),
  ('remote_name',     'partner.nrpart',  'trading_partner.remote_name',    'direct',   NULL),
  ('host',            'tcp.host',        'network.host',                   'direct',   NULL),
  ('port',            'tcp.cnxout',      'network.port',                   'direct',   NULL),
  ('ssl_enabled',     'partner.ssl',     'network.ssl_enabled',            'direct',   NULL),
  ('protocol',        NULL,              'network.protocol',               'static',   '{"value": "PESIT"}'),
  ('direction_send',  'flow.direct',     'flow.direction',                 'lookup',   '{"send": "SENDER", "recv": "RECEIVER"}');
