#!/usr/bin/env python3
"""Generate personalized cold emails for selling trucking insurance to motor carriers.

Supports three email templates (introduction, follow-up, lapsed-insurance) and
personalizes content based on carrier details including fleet size, operating
region/state, and physical city. Accepts individual carrier details via CLI
flags or batch input via CSV.

Usage examples::

    # Single carrier — all three templates
    python trucking_insurance_email_generator.py \\
        --carrier-name "Big Rig Logistics" --dot-number 1234567 \\
        --mc-number 987654 --fleet-size 25 --state TX \\
        --phys-city "Dallas" --contact-name "Mike Johnson" \\
        --email mike@bigriglogistics.com

    # Batch mode from CSV
    python trucking_insurance_email_generator.py --csv-file carriers.csv

    # Single carrier, specific template, JSON output
    python trucking_insurance_email_generator.py \\
        --carrier-name "Sunrise Transport" --dot-number 7654321 \\
        --fleet-size 8 --state FL --phys-city "Miami" \\
        --output-format json

CSV format (header row required)::

    name,dot_number,fleet_size,state,city,email
    Big Rig Logistics,1234567,25,TX,Dallas,mike@bigrig.com
    Sunrise Transport,7654321,8,FL,Miami,ana@sunrise.com

Exit codes:
    0  Success
    1  Runtime error
    2  Invalid arguments
"""

import argparse
import csv
import json
import logging
import re
import sys
import textwrap
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

STATE_TO_REGION: dict[str, str] = {
    "CT": "Northeast", "DE": "Northeast", "MA": "Northeast", "MD": "Northeast",
    "ME": "Northeast", "NH": "Northeast", "NJ": "Northeast", "NY": "Northeast",
    "PA": "Northeast", "RI": "Northeast", "VT": "Northeast", "DC": "Northeast",
    "AL": "Southeast", "AR": "Southeast", "FL": "Southeast", "GA": "Southeast",
    "KY": "Southeast", "LA": "Southeast", "MS": "Southeast", "NC": "Southeast",
    "SC": "Southeast", "TN": "Southeast", "VA": "Southeast", "WV": "Southeast",
    "IA": "Midwest", "IL": "Midwest", "IN": "Midwest", "KS": "Midwest",
    "MI": "Midwest", "MN": "Midwest", "MO": "Midwest", "ND": "Midwest",
    "NE": "Midwest", "OH": "Midwest", "SD": "Midwest", "WI": "Midwest",
    "AZ": "Southwest", "NM": "Southwest", "OK": "Southwest", "TX": "Southwest",
    "CA": "West", "CO": "West", "HI": "West", "ID": "West", "MT": "West",
    "NV": "West", "OR": "West", "UT": "West", "WA": "West", "WY": "West",
    "AK": "West",
}

STATE_NAMES: dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}


@dataclass
class CarrierInfo:
    """Motor carrier details used to personalize email templates."""

    carrier_name: str
    dot_number: str
    mc_number: str
    fleet_size: int
    state: str
    phys_city: str
    contact_name: str
    email: str

    @property
    def region(self) -> str:
        """Operating region derived from state abbreviation."""
        return STATE_TO_REGION.get(self.state.upper(), "National")

    @property
    def state_name(self) -> str:
        """Full state name from abbreviation."""
        return STATE_NAMES.get(self.state.upper(), self.state)

    @property
    def fleet_tier(self) -> str:
        """Classify fleet as small, mid-size, or large."""
        if self.fleet_size <= 10:
            return "small"
        if self.fleet_size <= 50:
            return "mid-size"
        return "large"

    @property
    def first_name(self) -> str:
        """Extract first name from contact name, or fallback greeting."""
        return self.contact_name.strip().split()[0] if self.contact_name.strip() else "there"

    @property
    def location(self) -> str:
        """City, State display string."""
        if self.phys_city:
            return f"{self.phys_city}, {self.state}"
        return self.state_name

    @property
    def safe_filename(self) -> str:
        """Generate a filesystem-safe version of the carrier name."""
        return re.sub(r"[^\w\-]", "_", self.carrier_name.strip()).strip("_")

    @property
    def authority_line(self) -> str:
        """Format DOT/MC number line for emails."""
        parts = [f"DOT# {self.dot_number}"]
        if self.mc_number:
            parts.append(f"MC# {self.mc_number}")
        return ", ".join(parts)


