from pathlib import Path
import re

def parse_bosco_config(filepath: Path) -> list[dict]:
    """
    Parse a Bosco INI-style config file into a list of section dicts.
    Format:
        [SECTION_NAME]
        KEY = VALUE
        ...
    """
    content = filepath.read_text(encoding="utf-8", errors="replace")
    sections = []
    current_section = None
    current_params = {}
    current_raw = []

    for line in content.splitlines():
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith("#"):
            continue

        # Section header
        section_match = re.match(r'^\[(.+)\]$', stripped)
        if section_match:
            if current_section:
                current_params["_section"] = current_section
                current_params["_raw"] = "\n".join(current_raw)
                sections.append(current_params)
            current_section = section_match.group(1)
            current_params = {}
            current_raw = [stripped]
            continue

        # Key = Value
        kv_match = re.match(r'^(\w+)\s*=\s*(.+)$', stripped)
        if kv_match and current_section:
            key = kv_match.group(1).upper()
            val = kv_match.group(2).strip()
            current_params[key] = val
            current_raw.append(stripped)

    # Last section
    if current_section:
        current_params["_section"] = current_section
        current_params["_raw"] = "\n".join(current_raw)
        sections.append(current_params)

    return sections