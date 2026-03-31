#!/usr/bin/env python3
"""
Trucking Company Insurance CRM Data Entry Tool.

A command-line CRM for logging interactions with trucking company insurance leads.
Stores carrier and interaction data in a local SQLite database. Optionally fetches
carrier details from the FMCSA Socrata API (data.transportation.gov) by DOT number.

Usage examples:
    # Add a new lead
    python trucking_crm_tool.py create --carrier-name "ABC Trucking" --dot-number 1234567 \\
        --mc-number 987654 --fleet-size 25 --phone "555-123-4567" --email "abc@example.com" \\
        --state TX --interaction-type "initial contact" --notes "Interested in full coverage"

    # Fetch carrier info from FMCSA and create lead
    python trucking_crm_tool.py create --dot-number 1234567 --fetch-fmcsa

    # Update an interaction
    python trucking_crm_tool.py update --id 1 --interaction-type "follow-up" --notes "Sent quote"

    # Search leads
    python trucking_crm_tool.py search --state TX
    python trucking_crm_tool.py search --interaction-type "quote request"

    # List all leads
    python trucking_crm_tool.py list --sort-by state

    # Delete a lead
    python trucking_crm_tool.py delete --id 3
"""

import argparse
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "trucking_crm_tool.db"
LOG_PATH = Path(__file__).parent / "trucking_crm_tool.log"

FMCSA_API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"

VALID_INTERACTION_TYPES = [
    "initial contact",
    "follow-up",
    "quote request",
    "meeting scheduled",
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


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create the carriers and interactions tables if they do not exist."""
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS carriers (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT,
                dot_number  TEXT UNIQUE,
                mc_number   TEXT,
                fleet_size  INTEGER,
                phone       TEXT,
                email       TEXT,
                state       TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                carrier_id      INTEGER NOT NULL,
                interaction_type TEXT NOT NULL,
                notes           TEXT,
                interaction_date TEXT NOT NULL,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_carriers_state ON carriers(state);
            CREATE INDEX IF NOT EXISTS idx_carriers_dot ON carriers(dot_number);
            CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(interaction_type);
            """
        )
        conn.commit()
        logger.debug("Database initialized at %s", DB_PATH)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# FMCSA API lookup
# ---------------------------------------------------------------------------


