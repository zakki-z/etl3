from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from migration_project.routers import (
    b2bi_inbound_flows,
    b2bi_partner_deliveries,
    b2bi_partners,
    boscosend_configs,
    cft_tcp,
    communities,
    exceptions,
    flow_actions,
    flows,
    generation_jobs,
    mapping_rules,
    moncft_configs,
    partners,
    pipeline,
    scripts,
    servers,
    ssh_pull,
    stats,
    stg_cft_tcp,
    transfers,
)

app = FastAPI(
    title="Stroom — CFT Inventory API",
    version="2.0.0",
    description="Phase 1 inventory + Phase 2 generation API for the CFT-to-B2Bi migration platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Phase 1 routers ──────────────────────────────────────────────────────
app.include_router(servers.router)
app.include_router(partners.router)
app.include_router(flows.router)
app.include_router(transfers.router)
app.include_router(scripts.router)
app.include_router(stats.router)
app.include_router(pipeline.router)
app.include_router(cft_tcp.router)
app.include_router(flow_actions.router)
app.include_router(moncft_configs.router)
app.include_router(boscosend_configs.router)
app.include_router(stg_cft_tcp.router)
app.include_router(ssh_pull.router)

# ── B2Bi domain routers (current Phase 2 schema: per-row migration_status,
#    no more job/exception tracking) ────────────────────────────────────
app.include_router(communities.router)
app.include_router(b2bi_partners.router)
app.include_router(b2bi_partner_deliveries.router)
app.include_router(b2bi_inbound_flows.router)

# ── Legacy Phase 2 routers ───────────────────────────────────────────────
# WARNING: mapping_rule, generation_job, exception_log, and b2bi_config no
# longer exist in the live database (replaced by the B2Bi domain tables
# above). Every endpoint below will fail with "table doesn't exist" until
# these are either removed or pointed at the new schema.
app.include_router(mapping_rules.router)
app.include_router(generation_jobs.router)
app.include_router(exceptions.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}