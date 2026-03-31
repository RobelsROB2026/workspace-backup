#!/usr/bin/env python3
"""CRM data entry tool for logging interactions with trucking company insurance leads.

Stores carrier information, contact details, and interaction history in a local
SQLite database. Supports full CRUD operations via command-line subcommands.

Usage examples:
    # Add a new lead
    python crm_lead_tracker.py add --carrier-name "FastHaul LLC" --dot-number 1234567 \
        --mc-number 987654 --fleet-size 25 --state TX --phone 555-123-4567 \
        --email dispatch@fasthaul.com --interaction-type lead --notes "Cold call prospect"

    # List all leads
    python crm_lead_tracker.py list

    # View a specific lead with interaction history
    python crm_lead_tracker.py view --id 1

    # Update a lead
    python crm_lead_tracker.py update --id 1 --fleet-size 30 --notes "Fleet grew"

    # Log a follow-up interaction on an existing lead
    python crm_lead_tracker.py log --id 1 --interaction-type follow-up \
        --notes "Sent quote, awaiting response"

    # Delete a lead
    python crm_lead_tracker.py delete --id 1

    # Search leads by state or carrier name
    python crm_lead_tracker.py search --state TX
    python crm_lead_tracker.py search --carrier-name "Fast"
"""

import argparse
import logging
import os
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "crm_leads.db"

LOG_PATH = Path(__file__).parent / "crm_lead_tracker.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

