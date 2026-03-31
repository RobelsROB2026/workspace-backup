#!/usr/bin/env python3
"""
LinkedIn Decision Maker Finder for Trucking Companies.

Cross-references trucking company names against LinkedIn via Google Custom
Search API to identify likely decision makers (Owner, President, CEO, VP).
Supports single-company lookup and batch CSV input. Outputs individual .txt
profile files and a JSON or TXT summary report.

Requirements:
    pip install requests

Environment variables:
    GOOGLE_CSE_API_KEY  - Google Custom Search JSON API key
    GOOGLE_CSE_CX       - Google Custom Search Engine ID (cx)

Usage examples:
    # Single company lookup
    python linkedin_decision_maker_finder.py --company-name "ABC Trucking" --state TX

    # Batch CSV input (CSV must have a 'company_name' column; optional 'state')
    python linkedin_decision_maker_finder.py --csv-input carriers.csv --max-results 5

    # TXT output with verbose logging
    python linkedin_decision_maker_finder.py --company-name "XYZ Freight" \\
        --state CA --output-format txt --verbose
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}

DEFAULT_TITLES = ["Owner", "President", "CEO", "Founder", "VP", "Director"]
GOOGLE_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, doubled each retry
REQUEST_TIMEOUT = 15  # seconds

OUTPUT_DIR = Path.home() / "research" / "dispatcher_output" / "linkedin_results"
LOG_FILE = Path.home() / "research" / "dispatcher_output" / "linkedin_decision_maker_finder.log"

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("linkedin_finder")
logger.setLevel(logging.DEBUG)

_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

_fh = logging.FileHandler(LOG_FILE)
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(_fmt)
logger.addHandler(_fh)

_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)  # raised to DEBUG when --verbose is used
_ch.setFormatter(_fmt)
logger.addHandler(_ch)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class DecisionMaker:
    """A potential decision maker extracted from search results."""

    name: str = ""
    title: str = ""
    company: str = ""
    linkedin_url: str = ""
    snippet: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    confidence: float = 0.0  # 0.0 - 1.0


@dataclass
class CompanyResult:
    """Aggregated search results for a single trucking company."""

    company_name: str
    state: str = ""
    search_query: str = ""
    decision_makers: list = field(default_factory=list)
    search_timestamp: str = ""
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

# Common trucking-related keywords for name validation
_TRUCKING_KEYWORDS = re.compile(
    r"(truck|freight|transport|haul|logistics|carrier|express|lines|moving|"
    r"delivery|shipping|motor|fleet|dispatch|cargo|cartage|drayage|ltl|"
    r"truckload|tanker|flatbed|reefer|intermodal|inc|llc|ltd|corp|co\b)",
    re.IGNORECASE,
)


def validate_company_name(name: str) -> tuple[bool, str]:
    """Validate a trucking company name.

    Args:
        name: Company name string.

    Returns:
        Tuple of (is_valid, reason).
    """
    stripped = name.strip()
    if not stripped:
        return False, "Company name is empty"
    if len(stripped) < 2:
        return False, "Company name too short (minimum 2 characters)"
    if len(stripped) > 200:
        return False, "Company name too long (maximum 200 characters)"
    if re.search(r"[<>{}\\|`]", stripped):
        return False, "Company name contains invalid characters"
    # Warn (but allow) if no trucking-related keyword found
    if not _TRUCKING_KEYWORDS.search(stripped):
        logger.warning(
            "Company name '%s' does not contain common trucking keywords - "
            "results may be less relevant",
            stripped,
        )
    return True, "OK"


def validate_state_code(state: str) -> tuple[bool, str]:
    """Validate a US state abbreviation.

    Args:
        state: Two-letter state code.

    Returns:
        Tuple of (is_valid, reason).
    """
    if not state:
        return True, "OK"  # state is optional
    upper = state.strip().upper()
    if upper not in VALID_US_STATES:
        return False, f"Invalid state code '{state}'. Must be a 2-letter US state abbreviation"
    return True, "OK"


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
_NAME_FROM_TITLE_RE = re.compile(r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,3})\s*[-\u2013|]")


def _extract_emails(text: str) -> list[str]:
    """Extract email addresses from text."""
    return _EMAIL_RE.findall(text)


def _extract_phones(text: str) -> list[str]:
    """Extract US phone numbers from text."""
    return _PHONE_RE.findall(text)


def _compute_confidence(item: dict, company_name: str, titles: list[str]) -> float:
    """Score 0-1 based on how well a search result matches the target company + title."""
    score = 0.0
    combined = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
    company_lower = company_name.lower()

    if company_lower in combined:
        score += 0.35
    elif company_lower.split()[0] in combined:
        score += 0.15

    link = item.get("link", "")
    if "linkedin.com/in/" in link:
        score += 0.25
    elif "linkedin.com" in link:
        score += 0.10

    for t in titles:
        if t.lower() in combined:
            score += 0.20
            break

    if len(item.get("snippet", "")) > 80:
        score += 0.10

    if _extract_emails(combined) or _extract_phones(combined):
        score += 0.10

    return min(round(score, 2), 1.0)


def _extract_name_from_result(item: dict) -> str:
    """Best-effort name extraction from a Google/LinkedIn result title."""
    title = item.get("title", "")
    match = _NAME_FROM_TITLE_RE.match(title)
    if match:
        return match.group(1).strip()
    for sep in [" - ", " \u2013 ", " | "]:
        if sep in title:
            candidate = title.split(sep)[0].strip()
            words = candidate.split()
            if 1 < len(words) <= 4 and all(w[0].isupper() for w in words):
                return candidate
    return title.split("|")[0].strip()


def _extract_title_from_result(item: dict) -> str:
    """Best-effort job title extraction from a Google result."""
    title_text = item.get("title", "")
    parts = re.split(r"\s*[-\u2013|]\s*", title_text)
    if len(parts) >= 2:
        return parts[1].strip()
    snippet = item.get("snippet", "")
    for t in DEFAULT_TITLES:
        if t.lower() in snippet.lower():
            return t
    return ""


def _extract_company_from_result(item: dict, target_company: str) -> str:
    """Extract company name from result, falling back to target company."""
    title_text = item.get("title", "")
    parts = re.split(r"\s*[-\u2013|]\s*", title_text)
    if len(parts) >= 3:
        candidate = parts[2].strip().replace("LinkedIn", "").strip()
        if candidate:
            return candidate
    return target_company


# ---------------------------------------------------------------------------
# Google Custom Search
# ---------------------------------------------------------------------------


def _google_search(query: str, api_key: str, cx: str, num: int = 10, start: int = 1) -> dict:
    """Execute a Google Custom Search request with retry logic.

    Args:
        query: Search query string.
        api_key: Google API key.
        cx: Custom Search Engine ID.
        num: Number of results (max 10 per request).
        start: Result offset.

    Returns:
        JSON response as dict.
    """
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": min(num, 10),
        "start": start,
    }
    delay = RETRY_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug("Google CSE request (attempt %d): q=%s", attempt, query)
            resp = requests.get(GOOGLE_CSE_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                logger.warning("Rate limited (429). Backing off %ds ...", delay)
                time.sleep(delay)
                delay *= 2
                continue
            if resp.status_code == 403:
                body = (
                    resp.json()
                    if resp.headers.get("content-type", "").startswith("application/json")
                    else {}
                )
                err_msg = body.get("error", {}).get("message", resp.text[:200])
                logger.error("API 403: %s", err_msg)
                raise RuntimeError(f"Google CSE API error 403: {err_msg}")
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            logger.warning("Request timed out (attempt %d/%d)", attempt, MAX_RETRIES)
            if attempt == MAX_RETRIES:
                raise
            time.sleep(delay)
            delay *= 2
        except requests.exceptions.ConnectionError as exc:
            logger.warning("Connection error (attempt %d/%d): %s", attempt, MAX_RETRIES, exc)
            if attempt == MAX_RETRIES:
                raise
            time.sleep(delay)
            delay *= 2
    return {}


# ---------------------------------------------------------------------------
# Core search logic
# ---------------------------------------------------------------------------


def build_query(company_name: str, state: str = "") -> str:
    """Build a LinkedIn-targeted Google search query for decision makers.

    Args:
        company_name: Name of the trucking carrier.
        state: US state abbreviation (optional).

    Returns:
        A search query string.
    """
    query = f'site:linkedin.com/in "{company_name}" Owner OR President'
    if state:
        query += f" {state}"
    logger.debug("Built query: %s", query)
    return query


def search_company(
    company_name: str,
    api_key: str,
    cx: str,
    state: str = "",
    max_results: int = 10,
) -> CompanyResult:
    """Search for decision makers at a single trucking company.

    Args:
        company_name: Carrier name.
        api_key: Google CSE API key.
        cx: Google CSE engine ID.
        state: Optional US state code.
        max_results: Maximum number of results to fetch.

    Returns:
        A CompanyResult with extracted decision makers.
    """
    query = build_query(company_name, state)
    result = CompanyResult(
        company_name=company_name,
        state=state,
        search_query=query,
        search_timestamp=datetime.utcnow().isoformat() + "Z",
    )

    # Validate inputs
    valid, reason = validate_company_name(company_name)
    if not valid:
        result.error = reason
        logger.error("Invalid company name '%s': %s", company_name, reason)
        return result

    valid, reason = validate_state_code(state)
    if not valid:
        result.error = reason
        logger.error("Invalid state '%s': %s", state, reason)
        return result

    try:
        items_collected: list[dict] = []
        fetched = 0
        start = 1
        while fetched < max_results:
            batch_size = min(10, max_results - fetched)
            data = _google_search(query, api_key, cx, num=batch_size, start=start)
            items = data.get("items", [])
            if not items:
                break
            items_collected.extend(items)
            fetched += len(items)
            start += len(items)
            if fetched < max_results and items:
                time.sleep(1)

        if not items_collected:
            logger.info("No results found for '%s'", company_name)
            result.error = "No search results returned"
            return result

        for item in items_collected:
            combined_text = f"{item.get('title', '')} {item.get('snippet', '')}"
            dm = DecisionMaker(
                name=_extract_name_from_result(item),
                title=_extract_title_from_result(item),
                company=_extract_company_from_result(item, company_name),
                linkedin_url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                email=(_extract_emails(combined_text) or [None])[0],
                phone=(_extract_phones(combined_text) or [None])[0],
                confidence=_compute_confidence(item, company_name, DEFAULT_TITLES),
            )
            result.decision_makers.append(dm)

        result.decision_makers.sort(key=lambda d: d.confidence, reverse=True)
        logger.info(
            "Found %d potential decision makers for '%s'",
            len(result.decision_makers),
            company_name,
        )

    except Exception as exc:
        result.error = str(exc)
        logger.error("Error searching for '%s': %s", company_name, exc)

    return result


# ---------------------------------------------------------------------------
# Output - individual .txt files and summary reports
# ---------------------------------------------------------------------------


def _format_dm_txt(dm: DecisionMaker, company_name: str) -> str:
    """Format a single decision maker as a readable text block."""
    lines = [
        f"Name:        {dm.name}",
        f"Title:       {dm.title}",
        f"Company:     {dm.company or company_name}",
        f"LinkedIn:    {dm.linkedin_url}",
        f"Email:       {dm.email or 'N/A'}",
        f"Phone:       {dm.phone or 'N/A'}",
        f"Confidence:  {dm.confidence:.0%}",
    ]
    return "\n".join(lines)


def _save_individual_txt(dm: DecisionMaker, company_name: str, output_dir: Path) -> Path:
    """Save an individual decision maker profile as a .txt file.

    Args:
        dm: DecisionMaker record.
        company_name: Parent company name.
        output_dir: Directory to write into.

    Returns:
        Path to the written file.
    """
    safe_name = re.sub(r"[^\w\s-]", "", dm.name).strip().replace(" ", "_") or "unknown"
    safe_company = re.sub(r"[^\w\s-]", "", company_name).strip().replace(" ", "_")
    filename = f"{safe_company}_{safe_name}.txt"
    path = output_dir / filename

    with open(path, "w") as f:
        f.write(f"Decision Maker Profile\n")
        f.write(f"{'=' * 40}\n")
        f.write(_format_dm_txt(dm, company_name))
        f.write(f"\n{'=' * 40}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")

    logger.debug("Saved profile: %s", path)
    return path


def write_results(results: list[CompanyResult], output_format: str, output_dir: Path) -> Path:
    """Write individual .txt profile files and a summary report.

    Args:
        results: List of CompanyResult objects.
        output_format: 'json' or 'txt'.
        output_dir: Directory for output files.

    Returns:
        Path to the summary report file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    profiles_dir = output_dir / "profiles"
    profiles_dir.mkdir(exist_ok=True)

    # Save individual .txt files for every decision maker
    for cr in results:
        for dm in cr.decision_makers:
            _save_individual_txt(dm, cr.company_name, profiles_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if output_format == "txt":
        report_path = output_dir / f"summary_report_{timestamp}.txt"
        with open(report_path, "w") as f:
            f.write("LinkedIn Decision Maker Finder - Summary Report\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Companies searched: {len(results)}\n")
            total_dm = sum(len(cr.decision_makers) for cr in results)
            f.write(f"Total decision makers found: {total_dm}\n")
            f.write("=" * 60 + "\n\n")

            for cr in results:
                f.write(f"Company: {cr.company_name}\n")
                f.write(f"State: {cr.state or 'N/A'}\n")
                f.write(f"Query: {cr.search_query}\n")
                if cr.error:
                    f.write(f"Error: {cr.error}\n")
                f.write(f"Results: {len(cr.decision_makers)}\n")
                f.write("-" * 40 + "\n")

                for i, dm in enumerate(cr.decision_makers, 1):
                    f.write(f"\n  [{i}] {_format_dm_txt(dm, cr.company_name)}\n")

                f.write("\n" + "=" * 60 + "\n\n")

        logger.info("TXT summary report saved: %s", report_path)

    else:  # json
        report_path = output_dir / f"summary_report_{timestamp}.json"
        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_companies": len(results),
            "total_decision_makers": sum(len(cr.decision_makers) for cr in results),
            "companies": [],
        }
        for cr in results:
            entry = {
                "company_name": cr.company_name,
                "state": cr.state,
                "search_query": cr.search_query,
                "search_timestamp": cr.search_timestamp,
                "error": cr.error,
                "decision_makers": [asdict(dm) for dm in cr.decision_makers],
            }
            payload["companies"].append(entry)
        with open(report_path, "w") as f:
            json.dump(payload, f, indent=2)
        logger.info("JSON summary report saved: %s", report_path)

    return report_path


