#!/usr/bin/env python3
"""Query the FMCSA Socrata API for newly authorized motor carriers.

Uses the Socrata Open Data API at data.transportation.gov to retrieve
carrier records filtered by authorization status and date range.
Results are written to a CSV file with key carrier details.

Usage:
    python fmcsa_new_carriers_query.py --api-key YOUR_KEY --output-file results.csv
    python fmcsa_new_carriers_query.py --api-key YOUR_KEY --state TX --min-dates 60 --output-file results.csv
"""

import argparse
import csv
import logging
import sys
from datetime import datetime, timedelta

import requests

API_BASE_URL = "https://data.transportation.gov/resource/az4b-hbig.json"

CSV_FIELDS = [
    "company_name",
    "dot_number",
    "mc_number",
    "phone_number",
    "state",
    "authorization_date",
    "fleet_size",
]

# Mapping from our CSV field names to Socrata dataset column names.
FIELD_MAP = {
    "company_name": "legal_name",
    "dot_number": "dot_number",
    "mc_number": "mc_mx_ff_number",
    "phone_number": "phone",
    "state": "phy_state",
    "authorization_date": "act_stat_dt",
    "fleet_size": "total_pwr_units",
}

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.WARNING,
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Query FMCSA Socrata API for newly authorized motor carriers."
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="Socrata application token (passed as $$app_token).",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="Optional two-letter state code to filter results (e.g. TX, CA).",
    )
    parser.add_argument(
        "--min-dates",
        type=int,
        default=30,
        help="Look-back window in days for authorization date (default: 30).",
    )
    parser.add_argument(
        "--output-file",
        required=True,
        help="Path to the output CSV file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Maximum number of records to retrieve (default: 5000).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def build_query_params(state, min_date, limit):
    """Build Socrata SoQL query parameters.

    Args:
        state: Optional two-letter state abbreviation.
        min_date: Earliest authorization date as a datetime object.
        limit: Maximum number of rows to return.

    Returns:
        Dictionary of query parameters for the Socrata API.
    """
    date_str = min_date.strftime("%Y-%m-%dT00:00:00.000")

    where_clauses = [
        "act_stat = 'A'",
        f"act_stat_dt >= '{date_str}'",
    ]

    if state:
        where_clauses.append(f"phy_state = '{state.upper()}'")

    params = {
        "$where": " AND ".join(where_clauses),
        "$order": "act_stat_dt DESC",
        "$limit": limit,
    }

    logger.debug("Query params: %s", params)
    return params


def fetch_carriers(api_key, params):
    """Fetch carrier records from the FMCSA Socrata API.

    Args:
        api_key: Socrata application token.
        params: Dictionary of SoQL query parameters.

    Returns:
        List of carrier record dictionaries.

    Raises:
        requests.HTTPError: If the API returns a non-2xx status.
        requests.ConnectionError: On network failure.
    """
    headers = {"X-App-Token": api_key}

    logger.debug("Requesting %s", API_BASE_URL)
    response = requests.get(API_BASE_URL, params=params, headers=headers, timeout=60)
    response.raise_for_status()

    records = response.json()
    logger.debug("Received %d records", len(records))
    return records


def extract_carrier_row(record):
    """Extract relevant fields from a single API record.

    Args:
        record: Dictionary representing one Socrata row.

    Returns:
        Dictionary with normalised field names and values.
    """
    row = {}
    for csv_field, api_field in FIELD_MAP.items():
        value = record.get(api_field, "")
        if csv_field == "authorization_date" and value:
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                value = dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                pass
        row[csv_field] = value
    return row


def write_csv(rows, output_path):
    """Write carrier rows to a CSV file.

    Args:
        rows: List of dictionaries with CSV_FIELDS keys.
        output_path: Destination file path.
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Wrote %d rows to %s", len(rows), output_path)


def main():
    """Entry point: parse args, query API, write CSV."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    min_date = datetime.now() - timedelta(days=args.min_dates)
    logger.info(
        "Querying carriers authorized since %s", min_date.strftime("%Y-%m-%d")
    )

    params = build_query_params(args.state, min_date, args.limit)

    try:
        records = fetch_carriers(args.api_key, params)
    except requests.ConnectionError:
        logger.error("Network error: could not reach %s", API_BASE_URL)
        sys.exit(1)
    except requests.HTTPError as exc:
        logger.error("API error: %s", exc.response.status_code)
        logger.debug("Response body: %s", exc.response.text)
        sys.exit(1)
    except requests.RequestException as exc:
        logger.error("Request failed: %s", exc)
        sys.exit(1)

    if not records:
        print("No newly authorized carriers found for the given filters.")
        sys.exit(0)

    rows = [extract_carrier_row(r) for r in records]

    try:
        write_csv(rows, args.output_file)
    except OSError as exc:
        logger.error("Failed to write CSV: %s", exc)
        sys.exit(1)

    print(f"Exported {len(rows)} carriers to {args.output_file}")


if __name__ == "__main__":
    main()
