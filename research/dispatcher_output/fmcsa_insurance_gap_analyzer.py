#!/usr/bin/env python3
"""
FMCSA Insurance Gap Analyzer

Queries the FMCSA Company Census dataset via the Socrata API to identify
motor carriers with insurance filing gaps exceeding a configurable threshold.

Dataset: FMCSA Company Census — Active & Authorized Motor Carriers
Primary endpoint: https://datahub.transportation.gov/resource/az4n-8mr2.json
Fallback endpoint: https://data.transportation.gov/resource/az4b-hbig.json

Features:
    - Filter by state and insurance gap threshold (days)
    - Cross-reference against a carrier watchlist file
    - Store results in a SQLite database for history tracking
    - Output as markdown table, CSV, or JSON
    - Risk classification based on gap severity

Usage:
    # Carriers in Texas with >90-day insurance gaps
    python fmcsa_insurance_gap_analyzer.py --state TX

    # Custom gap threshold, CSV output
    python fmcsa_insurance_gap_analyzer.py --state CA --insurance-gap-days 60 --output-format csv

    # Filter against a watchlist of DOT numbers
    python fmcsa_insurance_gap_analyzer.py --carriers-file watchlist.txt --output-format json

    # All states, default settings
    python fmcsa_insurance_gap_analyzer.py
"""

import argparse
import csv
import io
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timedelta

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_ENDPOINTS = [
    "https://datahub.transportation.gov/resource/az4n-8mr2.json",
    "https://data.transportation.gov/resource/az4b-hbig.json",
]
PAGE_SIZE = 1000
REQUEST_TIMEOUT = 30
DEFAULT_GAP_DAYS = 90
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fmcsa_insurance_gaps.db")

