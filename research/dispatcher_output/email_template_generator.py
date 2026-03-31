#!/usr/bin/env python3
"""
Trucking Insurance Cold Email Template Generator

Generates personalized cold email templates for trucking insurance sales
by querying FMCSA carrier data from data.transportation.gov and tailoring
the pitch based on fleet size, operating region, and insurance status.

Usage Examples:
    # Basic usage with company name and region
    ./email_template_generator.py --company "ABC Trucking" --region TX

    # With DOT number for personalized data lookup
    ./email_template_generator.py --company "ABC Trucking" --dot 123456 --region TX

    # Save output to a file
    ./email_template_generator.py --company "ABC Trucking" --dot 123456 --region CA --output email.txt
"""

import argparse
import json
import sys
import textwrap
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

FMCSA_API_URL = "https://data.transportation.gov/resource/az4b-hbig.json"

REGION_REFERENCES = {
    "AL": ("Alabama", "I-65 corridor", "Port of Mobile freight lanes"),
    "AK": ("Alaska", "Alaska Highway routes", "Anchorage distribution hub"),
    "AZ": ("Arizona", "I-10 and I-40 corridors", "Phoenix metro freight zones"),
    "AR": ("Arkansas", "I-30 and I-40 interchange", "Northwest Arkansas logistics hub"),
    "CA": ("California", "I-5 and I-10 corridors", "Port of Long Beach and LA freight lanes"),
    "CO": ("Colorado", "I-25 and I-70 corridors", "Front Range distribution network"),
    "CT": ("Connecticut", "I-95 Northeast corridor", "Hartford logistics hub"),
    "DE": ("Delaware", "I-95 Mid-Atlantic corridor", "Port of Wilmington freight lanes"),
    "FL": ("Florida", "I-95 and I-75 corridors", "Port of Jacksonville and Miami freight lanes"),
    "GA": ("Georgia", "I-75 and I-85 corridors", "Port of Savannah freight lanes"),
    "HI": ("Hawaii", "inter-island freight", "Honolulu port operations"),
    "ID": ("Idaho", "I-84 and I-90 corridors", "Boise distribution hub"),
    "IL": ("Illinois", "I-80 and I-55 corridors", "Chicago intermodal hub"),
    "IN": ("Indiana", "I-65 and I-70 crossroads", "Indianapolis logistics hub"),
    "IA": ("Iowa", "I-80 and I-35 corridors", "Des Moines distribution center"),
    "KS": ("Kansas", "I-70 and I-35 corridors", "Kansas City freight hub"),
    "KY": ("Kentucky", "I-65 and I-75 corridors", "Louisville logistics hub"),
    "LA": ("Louisiana", "I-10 and I-20 corridors", "Port of New Orleans freight lanes"),
    "ME": ("Maine", "I-95 Northern corridor", "Portland distribution hub"),
    "MD": ("Maryland", "I-95 and I-70 corridors", "Port of Baltimore freight lanes"),
    "MA": ("Massachusetts", "I-90 and I-95 corridors", "Boston metro freight zones"),
    "MI": ("Michigan", "I-94 and I-75 corridors", "Detroit automotive freight lanes"),
    "MN": ("Minnesota", "I-94 and I-35 corridors", "Twin Cities distribution hub"),
    "MS": ("Mississippi", "I-55 and I-20 corridors", "Gulfport port freight lanes"),
    "MO": ("Missouri", "I-70 and I-44 corridors", "St. Louis and KC freight hubs"),
    "MT": ("Montana", "I-90 and I-15 corridors", "Billings distribution hub"),
    "NE": ("Nebraska", "I-80 corridor", "Omaha logistics hub"),
    "NV": ("Nevada", "I-80 and I-15 corridors", "Reno-Las Vegas freight lanes"),
    "NH": ("New Hampshire", "I-93 and I-89 corridors", "Manchester distribution hub"),
    "NJ": ("New Jersey", "I-95 and NJ Turnpike corridors", "Port Newark freight lanes"),
    "NM": ("New Mexico", "I-25 and I-40 corridors", "Albuquerque distribution hub"),
    "NY": ("New York", "I-87 and I-90 corridors", "Port of New York freight lanes"),
    "NC": ("North Carolina", "I-85 and I-40 corridors", "Charlotte logistics hub"),
    "ND": ("North Dakota", "I-94 and I-29 corridors", "Fargo distribution hub"),
    "OH": ("Ohio", "I-71 and I-75 corridors", "Columbus logistics hub"),
    "OK": ("Oklahoma", "I-35 and I-40 corridors", "Oklahoma City freight hub"),
    "OR": ("Oregon", "I-5 and I-84 corridors", "Port of Portland freight lanes"),
    "PA": ("Pennsylvania", "I-76 and I-81 corridors", "Philadelphia and Pittsburgh freight hubs"),
    "RI": ("Rhode Island", "I-95 corridor", "Providence port operations"),
    "SC": ("South Carolina", "I-26 and I-95 corridors", "Port of Charleston freight lanes"),
    "SD": ("South Dakota", "I-90 and I-29 corridors", "Sioux Falls distribution hub"),
    "TN": ("Tennessee", "I-40 and I-65 corridors", "Memphis logistics hub"),
    "TX": ("Texas", "I-35 and I-10 corridors", "DFW, Houston, and Laredo freight hubs"),
    "UT": ("Utah", "I-15 and I-80 corridors", "Salt Lake City distribution hub"),
    "VT": ("Vermont", "I-89 and I-91 corridors", "Burlington distribution hub"),
    "VA": ("Virginia", "I-81 and I-95 corridors", "Port of Virginia freight lanes"),
    "WA": ("Washington", "I-5 and I-90 corridors", "Port of Seattle and Tacoma freight lanes"),
    "WV": ("West Virginia", "I-77 and I-64 corridors", "Charleston logistics hub"),
    "WI": ("Wisconsin", "I-94 and I-43 corridors", "Milwaukee distribution hub"),
    "WY": ("Wyoming", "I-80 and I-25 corridors", "Cheyenne logistics hub"),
}


