#!/usr/bin/env python3
"""Cold email template generator for trucking insurance sales.

Generates personalized cold email templates for prospective trucking carrier
clients. Supports single-carrier mode via CLI arguments and batch mode via
CSV input. Produces four template variants per carrier: introduction,
fleet-specific pitch, compliance-focused, and follow-up.

Usage examples:
    # Single carrier
    python cold_email_generator.py \\
        --carrier-name "ABC Trucking" --dot-number 1234567 \\
        --fleet-size 25 --state TX --region Southwest \\
        --contact-email dispatch@abctrucking.com \\
        --coverage-type "auto liability"

    # Batch mode from CSV
    python cold_email_generator.py --csv-file carriers.csv

    # CSV columns: carrier_name,dot_number,fleet_size,state,region,contact_email,coverage_type
"""

import argparse
import csv
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_FMT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Carrier:
    """Represents a trucking carrier prospect."""
    carrier_name: str
    dot_number: str
    fleet_size: int
    state: str
    region: str
    contact_email: str
    coverage_type: str = "auto liability"

    def __post_init__(self):
        self.dot_number = str(self.dot_number).strip()
        self.fleet_size = int(self.fleet_size)
        if self.fleet_size < 1:
            raise ValueError(f"fleet_size must be >= 1, got {self.fleet_size}")
        if not self.carrier_name.strip():
            raise ValueError("carrier_name must not be empty")

    @property
    def fleet_tier(self) -> str:
        """Classify carrier by fleet size for messaging."""
        if self.fleet_size <= 5:
            return "small"
        if self.fleet_size <= 50:
            return "mid-size"
        return "large"


# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, dict[str, str]] = {
    "introduction": {
        "subject": "Insurance options for {carrier_name} (DOT {dot_number})",
        "body": """\
Hi,

My name is [Your Name] with [Agency Name], and I specialize in commercial
trucking insurance for carriers in the {region} region.

I noticed that {carrier_name} (USDOT {dot_number}) is operating a {fleet_tier}
fleet of {fleet_size} units out of {state}. We work with many {fleet_tier}
carriers in {state} and have been able to secure competitive {coverage_type}
rates through our specialized markets.

I'd love to put together a no-obligation quote so you can see how your current
coverage and pricing compare. Would you have 15 minutes this week for a quick
call?

Best regards,
[Your Name]
[Agency Name]
[Phone Number]
""",
    },
    "fleet_pitch": {
        "subject": "Tailored coverage for your {fleet_size}-unit fleet",
        "body": """\
Hi,

I'm reaching out because we've developed insurance programs specifically
designed for {fleet_tier} fleets like {carrier_name}.

With {fleet_size} units on the road, you know that every dollar per truck
matters. Our markets reward carriers with clean safety records, and we've
helped similar {fleet_tier} operations in {state} reduce premiums by bundling
{coverage_type} with physical damage, cargo, and general liability.

Here's what we typically see for a {fleet_size}-truck fleet in the {region}
region:
  - Competitive per-truck {coverage_type} rates
  - Flexible payment plans to smooth cash flow
  - Dedicated claims support so your trucks stay moving

Can I send over a preliminary indication? I just need a current dec page or
loss runs to get started.

Best regards,
[Your Name]
[Agency Name]
[Phone Number]
""",
    },
    "compliance": {
        "subject": "Keeping DOT {dot_number} compliant — are your limits up to date?",
        "body": """\
Hi,

FMCSA compliance requirements change, and gaps in {coverage_type} coverage can
put your authority at risk. As a broker who works exclusively with trucking
carriers, I help operations like {carrier_name} stay ahead of filing
requirements.

For a {fleet_size}-unit fleet based in {state}, here are the key areas I'd
review:
  - BMC-91 / BMC-34 filing status for DOT {dot_number}
  - Minimum {coverage_type} limits for the commodities you haul
  - State-specific requirements in {state} and across the {region} region
  - MCS-90 endorsement adequacy

If you'd like a free compliance check, I'm happy to pull your FMCSA snapshot
and highlight anything that needs attention before your next audit or renewal.

Best regards,
[Your Name]
[Agency Name]
[Phone Number]
""",
    },
    "follow_up": {
        "subject": "Following up — insurance quote for {carrier_name}",
        "body": """\
Hi,

I wanted to follow up on my earlier message about {coverage_type} options for
{carrier_name} (DOT {dot_number}).

I understand you're busy running a {fleet_size}-truck operation, so I'll keep
this brief: we recently placed a {fleet_tier} fleet in {state} with a program
that saved them over 15% on their {coverage_type} renewal. I think we could
do something similar for you.

If now isn't the right time, no problem at all — just let me know when your
renewal date is and I'll reach back out ahead of it so you have a comparison
in hand.

Best regards,
[Your Name]
[Agency Name]
[Phone Number]
""",
    },
}


