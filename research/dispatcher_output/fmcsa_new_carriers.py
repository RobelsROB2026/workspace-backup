#!/usr/bin/env python3
"""
FMCSA New Carrier Query Tool

Queries the FMCSA Socrata API at data.transportation.gov/resource/az4b-hbig.json
for newly authorized motor carriers and exports results to CSV.

Usage:
    python fmcsa_new_carriers.py
    python fmcsa_new_carriers.py --output-file carriers.csv --min-dot-number 4000000
    python fmcsa_new_carriers.py --debug --limit 500
"""

import argparse
import csv
import json
import logging
import sys

import requests

DEFAULT_API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"
DEFAULT_OUTPUT = "fmcsa_new_carriers.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments for API URL, output file, and filters."""
    parser = argparse.ArgumentParser(
        description="Query FMCSA Socrata API for newly authorized motor carriers."
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Socrata API endpoint (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--output-file",
        default=DEFAULT_OUTPUT,
        help=f"Output CSV file path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--min-dot-number",
        type=int,
        default=None,
        help="Only include carriers with DOT number >= this value",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Max number of records to fetch per request (default: 1000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def fetch_carriers(api_url, limit=1000, min_dot_number=None):
    """Fetch newly authorized carrier records from the FMCSA Socrata API.

    Builds a SoQL query filtering on authorization status and optional
    minimum DOT number, then returns parsed JSON records.

    Args:
        api_url: Socrata API endpoint URL.
        limit: Maximum records to retrieve.
        min_dot_number: Optional minimum DOT number filter.

    Returns:
        List of carrier dictionaries, or empty list on failure.
    """
    params = {
        "$limit": limit,
        "$order": "dot_number DESC",
    }

    where_clauses = ["new_authority = 'Y'"]
    if min_dot_number is not None:
        where_clauses.append(f"dot_number >= '{min_dot_number}'")
    params["$where"] = " AND ".join(where_clauses)

    logger.debug("Request URL: %s", api_url)
    logger.debug("Request params: %s", params)

    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
    except requests.ConnectionError:
        logger.error("Could not connect to %s — check your network.", api_url)
        return []
    except requests.Timeout:
        logger.error("Request to %s timed out.", api_url)
        return []
    except requests.RequestException as exc:
        logger.error("HTTP request failed: %s", exc)
        return []

    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to parse JSON response: %s", exc)
        logger.debug("Raw response text: %.500s", response.text)
        return []

    if not isinstance(data, list):
        logger.error(
            "Unexpected response format (expected list, got %s)",
            type(data).__name__,
        )
        return []

    logger.info("Fetched %d carrier record(s)", len(data))
    return data


def extract_fields(record):
    """Extract the desired fields from a single carrier record.

    Maps raw API field names to the output CSV column names.

    Args:
        record: Dictionary representing one carrier from the API.

    Returns:
        Dictionary with keys: company_name, dot_number, mc_number, phone, state.
    """
    return {
        "company_name": record.get("legal_name", ""),
        "dot_number": record.get("dot_number", ""),
        "mc_number": record.get("mc_number", ""),
        "phone": record.get("telephone", ""),
        "state": record.get("phy_state", record.get("state", "")),
    }


def write_csv(records, output_file):
    """Write carrier records to a CSV file using csv.writer.

    Args:
        records: List of carrier dictionaries with extracted fields.
        output_file: Path to the output CSV file.
    """
    fieldnames = ["company_name", "dot_number", "mc_number", "phone", "state"]

    try:
        with open(output_file, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(fieldnames)
            for rec in records:
                writer.writerow([rec[col] for col in fieldnames])
    except OSError as exc:
        logger.error("Failed to write CSV file %s: %s", output_file, exc)
        sys.exit(1)

    logger.info("Wrote %d rows to %s", len(records), output_file)


def main():
    """Entry point: parse args, fetch newly authorized carriers, write CSV."""
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Querying FMCSA API for newly authorized carriers...")
    raw_records = fetch_carriers(
        api_url=args.api_url,
        limit=args.limit,
        min_dot_number=args.min_dot_number,
    )

    if not raw_records:
        logger.warning("No records returned. CSV will not be created.")
        sys.exit(0)

    extracted = [extract_fields(r) for r in raw_records]
    write_csv(extracted, args.output_file)


if __name__ == "__main__":
    main()
