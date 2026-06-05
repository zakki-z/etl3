from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.config import get_settings
from migration_project.parsers.post_script_parser import (
    parse_global_script,
    script_direction,
)
from migration_project.parsers.post_script_records import ParsedAction
from migration_project.repositories.flow_action_repository import FlowActionRepository
from migration_project.repositories.post_processing_script_repository import (
    PostProcessingScriptRepository,
)
from migration_project.utils.file_selector import get_server_script_dirs


# Path used to store the script_path in DB (Windows path on the CFT host).
_DB_SCRIPT_DIR = r"D:\Tessi\Outils\Exe"


GLOBAL_SCRIPT_NAMES = {"RECVOK.bat", "RECVNOK.bat", "SENDOK.bat", "SENDNOK.bat"}


@dataclass
class PostScriptImportReport:
    servers_scanned: int = 0
    scripts_seen: int = 0
    global_scripts_imported: int = 0
    specific_scripts_imported: int = 0
    actions_inserted: int = 0
    skipped_unknown_idf: int = 0
    skipped_unknown_partner: int = 0
    skipped_specific_unbound: int = 0
    missing_servers: list[str] = field(default_factory=list)


class PostScriptImportService:
    """Parse RECV*.bat / SEND*.bat scripts under <data_dir>/<server>/scripts/.

    Two kinds of scripts are processed:
      * Global scripts (RECVOK / RECVNOK / SENDOK / SENDNOK) -> conditional actions
      * Specific scripts (file name referenced by cft_flow.exec or cft_flow.exece)
        -> all actions stored under IDF_SCRIPT scope, bound to that idf
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.script_repo = PostProcessingScriptRepository()
        self.action_repo = FlowActionRepository()

    # -- Public ---------------------------------------------------------------

    def run(self, session: Session) -> PostScriptImportReport:
        report = PostScriptImportReport()

        valid_server_ids = self._load_valid_server_ids(session)
        flow_id_by_key = self._load_flow_index(session)
        partner_ids = self._load_partner_ids(session)
        ipart_to_partner = self._load_ipart_to_partner(session)
        specific_index = self._load_specific_script_index(session)

        for server_id, scripts_dir in get_server_script_dirs(self.settings.data_dir):
            report.servers_scanned += 1

            if server_id not in valid_server_ids:
                report.missing_servers.append(server_id)
                continue

            for script_file in sorted(scripts_dir.iterdir()):
                if not script_file.is_file():
                    continue
                if script_file.suffix.lower() != ".bat":
                    continue

                report.scripts_seen += 1
                self._process_script(
                    session,
                    server_id=server_id,
                    script_file=script_file,
                    flow_id_by_key=flow_id_by_key,
                    partner_ids=partner_ids,
                    ipart_to_partner=ipart_to_partner,
                    specific_index=specific_index,
                    report=report,
                )

        return report

    # -- Internals ------------------------------------------------------------

    def _process_script(
        self,
        session: Session,
        *,
        server_id: str,
        script_file: Path,
        flow_id_by_key: dict[tuple[str, str], int],
        partner_ids: set[str],
        ipart_to_partner: dict[str, str],
        specific_index: dict[tuple[str, str], tuple[int, str]],
        report: PostScriptImportReport,
    ) -> None:
        script_name = script_file.name
        is_global = script_name.upper() in {n.upper() for n in GLOBAL_SCRIPT_NAMES}
        direct = script_direction(script_name)

        # For specific scripts, look up the binding by file basename only:
        # the same script path is reused on every server (as confirmed by
        # the user), so basename is enough to find the matching cft_flow row.
        specific_binding: tuple[int, str] | None = None
        if not is_global:
            specific_binding = specific_index.get(("*", script_name.lower()))
            if specific_binding is None:
                # Not referenced by any cft_flow.exec/exece -> we can't bind
                # actions to an idf, so skip the file entirely.
                report.skipped_specific_unbound += 1
                return

        # Insert / refresh the script row first so we get its PK.
        script_path = f"{_DB_SCRIPT_DIR}\\{script_name}"
        script_id = self.script_repo.upsert(
            session,
            server_id=server_id,
            script_path=script_path,
            script_name=script_name,
        )

        # Wipe previous actions so re-runs are idempotent for this script.
        self.action_repo.delete_for_script(session, script_id)

        # Parse the file according to its kind.
        if is_global:
            actions = parse_global_script(script_file, direct=direct)
            report.global_scripts_imported += 1
        else:
            # For specific scripts (referenced by cft_flow.exec / cft_flow.exece)
            # we do NOT trace individual actions. We just emit a single marker
            # row stating that this IDF has a specific script with actions.
            # The script file itself is still registered in post_processing_scripts.
            assert specific_binding is not None
            _idf_id, idf_code = specific_binding
            actions = [
                ParsedAction(
                    scope_type="IDF_SCRIPT",
                    action_order=1,
                    action_text=f"Script spécifique : {script_name} (actions non détaillées)",
                    idf_code=idf_code,
                    flow_direct=direct,
                )
            ]
            report.specific_scripts_imported += 1

        rows = self._actions_to_rows(
            actions,
            script_id=script_id,
            flow_id_by_key=flow_id_by_key,
            partner_ids=partner_ids,
            ipart_to_partner=ipart_to_partner,
            specific_idf_id=specific_binding[0] if specific_binding else None,
            report=report,
        )
        report.actions_inserted += self.action_repo.insert_many(session, rows)

    def _actions_to_rows(
        self,
        actions: Iterable[ParsedAction],
        *,
        script_id: int,
        flow_id_by_key: dict[tuple[str, str], int],
        partner_ids: set[str],
        ipart_to_partner: dict[str, str],
        specific_idf_id: int | None,
        report: PostScriptImportReport,
    ) -> list[dict]:
        rows: list[dict] = []
        for action in actions:
            idf_id: int | None = None
            partner_id: str | None = None
            ipart_value: str | None = None

            if action.scope_type == "IDF":
                if action.idf_code and action.flow_direct:
                    idf_id = flow_id_by_key.get(
                        (action.idf_code.lower(), action.flow_direct)
                    )
                if idf_id is None:
                    report.skipped_unknown_idf += 1
                    continue

            elif action.scope_type == "IDF_SCRIPT":
                idf_id = specific_idf_id
                if idf_id is None:
                    # Should never happen: parser only emits IDF_SCRIPT for specific scripts.
                    report.skipped_unknown_idf += 1
                    continue

            elif action.scope_type == "PART":
                if action.partner_id and action.partner_id in partner_ids:
                    partner_id = action.partner_id
                else:
                    report.skipped_unknown_partner += 1
                    continue

            elif action.scope_type == "IPART":
                # ipart_value is always kept verbatim. We additionally try to
                # resolve it to a partner_id when it matches cft_partner.ipart.
                ipart_value = action.ipart_value
                if action.ipart_value and action.ipart_value in ipart_to_partner:
                    partner_id = ipart_to_partner[action.ipart_value]

            rows.append(
                {
                    "script_id": script_id,
                    "scope_type": action.scope_type,
                    "idf_id": idf_id,
                    "partner_id": partner_id,
                    "ipart_value": ipart_value,
                    "action_order": action.action_order,
                    "action_text": action.action_text,
                }
            )
        return rows

    # -- Lookups --------------------------------------------------------------

    def _load_valid_server_ids(self, session: Session) -> set[str]:
        rows = session.execute(text("SELECT id FROM server")).mappings().all()
        return {str(r["id"]) for r in rows}

    def _load_flow_index(self, session: Session) -> dict[tuple[str, str], int]:
        rows = (
            session.execute(text("SELECT id, idf_code, direct FROM cft_flow"))
            .mappings()
            .all()
        )
        return {
            (str(r["idf_code"]).lower(), str(r["direct"]).lower()): int(r["id"])
            for r in rows
        }

    def _load_partner_ids(self, session: Session) -> set[str]:
        rows = session.execute(text("SELECT id FROM cft_partner")).mappings().all()
        return {str(r["id"]) for r in rows}

    def _load_ipart_to_partner(self, session: Session) -> dict[str, str]:
        """Map raw ipart literal -> a partner_id (any of the matching ones).

        cft_partner.ipart is not unique in the conf, so we keep the first match
        per ipart value (case-insensitive). We store the original casing as key.
        """
        rows = (
            session.execute(
                text("SELECT id, ipart FROM cft_partner WHERE ipart IS NOT NULL AND ipart <> ''")
            )
            .mappings()
            .all()
        )
        out: dict[str, str] = {}
        for r in rows:
            ipart = str(r["ipart"]).strip()
            if ipart and ipart not in out:
                out[ipart] = str(r["id"])
        return out

    def _load_specific_script_index(
        self, session: Session
    ) -> dict[tuple[str, str], tuple[int, str]]:
        """Build (server_id, lowercased_script_basename) -> (cft_flow.id, idf_code).

        The server_id must be derivable from the EXEC/EXECE path. We use
        the first folder name after the data root as the server id, but to
        keep things robust we also accept the file name alone (when the same
        script name appears for one server only). For now we do a simpler
        match: any cft_flow row whose exec/exece basename equals the file name
        is bound to that file regardless of server. If multiple rows match,
        the first one wins (consistent runs).
        """
        rows = (
            session.execute(
                text(
                    """
                    SELECT id, idf_code, `exec` AS exec_path, exece
                    FROM cft_flow
                    WHERE (`exec` IS NOT NULL AND `exec` <> '')
                       OR (exece IS NOT NULL AND exece <> '')
                    """
                )
            )
            .mappings()
            .all()
        )

        out: dict[tuple[str, str], tuple[int, str]] = {}
        for r in rows:
            for raw_path in (r.get("exec_path"), r.get("exece")):
                if not raw_path:
                    continue
                basename = _windows_basename(str(raw_path)).lower()
                if not basename:
                    continue
                # Bind to every server -> we'll match by file name alone for
                # the lookup. Use a sentinel "*" server id meaning "any".
                key = ("*", basename)
                if key not in out:
                    out[key] = (int(r["id"]), str(r["idf_code"]))
        return out


def _windows_basename(path: str) -> str:
    cleaned = path.strip().strip("'").strip('"')
    if not cleaned:
        return ""
    last_sep = max(cleaned.rfind("\\"), cleaned.rfind("/"))
    return cleaned[last_sep + 1 :] if last_sep != -1 else cleaned
