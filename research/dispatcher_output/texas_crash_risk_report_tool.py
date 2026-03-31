#!/usr/bin/env python3
"""
FMCSA Crash Risk Report Tool

Queries the FMCSA Socrata API (Company Census) for motor carriers filtered by
state, fleet size, and active status, then scrapes each carrier's SAFER detail
page for crash history, insurance, and authority data.  Produces a per-carrier
Markdown risk report suitable for sales prospecting.

Usage examples:
    python texas_crash_risk_report_tool.py
    python texas_crash_risk_report_tool.py --state TX --min-fleet-size 1 --max-fleet-size 5 --limit 50
    python texas_crash_risk_report_tool.py --output-dir ./reports --limit 10
"""

import argparse
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The correct FMCSA Company Census dataset on data.transportation.gov
SOCRATA_BASE = "https://data.transportation.gov/resource/az4n-8mr2.json"

# SAFER company snapshot (HTML)
SAFER_SNAPSHOT_URL = "https://safer.fmcsa.dot.gov/query.asp"

# Request settings
REQUEST_TIMEOUT = 30
SAFER_DELAY = 2  # polite delay between SAFER page fetches (seconds)

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

logger = logging.getLogger("crash_risk_tool")


# ---------------------------------------------------------------------------
# Socrata query
# ---------------------------------------------------------------------------

def build_soql_where(state: str, min_fleet: int, max_fleet: int) -> str:
    """Build the SoQL $where clause for the census dataset.

    Note: The census dataset does NOT contain crash columns.  Crash data is
    obtained separately from the SAFER website.  The query here filters only
    by state and fleet (power_units) range.
    """
    return (
        f"phy_state='{state.upper()}' "
        f"AND power_units>={min_fleet} "
        f"AND power_units<={max_fleet} "
        f"AND status_code='A'"
    )