# ---------------------------------------------------------------------------
# Region-specific content
# ---------------------------------------------------------------------------

REGION_RISKS: dict[str, dict[str, str]] = {
    "Northeast": {
        "weather": "harsh winter conditions, ice-related claims, and pothole damage",
        "regulation": "strict state-level DOT enforcement along the I-95 corridor",
        "tip": (
            "Many Northeast carriers overlook seasonal layup credits that can "
            "cut premiums during low-mileage winter months."
        ),
    },
    "Southeast": {
        "weather": "hurricane season exposure, flood-zone routing, and high heat",
        "regulation": "increased weigh-station enforcement across the I-10/I-75 network",
        "tip": (
            "Florida and Georgia have seen double-digit rate increases — "
            "carriers who bundle cargo and liability early lock in better terms."
        ),
    },
    "Midwest": {
        "weather": "tornado-alley exposure, spring flooding, and ice storms",
        "regulation": "cross-state compliance across varying DOT requirements",
        "tip": (
            "Midwest fleets running ag commodities often qualify for specialized "
            "cargo programs that general brokers miss."
        ),
    },
    "Southwest": {
        "weather": "extreme heat breakdowns, tire blowouts, and wildfire detour risks",
        "regulation": "FMCSA border-crossing compliance for cross-border lanes",
        "tip": (
            "Heat-related tire blowouts are the #1 preventable claim in AZ, TX, and "
            "NM — telematics discounts can offset that risk."
        ),
    },
    "West": {
        "weather": "mountain-pass closures, wildfire smoke, and steep-grade risks",
        "regulation": "CARB emissions compliance that ties into insurance eligibility",
        "tip": (
            "California's nuclear verdicts trend makes umbrella/excess coverage "
            "essential for West Coast operators."
        ),
    },
    "National": {
        "weather": "varied climate exposure across multiple operating zones",
        "regulation": "multi-state DOT and FMCSA compliance complexity",
        "tip": (
            "National fleets benefit most from a single-carrier program that "
            "eliminates coverage gaps between state lines."
        ),
    },
}

FLEET_HOOKS: dict[str, str] = {
    "small": (
        "With {fleet_size} power units, you're at the stage where the right insurance "
        "program directly impacts whether you grow profitably or get squeezed by overhead. "
        "Many carriers your size are over-insured on lines they don't need while "
        "under-covered where it matters most."
    ),
    "mid-size": (
        "Managing a {fleet_size}-unit fleet puts you in the sweet spot where insurance "
        "markets compete hardest for your business — but only if you leverage that "
        "position. Most mid-size fleets leave money on the table by staying with the "
        "same broker year after year without benchmarking."
    ),
    "large": (
        "With {fleet_size} power units on the road, your insurance program is one of "
        "your largest operating expenses. At your scale, even modest per-truck savings "
        "compound into significant annual dollars — and risk exposure from coverage "
        "gaps multiplies just as fast."
    ),
}

COVERAGE_BENEFITS: dict[str, list[str]] = {
    "small": [
        "Right-sized coverage that eliminates waste — typical savings of $800–$2,000 per truck annually",
        "Bundled cargo + liability programs designed for fleets under 15 units",
        "Flexible payment plans that match cash-flow cycles for growing operations",
    ],
    "mid-size": [
        "Consolidated single-carrier program replacing fragmented multi-policy setups",
        "Telematics-based discount programs that pay for themselves within 90 days",
        "Competitive umbrella/excess capacity up to $10M without surplus-lines pricing",
    ],
    "large": [
        "Dedicated claims team with trucking-specific adjusters who understand your operations",
        "Custom loss-control programs that directly improve your experience mod",
        "Enterprise risk management integration with your existing fleet safety systems",
    ],
}


# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------


def _generate_introduction(carrier: CarrierInfo) -> str:
    """Generate an introduction cold email for a carrier.

    First-touch email introducing insurance services, personalized with
    fleet size, region, city, and operating risks.

    Args:
        carrier: Motor carrier details.

    Returns:
        Formatted introduction email string.
    """
    region_info = REGION_RISKS.get(carrier.region, REGION_RISKS["National"])
    fleet_hook = FLEET_HOOKS[carrier.fleet_tier].format(fleet_size=carrier.fleet_size)
    benefits = COVERAGE_BENEFITS[carrier.fleet_tier]

    to_line = f"To: {carrier.email}" if carrier.email else "To: {{recipient_email}}"

    return textwrap.dedent(f"""\
        {to_line}
        Subject: Trucking Insurance Review for {carrier.carrier_name} ({carrier.authority_line})

        Hi {carrier.first_name},

        I'm reaching out because I work exclusively with motor carriers in the
        {carrier.region} region, and I noticed {carrier.carrier_name} operating
        out of {carrier.location}.

        {fleet_hook}

        Operating in {carrier.state_name}, your fleet faces specific challenges:
        {region_info['weather']} and {region_info['regulation']} are realities
        that demand coverage built for your exact situation — not a one-size-fits-all
        policy from a generalist broker.

        {region_info['tip']}

        Here's what the right program delivers for a fleet like yours:

        {chr(10).join(f'  • {b}' for b in benefits)}

        I'd love to offer a complimentary 15-minute coverage review. If your current
        program checks out, you'll have peace of mind. If not, you'll know exactly
        where you're exposed before your next renewal.

        Would {{{{preferred_day}}}} work for a quick call?

        Best regards,
        {{{{sender_name}}}}
        {{{{sender_title}}}}
        {{{{sender_phone}}}}
        {{{{sender_email}}}}
    """)


def _generate_follow_up(carrier: CarrierInfo) -> str:
    """Generate a follow-up email for a carrier who hasn't responded.

    Shorter and more direct than the introduction, with a value-driven hook.

    Args:
        carrier: Motor carrier details.

    Returns:
        Formatted follow-up email string.
    """
    region_info = REGION_RISKS.get(carrier.region, REGION_RISKS["National"])

    if carrier.fleet_tier == "small":
        savings_line = (
            "Carriers your size typically save $800–$2,000 per truck annually "
            "when we right-size their coverage."
        )
    elif carrier.fleet_tier == "mid-size":
        savings_line = (
            "Mid-size fleets like yours often save 12–18% by consolidating "
            "fragmented policies into a single program."
        )
    else:
        savings_line = (
            f"For a {carrier.fleet_size}-unit fleet, even a 5% improvement in per-truck "
            "cost translates to six-figure annual savings."
        )

    to_line = f"To: {carrier.email}" if carrier.email else "To: {{recipient_email}}"

    return textwrap.dedent(f"""\
        {to_line}
        Subject: Following up — insurance review for {carrier.carrier_name}

        Hi {carrier.first_name},

        I reached out recently about a complimentary insurance review for
        {carrier.carrier_name} ({carrier.authority_line}). I know how busy
        things get running a {carrier.fleet_size}-truck operation out of
        {carrier.location}, so I wanted to follow up with one quick number:

        {savings_line}

        With {region_info['weather']} affecting {carrier.state_name} carriers,
        the difference between adequate and optimized coverage is real money —
        and real protection when you need it.

        I only need 15 minutes to benchmark your current program. No obligation,
        no pressure — just a clear picture of where you stand.

        Would later this week work?

        Best regards,
        {{{{sender_name}}}}
        {{{{sender_title}}}}
        {{{{sender_phone}}}}
        {{{{sender_email}}}}
    """)


