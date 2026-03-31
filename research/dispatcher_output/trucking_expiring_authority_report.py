#!/usr/bin/env python3
"""
Expiring Operating Authority Report Generator

Queries FMCSA SAFER (safer.fmcsa.dot.gov) and the Socrata Open Data API
(data.transportation.gov) to identify motor carriers whose MC/PC operating
authority expires within a configurable window (default 60 days). Produces
a sales-call-ready CSV report.

Data sources
------------
1. Socrata / data.transportation.gov  – FMCSA Census dataset (primary).
   Provides structured, SoQL-queryable carrier records including MCS-150
   dates, authority status, fleet size, and contact info.
2. FMCSA SAFER Company Snapshot – HTML scraping fallback for supplemental
   detail (insurance status, phone) when the Socrata record is incomplete.

Usage
-----
    # Default: carriers expiring in 60 days, all states, CSV to stdout
    python trucking_expiring_authority_report.py

    # Filter to Texas & Oklahoma, save to file
    python trucking_expiring_authority_report.py --states TX OK --output leads.csv

    # Narrow to property carriers, 30-day window, verbose logging
    python trucking_expiring_authority_report.py --carrier-type property --days 30 -v

    # Use a Socrata app token for higher rate limits
    python trucking_expiring_authority_report.py --app-token YOUR_TOKEN

Requirements
------------
    pip install requests beautifulsoup4
"""

import argparse
import csv
import io
import logging
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOCRATA_BASE = "https://data.transportation.gov/resource"
# FMCSA Motor Carrier Census – Socrata dataset identifier
CENSUS_DATASET_ID = "az4n-8mr4"

SAFER_SNAPSHOT_URL = "https://safer.fmcsa.dot.gov/CompanySnapshot.aspx"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5
# Socrata returns max 50 000 rows per request; we page in chunks.
SOCRATA_PAGE_SIZE = 1000

CARRIER_TYPE_MAP = {
    "property": "A",   # authorized for property (freight)
    "passenger": "B",   # authorized for passenger
    "household": "C",   # household goods
}

CSV_COLUMNS = [
    "Company Name",
    "DOT#",
    "MC#",
    "Expiration Date",
    "State",
    "Phone",
    "Email",
    "Fleet Size",
    "Insurance Status",
]


# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

def _session() -> requests.Session:
    """Build a requests session with retry adapter."""
    sess = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.packages.urllib3.util.retry.Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
    )
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    sess.headers.update({
        "User-Agent": "ExpiringAuthorityReport/1.0 (sales-research-tool)",
    })
    return sess


