from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from migration_project.routers import (
    flows,
    partners,
    pipeline,
    scripts,
    servers,
    stats,
    transfers,
)

app = FastAPI(
    title="Stroom — CFT Inventory API",
    version="1.0.0",
    description="Phase 1 inventory API for the CFT-to-B2Bi migration platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(servers.router)
app.include_router(partners.router)
app.include_router(flows.router)
app.include_router(transfers.router)
app.include_router(scripts.router)
app.include_router(stats.router)
app.include_router(pipeline.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}