def _generate_lapsed_insurance(carrier: CarrierInfo) -> str:
    """Generate an outreach email for carriers with lapsed or expiring insurance.

    Emphasizes urgency and FMCSA compliance requirements.

    Args:
        carrier: Motor carrier details.

    Returns:
        Formatted lapsed-insurance outreach email string.
    """
    region_info = REGION_RISKS.get(carrier.region, REGION_RISKS["National"])

    if carrier.fleet_tier == "small":
        authority_note = (
            f"For a {carrier.fleet_size}-unit fleet, a lapse can mean the difference between "
            "staying on the road and losing loads to brokers who check insurance status "
            "before dispatching."
        )
    elif carrier.fleet_tier == "mid-size":
        authority_note = (
            f"At {carrier.fleet_size} units, an insurance lapse doesn't just risk your authority — "
            "it triggers shipper audits and can cost you contracts that took years to build."
        )
    else:
        authority_note = (
            f"With {carrier.fleet_size} units, an insurance lapse creates cascading risk: "
            "broker holds, shipper contract violations, and potential DOT out-of-service "
            "orders that idle your entire fleet."
        )

    to_line = f"To: {carrier.email}" if carrier.email else "To: {{recipient_email}}"

    return textwrap.dedent(f"""\
        {to_line}
        Subject: URGENT — Insurance coverage gap for {carrier.carrier_name} ({carrier.authority_line})

        Hi {carrier.first_name},

        I'm contacting you regarding a potential insurance coverage gap for
        {carrier.carrier_name} ({carrier.authority_line}). FMCSA records
        indicate your current coverage may be lapsed or approaching expiration,
        and I want to make sure your authority and operations aren't at risk.

        Here's what's at stake:

          • FMCSA can revoke operating authority for carriers without continuous
            insurance coverage meeting minimum financial responsibility requirements
          • Brokers and shippers routinely verify insurance status — a lapse shows
            up immediately on carrier monitoring services
          • Reinstatement after a lapse often means higher premiums and more
            restrictive terms

        {authority_note}

        I specialize in helping {carrier.region} carriers in {carrier.location}
        get coverage reinstated quickly — often within 24–48 hours. For
        {carrier.state_name} operators dealing with {region_info['weather']},
        I can also make sure your new program addresses the specific risks
        your fleet faces daily.

        This is time-sensitive. If your coverage has lapsed or is about to,
        please call me directly at {{{{sender_phone}}}} or reply to this email
        so we can get you protected before it impacts your operations.

        Best regards,
        {{{{sender_name}}}}
        {{{{sender_title}}}}
        {{{{sender_phone}}}}
        {{{{sender_email}}}}
    """)


TEMPLATES: dict[str, callable] = {
    "introduction": _generate_introduction,
    "follow-up": _generate_follow_up,
    "lapsed-insurance": _generate_lapsed_insurance,
}


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def generate_emails_for_carrier(
    carrier: CarrierInfo,
    template_name: Optional[str] = None,
) -> dict[str, str]:
    """Generate one or all email templates for a carrier.

    Args:
        carrier: Motor carrier details.
        template_name: Specific template to generate, or None for all three.

    Returns:
        Dict mapping template name to generated email text.

    Raises:
        ValueError: If template_name is not recognized.
    """
    if template_name:
        if template_name not in TEMPLATES:
            raise ValueError(
                f"Unknown template '{template_name}'. "
                f"Choose from: {', '.join(TEMPLATES)}"
            )
        return {template_name: TEMPLATES[template_name](carrier)}
    return {name: fn(carrier) for name, fn in TEMPLATES.items()}


