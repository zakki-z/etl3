from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FlowContext:
    """Minimal CFT flow data relevant for B2Bi generation."""
    idf_code: str
    direct: str          # 'send' | 'recv'
    fcode: str | None
    ftype: str | None
    fname: str | None
    xlate: int           # 0 | 1
    exec: str | None
    exece: str | None


@dataclass
class PartnerContext:
    """All CFT data for a single partner, ready for the generation engine."""
    partner_id: str
    nspart: str | None
    nrpart: str | None
    ssl: int             # 0 | 1
    sap: str | None
    host: str | None
    cnxout: str | None   # raw CNXOUT value (e.g. '3')
    flows: list[FlowContext] = field(default_factory=list)
    # True when at least one post-script is Bucket C (blocking)
    has_bucket_c_script: bool = False
