from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.repositories.b2bi_config_repository import B2biConfigRepository
from migration_project.repositories.exception_log_repository import ExceptionLogRepository
from migration_project.repositories.generation_job_repository import GenerationJobRepository
from migration_project.repositories.mapping_rule_repository import MappingRuleRepository
from migration_project.services.context_builder import FlowContext, PartnerContext
from migration_project.services.generation_engine import generate


@dataclass
class GenerationReport:
    job_id: int
    partners_total: int
    partners_ok: int
    partners_blocked: int
    configs_created: int
    exceptions_logged: int


class GenerationService:
    """
    Orchestrates a full Phase 2 generation run.
    Loads partner contexts from the DB, calls the pure engine for each,
    and persists the results (b2bi_config + exception_log).
    """

    def __init__(self) -> None:
        self.job_repo = GenerationJobRepository()
        self.rule_repo = MappingRuleRepository()
        self.config_repo = B2biConfigRepository()
        self.exception_repo = ExceptionLogRepository()

    def run(self, session: Session) -> GenerationReport:
        # 1. Create job row
        job = self.job_repo.create(session)
        session.flush()

        try:
            self.job_repo.mark_in_progress(session, job)

            # 2. Load inputs
            rules = self.rule_repo.get_active(session)
            contexts = _load_all_partner_contexts(session)

            # 3. Generate for each partner
            config_rows: list[dict] = []
            exception_rows: list[dict] = []
            ok, blocked = 0, 0

            for ctx in contexts:
                result = generate(ctx, rules)
                if result.is_blocked:
                    blocked += 1
                else:
                    ok += 1

                config_rows.append({
                    "job_id": job.id,
                    "partner_id": result.partner_id,
                    "payload": result.payload,
                    "sync_status": "PENDING",
                })

                for exc in result.exceptions:
                    exception_rows.append({
                        "job_id": job.id,
                        "partner_id": result.partner_id,
                        "severity": exc.severity,
                        "exception_type": exc.exception_type,
                        "message": exc.message,
                        "resolved": 0,
                    })

            # 4. Persist results
            configs_created = self.config_repo.insert_many(session, config_rows)
            exceptions_logged = self.exception_repo.insert_many(session, exception_rows)

            # 5. Mark job done
            self.job_repo.mark_completed(
                session, job,
                partners_total=len(contexts),
                partners_ok=ok,
                partners_blocked=blocked,
            )

        except Exception:
            self.job_repo.mark_failed(session, job)
            raise

        return GenerationReport(
            job_id=job.id,
            partners_total=len(contexts),
            partners_ok=ok,
            partners_blocked=blocked,
            configs_created=configs_created,
            exceptions_logged=exceptions_logged,
        )


# ---------------------------------------------------------------------------
# Context loading (reads from Phase 1 tables)
# ---------------------------------------------------------------------------

def _load_all_partner_contexts(session: Session) -> list[PartnerContext]:
    """
    Build a PartnerContext for every partner in cft_partner,
    joining tcp, flows, and checking for Bucket C scripts.
    """
    # Load base partner + tcp data
    partner_rows = session.execute(text("""
        SELECT
            p.id        AS partner_id,
            p.nspart,
            p.nrpart,
            p.`ssl`     AS ssl,
            p.sap,
            t.host,
            t.cnxout
        FROM cft_partner p
        LEFT JOIN cft_tcp t ON t.partner_id = p.id
    """)).mappings().all()

    if not partner_rows:
        return []

    # Load all flows indexed by idf_code for efficient lookup
    flow_rows = session.execute(text("""
        SELECT id, idf_code, direct, fcode, ftype, fname, xlate, `exec`, exece
        FROM cft_flow
    """)).mappings().all()

    # Load partner -> flow associations via transfer table
    transfer_rows = session.execute(text("""
        SELECT DISTINCT partner_id, idf_id
        FROM transfer
        WHERE partner_id IS NOT NULL AND idf_id IS NOT NULL
    """)).mappings().all()

    flow_by_id: dict[int, FlowContext] = {
        int(r["id"]): FlowContext(
            idf_code=str(r["idf_code"]),
            direct=str(r["direct"]),
            fcode=r["fcode"],
            ftype=r["ftype"],
            fname=r["fname"],
            xlate=int(r["xlate"] or 0),
            exec=r["exec"],
            exece=r["exece"],
        )
        for r in flow_rows
    }

    # partner_id -> set of flow ids
    flows_for_partner: dict[str, list[FlowContext]] = {}
    for t in transfer_rows:
        pid = str(t["partner_id"])
        fid = int(t["idf_id"])
        if fid in flow_by_id:
            flows_for_partner.setdefault(pid, []).append(flow_by_id[fid])

    # Detect Bucket C scripts: flow_action rows with scope IDF_SCRIPT
    # where action_text contains 'Bucket C' (post-script parser marks these)
    bucket_c_partners: set[str] = _detect_bucket_c_partners(session)

    contexts: list[PartnerContext] = []
    for row in partner_rows:
        pid = str(row["partner_id"])
        contexts.append(PartnerContext(
            partner_id=pid,
            nspart=row["nspart"],
            nrpart=row["nrpart"],
            ssl=int(row["ssl"] or 0),
            sap=row["sap"],
            host=row["host"],
            cnxout=row["cnxout"],
            flows=flows_for_partner.get(pid, []),
            has_bucket_c_script=pid in bucket_c_partners,
        ))

    return contexts


def _detect_bucket_c_partners(session: Session) -> set[str]:
    """
    Return the set of partner_ids that have at least one Bucket C script action.
    Bucket C = a post-script that cannot be auto-migrated (complex logic).
    We identify them by the marker text the post_script_import service writes.
    """
    rows = session.execute(text("""
        SELECT DISTINCT cp.id AS partner_id
        FROM cft_partner cp
        JOIN transfer t ON t.partner_id = cp.id
        JOIN cft_flow f ON f.id = t.idf_id
        JOIN flow_action fa ON fa.idf_id = f.id
        WHERE fa.action_text LIKE '%Bucket C%'
           OR fa.scope_type = 'IDF_SCRIPT'
    """)).mappings().all()
    return {str(r["partner_id"]) for r in rows}