def query_carriers(state: str, min_fleet: int, max_fleet: int, limit: int) -> list[dict]:
    """Fetch carrier records from the FMCSA Socrata Census API.

    Args:
        state: Two-letter state abbreviation.
        min_fleet: Minimum power units (inclusive).
        max_fleet: Maximum power units (inclusive).
        limit: Max number of records to return.

    Returns:
        List of carrier dicts from the API.
    """
    where = build_soql_where(state, min_fleet, max_fleet)
    params = {
        "$where": where,
        "$limit": limit,
        "$order": "add_date DESC",
    }
    logger.info("Querying Socrata: %s  params=%s", SOCRATA_BASE, params)

    resp = requests.get(SOCRATA_BASE, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    carriers = resp.json()
    logger.info("Received %d carrier records from Socrata.", len(carriers))
    return carriers


# ---------------------------------------------------------------------------
# SAFER scraping helpers
# ---------------------------------------------------------------------------

def fetch_safer_page(dot_number: str) -> Optional[str]:
    """Fetch the SAFER company snapshot HTML for a given DOT number.

    Args:
        dot_number: USDOT number string.

    Returns:
        Raw HTML string, or None on failure.
    """
    params = {
        "searchtype": "ANY",
        "query_type": "queryCarrierSnapshot",
        "query_param": "USDOT",
        "query_string": dot_number,
    }
    try:
        resp = requests.get(SAFER_SNAPSHOT_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        logger.warning("Failed to fetch SAFER page for DOT %s: %s", dot_number, exc)
        return None


def _extract_between(html: str, before: str, after: str) -> str:
    """Return text between two marker strings, stripped."""
    idx = html.find(before)
    if idx == -1:
        return ""
    start = idx + len(before)
    end = html.find(after, start)
    if end == -1:
        return ""
    return html[start:end].strip()


def _strip_tags(html_fragment: str) -> str:
    """Crudely remove HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", html_fragment)
    text = re.sub(r"&nbsp;?", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_safer_html(html: str) -> dict[str, Any]:
    """Parse key fields from a SAFER company snapshot page.

    Extracts MC number, insurance status, crash counts, inspections, and
    out-of-service information.

    Args:
        html: Raw HTML from SAFER.

    Returns:
        Dict of parsed fields.
    """
    data: dict[str, Any] = {}

    # MC / MX / FF number
    mc_match = re.search(r"MC[-/]?MX[-/]?FF\s*Number[^:]*:\s*</?\w[^>]*>\s*(\d+)", html)
    if not mc_match:
        mc_match = re.search(r"MC\s*Number[^:]*:\s*</?\w[^>]*>\s*(\d+)", html)
    if not mc_match:
        mc_match = re.search(r"MC-?\s*(\d{4,})", html)
    data["mc_number"] = mc_match.group(1) if mc_match else "N/A"

    # Insurance — look for BIPD required / on-file
    ins_section = _extract_between(html, "Insurance", "Crash")
    if ins_section:
        bipd = re.findall(r"BIPD.*?(\$[\d,]+)", ins_section)
        data["insurance_bipd_on_file"] = bipd[0] if bipd else "N/A"
        data["insurance_status"] = "On File" if bipd else "Unknown"
    else:
        data["insurance_bipd_on_file"] = "N/A"
        data["insurance_status"] = "Unknown"

    # Crash information table — look for Tow / Injury / Fatal / Total
    crash_section = _extract_between(html, "Crash Information", "Safety Rating")
    if not crash_section:
        crash_section = _extract_between(html, "Crash Information", "Inspection")
    crash_nums = re.findall(r"(\d+)", crash_section)
    if len(crash_nums) >= 4:
        data["crashes_fatal"] = int(crash_nums[0])
        data["crashes_injury"] = int(crash_nums[1])
        data["crashes_tow"] = int(crash_nums[2])
        data["crashes_total"] = int(crash_nums[3])
    elif len(crash_nums) >= 1:
        data["crashes_total"] = int(crash_nums[-1])
        data["crashes_fatal"] = 0
        data["crashes_injury"] = 0
        data["crashes_tow"] = 0
    else:
        data["crashes_total"] = 0
        data["crashes_fatal"] = 0
        data["crashes_injury"] = 0
        data["crashes_tow"] = 0

    # Inspection totals
    insp_section = _extract_between(html, "Inspection", "Out of Service")
    if not insp_section:
        insp_section = _extract_between(html, "Inspection", "</table>")
    insp_nums = re.findall(r"(\d+)", insp_section)
    data["inspections_total"] = int(insp_nums[0]) if insp_nums else 0

    # Out-of-service rate
    oos_match = re.search(r"Out\s*of\s*Service\s*%.*?(\d+\.?\d*)\s*%", html, re.IGNORECASE)
    data["oos_rate"] = f"{oos_match.group(1)}%" if oos_match else "N/A"

    # Operating status
    status_match = re.search(r"Operating\s*Status[^:]*:\s*</?\w[^>]*>\s*(\w[\w\s]*)", html)
    data["operating_status"] = _strip_tags(status_match.group(1)) if status_match else "N/A"

    return data


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def assess_risk(carrier: dict, safer: dict) -> tuple[str, list[str]]:
    """Produce a risk level and list of risk factors.

    Args:
        carrier: Census API record.
        safer: Parsed SAFER data.

    Returns:
        (risk_level, [risk_factors])
    """
    factors: list[str] = []
    score = 0

    total_crashes = safer.get("crashes_total", 0)
    if total_crashes >= 3:
        factors.append(f"High crash count ({total_crashes} in 24 months)")
        score += 3
    elif total_crashes >= 1:
        factors.append(f"Has {total_crashes} crash(es) in 24 months")
        score += 1

    if safer.get("crashes_fatal", 0) > 0:
        factors.append(f"Fatal crash(es): {safer['crashes_fatal']}")
        score += 3

    if safer.get("crashes_injury", 0) > 0:
        factors.append(f"Injury crash(es): {safer['crashes_injury']}")
        score += 2

    fleet = int(carrier.get("power_units", 0))
    if fleet <= 3 and total_crashes >= 1:
        factors.append(f"Small fleet ({fleet} units) with crash history — higher per-unit risk")
        score += 1

    if safer.get("insurance_status") != "On File":
        factors.append("Insurance status not confirmed on file")
        score += 1

    oos = safer.get("oos_rate", "N/A")
    if oos not in ("N/A", "0%", "0.0%"):
        factors.append(f"Out-of-service rate: {oos}")
        score += 1

    if score >= 5:
        level = "HIGH"
    elif score >= 2:
        level = "MODERATE"
    else:
        level = "LOW"

    return level, factors


def build_sales_angles(carrier: dict, safer: dict, risk_level: str) -> list[str]:
    """Generate sales angle recommendations based on carrier profile.

    Args:
        carrier: Census API record.
        safer: Parsed SAFER data.
        risk_level: HIGH / MODERATE / LOW.

    Returns:
        List of sales recommendation strings.
    """
    angles: list[str] = []
    fleet = int(carrier.get("power_units", 0))
    total_crashes = safer.get("crashes_total", 0)

    if total_crashes >= 1:
        angles.append(
            "Crash history creates urgency — carrier may face premium increases "
            "or non-renewal. Lead with rate comparison."
        )

    if risk_level == "HIGH":
        angles.append(
            "High-risk profile. Position as a specialist who can place "
            "hard-to-insure fleets. Emphasize claims advocacy."
        )

    if fleet <= 3:
        angles.append(
            "Micro-fleet owner likely wears many hats. Keep pitch concise, "
            "emphasize time savings and bundled coverage."
        )

    if safer.get("insurance_status") != "On File":
        angles.append(
            "Insurance not confirmed on SAFER — possible lapse or new authority. "
            "Offer to help get compliant quickly."
        )

    if safer.get("crashes_fatal", 0) > 0 or safer.get("crashes_injury", 0) > 0:
        angles.append(
            "Serious crash on record. Carrier likely shopping or being dropped. "
            "Time-sensitive opportunity."
        )

    if not angles:
        angles.append(
            "Clean profile — compete on price and service. Highlight proactive "
            "safety resources to differentiate."
        )

    return angles


def generate_report(carrier: dict, safer: dict, output_dir: Path) -> Path:
    """Write a Markdown risk report for a single carrier.

    Args:
        carrier: Census API record.
        safer: Parsed SAFER data.
        output_dir: Directory to write the .md file into.

    Returns:
        Path to the written report file.
    """
    dot = carrier.get("dot_number", "unknown")
    name = carrier.get("legal_name", "Unknown Carrier")
    dba = carrier.get("dba_name", "")
    fleet = carrier.get("power_units", "N/A")
    phone = carrier.get("phone", "N/A")
    email = carrier.get("email_address", "N/A")
    phy_street = carrier.get("phy_street", "")
    phy_city = carrier.get("phy_city", "")
    phy_state = carrier.get("phy_state", "")
    phy_zip = carrier.get("phy_zip", "")
    address = f"{phy_street}, {phy_city}, {phy_state} {phy_zip}".strip(", ")

    risk_level, risk_factors = assess_risk(carrier, safer)
    sales_angles = build_sales_angles(carrier, safer, risk_level)

    now = datetime.now()
    report_date = now.strftime("%Y-%m-%d %H:%M")

    # Crash details
    crashes_total = safer.get("crashes_total", 0)
    crashes_fatal = safer.get("crashes_fatal", 0)
    crashes_injury = safer.get("crashes_injury", 0)
    crashes_tow = safer.get("crashes_tow", 0)

    risk_emoji_map = {"HIGH": "RED", "MODERATE": "YELLOW", "LOW": "GREEN"}
    risk_label = risk_emoji_map.get(risk_level, risk_level)

    md = f"""# Crash Risk Report: {name}

**Report Generated:** {report_date}
**DOT Number:** {dot}

---

## Carrier Profile

| Field | Value |
|---|---|
| **Legal Name** | {name} |
| **DBA** | {dba or 'N/A'} |
| **DOT Number** | {dot} |
| **MC Number** | {safer.get('mc_number', 'N/A')} |
| **Fleet Size (Power Units)** | {fleet} |
| **Operating Status** | {safer.get('operating_status', 'N/A')} |
| **Physical Address** | {address or 'N/A'} |
| **Phone** | {phone} |
| **Email** | {email} |

---

## Insurance Status

| Field | Value |
|---|---|
| **BIPD On File** | {safer.get('insurance_bipd_on_file', 'N/A')} |
| **Insurance Status** | {safer.get('insurance_status', 'Unknown')} |

---

## Crash Risk Assessment

**Risk Level: {risk_level} ({risk_label})**

### Crash History (24-Month Window)

| Category | Count |
|---|---|
| **Fatal Crashes** | {crashes_fatal} |
| **Injury Crashes** | {crashes_injury} |
| **Tow-Away Crashes** | {crashes_tow} |
| **Total Crashes** | {crashes_total} |

### Inspection Summary

| Field | Value |
|---|---|
| **Total Inspections** | {safer.get('inspections_total', 'N/A')} |
| **Out-of-Service Rate** | {safer.get('oos_rate', 'N/A')} |

### Risk Factors

"""
    if risk_factors:
        for f in risk_factors:
            md += f"- {f}\n"
    else:
        md += "- No significant risk factors identified.\n"

    md += """
---

## Sales Angle Recommendations

"""
    for i, angle in enumerate(sales_angles, 1):
        md += f"{i}. {angle}\n"

    md += f"""
---

## Contact Information

- **Phone:** {phone}
- **Email:** {email}
- **Address:** {address or 'N/A'}
- **SAFER Link:** https://safer.fmcsa.dot.gov/query.asp?searchtype=ANY&query_type=queryCarrierSnapshot&query_param=USDOT&query_string={dot}

---

*Generated by FMCSA Crash Risk Report Tool — {report_date}*
"""

    safe_name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")[:60]
    filename = f"DOT_{dot}_{safe_name}.md"
    filepath = output_dir / filename
    filepath.write_text(md, encoding="utf-8")
    logger.info("Report written: %s", filepath)
    return filepath


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> None:
    """Execute the full pipeline: query, enrich, filter, report.

    Args:
        args: Parsed CLI arguments.
    """
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1 — Query Socrata for carrier census records
    carriers = query_carriers(
        state=args.state,
        min_fleet=args.min_fleet_size,
        max_fleet=args.max_fleet_size,
        limit=args.limit,
    )

    if not carriers:
        logger.warning("No carriers returned from Socrata. Check filters.")
        return

    # Step 2 — Enrich each carrier via SAFER and generate reports
    reports_written = 0
    carriers_with_crashes = 0

    for i, carrier in enumerate(carriers, 1):
        dot = carrier.get("dot_number", "")
        name = carrier.get("legal_name", "Unknown")
        logger.info("[%d/%d] Processing DOT %s — %s", i, len(carriers), dot, name)

        if not dot:
            logger.warning("  Skipping carrier with missing DOT number.")
            continue

        html = fetch_safer_page(dot)
        if not html:
            logger.warning("  Could not fetch SAFER page; skipping.")
            continue

        safer = parse_safer_html(html)

        # Filter: only produce reports for carriers with at least 1 crash
        if safer.get("crashes_total", 0) < 1:
            logger.info("  No crashes found on SAFER; skipping report.")
        else:
            carriers_with_crashes += 1
            report_path = generate_report(carrier, safer, output_dir)
            reports_written += 1
            logger.info("  -> %s (crashes=%d)", report_path.name, safer["crashes_total"])

        # Be polite to SAFER
        if i < len(carriers):
            time.sleep(SAFER_DELAY)

    # Summary
    logger.info(
        "Done. %d carriers queried, %d had crashes, %d reports written to %s",
        len(carriers),
        carriers_with_crashes,
        reports_written,
        output_dir,
    )

    # Write a summary index file
    summary_path = output_dir / "00_SUMMARY.md"
    summary_path.write_text(
        f"# Crash Risk Report Summary\n\n"
        f"- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"- **State:** {args.state}\n"
        f"- **Fleet Size Range:** {args.min_fleet_size}–{args.max_fleet_size} power units\n"
        f"- **Carriers Queried:** {len(carriers)}\n"
        f"- **Carriers With Crashes:** {carriers_with_crashes}\n"
        f"- **Reports Generated:** {reports_written}\n"
        f"- **Output Directory:** `{output_dir}`\n",
        encoding="utf-8",
    )
    logger.info("Summary index written to %s", summary_path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional list of argument strings (defaults to sys.argv[1:]).

    Returns:
        Parsed argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description="FMCSA Crash Risk Report Tool — identify small-fleet carriers with crash history.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --state TX --limit 50\n"
            "  %(prog)s --state CA --min-fleet-size 1 --max-fleet-size 10 --limit 100\n"
            "  %(prog)s --output-dir ./my_reports\n"
        ),
    )
    parser.add_argument(
        "--state",
        default="TX",
        help="Two-letter state abbreviation (default: TX)",
    )
    parser.add_argument(
        "--min-fleet-size",
        type=int,
        default=1,
        help="Minimum power units (default: 1)",
    )
    parser.add_argument(
        "--max-fleet-size",
        type=int,
        default=5,
        help="Maximum power units (default: 5)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max number of carriers to query from Socrata (default: 50)",
    )
    parser.add_argument(
        "--output-dir",
        default="./crash_risk_reports",
        help="Directory to write reports into (default: ./crash_risk_reports)",
    )
    return parser.parse_args(argv)


def main() -> None:
    """Entry point."""
    args = parse_args()

    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logger.setLevel(logging.INFO)

    logger.info(
        "Starting FMCSA Crash Risk Report Tool — state=%s fleet=%d-%d limit=%d",
        args.state,
        args.min_fleet_size,
        args.max_fleet_size,
        args.limit,
    )

    try:
        run(args)
    except requests.HTTPError as exc:
        logger.error("HTTP error from API: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
