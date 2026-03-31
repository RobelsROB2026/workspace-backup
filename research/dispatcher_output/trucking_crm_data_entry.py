#!/usr/bin/env python3
"""
Trucking Company Insurance Leads CRM Data Entry Tool

A command-line CRM for tracking interactions with trucking company insurance
leads. Supports CRUD operations, batch CSV import, and formatted reporting.
Data is stored in a local SQLite database.

Usage examples:
    # Add a new carrier lead
    python trucking_crm_data_entry.py add \
        --carrier-name "ABC Trucking" --dot-number 1234567 \
        --mc-number 987654 --fleet-size 25 --phone "555-123-4567" \
        --email "info@abctrucking.com" --state TX

    # Log an interaction
    python trucking_crm_data_entry.py interact \
        --dot-number 1234567 --interaction-type "initial contact" \
        --notes "Spoke with owner about fleet coverage" --date 2026-03-28

    # Search leads
    python trucking_crm_data_entry.py search --state TX
    python trucking_crm_data_entry.py search --dot-number 1234567
    python trucking_crm_data_entry.py search --interaction-type "follow-up"

    # Update a carrier record
    python trucking_crm_data_entry.py update --dot-number 1234567 \
        --fleet-size 30 --email "new@abctrucking.com"

    # Delete a carrier record
    python trucking_crm_data_entry.py delete --dot-number 1234567

    # Batch import from CSV
    python trucking_crm_data_entry.py import --csv-file leads.csv

    # Generate reports
    python trucking_crm_data_entry.py report
"""

import argparse
import csv
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "trucking_crm_data_entry.db"
LOG_PATH = Path(__file__).parent / "trucking_crm_data_entry.log"

VALID_INTERACTION_TYPES = [
    "initial contact",
    "follow-up",
    "meeting scheduled",
    "quote requested",
]

US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

# ---------------------------------------------------------------------------
# Logging setup
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


def get_connection():
    """Return a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the carriers and interactions tables if they do not exist."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS carriers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                carrier_name    TEXT NOT NULL,
                dot_number      TEXT NOT NULL UNIQUE,
                mc_number       TEXT,
                fleet_size      INTEGER,
                phone           TEXT,
                email           TEXT,
                state           TEXT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                carrier_id       INTEGER NOT NULL,
                interaction_type TEXT NOT NULL,
                notes            TEXT,
                interaction_date TEXT NOT NULL,
                created_at       TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_carriers_dot ON carriers(dot_number);
            CREATE INDEX IF NOT EXISTS idx_carriers_state ON carriers(state);
            CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(interaction_type);
        """)
        conn.commit()
        logger.info("Database initialized at %s", DB_PATH)
    except sqlite3.Error as exc:
        logger.error("Failed to initialize database: %s", exc)
        raise
    finally:
        conn.close()

# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------


def add_carrier(carrier_name, dot_number, mc_number=None, fleet_size=None,
                phone=None, email=None, state=None):
    """Insert a new carrier lead into the database.

    Args:
        carrier_name: Name of the trucking company.
        dot_number: USDOT number (unique identifier).
        mc_number: Motor carrier number (optional).
        fleet_size: Number of vehicles in the fleet (optional).
        phone: Contact phone number (optional).
        email: Contact email address (optional).
        state: Two-letter US state code (optional).

    Returns:
        The row id of the newly inserted carrier.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO carriers
               (carrier_name, dot_number, mc_number, fleet_size, phone, email, state)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (carrier_name, str(dot_number), mc_number, fleet_size, phone, email,
             state.upper() if state else None),
        )
        conn.commit()
        logger.info("Added carrier '%s' (DOT %s)", carrier_name, dot_number)
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        logger.error("Carrier with DOT number %s already exists", dot_number)
        raise
    except sqlite3.Error as exc:
        logger.error("Error adding carrier: %s", exc)
        raise
    finally:
        conn.close()


def update_carrier(dot_number, **fields):
    """Update an existing carrier record identified by DOT number.

    Args:
        dot_number: The USDOT number of the carrier to update.
        **fields: Keyword arguments for columns to update. Accepted keys:
            carrier_name, mc_number, fleet_size, phone, email, state.

    Returns:
        Number of rows updated (0 or 1).
    """
    allowed = {"carrier_name", "mc_number", "fleet_size", "phone", "email", "state"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}

    if not updates:
        logger.warning("No valid fields provided for update")
        return 0

    if "state" in updates:
        updates["state"] = updates["state"].upper()

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values())
    values.append(str(dot_number))

    conn = get_connection()
    try:
        cursor = conn.execute(
            f"UPDATE carriers SET {set_clause}, updated_at = datetime('now') "
            "WHERE dot_number = ?",
            values,
        )
        conn.commit()
        if cursor.rowcount:
            logger.info("Updated carrier DOT %s: %s", dot_number, updates)
        else:
            logger.warning("No carrier found with DOT number %s", dot_number)
        return cursor.rowcount
    except sqlite3.Error as exc:
        logger.error("Error updating carrier: %s", exc)
        raise
    finally:
        conn.close()


def delete_carrier(dot_number):
    """Delete a carrier and all associated interactions by DOT number.

    Args:
        dot_number: The USDOT number of the carrier to delete.

    Returns:
        Number of rows deleted (0 or 1).
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM carriers WHERE dot_number = ?",
            (str(dot_number),),
        )
        conn.commit()
        if cursor.rowcount:
            logger.info("Deleted carrier DOT %s and related interactions", dot_number)
        else:
            logger.warning("No carrier found with DOT number %s", dot_number)
        return cursor.rowcount
    except sqlite3.Error as exc:
        logger.error("Error deleting carrier: %s", exc)
        raise
    finally:
        conn.close()


