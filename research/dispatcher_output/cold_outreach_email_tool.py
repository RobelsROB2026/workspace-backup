#!/usr/bin/env python3
"""
Cold Outreach Email Generator for Trucking Insurance Sales.

Generates personalized cold outreach emails to motor carriers for selling
trucking insurance. Supports single-carrier mode via CLI flags and batch
mode via CSV input. Produces individual email files and a summary report.
"""

import argparse
import csv
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from string import Template

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = Path(__file__).with_suffix(".log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Carrier:
    carrier_name: str
    dot_number: str
    fleet_size: int
    state: str
    contact_name: str

    def first_name(self) -> str:
        return self.contact_name.strip().split()[0] if self.contact_name.strip() else "there"

    def fleet_descriptor(self) -> str:
        if self.fleet_size <= 5:
            return "small but mighty"
        if self.fleet_size <= 25:
            return "growing"
        if self.fleet_size <= 100:
            return "mid-size"
        return "large-scale"

# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, Template] = {
    "introduction": Template("""\
Subject: Trucking Insurance Built for ${carrier_name} (DOT #${dot_number})

Hi ${first_name},

I came across ${carrier_name} while reviewing motor carriers operating out of \
${state}, and I wanted to reach out personally.

Running a ${fleet_descriptor} fleet of ${fleet_size} units is no small feat, \
and I know insurance costs can be one of the biggest line items on your P&L. \
We specialize exclusively in commercial trucking insurance and work with \
carriers of every size across ${state} and nationwide.

Here's what we typically help carriers like ${carrier_name} with:

  - Primary liability & cargo coverage tailored to your operating authority
  - Physical damage plans scaled to a ${fleet_size}-unit fleet
  - Competitive rates through our panel of A-rated trucking insurers
  - Fast certificates of insurance — often same-day

I'd love to spend 10 minutes learning about your current coverage and see \
if we can save you money without cutting corners on protection.

Would you be open to a quick call this week?

Best regards,
[Your Name]
[Your Agency]
[Phone] | [Email]
"""),

    "follow_up": Template("""\
Subject: Following Up — Insurance Options for ${carrier_name}

Hi ${first_name},

I reached out recently about trucking insurance options for ${carrier_name} \
(DOT #${dot_number}) and wanted to circle back.

I understand things move fast when you're managing ${fleet_size} units, so I \
wanted to keep this brief. We've been helping ${state}-based carriers \
reduce their insurance spend by 10-25% on average — without sacrificing coverage.

A few things that might be relevant to your ${fleet_descriptor} operation:

  - No-obligation rate comparison against your current policy
  - Dedicated agent who understands trucking — not a generic call center
  - We handle filings, COIs, and compliance so you can focus on freight

If now isn't the right time, no worries at all. But if your renewal is \
coming up in the next 90 days, it's worth getting a quote now so you have \
options on the table.

Happy to work around your schedule — just reply to this email or give me a \
call anytime.

Best,
[Your Name]
[Your Agency]
[Phone] | [Email]
"""),

    "lapsed_insurance": Template("""\
Subject: Urgent — Insurance Gap Alert for ${carrier_name} (DOT #${dot_number})

Hi ${first_name},

I'm reaching out because our records indicate that ${carrier_name} \
(DOT #${dot_number}) may have a lapse or gap in insurance coverage. \
If that's the case, I want to help you get this resolved quickly — \
operating without valid coverage puts your authority and your ${fleet_size} \
units at serious risk.

Here's what's at stake:

  - FMCSA can revoke your operating authority for insurance non-compliance
  - Brokers and shippers will stop tendering loads to uninsured carriers
  - A single uninsured accident could be financially devastating

The good news: we specialize in getting ${state} carriers back into \
compliance fast. We've helped dozens of ${fleet_descriptor} fleets in \
situations just like this.

What we can do right now:

  - Same-day bind on primary liability to restore your authority status
  - Competitive rates even with a coverage gap on your record
  - Handle all FMCSA filings on your behalf

Time is critical here, ${first_name}. Let's get on a call today if \
possible so we can get ${carrier_name} protected and back in compliance.

Regards,
[Your Name]
[Your Agency]
[Phone] | [Email]
"""),
}

TEMPLATE_NAMES = list(TEMPLATES.keys())

# ---------------------------------------------------------------------------
# Email generation
# ---------------------------------------------------------------------------

def generate_email(carrier: Carrier, template_name: str) -> str:
    """Render a single email from a template and carrier data."""
    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown template '{template_name}'. Choose from: {TEMPLATE_NAMES}")

    return TEMPLATES[template_name].substitute(
        carrier_name=carrier.carrier_name,
        dot_number=carrier.dot_number,
        fleet_size=carrier.fleet_size,
        state=carrier.state,
        contact_name=carrier.contact_name,
        first_name=carrier.first_name(),
        fleet_descriptor=carrier.fleet_descriptor(),
    )


def generate_all_emails(carrier: Carrier) -> dict[str, str]:
    """Generate all template variants for one carrier."""
    return {name: generate_email(carrier, name) for name in TEMPLATE_NAMES}

# ---------------------------------------------------------------------------
# CSV batch processing
# ---------------------------------------------------------------------------

REQUIRED_CSV_COLUMNS = {"carrier_name", "dot_number", "fleet_size", "state", "contact_name"}