def render_email(template_key: str, carrier: Carrier) -> dict[str, str]:
    """Render a single email template for a carrier.

    Args:
        template_key: One of the keys in TEMPLATES.
        carrier: Carrier data used to personalize the template.

    Returns:
        Dict with 'subject' and 'body' strings.
    """
    tmpl = TEMPLATES[template_key]
    fields = {
        "carrier_name": carrier.carrier_name,
        "dot_number": carrier.dot_number,
        "fleet_size": carrier.fleet_size,
        "fleet_tier": carrier.fleet_tier,
        "state": carrier.state,
        "region": carrier.region,
        "contact_email": carrier.contact_email,
        "coverage_type": carrier.coverage_type,
    }
    return {
        "subject": tmpl["subject"].format(**fields),
        "body": tmpl["body"].format(**fields),
    }


def generate_all_emails(carrier: Carrier) -> dict[str, dict[str, str]]:
    """Generate all four email templates for a carrier.

    Args:
        carrier: Carrier data.

    Returns:
        Dict mapping template name to rendered email (subject + body).
    """
    results = {}
    for key in TEMPLATES:
        results[key] = render_email(key, carrier)
    return results


# ---------------------------------------------------------------------------
# CSV batch processing
# ---------------------------------------------------------------------------

REQUIRED_CSV_COLS = {
    "carrier_name", "dot_number", "fleet_size", "state",
    "region", "contact_email",
}

