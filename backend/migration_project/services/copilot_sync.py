from __future__ import annotations


from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta


from sqlalchemy import bindparam, create_engine, delete, text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session


from migration_project.config import get_settings
from migration_project.models.transfer import Transfer, TransferStatut




# Anything strictly greater than this value is treated as epoch in milliseconds.
_EPOCH_S_MAX = 9_999_999_999




def _epoch_to_date(value: object) -> date | None:
    if value is None:
        return None
    try:
        ts = int(value)
    except (TypeError, ValueError):
        return None
    # Copilot may store epoch in milliseconds.
    if ts > 10**12:
        ts //= 1000
    try:
        return datetime.fromtimestamp(ts, tz=UTC).date()
    except (OSError, OverflowError, ValueError):
        return None




def _flow_direct_for_mapping(value: object) -> str:
    """Normalize flux.Direct to values used by cft_flow.direct."""
    raw = str(value).strip().upper() if value is not None else ""
    if raw == "CHER":
        return "recv"
    if raw == "RECUP":
        return "send"
    return raw.lower()




@dataclass(frozen=True)
class CopilotSyncReport:
    transfers_deleted: int
    transfers_inserted: int
    skipped_flux_rows: int




class CopilotSyncService:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not all([self.settings.cop_db_host, self.settings.cop_db_user, self.settings.cop_db_name]):
            raise ValueError("Copilot DB settings are missing (COP_DB_HOST/COP_DB_USER/COP_DB_NAME).")
        copilot_url = URL.create(
            drivername="mysql+pymysql",
            username=self.settings.cop_db_user,
            password=self.settings.cop_db_password,
            host=self.settings.cop_db_host,
            port=self.settings.cop_db_port,
            database=self.settings.cop_db_name,
            query={"charset": "utf8mb4"},
        )
        self.copilot_engine = create_engine(
            copilot_url,
            pool_pre_ping=True,
            future=True,
            pool_recycle=1800,
            connect_args={
                "connect_timeout": 30,
                "read_timeout": 1800,
                "write_timeout": 1800,
            },
        )


    def run(self, session: Session) -> CopilotSyncReport:
        transfers_deleted, transfers_inserted, skipped_flux_rows = self._sync_transfers(session)
        return CopilotSyncReport(
            transfers_deleted=transfers_deleted,
            transfers_inserted=transfers_inserted,
            skipped_flux_rows=skipped_flux_rows,
        )


    def _sync_transfers(self, session: Session) -> tuple[int, int, int]:
        lookback_months = max(1, int(self.settings.cop_lookback_months))


        # Compute the cut-off epoch in Python so MySQL can use any index on
        # flux.Date instead of evaluating FROM_UNIXTIME(...) row by row.
        # Approximate 30 days per month is enough for a rolling window.
        cutoff_dt = datetime.now(tz=UTC) - timedelta(days=30 * lookback_months)
        cutoff_s = int(cutoff_dt.timestamp())
        cutoff_ms = cutoff_s * 1000


        # Deduplicate server-side without window functions (Copilot's MySQL
        # version may not support ROW_NUMBER). We compute MAX(Date) per
        # (Part, Direct, Idf) tuple and join back to fetch Statut and Techno.
        # Any residual duplicates (same Part, Direct, Idf, Date) are folded
        # by values_by_key on the Python side.
        stmt = text(
            f"""
            SELECT f.Part, f.Direct, f.Statut, f.`Date`, f.Idf, f.Techno
            FROM flux f
            INNER JOIN (
                SELECT Part, Direct, Idf, MAX(`Date`) AS max_date
                FROM flux
                WHERE ((`Date` BETWEEN :cutoff_s AND {_EPOCH_S_MAX})
                    OR (`Date` >= :cutoff_ms))
                  AND Idf IS NOT NULL AND Idf <> '' AND Idf <> '-'
                  AND Part IS NOT NULL AND Part <> ''
                GROUP BY Part, Direct, Idf
            ) latest
              ON f.Part = latest.Part
             AND f.Direct = latest.Direct
             AND f.Idf = latest.Idf
             AND f.`Date` = latest.max_date
            """
        ).bindparams(
            bindparam("cutoff_s", value=cutoff_s),
            bindparam("cutoff_ms", value=cutoff_ms),
        )
        with self.copilot_engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()


        flow_rows = session.execute(
            text("SELECT id, idf_code, direct FROM cft_flow")
        ).mappings().all()
        flow_id_by_key: dict[tuple[str, str], int] = {
            (str(r["idf_code"]), str(r["direct"]).lower()): int(r["id"]) for r in flow_rows
        }


        partner_rows = session.execute(text("SELECT id FROM cft_partner")).mappings().all()
        valid_partner_ids = {str(r["id"]) for r in partner_rows}


        server_rows = session.execute(text("SELECT id FROM server")).mappings().all()
        valid_server_ids = {str(r["id"]) for r in server_rows}


        values_by_key: dict[tuple[str | None, int, str], dict[str, object]] = {}
        skipped = 0
        for row in rows:
            server_id = str(row["Techno"]).strip()
            if not server_id or server_id not in valid_server_ids:
                skipped += 1
                continue


            idf_code = row["Idf"]
            if not idf_code or idf_code == "-":
                skipped += 1
                continue


            partner_id = str(row["Part"]).strip() if row["Part"] is not None else None
            if not partner_id or partner_id not in valid_partner_ids:
                skipped += 1
                continue
            direct_raw = str(row["Direct"]).strip() if row["Direct"] is not None else ""
            direct_for_mapping = _flow_direct_for_mapping(row["Direct"])
            idf_id = flow_id_by_key.get((str(idf_code), direct_for_mapping))
            if idf_id is None:
                skipped += 1
                continue
            key = (partner_id, idf_id, direct_raw)


            statut = None
            raw_statut = str(row["Statut"]).strip().upper() if row["Statut"] is not None else ""
            if raw_statut == TransferStatut.OK.value:
                statut = TransferStatut.OK
            elif raw_statut == TransferStatut.NOK.value:
                statut = TransferStatut.NOK


            existing = values_by_key.get(key)
            if existing is None:
                values_by_key[key] = {
                    "partner_id": partner_id,
                    "idf_id": idf_id,
                    "direct": direct_raw,
                    "server_id": server_id,
                    "date": _epoch_to_date(row["Date"]),
                    "statut": statut,
                }
            else:
                new_date = _epoch_to_date(row["Date"])
                if new_date and (
                    existing["date"] is None
                    or new_date > existing["date"]
                ):
                    existing["date"] = new_date
                    existing["statut"] = statut


        values = list(values_by_key.values())


        # Strict snapshot mode: transfer contains only rows seen in the current
        # Copilot lookback window. Rows that disappear from the window are removed.
        delete_result = session.execute(delete(Transfer))
        transfers_deleted = int(delete_result.rowcount or 0)
        session.flush()


        if values:
            session.execute(insert(Transfer).values(values))


        return transfers_deleted, len(values), skipped