def fetch_fmcsa(dot_number: str) -> dict | None:
    """Fetch carrier details from the FMCSA Socrata API by DOT number.

    Returns a dict with normalized keys or None on failure.
    """
    if requests is None:
        logger.error("The 'requests' package is required for FMCSA lookups. pip install requests")
        return None

    params = {"dot_number": dot_number, "$limit": 1}
    try:
        logger.info("Querying FMCSA API for DOT# %s ...", dot_number)
        resp = requests.get(FMCSA_API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.error("FMCSA API request failed: %s", exc)
        return None

    if not data:
        logger.warning("No FMCSA results for DOT# %s", dot_number)
        return None

    rec = data[0]
    result = {
        "name": rec.get("legal_name") or rec.get("dba_name", ""),
        "dot_number": rec.get("dot_number", dot_number),
        "mc_number": rec.get("mc_mx_ff_number", ""),
        "fleet_size": _parse_int(rec.get("total_power_units", "")),
        "phone": rec.get("phone", ""),
        "state": rec.get("phy_state", ""),
    }
    logger.info("FMCSA returned carrier: %s (DOT# %s)", result["name"], dot_number)
    return result


def _parse_int(val) -> int | None:
    """Safely parse an integer from a string-like value."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------


def create_lead(args: argparse.Namespace) -> None:
    """Insert a new carrier and optionally an initial interaction."""
    fmcsa_data: dict = {}
    if getattr(args, "fetch_fmcsa", False) and args.dot_number:
        fmcsa_data = fetch_fmcsa(args.dot_number) or {}

    name = args.carrier_name or fmcsa_data.get("name", "")
    dot = args.dot_number or fmcsa_data.get("dot_number", "")
    mc = args.mc_number or fmcsa_data.get("mc_number", "")
    fleet = args.fleet_size if args.fleet_size is not None else fmcsa_data.get("fleet_size")
    phone = args.phone or fmcsa_data.get("phone", "")
    email = args.email or ""
    state = args.state or fmcsa_data.get("state", "")

    if not name and not dot:
        logger.error("Provide at least --carrier-name or --dot-number.")
        sys.exit(1)

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO carriers (name, dot_number, mc_number, fleet_size, phone, email, state)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, dot, mc, fleet, phone, email, state.upper() if state else ""),
        )
        carrier_id = cur.lastrowid

        if args.interaction_type:
            interaction_date = args.date or datetime.now().strftime("%Y-%m-%d")
            conn.execute(
                """
                INSERT INTO interactions (carrier_id, interaction_type, notes, interaction_date)
                VALUES (?, ?, ?, ?)
                """,
                (carrier_id, args.interaction_type, args.notes or "", interaction_date),
            )

        conn.commit()
        logger.info("Created lead #%d: %s (DOT# %s)", carrier_id, name, dot)
        _print_carrier_row(conn, carrier_id)
    except sqlite3.IntegrityError as exc:
        logger.error("Duplicate DOT number or constraint error: %s", exc)
    finally:
        conn.close()


def update_lead(args: argparse.Namespace) -> None:
    """Update a carrier's details and/or add a new interaction record."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM carriers WHERE id = ?", (args.id,)).fetchone()
        if not row:
            logger.error("Carrier #%d not found.", args.id)
            sys.exit(1)

        # Update carrier fields if provided
        updates = {}
        for field in ("carrier_name", "dot_number", "mc_number", "fleet_size", "phone", "email", "state"):
            val = getattr(args, field, None)
            if val is not None:
                col = "name" if field == "carrier_name" else field
                if field == "state" and val:
                    val = val.upper()
                updates[col] = val

        if updates:
            updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(
                f"UPDATE carriers SET {set_clause} WHERE id = ?",
                (*updates.values(), args.id),
            )

        # Add interaction if type given
        if args.interaction_type:
            interaction_date = args.date or datetime.now().strftime("%Y-%m-%d")
            conn.execute(
                """
                INSERT INTO interactions (carrier_id, interaction_type, notes, interaction_date)
                VALUES (?, ?, ?, ?)
                """,
                (args.id, args.interaction_type, args.notes or "", interaction_date),
            )
            logger.info("Added '%s' interaction to carrier #%d", args.interaction_type, args.id)

        conn.commit()
        logger.info("Updated carrier #%d", args.id)
        _print_carrier_row(conn, args.id)
    finally:
        conn.close()


def delete_lead(args: argparse.Namespace) -> None:
    """Delete a carrier and all associated interactions."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT name, dot_number FROM carriers WHERE id = ?", (args.id,)).fetchone()
        if not row:
            logger.error("Carrier #%d not found.", args.id)
            sys.exit(1)

        conn.execute("DELETE FROM carriers WHERE id = ?", (args.id,))
        conn.commit()
        logger.info("Deleted carrier #%d (%s, DOT# %s) and all interactions.", args.id, row["name"], row["dot_number"])
    finally:
        conn.close()


def search_leads(args: argparse.Namespace) -> None:
    """Search carriers by state, DOT number, or interaction type."""
    conn = get_connection()
    try:
        if args.dot_number:
            rows = conn.execute(
                "SELECT * FROM carriers WHERE dot_number = ?", (args.dot_number,)
            ).fetchall()
        elif args.state:
            rows = conn.execute(
                "SELECT * FROM carriers WHERE state = ?", (args.state.upper(),)
            ).fetchall()
        elif args.interaction_type:
            rows = conn.execute(
                """
                SELECT DISTINCT c.* FROM carriers c
                JOIN interactions i ON c.id = i.carrier_id
                WHERE i.interaction_type = ?
                """,
                (args.interaction_type,),
            ).fetchall()
        else:
            logger.error("Provide at least one search filter: --state, --dot-number, or --interaction-type")
            sys.exit(1)

        if not rows:
            logger.info("No matching carriers found.")
            return

        _print_carrier_table(rows)

        # Show interactions for matched carriers
        carrier_ids = [r["id"] for r in rows]
        placeholders = ",".join("?" * len(carrier_ids))
        interactions = conn.execute(
            f"""
            SELECT i.*, c.name AS carrier_name FROM interactions i
            JOIN carriers c ON c.id = i.carrier_id
            WHERE i.carrier_id IN ({placeholders})
            ORDER BY i.interaction_date DESC
            """,
            carrier_ids,
        ).fetchall()
        if interactions:
            print()
            _print_interaction_table(interactions)
    finally:
        conn.close()


def list_leads(args: argparse.Namespace) -> None:
    """List all carriers, sorted by state or date."""
    sort_col = "state" if args.sort_by == "state" else "created_at"
    conn = get_connection()
    try:
        rows = conn.execute(f"SELECT * FROM carriers ORDER BY {sort_col}").fetchall()
        if not rows:
            logger.info("No leads in the database.")
            return

        _print_carrier_table(rows)

        # Show recent interactions
        interactions = conn.execute(
            """
            SELECT i.*, c.name AS carrier_name FROM interactions i
            JOIN carriers c ON c.id = i.carrier_id
            ORDER BY i.interaction_date DESC
            LIMIT 50
            """
        ).fetchall()
        if interactions:
            print(f"\n--- Recent Interactions (up to 50) ---")
            _print_interaction_table(interactions)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

COL_WIDTHS = {
    "id": 4,
    "name": 28,
    "dot": 10,
    "mc": 10,
    "fleet": 6,
    "phone": 15,
    "email": 25,
    "state": 6,
    "updated": 19,
}


def _print_carrier_table(rows) -> None:
    """Print a formatted table of carrier rows."""
    hdr = (
        f"{'ID':<{COL_WIDTHS['id']}} "
        f"{'Carrier Name':<{COL_WIDTHS['name']}} "
        f"{'DOT#':<{COL_WIDTHS['dot']}} "
        f"{'MC#':<{COL_WIDTHS['mc']}} "
        f"{'Fleet':<{COL_WIDTHS['fleet']}} "
        f"{'Phone':<{COL_WIDTHS['phone']}} "
        f"{'Email':<{COL_WIDTHS['email']}} "
        f"{'State':<{COL_WIDTHS['state']}} "
        f"{'Updated':<{COL_WIDTHS['updated']}}"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(
            f"{r['id']:<{COL_WIDTHS['id']}} "
            f"{(r['name'] or ''):<{COL_WIDTHS['name']}} "
            f"{(r['dot_number'] or ''):<{COL_WIDTHS['dot']}} "
            f"{(r['mc_number'] or ''):<{COL_WIDTHS['mc']}} "
            f"{str(r['fleet_size'] or ''):<{COL_WIDTHS['fleet']}} "
            f"{(r['phone'] or ''):<{COL_WIDTHS['phone']}} "
            f"{(r['email'] or ''):<{COL_WIDTHS['email']}} "
            f"{(r['state'] or ''):<{COL_WIDTHS['state']}} "
            f"{r['updated_at']:<{COL_WIDTHS['updated']}}"
        )
    print(f"\n{len(rows)} carrier(s) found.")


def _print_interaction_table(interactions) -> None:
    """Print a formatted table of interaction rows."""
    hdr = f"{'ID':<5} {'Carrier':<28} {'Type':<18} {'Date':<12} {'Notes'}"
    print(hdr)
    print("-" * max(len(hdr), 90))
    for i in interactions:
        print(
            f"{i['id']:<5} "
            f"{(i['carrier_name'] or ''):<28} "
            f"{i['interaction_type']:<18} "
            f"{i['interaction_date']:<12} "
            f"{(i['notes'] or '')}"
        )


def _print_carrier_row(conn: sqlite3.Connection, carrier_id: int) -> None:
    """Print a single carrier with its interactions."""
    row = conn.execute("SELECT * FROM carriers WHERE id = ?", (carrier_id,)).fetchone()
    if row:
        _print_carrier_table([row])
        interactions = conn.execute(
            """
            SELECT i.*, c.name AS carrier_name FROM interactions i
            JOIN carriers c ON c.id = i.carrier_id
            WHERE i.carrier_id = ?
            ORDER BY i.interaction_date DESC
            """,
            (carrier_id,),
        ).fetchall()
        if interactions:
            print()
            _print_interaction_table(interactions)


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argparse argument parser."""
    parser = argparse.ArgumentParser(
        description="Trucking Insurance CRM - manage carrier leads and interaction history.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  %(prog)s create --carrier-name "ABC Trucking" --dot-number 1234567 --state TX --interaction-type "initial contact"
  %(prog)s create --dot-number 1234567 --fetch-fmcsa --interaction-type "initial contact"
  %(prog)s update --id 1 --interaction-type "follow-up" --notes "Sent quote PDF"
  %(prog)s search --state TX
  %(prog)s search --interaction-type "quote request"
  %(prog)s list --sort-by date
  %(prog)s delete --id 3
        """,
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # Shared carrier arguments
    carrier_args = argparse.ArgumentParser(add_help=False)
    carrier_args.add_argument("--carrier-name", help="Legal name of the carrier")
    carrier_args.add_argument("--dot-number", help="USDOT number")
    carrier_args.add_argument("--mc-number", help="MC/MX number")
    carrier_args.add_argument("--fleet-size", type=int, help="Number of power units")
    carrier_args.add_argument("--phone", help="Contact phone number")
    carrier_args.add_argument("--email", help="Contact email address")
    carrier_args.add_argument("--state", help="State abbreviation (e.g., TX, CA)")
    carrier_args.add_argument(
        "--interaction-type",
        choices=VALID_INTERACTION_TYPES,
        help="Type of interaction to log",
    )
    carrier_args.add_argument("--notes", help="Free-text notes for this interaction")
    carrier_args.add_argument("--date", help="Interaction date (YYYY-MM-DD), defaults to today")

    # create
    create_p = sub.add_parser("create", parents=[carrier_args], help="Create a new carrier lead")
    create_p.add_argument(
        "--fetch-fmcsa",
        action="store_true",
        help="Fetch carrier details from the FMCSA API using the DOT number",
    )

    # update
    update_p = sub.add_parser("update", parents=[carrier_args], help="Update a carrier or add interaction")
    update_p.add_argument("--id", type=int, required=True, help="Carrier ID to update")

    # delete
    delete_p = sub.add_parser("delete", help="Delete a carrier and all its interactions")
    delete_p.add_argument("--id", type=int, required=True, help="Carrier ID to delete")

    # search
    search_p = sub.add_parser("search", help="Search carriers by state, DOT#, or interaction type")
    search_p.add_argument("--state", help="Filter by state abbreviation")
    search_p.add_argument("--dot-number", help="Filter by DOT number")
    search_p.add_argument(
        "--interaction-type",
        choices=VALID_INTERACTION_TYPES,
        help="Filter by interaction type",
    )

    # list
    list_p = sub.add_parser("list", help="List all carriers")
    list_p.add_argument(
        "--sort-by",
        choices=["state", "date"],
        default="state",
        help="Sort results by state or date (default: state)",
    )

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: parse args, initialize DB, dispatch to the appropriate command."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    init_db()

    commands = {
        "create": create_lead,
        "update": update_lead,
        "delete": delete_lead,
        "search": search_leads,
        "list": list_leads,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