def add_interaction(dot_number, interaction_type, notes=None, date=None):
    """Log a new interaction for a carrier.

    Args:
        dot_number: The USDOT number of the carrier.
        interaction_type: One of the valid interaction types.
        notes: Free-text notes about the interaction (optional).
        date: Date of interaction as YYYY-MM-DD string (defaults to today).

    Returns:
        The row id of the newly inserted interaction.
    """
    interaction_type_lower = interaction_type.lower()
    if interaction_type_lower not in VALID_INTERACTION_TYPES:
        raise ValueError(
            f"Invalid interaction type '{interaction_type}'. "
            f"Must be one of: {', '.join(VALID_INTERACTION_TYPES)}"
        )

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM carriers WHERE dot_number = ?",
            (str(dot_number),),
        ).fetchone()
        if not row:
            raise ValueError(f"No carrier found with DOT number {dot_number}")

        cursor = conn.execute(
            """INSERT INTO interactions (carrier_id, interaction_type, notes, interaction_date)
               VALUES (?, ?, ?, ?)""",
            (row["id"], interaction_type_lower, notes, date),
        )
        conn.commit()
        logger.info("Logged '%s' interaction for DOT %s", interaction_type_lower, dot_number)
        return cursor.lastrowid
    except sqlite3.Error as exc:
        logger.error("Error adding interaction: %s", exc)
        raise
    finally:
        conn.close()


def search_carriers(dot_number=None, state=None, interaction_type=None):
    """Search carriers with optional filters.

    Args:
        dot_number: Filter by exact DOT number (optional).
        state: Filter by state code (optional).
        interaction_type: Filter by interaction type (optional).

    Returns:
        List of matching carrier rows (as dicts).
    """
    conn = get_connection()
    try:
        if interaction_type:
            query = """
                SELECT DISTINCT c.* FROM carriers c
                JOIN interactions i ON c.id = i.carrier_id
                WHERE 1=1
            """
        else:
            query = "SELECT * FROM carriers WHERE 1=1"

        params = []
        if dot_number:
            query += " AND c.dot_number = ?" if interaction_type else " AND dot_number = ?"
            params.append(str(dot_number))
        if state:
            col = "c.state" if interaction_type else "state"
            query += f" AND {col} = ?"
            params.append(state.upper())
        if interaction_type:
            query += " AND i.interaction_type = ?"
            params.append(interaction_type.lower())

        query += " ORDER BY " + ("c.carrier_name" if interaction_type else "carrier_name")

        rows = conn.execute(query, params).fetchall()
        logger.info("Search returned %d result(s)", len(rows))
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("Error searching carriers: %s", exc)
        raise
    finally:
        conn.close()

# ---------------------------------------------------------------------------
# CSV batch import
# ---------------------------------------------------------------------------


