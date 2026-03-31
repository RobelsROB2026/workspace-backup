#!/usr/bin/env python3
"""
FMCSA Safety Measurement System (SMS) Monitor

Monitors motor carriers for deteriorating safety scores by querying the
FMCSA Socrata API at data.transportation.gov/resource/az4b-hbig.json.

Compares current vs historical SMS data to identify carriers with:
  - 10+ point drops in safety scores (configurable via --alert-threshold)
  - Multiple violations across BASIC categories
  - High risk ratings or OOS (out-of-service) rates
  - Recent accidents indicating urgent insurance review

Supports auto-fetching carrier details by DOT number, tracking safety
score trends over configurable intervals, and exporting alerts in
CSV, JSON, or Markdown formats.

Usage:
    python fmcsa_sms_monitor.py --carrier-list carriers.csv --output-format csv
    python fmcsa_sms_monitor.py --csv-file my_carriers.csv --alert-threshold 15
    python fmcsa_sms_monitor.py --carrier-list auto --api-key YOUR_KEY
    python fmcsa_sms_monitor.py --help
"""

import argparse
import csv
import io
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# --- Constants ---

SOCRATA_API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"
FMCSA_CARRIER_API = "https://mobile.fmcsa.dot.gov/qc/services/carriers"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2

# SMS BASIC categories tracked by FMCSA
BASIC_CATEGORIES = [
    "unsafe_driving",
    "hours_of_service",
    "driver_fitness",
    "controlled_substances",
    "vehicle_maintenance",
    "hazmat_compliance",
    "crash_indicator",
]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Monitor FMCSA SMS data for carriers with deteriorating safety scores.",
        epilog="Example: python fmcsa_sms_monitor.py --carrier-list carriers.csv --output-format json",
    )
    parser.add_argument(
        "--api-key",
        help="Socrata API app token for higher rate limits (optional but recommended).",
    )
    parser.add_argument(
        "--output-format",
        choices=["csv", "json", "markdown"],
        default="json",
        help="Output format for results (default: json).",
    )
    parser.add_argument(
        "--alert-threshold",
        type=float,
        default=10.0,
        help="Point drop threshold to trigger alert (default: 10 points).",
    )
    parser.add_argument(
        "--monitor-interval",
        type=int,
        default=90,
        help="Number of days to look back for historical comparison (default: 90).",
    )
    parser.add_argument(
        "--carrier-list",
        help=(
            "Path to CSV file with DOT numbers (column: dot_number), "
            "or 'auto' to auto-fetch recently active carriers from the API."
        ),
    )
    parser.add_argument(
        "--csv-file",
        help="Alternate path to a CSV file with carrier DOT numbers (column: dot_number).",
    )
    parser.add_argument(
        "--output-file",
        help="Path to write output file. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Max number of carriers to fetch in auto mode (default: 200).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


class SocrataClient:
    """Client for querying the FMCSA Socrata Open Data API."""

    def __init__(self, api_key: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "FMCSA-SMS-Monitor/1.0",
        })
        if api_key:
            self.session.headers["X-App-Token"] = api_key

    def _request(self, url: str, params: dict) -> list[dict]:
        """Make a GET request with retries."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as exc:
                if resp.status_code == 429:
                    wait = RETRY_DELAY * attempt
                    logger.warning("Rate limited, waiting %ds (attempt %d/%d)", wait, attempt, MAX_RETRIES)
                    time.sleep(wait)
                    continue
                logger.error("HTTP error %s: %s", resp.status_code, exc)
                raise
            except requests.exceptions.RequestException as exc:
                if attempt < MAX_RETRIES:
                    logger.warning("Request failed (attempt %d/%d): %s", attempt, MAX_RETRIES, exc)
                    time.sleep(RETRY_DELAY * attempt)
                else:
                    raise
        return []

    def fetch_carrier_inspections(
        self, dot_number: str, limit: int = 1000, offset: int = 0
    ) -> list[dict]:
        """Fetch inspection records for a specific carrier by DOT number."""
        params = {
            "$where": f"dot_number='{dot_number}'",
            "$order": "inspection_date DESC",
            "$limit": str(limit),
            "$offset": str(offset),
        }
        logger.debug("Fetching inspections for DOT %s", dot_number)
        return self._request(SOCRATA_API_URL, params)

    def fetch_recent_carriers(self, days_back: int = 90, limit: int = 200) -> list[dict]:
        """Auto-fetch carriers with recent inspection activity."""
        cutoff = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00")
        params = {
            "$where": f"inspection_date > '{cutoff}'",
            "$select": "dot_number, legal_name, inspection_date, total_violations_s",
            "$order": "inspection_date DESC",
            "$limit": str(limit),
        }
        logger.info("Auto-fetching carriers with inspections since %s", cutoff)
        return self._request(SOCRATA_API_URL, params)

    def fetch_carrier_details(self, dot_number: str) -> Optional[dict]:
        """Fetch carrier detail info from FMCSA carrier API."""
        url = f"{FMCSA_CARRIER_API}/{dot_number}"
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                if "content" in data:
                    return data["content"].get("carrier", data["content"])
                return data
        except requests.exceptions.RequestException as exc:
            logger.debug("Could not fetch carrier details for DOT %s: %s", dot_number, exc)
        return None


def load_carrier_list_from_csv(filepath: str) -> list[str]:
    """Load DOT numbers from a CSV file.

    Expects a column named 'dot_number' (case-insensitive). Falls back to
    the first column if no header match is found.
    """
    path = Path(filepath)
    if not path.exists():
        logger.error("Carrier list file not found: %s", filepath)
        sys.exit(1)

    dot_numbers = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Find the DOT number column (case-insensitive)
        dot_col = None
        if reader.fieldnames:
            for col in reader.fieldnames:
                if col.strip().lower().replace(" ", "_") in ("dot_number", "dot", "dotnumber", "usdot"):
                    dot_col = col
                    break
            if dot_col is None:
                dot_col = reader.fieldnames[0]
                logger.warning("No 'dot_number' column found, using first column: %s", dot_col)

        for row in reader:
            val = row.get(dot_col, "").strip()
            if val and val.isdigit():
                dot_numbers.append(val)

    logger.info("Loaded %d DOT numbers from %s", len(dot_numbers), filepath)
    return dot_numbers


def compute_safety_scores(inspections: list[dict], monitor_interval_days: int) -> dict:
    """Compute current and historical safety metrics from inspection records.

    Splits inspections into 'current' (within monitor_interval_days) and
    'historical' (older) periods, then computes average violation rates
    and OOS percentages for each BASIC-adjacent metric.

    Returns a dict with current scores, historical scores, deltas, and flags.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(days=monitor_interval_days)

    current_records = []
    historical_records = []

    for rec in inspections:
        insp_date_str = rec.get("inspection_date", "")
        try:
            insp_date = datetime.fromisoformat(insp_date_str.replace("Z", "+00:00").split("+")[0])
        except (ValueError, AttributeError):
            continue

        if insp_date >= cutoff:
            current_records.append(rec)
        else:
            historical_records.append(rec)

    def _aggregate(records: list[dict]) -> dict:
        """Aggregate violation and OOS metrics from a list of inspection records."""
        if not records:
            return {
                "total_inspections": 0,
                "total_violations": 0,
                "driver_oos_count": 0,
                "vehicle_oos_count": 0,
                "hazmat_violations": 0,
                "unsafe_driving_violations": 0,
                "hos_violations": 0,
                "avg_violations_per_inspection": 0.0,
                "oos_rate": 0.0,
                "accident_count": 0,
            }

        total_violations = 0
        driver_oos = 0
        vehicle_oos = 0
        hazmat = 0
        unsafe = 0
        hos = 0
        accidents = 0

        for r in records:
            total_violations += _safe_int(r.get("total_violations_s", 0))
            driver_oos += _safe_int(r.get("driver_oos_total_s", 0))
            vehicle_oos += _safe_int(r.get("vehicle_oos_total_s", 0))
            hazmat += _safe_int(r.get("hazmat_total_s", 0))
            unsafe += _safe_int(r.get("unsafe_driv_insp_w_viol_s", 0))
            hos += _safe_int(r.get("hos_insp_w_viol_s", 0))
            accidents += _safe_int(r.get("crash_total_s", 0))

        n = len(records)
        oos_total = driver_oos + vehicle_oos
        return {
            "total_inspections": n,
            "total_violations": total_violations,
            "driver_oos_count": driver_oos,
            "vehicle_oos_count": vehicle_oos,
            "hazmat_violations": hazmat,
            "unsafe_driving_violations": unsafe,
            "hos_violations": hos,
            "avg_violations_per_inspection": round(total_violations / n, 2),
            "oos_rate": round((oos_total / n) * 100, 1) if n else 0.0,
            "accident_count": accidents,
        }

    current = _aggregate(current_records)
    historical = _aggregate(historical_records)

    # Calculate deltas (positive = worsening)
    avg_delta = round(
        current["avg_violations_per_inspection"] - historical["avg_violations_per_inspection"], 2
    )
    oos_delta = round(current["oos_rate"] - historical["oos_rate"], 1)

    # Composite safety score: weighted sum scaled to 0-100
    # Higher = worse
    def _composite(agg: dict) -> float:
        return round(
            agg["avg_violations_per_inspection"] * 15
            + agg["oos_rate"] * 0.5
            + agg["unsafe_driving_violations"] * 3
            + agg["hos_violations"] * 2
            + agg["hazmat_violations"] * 5
            + agg["accident_count"] * 10,
            1,
        )

    current_score = _composite(current)
    historical_score = _composite(historical)
    score_delta = round(current_score - historical_score, 1)

    return {
        "current": current,
        "historical": historical,
        "avg_violations_delta": avg_delta,
        "oos_rate_delta": oos_delta,
        "current_composite_score": current_score,
        "historical_composite_score": historical_score,
        "score_delta": score_delta,
    }


