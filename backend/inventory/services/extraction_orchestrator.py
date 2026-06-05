"""
Discovers server directories, parses CFT configs / exit scripts /
Bosco routes / Copilot CSVs, and loads everything into the database.
"""

import logging
import re
from pathlib import Path

from sqlalchemy import create_engine, text

from ..models import (
    server_table, cfttcp_table, cftprot_table, cftssl_table,
    partner_table, flow_table, processing_table,
    bosco_route_table, copilot_activity_table, migration_table,
)
from .cft_config_parser import parse_cft_blocks, extract_server_info
from .exit_script_parser import classify_exit_script
from .bosco_config_parser import parse_bosco_config
from .copilot_activity_parser import parse_copilot_csv
from .database_operations import (
    create_schema, drop_schema,
    upsert_server, insert_cfttcp, insert_partner, insert_flow,
    expand_partner_list, insert_processing, insert_bosco_route,
    insert_copilot_activity, insert_cftprot, insert_cftssl,
    enrich_with_copilot, create_migration_stubs,
)

log = logging.getLogger("cft_extractor")


def process_server_directory(conn, server_dir: Path):
    """Process one server directory: config, exits, bosco."""
    dir_name = server_dir.name
    log.info(f"{'='*60}")
    log.info(f"Processing server: {dir_name}")
    log.info(f"{'='*60}")

    #1. Parse CFTUTIL export
    config_dir = server_dir / "config"
    cfg_files = list(config_dir.glob("*.cfg")) if config_dir.exists() else []

    if not cfg_files:
        log.warning(f"  No .cfg files found in {config_dir}")
        return

    cfg_file = cfg_files[0]
    log.info(f"  Parsing CFT export: {cfg_file.name}")
    cfg_text = cfg_file.read_text(encoding="utf-8", errors="replace")

    server_info = extract_server_info(cfg_text, dir_name)
    server_id = upsert_server(conn, server_info)
    log.info(f"  Server '{server_info['name']}' → ID {server_id}")

    blocks = parse_cft_blocks(cfg_text)
    log.info(f"  Parsed {len(blocks)} CFT blocks")

    tcp_blocks = [b for b in blocks if b["_type"] == "CFTTCP"]
    part_blocks = [b for b in blocks if b["_type"] == "CFTPART"]
    send_blocks = [b for b in blocks if b["_type"] == "CFTSEND"]
    recv_blocks = [b for b in blocks if b["_type"] == "CFTRECV"]
    prot_blocks = [b for b in blocks if b["_type"] == "CFTPROT"]
    ssl_blocks = [b for b in blocks if b["_type"] == "CFTSSL"]

    #2. Insert CFTPROT and CFTSSL
    for block in prot_blocks:
        insert_cftprot(conn, server_id, block)
    log.info(f"  Inserted {len(prot_blocks)} CFTPROT records")

    for block in ssl_blocks:
        insert_cftssl(conn, server_id, block)
    log.info(f"  Inserted {len(ssl_blocks)} CFTSSL records")

    #3. Insert CFTTCP
    tcp_map = {}
    for block in tcp_blocks:
        tcp_id = insert_cfttcp(conn, server_id, block)
        tcp_map[block.get("ID", "")] = tcp_id
    log.info(f"  Inserted {len(tcp_blocks)} CFTTCP records")

    #4. Insert CFTPART
    partner_map = {}
    for block in part_blocks:
        pid = insert_partner(conn, server_id, block, tcp_map)
        partner_map[block.get("ID", "")] = pid
    log.info(f"  Inserted {len(part_blocks)} partner records")

    #5. Insert CFTSEND/CFTRECV as flows
    flow_map = {}
    flow_count = 0

    for block in send_blocks:
        partners = expand_partner_list(block.get("PART", ""))
        idf = block.get("ID", "")
        for pname in partners:
            pid = partner_map.get(pname)
            if not pid:
                log.warning(f"  CFTSEND references unknown partner '{pname}' — skipping")
                continue
            fid = insert_flow(conn, server_id, pid, block, "SEND")
            flow_map[(pname, idf, "SEND")] = fid
            flow_count += 1

    for block in recv_blocks:
        partners = expand_partner_list(block.get("PART", ""))
        idf = block.get("ID", "")
        for pname in partners:
            pid = partner_map.get(pname)
            if not pid:
                log.warning(f"  CFTRECV references unknown partner '{pname}' — skipping")
                continue
            fid = insert_flow(conn, server_id, pid, block, "RECV")
            flow_map[(pname, idf, "RECV")] = fid
            flow_count += 1

    log.info(f"  Inserted {flow_count} flow records (SEND + RECV)")

    #6. Parse and insert exit scripts
    exits_dir = server_dir / "exits"
    exit_count = 0

    idf_to_flows: dict[str, list[int]] = {}
    part_to_flows: dict[str, list[int]] = {}

    for (pname, idf, cft_type), fid in flow_map.items():
        idf_to_flows.setdefault(idf.upper(), []).append(fid)
        part_to_flows.setdefault(pname.upper(), []).append(fid)

    exec_to_flows: dict[str, list[int]] = {}
    for (pname, idf, cft_type), fid in flow_map.items():
        flow_rec = conn.execute(
            flow_table.select().where(flow_table.c.id == fid)
        ).fetchone()
        if flow_rec and flow_rec._mapping.get("exec"):
            exec_path = flow_rec._mapping["exec"]
            exec_basename = exec_path.replace("\\", "/").split("/")[-1].lower()
            exec_to_flows.setdefault(exec_basename, []).append(fid)

    if exits_dir.exists():
        for bat_file in sorted(exits_dir.glob("*.bat")):
            exit_info = classify_exit_script(bat_file)
            bat_name = bat_file.name.lower()
            branches = exit_info.get("branches", [])

            linked_flow_ids = exec_to_flows.get(bat_name, [])

            if not linked_flow_ids:
                insert_processing(conn, server_id, None, exit_info, branch=None)
                exit_count += 1
                continue

            if not branches:
                for fid in linked_flow_ids:
                    insert_processing(conn, server_id, fid, exit_info, branch=None)
                    exit_count += 1
                continue

            for fid in linked_flow_ids:
                flow_rec = conn.execute(
                    flow_table.select().where(flow_table.c.id == fid)
                ).fetchone()
                if not flow_rec:
                    continue

                flow_idf = (flow_rec.idf or "").upper()

                partner_rec = conn.execute(
                    partner_table.select().where(
                        partner_table.c.id == flow_rec.partner_id
                    )
                ).fetchone()
                flow_part = (partner_rec.name if partner_rec else "").upper()

                matched_branches = []
                for branch in branches:
                    condition = branch["condition"]
                    terms = re.findall(
                        r'(IDF|PART|PARTENAIRE|PARTNER)\s*==\s*(\S+)',
                        condition,
                        re.IGNORECASE,
                    )

                    match = True
                    for key, val in terms:
                        key = key.upper()
                        val = val.upper()
                        if key == "IDF" and flow_idf != val:
                            match = False
                            break
                        if key in ("PART", "PARTENAIRE", "PARTNER") and flow_part != val:
                            match = False
                            break

                    if match:
                        matched_branches.append(branch)

                if matched_branches:
                    for branch in matched_branches:
                        insert_processing(conn, server_id, fid, exit_info, branch=branch)
                        exit_count += 1
                else:
                    insert_processing(conn, server_id, fid, exit_info, branch=None)
                    exit_count += 1

    log.info(f"  Inserted {exit_count} exit script records")

    #7. Parse and insert Bosco configs
    bosco_send_dir = server_dir / "bosco_send"
    bosco_recv_dir = server_dir / "bosco_receive"
    bosco_count = 0

    if bosco_send_dir.exists():
        for cfg in bosco_send_dir.glob("*.cfg"):
            sections = parse_bosco_config(cfg)
            for section in sections:
                flow_id = None
                partner_ref = section.get("PARTNER", "")
                idf_ref = section.get("IDF", "")
                if partner_ref and idf_ref:
                    flow_id = flow_map.get((partner_ref, idf_ref, "SEND"))

                bid = insert_bosco_route(conn, server_id, section, "BOSCO_SEND")
                if flow_id:
                    conn.execute(
                        bosco_route_table.update()
                        .where(bosco_route_table.c.id == bid)
                        .values(flow_id=flow_id)
                    )
                bosco_count += 1

    if bosco_recv_dir.exists():
        for cfg in bosco_recv_dir.glob("*.cfg"):
            sections = parse_bosco_config(cfg)
            for section in sections:
                insert_bosco_route(conn, server_id, section, "BOSCO_RECV")
                bosco_count += 1

    log.info(f"  Inserted {bosco_count} Bosco route records")


