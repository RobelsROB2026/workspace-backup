#!/usr/bin/env python3
"""
Trucking Insurance CRM Data Entry Tool

A command-line CRM tool for logging interactions with trucking company
insurance leads. Supports manual entry, CSV batch import, and automatic
carrier detail lookup via the FMCSA Socrata API.

Usage examples:
    # Single lead entry with DOT lookup:
    python trucking_insurance_crm_tool.py --dot-number 1234567 \
        --interaction-type "initial contact" --priority high

    # Manual entry without API lookup:
    python trucking_insurance_crm_tool.py --lead-name "ABC Trucking" \
        --state TX --fleet-size 25 --interaction-type follow-up \
        --notes "Discussed fleet coverage options"

    # Batch import from CSV:
    python trucking_insurance_crm_tool.py --csv-file leads.csv
"""

import argparse
import csv
import io
import logging
import os
import sqlite3
import sys
from typing import Dict, List, Optional
from datetime import datetime, date

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FMCSA_API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trucking_insurance_crm.db")

VALID_INTERACTION_TYPES = [
    "initial contact",
    "follow-up",
    "lapsed",
    "renewal",
    "meeting scheduled",
]
VALID_PRIORITIES = ["low", "medium", "high"]

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Initialise the SQLite database and return a connection.

    Creates the leads table if it does not already exist.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_name       TEXT,
            dot_number      TEXT,
            mc_number       TEXT,
            fleet_size      INTEGER,
            state           TEXT,
            phone           TEXT,
            email           TEXT,
            insurance_status TEXT,
            interaction_type TEXT,
            notes           TEXT,
            date            TEXT,
            priority        TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    logger.info("Database initialised at %s", db_path)
    return conn


def insert_lead(conn: sqlite3.Connection, record: dict) -> int:
    """Insert a single lead record and return its row id."""
    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        """
        INSERT INTO leads
            (lead_name, dot_number, mc_number, fleet_size, state, phone,
             email, insurance_status, interaction_type, notes, date,
             priority, created_at, updated_at)
        VALUES
            (:lead_name, :dot_number, :mc_number, :fleet_size, :state,
             :phone, :email, :insurance_status, :interaction_type, :notes,
             :date, :priority, :created_at, :updated_at)
        """,
        {
            "lead_name": record.get("lead_name"),
            "dot_number": record.get("dot_number"),
            "mc_number": record.get("mc_number"),
            "fleet_size": record.get("fleet_size"),
            "state": record.get("state"),
            "phone": record.get("phone"),
            "email": record.get("email"),
            "insurance_status": record.get("insurance_status"),
            "interaction_type": record.get("interaction_type"),
            "notes": record.get("notes"),
            "date": record.get("date", date.today().isoformat()),
            "priority": record.get("priority", "medium"),
            "created_at": now,
            "updated_at": now,
        },
    )
    conn.commit()
    logger.info(
        "Inserted lead id=%d  name=%s  dot=%s",
        cur.lastrowid,
        record.get("lead_name", "N/A"),
        record.get("dot_number", "N/A"),
    )
    return cur.lastrowid


def get_record_count(conn: sqlite3.Connection) -> int:
    """Return the total number of lead records in the database."""
    row = conn.execute("SELECT COUNT(*) AS cnt FROM leads").fetchone()
    return row["cnt"]


# ---------------------------------------------------------------------------
# FMCSA API lookup
# ---------------------------------------------------------------------------


