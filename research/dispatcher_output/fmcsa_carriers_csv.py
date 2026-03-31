#!/usr/bin/env python3
"""Query the FMCSA Socrata API for newly authorized motor carriers.

Fetches carrier records from data.transportation.gov (dataset az4b-hbig)
filtered by authorization date, and writes results to a CSV file.

Usage:
    python fmcsa_carriers_csv.py --api-key YOUR_KEY --output-csv carriers.csv --min-authorized-date 2024-01-01

The Socrata API app token is optional but recommended to avoid throttling.
Without it, requests are subject to stricter rate limits.
"""

import argparse
import csv
import sys
from datetime import datetime

import requests

API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"

FIELD_MAP = {
    "legal_name": "company_name",
    "dot_number": "dot_number",
    "mc_number": "mc_number",
    "phone": "phone",
    "phy_state": "state",
    "auth_granted_date": "authorization_date",
    "total_power_units": "fleet_size",
}

CSV_HEADERS = [
    "company_name",
    "dot_number",
    "mc_number",
    "phone",
    "state",
    "authorization_date",
    "fleet_size",
]


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch newly authorized motor carriers from the FMCSA Socrata API."
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Socrata app token (optional but recommended to avoid throttling).",
    )
    parser.add_argument(
        "--output-csv",
        default="fmcsa_carriers.csv",
        help="Path for the output CSV file (default: fmcsa_carriers.csv).",
    )
    parser.add_argument(
        "--min-authorized-date",
        default=None,
        help="Only include carriers authorized on or after this date (YYYY-MM-DD).",
    )
    return parser.parse_args()


def validate_date(date_str):
    """Validate and return a date string in YYYY-MM-DD format.

    Raises:
        SystemExit: If the date string is not valid ISO format.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        sys.exit(f"Error: invalid date format '{date_str}'. Expected YYYY-MM-DD.")


def fetch_carriers(api_key=None, min_date=None, limit=5000):
    """Fetch authorized carrier records from the FMCSA Socrata API.

    Args:
        api_key: Optional Socrata app token.
        min_date: Optional minimum authorization date (YYYY-MM-DD).
        limit: Maximum number of records to fetch per request.

    Returns:
        List of carrier record dicts from the API.

    Raises:
        SystemExit: On network errors or non-200 API responses.
    """
    headers = {}
    if api_key:
        headers["X-App-Token"] = api_key

    params = {
        "$limit": limit,
        "$order": "auth_granted_date DESC",
    }

    where_clauses = ["act_stat = 'A'"]
    if min_date:
        where_clauses.append(f"auth_granted_date >= '{min_date}T00:00:00.000'")

    params["$where"] = " AND ".join(where_clauses)

    try:
        resp = requests.get(API_URL, headers=headers, params=params, timeout=60)
    except requests.ConnectionError:
        sys.exit("Error: could not connect to data.transportation.gov.")
    except requests.Timeout:
        sys.exit("Error: request to FMCSA API timed out.")
    except requests.RequestException as exc:
        sys.exit(f"Error: network request failed: {exc}")

    if resp.status_code != 200:
        sys.exit(
            f"Error: API returned HTTP {resp.status_code}.\n"
            f"Response: {resp.text[:500]}"
        )

    try:
        data = resp.json()
    except ValueError:
        sys.exit("Error: API returned non-JSON response.")

    if not isinstance(data, list):
        sys.exit("Error: unexpected API response format (expected a JSON array).")

    return data


def extract_record(raw):
    """Extract relevant fields from a raw API record.

    Args:
        raw: A single carrier record dict from the API.

    Returns:
        Dict with normalized field names matching CSV_HEADERS.
    """
    record = {}
    for api_field, csv_field in FIELD_MAP.items():
        value = raw.get(api_field, "")
        if csv_field == "authorization_date" and value:
            value = value[:10]  # trim timestamp to YYYY-MM-DD
        record[csv_field] = value
    return record


def write_csv(records, output_path):
    """Write carrier records to a CSV file.

    Args:
        records: List of normalized carrier record dicts.
        output_path: File path for the output CSV.
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(records)


def main():
    """Entry point: parse args, fetch data, write CSV."""
    args = parse_args()

    min_date = None
    if args.min_authorized_date:
        min_date = validate_date(args.min_authorized_date)

    print(f"Fetching authorized carriers from FMCSA API...")
    raw_records = fetch_carriers(api_key=args.api_key, min_date=min_date)

    if not raw_records:
        print("No carrier records found matching the criteria.")
        sys.exit(0)

    records = [extract_record(r) for r in raw_records]

    write_csv(records, args.output_csv)
    print(f"Wrote {len(records)} carriers to {args.output_csv}")


if __name__ == "__main__":
    main()
