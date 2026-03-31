#!/usr/bin/env python3
"""
FMCSA Carrier Address Location Type Classifier

Queries the FMCSA Socrata API for trucking carrier data, then uses the
OpenStreetMap Nominatim API to classify each carrier's physical address
as 'residential' or 'commercial'.

Usage:
    python fmcsa_address_location_type_tool.py --state TX --min-fleet-size 5 --limit 20
    python fmcsa_address_location_type_tool.py --state CA --limit 10 --output-format csv
    python fmcsa_address_location_type_tool.py --state FL --limit 5 --output-csv results.csv
"""

import argparse
import csv
import io
import logging
import sys
import time

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

FMCSA_API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Nominatim categories/types that indicate residential use
RESIDENTIAL_TYPES = {
    "house", "residential", "apartments", "detached", "semidetached_house",
    "terrace", "farm", "farmhouse", "bungalow", "dormitory", "cabin",
    "static_caravan", "houseboat", "dwelling", "yes",
}

# Nominatim categories that indicate commercial/industrial use
COMMERCIAL_TYPES = {
    "commercial", "industrial", "retail", "office", "warehouse",
    "manufacture", "factory", "shop", "marketplace", "store",
    "business", "company", "trade",
}


def query_fmcsa(state: str, min_fleet_size: int, limit: int) -> list[dict]:
    """Query the FMCSA Socrata API for carriers in the given state.

    Args:
        state: Two-letter state abbreviation (e.g. 'TX').
        min_fleet_size: Minimum number of power units.
        limit: Maximum number of records to return.

    Returns:
        List of carrier record dicts from the API.

    Raises:
        requests.HTTPError: If the API returns a non-2xx status.
    """
    where_clauses = [
        f"phy_state='{state.upper()}'",
        f"tot_pwr_units >= {min_fleet_size}",
    ]
    params = {
        "$select": (
            "legal_name, dot_number, mc_mx_ff_number, tot_pwr_units, "
            "telephone, phy_street, phy_city, phy_state, phy_zip, "
            "insurance_status, oic_state"
        ),
        "$where": " AND ".join(where_clauses),
        "$limit": limit,
        "$order": "tot_pwr_units DESC",
    }

    logger.info("Querying FMCSA API for carriers in %s with >= %d power units", state, min_fleet_size)
    resp = requests.get(FMCSA_API_URL, params=params, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    logger.info("FMCSA API returned %d carrier(s)", len(data))
    return data


def classify_address(street: str, city: str, state: str, zipcode: str) -> str:
    """Use Nominatim to classify an address as residential or commercial.

    Args:
        street: Street address line.
        city: City name.
        state: Two-letter state code.
        zipcode: ZIP code.

    Returns:
        'residential', 'commercial', or 'unknown'.
    """
    query = f"{street}, {city}, {state} {zipcode}, USA"
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 1,
    }
    headers = {
        "User-Agent": "FMCSAAddressClassifier/1.0 (research tool)",
    }

    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        results = resp.json()
    except requests.RequestException as exc:
        logger.warning("Nominatim lookup failed for %r: %s", query, exc)
        return "unknown"

    if not results:
        logger.debug("Nominatim returned no results for %r", query)
        return "unknown"

    result = results[0]
    osm_type = result.get("type", "").lower()
    osm_class = result.get("class", "").lower()
    address = result.get("address", {})
    addr_type = address.get("type", "").lower() if isinstance(address.get("type"), str) else ""

    all_indicators = {osm_type, osm_class, addr_type}

    if all_indicators & RESIDENTIAL_TYPES:
        return "residential"
    if all_indicators & COMMERCIAL_TYPES:
        return "commercial"

    # Heuristic: if Nominatim returned a 'place' class with 'house' or similar,
    # treat as residential. If 'building' class, lean commercial for business addresses.
    if osm_class == "place" and osm_type in ("house", "yes"):
        return "residential"
    if osm_class == "building":
        return "commercial"

    return "unknown"