VALID_INTERACTION_TYPES = ("lead", "contact", "follow-up")
VALID_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
]


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Initialize the SQLite database with schema, indexes, and foreign keys.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        An open sqlite3.Connection with foreign keys enabled.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS leads (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            carrier_name    TEXT    NOT NULL,
            dot_number      TEXT,
            mc_number       TEXT,
            fleet_size      INTEGER,
            state           TEXT,
            phone           TEXT,
            email           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id         INTEGER NOT NULL,
            interaction_type TEXT   NOT NULL CHECK(interaction_type IN ('lead', 'contact', 'follow-up')),
            notes           TEXT,
            interaction_date TEXT   NOT NULL,
            created_at      TEXT   NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_leads_state ON leads(state);
        CREATE INDEX IF NOT EXISTS idx_leads_dot ON leads(dot_number);
        CREATE INDEX IF NOT EXISTS idx_leads_carrier ON leads(carrier_name);
        CREATE INDEX IF NOT EXISTS idx_interactions_lead ON interactions(lead_id);
        CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(interaction_type);
        CREATE INDEX IF NOT EXISTS idx_interactions_date ON interactions(interaction_date);
    """)
    conn.commit()
    return conn


def add_lead(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Insert a new lead and its initial interaction record.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments containing carrier details.
    """
    cur = conn.execute(
        """INSERT INTO leads (carrier_name, dot_number, mc_number, fleet_size, state, phone, email)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (args.carrier_name, args.dot_number, args.mc_number,
         args.fleet_size, args.state, args.phone, args.email),
    )
    lead_id = cur.lastrowid

    interaction_date = args.date or date.today().isoformat()
    conn.execute(
        """INSERT INTO interactions (lead_id, interaction_type, notes, interaction_date)
           VALUES (?, ?, ?, ?)""",
        (lead_id, args.interaction_type, args.notes, interaction_date),
    )
    conn.commit()
    logger.info("Added lead #%d: %s (DOT: %s)", lead_id, args.carrier_name, args.dot_number)


def list_leads(conn: sqlite3.Connection, _args: argparse.Namespace) -> None:
    """Print a summary table of all leads.

    Args:
        conn: Active database connection.
        _args: Parsed CLI arguments (unused).
    """
    rows = conn.execute(
        """SELECT l.id, l.carrier_name, l.dot_number, l.state, l.fleet_size,
                  (SELECT COUNT(*) FROM interactions WHERE lead_id = l.id) AS interactions,
                  (SELECT interaction_type FROM interactions WHERE lead_id = l.id
                   ORDER BY interaction_date DESC LIMIT 1) AS last_type,
                  (SELECT interaction_date FROM interactions WHERE lead_id = l.id
                   ORDER BY interaction_date DESC LIMIT 1) AS last_date
           FROM leads l ORDER BY l.updated_at DESC"""
    ).fetchall()

    if not rows:
        print("No leads found.")
        return

    print(f"\n{'ID':<5} {'Carrier':<30} {'DOT':<12} {'State':<6} {'Fleet':<6} "
          f"{'#Int':<5} {'Last Type':<12} {'Last Date':<12}")
    print("-" * 98)
    for r in rows:
        print(f"{r['id']:<5} {(r['carrier_name'] or '')[:29]:<30} "
              f"{(r['dot_number'] or ''):<12} {(r['state'] or ''):<6} "
              f"{str(r['fleet_size'] or ''):<6} {r['interactions']:<5} "
              f"{(r['last_type'] or ''):<12} {(r['last_date'] or ''):<12}")
    print(f"\nTotal: {len(rows)} leads\n")


def view_lead(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Display full details and interaction history for a single lead.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments containing --id.
    """
    lead = conn.execute("SELECT * FROM leads WHERE id = ?", (args.id,)).fetchone()
    if not lead:
        logger.error("Lead #%d not found.", args.id)
        sys.exit(1)

    print(f"\n--- Lead #{lead['id']} ---")
    print(f"  Carrier:    {lead['carrier_name']}")
    print(f"  DOT:        {lead['dot_number'] or 'N/A'}")
    print(f"  MC:         {lead['mc_number'] or 'N/A'}")
    print(f"  Fleet Size: {lead['fleet_size'] or 'N/A'}")
    print(f"  State:      {lead['state'] or 'N/A'}")
    print(f"  Phone:      {lead['phone'] or 'N/A'}")
    print(f"  Email:      {lead['email'] or 'N/A'}")
    print(f"  Created:    {lead['created_at']}")
    print(f"  Updated:    {lead['updated_at']}")

    interactions = conn.execute(
        """SELECT * FROM interactions WHERE lead_id = ?
           ORDER BY interaction_date DESC, created_at DESC""",
        (args.id,),
    ).fetchall()

    print(f"\n  Interaction History ({len(interactions)} records):")
    for ix in interactions:
        print(f"    [{ix['interaction_date']}] {ix['interaction_type'].upper()}"
              f" — {ix['notes'] or '(no notes)'}")
    print()


def update_lead(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Update fields on an existing lead record.

    Only fields explicitly provided on the CLI are modified.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments containing --id and fields to update.
    """
    lead = conn.execute("SELECT id FROM leads WHERE id = ?", (args.id,)).fetchone()
    if not lead:
        logger.error("Lead #%d not found.", args.id)
        sys.exit(1)

    updates = {}
    for field in ("carrier_name", "dot_number", "mc_number", "fleet_size",
                  "state", "phone", "email"):
        val = getattr(args, field, None)
        if val is not None:
            updates[field] = val

    if not updates:
        logger.warning("No fields to update. Provide at least one field flag.")
        return

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [args.id]
    conn.execute(
        f"UPDATE leads SET {set_clause}, updated_at = datetime('now', 'localtime') WHERE id = ?",
        values,
    )
    conn.commit()
    logger.info("Updated lead #%d: %s", args.id, ", ".join(f"{k}={v}" for k, v in updates.items()))


def log_interaction(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Log a new interaction against an existing lead.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments containing --id, --interaction-type, --notes, --date.
    """
    lead = conn.execute("SELECT id FROM leads WHERE id = ?", (args.id,)).fetchone()
    if not lead:
        logger.error("Lead #%d not found.", args.id)
        sys.exit(1)

    interaction_date = args.date or date.today().isoformat()
    conn.execute(
        """INSERT INTO interactions (lead_id, interaction_type, notes, interaction_date)
           VALUES (?, ?, ?, ?)""",
        (args.id, args.interaction_type, args.notes, interaction_date),
    )
    conn.execute(
        "UPDATE leads SET updated_at = datetime('now', 'localtime') WHERE id = ?",
        (args.id,),
    )
    conn.commit()
    logger.info("Logged %s interaction for lead #%d.", args.interaction_type, args.id)


def delete_lead(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Delete a lead and all its associated interactions (via CASCADE).

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments containing --id.
    """
    lead = conn.execute(
        "SELECT id, carrier_name FROM leads WHERE id = ?", (args.id,)
    ).fetchone()
    if not lead:
        logger.error("Lead #%d not found.", args.id)
        sys.exit(1)

    if not args.force:
        confirm = input(f"Delete lead #{args.id} ({lead['carrier_name']}) and all interactions? [y/N] ")
        if confirm.lower() != "y":
            print("Cancelled.")
            return

    conn.execute("DELETE FROM leads WHERE id = ?", (args.id,))
    conn.commit()
    logger.info("Deleted lead #%d: %s", args.id, lead["carrier_name"])


def search_leads(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Search leads by carrier name, state, DOT number, or interaction type.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments with search filters.
    """
    conditions = []
    params = []

    if args.carrier_name:
        conditions.append("l.carrier_name LIKE ?")
        params.append(f"%{args.carrier_name}%")
    if args.state:
        conditions.append("l.state = ?")
        params.append(args.state.upper())
    if args.dot_number:
        conditions.append("l.dot_number = ?")
        params.append(args.dot_number)
    if args.interaction_type:
        conditions.append(
            "EXISTS (SELECT 1 FROM interactions i WHERE i.lead_id = l.id AND i.interaction_type = ?)"
        )
        params.append(args.interaction_type)

    if not conditions:
        logger.warning("Provide at least one search filter.")
        return

    where = " AND ".join(conditions)
    rows = conn.execute(
        f"""SELECT l.id, l.carrier_name, l.dot_number, l.state, l.fleet_size, l.phone
            FROM leads l WHERE {where} ORDER BY l.carrier_name""",
        params,
    ).fetchall()

    if not rows:
        print("No matching leads found.")
        return

    print(f"\n{'ID':<5} {'Carrier':<30} {'DOT':<12} {'State':<6} {'Fleet':<6} {'Phone':<15}")
    print("-" * 80)
    for r in rows:
        print(f"{r['id']:<5} {(r['carrier_name'] or '')[:29]:<30} "
              f"{(r['dot_number'] or ''):<12} {(r['state'] or ''):<6} "
              f"{str(r['fleet_size'] or ''):<6} {(r['phone'] or ''):<15}")
    print(f"\n{len(rows)} results\n")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with subcommands for each CRUD operation.

    Returns:
        Configured argparse.ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        description="CRM tool for trucking company insurance leads.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--db", default=str(DB_PATH), help="Path to SQLite database file.")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- add ---
    p_add = sub.add_parser("add", help="Add a new lead with an initial interaction.")
    p_add.add_argument("--carrier-name", required=True, help="Carrier company name.")
    p_add.add_argument("--dot-number", help="USDOT number.")
    p_add.add_argument("--mc-number", help="MC number.")
    p_add.add_argument("--fleet-size", type=int, help="Number of trucks.")
    p_add.add_argument("--state", choices=VALID_STATES, help="US state abbreviation.")
    p_add.add_argument("--phone", help="Contact phone number.")
    p_add.add_argument("--email", help="Contact email address.")
    p_add.add_argument("--interaction-type", choices=VALID_INTERACTION_TYPES,
                       default="lead", help="Type of initial interaction (default: lead).")
    p_add.add_argument("--notes", help="Notes about this interaction.")
    p_add.add_argument("--date", help="Interaction date (YYYY-MM-DD, default: today).")

    # --- list ---
    sub.add_parser("list", help="List all leads.")

    # --- view ---
    p_view = sub.add_parser("view", help="View a lead and its interaction history.")
    p_view.add_argument("--id", type=int, required=True, help="Lead ID.")

    # --- update ---
    p_upd = sub.add_parser("update", help="Update an existing lead's details.")
    p_upd.add_argument("--id", type=int, required=True, help="Lead ID to update.")
    p_upd.add_argument("--carrier-name", help="New carrier name.")
    p_upd.add_argument("--dot-number", help="New DOT number.")
    p_upd.add_argument("--mc-number", help="New MC number.")
    p_upd.add_argument("--fleet-size", type=int, help="New fleet size.")
    p_upd.add_argument("--state", choices=VALID_STATES, help="New state.")
    p_upd.add_argument("--phone", help="New phone number.")
    p_upd.add_argument("--email", help="New email.")

    # --- log ---
    p_log = sub.add_parser("log", help="Log a new interaction on an existing lead.")
    p_log.add_argument("--id", type=int, required=True, help="Lead ID.")
    p_log.add_argument("--interaction-type", choices=VALID_INTERACTION_TYPES,
                       required=True, help="Interaction type.")
    p_log.add_argument("--notes", help="Interaction notes.")
    p_log.add_argument("--date", help="Interaction date (YYYY-MM-DD, default: today).")

    # --- delete ---
    p_del = sub.add_parser("delete", help="Delete a lead and all interactions.")
    p_del.add_argument("--id", type=int, required=True, help="Lead ID to delete.")
    p_del.add_argument("--force", "-f", action="store_true",
                       help="Skip confirmation prompt.")

    # --- search ---
    p_search = sub.add_parser("search", help="Search leads by field values.")
    p_search.add_argument("--carrier-name", help="Partial carrier name match.")
    p_search.add_argument("--state", choices=VALID_STATES, help="State filter.")
    p_search.add_argument("--dot-number", help="Exact DOT number.")
    p_search.add_argument("--interaction-type", choices=VALID_INTERACTION_TYPES,
                          help="Filter by interaction type.")

    return parser


DISPATCH = {
    "add": add_lead,
    "list": list_leads,
    "view": view_lead,
    "update": update_lead,
    "log": log_interaction,
    "delete": delete_lead,
    "search": search_leads,
}


def main() -> None:
    """Entry point: parse arguments, initialize DB, and dispatch to the requested subcommand."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "add" and args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            parser.error("--date must be in YYYY-MM-DD format.")

    if args.command == "log" and hasattr(args, "date") and args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            parser.error("--date must be in YYYY-MM-DD format.")

    try:
        conn = init_db(args.db)
    except sqlite3.Error as exc:
        logger.error("Database error: %s", exc)
        sys.exit(1)

    try:
        DISPATCH[args.command](conn, args)
    except sqlite3.Error as exc:
        logger.error("Database error during '%s': %s", args.command, exc)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