VALID_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze FMCSA carrier insurance filing gaps.",
        epilog=(
            "Examples:\n"
            "  python fmcsa_insurance_gap_analyzer.py --state TX\n"
            "  python fmcsa_insurance_gap_analyzer.py --state CA --insurance-gap-days 60 --output-format csv\n"
            "  python fmcsa_insurance_gap_analyzer.py --carriers-file watchlist.txt --output-format json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Two-letter state abbreviation to filter carriers (e.g. TX, CA).",
    )
    parser.add_argument(
        "--insurance-gap-days",
        type=int,
        default=DEFAULT_GAP_DAYS,
        help=f"Minimum insurance filing gap in days to flag. Default: {DEFAULT_GAP_DAYS}.",
    )
    parser.add_argument(
        "--output-format",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format: markdown table (default), csv, or json.",
    )
    parser.add_argument(
        "--carriers-file",
        type=str,
        default=None,
        help="Path to a watchlist file with one DOT number per line.",
    )
    parser.add_argument(
        "--app-token",
        type=str,
        default=os.environ.get("SOCRATA_APP_TOKEN"),
        help="Socrata app token for higher rate limits. Also reads SOCRATA_APP_TOKEN env var.",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=DB_PATH,
        help=f"SQLite database path for history tracking. Default: {DB_PATH}",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    args = parser.parse_args()

    if args.state and args.state.upper() not in VALID_STATES:
        parser.error(f"Invalid state: {args.state}. Must be a two-letter US state/territory code.")
    if args.state:
        args.state = args.state.upper()

    return args


# ---------------------------------------------------------------------------
# Watchlist loading
# ---------------------------------------------------------------------------

def load_watchlist(filepath: str) -> set[str]:
    """Load DOT numbers from a watchlist file (one per line).

    Args:
        filepath: Path to the watchlist text file.

    Returns:
        Set of DOT number strings.
    """
    dot_numbers = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                dot_numbers.add(stripped)
    log.info("Loaded %d DOT numbers from watchlist: %s", len(dot_numbers), filepath)
    return dot_numbers


# ---------------------------------------------------------------------------
# API interaction
# ---------------------------------------------------------------------------

def build_where_clause(state: str | None) -> str:
    """Build a SoQL $where clause for active carriers.

    Args:
        state: Optional two-letter state code.

    Returns:
        SoQL WHERE clause string.
    """
    clauses = ["status_code = 'A'"]
    if state:
        clauses.append(f"phy_state = '{state}'")
    return " AND ".join(clauses)


def fetch_carriers(where: str, app_token: str | None = None) -> list[dict]:
    """Fetch carriers from the Socrata API with pagination and endpoint fallback.

    Args:
        where: SoQL $where clause.
        app_token: Optional Socrata app token.

    Returns:
        List of carrier record dicts from the API.

    Raises:
        SystemExit: If all API endpoints fail.
    """
    headers = {"Accept": "application/json"}
    if app_token:
        headers["X-App-Token"] = app_token

    for endpoint in API_ENDPOINTS:
        log.info("Trying endpoint: %s", endpoint)
        try:
            return _fetch_from_endpoint(endpoint, where, headers)
        except requests.exceptions.RequestException as exc:
            log.warning("Endpoint %s failed: %s", endpoint, exc)
            continue

    log.error("All API endpoints failed.")
    sys.exit(1)


def _fetch_from_endpoint(endpoint: str, where: str, headers: dict) -> list[dict]:
    """Page through a single Socrata endpoint.

    Args:
        endpoint: Full API URL.
        where: SoQL $where clause.
        headers: HTTP headers dict.

    Returns:
        List of all matching records.
    """
    all_records = []
    offset = 0

    while True:
        params = {
            "$where": where,
            "$limit": PAGE_SIZE,
            "$offset": offset,
            "$order": "dot_number ASC",
        }
        log.debug("GET %s offset=%d", endpoint, offset)

        resp = requests.get(endpoint, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        # Guard against HTML error pages
        content_type = resp.headers.get("Content-Type", "")
        if "json" not in content_type and "javascript" not in content_type:
            raise requests.exceptions.RequestException(
                f"Non-JSON response (Content-Type: {content_type})"
            )

        batch = resp.json()
        if not batch:
            break

        all_records.extend(batch)
        log.info("Fetched %d records (total: %d)", len(batch), len(all_records))

        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return all_records


# ---------------------------------------------------------------------------
# Record transformation & gap calculation
# ---------------------------------------------------------------------------

def parse_date(date_str: str | None) -> datetime | None:
    """Parse a Socrata date string into a datetime object.

    Handles ISO 8601 format (with or without time component) and
    common date-only formats.

    Args:
        date_str: Date string from the API.

    Returns:
        datetime object or None if unparseable.
    """
    if not date_str or not date_str.strip():
        return None
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def build_mc_number(record: dict) -> str:
    """Construct MC number from docket prefix and number fields.

    Args:
        record: Raw API record dict.

    Returns:
        Formatted MC number string or empty string.
    """
    prefix = record.get("docket1prefix", "").strip()
    number = record.get("docket1", "").strip()
    if prefix and number:
        return f"{prefix}-{number}"
    return number


def classify_risk(gap_days: int) -> str:
    """Classify insurance gap risk based on severity.

    Args:
        gap_days: Number of days since last insurance filing.

    Returns:
        Risk classification string.
    """
    if gap_days >= 365:
        return "CRITICAL"
    if gap_days >= 180:
        return "HIGH"
    if gap_days >= 90:
        return "MEDIUM"
    return "LOW"


def transform_and_filter(
    raw_records: list[dict],
    gap_threshold: int,
    watchlist: set[str] | None = None,
) -> list[dict]:
    """Transform raw API records and filter by insurance gap threshold.

    Args:
        raw_records: List of raw record dicts from the API.
        gap_threshold: Minimum gap in days to include a carrier.
        watchlist: Optional set of DOT numbers to restrict results to.

    Returns:
        List of transformed carrier dicts sorted by gap_days descending.
    """
    now = datetime.now()
    results = []

    for record in raw_records:
        dot_number = record.get("dot_number", "").strip()

        # If watchlist provided, skip carriers not on it
        if watchlist and dot_number not in watchlist:
            continue

        # Parse insurance-related dates
        mcs150_raw = record.get("mcs150_date", "")
        mcs150_date = parse_date(mcs150_raw)

        # Use add_date as a proxy for initial filing if mcs150 unavailable
        add_date_raw = record.get("add_date", "")
        add_date = parse_date(add_date_raw)

        # Determine the most recent filing date
        filing_date = mcs150_date or add_date
        if filing_date is None:
            continue

        gap_days = (now - filing_date).days

        if gap_days < gap_threshold:
            continue

        fleet_size = record.get("power_units", "0").strip()
        try:
            fleet_size_int = int(fleet_size)
        except (ValueError, TypeError):
            fleet_size_int = 0

        results.append({
            "dot_number": dot_number,
            "mc_number": build_mc_number(record),
            "company_name": record.get("legal_name", "").strip(),
            "state": record.get("phy_state", "").strip(),
            "phone": record.get("phone", "").strip(),
            "fleet_size": fleet_size_int,
            "last_filing_date": filing_date.strftime("%Y-%m-%d"),
            "mcs150_date": mcs150_date.strftime("%Y-%m-%d") if mcs150_date else "",
            "gap_days": gap_days,
            "risk": classify_risk(gap_days),
            "on_watchlist": "Yes" if watchlist and dot_number in watchlist else "No",
        })

    results.sort(key=lambda r: r["gap_days"], reverse=True)
    log.info("Found %d carriers exceeding %d-day gap threshold.", len(results), gap_threshold)
    return results


# ---------------------------------------------------------------------------
# SQLite history tracking
# ---------------------------------------------------------------------------

def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize the SQLite database and create table if needed.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        sqlite3.Connection object.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS insurance_gap_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date TEXT NOT NULL,
            dot_number TEXT NOT NULL,
            mc_number TEXT,
            company_name TEXT,
            state TEXT,
            phone TEXT,
            fleet_size INTEGER,
            last_filing_date TEXT,
            mcs150_date TEXT,
            gap_days INTEGER,
            risk TEXT,
            on_watchlist TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_gap_dot
        ON insurance_gap_history (dot_number, scan_date)
    """)
    conn.commit()
    log.info("Database initialized: %s", db_path)
    return conn


def save_to_db(conn: sqlite3.Connection, carriers: list[dict]):
    """Insert carrier gap records into the history database.

    Args:
        conn: SQLite connection.
        carriers: List of transformed carrier dicts.
    """
    scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        (
            scan_date,
            c["dot_number"],
            c["mc_number"],
            c["company_name"],
            c["state"],
            c["phone"],
            c["fleet_size"],
            c["last_filing_date"],
            c["mcs150_date"],
            c["gap_days"],
            c["risk"],
            c["on_watchlist"],
        )
        for c in carriers
    ]
    conn.executemany(
        """INSERT INTO insurance_gap_history
           (scan_date, dot_number, mc_number, company_name, state, phone,
            fleet_size, last_filing_date, mcs150_date, gap_days, risk, on_watchlist)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    log.info("Saved %d records to database.", len(rows))


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_table(carriers: list[dict]) -> str:
    """Format carrier data as a markdown table sorted by gap severity.

    Args:
        carriers: List of transformed carrier dicts.

    Returns:
        Markdown-formatted table string.
    """
    if not carriers:
        return "No carriers found with insurance filing gaps exceeding the threshold."

    lines = [
        f"# FMCSA Insurance Gap Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"**{len(carriers)} carriers** with insurance filing gaps",
        "",
        "| Risk | DOT # | MC # | Company | State | Fleet | Last Filing | Gap (days) | Phone | Watchlist |",
        "|------|-------|------|---------|-------|-------|-------------|------------|-------|-----------|",
    ]
    for c in carriers:
        lines.append(
            f"| {c['risk']} | {c['dot_number']} | {c['mc_number']} | "
            f"{c['company_name'][:40]} | {c['state']} | {c['fleet_size']} | "
            f"{c['last_filing_date']} | {c['gap_days']} | {c['phone']} | {c['on_watchlist']} |"
        )
    return "\n".join(lines)


def format_csv(carriers: list[dict]) -> str:
    """Format carrier data as CSV.

    Args:
        carriers: List of transformed carrier dicts.

    Returns:
        CSV-formatted string.
    """
    if not carriers:
        return ""
    output = io.StringIO()
    fieldnames = [
        "risk", "dot_number", "mc_number", "company_name", "state",
        "fleet_size", "last_filing_date", "mcs150_date", "gap_days", "phone", "on_watchlist",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(carriers)
    return output.getvalue()


def format_json(carriers: list[dict]) -> str:
    """Format carrier data as JSON.

    Args:
        carriers: List of transformed carrier dicts.

    Returns:
        JSON-formatted string.
    """
    return json.dumps(carriers, indent=2)


FORMATTERS = {
    "table": format_table,
    "csv": format_csv,
    "json": format_json,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Entry point: parse args, query API, filter, store, and report."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load watchlist if provided
    watchlist = None
    if args.carriers_file:
        watchlist = load_watchlist(args.carriers_file)

    # Build query and fetch
    where = build_where_clause(args.state)
    log.info(
        "Querying FMCSA API: state=%s, gap_threshold=%d days",
        args.state or "ALL",
        args.insurance_gap_days,
    )
    log.debug("SoQL $where: %s", where)

    raw_records = fetch_carriers(where, args.app_token)
    log.info("Retrieved %d raw carrier records.", len(raw_records))

    # Transform and filter
    carriers = transform_and_filter(raw_records, args.insurance_gap_days, watchlist)

    # Store in SQLite
    conn = init_db(args.db_path)
    try:
        if carriers:
            save_to_db(conn, carriers)
        else:
            log.info("No carriers matched — nothing saved to database.")
    finally:
        conn.close()

    # Output
    formatter = FORMATTERS[args.output_format]
    output = formatter(carriers)
    print(output)

    # Summary stats
    if carriers and args.output_format == "table":
        risk_counts = {}
        for c in carriers:
            risk_counts[c["risk"]] = risk_counts.get(c["risk"], 0) + 1
        print("\n## Risk Summary\n")
        for risk in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if risk in risk_counts:
                print(f"- **{risk}**: {risk_counts[risk]} carriers")
        print(f"\nResults saved to: {args.db_path}")


if __name__ == "__main__":
    main()
