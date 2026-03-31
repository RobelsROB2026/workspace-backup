#!/usr/bin/env python3
"""
FMCSA Address Location Classifier

Queries the FMCSA Socrata API for trucking carrier physical addresses,
then uses OpenStreetMap Nominatim to classify each address as residential
or commercial. Useful for qualifying leads in trucking insurance outreach.

Usage:
    python fmcsa_address_location_classifier.py --state TX --min-fleet-size 5 --limit 20
    python fmcsa_address_location_classifier.py --state CA --output-format csv --limit 50
"""

import argparse
import csv
import io
import logging
import sys
import time

import requests

FMCSA_API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Nominatim usage policy: max 1 request per second
NOMINATIM_DELAY = 1.1

# OSM class/type combos that indicate residential locations
RESIDENTIAL_TYPES = {
    "residential",
    "house",
    "apartments",
    "detached",
    "semidetached_house",
    "farm",
    "farmhouse",
    "hamlet",
    "dwelling",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Classify FMCSA carrier addresses as residential or commercial "
        "using OpenStreetMap/Nominatim geocoding.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --state TX --min-fleet-size 5 --limit 20\n"
            "  %(prog)s --state CA --output-format csv --limit 50\n"
        ),
    )
    parser.add_argument(
        "--state",
        required=True,
        type=str,
        help="2-letter US state code (e.g. TX, CA, FL)",
    )
    parser.add_argument(
        "--min-fleet-size",
        type=int,
        default=1,
        help="Minimum number of power units (default: 1)",
    )
    parser.add_argument(
        "--output-format",
        choices=["table", "csv"],
        default="table",
        help="Output format: table or csv (default: table)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Max number of carriers to fetch (default: 25)",
    )
    return parser.parse_args()