def _safe_int(val: Any) -> int:
    """Safely convert a value to int, returning 0 on failure."""
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def evaluate_carrier(
    dot_number: str,
    scores: dict,
    alert_threshold: float,
    carrier_details: Optional[dict] = None,
) -> dict:
    """Evaluate a carrier's safety trend and determine alert status.

    Flags carriers that meet any of these criteria:
      - Composite score increased by >= alert_threshold points
      - Multiple violation categories worsening simultaneously
      - OOS rate above 30%
      - Recent accident count > 0
    """
    alerts = []
    score_delta = scores["score_delta"]
    current = scores["current"]

    # Check composite score deterioration
    if score_delta >= alert_threshold:
        alerts.append(f"Composite score worsened by {score_delta} points (threshold: {alert_threshold})")

    # Check multiple violation categories worsening
    worsening_categories = []
    if scores["avg_violations_delta"] > 0:
        worsening_categories.append("violations_per_inspection")
    if scores["oos_rate_delta"] > 5:
        worsening_categories.append("oos_rate")
    if current["unsafe_driving_violations"] > 0:
        worsening_categories.append("unsafe_driving")
    if current["hos_violations"] > 0:
        worsening_categories.append("hours_of_service")
    if current["hazmat_violations"] > 0:
        worsening_categories.append("hazmat")

    if len(worsening_categories) >= 3:
        alerts.append(f"Multiple violation categories flagged: {', '.join(worsening_categories)}")

    # High OOS rate
    if current["oos_rate"] > 30:
        alerts.append(f"High OOS rate: {current['oos_rate']}%")

    # Recent accidents
    if current["accident_count"] > 0:
        alerts.append(f"Recent accidents: {current['accident_count']}")

    # Determine risk level
    if score_delta >= alert_threshold * 2 or (current["oos_rate"] > 50 and current["accident_count"] > 0):
        risk_level = "CRITICAL"
    elif alerts:
        risk_level = "HIGH"
    elif score_delta > 0:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    # Build carrier info
    name = "Unknown"
    phone = ""
    address = ""
    if carrier_details:
        name = carrier_details.get("legalName") or carrier_details.get("legal_name", "Unknown")
        phone = carrier_details.get("phoneNumber") or carrier_details.get("phone", "")
        city = carrier_details.get("phyCity", "")
        state = carrier_details.get("phyState", "")
        if city and state:
            address = f"{city}, {state}"

    return {
        "dot_number": dot_number,
        "carrier_name": name,
        "phone": phone,
        "address": address,
        "risk_level": risk_level,
        "current_composite_score": scores["current_composite_score"],
        "historical_composite_score": scores["historical_composite_score"],
        "score_change": score_delta,
        "current_inspections": current["total_inspections"],
        "current_violations": current["total_violations"],
        "oos_rate": current["oos_rate"],
        "accident_count": current["accident_count"],
        "avg_violations_delta": scores["avg_violations_delta"],
        "oos_rate_delta": scores["oos_rate_delta"],
        "alerts": alerts,
        "needs_insurance_review": risk_level in ("HIGH", "CRITICAL"),
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
    }