def load_carriers_from_csv(csv_path: str) -> list[Carrier]:
    """Load carrier records from a CSV file.

    The CSV must include columns: carrier_name, dot_number, fleet_size,
    state, region, contact_email. An optional coverage_type column is
    supported; if absent, defaults to 'auto liability'.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        List of Carrier objects.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(csv_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    carriers: list[Carrier] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header row")
        present = set(reader.fieldnames)
        missing = REQUIRED_CSV_COLS - present
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        for row_num, row in enumerate(reader, start=2):
            try:
                carriers.append(Carrier(
                    carrier_name=row["carrier_name"],
                    dot_number=row["dot_number"],
                    fleet_size=int(row["fleet_size"]),
                    state=row["state"],
                    region=row["region"],
                    contact_email=row["contact_email"],
                    coverage_type=row.get("coverage_type", "auto liability") or "auto liability",
                ))
            except (ValueError, KeyError) as exc:
                logger.warning("Skipping CSV row %d: %s", row_num, exc)

    logger.info("Loaded %d carriers from %s", len(carriers), path)
    return carriers


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_emails(carrier: Carrier, emails: dict[str, dict[str, str]]) -> None:
    """Print rendered emails to stdout."""
    sep = "=" * 72
    print(f"\n{sep}")
    print(f"  Carrier : {carrier.carrier_name}")
    print(f"  DOT#    : {carrier.dot_number}")
    print(f"  Fleet   : {carrier.fleet_size} units ({carrier.fleet_tier})")
    print(f"  State   : {carrier.state}  |  Region: {carrier.region}")
    print(f"  Email   : {carrier.contact_email}")
    print(f"  Coverage: {carrier.coverage_type}")
    print(sep)

    for name, email in emails.items():
        print(f"\n--- Template: {name} ---")
        print(f"To:      {carrier.contact_email}")
        print(f"Subject: {email['subject']}")
        print(f"\n{email['body']}")


def write_summary_report(
    results: list[tuple[Carrier, dict[str, dict[str, str]]]],
    out_path: Optional[str] = None,
) -> str:
    """Write a JSON summary report of all generated emails.

    Args:
        results: List of (Carrier, emails_dict) tuples.
        out_path: Optional output file path. Defaults to
                  cold_email_report_<timestamp>.json in the cwd.

    Returns:
        Path to the written report file.
    """
    if out_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = f"cold_email_report_{ts}.json"

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_carriers": len(results),
        "templates_per_carrier": len(TEMPLATES),
        "total_emails": len(results) * len(TEMPLATES),
        "carriers": [],
    }

    for carrier, emails in results:
        entry = {
            "carrier": asdict(carrier),
            "fleet_tier": carrier.fleet_tier,
            "emails": {},
        }
        for tmpl_name, email in emails.items():
            entry["emails"][tmpl_name] = {
                "subject": email["subject"],
                "body_length": len(email["body"]),
            }
        report["carriers"].append(entry)

    path = Path(out_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    logger.info("Summary report written to %s", path)
    return str(path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate personalized cold email templates for trucking insurance sales.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s --carrier-name "ABC Trucking" --dot-number 1234567 \\
           --fleet-size 25 --state TX --region Southwest \\
           --contact-email dispatch@abc.com

  %(prog)s --csv-file carriers.csv --report-path report.json
        """,
    )

    single = parser.add_argument_group("single-carrier mode")
    single.add_argument("--carrier-name", help="Name of the carrier")
    single.add_argument("--dot-number", help="USDOT number")
    single.add_argument("--fleet-size", type=int, help="Number of power units")
    single.add_argument("--state", help="State of domicile (e.g. TX)")
    single.add_argument("--region", help="Operating region (e.g. Southwest)")
    single.add_argument("--contact-email", help="Prospect email address")
    single.add_argument(
        "--coverage-type",
        default="auto liability",
        help="Primary coverage type (default: auto liability)",
    )

    batch = parser.add_argument_group("batch mode")
    batch.add_argument(
        "--csv-file",
        help="Path to CSV with carrier records for batch processing",
    )

    output = parser.add_argument_group("output options")
    output.add_argument(
        "--report-path",
        help="Path for JSON summary report (default: auto-named in cwd)",
    )
    output.add_argument(
        "--quiet", action="store_true",
        help="Suppress email output; only write the report",
    )

    return parser


def main() -> None:
    """Entry point for the cold email generator."""
    parser = build_parser()
    args = parser.parse_args()

    carriers: list[Carrier] = []

    # --- Batch mode ---
    if args.csv_file:
        try:
            carriers = load_carriers_from_csv(args.csv_file)
        except (FileNotFoundError, ValueError) as exc:
            logger.error("CSV error: %s", exc)
            sys.exit(1)

    # --- Single-carrier mode ---
    single_fields = [args.carrier_name, args.dot_number, args.fleet_size,
                     args.state, args.region, args.contact_email]
    if any(f is not None for f in single_fields):
        missing = []
        for name in ("carrier_name", "dot_number", "fleet_size",
                      "state", "region", "contact_email"):
            if getattr(args, name.replace("-", "_")) is None:
                missing.append(f"--{name.replace('_', '-')}")
        if missing:
            parser.error(
                f"Single-carrier mode requires all of: {', '.join(missing)} "
                "(or use --csv-file for batch mode)"
            )
        carriers.append(Carrier(
            carrier_name=args.carrier_name,
            dot_number=args.dot_number,
            fleet_size=args.fleet_size,
            state=args.state,
            region=args.region,
            contact_email=args.contact_email,
            coverage_type=args.coverage_type,
        ))

    if not carriers:
        parser.print_help()
        sys.exit(0)

    # --- Generate emails ---
    results: list[tuple[Carrier, dict[str, dict[str, str]]]] = []
    for carrier in carriers:
        logger.info(
            "Generating emails for %s (DOT %s)", carrier.carrier_name, carrier.dot_number
        )
        emails = generate_all_emails(carrier)
        results.append((carrier, emails))
        if not args.quiet:
            print_emails(carrier, emails)

    # --- Summary report ---
    report_path = write_summary_report(results, args.report_path)
    print(f"\nGenerated {len(results) * len(TEMPLATES)} emails for "
          f"{len(results)} carrier(s).")
    print(f"Summary report: {report_path}")


if __name__ == "__main__":
    main()