def write_email_files(
    carrier: CarrierInfo,
    emails: dict[str, str],
    output_dir: Path,
) -> list[Path]:
    """Write generated emails to individual text files.

    Files are named: {carrier_safe_name}_DOT{dot}_{template}.txt

    Args:
        carrier: Motor carrier details (used for file naming).
        emails: Dict mapping template name to email text.
        output_dir: Directory to write files into.

    Returns:
        List of paths to written files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for template_name, content in emails.items():
        filename = f"{carrier.safe_filename}_DOT{carrier.dot_number}_{template_name}.txt"
        filepath = output_dir / filename
        filepath.write_text(content, encoding="utf-8")
        logger.info("Wrote: %s", filepath)
        written.append(filepath)

    return written


def write_email_json(
    carrier: CarrierInfo,
    emails: dict[str, str],
    output_dir: Path,
) -> Path:
    """Write generated emails as a single JSON file per carrier.

    Args:
        carrier: Motor carrier details.
        emails: Dict mapping template name to email text.
        output_dir: Directory to write files into.

    Returns:
        Path to the written JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{carrier.safe_filename}_DOT{carrier.dot_number}.json"
    filepath = output_dir / filename

    payload = {
        "carrier": {
            "name": carrier.carrier_name,
            "dot_number": carrier.dot_number,
            "mc_number": carrier.mc_number,
            "fleet_size": carrier.fleet_size,
            "fleet_tier": carrier.fleet_tier,
            "state": carrier.state,
            "state_name": carrier.state_name,
            "city": carrier.phys_city,
            "region": carrier.region,
            "contact_name": carrier.contact_name,
            "email": carrier.email,
        },
        "generated_at": datetime.now().isoformat(),
        "emails": emails,
    }

    filepath.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote JSON: %s", filepath)
    return filepath


def write_summary(
    results: list[dict],
    output_dir: Path,
) -> Path:
    """Write a summary report of all generated emails.

    Args:
        results: List of dicts with carrier info and generated file paths.
        output_dir: Directory to write summary into.

    Returns:
        Path to the summary file.
    """
    summary_path = output_dir / "generation_summary.txt"
    lines = [
        "=" * 70,
        "TRUCKING INSURANCE EMAIL GENERATION SUMMARY",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        "",
        f"Total carriers processed: {len(results)}",
        f"Total emails generated:   {sum(len(r['templates']) for r in results)}",
        "",
    ]

    for i, result in enumerate(results, 1):
        c = result["carrier"]
        lines.append(f"--- Carrier {i} ---")
        lines.append(f"  Name:       {c.carrier_name}")
        lines.append(f"  DOT#:       {c.dot_number}")
        if c.mc_number:
            lines.append(f"  MC#:        {c.mc_number}")
        lines.append(f"  Fleet:      {c.fleet_size} units ({c.fleet_tier})")
        lines.append(f"  Location:   {c.location}")
        lines.append(f"  Region:     {c.region}")
        lines.append(f"  Contact:    {c.contact_name}")
        if c.email:
            lines.append(f"  Email:      {c.email}")
        lines.append(f"  Templates:  {', '.join(result['templates'])}")
        lines.append("  Files:")
        for fp in result["files"]:
            lines.append(f"    - {fp.name}")
        if result.get("error"):
            lines.append(f"  ERROR: {result['error']}")
        lines.append("")

    summary_text = "\n".join(lines) + "\n"
    summary_path.write_text(summary_text, encoding="utf-8")
    logger.info("Summary written to: %s", summary_path)
    return summary_path


# ---------------------------------------------------------------------------
# CSV batch processing
# ---------------------------------------------------------------------------

REQUIRED_CSV_COLUMNS = {"name", "dot_number", "fleet_size", "state"}


