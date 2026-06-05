-- Run once in DBeaver (MySQL 8+)

-- Idempotent partner upserts (matches ORM UniqueConstraint)
ALTER TABLE migration_db.cft_partner
ADD UNIQUE KEY uq_cft_partner_nspart_nrpart (nspart, nrpart);

-- Idempotent flow upserts (matches ORM UniqueConstraint)
ALTER TABLE migration_db.cft_flow
ADD UNIQUE KEY uq_cft_flow_idf_direct (idf_code, direct);

-- Staging table for CFTTCP entries without matching partner
CREATE TABLE IF NOT EXISTS migration_db.stg_cft_tcp_without_partner (
  id VARCHAR(100) NOT NULL,
  cnxout VARCHAR(100) DEFAULT NULL,
  host VARCHAR(100) DEFAULT NULL,
  reason VARCHAR(255) NOT NULL DEFAULT 'missing_partner_mapping',
  first_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_seen_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP VIEW IF EXISTS migration_db.v_stg_cft_tcp_without_partner;
CREATE VIEW migration_db.v_stg_cft_tcp_without_partner AS
SELECT
  id,
  cnxout,
  host,
  reason,
  first_seen_at,
  last_seen_at
FROM migration_db.stg_cft_tcp_without_partner;
