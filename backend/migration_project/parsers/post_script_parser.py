from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from migration_project.parsers.post_script_records import ParsedAction, ScopeType


# --- Direction inferred from the script file name ----------------------------
# Global scripts: RECVOK.bat / RECVNOK.bat / SENDOK.bat / SENDNOK.bat
# Specific scripts: file name appears in cft_flow.exec / cft_flow.exece
#                   we infer the direction the same way (RECV* -> recv, SEND* -> send).

_DIRECT_RECV_PREFIXES = ("RECVOK", "RECVNOK", "RECV_")
_DIRECT_SEND_PREFIXES = ("SENDOK", "SENDNOK", "SEND_")


def script_direction(script_name: str) -> Literal["recv", "send"] | None:
    upper = script_name.upper()
    if upper.startswith(_DIRECT_RECV_PREFIXES) or upper.startswith("RECV"):
        return "recv"
    if upper.startswith(_DIRECT_SEND_PREFIXES) or upper.startswith("SEND"):
        return "send"
    return None


# --- Line classification helpers --------------------------------------------

# Skip lines that are pure technical plumbing.
_TECHNICAL_KEYWORDS = (
    "echo off",
    "@echo off",
    "setlocal",
    "endlocal",
    "exit",
)

# Inline patterns we want to recognise.
_RE_LABEL = re.compile(r"^\s*:[A-Za-z0-9_\-]+\s*$")
_RE_GOTO = re.compile(r"^\s*goto\s+([A-Za-z0-9_\-]+)\s*$", re.IGNORECASE)