def fetch_carriers(state, min_fleet_size, limit):
    """Fetch carrier records from FMCSA Socrata API.

    Args:
        state: 2-letter state code.
        min_fleet_size: Minimum number of power units.
        limit: Maximum records to return.

    Returns:
        List of carrier dicts from the API.
    """
    params = {
        "$where": (
            f"phy_state='{state.upper()}' "
            f"AND tot_pwr_units >= {min_fleet_size} "
            "AND phy_street IS NOT NULL"
        ),
        "$select": (
            "legal_name, dba_name, dot_number, "
            "phy_street, phy_city, phy_state, phy_zip, "
            "tot_pwr_units, tot_drivers, telephone"
        ),
        "$order": "tot_pwr_units DESC",
        "$limit": limit,
    }

    logger.info(
        "Querying FMCSA API for carriers in %s with >= %d power units (limit %d)",
        state.upper(),
        min_fleet_size,
        limit,
    )

    try:
        resp = requests.get(FMCSA_API_URL, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("FMCSA API request failed: %s", exc)
        sys.exit(1)

    carriers = resp.json()
    logger.info("Received %d carrier records", len(carriers))
    return carriers


def classify_address(street, city, state, zipcode):
    """Geocode an address via Nominatim and classify as residential or commercial.

    Args:
        street: Street address string.
        city: City name.
        state: State code.
        zipcode: ZIP code.

    Returns:
        Tuple of (location_type, osm_class, osm_type) where location_type
        is 'Residential', 'Commercial', or 'Unknown'.
    """
    full_address = f"{street}, {city}, {state} {zipcode}"
    params = {
        "q": full_address,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    headers = {
        "User-Agent": "FMCSAAddressClassifier/1.0 (research tool)",
    }

    try:
        resp = requests.get(
            NOMINATIM_URL, params=params, headers=headers, timeout=15
        )
        resp.raise_for_status()
        results = resp.json()
    except requests.RequestException as exc:
        logger.warning("Nominatim request failed for '%s': %s", full_address, exc)
        return "Unknown", "", ""

    if not results:
        logger.debug("No Nominatim results for '%s'", full_address)
        return "Unknown", "", ""

    hit = results[0]
    osm_class = hit.get("class", "")
    osm_type = hit.get("type", "")

    # Check if the type indicates residential
    if osm_type in RESIDENTIAL_TYPES or osm_class == "place" and osm_type in (
        "house",
        "hamlet",
        "isolated_dwelling",
    ):
        location_type = "Residential"
    elif osm_class in ("building", "place") and osm_type in (
        "commercial",
        "industrial",
        "retail",
        "warehouse",
        "office",
    ):
        location_type = "Commercial"
    elif osm_class == "building":
        # Generic building — check address details for clues
        addr = hit.get("address", {})
        if any(
            kw in (addr.get("road", "") + addr.get("suburb", "")).lower()
            for kw in ("industrial", "commerce", "business", "park")
        ):
            location_type = "Commercial"
        else:
            location_type = "Residential"
    elif osm_class in ("highway", "amenity"):
        location_type = "Commercial"
    else:
        location_type = "Unknown"

    return location_type, osm_class, osm_type


def build_results(carriers):
    """Classify each carrier's address and build result rows.

    Args:
        carriers: List of carrier dicts from FMCSA API.

    Returns:
        List of result dicts with carrier info + location classification.
    """
    results = []
    total = len(carriers)

    for i, c in enumerate(carriers, 1):
        name = c.get("legal_name", "N/A")
        dba = c.get("dba_name", "")
        dot = c.get("dot_number", "")
        street = c.get("phy_street", "")
        city = c.get("phy_city", "")
        state = c.get("phy_state", "")
        zipcode = c.get("phy_zip", "")
        units = c.get("tot_pwr_units", "")
        drivers = c.get("tot_drivers", "")
        phone = c.get("telephone", "")

        full_addr = f"{street}, {city}, {state} {zipcode}".strip(", ")

        logger.info(
            "[%d/%d] Classifying: %s — %s", i, total, name, full_addr
        )

        loc_type, osm_class, osm_type = classify_address(
            street, city, state, zipcode
        )

        results.append(
            {
                "DOT#": dot,
                "Legal Name": name,
                "DBA": dba,
                "Address": full_addr,
                "Power Units": units,
                "Drivers": drivers,
                "Phone": phone,
                "Location Type": loc_type,
                "OSM Class": osm_class,
                "OSM Type": osm_type,
            }
        )

        # Respect Nominatim rate limit
        if i < total:
            time.sleep(NOMINATIM_DELAY)

    return results


def print_table(results):
    """Print results as a formatted ASCII table."""
    if not results:
        print("No results.")
        return

    # Columns to display (skip OSM internals for table view)
    columns = [
        "DOT#",
        "Legal Name",
        "Address",
        "Power Units",
        "Drivers",
        "Phone",
        "Location Type",
    ]
    widths = {}
    for col in columns:
        widths[col] = max(
            len(col), max((len(str(r.get(col, ""))) for r in results), default=0)
        )

    # Cap widths for readability
    widths["Legal Name"] = min(widths["Legal Name"], 35)
    widths["Address"] = min(widths["Address"], 40)

    header = " | ".join(col.ljust(widths[col]) for col in columns)
    separator = "-+-".join("-" * widths[col] for col in columns)

    print(header)
    print(separator)
    for r in results:
        row_vals = []
        for col in columns:
            val = str(r.get(col, ""))
            max_w = widths[col]
            if len(val) > max_w:
                val = val[: max_w - 1] + "\u2026"
            row_vals.append(val.ljust(max_w))
        print(" | ".join(row_vals))


def print_csv(results):
    """Print results as CSV to stdout."""
    if not results:
        return
    columns = list(results[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns)
    writer.writeheader()
    writer.writerows(results)
    print(buf.getvalue(), end="")


def main():
    """Entry point: parse args, fetch carriers, classify addresses, output results."""
    args = parse_args()

    carriers = fetch_carriers(args.state, args.min_fleet_size, args.limit)
    if not carriers:
        logger.warning("No carriers found matching criteria.")
        sys.exit(0)

    results = build_results(carriers)

    # Summary stats
    residential = sum(1 for r in results if r["Location Type"] == "Residential")
    commercial = sum(1 for r in results if r["Location Type"] == "Commercial")
    unknown = sum(1 for r in results if r["Location Type"] == "Unknown")
    logger.info(
        "Classification complete: %d Residential, %d Commercial, %d Unknown",
        residential,
        commercial,
        unknown,
    )

    if args.output_format == "csv":
        print_csv(results)
    else:
        print_table(results)
        print(
            f"\nSummary: {residential} Residential | {commercial} Commercial | {unknown} Unknown"
        )


if __name__ == "__main__":
    main()
