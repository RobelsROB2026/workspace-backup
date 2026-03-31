#!/usr/bin/env python3
"""
DOT Number Web Search & Contact Extractor

Looks up carrier details from the FMCSA Socrata API by DOT number, searches
the web for official company websites, and scrapes email addresses and phone
numbers from those sites.

Dataset: FMCSA Census — Active & Authorized Motor Carriers
Endpoint: https://data.transportation.gov/resource/az4b-hbig.json

Usage:
    # Search for a single DOT number
    python dot_number_web_search.py --dot-numbers 1234567

    # Search for multiple DOT numbers (comma-separated)
    python dot_number_web_search.py --dot-numbers 1234567,2345678,3456789

    # Pass as JSON list
    python dot_number_web_search.py --dot-numbers '[1234567, 2345678]'

    # Save results to CSV
    python dot_number_web_search.py --dot-numbers 1234567,2345678 --output-csv results.csv

Requirements:
    pip install requests beautifulsoup4 duckduckgo-search
"""

import argparse
import csv
import json
import logging
import re
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

FMCSA_API = "https://data.transportation.gov/resource/az4b-hbig.json"
REQUEST_TIMEOUT = 20
SEARCH_PAUSE = 1.5  # seconds between web searches to avoid rate limits
SCRAPE_PAUSE = 1.0

CSV_HEADERS = [
    "DOT Number",
    "Company Name",
    "MC Number",
    "FMCSA Phone",
    "State",
    "Website",
    "Scraped Emails",
    "Scraped Phones",
]

# Regex patterns for contact extraction
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)
PHONE_RE = re.compile(
    r"""(?:\+?1[\s.\-]?)?"""           # optional country code
    r"""(?:\(?\d{3}\)?[\s.\-]?)"""      # area code
    r"""\d{3}[\s.\-]?\d{4}"""           # subscriber number
    r"""(?:\s*(?:ext|x|ext\.)\s*\d+)?""",  # optional extension
    re.VERBOSE,
)

# Domains to skip when filtering search results
SKIP_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "linkedin.com", "instagram.com",
    "youtube.com", "tiktok.com", "reddit.com", "wikipedia.org", "yelp.com",
    "bbb.org", "indeed.com", "glassdoor.com", "zoominfo.com",
    "dnb.com", "manta.com", "buzzfile.com", "opencorporates.com",
    "safer.fmcsa.dot.gov", "data.transportation.gov",
}

# Junk emails to filter out
JUNK_EMAIL_PATTERNS = [
    "sentry.io", "example.com", "wixpress.com", "googleapis.com",
    "sentry-next.wixpress.com", "protection.outlook.com",
    ".png", ".jpg", ".gif", ".svg", ".webp",
]


def parse_dot_numbers(raw: str) -> list[int]:
    """Parse DOT numbers from comma-separated string or JSON list."""
    raw = raw.strip()
    # Try JSON first
    if raw.startswith("["):
        try:
            nums = json.loads(raw)
            return [int(n) for n in nums]
        except (json.JSONDecodeError, ValueError) as exc:
            raise argparse.ArgumentTypeError(
                f"Invalid JSON list of DOT numbers: {exc}"
            ) from exc
    # Comma-separated
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    results = []
    for p in parts:
        try:
            results.append(int(p))
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"Invalid DOT number '{p}' — must be an integer"
            ) from exc
    if not results:
        raise argparse.ArgumentTypeError("No DOT numbers provided")
    return results


def fetch_carrier(dot_number: int) -> dict | None:
    """Query FMCSA Socrata API for a single DOT number."""
    params = {
        "$where": f"dot_number={dot_number}",
        "$limit": 1,
    }
    try:
        resp = requests.get(FMCSA_API, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        rows = resp.json()
        if rows:
            return rows[0]
        logger.warning("DOT %s: no record found in FMCSA database", dot_number)
        return None
    except requests.RequestException as exc:
        logger.error("DOT %s: FMCSA API error — %s", dot_number, exc)
        return None


def search_website(company_name: str, state: str = "") -> str | None:
    """Search the web for the company's official website."""
    query = f"{company_name} {state} trucking company official website".strip()
    logger.info("Searching web: %s", query)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10))
    except Exception as exc:
        logger.error("Web search failed for '%s': %s", company_name, exc)
        return None

    for r in results:
        url = r.get("href", "")
        domain = urlparse(url).netloc.lower().lstrip("www.")
        if domain and not any(skip in domain for skip in SKIP_DOMAINS):
            logger.info("Found website: %s", url)
            return url
    logger.warning("No website found for '%s'", company_name)
    return None


def is_junk_email(email: str) -> bool:
    """Filter out image filenames, tracking pixels, and junk addresses."""
    email_lower = email.lower()
    return any(pat in email_lower for pat in JUNK_EMAIL_PATTERNS)


