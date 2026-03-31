#!/usr/bin/env python3
"""
Broker Authority Checker — FMCSA Socrata API

Checks if a trucking company's DOT number is associated with freight broker
authority (MC number) using the FMCSA Company Census dataset. Supports single
DOT lookups and batch queries filtered by state.

API endpoint: https://data.transportation.gov/resource/az4b-hbig.json
Fallback:     https://data.transportation.gov/resource/az4n-8mr2.json

Usage examples:
    # Single DOT lookup
    python3 broker_authority_checker.py --dot-number 12345

    # Batch: active brokers in Texas, output JSON
    python3 broker_authority_checker.py --state TX --limit 25 --output-json results.json

    # Combine filters
    python3 broker_authority_checker.py --dot-number 12345 --output-json carrier.json
"""

import argparse
import json
import logging
import sys
import urllib.request
import urllib.parse
import urllib.error

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PRIMARY_API = "https://data.transportation.gov/resource/az4b-hbig.json"
FALLBACK_API = "https://data.transportation.gov/resource/az4n-8mr2.json"

FLEET_SIZE_MAP = {
    "A": "1-6",
    "B": "7-11",
    "C": "12-20",
    "D": "21-50",
    "E": "51-100",
    "F": "101-500",
    "G": "501-1000",
    "H": "1001-5000",
    "I": "5001-10000",
    "J": "10001+",
    "P": "Pool/Other",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _fetch_json(url: str, timeout: int = 30) -> list[dict]:
    """Fetch JSON from *url*, return parsed list of records."""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode()
    return json.loads(data)


def query_fmcsa(
    dot_number: int | None = None,
    state: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Query FMCSA Socrata API with SoQL filters.

    Args:
        dot_number: Specific DOT number to look up.
        state: Two-letter state code to filter by.
        limit: Maximum records to return (Socrata default is 1000).

    Returns:
        List of carrier record dicts from the API.
    """
    clauses: list[str] = []
    if dot_number is not None:
        clauses.append(f"dot_number={dot_number}")
    if state:
        clauses.append(f"phy_state='{state.upper()}'")

    params: dict[str, str] = {"$limit": str(limit)}
    if clauses:
        params["$where"] = " AND ".join(clauses)

    qs = urllib.parse.urlencode(params)

    # Try primary endpoint, fall back if it 404s or errors
    for base in (PRIMARY_API, FALLBACK_API):
        url = f"{base}?{qs}"
        log.info("Querying %s", url)
        try:
            records = _fetch_json(url)
            if records or dot_number is not None:
                return records
        except urllib.error.HTTPError as exc:
            log.warning("HTTP %s from %s — trying fallback", exc.code, base)
        except urllib.error.URLError as exc:
            log.warning("Connection error (%s) — trying fallback", exc.reason)

    log.error("All API endpoints failed")
    return []


# ---------------------------------------------------------------------------
# Record parsing
# ---------------------------------------------------------------------------

def _mc_numbers(rec: dict) -> list[dict]:
    """Extract MC docket entries from a carrier record."""
    results = []
    for slot in ("1", "2", "3"):
        prefix = rec.get(f"docket{slot}prefix", "")
        number = rec.get(f"docket{slot}", "")
        status = rec.get(f"docket{slot}_status_code", "")
        if prefix and number:
            results.append({
                "prefix": prefix,
                "number": number,
                "full": f"{prefix}-{number}",
                "status": "Active" if status == "A" else "Inactive" if status == "I" else status or "Unknown",
            })
    return results


def _has_broker_indicators(rec: dict) -> bool:
    """Return True if the record suggests freight broker authority."""
    classdef = rec.get("classdef", "").upper()
    if "BROKER" in classdef:
        return True
    # MC docket with active status is a strong indicator
    for d in _mc_numbers(rec):
        if d["prefix"] == "MC" and d["status"] == "Active":
            return True
    return False


def format_record(rec: dict) -> dict:
    """Normalise a raw API record into a clean summary dict."""
    dockets = _mc_numbers(rec)
    mc_entries = [d for d in dockets if d["prefix"] == "MC"]
    fleet_code = rec.get("fleetsize", "")

    return {
        "dot_number": rec.get("dot_number", ""),
        "legal_name": rec.get("legal_name", ""),
        "dba_name": rec.get("dba_name", ""),
        "state": rec.get("phy_state", ""),
        "city": rec.get("phy_city", ""),
        "status": "Active" if rec.get("status_code") == "A" else "Inactive",
        "mc_numbers": mc_entries if mc_entries else None,
        "all_dockets": dockets if dockets else None,
        "has_broker_authority": _has_broker_indicators(rec),
        "carrier_operation": rec.get("carrier_operation", ""),
        "class_definition": rec.get("classdef", ""),
        "fleet_size": FLEET_SIZE_MAP.get(fleet_code, fleet_code),
        "power_units": rec.get("power_units", ""),
        "total_drivers": rec.get("total_drivers", ""),
        "phone": rec.get("phone", ""),
        "email": rec.get("email_address", ""),
        "insurance_status": (
            "Rated" if rec.get("safety_rating") else "Not rated"
        ),
        "safety_rating": rec.get("safety_rating", ""),
    }


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_record(rec: dict) -> None:
    """Pretty-print a single formatted record to stdout."""
    sep = "-" * 60
    print(sep)
    print(f"  DOT Number      : {rec['dot_number']}")
    print(f"  Company          : {rec['legal_name']}")
    if rec["dba_name"]:
        print(f"  DBA              : {rec['dba_name']}")
    print(f"  State            : {rec['state']}")
    print(f"  City             : {rec['city']}")
    print(f"  Status           : {rec['status']}")

    if rec["mc_numbers"]:
        for mc in rec["mc_numbers"]:
            print(f"  MC Number        : {mc['full']}  ({mc['status']})")
    else:
        print("  MC Number        : None")

    broker_flag = "YES" if rec["has_broker_authority"] else "No"
    print(f"  Broker Authority : {broker_flag}")
    print(f"  Class Definition : {rec['class_definition']}")
    print(f"  Fleet Size       : {rec['fleet_size']}")
    print(f"  Power Units      : {rec['power_units']}")
    print(f"  Total Drivers    : {rec['total_drivers']}")
    print(f"  Phone            : {rec['phone']}")
    print(f"  Email            : {rec['email']}")
    print(f"  Insurance/Safety : {rec['insurance_status']}")
    if rec["safety_rating"]:
        print(f"  Safety Rating    : {rec['safety_rating']}")
    print(sep)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Check FMCSA carrier records for freight broker authority (MC numbers). "
            "Queries the FMCSA Company Census via the Socrata open-data API."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --dot-number 12345\n"
            "  %(prog)s --state TX --limit 20\n"
            "  %(prog)s --state CA --limit 50 --output-json brokers_ca.json\n"
        ),
    )
    parser.add_argument(
        "--dot-number",
        type=int,
        default=None,
        help="Look up a specific DOT number",
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Filter carriers by two-letter state code (e.g. TX, CA)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of records to return (default: 50)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        metavar="FILE",
        help="Write results as JSON to FILE (batch mode)",
    )
    return parser


def main() -> None:
    """Entry point: parse args, query API, display or save results."""
    parser = build_parser()
    args = parser.parse_args()

    if args.dot_number is None and args.state is None:
        parser.error("Provide at least --dot-number or --state")

    log.info(
        "Searching FMCSA — DOT: %s | State: %s | Limit: %d",
        args.dot_number or "any",
        args.state or "any",
        args.limit,
    )

    raw_records = query_fmcsa(
        dot_number=args.dot_number,
        state=args.state,
        limit=args.limit,
    )

    if not raw_records:
        log.warning("No records found for the given filters")
        sys.exit(0)

    formatted = [format_record(r) for r in raw_records]
    brokers = [r for r in formatted if r["has_broker_authority"]]

    # Console output
    print(f"\nTotal records returned : {len(formatted)}")
    print(f"With broker authority  : {len(brokers)}\n")

    for rec in formatted:
        print_record(rec)

    if brokers:
        print(f"\n=== BROKERS WITH ACTIVE MC NUMBERS ({len(brokers)}) ===\n")
        for rec in brokers:
            mc_str = ", ".join(m["full"] for m in (rec["mc_numbers"] or []))
            print(f"  DOT {rec['dot_number']}  {rec['legal_name']}  —  MC: {mc_str}  [{rec['state']}]")
        print()

    # JSON output
    if args.output_json:
        output = {
            "query": {
                "dot_number": args.dot_number,
                "state": args.state,
                "limit": args.limit,
            },
            "total_records": len(formatted),
            "broker_count": len(brokers),
            "records": formatted,
            "brokers_only": brokers,
        }
        with open(args.output_json, "w") as fh:
            json.dump(output, fh, indent=2)
        log.info("JSON output written to %s", args.output_json)


if __name__ == "__main__":
    main()