def load_carriers_from_csv(csv_path: str) -> list[CarrierInfo]:
    """Load carrier records from a CSV file.

    Expected columns: name, dot_number, fleet_size, state, city, email.
    The city and email columns are optional.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        List of CarrierInfo objects parsed from the CSV.

    Raises:
        FileNotFoundError: If csv_path does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    carriers: list[CarrierInfo] = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(f"CSV file is empty: {csv_path}")

        actual_columns = {col.strip().lower() for col in reader.fieldnames}
        missing = REQUIRED_CSV_COLUMNS - actual_columns
        if missing:
            raise ValueError(
                f"CSV is missing required columns: {', '.join(sorted(missing))}. "
                f"Required: {', '.join(sorted(REQUIRED_CSV_COLUMNS))}"
            )

        for row_num, row in enumerate(reader, start=2):
            row = {k.strip().lower(): v.strip() for k, v in row.items()}

            carrier_name = row.get("name", "")
            dot_number = row.get("dot_number", "")
            mc_number = row.get("mc_number", "")
            fleet_size_raw = row.get("fleet_size", "0")
            state = row.get("state", "").upper()
            city = row.get("city", "")
            email = row.get("email", "")

            if not carrier_name:
                logger.warning("Row %d: missing name, skipping", row_num)
                continue

            try:
                fleet_size = int(fleet_size_raw)
            except ValueError:
                logger.warning(
                    "Row %d: invalid fleet_size '%s', defaulting to 1",
                    row_num,
                    fleet_size_raw,
                )
                fleet_size = 1

            if fleet_size < 1:
                fleet_size = 1

            if len(state) != 2:
                logger.warning(
                    "Row %d: state '%s' is not a 2-letter abbreviation",
                    row_num,
                    state,
                )

            carriers.append(
                CarrierInfo(
                    carrier_name=carrier_name,
                    dot_number=dot_number,
                    mc_number=mc_number,
                    fleet_size=fleet_size,
                    state=state,
                    phys_city=city,
                    contact_name=row.get("contact_name", "Operations Manager"),
                    email=email,
                )
            )

    logger.info("Loaded %d carriers from %s", len(carriers), csv_path)
    return carriers


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate personalized cold emails for selling trucking insurance "
            "to motor carriers. Supports introduction, follow-up, and "
            "lapsed-insurance templates with fleet-size and region personalization."
        ),
        epilog=textwrap.dedent("""\
            examples:
              # Single carrier, all templates
              %(prog)s --carrier-name "Big Rig Logistics" --dot-number 1234567 \\
                  --mc-number 987654 --fleet-size 25 --state TX \\
                  --phys-city "Dallas" --contact-name "Mike Johnson"

              # Single carrier, one template, JSON output
              %(prog)s --carrier-name "Sunrise Transport" --dot-number 7654321 \\
                  --fleet-size 8 --state FL --phys-city "Miami" \\
                  --template follow-up --output-format json

              # Batch mode from CSV
              %(prog)s --csv-file carriers.csv

              # Custom output directory
              %(prog)s --csv-file carriers.csv --output-dir ./email_output
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    single = parser.add_argument_group("single carrier mode")
    single.add_argument(
        "--carrier-name",
        metavar="NAME",
        help="Legal name of the motor carrier",
    )
    single.add_argument(
        "--dot-number",
        metavar="DOT",
        help="USDOT number of the carrier",
    )
    single.add_argument(
        "--mc-number",
        metavar="MC",
        default="",
        help="MC number of the carrier (optional)",
    )
    single.add_argument(
        "--fleet-size",
        metavar="N",
        type=int,
        help="Number of power units in the fleet",
    )
    single.add_argument(
        "--state",
        metavar="ST",
        help="Two-letter state abbreviation (e.g., TX, CA, FL)",
    )
    single.add_argument(
        "--phys-city",
        metavar="CITY",
        default="",
        help="Physical city where the carrier is based (optional)",
    )
    single.add_argument(
        "--contact-name",
        metavar="NAME",
        default="",
        help="Name of the contact person at the carrier (optional)",
    )
    single.add_argument(
        "--email",
        metavar="EMAIL",
        default="",
        help="Email address of the contact person (optional)",
    )

    batch = parser.add_argument_group("batch mode")
    batch.add_argument(
        "--csv-file",
        metavar="FILE",
        help=(
            "Path to CSV file with columns: name, dot_number, fleet_size, "
            "state, city, email"
        ),
    )

    parser.add_argument(
        "--template",
        choices=list(TEMPLATES.keys()),
        default=None,
        help="Generate only this template (default: all three)",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format: text files or JSON (default: text)",
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default="./generated_emails",
        help="Directory to save generated emails (default: ./generated_emails)",
    )

    return parser


