#!/usr/bin/env python3
"""
FMCSA New Carrier Authority Query Tool

Queries the FMCSA Socrata API (data.transportation.gov) for newly authorized
motor carriers and exports results to CSV.

Features:
    1. Filters carriers by authorization date (defaults to today onward)
    2. Extracts carrier details: company name, DOT#, MC#, phone, state
    3. Writes results to CSV with headers

API endpoint: https://data.transportation.gov/resource/az4b-hbig.json
API docs: https://dev.socrata.com/foundry/data.transportation.gov/az4b-hbig

Example usage:
    # Query carriers authorized from today onward, save to default output
    python3 fmcsa_carrier_query.py

    # Specify a minimum authorization date and output file
    python3 fmcsa_carrier_query.py --min-dates 2026-03-01 --output-file carriers_march.csv

    # Batch mode: read multiple dates from a CSV file (one YYYY-MM-DD per line)
    python3 fmcsa_carrier_query.py --csv-file dates.csv --output-file batch_results.csv

    # Use a custom API endpoint
    python3 fmcsa_carrier_query.py --api-url "https://data.transportation.gov/resource/az4b-hbig.json"
"""

import argparse
import csv
import json
import logging
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"
DEFAULT_OUTPUT = "fmcsa_new_carriers.csv"
CSV_HEADERS = ["company_name", "dot_number", "mc_number", "phone", "state"]
PAGE_LIMIT = 1000


def parse_args(argv=None):
    """Parse and validate command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        argparse.Namespace with parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Query the FMCSA Socrata API for newly authorized motor carriers and export to CSV.",
        epilog=(
            "Examples:\n"
            "  %(prog)s\n"
            "  %(prog)s --min-dates 2026-03-01 --output-file march.csv\n"
            "  %(prog)s --csv-file dates.csv --output-file batch.csv\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Socrata API endpoint URL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--output-file",
        default=DEFAULT_OUTPUT,
        help=f"Path for CSV output file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--min-dates",
        default=None,
        help=(
            "Minimum authorization date in YYYY-MM-DD format. "
            "Only carriers authorized on or after this date are returned (default: today)."
        ),
    )
    parser.add_argument(
        "--csv-file",
        default=None,
        help=(
            "Path to a CSV file containing dates (one YYYY-MM-DD per line) for batch querying. "
            "Each date is used as a separate --min-dates value; results are merged and deduplicated."
        ),
    )
    return parser.parse_args(argv)


def fetch_page(api_url, min_date, offset=0, limit=PAGE_LIMIT):
    """Fetch a single page of carrier records from the FMCSA Socrata API.

    Constructs a SoQL query filtering on authorization_date >= min_date and
    requests up to `limit` records starting at `offset`.

    Args:
        api_url: Base Socrata API endpoint URL.
        min_date: ISO date string (YYYY-MM-DD) for the authorization_date filter.
        offset: Pagination offset.
        limit: Maximum records to return per request.

    Returns:
        List of record dicts from the API response.

    Raises:
        urllib.error.URLError: On network or HTTP errors.
        json.JSONDecodeError: If the response is not valid JSON.
    """
    params = {
        "$where": f"authorization_date >= '{min_date}T00:00:00.000'",
        "$limit": str(limit),
        "$offset": str(offset),
        "$order": "authorization_date DESC",
    }
    url = f"{api_url}?{urllib.parse.urlencode(params)}"
    logger.debug("GET %s", url)

    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if not isinstance(data, list):
        logger.error("Unexpected API response type: %s", type(data).__name__)
        return []

    return data


def fetch_all_carriers(api_url, min_date):
    """Fetch all carrier records across paginated API responses.

    Pages through the Socrata API until fewer than PAGE_LIMIT records are
    returned, indicating the last page.

    Args:
        api_url: Base Socrata API endpoint URL.
        min_date: ISO date string (YYYY-MM-DD) for the authorization_date filter.

    Returns:
        List of all matching record dicts.
    """
    all_records = []
    offset = 0

    while True:
        logger.info(
            "Fetching records offset=%d limit=%d for authorization_date >= %s",
            offset, PAGE_LIMIT, min_date,
        )
        page = fetch_page(api_url, min_date, offset=offset, limit=PAGE_LIMIT)

        if not page:
            break

        all_records.extend(page)
        logger.info("Received %d records (total so far: %d)", len(page), len(all_records))

        if len(page) < PAGE_LIMIT:
            break
        offset += PAGE_LIMIT

    return all_records


def extract_carrier_details(record):
    """Extract relevant carrier fields from a raw Socrata API record.

    Maps FMCSA field names to the standardized output column names used in
    the CSV output.

    Args:
        record: A single carrier record dict from the API.

    Returns:
        Dict with keys: company_name, dot_number, mc_number, phone, state.
    """
    return {
        "company_name": str(record.get("legal_name", "")).strip(),
        "dot_number": str(record.get("dot_number", "")).strip(),
        "mc_number": str(record.get("mc_mx_ff_number", "")).strip(),
        "phone": str(record.get("phone", record.get("telephone", ""))).strip(),
        "state": str(record.get("phy_state", "")).strip(),
    }


def write_csv(carriers, output_path):
    """Write carrier records to a CSV file with headers.

    Args:
        carriers: List of carrier detail dicts (keys must match CSV_HEADERS).
        output_path: File path for the CSV output.
    """
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(carriers)
    except OSError as exc:
        logger.error("Failed to write CSV file %s: %s", output_path, exc)
        sys.exit(1)

    logger.info("Wrote %d records to %s", len(carriers), output_path)


def load_dates_from_csv(csv_path):
    """Load dates from a CSV file for batch querying.

    Reads one YYYY-MM-DD date per line. Skips blank lines, header rows
    (starting with 'date'), and lines that don't parse as valid dates.

    Args:
        csv_path: Path to the CSV file containing dates.

    Returns:
        List of validated date strings (YYYY-MM-DD).
    """
    dates = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                raw = row[0].strip()
                if not raw or raw.lower().startswith("date"):
                    continue
                try:
                    datetime.strptime(raw, "%Y-%m-%d")
                    dates.append(raw)
                except ValueError:
                    logger.warning("Skipping invalid date in %s: %r", csv_path, raw)
    except OSError as exc:
        logger.error("Failed to read CSV file %s: %s", csv_path, exc)
        sys.exit(1)

    logger.info("Loaded %d date(s) from %s", len(dates), csv_path)
    return dates


def validate_date(date_str):
    """Validate that a string is a properly formatted YYYY-MM-DD date.

    Args:
        date_str: The date string to validate.

    Returns:
        The validated date string.

    Raises:
        SystemExit: If the date string is not valid.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        logger.error("Invalid date format: %r (expected YYYY-MM-DD)", date_str)
        sys.exit(1)
    return date_str