def load_carriers_from_csv(csv_path: str) -> list[Carrier]:
    """Load carrier records from a CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    carriers: list[Carrier] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header row.")
        missing = REQUIRED_CSV_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

        for row_num, row in enumerate(reader, start=2):
            try:
                carriers.append(Carrier(
                    carrier_name=row["carrier_name"].strip(),
                    dot_number=row["dot_number"].strip(),
                    fleet_size=int(row["fleet_size"]),
                    state=row["state"].strip(),
                    contact_name=row["contact_name"].strip(),
                ))
            except (ValueError, KeyError) as exc:
                log.warning("Skipping CSV row %d: %s", row_num, exc)

    return carriers

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_ " else "" for c in name).strip().replace(" ", "_")


def write_emails(carriers: list[Carrier], output_dir: Path) -> list[dict]:
    """Write emails to disk and return summary records."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary: list[dict] = []

    for carrier in carriers:
        log.info("Generating emails for %s (DOT #%s)", carrier.carrier_name, carrier.dot_number)
        emails = generate_all_emails(carrier)
        carrier_dir = output_dir / sanitize_filename(carrier.carrier_name)
        carrier_dir.mkdir(parents=True, exist_ok=True)

        for tmpl_name, body in emails.items():
            out_file = carrier_dir / f"{tmpl_name}.txt"
            out_file.write_text(body, encoding="utf-8")
            log.info("  Wrote %s", out_file)
            summary.append({
                "carrier_name": carrier.carrier_name,
                "dot_number": carrier.dot_number,
                "template": tmpl_name,
                "file": str(out_file),
            })

    return summary


def write_summary_report(summary: list[dict], output_dir: Path) -> Path:
    """Write a CSV summary report of all generated emails."""
    report_path = output_dir / "summary_report.csv"
    with open(report_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["carrier_name", "dot_number", "template", "file"])
        writer.writeheader()
        writer.writerows(summary)
    log.info("Summary report written to %s", report_path)
    return report_path


def print_emails_to_stdout(carrier: Carrier) -> None:
    """Print all email variants for a single carrier to stdout."""
    emails = generate_all_emails(carrier)
    for name, body in emails.items():
        print(f"\n{'='*70}")
        print(f"  TEMPLATE: {name.upper()}")
        print(f"{'='*70}\n")
        print(body)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate personalized cold outreach emails to sell trucking insurance to motor carriers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  # Single carrier
  %(prog)s --carrier-name "ABC Trucking" --dot-number 1234567 \\
           --fleet-size 12 --state Texas --contact-name "John Smith"

  # Batch mode from CSV
  %(prog)s --csv-file carriers.csv --output-dir ./emails

  CSV columns (required): carrier_name, dot_number, fleet_size, state, contact_name
""",
    )

    single = parser.add_argument_group("single carrier mode")
    single.add_argument("--carrier-name", help="Motor carrier company name")
    single.add_argument("--dot-number", help="USDOT number")
    single.add_argument("--fleet-size", type=int, help="Number of power units")
    single.add_argument("--state", help="Primary state of operation")
    single.add_argument("--contact-name", help="Name of the contact person")

    batch = parser.add_argument_group("batch mode")
    batch.add_argument("--csv-file", help="Path to CSV file with carrier records")

    output = parser.add_argument_group("output options")
    output.add_argument(
        "--output-dir",
        default="./outreach_emails",
        help="Directory to save generated emails (default: ./outreach_emails)",
    )
    output.add_argument(
        "--template",
        choices=TEMPLATE_NAMES,
        help="Generate only a specific template (default: all)",
    )
    output.add_argument(
        "--stdout-only",
        action="store_true",
        help="Print emails to stdout instead of writing files",
    )

    return parser


def validate_single_carrier_args(args: argparse.Namespace) -> Carrier:
    """Validate that all required single-carrier args are present."""
    required = ["carrier_name", "dot_number", "fleet_size", "state", "contact_name"]
    missing = [f"--{r.replace('_', '-')}" for r in required if getattr(args, r) is None]
    if missing:
        raise SystemExit(
            f"Error: single-carrier mode requires all of: {', '.join(missing)}\n"
            "Or use --csv-file for batch mode."
        )
    return Carrier(
        carrier_name=args.carrier_name,
        dot_number=args.dot_number,
        fleet_size=args.fleet_size,
        state=args.state,
        contact_name=args.contact_name,
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Determine mode
    if not args.csv_file and args.carrier_name is None:
        parser.print_help()
        raise SystemExit("\nError: provide either single-carrier flags or --csv-file.")

    output_dir = Path(args.output_dir)
    carriers: list[Carrier] = []

    if args.csv_file:
        log.info("Loading carriers from %s", args.csv_file)
        try:
            carriers = load_carriers_from_csv(args.csv_file)
        except (FileNotFoundError, ValueError) as exc:
            log.error("CSV error: %s", exc)
            raise SystemExit(1)
        log.info("Loaded %d carrier(s) from CSV", len(carriers))
        if not carriers:
            log.warning("No valid carriers found in CSV. Exiting.")
            raise SystemExit(1)
    else:
        carriers.append(validate_single_carrier_args(args))

    # Generate emails
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.stdout_only:
        for carrier in carriers:
            if args.template:
                print(generate_email(carrier, args.template))
            else:
                print_emails_to_stdout(carrier)
        return

    run_dir = output_dir / f"run_{timestamp}"
    summary = write_emails(carriers, run_dir)
    report = write_summary_report(summary, run_dir)

    # Print summary
    print(f"\nGenerated {len(summary)} email(s) for {len(carriers)} carrier(s).")
    print(f"Output directory: {run_dir}")
    print(f"Summary report:   {report}")


if __name__ == "__main__":
    main()