def socrata_get(
    session: requests.Session,
    dataset_id: str,
    params: Dict[str, str],
    app_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Execute a paginated Socrata SoQL query and return all rows."""
    url = f"{SOCRATA_BASE}/{dataset_id}.json"
    headers = {}
    if app_token:
        headers["X-App-Token"] = app_token

    all_rows: List[Dict[str, Any]] = []
    offset = 0
    limit = int(params.get("$limit", SOCRATA_PAGE_SIZE))

    while True:
        page_params = {**params, "$limit": str(limit), "$offset": str(offset)}
        logger.debug("Socrata request: %s  params=%s", url, page_params)
        try:
            resp = session.get(
                url, params=page_params, headers=headers, timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error querying Socrata: %s", exc)
            break
        except requests.exceptions.Timeout:
            logger.error("Timeout querying Socrata (limit=%ss)", REQUEST_TIMEOUT)
            break
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error from Socrata: %s", exc)
            break

        rows = resp.json()
        if not isinstance(rows, list):
            logger.error("Unexpected Socrata response type: %s", type(rows))
            break

        all_rows.extend(rows)
        if len(rows) < limit:
            break
        offset += limit
        time.sleep(0.25)  # politeness

    return all_rows


# ---------------------------------------------------------------------------
# SAFER HTML scraper (supplemental detail)
# ---------------------------------------------------------------------------

def scrape_safer_snapshot(
    session: requests.Session, dot_number: str,
) -> Dict[str, str]:
    """Scrape the SAFER Company Snapshot page for a single DOT number.

    Returns a dict with keys like 'phone', 'insurance_status', 'mc_number',
    'email'.  Missing fields are omitted rather than set to empty strings.
    """
    result: Dict[str, str] = {}
    try:
        resp = session.get(
            SAFER_SNAPSHOT_URL,
            params={"QRY": "1", "DOT": dot_number},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.debug("SAFER fetch failed for DOT %s: %s", dot_number, exc)
        return result

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Phone
    phone_match = re.search(r"Phone\s*:\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", text)
    if phone_match:
        digits = re.sub(r"\D", "", phone_match.group())[-10:]
        result["phone"] = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

    # MC / MX number
    mc_match = re.search(r"MC/MX/FF Number[^:]*:\s*(MC-?\d+)", text, re.IGNORECASE)
    if mc_match:
        result["mc_number"] = mc_match.group(1).replace("-", "")

    # Insurance – look for BIPD/cargo filing status
    if re.search(r"BIPD\s+(Insurance|Filing)\s*.*?(Active|Yes)", text, re.IGNORECASE):
        result["insurance_status"] = "Active"
    elif re.search(r"BIPD\s+(Insurance|Filing)", text, re.IGNORECASE):
        result["insurance_status"] = "Lapsed/Pending"

    return result


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def build_socrata_query(
    days: int,
    states: Optional[List[str]],
    carrier_type: Optional[str],
) -> Dict[str, str]:
    """Build a SoQL parameter dict for the FMCSA census dataset.

    Targets carriers whose MCS-150 form date (which reflects authority
    renewal status) falls within the expiration window.  The Socrata
    dataset exposes ``mcs_150_form_date`` and ``oic_state`` among other
    columns useful for filtering.
    """
    today = datetime.utcnow().date()
    cutoff = today + timedelta(days=days)

    # Build $where clause pieces
    where_clauses = [
        # Authority still nominally active or pending revocation
        "oper_auth_status = 'A'",
        # MCS-150 date acts as proxy for renewal/expiration tracking
        f"mcs_150_form_date >= '{today.isoformat()}'",
        f"mcs_150_form_date <= '{cutoff.isoformat()}'",
    ]

    if states:
        state_list = ", ".join(f"'{s.upper()}'" for s in states)
        where_clauses.append(f"phy_state IN ({state_list})")

    if carrier_type and carrier_type.lower() in CARRIER_TYPE_MAP:
        code = CARRIER_TYPE_MAP[carrier_type.lower()]
        where_clauses.append(f"carrier_operation LIKE '%{code}%'")

    params = {
        "$where": " AND ".join(where_clauses),
        "$select": (
            "legal_name, dot_number, mc_mx_ff_number, mcs_150_form_date, "
            "phy_state, telephone, email_address, total_power_units, "
            "total_drivers, oper_auth_status"
        ),
        "$order": "mcs_150_form_date ASC",
        "$limit": str(SOCRATA_PAGE_SIZE),
    }
    return params


def normalize_row(raw: Dict[str, Any]) -> Dict[str, str]:
    """Map a raw Socrata row to the output CSV schema."""
    # Expiration date
    exp_raw = raw.get("mcs_150_form_date", "")
    exp_date = ""
    if exp_raw:
        try:
            exp_date = datetime.fromisoformat(
                exp_raw.replace("Z", "+00:00")
            ).strftime("%Y-%m-%d")
        except ValueError:
            exp_date = exp_raw[:10]

    # Fleet size = power units (trucks) or driver count as fallback
    fleet = raw.get("total_power_units", "") or raw.get("total_drivers", "")

    # Phone formatting
    phone_raw = raw.get("telephone", "") or ""
    phone = ""
    if phone_raw:
        digits = re.sub(r"\D", "", str(phone_raw))[-10:]
        if len(digits) == 10:
            phone = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        else:
            phone = str(phone_raw)

    mc_raw = raw.get("mc_mx_ff_number", "") or ""

    return {
        "Company Name": (raw.get("legal_name") or "").strip().title(),
        "DOT#": str(raw.get("dot_number", "")),
        "MC#": mc_raw,
        "Expiration Date": exp_date,
        "State": (raw.get("phy_state") or "").upper(),
        "Phone": phone,
        "Email": (raw.get("email_address") or "").lower(),
        "Fleet Size": str(fleet),
        "Insurance Status": "",  # filled by SAFER if --enrich
    }


def enrich_from_safer(
    session: requests.Session,
    rows: List[Dict[str, str]],
    max_lookups: int = 50,
) -> None:
    """Supplement rows with SAFER HTML data (insurance, phone, MC#).

    Mutates rows in place.  Limits scraping to ``max_lookups`` to avoid
    hammering the SAFER server.
    """
    count = 0
    for row in rows:
        if count >= max_lookups:
            logger.info(
                "Reached SAFER lookup limit (%d); remaining rows unenriched.",
                max_lookups,
            )
            break
        dot = row.get("DOT#", "")
        if not dot:
            continue

        detail = scrape_safer_snapshot(session, dot)
        count += 1

        if not row["Phone"] and detail.get("phone"):
            row["Phone"] = detail["phone"]
        if not row["MC#"] and detail.get("mc_number"):
            row["MC#"] = detail["mc_number"]
        if detail.get("insurance_status"):
            row["Insurance Status"] = detail["insurance_status"]

        time.sleep(1)  # be polite to SAFER


def write_csv(rows: List[Dict[str, str]], dest: Optional[str]) -> None:
    """Write rows to a CSV file or stdout."""
    if dest:
        fh = open(dest, "w", newline="", encoding="utf-8")
    else:
        fh = io.StringIO()

    writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

    if dest:
        fh.close()
        logger.info("Wrote %d rows to %s", len(rows), dest)
    else:
        # Print to stdout
        print(fh.getvalue(), end="")
        fh.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser with full --help documentation."""
    parser = argparse.ArgumentParser(
        prog="trucking_expiring_authority_report",
        description=(
            "Generate a sales call list of motor carriers whose MC/PC "
            "operating authority expires within a configurable window.\n\n"
            "Data is pulled from the FMCSA Census dataset on "
            "data.transportation.gov (Socrata API) and optionally enriched "
            "with detail from the SAFER Company Snapshot at "
            "safer.fmcsa.dot.gov."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --days 30 --states TX OK --output leads.csv\n"
            "  %(prog)s --carrier-type property --enrich --max-safer 25\n"
            "  %(prog)s --app-token $SOCRATA_TOKEN -v\n"
        ),
    )
    parser.add_argument(
        "--days", type=int, default=60,
        help="Look-ahead window in days for expiring authority (default: 60).",
    )
    parser.add_argument(
        "--states", nargs="+", metavar="ST",
        help="Two-letter state codes to filter by (e.g., TX CA NY).",
    )
    parser.add_argument(
        "--carrier-type",
        choices=["property", "passenger", "household"],
        help="Filter by carrier operation type.",
    )
    parser.add_argument(
        "--output", "-o", metavar="FILE",
        help="Path for the output CSV. Omit to print to stdout.",
    )
    parser.add_argument(
        "--app-token", metavar="TOKEN",
        help=(
            "Socrata application token for higher rate limits. "
            "Register at data.transportation.gov for a free token."
        ),
    )
    parser.add_argument(
        "--enrich", action="store_true",
        help="Scrape SAFER for supplemental detail (insurance, phone, MC#).",
    )
    parser.add_argument(
        "--max-safer", type=int, default=50, metavar="N",
        help="Max SAFER lookups when --enrich is used (default: 50).",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug-level logging.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point. Returns 0 on success, 1 on failure."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(
        "Searching for carriers with authority expiring within %d days", args.days,
    )
    if args.states:
        logger.info("State filter: %s", ", ".join(s.upper() for s in args.states))
    if args.carrier_type:
        logger.info("Carrier type filter: %s", args.carrier_type)

    session = _session()

    # 1. Query Socrata
    params = build_socrata_query(args.days, args.states, args.carrier_type)
    logger.debug("SoQL params: %s", params)

    raw_rows = socrata_get(session, CENSUS_DATASET_ID, params, args.app_token)
    if not raw_rows:
        logger.warning("No carriers found matching the criteria.")
        return 0

    logger.info("Socrata returned %d carrier records.", len(raw_rows))

    # 2. Normalize
    rows = [normalize_row(r) for r in raw_rows]

    # 3. Optional SAFER enrichment
    if args.enrich:
        logger.info("Enriching up to %d records from SAFER...", args.max_safer)
        enrich_from_safer(session, rows, max_lookups=args.max_safer)

    # 4. Output
    write_csv(rows, args.output)

    if args.output:
        print(f"Report saved: {args.output}  ({len(rows)} carriers)")
    else:
        logger.info("Listed %d carriers.", len(rows))

    return 0


if __name__ == "__main__":
    sys.exit(main())