# ---------------------------------------------------------------------------
# CSV batch input
# ---------------------------------------------------------------------------


def load_csv_carriers(csv_path: str) -> list[dict]:
    """Load carrier records from a CSV file.

    The CSV must have a 'company_name' column. Optional column: 'state'.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        List of dicts with keys: company_name, state.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV is missing the 'company_name' column.
    """
    path = Path(csv_path)
    if not path.exists():
        logger.error("CSV file not found: %s", csv_path)
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    carriers = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if "company_name" not in (reader.fieldnames or []):
            raise ValueError("CSV must contain a 'company_name' column")
        for row in reader:
            name = row["company_name"].strip()
            state = row.get("state", "").strip().upper()

            valid_name, reason = validate_company_name(name)
            if not valid_name:
                logger.warning("Skipping invalid company '%s': %s", name, reason)
                continue

            if state:
                valid_state, reason = validate_state_code(state)
                if not valid_state:
                    logger.warning("Invalid state '%s' for '%s': %s", state, name, reason)
                    state = ""

            carriers.append({"company_name": name, "state": state})

    logger.info("Loaded %d valid carriers from %s", len(carriers), csv_path)
    return carriers


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv).

    Returns:
        Parsed argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Cross-reference trucking company names against LinkedIn via "
            "Google Custom Search to find decision makers (Owner, President, CEO)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Environment variables:\n"
            "  GOOGLE_CSE_API_KEY   Google Custom Search API key\n"
            "  GOOGLE_CSE_CX        Google Custom Search Engine ID\n\n"
            "Examples:\n"
            '  %(prog)s --company-name "ABC Trucking" --state TX\n'
            '  %(prog)s --csv-input carriers.csv --output-format json --max-results 5\n'
            '  %(prog)s --company-name "XYZ Freight" --state CA --verbose\n'
        ),
    )

    input_group = parser.add_argument_group("input options (choose one)")
    input_group.add_argument(
        "--company-name",
        help="Single trucking company name to search for.",
    )
    input_group.add_argument(
        "--csv-input",
        metavar="FILE",
        help="Path to CSV file with a 'company_name' column for batch mode.",
    )

    parser.add_argument(
        "--state",
        default="",
        help="Two-letter US state code to narrow results (e.g. TX, CA).",
    )
    parser.add_argument(
        "--output-format",
        choices=["txt", "json"],
        default="json",
        help="Summary report format: txt or json (default: json).",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum search results per company (default: 10).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging to the console.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help=f"Directory for output files (default: {OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("GOOGLE_CSE_API_KEY", ""),
        help="Google CSE API key (or set GOOGLE_CSE_API_KEY env var).",
    )
    parser.add_argument(
        "--cx",
        default=os.environ.get("GOOGLE_CSE_CX", ""),
        help="Google CSE engine ID (or set GOOGLE_CSE_CX env var).",
    )

    args = parser.parse_args(argv)

    if not args.company_name and not args.csv_input:
        parser.error("Provide either --company-name or --csv-input.")
    if not args.api_key:
        parser.error("Google CSE API key required (--api-key or GOOGLE_CSE_API_KEY env var).")
    if not args.cx:
        parser.error("Google CSE engine ID required (--cx or GOOGLE_CSE_CX env var).")

    return args


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for the LinkedIn Decision Maker Finder.

    Parses arguments, validates inputs, runs searches, and writes output.
    """
    args = parse_args(argv)

    # Apply --verbose
    if args.verbose:
        _ch.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    output_dir = Path(args.output_dir)

    # Validate state if provided via CLI
    if args.state:
        args.state = args.state.strip().upper()
        valid, reason = validate_state_code(args.state)
        if not valid:
            logger.error(reason)
            sys.exit(1)

    # Build carrier list
    carriers: list[dict] = []
    if args.csv_input:
        carriers = load_csv_carriers(args.csv_input)
        if not carriers:
            logger.error("No valid carriers found in CSV. Exiting.")
            sys.exit(1)
    else:
        valid, reason = validate_company_name(args.company_name)
        if not valid:
            logger.error("Invalid company name: %s", reason)
            sys.exit(1)
        carriers = [{"company_name": args.company_name, "state": args.state}]

    logger.info("Processing %d carrier(s) ...", len(carriers))

    results: list[CompanyResult] = []
    for i, carrier in enumerate(carriers, 1):
        name = carrier["company_name"]
        state = carrier.get("state", "") or args.state

        logger.info("[%d/%d] Searching: %s (%s)", i, len(carriers), name, state or "any state")

        cr = search_company(
            company_name=name,
            api_key=args.api_key,
            cx=args.cx,
            state=state,
            max_results=args.max_results,
        )
        results.append(cr)

        if i < len(carriers):
            time.sleep(1.5)

    report_path = write_results(results, args.output_format, output_dir)

    # Print summary to stdout
    total_dm = sum(len(cr.decision_makers) for cr in results)
    errors = sum(1 for cr in results if cr.error)
    print(f"\n{'=' * 60}")
    print(f"  LinkedIn Decision Maker Finder - Summary")
    print(f"{'=' * 60}")
    print(f"  Companies searched : {len(results)}")
    print(f"  Decision makers    : {total_dm}")
    print(f"  Errors             : {errors}")
    print(f"  Report saved to    : {report_path}")
    print(f"  Profiles dir       : {output_dir / 'profiles'}")
    print(f"{'=' * 60}\n")

    for cr in results:
        if cr.error and not cr.decision_makers:
            print(f"  {cr.company_name}: ERROR - {cr.error}")
            continue
        print(f"  {cr.company_name}:")
        for dm in cr.decision_makers[:3]:
            conf_bar = "#" * int(dm.confidence * 10)
            print(f"    [{dm.confidence:.0%} {conf_bar:<10}] {dm.name} - {dm.title}")
            if dm.email:
                print(f"      Email: {dm.email}")
            if dm.phone:
                print(f"      Phone: {dm.phone}")
        if len(cr.decision_makers) > 3:
            print(f"    ... and {len(cr.decision_makers) - 3} more (see report)")
        print()


if __name__ == "__main__":
    main()
