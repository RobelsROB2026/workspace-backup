#!/usr/bin/env python3
"""Query the FMCSA Socrata API for newly authorized motor carriers.

Queries data.transportation.gov (dataset az4b-hbig) for carriers that received
new operating authority in the last 6 months. Results are written to a CSV file.

Usage examples:
    # Basic query with API key
    python fmcsa_new_authority_carriers.py --api-key YOUR_APP_TOKEN

    # Filter by state and minimum fleet size
    python fmcsa_new_authority_carriers.py --api-key YOUR_APP_TOKEN --state-filter TX --min-fleet-size 5

    # Custom output file
    python fmcsa_new_authority_carriers.py --api-key YOUR_APP_TOKEN --output-csv results.csv

The Socrata API app token is optional but recommended to avoid throttling.
Register for one at https://data.transportation.gov/profile/edit/developer_settings
"""

import argparse
import csv
import sys
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json


API_BASE = "https://data.transportation.gov/resource/az4b-hbig.json"
DEFAULT_OUTPUT = "fmcsa_new_authority_carriers.csv"
PAGE_SIZE = 1000


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Query FMCSA Socrata API for newly authorized motor carriers."
    )
    parser.add_argument(
        "--api-key",
        help="Socrata app token (optional, avoids throttling)",
    )
    parser.add_argument(
        "--state-filter",
        help="Two-letter state abbreviation to filter by (e.g. TX, CA)",
    )
    parser.add_argument(
        "--min-fleet-size",
        type=int,
        default=0,
        help="Minimum fleet size (total power units) to include (default: 0)",
    )
    parser.add_argument(
        "--output-csv",
        default=DEFAULT_OUTPUT,
        help=f"Output CSV file path (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def build_query(state_filter=None, offset=0):
    """Build SoQL query parameters for newly authorized carriers.

    Args:
        state_filter: Optional two-letter state code.
        offset: Pagination offset.

    Returns:
        Dict of query parameters for the Socrata API.
    """
    six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%dT00:00:00")

    where_clauses = [
        f"authGrantDate > '{six_months_ago}'",
    ]
    if state_filter:
        where_clauses.append(f"upper(phyState) = '{state_filter.upper()}'")

    params = {
        "$where": " AND ".join(where_clauses),
        "$order": "authGrantDate DESC",
        "$limit": str(PAGE_SIZE),
        "$offset": str(offset),
    }
    return params


def fetch_page(params, api_key=None):
    """Fetch a single page of results from the Socrata API.

    Args:
        params: Dict of query parameters.
        api_key: Optional Socrata app token.

    Returns:
        List of record dicts.

    Raises:
        SystemExit: On unrecoverable HTTP or connection errors.
    """
    url = f"{API_BASE}?{urlencode(params)}"
    req = Request(url)
    if api_key:
        req.add_header("X-App-Token", api_key)

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data
    except HTTPError as e:
        print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
        if e.code == 403:
            print("Hint: provide --api-key to avoid rate limits.", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Failed to parse API response: {e}", file=sys.stderr)
        sys.exit(1)


def extract_carrier(record):
    """Extract relevant fields from a raw API record.

    Args:
        record: Dict from the Socrata API.

    Returns:
        Dict with normalized carrier fields.
    """
    def safe(key):
        return (record.get(key) or "").strip()

    # Fleet size is total power units
    try:
        fleet_size = int(record.get("totalPowerUnits", 0) or 0)
    except (ValueError, TypeError):
        fleet_size = 0

    # Parse the authority grant date to a readable format
    raw_date = safe("authGrantDate")
    grant_date = ""
    if raw_date:
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            grant_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            grant_date = raw_date[:10]

    return {
        "company_name": safe("legalName") or safe("dbaName"),
        "dot_number": safe("dotNumber"),
        "mc_number": safe("mcNumber"),
        "phone": safe("phone"),
        "state": safe("phyState"),
        "authority_grant_date": grant_date,
        "fleet_size": fleet_size,
    }


def main():
    """Main entry point: query API, filter, and write CSV."""
    args = parse_args()

    carriers = []
    offset = 0

    print("Querying FMCSA Socrata API for newly authorized carriers...")
    while True:
        params = build_query(state_filter=args.state_filter, offset=offset)
        page = fetch_page(params, api_key=args.api_key)

        if not page:
            break

        for record in page:
            carrier = extract_carrier(record)
            if carrier["fleet_size"] >= args.min_fleet_size:
                carriers.append(carrier)

        print(f"  Fetched {offset + len(page)} records so far...")
        offset += PAGE_SIZE

        if len(page) < PAGE_SIZE:
            break

    if not carriers:
        print("No carriers matched the given filters.")
        sys.exit(0)

    # Write CSV
    fieldnames = [
        "company_name",
        "dot_number",
        "mc_number",
        "phone",
        "state",
        "authority_grant_date",
        "fleet_size",
    ]
    try:
        with open(args.output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(carriers)
    except OSError as e:
        print(f"Failed to write CSV: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {len(carriers)} carriers to {args.output_csv}")


if __name__ == "__main__":
    main()
