from pathlib import Path
import re
BUCKET_PATTERN = re.compile(
    r"Classification:\s*Bucket\s+([ABC])", re.IGNORECASE
)

def classify_exit_script(filepath: Path) -> dict:
    """
    Parse a .bat exit script to extract:
    - script_type (EXITEOT, EXITBOT, EXITDIR, EXITFILE)
    - bucket classification (A, B, C)
    - whether it calls unknown external scripts
    - list of unknown script paths
    - per-branch conditions: list of dicts, one per IF block found in the script
      Each dict: { 'condition': str, 'action': str, 'has_unknown_call': bool }
    """
    content = filepath.read_text(encoding="utf-8", errors="replace")
    filename = filepath.name.lower()

    result = {
        "script_path": str(filepath),
        "script_type": "EXITEOT",
        "bucket": None,
        "classification_notes": None,
        "script_content": content,
        "calls_unknown_scripts": False,
        "unknown_script_paths": [],
        "branches": [],  # NEW — list of per-branch dicts
    }

    # Determine exit type from filename
    if "exitdir" in filename:
        result["script_type"] = "EXITDIR"
    elif "exitbot" in filename:
        result["script_type"] = "EXITBOT"
    elif "exitfile" in filename:
        result["script_type"] = "EXITFILE"
    else:
        result["script_type"] = "EXITEOT"

    # Extract bucket classification from REM comments
    bucket_match = BUCKET_PATTERN.search(content)
    if bucket_match:
        result["bucket"] = bucket_match.group(1).upper()

    # Extract classification notes
    for line in content.splitlines():
        line_s = line.strip()
        if line_s.startswith("REM") and "Classification:" in line_s:
            notes = line_s.split("Classification:", 1)[1].strip()
            result["classification_notes"] = notes
            break

    # ── Extract per-branch conditions ─────────────────────────────────────
    # Matches patterns like:
    #   IF "%IDF%"=="ICSCPT" (
    #   IF /I "%PART%"=="BNKFR01" (
    #   IF "%IDF%"=="SEPAXML" IF "%PART%"=="SGENPRD" (
    #   IF ERRORLEVEL 1 (   ← not a partner/IDF condition, skip
    branch_pattern = re.compile(
        r'IF\s+(?:/I\s+)?'                          # IF or IF /I
        r'(?P<cond>'
        r'"%(?:IDF|PART|PARTENAIRE|PARTNER)%"\s*==\s*"[^"]*"'  # IDF or PART check
        r'(?:\s+IF\s+(?:/I\s+)?"%(?:IDF|PART|PARTENAIRE|PARTNER)%"\s*==\s*"[^"]*")*'  # chained
        r')'
        r'\s*\(',                                   # opening paren of block
        re.IGNORECASE
    )

    lines = content.splitlines()

    for i, line in enumerate(lines):
        m = branch_pattern.search(line)
        if not m:
            continue

        raw_condition = m.group("cond").strip()

        # Normalize condition into readable form:
        # '"%IDF%"=="ICSCPT"' → 'IDF == ICSCPT'
        normalized = re.sub(
            r'"%?(IDF|PART|PARTENAIRE|PARTNER)%?"\s*==\s*"([^"]*)"',
            lambda x: f"{x.group(1).upper()} == {x.group(2)}",
            raw_condition,
            flags=re.IGNORECASE
        )
        # Clean up chained IF
        normalized = re.sub(r'\s+IF\s+(?:/I\s+)?', ' AND ', normalized, flags=re.IGNORECASE).strip()

        # Collect the body of this IF block (lines between the opening ( and closing ))
        # Simple approach: grab lines until we hit the matching closing paren
        body_lines = []
        depth = 0
        for j in range(i, min(i + 50, len(lines))):  # look ahead up to 50 lines
            body_line = lines[j]
            depth += body_line.count("(") - body_line.count(")")
            if j > i:
                body_lines.append(body_line.strip())
            if depth <= 0 and j > i:
                break

        branch_body = "\n".join(body_lines)

        # Detect unknown calls within this branch
        branch_unknown = False
        branch_unknown_paths = []

        call_pattern = re.compile(r'call\s+"?([^"\s]+\.bat)"?', re.IGNORECASE)
        for cm in call_pattern.finditer(branch_body):
            called_path = cm.group(1)
            if "LEGACY" in called_path.upper() or "\\Axway\\CFT\\exits\\" not in called_path:
                if "send_alert" not in called_path.lower():
                    branch_unknown = True
                    branch_unknown_paths.append(called_path)
                    if called_path not in result["unknown_script_paths"]:
                        result["unknown_script_paths"].append(called_path)
                        result["calls_unknown_scripts"] = True

        # Summarize what the branch does (first meaningful non-REM line)
        action_summary = None
        for bl in body_lines:
            if bl and not bl.upper().startswith("REM") and not bl.startswith(")"):
                action_summary = bl[:200]  # cap length
                break

        result["branches"].append({
            "condition": normalized,
            "action": action_summary,
            "has_unknown_call": branch_unknown,
            "unknown_paths": branch_unknown_paths,
        })

    # Detect unknown calls at the global level (outside any IF block)
    call_pattern = re.compile(r'call\s+"?([^"\s]+\.bat)"?', re.IGNORECASE)
    exe_pattern = re.compile(r'([A-Z]:\\[^\s"]+\.exe)', re.IGNORECASE)

    for m in call_pattern.finditer(content):
        called_path = m.group(1)
        if "send_alert" in called_path.lower() or "relay_to_prod" in called_path.lower():
            continue
        if "LEGACY" in called_path.upper() or "\\Axway\\CFT\\exits\\" not in called_path:
            if called_path not in result["unknown_script_paths"]:
                result["unknown_script_paths"].append(called_path)
                result["calls_unknown_scripts"] = True

    for m in exe_pattern.finditer(content):
        exe_path = m.group(1)
        if "LEGACY" in exe_path.upper():
            if exe_path not in result["unknown_script_paths"]:
                result["unknown_script_paths"].append(exe_path)
                result["calls_unknown_scripts"] = True

    return result