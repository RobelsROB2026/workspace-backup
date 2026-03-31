#!/usr/bin/env python3
"""Query the FMCSA Socrata API for newly authorized motor carriers.

Queries data.transportation.gov (dataset az4b-hbig) for carriers that received
new operating authority within the last 6 months. Supports filtering by state
and minimum fleet size, with output in CSV, JSON, or formatted table.

Usage examples:
    # Default: 50 results as a table
    python fmcsa_newly_authorized_carriers.py

    # Filter by state, output CSV
    python fmcsa_newly_authorized_carriers.py --state TX --output-format csv

    # Larger fleet carriers in JSON
    python fmcsa_newly_authorized_carriers.py --min-fleet-size 5 --limit 100 --output-format json

The Socrata API works without an app token but may throttle. Set the
SOCRATA_APP_TOKEN environment variable to avoid rate limits.
"""

import argparse
import csv
import io
import json
import logging
import os
import sys
from datetime import datetime, timedelta

import requests

API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace with state, min_fleet_size, limit, and output_format.
    """
    parser = argparse.ArgumentParser(
        description="Query FMCSA Socrata API for newly authorized motor carriers.",
    )
    parser.add_argument(
        "--state",
        help="Two-letter state abbreviation to filter by (e.g. TX, CA)",
    )
    parser.add_argument(
        "--min-fleet-size",
        type=int,
        default=1,
        help="Minimum total power units (default: 1)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of results to return (default: 50)",
    )
    parser.add_argument(
        "--output-format",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return parser.parse_args()


def build_query_params(state=None, min_fleet_size=1, limit=50):
    """Build SoQL query parameters for newly authorized carriers.

    Args:
        state: Optional two-letter state code to filter results.
        min_fleet_size: Minimum fleet size (totalPowerUnits) to include.
        limit: Maximum number of records to return.

    Returns:
        Dict of Socrata query parameters.
    """
    six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%dT00:00:00")

    where_clauses = [
        f"authGrantDate > '{six_months_ago}'",
        f"totalPowerUnits >= {min_fleet_size}",
    ]
    if state:
        where_clauses.append(f"upper(phyState) = '{state.upper()}'")

    params = {
        "$where": " AND ".join(where_clauses),
        "$order": "authGrantDate DESC",
        "$limit": limit,
    }

    app_token = os.environ.get("SOCRATA_APP_TOKEN")
    if app_token:
        params["$$app_token"] = app_token

    return params


def fetch_carriers(params):
    """Fetch carrier records from the FMCSA Socrata API.

    Args:
        params: Dict of query parameters for the API request.

    Returns:
        List of carrier record dicts from the API.

    Raises:
        SystemExit: On HTTP errors or connection failures.
    """
    logger.info("Querying FMCSA API at %s", API_URL)
    try:
        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error: %s", e)
        if resp.status_code == 403:
            logger.error("Hint: set SOCRATA_APP_TOKEN env var to avoid rate limits.")
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error: %s", e)
        sys.exit(1)
    except requests.exceptions.Timeout:
        logger.error("Request timed out after 30 seconds.")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        logger.error("Request failed: %s", e)
        sys.exit(1)

    try:
        data = resp.json()
    except ValueError:
        logger.error("Failed to parse JSON response.")
        sys.exit(1)

    if not isinstance(data, list):
        logger.error("Unexpected API response format.")
        sys.exit(1)

    logger.info("Received %d records from API.", len(data))
    return data


def extract_carrier(record):
    """Extract and normalize relevant fields from a raw API record.

    Args:
        record: Dict from the Socrata API response.

    Returns:
        Dict with keys: company_name, dot_number, mc_number, phone, address,
        state, authorization_date.
    """
    def safe(key):
        return (record.get(key) or "").strip()

    raw_date = safe("authGrantDate")
    auth_date = ""
    if raw_date:
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            auth_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            auth_date = raw_date[:10]

    address_parts = filter(None, [safe("phyStreet"), safe("phyCity")])
    address = ", ".join(address_parts)

    return {
        "company_name": safe("legalName") or safe("dbaName"),
        "dot_number": safe("dotNumber"),
        "mc_number": safe("mcNumber"),
        "phone": safe("phone"),
        "address": address,
        "state": safe("phyState"),
        "authorization_date": auth_date,
    }


FIELDS = [
    "company_name",
    "dot_number",
    "mc_number",
    "phone",
    "address",
    "state",
    "authorization_date",
]

HEADERS = {
    "company_name": "Company Name",
    "dot_number": "DOT #",
    "mc_number": "MC #",
    "phone": "Phone",
    "address": "Address",
    "state": "State",
    "authorization_date": "Auth Date",
}


def output_table(carriers):
    """Print carriers as a formatted ASCII table.

    Args:
        carriers: List of carrier dicts.
    """
    # Calculate column widths
    widths = {f: len(HEADERS[f]) for f in FIELDS}
    for c in carriers:
        for f in FIELDS:
            widths[f] = max(widths[f], len(str(c.get(f, ""))))

    header = " | ".join(HEADERS[f].ljust(widths[f]) for f in FIELDS)
    separator = "-+-".join("-" * widths[f] for f in FIELDS)

    print(header)
    print(separator)
    for c in carriers:
        row = " | ".join(str(c.get(f, "")).ljust(widths[f]) for f in FIELDS)
        print(row)


def output_csv(carriers):
    """Print carriers as CSV to stdout.

    Args:
        carriers: List of carrier dicts.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(carriers)
    print(buf.getvalue(), end="")


def output_json(carriers):
    """Print carriers as formatted JSON to stdout.

    Args:
        carriers: List of carrier dicts.
    """
    print(json.dumps(carriers, indent=2))


def main():
    """Main entry point: parse args, query API, and display results."""
    args = parse_args()

    params = build_query_params(
        state=args.state,
        min_fleet_size=args.min_fleet_size,
        limit=args.limit,
    )

    records = fetch_carriers(params)

    if not records:
        logger.info("No carriers matched the given filters.")
        sys.exit(0)

    carriers = [extract_carrier(r) for r in records]
    logger.info("Displaying %d carriers.", len(carriers))

    formatters = {
        "table": output_table,
        "csv": output_csv,
        "json": output_json,
    }
    formatters[args.output_format](carriers)


if __name__ == "__main__":
    main()