# Variants of "if &xxx==VALUE ..." (the rest is either a goto or an inline action).
# We tolerate spaces around == and a leading "@".
_RE_IF_VAR = re.compile(
    r"""^\s*(?:@)?\s*if\s+
        &(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*
        ==\s*
        (?P<value>[^\s\(\)]+)\s+
        (?P<rest>.+?)\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# "if &xxx==VALUE goto LABEL"
_RE_IF_GOTO = re.compile(
    r"""^\s*(?:@)?\s*if\s+
        &(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*
        ==\s*
        (?P<value>[^\s\(\)]+)\s+
        goto\s+(?P<label>[A-Za-z0-9_\-]+)\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _is_comment(line: str) -> bool:
    s = line.lstrip()
    if not s:
        return True
    upper = s.upper()
    return upper.startswith("REM ") or upper == "REM" or s.startswith("::")


def _is_technical(line: str) -> bool:
    """Return True for empty lines or batch plumbing (echo off, setlocal, exit, ...).

    NOTE: labels (':XYZ') and goto lines are intentionally NOT classified as
    technical here, because the caller needs to detect them explicitly to
    drive control flow.
    """
    s = line.strip().lower()
    if not s:
        return True
    for kw in _TECHNICAL_KEYWORDS:
        if s == kw or s.startswith(kw + " "):
            return True
    return False


def _contains_gmcft(line: str) -> bool:
    return "gmcft" in line.lower()


# --- Block / label utilities -------------------------------------------------


def _read_lines(file_path: Path) -> list[str]:
    with file_path.open("r", encoding="utf-8", errors="ignore") as fh:
        return [raw.rstrip("\r\n") for raw in fh]


def _build_label_index(lines: list[str]) -> dict[str, int]:
    """Map LABEL (lowercased) -> line index of the matching ':LABEL' line."""
    index: dict[str, int] = {}
    for i, raw in enumerate(lines):
        m = _RE_LABEL.match(raw)
        if m:
            label = raw.strip().lstrip(":").strip().lower()
            if label and label not in index:
                index[label] = i
    return index


def _block_lines(
    lines: list[str], label_index: dict[str, int], label: str
) -> list[str]:
    """Return all raw lines until next label / EOF / `goto :eof` / `exit`."""
    start = label_index.get(label.lower())
    if start is None:
        return []
    out: list[str] = []
    for raw in lines[start + 1 :]:
        if _RE_LABEL.match(raw):
            break
        s = raw.strip().lower()
        if s in ("goto :eof", "goto:eof"):
            break
        if s == "exit" or s.startswith("exit "):
            break
        out.append(raw)
    return out


# --- Action emission helpers -------------------------------------------------


class _ScopedOrderCounter:
    """Per-scope-key incremental counter.

    Each distinct (scope_type, scope_id) tuple gets its own 1-based sequence,
    so action_order restarts at 1 for every IDF / PART / IPART / IDF_SCRIPT
    appearing in a script.
    """

    def __init__(self) -> None:
        self._counters: dict[tuple, int] = {}

    def next(self, key: tuple) -> int:
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]


def _scope_key(
    scope: ScopeType,
    *,
    idf_code: str | None,
    flow_direct: Literal["recv", "send"] | None,
    partner_id: str | None,
    ipart_value: str | None,
) -> tuple:
    """Build the bucket key under which an action's order counter is tracked."""
    if scope == "IDF":
        return ("IDF", (idf_code or "").lower(), flow_direct or "")
    if scope == "PART":
        return ("PART", (partner_id or "").lower())
    if scope == "IPART":
        return ("IPART", (ipart_value or "").lower())
    if scope == "IDF_SCRIPT":
        return ("IDF_SCRIPT", (idf_code or "").lower())
    return ("GLOBAL",)


def _emit_with_scope(
    actions: list[ParsedAction],
    order: _ScopedOrderCounter,
    *,
    scope: ScopeType,
    raw_text: str,
    idf_code: str | None = None,
    flow_direct: Literal["recv", "send"] | None = None,
    partner_id: str | None = None,
    ipart_value: str | None = None,
    prefix: str | None = None,
) -> None:
    text = raw_text.strip()
    if not text:
        return
    if prefix:
        text = f"{prefix} {text}"
    if len(text) > 2000:
        text = text[:2000]
    key = _scope_key(
        scope,
        idf_code=idf_code,
        flow_direct=flow_direct,
        partner_id=partner_id,
        ipart_value=ipart_value,
    )
    actions.append(
        ParsedAction(
            scope_type=scope,
            action_order=order.next(key),
            action_text=text,
            idf_code=idf_code,
            flow_direct=flow_direct,
            partner_id=partner_id,
            ipart_value=ipart_value,
        )
    )


def _classify_inline_if(
    var: str,
    value: str,
    inline_action: str,
    direct: Literal["recv", "send"] | None,
) -> tuple[ScopeType, dict[str, str | None]]:
    """Map an inline 'if &VAR==VAL <action>' to a scope + scope hints."""
    var_l = var.lower()
    if var_l == "idf":
        return "IDF", {"idf_code": value, "flow_direct": direct}
    if var_l == "part":
        return "PART", {"partner_id": value}
    if var_l == "ipart":
        return "IPART", {"ipart_value": value}
    return "GLOBAL", {}


# --- Main parser entry points -----------------------------------------------


def parse_global_script(
    file_path: Path, *, direct: Literal["recv", "send"] | None
) -> list[ParsedAction]:
    """Parse a global RECVOK / RECVNOK / SENDOK / SENDNOK script.

    Rules (validated with the user):
      * Skip empty lines, REM/::, echo off, setlocal/endlocal, exit, labels, goto.
      * Skip ANY line containing 'gmCft*'.
      * Top level: only capture lines starting with 'if &xxx==V ...'.
        - If 'goto LABEL': descend into the label's block and capture every
          actionable line of that block, prefixed by the matching condition.
        - Otherwise: inline action -> capture with the inferred scope.
      * Non-conditional / default goto blocks are NOT captured for global scripts.
    """
    return _parse_script(file_path, direct=direct, mode="global")


def parse_specific_script(
    file_path: Path, *, direct: Literal["recv", "send"] | None, idf_code: str
) -> list[ParsedAction]:
    """Parse a script referenced by cft_flow.exec / cft_flow.exece (specific to one IDF).

    Rules (validated with the user):
      * All emitted actions get scope = IDF_SCRIPT, idf_code = the bound IDF.
      * Skip the same plumbing as global scripts and any line with 'gmCft*'.
      * Inline 'if &part==X <action>' / 'if &ipart==Y <action>' are kept as-is
        (the condition is preserved verbatim in action_text).
      * 'if &xxx==V goto LABEL' descends into the block; every captured line
        is prefixed by 'if &xxx==V' to keep the condition trace.
      * Unconditional 'goto LABEL' also descends and captures the block lines
        (no prefix), still under IDF_SCRIPT.
    """
    return _parse_script(
        file_path, direct=direct, mode="specific", bound_idf_code=idf_code
    )


def _parse_script(
    file_path: Path,
    *,
    direct: Literal["recv", "send"] | None,
    mode: Literal["global", "specific"],
    bound_idf_code: str | None = None,
) -> list[ParsedAction]:
    lines = _read_lines(file_path)
    label_index = _build_label_index(lines)
    actions: list[ParsedAction] = []
    order = _ScopedOrderCounter()

    # Tracks labels we've already expanded from the top-level (some scripts
    # `goto LABEL` and then label code follows; we only walk it once).
    visited_labels: set[str] = set()

    # Top-level walk
    i = 0
    in_executable_top_level = True
    while i < len(lines):
        raw = lines[i]
        i += 1

        # Once we hit a label at top-level, stop linear walking: subsequent
        # lines belong to that label and are only reached via goto.
        if _RE_LABEL.match(raw):
            in_executable_top_level = False
            continue
        if not in_executable_top_level:
            continue

        if _is_comment(raw):
            continue
        if _contains_gmcft(raw):
            continue
        if _is_technical(raw):
            continue

        # 1) "if &VAR==V goto LABEL" -> descend
        m_goto = _RE_IF_GOTO.match(raw)
        if m_goto:
            var = m_goto.group("var")
            value = m_goto.group("value")
            label = m_goto.group("label")
            if label.lower() in visited_labels:
                continue
            visited_labels.add(label.lower())
            _emit_block(
                actions,
                order,
                lines=lines,
                label_index=label_index,
                label=label,
                direct=direct,
                mode=mode,
                bound_idf_code=bound_idf_code,
                triggering_var=var,
                triggering_value=value,
            )
            continue

        # 2) "if &VAR==V <action>" -> inline action
        m_if = _RE_IF_VAR.match(raw)
        if m_if:
            var = m_if.group("var")
            value = m_if.group("value")
            rest = m_if.group("rest").strip()

            # Defensive: a goto would have matched the previous regex, but
            # just in case the rest starts with 'goto' (different spacing).
            if re.match(r"^goto\s+\S+\s*$", rest, re.IGNORECASE):
                continue

            if mode == "specific":
                # Keep full original line (condition included).
                _emit_with_scope(
                    actions, order,
                    scope="IDF_SCRIPT",
                    raw_text=raw,
                    idf_code=bound_idf_code,
                    flow_direct=direct,
                )
            else:
                scope, hints = _classify_inline_if(var, value, rest, direct)
                if scope == "GLOBAL":
                    # Unknown variable: keep as global with the full line.
                    _emit_with_scope(actions, order, scope="GLOBAL", raw_text=raw)
                else:
                    _emit_with_scope(
                        actions, order,
                        scope=scope,
                        raw_text=rest,
                        idf_code=hints.get("idf_code"),  # type: ignore[arg-type]
                        flow_direct=hints.get("flow_direct"),  # type: ignore[arg-type]
                        partner_id=hints.get("partner_id"),  # type: ignore[arg-type]
                        ipart_value=hints.get("ipart_value"),  # type: ignore[arg-type]
                    )
            continue

        # 3) Unconditional `goto LABEL`
        m_unc_goto = _RE_GOTO.match(raw)
        if m_unc_goto:
            label = m_unc_goto.group(1)
            if label.lower() in visited_labels:
                continue
            visited_labels.add(label.lower())
            if mode == "specific":
                # In specific scripts, follow the goto and capture lines
                # under IDF_SCRIPT (no prefix).
                _emit_block(
                    actions,
                    order,
                    lines=lines,
                    label_index=label_index,
                    label=label,
                    direct=direct,
                    mode=mode,
                    bound_idf_code=bound_idf_code,
                    triggering_var=None,
                    triggering_value=None,
                )
            # In global mode, default/unconditional goto blocks are skipped.
            continue

        # 4) Plain top-level command
        if mode == "specific":
            _emit_with_scope(
                actions, order,
                scope="IDF_SCRIPT",
                raw_text=raw,
                idf_code=bound_idf_code,
                flow_direct=direct,
            )
        # In global mode, plain top-level commands are NOT captured.

    return actions


def _emit_block(
    actions: list[ParsedAction],
    order: _ScopedOrderCounter,
    *,
    lines: list[str],
    label_index: dict[str, int],
    label: str,
    direct: Literal["recv", "send"] | None,
    mode: Literal["global", "specific"],
    bound_idf_code: str | None,
    triggering_var: str | None,
    triggering_value: str | None,
) -> None:
    """Walk a labelled block and emit captured lines.

    For global scripts:
      * triggering_var/value are mandatory (we only descend through `if &x==v goto`).
      * scope is derived from triggering_var (idf -> IDF, part -> PART, ipart -> IPART,
        unknown -> GLOBAL).
      * Each captured line keeps its original text (no prefix), since the
        triggering condition is the scope itself.

    For specific scripts:
      * scope is always IDF_SCRIPT with idf_code = bound_idf_code.
      * If triggering_var/value are provided, every captured line is prefixed by
        'if &VAR==VALUE' to keep the condition trace.
    """
    block = _block_lines(lines, label_index, label)
    if not block:
        return

    # Pre-compute scope + hints for global mode.
    if mode == "global":
        if triggering_var is None or triggering_value is None:
            return  # Defensive: should never happen for global scripts.
        scope, hints = _classify_inline_if(
            triggering_var, triggering_value, "", direct
        )
    else:
        scope = "IDF_SCRIPT"
        hints = {}

    prefix: str | None = None
    if mode == "specific" and triggering_var and triggering_value:
        prefix = f"if &{triggering_var}=={triggering_value}"

    for raw in block:
        if _is_comment(raw):
            continue
        if _contains_gmcft(raw):
            continue
        if _is_technical(raw):
            continue

        # Allow nested 'if &VAR==V ...' lines: keep them verbatim.
        # Allow plain commands too.
        if _RE_GOTO.match(raw):
            # Don't recurse into further gotos to keep things simple
            # (the user examples don't require deeper recursion).
            continue

        if mode == "global":
            _emit_with_scope(
                actions, order,
                scope=scope,
                raw_text=raw,
                idf_code=hints.get("idf_code"),  # type: ignore[arg-type]
                flow_direct=hints.get("flow_direct"),  # type: ignore[arg-type]
                partner_id=hints.get("partner_id"),  # type: ignore[arg-type]
                ipart_value=hints.get("ipart_value"),  # type: ignore[arg-type]
            )
        else:
            _emit_with_scope(
                actions, order,
                scope="IDF_SCRIPT",
                raw_text=raw,
                idf_code=bound_idf_code,
                flow_direct=direct,
                prefix=prefix,
            )