def format_csv(results: list[dict]) -> str:
    """Format results as CSV."""
    if not results:
        return ""
    output = io.StringIO()
    fields = [
        "dot_number", "carrier_name", "risk_level", "score_change",
        "current_composite_score", "historical_composite_score",
        "current_inspections", "current_violations", "oos_rate",
        "accident_count", "needs_insurance_review", "alerts",
        "phone", "address", "evaluated_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for r in results:
        row = dict(r)
        row["alerts"] = "; ".join(r.get("alerts", []))
        writer.writerow(row)
    return output.getvalue()


def format_json(results: list[dict]) -> str:
    """Format results as JSON."""
    return json.dumps(results, indent=2, default=str)


def format_markdown(results: list[dict]) -> str:
    """Format results as a Markdown table with alert details."""
    if not results:
        return "No carriers flagged.\n"

    lines = [
        "# FMCSA SMS Safety Monitor Report",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Summary",
        f"- Carriers evaluated: {len(results)}",
        f"- Needing insurance review: {sum(1 for r in results if r['needs_insurance_review'])}",
        f"- Critical risk: {sum(1 for r in results if r['risk_level'] == 'CRITICAL')}",
        f"- High risk: {sum(1 for r in results if r['risk_level'] == 'HIGH')}",
        "",
        "## Carrier Details",
        "",
        "| DOT# | Carrier | Risk | Score Change | OOS% | Accidents | Review? |",
        "|------|---------|------|-------------|------|-----------|---------|",
    ]

    for r in results:
        review = "YES" if r["needs_insurance_review"] else "no"
        lines.append(
            f"| {r['dot_number']} | {r['carrier_name'][:30]} | {r['risk_level']} "
            f"| {r['score_change']:+.1f} | {r['oos_rate']}% | {r['accident_count']} | {review} |"
        )

    # Alert details for flagged carriers
    flagged = [r for r in results if r["alerts"]]
    if flagged:
        lines.extend(["", "## Alerts"])
        for r in flagged:
            lines.append(f"\n### DOT {r['dot_number']} — {r['carrier_name']}")
            lines.append(f"- Risk level: **{r['risk_level']}**")
            for alert in r["alerts"]:
                lines.append(f"- {alert}")
            if r["phone"]:
                lines.append(f"- Phone: {r['phone']}")
            if r["address"]:
                lines.append(f"- Location: {r['address']}")

    lines.append("")
    return "\n".join(lines)


def run_monitor(args: argparse.Namespace) -> list[dict]:
    """Main monitoring logic: fetch data, compute scores, evaluate carriers."""
    client = SocrataClient(api_key=args.api_key)

    # Determine carrier list
    dot_numbers = []
    csv_source = args.csv_file or args.carrier_list

    if csv_source and csv_source.lower() != "auto":
        dot_numbers = load_carrier_list_from_csv(csv_source)
    elif csv_source and csv_source.lower() == "auto":
        logger.info("Auto-fetching carriers from API...")
        records = client.fetch_recent_carriers(
            days_back=args.monitor_interval, limit=args.limit
        )
        seen = set()
        for rec in records:
            dot = rec.get("dot_number", "").strip()
            if dot and dot not in seen:
                dot_numbers.append(dot)
                seen.add(dot)
        logger.info("Found %d unique carriers via auto-fetch", len(dot_numbers))
    else:
        logger.error("Provide --carrier-list or --csv-file with DOT numbers.")
        sys.exit(1)

    if not dot_numbers:
        logger.warning("No carriers to monitor.")
        return []

    results = []
    for i, dot in enumerate(dot_numbers, 1):
        logger.info("Processing carrier %d/%d: DOT %s", i, len(dot_numbers), dot)

        try:
            inspections = client.fetch_carrier_inspections(dot)
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to fetch data for DOT %s: %s", dot, exc)
            continue

        if not inspections:
            logger.info("No inspection records found for DOT %s, skipping", dot)
            continue

        scores = compute_safety_scores(inspections, args.monitor_interval)

        # Try to get carrier details
        carrier_details = None
        if inspections:
            # Use name from inspection data if available
            carrier_details = {
                "legal_name": inspections[0].get("legal_name", "Unknown"),
            }
            # Optionally fetch richer details
            try:
                full_details = client.fetch_carrier_details(dot)
                if full_details:
                    carrier_details.update(full_details)
            except Exception:
                pass

        result = evaluate_carrier(dot, scores, args.alert_threshold, carrier_details)
        results.append(result)

        # Brief pause to avoid hammering the API
        if i < len(dot_numbers):
            time.sleep(0.3)

    # Sort by risk: CRITICAL first, then HIGH, then by score_change descending
    risk_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3}
    results.sort(key=lambda r: (risk_order.get(r["risk_level"], 9), -r["score_change"]))

    return results


def main():
    """Entry point: parse args, run monitor, format and output results."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("FMCSA SMS Safety Monitor starting")
    logger.info(
        "Alert threshold: %.1f points | Monitor interval: %d days | Format: %s",
        args.alert_threshold, args.monitor_interval, args.output_format,
    )

    results = run_monitor(args)

    # Format output
    if args.output_format == "csv":
        output = format_csv(results)
    elif args.output_format == "markdown":
        output = format_markdown(results)
    else:
        output = format_json(results)

    # Write or print
    if args.output_file:
        Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_file).write_text(output, encoding="utf-8")
        logger.info("Results written to %s", args.output_file)
    else:
        print(output)

    # Summary
    flagged = [r for r in results if r["needs_insurance_review"]]
    logger.info(
        "Done. %d carriers evaluated, %d flagged for insurance review.",
        len(results), len(flagged),
    )
    if flagged:
        logger.info("Flagged carriers: %s", ", ".join(r["dot_number"] for r in flagged))


if __name__ == "__main__":
    main()
