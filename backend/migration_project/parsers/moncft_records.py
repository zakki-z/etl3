from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonCftRepertoire:
    """One '[Repertoire : N]' section from a C2I_MonCft<XXX>.ini file."""

    idf_code: str
    partner_code: str
    fname: str | None
    filtre: str | None
    parm: str | None
    nfname: str | None
    sappl: str | None
    rappl: str | None
    suser: str | None