def import_csv(csv_path):
    """Batch-import carrier leads from a CSV file.

    Expected CSV columns (header row required):
        carrier_name, dot_number, mc_number, fleet_size, phone, email, state

    Optional additional columns for an initial interaction:
        interaction_type, notes, date

    Args:
        csv_path: Path to the CSV file.

    Returns:
        Tuple of (imported_count, skipped_count).
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    imported = 0
    skipped = 0

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row_num, row in enumerate(reader, start=2):
            # Normalize keys
            row = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if v}

            carrier_name = row.get("carrier_name")
            dot_number = row.get("dot_number")
            if not carrier_name or not dot_number:
                logger.warning("Row %d: missing carrier_name or dot_number, skipping", row_num)
                skipped += 1
                continue

            try:
                add_carrier(
                    carrier_name=carrier_name,
                    dot_number=dot_number,
                    mc_number=row.get("mc_number"),
                    fleet_size=int(row["fleet_size"]) if row.get("fleet_size") else None,
                    phone=row.get("phone"),
                    email=row.get("email"),
                    state=row.get("state"),
                )

                # If the CSV row includes interaction data, log it too
                itype = row.get("interaction_type")
                if itype:
                    try:
                        add_interaction(
                            dot_number=dot_number,
                            interaction_type=itype,
                            notes=row.get("notes"),
                            date=row.get("date"),
                        )
                    except ValueError as exc:
                        logger.warning("Row %d interaction skipped: %s", row_num, exc)

                imported += 1
            except sqlite3.IntegrityError:
                logger.warning("Row %d: DOT %s already exists, skipping", row_num, dot_number)
                skipped += 1
            except Exception as exc:
                logger.error("Row %d: unexpected error: %s", row_num, exc)
                skipped += 1

    logger.info("CSV import complete: %d imported, %d skipped", imported, skipped)
    return imported, skipped

# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def generate_report():
    """Generate and print a formatted summary report.

    Report includes:
        - Total number of carrier leads
        - Interactions per carrier
        - Leads breakdown by state
        - Interactions breakdown by type
    """
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) AS cnt FROM carriers").fetchone()["cnt"]

        interactions_per_carrier = conn.execute("""
            SELECT c.carrier_name, c.dot_number, COUNT(i.id) AS interaction_count
            FROM carriers c
            LEFT JOIN interactions i ON c.id = i.carrier_id
            GROUP BY c.id
            ORDER BY interaction_count DESC, c.carrier_name
        """).fetchall()

        state_breakdown = conn.execute("""
            SELECT COALESCE(state, 'Unknown') AS state, COUNT(*) AS cnt
            FROM carriers
            GROUP BY state
            ORDER BY cnt DESC
        """).fetchall()

        type_breakdown = conn.execute("""
            SELECT interaction_type, COUNT(*) AS cnt
            FROM interactions
            GROUP BY interaction_type
            ORDER BY cnt DESC
        """).fetchall()

        # Format output
        sep = "=" * 60
        print(f"\n{sep}")
        print("  TRUCKING INSURANCE LEADS CRM REPORT")
        print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(sep)

        print(f"\n  Total carrier leads: {total}\n")

        print("-" * 60)
        print("  INTERACTIONS PER CARRIER")
        print("-" * 60)
        if interactions_per_carrier:
            print(f"  {'Carrier':<30} {'DOT':<12} {'Interactions':>12}")
            print(f"  {'-------':<30} {'---':<12} {'------------':>12}")
            for row in interactions_per_carrier:
                name = row["carrier_name"][:28]
                print(f"  {name:<30} {row['dot_number']:<12} {row['interaction_count']:>12}")
        else:
            print("  No carriers in database.")

        print(f"\n{'-' * 60}")
        print("  LEADS BY STATE")
        print("-" * 60)
        if state_breakdown:
            print(f"  {'State':<10} {'Count':>8}")
            print(f"  {'-----':<10} {'-----':>8}")
            for row in state_breakdown:
                print(f"  {row['state']:<10} {row['cnt']:>8}")
        else:
            print("  No data.")

        print(f"\n{'-' * 60}")
        print("  INTERACTIONS BY TYPE")
        print("-" * 60)
        if type_breakdown:
            print(f"  {'Type':<25} {'Count':>8}")
            print(f"  {'----':<25} {'-----':>8}")
            for row in type_breakdown:
                print(f"  {row['interaction_type']:<25} {row['cnt']:>8}")
        else:
            print("  No interactions recorded.")

        print(f"\n{sep}\n")
        logger.info("Report generated")
    except sqlite3.Error as exc:
        logger.error("Error generating report: %s", exc)
        raise
    finally:
        conn.close()

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def print_carriers(carriers):
    """Pretty-print a list of carrier records.

    Args:
        carriers: List of carrier dicts as returned by search_carriers().
    """
    if not carriers:
        print("No carriers found.")
        return

    sep = "-" * 80
    for c in carriers:
        print(sep)
        print(f"  Carrier:    {c['carrier_name']}")
        print(f"  DOT#:       {c['dot_number']}")
        print(f"  MC#:        {c.get('mc_number') or 'N/A'}")
        print(f"  Fleet Size: {c.get('fleet_size') or 'N/A'}")
        print(f"  Phone:      {c.get('phone') or 'N/A'}")
        print(f"  Email:      {c.get('email') or 'N/A'}")
        print(f"  State:      {c.get('state') or 'N/A'}")
        print(f"  Added:      {c['created_at']}")
        print(f"  Updated:    {c['updated_at']}")
    print(sep)
    print(f"\n  {len(carriers)} result(s) found.\n")

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def build_parser():
    """Build and return the argparse argument parser.

    Returns:
        Configured argparse.ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="trucking_crm_data_entry",
        description="CRM data entry tool for tracking trucking company insurance leads.",
        epilog="Examples:\n"
               "  %(prog)s add --carrier-name 'ABC Trucking' --dot-number 1234567 --state TX\n"
               "  %(prog)s interact --dot-number 1234567 --interaction-type 'initial contact'\n"
               "  %(prog)s search --state TX\n"
               "  %(prog)s import --csv-file leads.csv\n"
               "  %(prog)s report\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- add ---
    p_add = subparsers.add_parser("add", help="Add a new carrier lead")
    p_add.add_argument("--carrier-name", required=True, help="Trucking company name")
    p_add.add_argument("--dot-number", required=True, help="USDOT number")
    p_add.add_argument("--mc-number", help="Motor carrier number")
    p_add.add_argument("--fleet-size", type=int, help="Number of vehicles")
    p_add.add_argument("--phone", help="Contact phone number")
    p_add.add_argument("--email", help="Contact email address")
    p_add.add_argument("--state", choices=US_STATES, help="Two-letter state code")

    # --- update ---
    p_upd = subparsers.add_parser("update", help="Update an existing carrier record")
    p_upd.add_argument("--dot-number", required=True, help="DOT number of carrier to update")
    p_upd.add_argument("--carrier-name", help="New carrier name")
    p_upd.add_argument("--mc-number", help="New MC number")
    p_upd.add_argument("--fleet-size", type=int, help="New fleet size")
    p_upd.add_argument("--phone", help="New phone number")
    p_upd.add_argument("--email", help="New email address")
    p_upd.add_argument("--state", choices=US_STATES, help="New state code")

    # --- delete ---
    p_del = subparsers.add_parser("delete", help="Delete a carrier and its interactions")
    p_del.add_argument("--dot-number", required=True, help="DOT number of carrier to delete")

    # --- interact ---
    p_int = subparsers.add_parser("interact", help="Log an interaction with a carrier")
    p_int.add_argument("--dot-number", required=True, help="DOT number of the carrier")
    p_int.add_argument(
        "--interaction-type", required=True,
        choices=VALID_INTERACTION_TYPES,
        help="Type of interaction",
    )
    p_int.add_argument("--notes", help="Notes about the interaction")
    p_int.add_argument("--date", help="Interaction date (YYYY-MM-DD, default: today)")

    # --- search ---
    p_srch = subparsers.add_parser("search", help="Search/filter carrier leads")
    p_srch.add_argument("--dot-number", help="Filter by DOT number")
    p_srch.add_argument("--state", choices=US_STATES, help="Filter by state")
    p_srch.add_argument(
        "--interaction-type",
        choices=VALID_INTERACTION_TYPES,
        help="Filter by interaction type",
    )

    # --- import ---
    p_imp = subparsers.add_parser("import", help="Batch-import leads from a CSV file")
    p_imp.add_argument("--csv-file", required=True, help="Path to CSV file")

    # --- report ---
    subparsers.add_parser("report", help="Generate a formatted summary report")

    return parser

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    """Parse arguments and dispatch to the appropriate CRM operation."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    init_db()

    try:
        if args.command == "add":
            carrier_id = add_carrier(
                carrier_name=args.carrier_name,
                dot_number=args.dot_number,
                mc_number=args.mc_number,
                fleet_size=args.fleet_size,
                phone=args.phone,
                email=args.email,
                state=args.state,
            )
            print(f"Carrier added successfully (ID: {carrier_id})")

        elif args.command == "update":
            count = update_carrier(
                dot_number=args.dot_number,
                carrier_name=args.carrier_name,
                mc_number=args.mc_number,
                fleet_size=args.fleet_size,
                phone=args.phone,
                email=args.email,
                state=args.state,
            )
            if count:
                print("Carrier updated successfully.")
            else:
                print(f"No carrier found with DOT number {args.dot_number}.")
                sys.exit(1)

        elif args.command == "delete":
            count = delete_carrier(args.dot_number)
            if count:
                print("Carrier deleted successfully.")
            else:
                print(f"No carrier found with DOT number {args.dot_number}.")
                sys.exit(1)

        elif args.command == "interact":
            interaction_id = add_interaction(
                dot_number=args.dot_number,
                interaction_type=args.interaction_type,
                notes=args.notes,
                date=args.date,
            )
            print(f"Interaction logged successfully (ID: {interaction_id})")

        elif args.command == "search":
            if not any([args.dot_number, args.state, args.interaction_type]):
                # No filters — show all
                results = search_carriers()
            else:
                results = search_carriers(
                    dot_number=args.dot_number,
                    state=args.state,
                    interaction_type=args.interaction_type,
                )
            print_carriers(results)

        elif args.command == "import":
            imported, skipped = import_csv(args.csv_file)
            print(f"Import complete: {imported} imported, {skipped} skipped.")

        elif args.command == "report":
            generate_report()

    except sqlite3.IntegrityError as exc:
        logger.error("Database integrity error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