def parse_args():
    """Parse and validate command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="email_template_generator",
        description="Generate personalized cold email templates for trucking insurance sales.",
        epilog=textwrap.dedent("""\
            examples:
              %(prog)s --company "ABC Trucking" --region TX
              %(prog)s --company "ABC Trucking" --dot 123456 --region TX
              %(prog)s --company "ABC Trucking" --dot 123456 --region CA --output email.txt
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--company", required=True, help="Company name for the email recipient"
    )
    parser.add_argument(
        "--dot", type=str, default=None, help="USDOT number for FMCSA carrier data lookup (optional)"
    )
    parser.add_argument(
        "--region", required=True, help="Two-letter state code (e.g., TX, CA, FL)"
    )
    parser.add_argument(
        "--output", type=str, default=None, help="File path to save the generated email template"
    )
    args = parser.parse_args()

    args.region = args.region.upper()
    if len(args.region) != 2 or not args.region.isalpha():
        parser.error(f"Region must be a two-letter state code, got: '{args.region}'")

    if args.dot is not None:
        if not args.dot.isdigit():
            parser.error(f"DOT number must be numeric, got: '{args.dot}'")

    return args


def fetch_carrier_data(dot_number):
    """Fetch carrier details from FMCSA via data.transportation.gov.

    Args:
        dot_number: The USDOT number to query.

    Returns:
        A dict with carrier details, or None if not found.

    Raises:
        SystemExit: On network errors or unexpected API failures.
    """
    url = f"{FMCSA_API_URL}?dot_number={dot_number}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"Error: Unable to connect to FMCSA API. Check your internet connection.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"Error: FMCSA API request timed out. Try again later.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"Error: FMCSA API returned HTTP {resp.status_code}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("Error: Could not parse FMCSA API response.", file=sys.stderr)
        sys.exit(1)

    if not data:
        print(f"Warning: No carrier found for DOT# {dot_number}. Generating generic template.", file=sys.stderr)
        return None

    return data[0]