def fetch_carrier_by_dot(dot_number: str) -> dict | None:
    """Query the FMCSA Socrata API for carrier details by DOT number.

    Returns a dict with normalised keys or None on failure.
    """
    params = {"dot_number": dot_number, "$limit": 1}
    logger.info("Querying FMCSA API for DOT# %s", dot_number)

    try:
        resp = requests.get(FMCSA_API_URL, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("FMCSA API request failed for DOT# %s: %s", dot_number, exc)
        return None

    data = resp.json()
    if not data:
        logger.info("No FMCSA records found for DOT# %s", dot_number)
        return None

    rec = data[0]
    carrier = {
        "lead_name": rec.get("legal_name") or rec.get("dba_name"),
        "dot_number": rec.get("dot_number"),
        "mc_number": rec.get("mc_mx_ff_number") or rec.get("mc_number"),
        "fleet_size": _parse_int(rec.get("total_power_units")),
        "state": rec.get("phy_state"),
        "phone": rec.get("telephone"),
    }
    logger.info(
        "FMCSA lookup success: %s (DOT# %s, %s power units)",
        carrier["lead_name"],
        carrier["dot_number"],
        carrier["fleet_size"],
    )
    return carrier


def _parse_int(value) -> int | None:
    """Safely parse a value to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Record building
# ---------------------------------------------------------------------------


def build_record_from_args(args: argparse.Namespace) -> dict:
    """Construct a lead record dict from parsed CLI arguments.

    If a DOT number is provided, attempt to enrich the record via the
    FMCSA API.  CLI-supplied values take precedence over API data.
    """
    api_data = {}
    if args.dot_number:
        fetched = fetch_carrier_by_dot(args.dot_number)
        if fetched:
            api_data = fetched

    record = {
        "lead_name": args.lead_name or api_data.get("lead_name"),
        "dot_number": args.dot_number or api_data.get("dot_number"),
        "mc_number": args.mc_number or api_data.get("mc_number"),
        "fleet_size": args.fleet_size if args.fleet_size is not None else api_data.get("fleet_size"),
        "state": args.state or api_data.get("state"),
        "phone": args.phone or api_data.get("phone"),
        "email": args.email,
        "insurance_status": args.insurance_status,
        "interaction_type": args.interaction_type,
        "notes": args.notes,
        "date": args.date,
        "priority": args.priority,
    }
    return record


def build_record_from_csv_row(row: dict) -> dict:
    """Construct a lead record from a CSV row dict.

    Column names are normalised (lowered, stripped, underscored).
    If a dot_number is present, attempt FMCSA enrichment.
    """
    def _get(key: str) -> str | None:
        """Look up a key using various common header spellings."""
        normalised = {k.strip().lower().replace("-", "_").replace(" ", "_"): v.strip() for k, v in row.items()}
        for candidate in [key, key.replace("_", "")]:
            if candidate in normalised and normalised[candidate]:
                return normalised[candidate]
        return None

    dot = _get("dot_number")
    api_data = {}
    if dot:
        fetched = fetch_carrier_by_dot(dot)
        if fetched:
            api_data = fetched

    fleet_raw = _get("fleet_size")
    fleet_size = _parse_int(fleet_raw) if fleet_raw else api_data.get("fleet_size")

    interaction = _get("interaction_type") or "initial contact"
    if interaction.lower() not in VALID_INTERACTION_TYPES:
        logger.warning("Invalid interaction_type '%s' in CSV row – defaulting to 'initial contact'", interaction)
        interaction = "initial contact"

    priority = _get("priority") or "medium"
    if priority.lower() not in VALID_PRIORITIES:
        logger.warning("Invalid priority '%s' in CSV row – defaulting to 'medium'", priority)
        priority = "medium"

    return {
        "lead_name": _get("lead_name") or api_data.get("lead_name"),
        "dot_number": dot or api_data.get("dot_number"),
        "mc_number": _get("mc_number") or api_data.get("mc_number"),
        "fleet_size": fleet_size,
        "state": _get("state") or api_data.get("state"),
        "phone": _get("phone") or api_data.get("phone"),
        "email": _get("email"),
        "insurance_status": _get("insurance_status"),
        "interaction_type": interaction.lower(),
        "notes": _get("notes"),
        "date": _get("date") or date.today().isoformat(),
        "priority": priority.lower(),
    }


# ---------------------------------------------------------------------------
# CSV batch processing
# ---------------------------------------------------------------------------


def process_csv(csv_path: str, conn: sqlite3.Connection) -> int:
    """Read a CSV file and insert each row as a lead record.

    Returns the number of records successfully inserted.
    """
    if not os.path.isfile(csv_path):
        logger.error("CSV file not found: %s", csv_path)
        return 0

    inserted = 0
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for idx, row in enumerate(reader, start=1):
            try:
                record = build_record_from_csv_row(row)
                insert_lead(conn, record)
                inserted += 1
            except Exception as exc:
                logger.error("Failed to process CSV row %d: %s", idx, exc)

    logger.info("CSV batch complete: %d/%d rows inserted from %s", inserted, idx if 'idx' in dir() else 0, csv_path)
    return inserted


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------


def print_summary(leads_processed: int, conn: sqlite3.Connection) -> None:
    """Print a summary report of the current session and database state."""
    total = get_record_count(conn)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    report = f"""
{'=' * 55}
  TRUCKING INSURANCE CRM – SESSION SUMMARY
{'=' * 55}
  Leads processed this session : {leads_processed}
  Total records in database    : {total}
  Last sync timestamp          : {now}
{'=' * 55}
"""
    print(report)
    logger.info("Summary: %d processed, %d total records", leads_processed, total)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Trucking Insurance CRM – log and manage insurance lead interactions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  %(prog)s --dot-number 1234567 --interaction-type "initial contact" --priority high
  %(prog)s --lead-name "ABC Trucking" --state TX --fleet-size 25 --interaction-type follow-up
  %(prog)s --csv-file leads.csv
        """,
    )

    parser.add_argument("--lead-name", help="Carrier / company name")
    parser.add_argument("--dot-number", help="USDOT number (triggers FMCSA API lookup)")
    parser.add_argument("--mc-number", help="MC/MX number")
    parser.add_argument("--fleet-size", type=int, help="Number of power units")
    parser.add_argument("--state", help="Two-letter state code")
    parser.add_argument("--phone", help="Contact phone number")
    parser.add_argument("--email", help="Contact email address")
    parser.add_argument("--insurance-status", help="Current insurance status description")
    parser.add_argument(
        "--interaction-type",
        choices=VALID_INTERACTION_TYPES,
        help="Type of interaction being logged",
    )
    parser.add_argument("--notes", help="Free-text notes about this interaction")
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Interaction date (YYYY-MM-DD, default: today)",
    )
    parser.add_argument(
        "--priority",
        choices=VALID_PRIORITIES,
        default="medium",
        help="Lead priority (default: medium)",
    )
    parser.add_argument(
        "--csv-file",
        help="Path to a CSV file for batch import of lead records",
    )
    parser.add_argument(
        "--db-path",
        default=DB_PATH,
        help=f"SQLite database path (default: {DB_PATH})",
    )

    args = parser.parse_args(argv)

    # Require at least one actionable input
    if not args.csv_file and not args.lead_name and not args.dot_number:
        parser.error("Provide at least --lead-name, --dot-number, or --csv-file")

    return args


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Entry point: parse arguments, process leads, and print a summary."""
    args = parse_args(argv)
    conn = init_db(args.db_path)
    leads_processed = 0

    try:
        # Batch mode
        if args.csv_file:
            leads_processed += process_csv(args.csv_file, conn)

        # Single-record mode (can run alongside CSV if both supplied)
        if args.lead_name or args.dot_number:
            record = build_record_from_args(args)
            insert_lead(conn, record)
            leads_processed += 1

        print_summary(leads_processed, conn)

    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
