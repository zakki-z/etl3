from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ScopeType = Literal["GLOBAL", "IDF", "PART", "IPART", "IDF_SCRIPT"]


@dataclass(frozen=True)
class ParsedAction:
    """One parsed action line, with its scope hints.

    For IDF / IDF_SCRIPT : idf_code + flow_direct identify the cft_flow row.
    For PART  : partner_id is the resolved cft_partner.id (== nrpart in conf).
    For IPART : ipart_value is the raw &ipart literal.
    For GLOBAL: no extra hint.
    """

    scope_type: ScopeType
    action_order: int
    action_text: str
    idf_code: str | None = None
    flow_direct: Literal["recv", "send"] | None = None
    partner_id: str | None = None
    ipart_value: str | None = None