def classify_fleet_size(carrier_data):
    """Classify fleet size as small, medium, or large based on power units.

    Args:
        carrier_data: Dict of carrier details from the FMCSA API.

    Returns:
        Tuple of (category_str, unit_count_int).
    """
    total = 0
    for field in ("total_power_units", "nbr_power_unit"):
        val = carrier_data.get(field)
        if val is not None:
            try:
                total = int(val)
                break
            except (ValueError, TypeError):
                continue

    if total < 20:
        return ("small", total)
    elif total <= 50:
        return ("medium", total)
    else:
        return ("large", total)


def check_insurance_status(carrier_data):
    """Determine whether the carrier's insurance/MCS-150 appears active or lapsed.

    Args:
        carrier_data: Dict of carrier details from the FMCSA API.

    Returns:
        Tuple of (is_active: bool, status_detail: str).
    """
    mcs150_date = carrier_data.get("mcs_150_form_date") or carrier_data.get("mcs150_date")
    oper_status = (carrier_data.get("carrier_operation") or carrier_data.get("opc_status") or "").upper()

    if oper_status and "NOT AUTH" in oper_status:
        return (False, "operating authority not active")

    if mcs150_date:
        try:
            # Handle various date formats
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d", "%m/%d/%Y"):
                try:
                    dt = datetime.strptime(mcs150_date.split("T")[0] if "T" in mcs150_date else mcs150_date,
                                           fmt if "T" not in mcs150_date else "%Y-%m-%d")
                    days_since = (datetime.now() - dt).days
                    if days_since > 730:  # > 2 years
                        return (False, f"MCS-150 last updated {days_since // 365} years ago")
                    break
                except ValueError:
                    continue
        except Exception:
            pass

    return (True, "appears current")


def get_region_context(region_code):
    """Get region-specific references for email personalization.

    Args:
        region_code: Two-letter state code.

    Returns:
        Tuple of (state_name, corridor_reference, hub_reference).
    """
    return REGION_REFERENCES.get(region_code, (region_code, "major highway corridors", "regional distribution hubs"))


