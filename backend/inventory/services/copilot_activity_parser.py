from pathlib import Path
from datetime import datetime
import csv
def parse_copilot_csv(filepath: Path) -> list[dict]:
    """Parse the Copilot activity CSV export."""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "server_name": row["server_name"].strip(),
                "partner_id_ref": row["partner_id"].strip(),
                "idf": row["idf"].strip(),
                "direction": row["direction"].strip(),
                "last_transfer_date": (
                    datetime.strptime(row["last_transfer_date"].strip(), "%Y-%m-%d")
                    if row["last_transfer_date"].strip() else None
                ),
                "transfer_count_12m": int(row["transfer_count_12m"]),
                "avg_daily_volume": float(row["avg_daily_volume"]),
                "status_recommendation": row["status_recommendation"].strip(),
            })
    return rows