def process_carriers(carriers: list[dict]) -> list[dict]:
    """Classify each carrier's physical address and return enriched records.

    Respects Nominatim's 1-request-per-second usage policy.

    Args:
        carriers: Raw carrier dicts from the FMCSA API.

    Returns:
        List of enriched dicts with a 'location_type' field.
    """
    results = []
    total = len(carriers)

    for idx, carrier in enumerate(carriers, 1):
        name = carrier.get("legal_name", "N/A")
        street = carrier.get("phy_street", "")
        city = carrier.get("phy_city", "")
        state = carrier.get("phy_state", "")
        zipcode = carrier.get("phy_zip", "")

        if street and city and state:
            logger.info("[%d/%d] Classifying address for %s", idx, total, name)
            location_type = classify_address(street, city, state, zipcode)
            # Nominatim usage policy: max 1 request per second
            time.sleep(1.1)
        else:
            logger.warning("[%d/%d] Incomplete address for %s, skipping lookup", idx, total, name)
            location_type = "unknown"

        results.append({
            "company_name": name,
            "dot_number": carrier.get("dot_number", "N/A"),
            "mc_number": carrier.get("mc_mx_ff_number", "N/A"),
            "fleet_size": carrier.get("tot_pwr_units", "N/A"),
            "phone": carrier.get("telephone", "N/A"),
            "state": state,
            "address": f"{street}, {city}, {state} {zipcode}".strip(", "),
            "insurance_status": carrier.get("insurance_status", "N/A"),
            "location_type": location_type,
        })

    return results


def format_table(records: list[dict]) -> str:
    """Format records as an aligned text table.

    Args:
        records: List of enriched carrier dicts.

    Returns:
        Multi-line string with column-aligned table.
    """
    if not records:
        return "No records found."

    columns = [
        ("Company", "company_name", 35),
        ("DOT#", "dot_number", 10),
        ("MC#", "mc_number", 12),
        ("Fleet", "fleet_size", 6),
        ("Phone", "phone", 14),
        ("St", "state", 4),
        ("Insurance", "insurance_status", 12),
        ("Loc Type", "location_type", 12),
    ]

    header = "  ".join(col[0].ljust(col[2]) for col in columns)
    separator = "  ".join("-" * col[2] for col in columns)
    lines = [header, separator]

    for rec in records:
        row = "  ".join(str(rec.get(col[1], "")).ljust(col[2])[:col[2]] for col in columns)
        lines.append(row)

    return "\n".join(lines)


def format_csv(records: list[dict]) -> str:
    """Format records as CSV text.

    Args:
        records: List of enriched carrier dicts.

    Returns:
        CSV-formatted string including header row.
    """
    if not records:
        return ""

    fieldnames = [
        "company_name", "dot_number", "mc_number", "fleet_size",
        "phone", "state", "address", "insurance_status", "location_type",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    return buf.getvalue()


def main():
    """Entry point: parse args, query FMCSA, classify addresses, and output results."""
    parser = argparse.ArgumentParser(
        description="Query FMCSA carriers and classify physical addresses as residential or commercial.",
    )
    parser.add_argument("--state", required=True, help="Two-letter state code (e.g. TX, CA, FL)")
    parser.add_argument("--min-fleet-size", type=int, default=1, help="Minimum power units (default: 1)")
    parser.add_argument("--limit", type=int, default=25, help="Max number of carriers to fetch (default: 25)")
    parser.add_argument(
        "--output-format", choices=["table", "csv"], default="table",
        help="Display format: table (default) or csv",
    )
    parser.add_argument("--output-csv", metavar="FILE", help="Export results to a CSV file")
    args = parser.parse_args()

    if len(args.state) != 2 or not args.state.isalpha():
        parser.error("--state must be a two-letter state code")

    try:
        carriers = query_fmcsa(args.state, args.min_fleet_size, args.limit)
    except requests.RequestException as exc:
        logger.error("Failed to query FMCSA API: %s", exc)
        sys.exit(1)

    if not carriers:
        logger.info("No carriers found matching the criteria.")
        sys.exit(0)

    records = process_carriers(carriers)

    # Print to stdout
    if args.output_format == "csv":
        print(format_csv(records), end="")
    else:
        print(format_table(records))

    # Optionally write CSV file
    if args.output_csv:
        csv_text = format_csv(records)
        with open(args.output_csv, "w", newline="") as f:
            f.write(csv_text)
        logger.info("Results exported to %s", args.output_csv)

    # Summary
    residential = sum(1 for r in records if r["location_type"] == "residential")
    commercial = sum(1 for r in records if r["location_type"] == "commercial")
    unknown = sum(1 for r in records if r["location_type"] == "unknown")
    logger.info(
        "Summary: %d residential, %d commercial, %d unknown out of %d carriers",
        residential, commercial, unknown, len(records),
    )


if __name__ == "__main__":
    main()