def generate_email(company, region_code, carrier_data=None):
    """Generate a personalized cold email template.

    Args:
        company: Company name string.
        region_code: Two-letter state code.
        carrier_data: Optional dict of FMCSA carrier data.

    Returns:
        The generated email template as a string.
    """
    state_name, corridor, hub = get_region_context(region_code)
    today = datetime.now().strftime("%B %d, %Y")

    # Defaults for when no carrier data is available
    fleet_category = "small"
    fleet_count = 0
    insurance_active = True
    insurance_detail = "unknown"
    legal_name = company

    if carrier_data:
        fleet_category, fleet_count = classify_fleet_size(carrier_data)
        insurance_active, insurance_detail = check_insurance_status(carrier_data)
        legal_name = carrier_data.get("legal_name") or carrier_data.get("dba_name") or company

    # Build subject line
    if not insurance_active:
        subject = f"Compliance Alert: Insurance Coverage Options for {company}"
    elif fleet_category == "small":
        subject = f"Affordable Coverage Designed for Owner-Operators & Small Fleets Like {company}"
    elif fleet_category == "medium":
        subject = f"Scalable Insurance Solutions for Growing Fleets Like {company}"
    else:
        subject = f"Enterprise Fleet Coverage & Risk Management for {company}"

    # Build opening
    opening = f"Dear {company} Team,"

    # Build intro paragraph based on fleet size
    if fleet_category == "small":
        intro = (
            f"As a {'fleet operating ' + str(fleet_count) + ' power units' if fleet_count else 'small fleet'} "
            f"in {state_name}, you know that every dollar counts. Finding the right insurance "
            f"coverage shouldn't mean compromising on protection to stay within budget."
        )
    elif fleet_category == "medium":
        intro = (
            f"With {fleet_count} power units on the road, {company} is in an exciting growth phase. "
            f"Mid-size fleets operating along the {corridor} face unique risks that generic "
            f"insurance packages don't adequately address."
        )
    else:
        intro = (
            f"Managing insurance across a fleet of {fleet_count}+ power units requires a partner "
            f"who understands large-scale operations. With trucks running the {corridor} and "
            f"serving the {hub}, your exposure profile demands specialized attention."
        )

    # Build urgency/insurance paragraph
    if not insurance_active:
        insurance_para = (
            f"Our records indicate that your filing status is: {insurance_detail}. "
            f"Operating without current filings puts your authority and livelihood at risk. "
            f"We specialize in fast-turnaround reinstatement and can often get you compliant "
            f"and back on the road within 24-48 hours."
        )
    else:
        insurance_para = (
            f"Even with current coverage, carriers in {state_name} are seeing rate increases "
            f"of 10-15% at renewal. We work with multiple A-rated underwriters to find competitive "
            f"rates without sacrificing the liability limits you need for the {hub}."
        )

    # Build value proposition based on fleet size
    if fleet_category == "small":
        value_prop = textwrap.dedent("""\
            What we offer small fleets:
            - Competitive primary liability starting at FMCSA minimums ($750K/$1M)
            - Physical damage coverage with flexible deductibles
            - Cargo insurance tailored to your freight types
            - Monthly payment plans with no large upfront deposits""")
    elif fleet_category == "medium":
        value_prop = textwrap.dedent("""\
            What we offer growing fleets:
            - Volume-based pricing that improves as you add units
            - Combined liability, cargo, and physical damage programs
            - Dedicated claims support with fast resolution
            - Driver safety programs that qualify you for premium discounts""")
    else:
        value_prop = textwrap.dedent("""\
            What we offer large fleet operations:
            - Custom risk management programs with loss-control consulting
            - Multi-state filings handled across all operating jurisdictions
            - Aggregate pricing across liability, cargo, physical damage, and excess
            - Dedicated account management with quarterly reviews
            - Workers' compensation and occupational accident coverage""")

    # Build region-specific closer
    closer = (
        f"We work with numerous carriers in the {state_name} market and understand the "
        f"specific challenges of operating along the {corridor}. I'd welcome 15 minutes "
        f"to review your current program and see if we can improve your coverage or pricing."
    )

    cta = (
        "Would any day this week or next work for a quick call? I'm happy to work "
        "around your schedule."
    )

    sign_off = textwrap.dedent("""\
        Best regards,

        [Your Name]
        [Your Title]
        [Company Name]
        [Phone Number]
        [Email Address]""")

    # Assemble the email
    email_parts = [
        f"Subject: {subject}",
        "",
        opening,
        "",
        intro,
        "",
        insurance_para,
        "",
        value_prop,
        "",
        closer,
        "",
        cta,
        "",
        sign_off,
    ]

    template = "\n".join(email_parts)

    # Add metadata footer
    metadata = [
        "",
        "---",
        f"Generated: {today}",
        f"Company: {legal_name}",
        f"Region: {state_name} ({region_code})",
        f"Fleet Size: {fleet_category} ({fleet_count} units)" if fleet_count else f"Fleet Size: {fleet_category} (unknown count)",
        f"Insurance Status: {'Active' if insurance_active else 'LAPSED'} ({insurance_detail})",
    ]
    if carrier_data:
        dot = carrier_data.get("dot_number", "N/A")
        metadata.append(f"DOT#: {dot}")

    template += "\n".join(metadata)
    return template


def main():
    """Main entry point: parse args, fetch data, generate and output email template."""
    args = parse_args()

    carrier_data = None
    if args.dot:
        print(f"Fetching FMCSA data for DOT# {args.dot}...", file=sys.stderr)
        carrier_data = fetch_carrier_data(args.dot)

    email = generate_email(args.company, args.region, carrier_data)

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(email + "\n")
            print(f"Email template saved to {args.output}", file=sys.stderr)
        except IOError as e:
            print(f"Error writing to {args.output}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(email)


if __name__ == "__main__":
    main()
