#!/usr/bin/env python3
"""
Insurance CRM Tool for Trucking Company Leads

A command-line CRM for logging interactions with trucking company insurance
leads. Stores carrier information (DOT#, MC#, fleet size, contact details,
insurance status) and interaction history in a local SQLite database.

Usage examples:
    # Add a new carrier lead
    python insurance_crm_tool.py add-lead --dot 1234567 --mc 987654 \
        --name "ABC Trucking" --fleet-size 25 --phone "555-123-4567" \
        --address "123 Main St, Dallas, TX 75201" --status prospect

    # Log an interaction
    python insurance_crm_tool.py log-interaction --dot 1234567 \
        --contact "John Smith" --type call --notes "Discussed fleet policy options"

    # View all leads
    python insurance_crm_tool.py view-leads

    # View interactions for a specific carrier
    python insurance_crm_tool.py view-interactions --dot 1234567

    # Export data to CSV
    python insurance_crm_tool.py export --output leads_export.csv
"""

import argparse
import csv
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "insurance_crm.db"

INSURANCE_STATUSES = [
    "prospect",
    "contacted",
    "quoted",
    "follow-up",
    "closed-won",
    "closed-lost",
    "renewal",
]

INTERACTION_TYPES = [
    "call",
    "email",
    "meeting",
    "voicemail",
    "text",
    "referral",
    "other",
]


def init_db(db_path: str) -> sqlite3.Connection:
    """Open the SQLite database and create tables if they don't exist.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        An open sqlite3.Connection with WAL mode and foreign keys enabled.

    Raises:
        SystemExit: If the database cannot be opened or tables cannot be created.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS carriers (
                dot_number  TEXT PRIMARY KEY,
                mc_number   TEXT,
                name        TEXT NOT NULL,
                fleet_size  INTEGER,
                phone       TEXT,
                address     TEXT,
                status      TEXT NOT NULL DEFAULT 'prospect',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                dot_number      TEXT NOT NULL,
                date            TEXT NOT NULL,
                contact_person  TEXT,
                type            TEXT NOT NULL,
                notes           TEXT,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (dot_number) REFERENCES carriers(dot_number)
            );

            CREATE INDEX IF NOT EXISTS idx_interactions_dot
                ON interactions(dot_number);
            """
        )
        conn.commit()
        return conn
    except sqlite3.Error as e:
        print(f"Error: Failed to initialize database at {db_path}: {e}", file=sys.stderr)
        sys.exit(1)


def add_lead(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Insert a new carrier lead into the database.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments containing carrier details.
    """
    now = datetime.now().isoformat(timespec="seconds")
    try:
        conn.execute(
            """
            INSERT INTO carriers
                (dot_number, mc_number, name, fleet_size, phone, address, status,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                args.dot,
                args.mc,
                args.name,
                args.fleet_size,
                args.phone,
                args.address,
                args.status,
                now,
                now,
            ),
        )
        conn.commit()
        print(f"Added lead: {args.name} (DOT# {args.dot})")
    except sqlite3.IntegrityError:
        print(
            f"Error: A carrier with DOT# {args.dot} already exists.",
            file=sys.stderr,
        )
        sys.exit(1)
    except sqlite3.Error as e:
        print(f"Error: Could not add lead: {e}", file=sys.stderr)
        sys.exit(1)


