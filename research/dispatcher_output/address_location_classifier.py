#!/usr/bin/env python3
"""
Address Location Classifier for Trucking Carriers

Fetches carrier physical addresses from FMCSA's public dataset and uses
OpenStreetMap/Nominatim to classify each address as residential or commercial.
Outputs a CSV with a 'Location Type' column to help qualify leads.

Usage:
    python address_location_classifier.py --output-csv carriers.csv --limit 50
    python address_location_classifier.py --nominatim-api-key YOUR_KEY --limit 100
"""

import argparse
import csv
import logging
import sys
import time
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_FMCSA_URL = "https://data.transportation.gov/resource/az4b-hbig.json"
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"

# Nominatim usage policy: max 1 request per second for unauthenticated use
NOMINATIM_DELAY = 1.1

# OSM place types mapped to location categories
RESIDENTIAL_TYPES = {
    "house", "residential", "apartments", "detached", "semidetached_house",
    "farm", "farmhouse", "bungalow", "static_caravan", "cabin",
    "terrace", "terraced_house",
}
COMMERCIAL_TYPES = {
    "commercial", "industrial", "warehouse", "retail", "office",
    "factory", "manufacture", "shop", "supermarket", "mall",
    "company", "yes",  # "yes" often appears for generic commercial buildings
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# FMCSA data retrieval
# ---------------------------------------------------------------------------
def fetch_carriers(fmcsa_url: str, limit: int) -> list[dict]:
    """Fetch carrier records from the FMCSA Socrata open-data endpoint.

    Args:
        fmcsa_url: Base URL of the FMCSA JSON resource.
        limit: Maximum number of records to retrieve.

    Returns:
        List of carrier dictionaries.
    """
    params = {"$limit": limit}
    logger.info("Fetching up to %d carriers from FMCSA...", limit)

    try:
        resp = requests.get(fmcsa_url, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("FMCSA request failed: %s", exc)
        sys.exit(1)

    carriers = resp.json()
    logger.info("Retrieved %d carrier records.", len(carriers))
    return carriers


def build_address(carrier: dict) -> Optional[str]:
    """Assemble a single-line physical address from FMCSA carrier fields.

    The dataset uses field names like phy_street, phy_city, phy_state, phy_zip.
    Returns None when essential parts are missing.
    """
    street = carrier.get("phy_street", "").strip()
    city = carrier.get("phy_city", "").strip()
    state = carrier.get("phy_state", "").strip()
    zipcode = carrier.get("phy_zip", "").strip()

    if not street or not city:
        return None

    parts = [street, city]
    if state:
        parts.append(state)
    if zipcode:
        parts.append(zipcode)
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Nominatim geocoding / classification
# ---------------------------------------------------------------------------
def classify_address(
    address: str,
    api_key: Optional[str] = None,
) -> tuple[str, float]:
    """Query Nominatim to determine whether *address* is residential or commercial.

    Args:
        address: Full address string to look up.
        api_key: Optional Nominatim API key (for higher rate limits).

    Returns:
        Tuple of (location_type, confidence_score).
        location_type is one of: 'Residential', 'Commercial', 'Unknown'.
        confidence_score is 0.0-1.0.
    """
    headers = {"User-Agent": "address-location-classifier/1.0"}
    params: dict = {
        "q": address,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 1,
    }
    if api_key:
        params["key"] = api_key

    try:
        resp = requests.get(
            NOMINATIM_SEARCH_URL, params=params, headers=headers, timeout=15,
        )
        resp.raise_for_status()
        results = resp.json()
    except requests.RequestException as exc:
        logger.warning("Nominatim lookup failed for '%s': %s", address, exc)
        return ("Unknown", 0.0)

    if not results:
        logger.debug("No Nominatim results for '%s'", address)
        return ("Unknown", 0.0)

    top = results[0]
    osm_type = top.get("type", "").lower()
    osm_category = top.get("category", "").lower()
    address_details = top.get("address", {})

    # Importance is 0-1; we use it as a rough confidence proxy
    confidence = round(float(top.get("importance", 0.5)), 2)

    # --- classification logic ---
    if osm_type in RESIDENTIAL_TYPES or osm_category == "place":
        if osm_type in RESIDENTIAL_TYPES:
            return ("Residential", confidence)

    if osm_type in COMMERCIAL_TYPES or osm_category in ("shop", "office", "company"):
        return ("Commercial", confidence)

    # Fall back to address-detail heuristics
    if "industrial" in address_details.get("road", "").lower():
        return ("Commercial", max(confidence, 0.4))
    if "suite" in address.lower() or "ste" in address.lower():
        return ("Commercial", max(confidence, 0.45))
    if osm_category == "building":
        # Generic building — lean slightly commercial for business addresses
        return ("Commercial", max(confidence * 0.8, 0.3))
    if osm_category == "highway" or osm_type == "street":
        # Nominatim matched to a road, not a building — low confidence
        return ("Unknown", 0.2)

    return ("Unknown", round(confidence * 0.5, 2))


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def process_carriers(
    fmcsa_url: str,
    nominatim_api_key: Optional[str],
    output_csv: str,
    limit: int,
) -> None:
    """End-to-end pipeline: fetch carriers, classify addresses, write CSV."""
    carriers = fetch_carriers(fmcsa_url, limit)

    fieldnames = [
        "Company Name",
        "DOT#",
        "MC#",
        "Physical Address",
        "Location Type",
        "Confidence Score",
    ]

    classified = 0
    skipped = 0

    with open(output_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()

        for i, carrier in enumerate(carriers, start=1):
            company = carrier.get("legal_name", carrier.get("dba_name", "N/A"))
            dot_number = carrier.get("dot_number", "N/A")
            mc_number = carrier.get("mc_mx_ff_number", "N/A")
            address = build_address(carrier)

            if not address:
                logger.debug(
                    "Skipping carrier %s (DOT %s): incomplete address", company, dot_number,
                )
                skipped += 1
                continue

            logger.info(
                "[%d/%d] Classifying: %s — %s", i, len(carriers), company, address,
            )

            location_type, confidence = classify_address(address, nominatim_api_key)

            writer.writerow({
                "Company Name": company,
                "DOT#": dot_number,
                "MC#": mc_number,
                "Physical Address": address,
                "Location Type": location_type,
                "Confidence Score": confidence,
            })
            classified += 1

            # Respect Nominatim rate limits
            time.sleep(NOMINATIM_DELAY)

    logger.info(
        "Done. %d carriers classified, %d skipped. Results saved to %s",
        classified, skipped, output_csv,
    )


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Classify trucking carrier physical addresses as residential or "
            "commercial using FMCSA data and OpenStreetMap/Nominatim."
        ),
    )
    parser.add_argument(
        "--fmcsa-url",
        default=DEFAULT_FMCSA_URL,
        help="FMCSA Socrata JSON endpoint (default: %(default)s)",
    )
    parser.add_argument(
        "--nominatim-api-key",
        default=None,
        help="Optional Nominatim API key for higher rate limits",
    )
    parser.add_argument(
        "--output-csv",
        default="carrier_locations.csv",
        help="Path to output CSV file (default: %(default)s)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of carrier records to fetch (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main() -> None:
    """Entry point."""
    args = parse_args()
    process_carriers(
        fmcsa_url=args.fmcsa_url,
        nominatim_api_key=args.nominatim_api_key,
        output_csv=args.output_csv,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
