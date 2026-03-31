#!/usr/bin/env python3
"""
Trucking Insurance Cold Email Template Generator

Generates personalized cold email templates for trucking insurance sales
based on company name, fleet size, and operating region. Optionally fetches
carrier data from the FMCSA SAFER API using a DOT or MC number.

Usage:
    # Basic usage with required arguments:
    python trucking_email_generator.py --company_name "ABC Trucking" --fleet_size 25 --state TX

    # With DOT number lookup (fetches public carrier data from FMCSA):
    python trucking_email_generator.py --company_name "ABC Trucking" --fleet_size 25 --state TX --dot_number 123456

    # Specify MC number and contact name:
    python trucking_email_generator.py --company_name "ABC Trucking" --fleet_size 25 --state TX \
        --mc_number 789012 --contact_name "John Smith"

    # Save output to a file:
    python trucking_email_generator.py --company_name "ABC Trucking" --fleet_size 25 --state TX \
        --output emails.txt

Requirements:
    pip install requests
"""

import argparse
import sys
import textwrap
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    requests = None


# ---------------------------------------------------------------------------
# FMCSA carrier data lookup
# ---------------------------------------------------------------------------

FMCSA_SAFER_URL = "https://safer.fmcsa.dot.gov/query.asp"


def fetch_carrier_data(dot_number: str) -> dict:
    """Fetch public carrier snapshot data from the FMCSA SAFER system.

    Args:
        dot_number: The USDOT number to look up.

    Returns:
        A dict with any carrier details that could be parsed, or an empty dict
        if the lookup failed or the requests library is unavailable.
    """
    if requests is None:
        print("[warning] 'requests' library not installed -- skipping FMCSA lookup.", file=sys.stderr)
        return {}

    try:
        resp = requests.get(
            FMCSA_SAFER_URL,
            params={"searchtype": "ANY", "query_type": "queryCarrierSnapshot", "query_param": "USDOT", "query_string": dot_number},
            timeout=15,
        )
        resp.raise_for_status()
        # The SAFER site returns HTML. We do a best-effort parse for a few fields.
        html = resp.text
        data: dict = {"dot_number": dot_number}

        def _extract(label: str) -> Optional[str]:
            """Pull the first table-cell value that follows *label* in the HTML."""
            idx = html.find(label)
            if idx == -1:
                return None
            # Walk forward to the next <td> content
            td_start = html.find("<td", idx)
            if td_start == -1:
                return None
            content_start = html.find(">", td_start) + 1
            content_end = html.find("</td>", content_start)
            if content_end == -1:
                return None
            raw = html[content_start:content_end].strip()
            # Strip nested tags
            import re
            return re.sub(r"<[^>]+>", "", raw).strip() or None

        for field, label in [
            ("legal_name", "Legal Name"),
            ("dba_name", "DBA Name"),
            ("physical_address", "Physical Address"),
            ("mc_number", "MC/MX/FF"),
            ("power_units", "Power Units"),
            ("drivers", "Drivers"),
            ("operation", "Operation Classification"),
            ("carrier_operation", "Carrier Operation"),
        ]:
            val = _extract(label)
            if val:
                data[field] = val

        return data

    except Exception as exc:
        print(f"[warning] FMCSA lookup failed: {exc}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------
# Coverage recommendation logic
# ---------------------------------------------------------------------------

STATE_RISK_PROFILES: dict[str, dict] = {
    # High-traffic / harsh-weather states get extra recommendations
    "TX": {"risk": "high", "notes": "extreme heat, long haul corridors (I-10, I-35), high accident rates"},
    "CA": {"risk": "high", "notes": "strict emissions regulations, congested metro corridors, wildfire risk"},
    "FL": {"risk": "high", "notes": "hurricane exposure, high uninsured motorist rates, tourist traffic"},
    "IL": {"risk": "medium", "notes": "harsh winters, Chicago metro congestion"},
    "PA": {"risk": "medium", "notes": "winter weather, mountainous terrain on I-80 corridor"},
    "OH": {"risk": "medium", "notes": "lake-effect snow, major crossroads of I-70/I-71"},
    "GA": {"risk": "medium", "notes": "Atlanta metro congestion, summer storms"},
}

DEFAULT_RISK_PROFILE: dict = {"risk": "medium", "notes": "standard operating conditions"}


def build_coverage_recommendations(fleet_size: int, state: str) -> list[str]:
    """Return a list of coverage recommendations tailored to fleet size and state.

    Args:
        fleet_size: Number of power units in the fleet.
        state: Two-letter state abbreviation.

    Returns:
        A list of recommendation strings.
    """
    profile = STATE_RISK_PROFILES.get(state.upper(), DEFAULT_RISK_PROFILE)
    recs: list[str] = []

    # Mandatory baseline
    recs.append("Primary Auto Liability ($1M minimum, $5M recommended for hazmat)")
    recs.append("Physical Damage coverage for owned units")
    recs.append("Motor Truck Cargo insurance")

    if fleet_size >= 10:
        recs.append("Fleet-rated blanket policy (volume discount eligible)")
    if fleet_size >= 50:
        recs.append("Excess / Umbrella liability ($5M+) for large-fleet exposure")
        recs.append("Hired & Non-Owned Auto liability")

    if profile["risk"] == "high":
        recs.append(f"Enhanced Uninsured/Underinsured Motorist coverage (state note: {profile['notes']})")
        recs.append("Downtime / Loss-of-Income coverage")

    recs.append("General Liability for terminal/yard operations")
    recs.append("Workers' Compensation (required in most states)")
    recs.append("Occupational Accident coverage for owner-operators / 1099 drivers")

    return recs


# ---------------------------------------------------------------------------
# Email template definitions
# ---------------------------------------------------------------------------

def _wrap(text: str, width: int = 76) -> str:
    """Wrap text to *width* columns, preserving paragraph breaks."""
    paragraphs = text.split("\n\n")
    wrapped = []
    for para in paragraphs:
        lines = para.strip().splitlines()
        for line in lines:
            wrapped.append(textwrap.fill(line.strip(), width=width))
        wrapped.append("")
    return "\n".join(wrapped).strip()


def template_consultative(ctx: dict) -> str:
    """Template 1 -- Consultative / value-first approach.

    Leads with industry insight and positions the sender as an advisor rather
    than a salesperson.
    """
    recs_block = "\n".join(f"  - {r}" for r in ctx["recommendations"][:5])
    body = f"""\
Subject: {ctx['company_name']} -- Are You Overpaying for Trucking Insurance in {ctx['state']}?

Hi {ctx['contact_name']},

I've been reviewing publicly available safety data for carriers operating
out of {ctx['state']}, and {ctx['company_name']} caught my attention. With a
fleet of {ctx['fleet_size']} power units, you're in a segment where we
consistently find carriers are either over-insured on low-risk lines or
under-insured where it matters most.

DOT #: {ctx['dot_number']}
MC #:  {ctx['mc_number']}

Based on your operating profile, here are a few coverage areas worth
reviewing:

{recs_block}

I'd love to run a no-obligation coverage audit for {ctx['company_name']}.
Most of our clients in the {ctx['fleet_size']}-unit range save 12-18% after
we right-size their program.

Would you have 15 minutes this week for a quick call?

Best regards,
{{{{sender_name}}}}
{{{{sender_title}}}}
{{{{agency_name}}}}
{{{{sender_phone}}}} | {{{{sender_email}}}}
"""
    return _wrap(body)


def template_pain_point(ctx: dict) -> str:
    """Template 2 -- Pain-point / problem-aware approach.

    Highlights common frustrations fleet owners face with insurance.
    """
    recs_block = "\n".join(f"  - {r}" for r in ctx["recommendations"][:4])
    body = f"""\
Subject: Tired of Surprise Premium Hikes? ({ctx['company_name']})

Hi {ctx['contact_name']},

If you're like most {ctx['state']}-based fleet owners I talk to, your
insurance renewal last year came with a number you didn't expect -- and an
explanation that didn't make it any easier to swallow.

Here's the thing: carriers running {ctx['fleet_size']} units often get
lumped into generic rating tiers that don't reflect their actual loss
history or safety record.

DOT #: {ctx['dot_number']}
MC #:  {ctx['mc_number']}

At {{{{agency_name}}}}, we specialize exclusively in trucking insurance.
That means we know which markets reward clean CSA scores, which ones are
flexible on radius, and how to structure a program that keeps your costs
predictable.

Coverage areas we'd review for {ctx['company_name']}:

{recs_block}

Can I send over a quick comparison quote? I just need your current dec
pages and I'll have numbers back within 48 hours.

Talk soon,
{{{{sender_name}}}}
{{{{sender_title}}}}
{{{{agency_name}}}}
{{{{sender_phone}}}} | {{{{sender_email}}}}
"""
    return _wrap(body)


def template_referral_social_proof(ctx: dict) -> str:
    """Template 3 -- Social proof / referral-style approach.

    Uses peer credibility to establish trust.
    """
    peer_size = "mid-size" if ctx["fleet_size"] < 50 else "large"
    recs_block = "\n".join(f"  - {r}" for r in ctx["recommendations"][:4])
    body = f"""\
Subject: How {peer_size} {ctx['state']} fleets are cutting insurance costs in {ctx['year']}

Hi {ctx['contact_name']},

I recently helped a {peer_size} carrier in {ctx['state']} restructure their
insurance program and save over ${{{{savings_amount}}}} annually -- without
reducing coverage limits. They were running a fleet similar in size to
{ctx['company_name']}'s {ctx['fleet_size']} units.

DOT #: {ctx['dot_number']}
MC #:  {ctx['mc_number']}

The key was moving away from a one-size-fits-all policy and building a
program around their actual operations:

{recs_block}

I'd be happy to take a look at {ctx['company_name']}'s current program and
see if there are similar opportunities. No pressure, no obligation -- just
a straightforward review.

Worth a conversation?

Best,
{{{{sender_name}}}}
{{{{sender_title}}}}
{{{{agency_name}}}}
{{{{sender_phone}}}} | {{{{sender_email}}}}
"""
    return _wrap(body)


TEMPLATES = [
    ("Consultative / Value-First", template_consultative),
    ("Pain-Point / Problem-Aware", template_pain_point),
    ("Social Proof / Referral-Style", template_referral_social_proof),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_emails(
    company_name: str,
    fleet_size: int,
    state: str,
    dot_number: str = "{DOT_NUMBER}",
    mc_number: str = "{MC_NUMBER}",
    contact_name: str = "{CONTACT_NAME}",
) -> str:
    """Generate all email template variations and return them as a single string.

    Args:
        company_name: Name of the target carrier.
        fleet_size: Number of power units.
        state: Two-letter state abbreviation.
        dot_number: USDOT number (or placeholder).
        mc_number: MC/MX number (or placeholder).
        contact_name: Name of the person being emailed (or placeholder).

    Returns:
        Formatted string containing all email templates separated by dividers.
    """
    recommendations = build_coverage_recommendations(fleet_size, state)

    ctx = {
        "company_name": company_name,
        "fleet_size": fleet_size,
        "state": state.upper(),
        "dot_number": dot_number,
        "mc_number": mc_number,
        "contact_name": contact_name,
        "recommendations": recommendations,
        "year": datetime.now().year,
    }

    sections: list[str] = []
    sections.append("=" * 76)
    sections.append(f"  Cold Email Templates for: {company_name}")
    sections.append(f"  Fleet Size: {fleet_size} | State: {state.upper()}")
    sections.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    sections.append("=" * 76)

    for i, (name, func) in enumerate(TEMPLATES, 1):
        sections.append(f"\n{'─' * 76}")
        sections.append(f"  TEMPLATE {i}: {name}")
        sections.append(f"{'─' * 76}\n")
        sections.append(func(ctx))

    sections.append(f"\n{'=' * 76}")
    sections.append("  RECOMMENDED COVERAGES (full list)")
    sections.append(f"{'=' * 76}\n")
    for rec in recommendations:
        sections.append(f"  * {rec}")

    sections.append(f"\n{'=' * 76}")
    sections.append("  PLACEHOLDERS TO FILL IN")
    sections.append(f"{'=' * 76}\n")
    placeholders = [
        ("{{sender_name}}", "Your full name"),
        ("{{sender_title}}", "Your job title"),
        ("{{agency_name}}", "Your agency / brokerage name"),
        ("{{sender_phone}}", "Your phone number"),
        ("{{sender_email}}", "Your email address"),
        ("{{savings_amount}}", "Dollar amount saved (Template 3)"),
    ]
    if dot_number == "{DOT_NUMBER}":
        placeholders.insert(0, ("{DOT_NUMBER}", "Carrier's USDOT number"))
    if mc_number == "{MC_NUMBER}":
        placeholders.insert(0, ("{MC_NUMBER}", "Carrier's MC/MX number"))
    if contact_name == "{CONTACT_NAME}":
        placeholders.insert(0, ("{CONTACT_NAME}", "Recipient's name"))

    for ph, desc in placeholders:
        sections.append(f"  {ph:<25s} -- {desc}")

    sections.append("")
    return "\n".join(sections)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate personalized cold email templates for trucking insurance sales.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              %(prog)s --company_name "ABC Trucking" --fleet_size 25 --state TX
              %(prog)s --company_name "ABC Trucking" --fleet_size 25 --state TX --dot_number 123456
              %(prog)s --company_name "ABC Trucking" --fleet_size 25 --state TX --output emails.txt
        """),
    )
    parser.add_argument("--company_name", required=True, help="Target company name")
    parser.add_argument("--fleet_size", required=True, type=int, help="Number of power units")
    parser.add_argument("--state", required=True, help="Two-letter state abbreviation (e.g. TX, CA)")
    parser.add_argument("--dot_number", default=None, help="USDOT number (triggers FMCSA lookup)")
    parser.add_argument("--mc_number", default=None, help="MC/MX number")
    parser.add_argument("--contact_name", default=None, help="Contact person's name")
    parser.add_argument("--output", "-o", default=None, help="Write output to file instead of stdout")
    return parser


def main() -> None:
    """Entry point for CLI execution."""
    parser = build_parser()
    args = parser.parse_args()

    dot_number = args.dot_number or "{DOT_NUMBER}"
    mc_number = args.mc_number or "{MC_NUMBER}"
    contact_name = args.contact_name or "{CONTACT_NAME}"

    # Attempt FMCSA lookup if a DOT number was provided
    if args.dot_number:
        print(f"[info] Looking up DOT# {args.dot_number} on FMCSA SAFER ...", file=sys.stderr)
        carrier = fetch_carrier_data(args.dot_number)
        if carrier:
            print(f"[info] Found carrier data: {carrier.get('legal_name', 'N/A')}", file=sys.stderr)
            mc_number = carrier.get("mc_number", mc_number)
            if carrier.get("power_units"):
                try:
                    fetched_units = int(carrier["power_units"].replace(",", ""))
                    if fetched_units != args.fleet_size:
                        print(
                            f"[info] FMCSA reports {fetched_units} power units "
                            f"(you specified {args.fleet_size}). Using your value.",
                            file=sys.stderr,
                        )
                except ValueError:
                    pass

    output = generate_emails(
        company_name=args.company_name,
        fleet_size=args.fleet_size,
        state=args.state,
        dot_number=dot_number,
        mc_number=mc_number,
        contact_name=contact_name,
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(output + "\n")
        print(f"[info] Emails written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