def main():
    """Entry point: parse arguments, query the FMCSA API, and write CSV output."""
    args = parse_args()

    # Determine which date(s) to query
    if args.csv_file:
        dates = load_dates_from_csv(args.csv_file)
        if not dates:
            logger.error("No valid dates found in %s", args.csv_file)
            sys.exit(1)
    else:
        min_date = args.min_dates if args.min_dates else date.today().isoformat()
        dates = [validate_date(min_date)]

    # Fetch and deduplicate carriers across all queried dates
    all_carriers = []
    seen_dots = set()

    for query_date in dates:
        logger.info("Querying carriers with authorization_date >= %s", query_date)
        try:
            records = fetch_all_carriers(args.api_url, query_date)
        except urllib.error.HTTPError as e:
            logger.error("HTTP error %d from API: %s", e.code, e.reason)
            continue
        except urllib.error.URLError as e:
            logger.error("Network error querying API: %s", e.reason)
            continue
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in API response: %s", e)
            continue
        except Exception:
            logger.exception("Unexpected error querying API for date %s", query_date)
            continue

        for record in records:
            carrier = extract_carrier_details(record)
            dot = carrier["dot_number"]
            if dot and dot not in seen_dots:
                seen_dots.add(dot)
                all_carriers.append(carrier)

    if not all_carriers:
        logger.warning("No carriers found matching the specified criteria.")

    logger.info("Total unique carriers: %d", len(all_carriers))
    write_csv(all_carriers, args.output_file)
    print(f"Done. {len(all_carriers)} carrier(s) written to {args.output_file}")


if __name__ == "__main__":
    main()
