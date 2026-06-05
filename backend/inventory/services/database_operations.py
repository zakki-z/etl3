"""
Database operations — schema management and record insert/upsert helpers.
"""

import logging
import json
from typing import Optional
from datetime import datetime

from sqlalchemy.engine import Engine

# Import the SHARED metadata that has all tables registered
from ..models import (
    metadata,
    server_table, cfttcp_table, cftprot_table, cftssl_table,
    partner_table, flow_table, processing_table,
    bosco_route_table, copilot_activity_table, migration_table,
)

log = logging.getLogger("cft_extractor")


#Schema management

def create_schema(engine: Engine):
    """Create all tables. Safe to call multiple times (IF NOT EXISTS)."""
    metadata.create_all(engine)
    log.info("Database schema created/verified.")


def drop_schema(engine: Engine):
    """Drop all tables. USE WITH CAUTION."""
    metadata.drop_all(engine)
    log.info("Database schema dropped.")


#Server

def upsert_server(conn, server_info: dict) -> int:
    """Insert or update a server record. Returns server ID."""
    result = conn.execute(
        server_table.select().where(server_table.c.name == server_info["name"])
    ).fetchone()

    if result:
        conn.execute(
            server_table.update()
            .where(server_table.c.name == server_info["name"])
            .values(**{k: v for k, v in server_info.items() if k != "created_at"})
        )
        return result.id
    else:
        result = conn.execute(
            server_table.insert().values(**server_info)
        )
        return result.inserted_primary_key[0]


#CFTTCP
def insert_cfttcp(conn, server_id: int, block: dict) -> int:
    row = {
        "server_id": server_id,
        "name": block.get("ID", ""),
        "host": block.get("HOST"),
        "port": int(block["PORT"]) if block.get("PORT") else None,
        "cnx_in": int(block["CNXIN"]) if block.get("CNXIN") else None,
        "cnx_out": int(block["CNXOUT"]) if block.get("CNXOUT") else None,
        "cnx_inout": int(block["CNXINOUT"]) if block.get("CNXINOUT") else None,
        "retry_wait": int(block["RETRYW"]) if block.get("RETRYW") else None,
        "retry_max": int(block["RETRY"]) if block.get("RETRY") else None,
        "ssl_id": block.get("SSL"),
        "comment": block.get("COMMENT"),
        "raw_config": block.get("_raw", ""),
    }

    existing = conn.execute(
        cfttcp_table.select().where(
            (cfttcp_table.c.server_id == server_id) &
            (cfttcp_table.c.name == row["name"])
        )
    ).fetchone()

    if existing:
        conn.execute(
            cfttcp_table.update()
            .where(cfttcp_table.c.id == existing.id)
            .values(**row)
        )
        return existing.id
    else:
        result = conn.execute(cfttcp_table.insert().values(**row))
        return result.inserted_primary_key[0]


#CFTPROT

def insert_cftprot(conn, server_id: int, block: dict) -> int:
    row = {
        "server_id": server_id,
        "name": block.get("ID", ""),
        "prot_type": block.get("TYPE"),
        "net": block.get("NET"),
        "sap": block.get("SAP"),
        "ssl_id": block.get("SSL"),
        "compress": block.get("COMPRESS"),
        "restart": block.get("RESTART"),
        "concat": block.get("CONCAT"),
        "comment": block.get("COMMENT"),
        "raw_config": block.get("_raw", ""),
    }
    existing = conn.execute(
        cftprot_table.select().where(
            (cftprot_table.c.server_id == server_id) &
            (cftprot_table.c.name == row["name"])
        )
    ).fetchone()
    if existing:
        conn.execute(cftprot_table.update().where(cftprot_table.c.id == existing.id).values(**row))
        return existing.id
    else:
        result = conn.execute(cftprot_table.insert().values(**row))
        return result.inserted_primary_key[0]


#CFTSSL

def insert_cftssl(conn, server_id: int, block: dict) -> int:
    row = {
        "server_id": server_id,
        "name": block.get("ID", ""),
        "direct": block.get("DIRECT"),
        "rootcid": block.get("ROOTCID"),
        "usercid": block.get("USERCID"),
        "userkey": block.get("USERKEY"),
        "version": block.get("VERSION"),
        "verify": block.get("VERIFY"),
        "ciphlist": block.get("CIPHLIST"),
        "raw_config": block.get("_raw", ""),
    }
    existing = conn.execute(
        cftssl_table.select().where(
            (cftssl_table.c.server_id == server_id) &
            (cftssl_table.c.name == row["name"])
        )
    ).fetchone()
    if existing:
        conn.execute(cftssl_table.update().where(cftssl_table.c.id == existing.id).values(**row))
        return existing.id
    else:
        result = conn.execute(cftssl_table.insert().values(**row))
        return result.inserted_primary_key[0]


#Partner

