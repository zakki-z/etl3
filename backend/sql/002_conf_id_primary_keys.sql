-- Run once in DBeaver before next pipeline run.
-- This migration switches PKs to business IDs from conf.
-- WARNING: it recreates 3 tables (existing data in these tables will be dropped).

USE migration_db;

DROP TABLE IF EXISTS cft_tcp;
DROP TABLE IF EXISTS cft_flow;
DROP TABLE IF EXISTS cft_partner;

CREATE TABLE cft_partner (
  id        VARCHAR(100) NOT NULL,
  nspart    VARCHAR(100) DEFAULT NULL,
  nrpart    VARCHAR(100) DEFAULT NULL,
  ipart     VARCHAR(100) DEFAULT NULL,
  `ssl`     TINYINT(1) DEFAULT NULL,
  sap       VARCHAR(100) DEFAULT NULL,
  nspassw   VARCHAR(100) DEFAULT NULL,
  nrpassw   VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cft_partner_nspart_nrpart (nspart, nrpart)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE cft_tcp (
  partner_id VARCHAR(100) NOT NULL,
  cnxout     VARCHAR(100) DEFAULT NULL,
  host       VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (partner_id),
  CONSTRAINT fk_cft_tcp_partner_conf_id
    FOREIGN KEY (partner_id) REFERENCES cft_partner(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE cft_flow (
  idf_code VARCHAR(100) NOT NULL,
  direct   VARCHAR(100) NOT NULL,
  fcode    VARCHAR(100) DEFAULT NULL,
  ftype    VARCHAR(100) DEFAULT NULL,
  flrecl   VARCHAR(100) DEFAULT NULL,
  frecfm   VARCHAR(100) DEFAULT NULL,
  fname    VARCHAR(100) DEFAULT NULL,
  xlate    TINYINT(1) DEFAULT NULL,
  `exec`   VARCHAR(1000) DEFAULT NULL,
  exece    VARCHAR(1000) DEFAULT NULL,
  PRIMARY KEY (idf_code, direct)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