def scrape_contacts(url: str) -> tuple[list[str], list[str]]:
    """Scrape email addresses and phone numbers from a URL and its contact page."""
    emails, phones = set(), set()
    pages_to_scrape = [url]

    # Fetch main page first and look for contact page link
    try:
        resp = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
            allow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        _extract_contacts(soup, resp.text, emails, phones)

        # Find contact page links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].lower()
            text = a_tag.get_text(strip=True).lower()
            if any(kw in href or kw in text for kw in ["contact", "about"]):
                full_url = urljoin(url, a_tag["href"])
                if full_url not in pages_to_scrape:
                    pages_to_scrape.append(full_url)
    except requests.RequestException as exc:
        logger.error("Failed to scrape %s: %s", url, exc)
        return sorted(emails), sorted(phones)

    # Scrape contact/about pages
    for page_url in pages_to_scrape[1:3]:  # limit to 2 extra pages
        time.sleep(SCRAPE_PAUSE)
        try:
            resp = requests.get(
                page_url,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
                allow_redirects=True,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            _extract_contacts(soup, resp.text, emails, phones)
        except requests.RequestException as exc:
            logger.warning("Failed to scrape %s: %s", page_url, exc)

    return sorted(emails), sorted(phones)


def _extract_contacts(
    soup: BeautifulSoup, raw_html: str, emails: set, phones: set
) -> None:
    """Extract emails and phones from parsed HTML and raw text."""
    # Get visible text
    text = soup.get_text(separator=" ")

    # Also check mailto: links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("mailto:"):
            addr = href[7:].split("?")[0].strip()
            if EMAIL_RE.fullmatch(addr) and not is_junk_email(addr):
                emails.add(addr)
        elif href.startswith("tel:"):
            phone = re.sub(r"[^\d+]", "", href[4:])
            if len(phone) >= 10:
                phones.add(phone)

    # Regex over visible text
    for match in EMAIL_RE.findall(text):
        if not is_junk_email(match):
            emails.add(match)
    for match in PHONE_RE.findall(text):
        cleaned = re.sub(r"[^\d]", "", match)
        if 10 <= len(cleaned) <= 11:
            phones.add(match.strip())


def process_dot_number(dot_number: int) -> dict:
    """Full pipeline for one DOT number: API lookup -> web search -> scrape."""
    result = {
        "dot_number": dot_number,
        "company_name": "",
        "mc_number": "",
        "fmcsa_phone": "",
        "state": "",
        "website": "",
        "emails": [],
        "phones": [],
    }

    # Step 1: FMCSA lookup
    carrier = fetch_carrier(dot_number)
    if carrier:
        result["company_name"] = carrier.get("legal_name", "")
        result["mc_number"] = carrier.get("mc_number", "")
        result["fmcsa_phone"] = carrier.get("phone", "")
        result["state"] = carrier.get("phy_state", "")
        logger.info(
            "DOT %s: %s (%s)",
            dot_number,
            result["company_name"],
            result["state"],
        )
    else:
        logger.warning("DOT %s: skipping web search — no carrier data", dot_number)
        return result

    # Step 2: Web search for official website
    time.sleep(SEARCH_PAUSE)
    website = search_website(result["company_name"], result["state"])
    if website:
        result["website"] = website

        # Step 3: Scrape contacts
        time.sleep(SCRAPE_PAUSE)
        emails, phones = scrape_contacts(website)
        result["emails"] = emails
        result["phones"] = phones
        logger.info(
            "DOT %s: found %d email(s), %d phone(s)",
            dot_number,
            len(emails),
            len(phones),
        )
    return result


def write_csv(results: list[dict], path: str) -> None:
    """Write results to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for r in results:
            writer.writerow([
                r["dot_number"],
                r["company_name"],
                r["mc_number"],
                r["fmcsa_phone"],
                r["state"],
                r["website"],
                "; ".join(r["emails"]),
                "; ".join(r["phones"]),
            ])
    logger.info("CSV saved to %s (%d rows)", path, len(results))


def print_results(results: list[dict]) -> None:
    """Print results to stdout in a readable format."""
    for r in results:
        print(f"\n{'=' * 60}")
        print(f"DOT Number:   {r['dot_number']}")
        print(f"Company:      {r['company_name']}")
        print(f"MC Number:    {r['mc_number']}")
        print(f"FMCSA Phone:  {r['fmcsa_phone']}")
        print(f"State:        {r['state']}")
        print(f"Website:      {r['website'] or 'Not found'}")
        print(f"Emails:       {', '.join(r['emails']) or 'None found'}")
        print(f"Phones:       {', '.join(r['phones']) or 'None found'}")
    print(f"\n{'=' * 60}")
    print(f"Total: {len(results)} carrier(s) processed")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Look up FMCSA carriers by DOT number, search for their official "
            "websites, and extract contact information (emails and phone numbers)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --dot-numbers 1234567\n"
            "  %(prog)s --dot-numbers 1234567,2345678,3456789\n"
            "  %(prog)s --dot-numbers '[1234567, 2345678]'\n"
            "  %(prog)s --dot-numbers 1234567,2345678 --output-csv results.csv\n"
        ),
    )
    parser.add_argument(
        "--dot-numbers",
        required=True,
        help=(
            "DOT numbers to search. Accepts comma-separated values "
            "(e.g. 1234567,2345678) or a JSON array (e.g. '[1234567, 2345678]')."
        ),
    )
    parser.add_argument(
        "--output-csv",
        metavar="FILE",
        help="Save results to a CSV file.",
    )
    args = parser.parse_args()

    try:
        dot_numbers = parse_dot_numbers(args.dot_numbers)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    logger.info("Processing %d DOT number(s): %s", len(dot_numbers), dot_numbers)

    results = []
    for i, dot in enumerate(dot_numbers, 1):
        logger.info("--- [%d/%d] DOT %s ---", i, len(dot_numbers), dot)
        result = process_dot_number(dot)
        results.append(result)

    if args.output_csv:
        write_csv(results, args.output_csv)

    print_results(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
