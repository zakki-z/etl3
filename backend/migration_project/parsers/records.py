from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PartnerRecord:
    conf_id: str
    nspart: str | None
    nrpart: str | None
    ipart: str | None
    sap: str | None
    nspassw: str | None
    nrpassw: str | None
    ssl: int


@dataclass(frozen=True)
class TcpRecord:
    conf_id: str
    cnxout: str | None
    host: str | None


@dataclass(frozen=True)
class FlowRecord:
    idf_code: str
    direct: Literal["send", "recv"]
    fcode: str | None
    ftype: str | None
    flrecl: str | None
    frecfm: str | None
    fname: str | None
    xlate: int
    exec: str | None
    exece: str | None