def validate_single_args(args: argparse.Namespace) -> CarrierInfo:
    """Validate and build a CarrierInfo from single-carrier CLI arguments.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Populated CarrierInfo.

    Raises:
        SystemExit: If required arguments are missing.
    """
    missing = []
    if not args.carrier_name:
        missing.append("--carrier-name")
    if not args.dot_number:
        missing.append("--dot-number")
    if args.fleet_size is None:
        missing.append("--fleet-size")
    if not args.state:
        missing.append("--state")

    if missing:
        logger.error(
            "Single-carrier mode requires: %s", ", ".join(missing)
        )
        sys.exit(2)

    state = args.state.upper()
    if len(state) != 2:
        logger.error("--state must be a 2-letter abbreviation (e.g., TX)")
        sys.exit(2)

    fleet_size = max(1, args.fleet_size)

    return CarrierInfo(
        carrier_name=args.carrier_name.strip(),
        dot_number=str(args.dot_number).strip(),
        mc_number=str(args.mc_number).strip() if args.mc_number else "",
        fleet_size=fleet_size,
        state=state,
        phys_city=args.phys_city.strip() if args.phys_city else "",
        contact_name=args.contact_name.strip() if args.contact_name else "Operations Manager",
        email=args.email.strip() if args.email else "",
    )


def process_carrier(
    carrier: CarrierInfo,
    template_name: Optional[str],
    output_dir: Path,
    output_format: str,
) -> dict:
    """Generate emails for a single carrier and write output files.

    Args:
        carrier: Motor carrier details.
        template_name: Specific template or None for all.
        output_dir: Directory to write files into.
        output_format: 'text' for .txt files, 'json' for .json.

    Returns:
        Result dict with carrier, templates, files, and any error.
    """
    result = {
        "carrier": carrier,
        "templates": [],
        "files": [],
        "error": None,
    }

    try:
        emails = generate_emails_for_carrier(carrier, template_name)
        result["templates"] = list(emails.keys())

        if output_format == "json":
            json_path = write_email_json(carrier, emails, output_dir)
            result["files"] = [json_path]
        else:
            result["files"] = write_email_files(carrier, emails, output_dir)
    except Exception as exc:
        logger.error(
            "Error processing carrier '%s': %s", carrier.carrier_name, exc
        )
        result["error"] = str(exc)

    return result


def main() -> None:
    """Parse arguments, generate emails, and write output files with summary."""
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    # Determine mode
    if args.csv_file:
        logger.info("Batch mode: loading carriers from %s", args.csv_file)
        try:
            carriers = load_carriers_from_csv(args.csv_file)
        except (FileNotFoundError, ValueError) as exc:
            logger.error("%s", exc)
            sys.exit(1)

        if not carriers:
            logger.error("No valid carriers found in CSV file")
            sys.exit(1)

    elif args.carrier_name or args.dot_number or args.fleet_size or args.state:
        carrier = validate_single_args(args)
        carriers = [carrier]

    else:
        parser.print_help()
        sys.exit(2)

    # Process all carriers
    results: list[dict] = []
    for carrier in carriers:
        logger.info(
            "Processing: %s (DOT# %s) — %d units, %s",
            carrier.carrier_name,
            carrier.dot_number,
            carrier.fleet_size,
            carrier.location,
        )
        result = process_carrier(carrier, args.template, output_dir, args.output_format)
        results.append(result)

    # Write summary
    summary_path = write_summary(results, output_dir)

    # Print summary to stdout
    total_emails = sum(len(r["templates"]) for r in results)
    errors = sum(1 for r in results if r["error"])
    print(f"\nDone. Generated {total_emails} emails for {len(results)} carriers.")
    print(f"Output directory: {output_dir.resolve()}")
    print(f"Summary: {summary_path}")
    if errors:
        print(f"Errors: {errors} carrier(s) had issues — see log output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
