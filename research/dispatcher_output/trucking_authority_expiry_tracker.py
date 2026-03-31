#!/usr/bin/env python3
"""
Trucking Authority Expiry Tracker & Sales Call List Generator

Queries the FMCSA Socrata API (data.transportation.gov) for motor carriers
whose operating authority (MC number) insurance is about to expire within a
configurable window. Stores results in SQLite for history tracking. Generates
sales call lists and personalized email templates for outreach.

Requirements:
    pip install requests tabulate

Usage:
    python trucking_authority_expiry_tracker.py --state TX --days-until-expiry 30
    python trucking_authority_expiry_tracker.py --output-format csv --include-emails
    python trucking_authority_expiry_tracker.py --carriers-file watchlist.csv
"""

import argparse
import csv
import json
import logging
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger("authority_tracker")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOCRATA_API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"
REQUEST_TIMEOUT = 30
SOCRATA_PAGE_SIZE = 1000
MAX_RETRIES = 3
RETRY_BACKOFF = 2

DEFAULT_DB_PATH = os.path.expanduser(
    "~/research/dispatcher_output/authority_expiry_history.db"
)
DEFAULT_OUTPUT_DIR = os.path.expanduser(
    "~/research/dispatcher_output/expiry_reports"
)

# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------


def init_database(db_path: str) -> sqlite3.Connection:
    """Initialize SQLite database with carrier tracking tables."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS carriers (
            dot_number TEXT PRIMARY KEY,
            carrier_name TEXT,
            mc_number TEXT,
            state TEXT,
            phone TEXT,
            email TEXT,
            fleet_size TEXT,
            insurance_expiry_date TEXT,
            days_remaining INTEGER,
            last_checked TEXT,
            first_seen TEXT,
            outreach_status TEXT DEFAULT 'none',
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS check_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dot_number TEXT NOT NULL,
            check_date TEXT NOT NULL,
            insurance_expiry_date TEXT,
            days_remaining INTEGER,
            FOREIGN KEY (dot_number) REFERENCES carriers(dot_number)
        );

        CREATE INDEX IF NOT EXISTS idx_carriers_expiry
            ON carriers(insurance_expiry_date);
        CREATE INDEX IF NOT EXISTS idx_carriers_state
            ON carriers(state);
        CREATE INDEX IF NOT EXISTS idx_history_dot
            ON check_history(dot_number);
    """)
    conn.commit()
    return conn


def upsert_carrier(conn: sqlite3.Connection, carrier: Dict[str, Any]) -> None:
    """Insert or update a carrier record and log the check."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        INSERT INTO carriers
            (dot_number, carrier_name, mc_number, state, phone, email,
             fleet_size, insurance_expiry_date, days_remaining,
             last_checked, first_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(dot_number) DO UPDATE SET
            carrier_name = excluded.carrier_name,
            mc_number = excluded.mc_number,
            state = excluded.state,
            phone = COALESCE(NULLIF(excluded.phone, ''), carriers.phone),
            email = COALESCE(NULLIF(excluded.email, ''), carriers.email),
            fleet_size = excluded.fleet_size,
            insurance_expiry_date = excluded.insurance_expiry_date,
            days_remaining = excluded.days_remaining,
            last_checked = excluded.last_checked
        """,
        (
            carrier["dot_number"],
            carrier["carrier_name"],
            carrier["mc_number"],
            carrier["state"],
            carrier["phone"],
            carrier["email"],
            carrier["fleet_size"],
            carrier["insurance_expiry_date"],
            carrier["days_remaining"],
            now,
            now,
        ),
    )
    conn.execute(
        """
        INSERT INTO check_history (dot_number, check_date, insurance_expiry_date, days_remaining)
        VALUES (?, ?, ?, ?)
        """,
        (
            carrier["dot_number"],
            now,
            carrier["insurance_expiry_date"],
            carrier["days_remaining"],
        ),
    )


# ---------------------------------------------------------------------------
# FMCSA Socrata API
# ---------------------------------------------------------------------------


def build_session() -> requests.Session:
    """Build a requests session with retry logic."""
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.packages.urllib3.util.retry.Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {"User-Agent": "TruckingAuthorityExpiryTracker/1.0 (sales-research)"}
    )
    return session


