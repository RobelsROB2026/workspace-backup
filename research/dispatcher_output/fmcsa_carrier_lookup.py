#!/usr/bin/env python3
"""
FMCSA New Carrier Authority Lookup

Queries the FMCSA Socrata API (data.transportation.gov) to find recently
authorized motor carriers. Filters by authorization date and outputs results
as CSV for lead generation and prospecting workflows.

Dataset: FMCSA Census — Active & Authorized Motor Carriers
Endpoint: https://data.transportation.gov/resource/az4b-hbig.json

Usage:
    # Fetch carriers authorized in the last 30 days (default), write to stdout
    python fmcsa_carrier_lookup.py

    # Fetch carriers authorized in the last 7 days, save to file
    python fmcsa_carrier_lookup.py --days 7 --output new_carriers.csv

    # Filter by state and increase result limit
    python fmcsa_carrier_lookup.py --state TX --limit 5000 --output texas_carriers.csv

    # Specify a fixed date range
    python fmcsa_carrier_lookup.py --since 2026-01-01 --output q1_carriers.csv
"""

import argparse
import csv
import logging
import sys
from datetime import datetime, timedelta

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

API_BASE = "https://data.transportation.gov/resource/az4b-hbig.json"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
DEFAULT_LIMIT = 1000
DEFAULT_DAYS = 30

CSV_COLUMNS = ["company_name", "dot_number", "mc_number", "phone", "state"]
CSV_HEADERS = ["Company Name", "DOT Number", "MC Number", "Phone", "State"]


def build_query_params(since_date, state=None, limit=DEFAULT_LIMIT, offset=0):
    """Build SoQL query parameters for the Socrata API."""
    since_str = since_date.strftime("%Y-%m-%dT00:00:00.000")
    where_clauses = [f"auth_grnt_dt > '{since_str}'"]
    if state:
        where_clauses.append(f"phy_state = '{state.upper()}'")

    return {
        "$where": " AND ".join(where_clauses),
        "$order": "auth_grnt_dt DESC",
        "$limit": limit,
        "$offset": offset,
    }


def fetch_carriers(since_date, state=None, limit=DEFAULT_LIMIT):
    """Fetch carrier records from the FMCSA Socrata API with pagination."""
    all_records = []
    offset = 0
    page_size = min(limit, 1000)

    while len(all_records) < limit:
        params = build_query_params(
            since_date, state=state, limit=page_size, offset=offset
        )
        logger.info(
            "Fetching records (offset=%d, page_size=%d)...", offset, page_size
        )

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.get(API_BASE, params=params, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                break
            except requests.ConnectionError as e:
                logger.warning("Connection error (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
                if attempt == MAX_RETRIES:
                    raise SystemExit(f"Failed to connect after {MAX_RETRIES} attempts: {e}")
            except requests.Timeout:
                logger.warning("Request timed out (attempt %d/%d)", attempt, MAX_RETRIES)
                if attempt == MAX_RETRIES:
                    raise SystemExit(f"Request timed out after {MAX_RETRIES} attempts")
            except requests.HTTPError as e:
                raise SystemExit(f"HTTP error from API: {e}")

        try:
            data = resp.json()
        except ValueError:
            raise SystemExit("Invalid JSON response from API")

        if not isinstance(data, list):
            raise SystemExit(f"Unexpected API response format: {type(data).__name__}")

        if not data:
            break

        all_records.extend(data)
        offset += len(data)

        if len(data) < page_size:
            break

    return all_records[:limit]


def normalize_record(record):
    """Extract and normalize fields from a raw API record."""
    phone_raw = record.get("telephone", "") or record.get("phone", "")
    phone = phone_raw.strip().replace("(", "").replace(")", "").replace(" ", "-")

    return {
        "company_name": (record.get("legal_name") or record.get("dba_name") or "").strip(),
        "dot_number": record.get("dot_number", "").strip(),
        "mc_number": record.get("mc_mx_ff_number", "").strip(),
        "phone": phone,
        "state": (record.get("phy_state") or "").strip(),
    }


def write_csv(records, output_file=None):
    """Write normalized records as CSV to a file or stdout."""
    if output_file:
        fh = open(output_file, "w", newline="")
    else:
        fh = sys.stdout

    try:
        writer = csv.writer(fh)
        writer.writerow(CSV_HEADERS)
        for rec in records:
            row = normalize_record(rec)
            writer.writerow([row[col] for col in CSV_COLUMNS])
    finally:
        if output_file:
            fh.close()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Query the FMCSA Socrata API for recently authorized motor carriers.",
        epilog=(
            "Examples:\n"
            "  %(prog)s --days 7 --output new_carriers.csv\n"
            "  %(prog)s --state TX --limit 5000\n"
            "  %(prog)s --since 2026-01-01 --output q1.csv\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"Look back N days from today (default: {DEFAULT_DAYS})",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Start date in YYYY-MM-DD format (overrides --days)",
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Filter by physical state abbreviation (e.g. TX, CA)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Maximum number of records to fetch (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path (default: stdout)",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()

    if args.since:
        try:
            since_date = datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            raise SystemExit(f"Invalid date format: {args.since} (expected YYYY-MM-DD)")
    else:
        since_date = datetime.now() - timedelta(days=args.days)

    logger.info(
        "Searching for carriers authorized since %s%s",
        since_date.strftime("%Y-%m-%d"),
        f" in {args.state.upper()}" if args.state else "",
    )

    records = fetch_carriers(since_date, state=args.state, limit=args.limit)
    logger.info("Retrieved %d carrier record(s)", len(records))

    if not records:
        logger.info("No carriers found matching criteria")
        return

    write_csv(records, output_file=args.output)

    if args.output:
        logger.info("Results written to %s", args.output)


if __name__ == "__main__":
    main()