def insert_partner(conn, server_id: int, block: dict, tcp_map: dict) -> int:
    tcp_ref = block.get("TCP", "")
    tcp_id = tcp_map.get(tcp_ref)

    row = {
        "server_id": server_id,
        "name": block.get("ID", ""),
        "nrpart": block.get("NRPART"),
        "nspart": block.get("NSPART"),
        "prot": block.get("PROT"),
        "sap": block.get("SAP"),
        "state": block.get("STATE"),
        "commut": block.get("COMMUT"),
        "idf_list": block.get("IDF"),
        "cfttcp_id": tcp_id,
        "cfttcp_name": tcp_ref,
        "comment": block.get("COMMENT"),
        "raw_config": block.get("_raw", ""),
    }

    existing = conn.execute(
        partner_table.select().where(
            (partner_table.c.server_id == server_id) &
            (partner_table.c.name == row["name"])
        )
    ).fetchone()

    if existing:
        conn.execute(
            partner_table.update()
            .where(partner_table.c.id == existing.id)
            .values(**row)
        )
        return existing.id
    else:
        result = conn.execute(partner_table.insert().values(**row))
        return result.inserted_primary_key[0]


#Flow

def insert_flow(conn, server_id: int, partner_id: int, block: dict, cft_type: str) -> int:
    row = {
        "partner_id": partner_id,
        "server_id": server_id,
        "idf": block.get("ID", ""),
        "cft_type": cft_type,
        "ftype": block.get("FTYPE"),
        "fcode": block.get("FCODE"),
        "fname": block.get("FNAME"),
        "wfname": block.get("WFNAME"),
        "nfname": block.get("NFNAME"),
        "exec": block.get("EXEC"),
        "comment": block.get("COMMENT"),
        "raw_config": block.get("_raw", ""),
        "partner_list": block.get("PART"),
    }

    existing = conn.execute(
        flow_table.select().where(
            (flow_table.c.partner_id == partner_id) &
            (flow_table.c.idf == row["idf"]) &
            (flow_table.c.cft_type == cft_type)
        )
    ).fetchone()

    if existing:
        conn.execute(
            flow_table.update()
            .where(flow_table.c.id == existing.id)
            .values(**row)
        )
        return existing.id
    else:
        result = conn.execute(flow_table.insert().values(**row))
        return result.inserted_primary_key[0]


def expand_partner_list(part_value: str) -> list[str]:
    if not part_value:
        return []
    val = part_value.strip()
    if val.startswith("(") and val.endswith(")"):
        val = val[1:-1]
    return [p.strip() for p in val.split(",") if p.strip()]


#Processing (exit scripts)

def insert_processing(
    conn,
    server_id: int,
    flow_id: Optional[int],
    exit_info: dict,
    branch: Optional[dict] = None,
) -> int:
    row = {
        "flow_id": flow_id,
        "server_id": server_id,
        "script_path": exit_info["script_path"],
        "script_type": exit_info["script_type"],
        "bucket": exit_info["bucket"],
        "classification_notes": exit_info.get("classification_notes"),
        "migration_action": exit_info.get("migration_action"),
        "script_content": exit_info.get("script_content"),
        "calls_unknown_scripts": exit_info.get("calls_unknown_scripts", False),
        "unknown_script_paths": (
            json.dumps(exit_info.get("unknown_script_paths", []))
            if exit_info.get("unknown_script_paths") else None
        ),
        "branch_condition": branch["condition"] if branch else None,
        "branch_action": branch["action"] if branch else None,
        "branch_has_unknown_call": branch["has_unknown_call"] if branch else False,
    }
    result = conn.execute(processing_table.insert().values(**row))
    return result.inserted_primary_key[0]


#Bosco routes

def insert_bosco_route(conn, server_id: int, section: dict, route_type: str) -> int:
    row = {
        "server_id": server_id,
        "section_name": section.get("_section", ""),
        "route_type": route_type,
        "active": section.get("ACTIVE", "YES").upper() == "YES",
        "local_dir": section.get("LOCAL_DIR"),
        "backup_dir": section.get("BACKUP_DIR"),
        "dest_dir": section.get("DEST_DIR"),
        "archive_dir": section.get("ARCHIVE_DIR"),
        "remote_address": section.get("REMOTE_ADDRESS"),
        "remote_port": int(section["REMOTE_PORT"]) if section.get("REMOTE_PORT") else None,
        "remote_subdir": section.get("REMOTE_SUBDIR"),
        "file_mask": section.get("FILE_MASK"),
        "protocol": section.get("PROTOCOL"),
        "partner_ref": section.get("PARTNER"),
        "idf_ref": section.get("IDF"),
        "schedule": section.get("SCHEDULE"),
        "processing_app": section.get("PROCESSING_APP"),
        "comment": section.get("COMMENT"),
        "raw_config": section.get("_raw", ""),
    }

    existing = conn.execute(
        bosco_route_table.select().where(
            (bosco_route_table.c.server_id == server_id) &
            (bosco_route_table.c.section_name == row["section_name"]) &
            (bosco_route_table.c.route_type == route_type)
        )
    ).fetchone()

    if existing:
        conn.execute(
            bosco_route_table.update()
            .where(bosco_route_table.c.id == existing.id)
            .values(**row)
        )
        return existing.id
    else:
        result = conn.execute(bosco_route_table.insert().values(**row))
        return result.inserted_primary_key[0]