def query_fmcsa_carriers(
    session: requests.Session,
    state: Optional[str] = None,
    days_until_expiry: int = 60,
    app_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Query the FMCSA Socrata API for carriers with expiring authority.

    Uses the dataset at data.transportation.gov/resource/az4b-hbig.json
    with filters for state and fleet size > 5.
    """
    today = datetime.utcnow().date()
    cutoff = today + timedelta(days=days_until_expiry)

    # Build SoQL WHERE clause
    where_parts = [
        f"mcs_150_form_date >= '{today.isoformat()}'",
        f"mcs_150_form_date <= '{cutoff.isoformat()}'",
    ]

    params: Dict[str, str] = {
        "$order": "mcs_150_form_date ASC",
        "$limit": str(SOCRATA_PAGE_SIZE),
    }

    # State filter
    if state:
        params["state"] = state.upper()
        where_parts.append(f"phy_state = '{state.upper()}'")

    # Fleet size > 5
    params["fleet_size"] = "GT 5"

    params["$where"] = " AND ".join(where_parts)

    headers = {}
    if app_token:
        headers["X-App-Token"] = app_token

    all_rows: List[Dict[str, Any]] = []
    offset = 0

    while True:
        page_params = {**params, "$offset": str(offset)}
        logger.debug("Querying FMCSA API: params=%s", page_params)

        try:
            resp = session.get(
                SOCRATA_API_URL,
                params=page_params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error querying FMCSA API: %s", exc)
            break
        except requests.exceptions.Timeout:
            logger.error("Request timed out after %ds", REQUEST_TIMEOUT)
            break
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error from FMCSA API: %s (response: %s)",
                         exc, getattr(exc.response, 'text', '')[:200])
            break

        try:
            rows = resp.json()
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from API")
            break

        if not isinstance(rows, list):
            logger.error("Unexpected response format: %s", type(rows).__name__)
            break

        logger.info("Fetched page at offset %d: %d records", offset, len(rows))
        all_rows.extend(rows)

        if len(rows) < SOCRATA_PAGE_SIZE:
            break
        offset += SOCRATA_PAGE_SIZE
        time.sleep(0.3)

    return all_rows


def normalize_carrier(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw Socrata row into a standardized carrier dict."""
    today = datetime.utcnow().date()

    # Parse expiry date
    expiry_raw = raw.get("mcs_150_form_date", "") or ""
    expiry_date = None
    expiry_str = ""
    days_remaining = -1

    if expiry_raw:
        try:
            expiry_date = datetime.fromisoformat(
                expiry_raw.replace("Z", "+00:00")
            ).date()
            expiry_str = expiry_date.strftime("%Y-%m-%d")
            days_remaining = (expiry_date - today).days
        except ValueError:
            expiry_str = expiry_raw[:10]

    # Phone formatting
    phone_raw = str(raw.get("telephone", "") or "")
    phone = ""
    if phone_raw:
        digits = re.sub(r"\D", "", phone_raw)[-10:]
        if len(digits) == 10:
            phone = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        else:
            phone = phone_raw

    # Fleet size
    fleet = raw.get("total_power_units", "") or raw.get("total_drivers", "") or ""

    return {
        "carrier_name": (raw.get("legal_name") or "").strip().title(),
        "dot_number": str(raw.get("dot_number", "")),
        "mc_number": str(raw.get("mc_mx_ff_number", "") or ""),
        "insurance_expiry_date": expiry_str,
        "days_remaining": days_remaining,
        "fleet_size": str(fleet),
        "phone": phone,
        "email": (raw.get("email_address") or "").strip().lower(),
        "state": (raw.get("phy_state") or "").upper(),
        "last_checked": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ---------------------------------------------------------------------------
# Watchlist CSV loading
# ---------------------------------------------------------------------------


def load_watchlist(filepath: str) -> List[str]:
    """Load DOT numbers from a watchlist CSV file.

    Expects a CSV with at least a 'dot_number' or 'DOT' column.
    """
    dot_numbers = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dot = row.get("dot_number") or row.get("DOT") or row.get("dot") or ""
                dot = dot.strip()
                if dot:
                    dot_numbers.append(dot)
    except FileNotFoundError:
        logger.error("Watchlist file not found: %s", filepath)
    except Exception as exc:
        logger.error("Error reading watchlist file: %s", exc)

    logger.info("Loaded %d carriers from watchlist: %s", len(dot_numbers), filepath)
    return dot_numbers


def query_watchlist_carriers(
    session: requests.Session,
    dot_numbers: List[str],
    app_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Query FMCSA API for specific DOT numbers from watchlist."""
    all_rows: List[Dict[str, Any]] = []
    headers = {}
    if app_token:
        headers["X-App-Token"] = app_token

    # Query in batches using SoQL IN clause
    batch_size = 50
    for i in range(0, len(dot_numbers), batch_size):
        batch = dot_numbers[i : i + batch_size]
        dot_list = ", ".join(f"'{d}'" for d in batch)
        params = {
            "$where": f"dot_number IN ({dot_list})",
            "$limit": str(len(batch)),
        }

        try:
            resp = session.get(
                SOCRATA_API_URL,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            rows = resp.json()
            if isinstance(rows, list):
                all_rows.extend(rows)
        except requests.RequestException as exc:
            logger.error("Error querying watchlist batch: %s", exc)

        time.sleep(0.3)

    return all_rows


# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

EMAIL_TEMPLATES = {
    "intro": {
        "subject": "Protect Your Fleet - Operating Authority Expiring Soon",
        "body": """Dear {carrier_name},

I'm reaching out because our records show that the operating authority
(MC-{mc_number}) for your company is set to expire on {insurance_expiry_date},
which is just {days_remaining} days from now.

An expired operating authority means your fleet of {fleet_size} vehicles
could be forced off the road, costing you revenue every single day.

We specialize in helping carriers like yours in {state} maintain continuous
coverage with competitive rates and fast turnaround. We can have a new
policy bound within 24-48 hours.

I'd love to schedule a quick 15-minute call to review your options.
You can reach me directly or reply to this email.

Best regards,
[Your Name]
[Your Company]
[Phone Number]

---
Carrier: {carrier_name}
DOT#: {dot_number} | MC#: {mc_number}
Authority Expires: {insurance_expiry_date} ({days_remaining} days remaining)
""",
    },
    "follow_up": {
        "subject": "Re: Your MC Authority Expires in {days_remaining} Days - Action Needed",
        "body": """Dear {carrier_name},

I wanted to follow up on my previous message regarding your expiring
operating authority (MC-{mc_number}). With only {days_remaining} days
remaining before your {insurance_expiry_date} expiration date, time is
running short.

I understand you're busy running your operations, so I'll keep this brief:

  - Your current authority expires: {insurance_expiry_date}
  - Days remaining: {days_remaining}
  - Fleet at risk: {fleet_size} power units

We've helped dozens of carriers in {state} avoid costly lapses. Our
process is simple:

  1. Quick 10-minute info call
  2. We shop multiple A-rated insurers on your behalf
  3. New policy bound in 24-48 hours - no gap in authority

Can we connect this week? Even a brief call could save you from a
compliance headache.

Best regards,
[Your Name]
[Your Company]
[Phone Number]

---
Carrier: {carrier_name}
DOT#: {dot_number} | MC#: {mc_number}
""",
    },
    "lapsed": {
        "subject": "Urgent: Your Operating Authority Has Lapsed - We Can Help",
        "body": """Dear {carrier_name},

Our records indicate that the operating authority (MC-{mc_number}) for
your company has lapsed or is now expired as of {insurance_expiry_date}.

This is a critical situation. Without active authority, your {fleet_size}
vehicles cannot legally operate, and you may face:

  - FMCSA enforcement actions and fines
  - Loss of broker/shipper contracts
  - Revenue loss for every day your fleet sits idle

The good news: we specialize in rapid authority reinstatement for carriers
in {state}. We've helped companies get back on the road in as little as
48 hours.

Here's what we need to get started:
  1. A quick call to review your current situation
  2. Basic company and fleet information
  3. We handle the rest - filing, insurance, compliance

Every day without authority is lost revenue. Let's fix this today.

Please call us immediately or reply to this email.

Urgently,
[Your Name]
[Your Company]
[Phone Number]

---
Carrier: {carrier_name}
DOT#: {dot_number} | MC#: {mc_number}
Authority Expired: {insurance_expiry_date} ({days_remaining} days ago)
""",
    },
}


def select_template(days_remaining: int) -> str:
    """Select the appropriate email template based on days remaining."""
    if days_remaining < 0:
        return "lapsed"
    elif days_remaining <= 14:
        return "follow_up"
    else:
        return "intro"


def render_email(template_key: str, carrier: Dict[str, Any]) -> Dict[str, str]:
    """Render an email template with carrier data."""
    template = EMAIL_TEMPLATES[template_key]
    fields = {
        "carrier_name": carrier.get("carrier_name", "Carrier"),
        "dot_number": carrier.get("dot_number", "N/A"),
        "mc_number": carrier.get("mc_number", "N/A"),
        "insurance_expiry_date": carrier.get("insurance_expiry_date", "N/A"),
        "days_remaining": str(abs(carrier.get("days_remaining", 0))),
        "fleet_size": carrier.get("fleet_size", "N/A"),
        "state": carrier.get("state", "N/A"),
        "phone": carrier.get("phone", "N/A"),
        "email": carrier.get("email", "N/A"),
    }
    return {
        "subject": template["subject"].format(**fields),
        "body": template["body"].format(**fields),
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_table_report(carriers: List[Dict[str, Any]]) -> str:
    """Generate a formatted table report."""
    try:
        from tabulate import tabulate

        headers = [
            "Carrier Name", "DOT#", "MC#", "Expiry Date",
            "Days Left", "Fleet", "Phone", "Email", "Last Checked",
        ]
        rows = []
        for c in carriers:
            rows.append([
                c["carrier_name"][:30],
                c["dot_number"],
                c["mc_number"],
                c["insurance_expiry_date"],
                c["days_remaining"],
                c["fleet_size"],
                c["phone"],
                c["email"][:25] if c["email"] else "",
                c["last_checked"][:10],
            ])
        return tabulate(rows, headers=headers, tablefmt="grid")
    except ImportError:
        # Fallback without tabulate
        lines = []
        sep = "-" * 140
        lines.append(sep)
        header = (
            f"{'Carrier Name':<30} {'DOT#':<12} {'MC#':<12} "
            f"{'Expiry':<12} {'Days':<6} {'Fleet':<6} "
            f"{'Phone':<16} {'Email':<25} {'Checked':<12}"
        )
        lines.append(header)
        lines.append(sep)
        for c in carriers:
            line = (
                f"{c['carrier_name'][:30]:<30} "
                f"{c['dot_number']:<12} "
                f"{c['mc_number']:<12} "
                f"{c['insurance_expiry_date']:<12} "
                f"{c['days_remaining']:<6} "
                f"{c['fleet_size']:<6} "
                f"{c['phone']:<16} "
                f"{(c['email'] or '')[:25]:<25} "
                f"{c['last_checked'][:10]:<12}"
            )
            lines.append(line)
        lines.append(sep)
        lines.append(f"\nTotal carriers: {len(carriers)}")
        return "\n".join(lines)


def generate_csv_report(carriers: List[Dict[str, Any]]) -> str:
    """Generate a CSV report string."""
    import io

    output = io.StringIO()
    fieldnames = [
        "carrier_name", "dot_number", "mc_number", "insurance_expiry_date",
        "days_remaining", "fleet_size", "phone", "email", "state", "last_checked",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(carriers)
    return output.getvalue()


def generate_json_report(carriers: List[Dict[str, Any]]) -> str:
    """Generate a JSON report string."""
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_carriers": len(carriers),
        "carriers": carriers,
    }
    return json.dumps(report, indent=2)


def write_email_files(
    carriers: List[Dict[str, Any]], output_dir: str
) -> List[str]:
    """Write individual email .txt files for each carrier.

    Returns list of file paths written.
    """
    email_dir = os.path.join(output_dir, "emails")
    os.makedirs(email_dir, exist_ok=True)
    written = []

    for carrier in carriers:
        template_key = select_template(carrier["days_remaining"])
        email = render_email(template_key, carrier)

        dot = carrier["dot_number"]
        safe_name = re.sub(r"[^\w\-]", "_", carrier["carrier_name"])[:40]
        filename = f"{safe_name}_DOT{dot}_{template_key}.txt"
        filepath = os.path.join(email_dir, filename)

        content = (
            f"To: {carrier['email'] or '[NO EMAIL ON FILE]'}\n"
            f"Subject: {email['subject']}\n"
            f"Template: {template_key}\n"
            f"{'=' * 60}\n\n"
            f"{email['body']}\n"
        )

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            written.append(filepath)
        except OSError as exc:
            logger.error("Failed to write email file %s: %s", filepath, exc)

    logger.info("Wrote %d email files to %s", len(written), email_dir)
    return written


def write_summary_report(
    carriers: List[Dict[str, Any]],
    output_dir: str,
    output_format: str,
    email_files: List[str],
) -> str:
    """Write the summary report to the output directory.

    Returns path to the summary file.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Main report
    ext = {"table": "txt", "csv": "csv", "json": "json"}[output_format]
    report_filename = f"expiry_report_{timestamp}.{ext}"
    report_path = os.path.join(output_dir, report_filename)

    if output_format == "table":
        content = generate_table_report(carriers)
    elif output_format == "csv":
        content = generate_csv_report(carriers)
    else:
        content = generate_json_report(carriers)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Report written to %s", report_path)

    # Summary metadata
    summary_path = os.path.join(output_dir, f"summary_{timestamp}.txt")
    urgent = sum(1 for c in carriers if 0 <= c["days_remaining"] <= 14)
    warning = sum(1 for c in carriers if 14 < c["days_remaining"] <= 30)
    upcoming = sum(1 for c in carriers if c["days_remaining"] > 30)
    lapsed = sum(1 for c in carriers if c["days_remaining"] < 0)

    states = {}
    for c in carriers:
        st = c["state"] or "Unknown"
        states[st] = states.get(st, 0) + 1

    summary_lines = [
        "=" * 60,
        "TRUCKING AUTHORITY EXPIRY - DAILY SUMMARY",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "=" * 60,
        "",
        f"Total carriers found:  {len(carriers)}",
        f"  LAPSED (expired):    {lapsed}",
        f"  URGENT (0-14 days):  {urgent}",
        f"  WARNING (15-30 days): {warning}",
        f"  UPCOMING (31+ days): {upcoming}",
        "",
        "Carriers by state:",
    ]
    for st, count in sorted(states.items(), key=lambda x: -x[1]):
        summary_lines.append(f"  {st}: {count}")

    summary_lines.extend([
        "",
        f"Report file: {report_path}",
        f"Email files generated: {len(email_files)}",
        "",
        "--- Top 10 Most Urgent ---",
    ])
    for c in carriers[:10]:
        status = "LAPSED" if c["days_remaining"] < 0 else f"{c['days_remaining']}d"
        summary_lines.append(
            f"  [{status:>7}] {c['carrier_name'][:35]:<35} "
            f"DOT:{c['dot_number']:<10} MC:{c['mc_number']:<10} "
            f"Ph:{c['phone'] or 'N/A'}"
        )

    summary_content = "\n".join(summary_lines) + "\n"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_content)
    logger.info("Summary written to %s", summary_path)

    return report_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trucking_authority_expiry_tracker",
        description=(
            "Generate a daily sales call list of trucking companies whose "
            "operating authority (MC number) is about to expire. Queries the "
            "FMCSA Socrata API and stores results in SQLite for history tracking."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --state TX --days-until-expiry 30\n"
            "  %(prog)s --output-format csv --include-emails\n"
            "  %(prog)s --carriers-file watchlist.csv --output-format json\n"
            "  %(prog)s --state CA --days-until-expiry 90 --include-emails\n"
        ),
    )
    parser.add_argument(
        "--state",
        metavar="XX",
        help="Two-letter state code to filter carriers (e.g., TX, CA, NY). "
             "Omit to search all states.",
    )
    parser.add_argument(
        "--days-until-expiry",
        type=int,
        default=60,
        metavar="N",
        help="Number of days to look ahead for expiring authority (default: 60).",
    )
    parser.add_argument(
        "--output-format",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format for the report: table (human-readable), csv, or "
             "json (default: table).",
    )
    parser.add_argument(
        "--carriers-file",
        metavar="FILE",
        help="Path to a watchlist CSV file with DOT numbers to track. "
             "CSV must have a 'dot_number' or 'DOT' column.",
    )
    parser.add_argument(
        "--include-emails",
        action="store_true",
        help="Generate personalized email template .txt files for each carrier "
             "(intro, follow-up, or lapsed based on urgency).",
    )
    parser.add_argument(
        "--app-token",
        metavar="TOKEN",
        help="Socrata application token for higher API rate limits. "
             "Register free at data.transportation.gov.",
    )
    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        metavar="PATH",
        help=f"Path to SQLite database for history tracking "
             f"(default: {DEFAULT_DB_PATH}).",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        metavar="DIR",
        help=f"Directory for output reports and email files "
             f"(default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug-level logging for troubleshooting.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point. Returns 0 on success, 1 on error."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    logger.info("=" * 60)
    logger.info("Trucking Authority Expiry Tracker")
    logger.info("=" * 60)
    logger.info("Expiry window: %d days", args.days_until_expiry)
    if args.state:
        logger.info("State filter: %s", args.state.upper())
    if args.carriers_file:
        logger.info("Watchlist file: %s", args.carriers_file)

    # Initialize database
    try:
        os.makedirs(os.path.dirname(args.db_path), exist_ok=True)
        conn = init_database(args.db_path)
        logger.info("Database initialized: %s", args.db_path)
    except sqlite3.Error as exc:
        logger.error("Failed to initialize database: %s", exc)
        return 1

    session = build_session()
    raw_rows: List[Dict[str, Any]] = []

    # Query API
    try:
        if args.carriers_file:
            dot_numbers = load_watchlist(args.carriers_file)
            if not dot_numbers:
                logger.error("No DOT numbers found in watchlist file")
                conn.close()
                return 1
            raw_rows = query_watchlist_carriers(
                session, dot_numbers, args.app_token
            )
        else:
            raw_rows = query_fmcsa_carriers(
                session,
                state=args.state,
                days_until_expiry=args.days_until_expiry,
                app_token=args.app_token,
            )
    except Exception as exc:
        logger.error("Unexpected error querying FMCSA API: %s", exc)
        conn.close()
        return 1

    if not raw_rows:
        logger.warning("No carriers found matching criteria.")
        print("\nNo carriers found with expiring authority in the specified window.")
        conn.close()
        return 0

    logger.info("Retrieved %d raw carrier records", len(raw_rows))

    # Normalize and filter
    carriers = [normalize_carrier(r) for r in raw_rows]

    # If using watchlist, filter to only those within expiry window
    if args.carriers_file:
        carriers = [
            c for c in carriers
            if c["days_remaining"] <= args.days_until_expiry
        ]

    # Sort by urgency (earliest expiry / most negative days first)
    carriers.sort(key=lambda c: c["days_remaining"])

    logger.info("Processed %d carriers after filtering", len(carriers))

    # Store in database
    try:
        for carrier in carriers:
            upsert_carrier(conn, carrier)
        conn.commit()
        logger.info("Updated %d carrier records in database", len(carriers))
    except sqlite3.Error as exc:
        logger.error("Database error: %s", exc)

    # Generate email files if requested
    email_files: List[str] = []
    if args.include_emails:
        email_files = write_email_files(carriers, args.output_dir)

    # Write reports
    try:
        report_path = write_summary_report(
            carriers, args.output_dir, args.output_format, email_files
        )
    except OSError as exc:
        logger.error("Failed to write reports: %s", exc)
        conn.close()
        return 1

    # Print report to stdout as well
    if args.output_format == "table":
        print("\n" + generate_table_report(carriers))
    elif args.output_format == "csv":
        print(generate_csv_report(carriers))
    else:
        print(generate_json_report(carriers))

    # Summary to stdout
    urgent = sum(1 for c in carriers if 0 <= c["days_remaining"] <= 14)
    lapsed = sum(1 for c in carriers if c["days_remaining"] < 0)
    print(f"\n--- {len(carriers)} carriers found ---")
    print(f"  Lapsed: {lapsed} | Urgent (0-14d): {urgent} | "
          f"Total: {len(carriers)}")
    print(f"  Report: {report_path}")
    if email_files:
        print(f"  Emails: {len(email_files)} files in {args.output_dir}/emails/")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
