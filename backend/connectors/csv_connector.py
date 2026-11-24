import csv
import io
from pathlib import Path

REQUIRED = {"name", "latitude", "longitude"}


def _parse_rows(handle):
    """Parse an open text handle into normalized source records.

    Header names are trimmed and lower-cased so files exported with headings such as
    "Name,Latitude,Longitude" work the same as "name,latitude,longitude".
    """
    reader = csv.DictReader(handle)
    reader.fieldnames = [(x or "").strip().lower() for x in (reader.fieldnames or [])]
    missing = REQUIRED - set(reader.fieldnames)
    if missing:
        raise ValueError("CSV missing required columns: " + ", ".join(sorted(missing)))
    rows = []
    for i, row in enumerate(reader, start=2):
        try:
            lat = float(row.get("latitude"))
            lon = float(row.get("longitude"))
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        name = (row.get("name") or "").strip()
        if not name:
            continue
        rows.append({
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "category": (row.get("category") or "").strip() or "Unknown",
            "location": (row.get("location") or "").strip(),
            "website": (row.get("website") or "").strip(),
            "distance_km": None,
            "source": "Approved CSV Dataset",
            "source_record_id": str(i),
            "source_url": (row.get("source_url") or "").strip(),
            "snippet": "Imported from user-provided approved dataset",
        })
    return rows


def load_approved_csv(path: str):
    """Import a user-provided dataset only when the user has permission to reuse it.
    Required columns: name, latitude, longitude. Optional: category, location, website, source_url.
    """
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return _parse_rows(f)


def load_approved_csv_bytes(content: bytes):
    """Same as load_approved_csv, but reads uploaded bytes directly.

    Avoids re-opening a NamedTemporaryFile by name, which fails on Windows while
    the temporary file handle is still open.
    """
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded.") from exc
    return _parse_rows(io.StringIO(text, newline=""))
