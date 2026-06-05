# Project Handoff - CFT Migration Pipeline

## Objective

Build an industrialized daily ingestion pipeline (Python + SQLAlchemy + Airflow) that parses a CFT export configuration file and loads MySQL tables:

- `cft_partner` from `CFTPART`
- `cft_tcp` from `CFTTCP` (linked to partner)
- `cft_flow` from `CFTSEND` and `CFTRECV` (`direct` must be `send`/`recv`)

Constraints requested by user:

- Step-by-step implementation (small increments, understandable)
- Industrialized structure (clean architecture, reusable)
- Airflow orchestration for daily run
- Prefer no raw SQL in app/business code (use SQLAlchemy ORM/Core)

---

## User Context (Important)

- User speaks mostly French.
- DB tool: DBeaver + MySQL 8.x.
- Local Windows environment.
- Export conf file is very large.

User-provided files:

- Config export: `C:\Users\OH\Desktop\data\conf_cft.20260422.txt`
- DB dump: `C:\Users\OH\dump-pfe_migration-202604221309.sql`

---

## Confirmed Database Schema (from dump)

### `cft_partner`

- `id` bigint unsigned PK auto_increment
- `nspart`, `nrpart`, `ssl`, `sap`, `nspassw`, `nrpassw`

### `cft_tcp`

- `partner_id` bigint unsigned PK and FK -> `cft_partner.id`
- columns: `cnxout`, `host`
- conf field extracted: `CNXOUT` (stored in DB column `cnxout`)

### `cft_flow`

- `id` bigint unsigned PK auto_increment
- `fcode`, `ftype`, `flrecl`, `frecfm`, `direct`, `fname`, `xlate`, `idf_code`

---

## Confirmed Conf Sections / Mapping

From `conf_cft.20260422.txt`:

- `CFTPART ID = '...'`
- `CFTTCP ID = '...'`
- `CFTSEND ID = '...'`
- `CFTRECV ID = '...'`

Expected mappings:

- `CFTPART` -> `cft_partner`
  - `NSPART`, `NRPART`, `SAP`, `NSPASSW`, `NRPASSW`, `SSL`
- `CFTTCP` -> `cft_tcp`
  - `ID` used to map to `CFTPART ID`
  - `CNXOUT` -> stored in DB column `cnxout`
  - `HOST`
- `CFTSEND` / `CFTRECV` -> `cft_flow`
  - `direct = 'send'` for send blocks
  - `direct = 'recv'` for recv blocks
  - `ID` -> `idf_code`
  - `FCODE` -> `fcode`
  - `TYPE` -> `ftype`
  - `LRECL` -> `flrecl`
  - `RECFM` -> `frecfm`
  - `FNAME` -> `fname` (truncated to 100 chars)
  - `XLATE` present/non-empty -> `xlate = 1` else `0`

---

## Known Pitfalls / Lessons Learned

- MySQL column `ssl` can trigger syntax issues if raw SQL without backticks.
- Host formatting errors in DB URL can produce `getaddrinfo failed` (`@localhost` invalid host).
- Very large conf file: parse streaming line-by-line; avoid full-memory load.
- DBeaver UI can show stale metadata until refresh.

---

## Quick Resume Prompt for Next Cursor

> Continue the CFT migration project from `PROJECT_HANDOFF.md`. Implement step-by-step with SQLAlchemy and Airflow. Validate schema alignment (`cft_tcp.cnxout` vs conf `CNXOUT`), then extend parsers/repositories for `transfer` and other tables, with idempotent upserts and daily DAG orchestration.
