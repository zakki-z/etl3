import re
from datetime import datetime

CFT_BLOCK_TYPES = {
    "CFTPARM", "CFTNET", "CFTPROT", "CFTSSL",
    "CFTTCP", "CFTPART", "CFTSEND", "CFTRECV",
}
def strip_quotes(val: str) -> str:
    """Remove surrounding single quotes from a CFT parameter value."""
    val = val.strip()
    if len(val) >= 2 and val[0] == "'" and val[-1] == "'":
        return val[1:-1]
    return val


def parse_cft_blocks(cfg_text: str) -> list[dict]:
    """
    Parse a CFTUTIL export into a list of blocks.
    Each block is a dict: { '_type': 'CFTTCP', 'ID': '...', 'HOST': '...', ... , '_raw': '...' }

    The CFT export format:
        BLOCK_TYPE  PARAM1 = VALUE1,
                    PARAM2 = VALUE2,
                    ...
                    PARAMN = VALUEN

    Values can be:
        - Simple: HOST = 192.168.10.50
        - Quoted: COMMENT = 'Some text'
        - List:   IDF = (SEPAXML,SCTSND,SCTRSP)
        - Multi-line quoted strings (rare in our exports)
    """
    # Remove /* ... */ comments
    text = re.sub(r'/\*.*?\*/', '', cfg_text, flags=re.DOTALL)

    blocks = []
    current_block_type = None
    current_raw_lines = []
    current_params = {}

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this line starts a new block
        block_match = re.match(r'^(CFT\w+)\s+(.*)', stripped)
        if block_match and block_match.group(1) in CFT_BLOCK_TYPES:
            # Save previous block if any
            if current_block_type:
                current_params["_type"] = current_block_type
                current_params["_raw"] = "\n".join(current_raw_lines)
                blocks.append(current_params)

            current_block_type = block_match.group(1)
            current_raw_lines = [stripped]
            current_params = {}
            rest = block_match.group(2)
        else:
            if current_block_type:
                current_raw_lines.append(stripped)
                rest = stripped
            else:
                continue

        # Parse KEY = VALUE pairs from the line
        # Handle trailing commas (continuation) and strip them
        rest = rest.rstrip(",").strip()

        # Split on commas that are NOT inside parentheses or quotes
        # We do a simpler approach: find all KEY = VALUE segments
        param_pattern = re.compile(
            r'(\w+)\s*=\s*('
            r"'[^']*'"          # quoted string
            r'|\([^)]*\)'       # parenthesized list
            r'|[^,\s]+'         # simple value
            r')'
        )
        for m in param_pattern.finditer(rest):
            key = m.group(1).upper()
            val = m.group(2).strip()

            # Handle parenthesized lists → store as comma-separated string
            if val.startswith("(") and val.endswith(")"):
                val = val[1:-1]  # remove parens, keep comma-separated

            val = strip_quotes(val)
            current_params[key] = val

    # Don't forget the last block
    if current_block_type:
        current_params["_type"] = current_block_type
        current_params["_raw"] = "\n".join(current_raw_lines)
        blocks.append(current_params)

    return blocks


def extract_server_info(cfg_text: str, dir_name: str) -> dict:
    """Extract server metadata from the CFTUTIL export header comments."""
    info = {
        "name": dir_name.upper().replace("SERVER_", ""),
        "ip_address": None,
        "environment": "PROD",
        "install_path": None,
        "os_info": None,
        "raw_export_date": None,
        "comment": None,
    }

    # Parse header comments
    header = cfg_text[:2000]

    m = re.search(r'Export Date:\s*(\d{4}-\d{2}-\d{2}\s+[\d:]+)', header)
    if m:
        try:
            info["raw_export_date"] = datetime.strptime(m.group(1).strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    m = re.search(r'Server:\s*(\S+)', header)
    if m:
        server_full = m.group(1)
        info["comment"] = f"Server hostname: {server_full}"

    m = re.search(r'Install Path:\s*(.+?)(?:\s*\*|$)', header, re.MULTILINE)
    if m:
        info["install_path"] = m.group(1).strip()

    m = re.search(r'Windows Server\s+\d+', header)
    if m:
        info["os_info"] = m.group(0)

    # Determine environment from name
    name_lower = dir_name.lower()
    if "dmz" in name_lower:
        info["environment"] = "DMZ"
    elif "recette" in name_lower or "test" in name_lower:
        info["environment"] = "RECETTE"
    else:
        info["environment"] = "PROD"

    # Extract IP from CFTNET block and CFTPARM ID
    blocks = parse_cft_blocks(cfg_text)
    parm_id = None
    for b in blocks:
        if b.get("_type") == "CFTNET" and not info["ip_address"]:
            info["ip_address"] = b.get("HOST")
        if b.get("_type") == "CFTPARM":
            parm_id = b.get("ID", "")

    # Use directory-based name (e.g. CFT_PROD1) as canonical name
    # because Copilot activity data references this convention,
    # not the CFTPARM ID (e.g. TESSI_PROD1).
    # Store CFTPARM ID in the comment for reference.
    canonical = dir_name.upper().replace("SERVER_", "")
    info["name"] = canonical
    if parm_id:
        info["comment"] = (info.get("comment") or "") + f" | CFTPARM ID: {parm_id}"

    return info