def log_interaction(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Record an interaction with an existing carrier lead.

    Also updates the carrier's updated_at timestamp.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments containing interaction details.
    """
    # Verify the carrier exists
    row = conn.execute(
        "SELECT name FROM carriers WHERE dot_number = ?", (args.dot,)
    ).fetchone()
    if row is None:
        print(
            f"Error: No carrier found with DOT# {args.dot}. Add the lead first.",
            file=sys.stderr,
        )
        sys.exit(1)

    now = datetime.now().isoformat(timespec="seconds")
    date = args.date or now[:10]

    try:
        conn.execute(
            """
            INSERT INTO interactions
                (dot_number, date, contact_person, type, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (args.dot, date, args.contact, args.type, args.notes, now),
        )
        conn.execute(
            "UPDATE carriers SET updated_at = ? WHERE dot_number = ?",
            (now, args.dot),
        )
        conn.commit()
        print(f"Logged {args.type} interaction with {row[0]} (DOT# {args.dot})")
    except sqlite3.Error as e:
        print(f"Error: Could not log interaction: {e}", file=sys.stderr)
        sys.exit(1)


def view_leads(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Display carrier leads, optionally filtered by insurance status.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments (may include --status filter).
    """
    query = "SELECT dot_number, mc_number, name, fleet_size, phone, address, status, updated_at FROM carriers"
    params: list = []

    if args.status:
        query += " WHERE status = ?"
        params.append(args.status)

    query += " ORDER BY updated_at DESC"

    try:
        rows = conn.execute(query, params).fetchall()
    except sqlite3.Error as e:
        print(f"Error: Could not query leads: {e}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("No leads found.")
        return

    header = f"{'DOT#':<12} {'MC#':<12} {'Name':<28} {'Fleet':<6} {'Phone':<16} {'Status':<12} {'Updated':<12}"
    print(header)
    print("-" * len(header))
    for r in rows:
        dot, mc, name, fleet, phone, _addr, status, updated = r
        print(
            f"{dot or '':<12} {mc or '':<12} {name:<28.28} "
            f"{fleet or '':<6} {phone or '':<16} {status:<12} {updated[:10]:<12}"
        )
    print(f"\n{len(rows)} lead(s) total.")


def view_interactions(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Display interaction history for a specific carrier.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments containing --dot filter.
    """
    row = conn.execute(
        "SELECT name FROM carriers WHERE dot_number = ?", (args.dot,)
    ).fetchone()
    if row is None:
        print(f"Error: No carrier found with DOT# {args.dot}.", file=sys.stderr)
        sys.exit(1)

    try:
        interactions = conn.execute(
            """
            SELECT date, contact_person, type, notes
            FROM interactions
            WHERE dot_number = ?
            ORDER BY date DESC
            """,
            (args.dot,),
        ).fetchall()
    except sqlite3.Error as e:
        print(f"Error: Could not query interactions: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Interactions for {row[0]} (DOT# {args.dot}):\n")
    if not interactions:
        print("  No interactions recorded.")
        return

    for date, contact, itype, notes in interactions:
        print(f"  [{date}] {itype.upper()} — {contact or 'N/A'}")
        if notes:
            print(f"    {notes}")
        print()

    print(f"{len(interactions)} interaction(s) total.")


def update_status(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Update the insurance status of an existing carrier lead.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments containing --dot and --status.
    """
    now = datetime.now().isoformat(timespec="seconds")
    try:
        cur = conn.execute(
            "UPDATE carriers SET status = ?, updated_at = ? WHERE dot_number = ?",
            (args.status, now, args.dot),
        )
        conn.commit()
        if cur.rowcount == 0:
            print(f"Error: No carrier found with DOT# {args.dot}.", file=sys.stderr)
            sys.exit(1)
        print(f"Updated DOT# {args.dot} status to '{args.status}'.")
    except sqlite3.Error as e:
        print(f"Error: Could not update status: {e}", file=sys.stderr)
        sys.exit(1)


def export_csv(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    """Export carriers and their interaction counts to a CSV file.

    Args:
        conn: Active database connection.
        args: Parsed CLI arguments containing --output path.
    """
    try:
        rows = conn.execute(
            """
            SELECT
                c.dot_number, c.mc_number, c.name, c.fleet_size,
                c.phone, c.address, c.status, c.created_at, c.updated_at,
                COUNT(i.id) AS interaction_count,
                MAX(i.date) AS last_interaction
            FROM carriers c
            LEFT JOIN interactions i ON c.dot_number = i.dot_number
            GROUP BY c.dot_number
            ORDER BY c.updated_at DESC
            """
        ).fetchall()
    except sqlite3.Error as e:
        print(f"Error: Could not query data for export: {e}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("No data to export.")
        return

    output_path = args.output
    try:
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "DOT#",
                    "MC#",
                    "Name",
                    "Fleet Size",
                    "Phone",
                    "Address",
                    "Status",
                    "Created",
                    "Updated",
                    "Interactions",
                    "Last Interaction",
                ]
            )
            writer.writerows(rows)
        print(f"Exported {len(rows)} lead(s) to {output_path}")
    except OSError as e:
        print(f"Error: Could not write CSV to {output_path}: {e}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser with all subcommands.

    Returns:
        Configured argparse.ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="insurance_crm_tool",
        description="CRM tool for managing trucking company insurance leads and interactions.",
        epilog="Use '%(prog)s <command> --help' for details on each command.",
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB),
        help=f"Path to SQLite database (default: {DEFAULT_DB})",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- add-lead ---
    p_add = sub.add_parser(
        "add-lead",
        help="Add a new carrier lead",
        description="Register a new trucking carrier as an insurance lead.",
    )
    p_add.add_argument("--dot", required=True, help="USDOT number (unique identifier)")
    p_add.add_argument("--mc", default=None, help="MC number")
    p_add.add_argument("--name", required=True, help="Carrier / company name")
    p_add.add_argument("--fleet-size", type=int, default=None, help="Number of power units")
    p_add.add_argument("--phone", default=None, help="Primary phone number")
    p_add.add_argument("--address", default=None, help="Business address")
    p_add.add_argument(
        "--status",
        choices=INSURANCE_STATUSES,
        default="prospect",
        help="Insurance pipeline status (default: prospect)",
    )

    # --- log-interaction ---
    p_log = sub.add_parser(
        "log-interaction",
        help="Log an interaction with a carrier",
        description="Record a call, email, meeting, or other interaction with a carrier lead.",
    )
    p_log.add_argument("--dot", required=True, help="USDOT number of the carrier")
    p_log.add_argument("--contact", default=None, help="Name of the contact person")
    p_log.add_argument(
        "--type",
        required=True,
        choices=INTERACTION_TYPES,
        help="Type of interaction",
    )
    p_log.add_argument("--date", default=None, help="Date of interaction (YYYY-MM-DD; default: today)")
    p_log.add_argument("--notes", default=None, help="Free-text notes about the interaction")

    # --- view-leads ---
    p_view = sub.add_parser(
        "view-leads",
        help="View carrier leads",
        description="List all carrier leads, optionally filtered by status.",
    )
    p_view.add_argument(
        "--status",
        choices=INSURANCE_STATUSES,
        default=None,
        help="Filter by insurance status",
    )

    # --- view-interactions ---
    p_hist = sub.add_parser(
        "view-interactions",
        help="View interactions for a carrier",
        description="Show the interaction history for a specific carrier lead.",
    )
    p_hist.add_argument("--dot", required=True, help="USDOT number of the carrier")

    # --- update-status ---
    p_upd = sub.add_parser(
        "update-status",
        help="Update a lead's insurance status",
        description="Change the insurance pipeline status of a carrier lead.",
    )
    p_upd.add_argument("--dot", required=True, help="USDOT number of the carrier")
    p_upd.add_argument(
        "--status",
        required=True,
        choices=INSURANCE_STATUSES,
        help="New insurance status",
    )

    # --- export ---
    p_exp = sub.add_parser(
        "export",
        help="Export leads and interaction summary to CSV",
        description="Export all carrier leads with interaction counts to a CSV file.",
    )
    p_exp.add_argument(
        "--output",
        default="insurance_leads_export.csv",
        help="Output CSV file path (default: insurance_leads_export.csv)",
    )

    return parser


COMMAND_MAP = {
    "add-lead": add_lead,
    "log-interaction": log_interaction,
    "view-leads": view_leads,
    "view-interactions": view_interactions,
    "update-status": update_status,
    "export": export_csv,
}


def main() -> None:
    """Entry point: parse arguments, open the database, and dispatch the command."""
    parser = build_parser()
    args = parser.parse_args()

    conn = init_db(args.db)
    try:
        COMMAND_MAP[args.command](conn, args)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