#Copilot activity

def insert_copilot_activity(conn, rows: list[dict]):
    if rows:
        conn.execute(copilot_activity_table.insert(), rows)
        log.info(f"  Inserted {len(rows)} Copilot activity records.")


#Copilot enrichment

def enrich_with_copilot(conn, copilot_rows: list[dict]):
    """Cross-reference Copilot activity data with partners and flows."""
    log.info("Enriching partners and flows with Copilot activity data...")

    partner_activity = {}
    flow_activity = {}

    for row in copilot_rows:
        sname = row["server_name"]
        pid = row["partner_id_ref"]
        idf = row["idf"]
        direction = row["direction"]

        pk = (sname, pid)
        if pk not in partner_activity:
            partner_activity[pk] = {
                "last_transfer_date": row["last_transfer_date"],
                "transfer_count_12m": 0,
                "avg_daily_volume": 0.0,
                "activity_status": "DORMANT",
                "is_active": False,
            }
        pa = partner_activity[pk]
        pa["transfer_count_12m"] += row["transfer_count_12m"]
        pa["avg_daily_volume"] += row["avg_daily_volume"]
        if row["last_transfer_date"] and (
            pa["last_transfer_date"] is None or
            row["last_transfer_date"] > pa["last_transfer_date"]
        ):
            pa["last_transfer_date"] = row["last_transfer_date"]
        if row["status_recommendation"] == "ACTIVE":
            pa["activity_status"] = "ACTIVE"
            pa["is_active"] = True
        elif row["status_recommendation"] == "ACTIVE_LOW" and pa["activity_status"] != "ACTIVE":
            pa["activity_status"] = "ACTIVE_LOW"
            pa["is_active"] = True

        cft_type = "SEND" if direction == "SEND" else "RECV"
        fk = (sname, pid, idf, cft_type)
        flow_activity[fk] = {
            "last_transfer_date": row["last_transfer_date"],
            "transfer_count_12m": row["transfer_count_12m"],
            "avg_daily_volume": row["avg_daily_volume"],
            "activity_status": row["status_recommendation"],
            "is_active": row["status_recommendation"] != "DORMANT",
        }

    servers = conn.execute(server_table.select()).fetchall()
    server_name_to_id = {s.name: s.id for s in servers}

    for (sname, pid), activity in partner_activity.items():
        sid = server_name_to_id.get(sname)
        if not sid:
            continue
        conn.execute(
            partner_table.update()
            .where(
                (partner_table.c.server_id == sid) &
                (partner_table.c.name == pid)
            )
            .values(
                is_active=activity["is_active"],
                last_transfer_date=activity["last_transfer_date"],
                transfer_count_12m=activity["transfer_count_12m"],
                avg_daily_volume=activity["avg_daily_volume"],
                activity_status=activity["activity_status"],
            )
        )

    for (sname, pid, idf, cft_type), activity in flow_activity.items():
        sid = server_name_to_id.get(sname)
        if not sid:
            continue
        partner = conn.execute(
            partner_table.select().where(
                (partner_table.c.server_id == sid) &
                (partner_table.c.name == pid)
            )
        ).fetchone()
        if not partner:
            continue
        conn.execute(
            flow_table.update()
            .where(
                (flow_table.c.partner_id == partner.id) &
                (flow_table.c.idf == idf) &
                (flow_table.c.cft_type == cft_type)
            )
            .values(
                is_active=activity["is_active"],
                last_transfer_date=activity["last_transfer_date"],
                transfer_count_12m=activity["transfer_count_12m"],
                avg_daily_volume=activity["avg_daily_volume"],
                activity_status=activity["activity_status"],
            )
        )

    log.info("  Copilot enrichment complete.")


#Migration stubs

def create_migration_stubs(conn):
    """Create initial migration records for all active flows."""
    log.info("Creating migration stubs for active flows...")

    flows = conn.execute(
        flow_table.select().where(flow_table.c.is_active == True)
    ).fetchall()

    count = 0
    for f in flows:
        existing = conn.execute(
            migration_table.select().where(migration_table.c.flow_id == f.id)
        ).fetchone()
        if existing:
            continue

        procs = conn.execute(
            processing_table.select().where(processing_table.c.flow_id == f.id)
        ).fetchall()

        complexity = "low"
        if procs:
            buckets = [p.bucket for p in procs if p.bucket]
            if "C" in buckets:
                complexity = "high"
            elif "B" in buckets:
                complexity = "medium"

        conn.execute(
            migration_table.insert().values(
                flow_id=f.id,
                status="pending",
                complexity=complexity,
                last_updated=datetime.utcnow(),
            )
        )
        count += 1

    log.info(f"  Created {count} migration stubs.")