def run_extraction(data_dir: str, db_url: str, reset: bool = False):
    """Main entry point: discover servers, parse, load."""
    data_path = Path(data_dir)
    if not data_path.exists():
        log.error(f"Data directory not found: {data_dir}")
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    log.info(f"Data directory: {data_path}")
    log.info(f"Database URL:   {db_url.split('@')[0] if '@' in db_url else db_url[:30]}@***")

    engine = create_engine(db_url, echo=False)

    if reset:
        log.warning("RESET mode — dropping all tables first!")
        drop_schema(engine)

    create_schema(engine)

    with engine.begin() as conn:
        #Discover server directories
        server_dirs = sorted([
            d for d in data_path.iterdir()
            if d.is_dir() and d.name.startswith("server_cft")
        ])

        if not server_dirs:
            log.warning("No server_cft_* directories found. Looking for config files directly...")
            if (data_path / "config").exists():
                server_dirs = [data_path]

        log.info(f"Found {len(server_dirs)} server directories")

        for server_dir in server_dirs:
            process_server_directory(conn, server_dir)

        #Process Copilot activity data
        copilot_dir = data_path / "copilot"
        copilot_files = list(copilot_dir.glob("*.csv")) if copilot_dir.exists() else []

        copilot_rows = []
        for cf in copilot_files:
            log.info(f"Parsing Copilot activity: {cf.name}")
            rows = parse_copilot_csv(cf)
            copilot_rows.extend(rows)

        if copilot_rows:
            insert_copilot_activity(conn, copilot_rows)
            enrich_with_copilot(conn, copilot_rows)

        #Create migration stubs
        create_migration_stubs(conn)

    #Summary
    log.info("")
    log.info("=" * 60)
    log.info("EXTRACTION COMPLETE — Summary")
    log.info("=" * 60)

    with engine.connect() as conn:
        tables_to_count = [
            ("server", server_table),
            ("cfttcp", cfttcp_table),
            ("cftprot", cftprot_table),
            ("cftssl", cftssl_table),
            ("partner", partner_table),
            ("flow", flow_table),
            ("processing", processing_table),
            ("bosco_route", bosco_route_table),
            ("copilot_activity", copilot_activity_table),
            ("migration", migration_table),
        ]
        for name, tbl in tables_to_count:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar()
            log.info(f"  {name:25s} {count:>6d} records")

    log.info("")
    log.info("Done. Database is ready for Phase 1 inventory queries.")
