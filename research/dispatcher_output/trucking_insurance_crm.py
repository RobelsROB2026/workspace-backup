#!/usr/bin/env python3
"""CRM data entry tool for tracking trucking company insurance leads.

Provides full CRUD operations on a local SQLite database of carrier leads,
with support for batch CSV import, CSV export, search by DOT number / state /
insurance status, interaction logging, and structured command-line access via
argparse subcommands.

Usage examples:
    # Add a new lead
    python trucking_insurance_crm.py add \\
        --carrier-name "ABC Trucking" --dot-number 1234567 --mc-number 654321 \\
        --fleet-size 25 --phone 555-867-5309 --email dispatch@abc.com \\
        --address "123 Main St, Dallas, TX 75201" --insurance-status active \\
        --mcs150-date 2025-06-15 --interaction-type initial \\
        --notes "Found via FMCSA new-authority report"

    # Batch import from CSV
    python trucking_insurance_crm.py import --csv-file leads.csv

    # Search leads
    python trucking_insurance_crm.py search --dot-number 1234567
    python trucking_insurance_crm.py search --state TX
    python trucking_insurance_crm.py search --insurance-status lapsed

    # Export all leads to CSV
    python trucking_insurance_crm.py export --csv-file leads_export.csv
"""

import argparse
import csv
import logging
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = Path.home() / "research" / "dispatcher_output" / "insurance_leads.db"

VALID_INSURANCE_STATUSES = ("active", "lapsed", "unknown")
VALID_INTERACTION_TYPES = ("initial", "follow-up", "quote-request")
VALID_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

LOG_PATH = Path.home() / "research" / "dispatcher_output" / "trucking_crm.log"

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


def get_connection():
    """Open a connection to the SQLite database, creating the file if needed.

    Returns:
        sqlite3.Connection with row_factory set to sqlite3.Row.
    """
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    except sqlite3.Error as exc:
        logger.error("Could not open database at %s: %s", DB_PATH, exc)
        sys.exit(1)


def init_db(conn):
    """Create the leads and interactions tables if they do not already exist.

    Args:
        conn: An open sqlite3.Connection.
    """
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS leads (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            carrier_name      TEXT    NOT NULL,
            dot_number        TEXT    UNIQUE,
            mc_number         TEXT,
            fleet_size        INTEGER,
            phone             TEXT,
            email             TEXT,
            address           TEXT,
            insurance_status  TEXT    DEFAULT 'unknown'
                              CHECK(insurance_status IN ('active','lapsed','unknown')),
            mcs150_date       TEXT,
            created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at        TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id           INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            interaction_type  TEXT    NOT NULL
                              CHECK(interaction_type IN ('initial','follow-up','quote-request')),
            notes             TEXT,
            created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_leads_dot    ON leads(dot_number);
        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(insurance_status);
    """)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_dot_number(value):
    """Ensure DOT number is numeric."""
    if not re.fullmatch(r"\d+", value):
        raise argparse.ArgumentTypeError(f"DOT number must be numeric, got '{value}'")
    return value


def validate_mc_number(value):
    """Ensure MC number is numeric."""
    if not re.fullmatch(r"\d+", value):
        raise argparse.ArgumentTypeError(f"MC number must be numeric, got '{value}'")
    return value


def validate_fleet_size(value):
    """Ensure fleet size is a positive integer."""
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Fleet size must be an integer, got '{value}'")
    if n < 1:
        raise argparse.ArgumentTypeError(f"Fleet size must be >= 1, got {n}")
    return n


def validate_email(value):
    """Basic email format check."""
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        raise argparse.ArgumentTypeError(f"Invalid email address: '{value}'")
    return value


def validate_phone(value):
    """Normalise a US phone number to 10 digits."""
    digits = re.sub(r"[^\d]", "", value)
    if digits.startswith("1") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10:
        raise argparse.ArgumentTypeError(
            f"Phone number must be 10 digits (got {len(digits)} from '{value}')"
        )
    return digits


def validate_date(value):
    """Validate a date string in YYYY-MM-DD format."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Date must be YYYY-MM-DD, got '{value}'")
    return value


