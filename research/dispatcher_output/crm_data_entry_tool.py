#!/usr/bin/env python3
"""CRM Data Entry Tool for Trucking Company Insurance Leads.

Logs and manages interactions with trucking company insurance leads,
storing all data in a local SQLite database. Supports CSV import/export
and full CRUD operations via command-line interface.

Usage examples:
    # Add a new lead
    python crm_data_entry_tool.py add \
        --carrier-name "ABC Trucking" \
        --dot-number 1234567 \
        --mc-number 654321 \
        --fleet-size 25 \
        --state TX \
        --phone "512-555-0199" \
        --email "dispatch@abctrucking.com" \
        --interaction-type lead \
        --notes "Found via FMCSA new authority list" \
        --date 2026-03-28

    # List all leads
    python crm_data_entry_tool.py list

    # Update a lead
    python crm_data_entry_tool.py update 1 --interaction-type follow-up --notes "Left voicemail"

    # Delete a lead
    python crm_data_entry_tool.py delete 1

    # Export to CSV
    python crm_data_entry_tool.py export --file leads_export.csv

    # Import from CSV
    python crm_data_entry_tool.py import --file leads_import.csv
"""

import argparse
import csv
import io
import logging
import os
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_DIR = Path.home() / "research" / "dispatcher_output"
DB_PATH = DB_DIR / "crm_data_entry_tool.db"
LOG_PATH = DB_DIR / "crm_data_entry_tool.log"

VALID_INTERACTION_TYPES = ("lead", "contact", "follow-up")
VALID_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
]