def validate_state(value):
    """Validate a US state abbreviation."""
    upper = value.upper()
    if upper not in VALID_US_STATES:
        raise argparse.ArgumentTypeError(f"Unknown US state abbreviation: '{value}'")
    return upper


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _format_phone(digits):
    """Format a 10-digit string as (XXX) XXX-XXXX."""
    if digits and len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return digits or ""


def _find_lead(conn, args):
    """Look up a lead by DOT number, MC number, or carrier name.

    Returns:
        A sqlite3.Row or None.
    """
    if getattr(args, "dot_number", None):
        return conn.execute(
            "SELECT * FROM leads WHERE dot_number = ?", (args.dot_number,)
        ).fetchone()
    if getattr(args, "mc_number", None):
        return conn.execute(
            "SELECT * FROM leads WHERE mc_number = ?", (args.mc_number,)
        ).fetchone()
    if getattr(args, "carrier_name", None):
        return conn.execute(
            "SELECT * FROM leads WHERE carrier_name = ? COLLATE NOCASE",
            (args.carrier_name,),
        ).fetchone()
    return None


def _print_leads_table(rows):
    """Print a formatted table of lead rows."""
    if not rows:
        logger.info("No leads found.")
        return
    header = (
        f"{'ID':>5}  {'Carrier':30}  {'DOT':>8}  {'MC':>8}  {'Fleet':>5}  "
        f"{'Phone':14}  {'Status':8}  {'MCS-150':10}  {'Created':19}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        phone = _format_phone(r["phone"]) if r["phone"] else ""
        print(
            f"{r['id']:>5}  {(r['carrier_name'] or '')[:30]:30}  "
            f"{(r['dot_number'] or ''):>8}  {(r['mc_number'] or ''):>8}  "
            f"{(str(r['fleet_size']) if r['fleet_size'] else ''):>5}  "
            f"{phone:14}  {(r['insurance_status'] or ''):8}  "
            f"{(r['mcs150_date'] or ''):10}  {r['created_at']:19}"
        )


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------


def cmd_add(conn, args):
    """Insert a new lead and optionally its first interaction.

    Args:
        conn: An open sqlite3.Connection.
        args: Parsed argparse.Namespace with lead fields.
    """
    if not args.carrier_name:
        logger.error("--carrier-name is required when adding a lead.")
        sys.exit(1)

    try:
        cur = conn.execute(
            """INSERT INTO leads
               (carrier_name, dot_number, mc_number, fleet_size, phone,
                email, address, insurance_status, mcs150_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                args.carrier_name,
                args.dot_number,
                args.mc_number,
                args.fleet_size,
                args.phone,
                args.email,
                args.address,
                args.insurance_status or "unknown",
                args.mcs150_date,
            ),
        )
        lead_id = cur.lastrowid

        if args.interaction_type:
            conn.execute(
                """INSERT INTO interactions (lead_id, interaction_type, notes)
                   VALUES (?, ?, ?)""",
                (lead_id, args.interaction_type, args.notes),
            )

        conn.commit()
        logger.info("Lead #%d created for '%s'.", lead_id, args.carrier_name)
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if "dot_number" in str(exc).lower():
            logger.error("A lead with DOT number %s already exists.", args.dot_number)
        else:
            logger.error("Constraint violation: %s", exc)
        sys.exit(1)


def cmd_update(conn, args):
    """Update mutable fields on an existing lead.

    Args:
        conn: An open sqlite3.Connection.
        args: Parsed argparse.Namespace with fields to update.
    """
    lead = _find_lead(conn, args)
    if lead is None:
        logger.error("No matching lead found.")
        sys.exit(1)

    updates = {}
    for field in ("carrier_name", "fleet_size", "phone", "email", "address",
                  "insurance_status", "mcs150_date"):
        val = getattr(args, field, None)
        if val is not None:
            updates[field] = val

    if not updates:
        logger.info("Nothing to update -- supply at least one field to change.")
        return

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [lead["id"]]
    conn.execute(
        f"UPDATE leads SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    conn.commit()
    logger.info("Lead #%d updated.", lead["id"])


def cmd_delete(conn, args):
    """Delete a lead and all its interactions.

    Args:
        conn: An open sqlite3.Connection.
        args: Parsed argparse.Namespace with identifier fields.
    """
    lead = _find_lead(conn, args)
    if lead is None:
        logger.error("No matching lead found.")
        sys.exit(1)

    conn.execute("DELETE FROM leads WHERE id = ?", (lead["id"],))
    conn.commit()
    logger.info("Lead #%d ('%s') deleted.", lead["id"], lead["carrier_name"])


def cmd_log(conn, args):
    """Log a new interaction against an existing lead.

    Args:
        conn: An open sqlite3.Connection.
        args: Parsed argparse.Namespace with interaction fields.
    """
    lead = _find_lead(conn, args)
    if lead is None:
        logger.error("No matching lead found. Add the lead first.")
        sys.exit(1)

    if not args.interaction_type:
        logger.error("--interaction-type is required when logging an interaction.")
        sys.exit(1)

    conn.execute(
        "INSERT INTO interactions (lead_id, interaction_type, notes) VALUES (?, ?, ?)",
        (lead["id"], args.interaction_type, args.notes),
    )
    conn.commit()
    logger.info(
        "Logged '%s' interaction for lead #%d (%s).",
        args.interaction_type, lead["id"], lead["carrier_name"],
    )


def cmd_show(conn, args):
    """Display full details and interaction history for a single lead.

    Args:
        conn: An open sqlite3.Connection.
        args: Parsed argparse.Namespace with identifier fields.
    """
    lead = _find_lead(conn, args)
    if lead is None:
        logger.error("No matching lead found.")
        sys.exit(1)

    phone = _format_phone(lead["phone"]) if lead["phone"] else "—"
    print(f"\nLead #{lead['id']}: {lead['carrier_name']}")
    print(f"  DOT: {lead['dot_number'] or '—'}  |  MC: {lead['mc_number'] or '—'}")
    print(f"  Fleet size: {lead['fleet_size'] or '—'}  |  Insurance: {lead['insurance_status'] or '—'}")
    print(f"  Phone: {phone}  |  Email: {lead['email'] or '—'}")
    print(f"  Address: {lead['address'] or '—'}")
    print(f"  MCS-150 date: {lead['mcs150_date'] or '—'}")
    print(f"  Created: {lead['created_at']}  |  Updated: {lead['updated_at']}")

    interactions = conn.execute(
        "SELECT * FROM interactions WHERE lead_id = ? ORDER BY created_at DESC",
        (lead["id"],),
    ).fetchall()

    if interactions:
        print(f"\n  Interactions ({len(interactions)}):")
        for ix in interactions:
            notes = ix["notes"] or ""
            print(f"    [{ix['created_at']}] {ix['interaction_type']:15}  {notes}")
    else:
        print("\n  No interactions recorded.")
    print()


def cmd_list(conn, args):
    """List all leads, optionally filtered by state or insurance status.

    Args:
        conn: An open sqlite3.Connection.
        args: Parsed argparse.Namespace.
    """
    query = "SELECT * FROM leads WHERE 1=1"
    params = []
    if getattr(args, "state", None):
        # Extract state from address field (look for 2-letter state code)
        query += " AND address LIKE ?"
        params.append(f"%, {args.state} %")
    if getattr(args, "insurance_status", None):
        query += " AND insurance_status = ?"
        params.append(args.insurance_status)
    query += " ORDER BY carrier_name"
    rows = conn.execute(query, params).fetchall()
    _print_leads_table(rows)


def cmd_search(conn, args):
    """Search leads by DOT number, state (from address), or insurance status.

    Args:
        conn: An open sqlite3.Connection.
        args: Parsed argparse.Namespace with search criteria.
    """
    if args.dot_number:
        rows = conn.execute(
            "SELECT * FROM leads WHERE dot_number = ?", (args.dot_number,)
        ).fetchall()
        _print_leads_table(rows)
        return

    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if args.state:
        query += " AND address LIKE ?"
        params.append(f"%, {args.state} %")

    if args.insurance_status:
        query += " AND insurance_status = ?"
        params.append(args.insurance_status)

    query += " ORDER BY carrier_name"
    rows = conn.execute(query, params).fetchall()
    logger.info("Search returned %d result(s).", len(rows))
    _print_leads_table(rows)


# ---------------------------------------------------------------------------
# CSV import / export
# ---------------------------------------------------------------------------

CSV_FIELD_MAP = {
    "carrier_name": "carrier_name",
    "dot_number": "dot_number",
    "mc_number": "mc_number",
    "fleet_size": "fleet_size",
    "phone": "phone",
    "email": "email",
    "address": "address",
    "insurance_status": "insurance_status",
    "mcs150_date": "mcs150_date",
}

EXPORT_COLUMNS = [
    "id", "carrier_name", "dot_number", "mc_number", "fleet_size",
    "phone", "email", "address", "insurance_status", "mcs150_date",
    "created_at", "updated_at",
]


def cmd_import(conn, args):
    """Batch import leads from a CSV file.

    Expected CSV columns (header row required): carrier_name, dot_number,
    mc_number, fleet_size, phone, email, address, insurance_status, mcs150_date.

    Args:
        conn: An open sqlite3.Connection.
        args: Parsed argparse.Namespace with csv_file path.
    """
    csv_path = Path(args.csv_file)
    if not csv_path.is_file():
        logger.error("CSV file not found: %s", csv_path)
        sys.exit(1)

    imported = 0
    skipped = 0

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row_num, row in enumerate(reader, start=2):
            carrier = row.get("carrier_name", "").strip()
            if not carrier:
                logger.warning("Row %d: missing carrier_name, skipping.", row_num)
                skipped += 1
                continue

            dot = row.get("dot_number", "").strip() or None
            mc = row.get("mc_number", "").strip() or None
            fleet = row.get("fleet_size", "").strip() or None
            if fleet:
                try:
                    fleet = int(fleet)
                except ValueError:
                    logger.warning("Row %d: invalid fleet_size '%s', setting to NULL.", row_num, fleet)
                    fleet = None

            phone = row.get("phone", "").strip() or None
            if phone:
                digits = re.sub(r"[^\d]", "", phone)
                if digits.startswith("1") and len(digits) == 11:
                    digits = digits[1:]
                phone = digits if len(digits) == 10 else None

            email = row.get("email", "").strip() or None
            address = row.get("address", "").strip() or None
            status = row.get("insurance_status", "").strip().lower() or "unknown"
            if status not in VALID_INSURANCE_STATUSES:
                logger.warning("Row %d: invalid insurance_status '%s', defaulting to 'unknown'.", row_num, status)
                status = "unknown"

            mcs150 = row.get("mcs150_date", "").strip() or None

            try:
                conn.execute(
                    """INSERT INTO leads
                       (carrier_name, dot_number, mc_number, fleet_size, phone,
                        email, address, insurance_status, mcs150_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (carrier, dot, mc, fleet, phone, email, address, status, mcs150),
                )
                imported += 1
            except sqlite3.IntegrityError as exc:
                logger.warning("Row %d: skipping duplicate (%s).", row_num, exc)
                skipped += 1

    conn.commit()
    logger.info("Import complete: %d imported, %d skipped.", imported, skipped)


def cmd_export(conn, args):
    """Export all leads to a CSV file.

    Args:
        conn: An open sqlite3.Connection.
        args: Parsed argparse.Namespace with csv_file path.
    """
    csv_path = Path(args.csv_file)
    rows = conn.execute(
        f"SELECT {', '.join(EXPORT_COLUMNS)} FROM leads ORDER BY carrier_name"
    ).fetchall()

    if not rows:
        logger.info("No leads to export.")
        return

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({col: r[col] for col in EXPORT_COLUMNS})

    logger.info("Exported %d leads to %s.", len(rows), csv_path)


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------


def build_parser():
    """Build and return the argparse.ArgumentParser with all subcommands.

    Returns:
        A configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="CRM tool for tracking trucking company insurance leads.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s add --carrier-name "ABC Trucking" --dot-number 1234567 \\
      --mc-number 654321 --fleet-size 25 --phone 555-867-5309 \\
      --email dispatch@abc.com --address "123 Main St, Dallas, TX 75201" \\
      --insurance-status active --mcs150-date 2025-06-15 \\
      --interaction-type initial --notes "Found via FMCSA lookup"

  %(prog)s log --dot-number 1234567 --interaction-type follow-up \\
      --notes "Left voicemail"

  %(prog)s search --state TX --insurance-status lapsed
  %(prog)s show --dot-number 1234567
  %(prog)s update --dot-number 1234567 --fleet-size 30 --insurance-status active
  %(prog)s delete --dot-number 1234567
  %(prog)s import --csv-file new_leads.csv
  %(prog)s export --csv-file all_leads.csv
""",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # -- shared argument groups ------------------------------------------------

    def add_id_args(p):
        """Add carrier identifier arguments to a subparser."""
        p.add_argument("--carrier-name", help="Carrier / company name")
        p.add_argument("--dot-number", type=validate_dot_number, help="USDOT number")
        p.add_argument("--mc-number", type=validate_mc_number, help="MC number")

    def add_detail_args(p):
        """Add carrier detail arguments to a subparser."""
        p.add_argument("--fleet-size", type=validate_fleet_size, help="Number of power units")
        p.add_argument("--phone", type=validate_phone, help="Contact phone number")
        p.add_argument("--email", type=validate_email, help="Contact email address")
        p.add_argument("--address", help="Physical address (street, city, state zip)")
        p.add_argument(
            "--insurance-status",
            choices=VALID_INSURANCE_STATUSES,
            help="Insurance status: active, lapsed, or unknown",
        )
        p.add_argument(
            "--mcs150-date", type=validate_date,
            help="MCS-150 form date (YYYY-MM-DD)",
        )

    def add_interaction_args(p):
        """Add interaction arguments to a subparser."""
        p.add_argument(
            "--interaction-type",
            choices=VALID_INTERACTION_TYPES,
            help="Type: initial, follow-up, or quote-request",
        )
        p.add_argument("--notes", help="Free-text notes about the interaction")

    # -- subcommands -----------------------------------------------------------

    # add
    p_add = sub.add_parser("add", help="Add a new lead")
    add_id_args(p_add)
    add_detail_args(p_add)
    add_interaction_args(p_add)

    # update
    p_upd = sub.add_parser("update", help="Update fields on an existing lead")
    add_id_args(p_upd)
    add_detail_args(p_upd)

    # delete
    p_del = sub.add_parser("delete", help="Delete a lead and its interactions")
    add_id_args(p_del)

    # log
    p_log = sub.add_parser("log", help="Log an interaction for an existing lead")
    add_id_args(p_log)
    add_interaction_args(p_log)

    # show
    p_show = sub.add_parser("show", help="Show details and history for one lead")
    add_id_args(p_show)

    # list
    p_ls = sub.add_parser("list", help="List all leads")
    p_ls.add_argument("--state", type=validate_state, help="Filter by US state in address")
    p_ls.add_argument(
        "--insurance-status", choices=VALID_INSURANCE_STATUSES,
        help="Filter by insurance status",
    )

    # search
    p_search = sub.add_parser("search", help="Search leads by DOT#, state, or insurance status")
    p_search.add_argument("--dot-number", type=validate_dot_number, help="Search by USDOT number")
    p_search.add_argument("--state", type=validate_state, help="Search by US state in address")
    p_search.add_argument(
        "--insurance-status", choices=VALID_INSURANCE_STATUSES,
        help="Search by insurance status",
    )

    # import
    p_imp = sub.add_parser("import", help="Batch import leads from a CSV file")
    p_imp.add_argument("--csv-file", required=True, help="Path to CSV file to import")

    # export
    p_exp = sub.add_parser("export", help="Export all leads to a CSV file")
    p_exp.add_argument("--csv-file", required=True, help="Path for output CSV file")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Parse arguments, initialise the database, and dispatch to the handler."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    conn = get_connection()
    init_db(conn)

    dispatch = {
        "add": cmd_add,
        "update": cmd_update,
        "delete": cmd_delete,
        "log": cmd_log,
        "show": cmd_show,
        "list": cmd_list,
        "search": cmd_search,
        "import": cmd_import,
        "export": cmd_export,
    }

    try:
        dispatch[args.command](conn, args)
    except sqlite3.Error as exc:
        logger.error("Database error: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted.")
        sys.exit(130)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