CSV_COLUMNS = [
    "id", "carrier_name", "dot_number", "mc_number", "fleet_size",
    "state", "phone", "email", "interaction_type", "notes",
    "interaction_date", "created_at", "updated_at",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS leads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    carrier_name    TEXT    NOT NULL,
    dot_number      INTEGER,
    mc_number       INTEGER,
    fleet_size      INTEGER,
    state           TEXT,
    phone           TEXT,
    email           TEXT,
    interaction_type TEXT   NOT NULL DEFAULT 'lead',
    notes           TEXT,
    interaction_date TEXT,
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL
);
"""

CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_leads_dot ON leads(dot_number);",
    "CREATE INDEX IF NOT EXISTS idx_leads_state ON leads(state);",
    "CREATE INDEX IF NOT EXISTS idx_leads_type ON leads(interaction_type);",
]


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database, creating it if needed."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create the leads table and indexes if they don't exist."""
    conn.execute(CREATE_TABLE_SQL)
    for idx_sql in CREATE_INDEX_SQL:
        conn.execute(idx_sql)
    conn.commit()


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def add_lead(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    """Insert a new lead record and return its row id."""
    now = datetime.now().isoformat(timespec="seconds")
    interaction_date = args.date or date.today().isoformat()

    cur = conn.execute(
        """\
        INSERT INTO leads
            (carrier_name, dot_number, mc_number, fleet_size, state,
             phone, email, interaction_type, notes, interaction_date,
             created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            args.carrier_name,
            args.dot_number,
            args.mc_number,
            args.fleet_size,
            args.state.upper() if args.state else None,
            args.phone,
            args.email,
            args.interaction_type,
            args.notes,
            interaction_date,
            now,
            now,
        ),
    )
    conn.commit()
    row_id = cur.lastrowid
    logger.info("Added lead id=%d  carrier=%s  DOT=%s",
                row_id, args.carrier_name, args.dot_number)
    return row_id


def update_lead(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Update an existing lead record by id."""
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (args.id,)).fetchone()
    if row is None:
        logger.error("Lead id=%d not found.", args.id)
        sys.exit(1)

    fields = {}
    for col in ("carrier_name", "dot_number", "mc_number", "fleet_size",
                "state", "phone", "email", "interaction_type", "notes", "date"):
        val = getattr(args, col.replace("-", "_"), None)
        if val is not None:
            db_col = "interaction_date" if col == "date" else col
            if col == "state":
                val = val.upper()
            fields[db_col] = val

    if not fields:
        logger.warning("No fields to update for lead id=%d.", args.id)
        return

    fields["updated_at"] = datetime.now().isoformat(timespec="seconds")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [args.id]

    conn.execute(f"UPDATE leads SET {set_clause} WHERE id = ?", values)
    conn.commit()
    logger.info("Updated lead id=%d  fields=%s", args.id, list(fields.keys()))


def delete_lead(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Delete a lead record by id."""
    cur = conn.execute("DELETE FROM leads WHERE id = ?", (args.id,))
    conn.commit()
    if cur.rowcount == 0:
        logger.error("Lead id=%d not found.", args.id)
        sys.exit(1)
    logger.info("Deleted lead id=%d", args.id)


def get_lead(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Display a single lead by id."""
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (args.id,)).fetchone()
    if row is None:
        logger.error("Lead id=%d not found.", args.id)
        sys.exit(1)
    _print_rows([row])


def list_leads(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """List leads with optional filters for state and interaction type."""
    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if args.state:
        query += " AND state = ?"
        params.append(args.state.upper())
    if args.interaction_type:
        query += " AND interaction_type = ?"
        params.append(args.interaction_type)

    query += " ORDER BY updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    if not rows:
        logger.info("No leads found.")
        return
    _print_rows(rows)


def _print_rows(rows: list) -> None:
    """Pretty-print lead rows to stdout."""
    sep = "-" * 90
    for row in rows:
        print(sep)
        print(f"  ID:               {row['id']}")
        print(f"  Carrier Name:     {row['carrier_name']}")
        print(f"  DOT Number:       {row['dot_number'] or 'N/A'}")
        print(f"  MC Number:        {row['mc_number'] or 'N/A'}")
        print(f"  Fleet Size:       {row['fleet_size'] or 'N/A'}")
        print(f"  State:            {row['state'] or 'N/A'}")
        print(f"  Phone:            {row['phone'] or 'N/A'}")
        print(f"  Email:            {row['email'] or 'N/A'}")
        print(f"  Interaction Type: {row['interaction_type']}")
        print(f"  Notes:            {row['notes'] or ''}")
        print(f"  Date:             {row['interaction_date']}")
        print(f"  Created:          {row['created_at']}")
        print(f"  Updated:          {row['updated_at']}")
    print(sep)
    print(f"  Total: {len(rows)} record(s)")


# ---------------------------------------------------------------------------
# CSV import / export
# ---------------------------------------------------------------------------

def export_csv(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Export all leads (or filtered set) to a CSV file."""
    query = "SELECT * FROM leads WHERE 1=1"
    params = []
    if getattr(args, "state", None):
        query += " AND state = ?"
        params.append(args.state.upper())
    if getattr(args, "interaction_type", None):
        query += " AND interaction_type = ?"
        params.append(args.interaction_type)
    query += " ORDER BY id"

    rows = conn.execute(query, params).fetchall()
    filepath = Path(args.file)

    with open(filepath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            writer.writerow([row[c] for c in CSV_COLUMNS])

    logger.info("Exported %d lead(s) to %s", len(rows), filepath)


def import_csv(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Import leads from a CSV file into the database.

    Rows whose DOT number already exists are skipped to avoid duplicates.
    """
    filepath = Path(args.file)
    if not filepath.is_file():
        logger.error("File not found: %s", filepath)
        sys.exit(1)

    now = datetime.now().isoformat(timespec="seconds")
    added = 0
    skipped = 0

    with open(filepath, "r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            dot = row.get("dot_number") or None
            if dot:
                existing = conn.execute(
                    "SELECT id FROM leads WHERE dot_number = ?", (int(dot),)
                ).fetchone()
                if existing:
                    skipped += 1
                    continue

            interaction_date = row.get("interaction_date") or date.today().isoformat()
            interaction_type = row.get("interaction_type", "lead")
            if interaction_type not in VALID_INTERACTION_TYPES:
                interaction_type = "lead"

            conn.execute(
                """\
                INSERT INTO leads
                    (carrier_name, dot_number, mc_number, fleet_size, state,
                     phone, email, interaction_type, notes, interaction_date,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("carrier_name", ""),
                    int(dot) if dot else None,
                    int(row["mc_number"]) if row.get("mc_number") else None,
                    int(row["fleet_size"]) if row.get("fleet_size") else None,
                    (row.get("state") or "").upper() or None,
                    row.get("phone") or None,
                    row.get("email") or None,
                    interaction_type,
                    row.get("notes") or None,
                    interaction_date,
                    now,
                    now,
                ),
            )
            added += 1

    conn.commit()
    logger.info("CSV import complete: %d added, %d skipped (duplicate DOT).", added, skipped)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _add_lead_fields(parser: argparse.ArgumentParser, required: bool = False) -> None:
    """Add the common lead field arguments to a subparser."""
    parser.add_argument("--carrier-name", required=required,
                        help="Carrier / trucking company name")
    parser.add_argument("--dot-number", type=int,
                        help="USDOT number")
    parser.add_argument("--mc-number", type=int,
                        help="MC (Motor Carrier) number")
    parser.add_argument("--fleet-size", type=int,
                        help="Number of power units")
    parser.add_argument("--state",
                        help="Two-letter US state code (e.g. TX)")
    parser.add_argument("--phone",
                        help="Contact phone number")
    parser.add_argument("--email",
                        help="Contact email address")
    parser.add_argument("--interaction-type",
                        choices=VALID_INTERACTION_TYPES,
                        default="lead" if required else None,
                        help="Type of interaction (default: lead)")
    parser.add_argument("--notes",
                        help="Free-text notes about the interaction")
    parser.add_argument("--date",
                        help="Interaction date (YYYY-MM-DD, default: today)")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        description="CRM data entry tool for trucking company insurance leads.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run '<command> --help' for details on each sub-command.",
    )
    parser.add_argument("--db", default=str(DB_PATH),
                        help=f"Path to SQLite database (default: {DB_PATH})")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # add -------------------------------------------------------------------
    p_add = sub.add_parser("add", help="Add a new lead")
    _add_lead_fields(p_add, required=True)

    # update ----------------------------------------------------------------
    p_upd = sub.add_parser("update", help="Update an existing lead by ID")
    p_upd.add_argument("id", type=int, help="Lead ID to update")
    _add_lead_fields(p_upd, required=False)

    # delete ----------------------------------------------------------------
    p_del = sub.add_parser("delete", help="Delete a lead by ID")
    p_del.add_argument("id", type=int, help="Lead ID to delete")

    # get -------------------------------------------------------------------
    p_get = sub.add_parser("get", help="Show a single lead by ID")
    p_get.add_argument("id", type=int, help="Lead ID to display")

    # list ------------------------------------------------------------------
    p_lst = sub.add_parser("list", help="List leads with optional filters")
    p_lst.add_argument("--state", help="Filter by state")
    p_lst.add_argument("--interaction-type", choices=VALID_INTERACTION_TYPES,
                        help="Filter by interaction type")

    # export ----------------------------------------------------------------
    p_exp = sub.add_parser("export", help="Export leads to CSV")
    p_exp.add_argument("--file", required=True, help="Output CSV file path")
    p_exp.add_argument("--state", help="Filter by state")
    p_exp.add_argument("--interaction-type", choices=VALID_INTERACTION_TYPES,
                        help="Filter by interaction type")

    # import ----------------------------------------------------------------
    p_imp = sub.add_parser("import", help="Import leads from CSV")
    p_imp.add_argument("--file", required=True, help="Input CSV file path")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

COMMAND_DISPATCH = {
    "add": add_lead,
    "update": update_lead,
    "delete": delete_lead,
    "get": get_lead,
    "list": list_leads,
    "export": export_csv,
    "import": import_csv,
}


def main() -> None:
    """Entry point: parse arguments, connect to DB, and dispatch command."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Validate date format if provided
    if hasattr(args, "date") and args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            logger.error("Invalid date format '%s'. Use YYYY-MM-DD.", args.date)
            sys.exit(1)

    # Validate state if provided
    if hasattr(args, "state") and args.state:
        if args.state.upper() not in VALID_STATES:
            logger.error("Invalid state code '%s'.", args.state)
            sys.exit(1)

    db_path = args.db
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        init_db(conn)
    except sqlite3.Error as exc:
        logger.error("Database error: %s", exc)
        sys.exit(1)

    handler = COMMAND_DISPATCH.get(args.command)
    try:
        handler(conn, args)
    except sqlite3.Error as exc:
        logger.error("Database error during '%s': %s", args.command, exc)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
