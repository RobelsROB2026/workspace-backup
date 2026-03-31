#!/usr/bin/env python3
"""
DOT Contact Extractor

Searches the web for official company websites associated with USDOT numbers,
then extracts email addresses and phone numbers from those websites.
Results are saved to a CSV file.

Usage:
    python dot_contact_extractor.py --dot-numbers 1234567 2345678 --output-csv contacts.csv
"""

import argparse
import csv
import logging
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

FMCSA_SEARCH_URL = "https://safer.fmcsa.dot.gov/query.asp"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 15

# Regex patterns for extraction
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE
)
PHONE_PATTERN = re.compile(
    r"""
    (?:
        \+?1[\s.\-]?          # optional country code
    )?
    \(?[2-9]\d{2}\)?          # area code with optional parens
    [\s.\-]?                  # separator
    [2-9]\d{2}                # exchange
    [\s.\-]?                  # separator
    \d{4}                     # subscriber
    """,
    re.VERBOSE,
)

# Common image/asset emails to skip
JUNK_EMAIL_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "googleapis.com",
    "w3.org", "schema.org", "facebook.com", "twitter.com",
    "google.com", "apple.com", "microsoft.com",
}


def lookup_company_name(dot_number: str) -> str:
    """Look up the company name from FMCSA SAFER for a given DOT number."""
    try:
        resp = requests.post(
            FMCSA_SEARCH_URL,
            data={
                "searchtype": "ANY",
                "query_type": "queryCarrierSnapshot",
                "query_param": "USDOT",
                "query_string": dot_number,
            },
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # The company name appears in a specific table cell on SAFER
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            for i, cell in enumerate(cells):
                if "Legal Name" in cell.get_text():
                    if i + 1 < len(cells):
                        return cells[i + 1].get_text(strip=True)
        # Fallback: try looking for it in a center tag or bold text
        center_tags = soup.find_all("center")
        for tag in center_tags:
            text = tag.get_text(strip=True)
            if text and len(text) > 3 and "FMCSA" not in text and "query" not in text.lower():
                return text
    except requests.RequestException as e:
        logger.warning("FMCSA lookup failed for DOT %s: %s", dot_number, e)
    return ""


def search_company_website(dot_number: str, company_name: str) -> str:
    """Search for the company's official website using a web search query.

    Tries a Google search for the DOT number or company name to find the
    official website URL.
    """
    queries = []
    if company_name:
        queries.append(f'"{company_name}" trucking company official website')
        queries.append(f'USDOT {dot_number} "{company_name}"')
    queries.append(f"USDOT {dot_number} official website")

    for query in queries:
        try:
            resp = requests.get(
                "https://www.google.com/search",
                params={"q": query, "num": 5},
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract URLs from search results
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                # Google wraps results in /url?q=... redirects
                if href.startswith("/url?q="):
                    url = href.split("/url?q=")[1].split("&")[0]
                    if _is_candidate_website(url):
                        logger.info("Found candidate website for DOT %s: %s", dot_number, url)
                        return url
        except requests.RequestException as e:
            logger.warning("Search failed for DOT %s with query '%s': %s", dot_number, query, e)

    return ""


def _is_candidate_website(url: str) -> bool:
    """Check if a URL looks like a real company website (not a directory/social site)."""
    skip_domains = {
        "google.com", "facebook.com", "twitter.com", "linkedin.com",
        "yelp.com", "bbb.org", "yellowpages.com", "manta.com",
        "dnb.com", "zoominfo.com", "fmcsa.dot.gov", "safer.fmcsa.dot.gov",
        "wikipedia.org", "youtube.com", "instagram.com", "tiktok.com",
        "indeed.com", "glassdoor.com", "mapquest.com",
    }
    url_lower = url.lower()
    for domain in skip_domains:
        if domain in url_lower:
            return False
    return url_lower.startswith("http")


def extract_emails(soup: BeautifulSoup, page_text: str) -> list[str]:
    """Extract unique email addresses from page content and mailto links."""
    emails = set()

    # From mailto links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("mailto:"):
            email = href.replace("mailto:", "").split("?")[0].strip()
            if email:
                emails.add(email.lower())

    # From page text via regex
    for match in EMAIL_PATTERN.findall(page_text):
        emails.add(match.lower())

    # Filter junk
    filtered = []
    for email in emails:
        domain = email.split("@")[1] if "@" in email else ""
        if domain not in JUNK_EMAIL_DOMAINS and not email.endswith((".png", ".jpg", ".gif", ".css", ".js")):
            filtered.append(email)

    return sorted(filtered)


def extract_phones(soup: BeautifulSoup, page_text: str) -> list[str]:
    """Extract unique phone numbers from page content and tel links."""
    phones = set()

    # From tel links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("tel:"):
            phone = href.replace("tel:", "").strip()
            if phone:
                phones.add(phone)

    # From page text via regex
    for match in PHONE_PATTERN.findall(page_text):
        cleaned = match.strip()
        # Only keep numbers that have 10+ digits
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) >= 10:
            phones.add(cleaned)

    return sorted(phones)


def fetch_and_extract(url: str) -> dict:
    """Fetch a website URL and extract contact information.

    Returns a dict with 'emails' and 'phones' lists.
    """
    result = {"emails": [], "phones": []}
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script and style elements for cleaner text extraction
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        page_text = soup.get_text(separator=" ", strip=True)
        result["emails"] = extract_emails(soup, page_text)
        result["phones"] = extract_phones(soup, page_text)

        # If no contact info on homepage, try /contact or /about pages
        if not result["emails"] and not result["phones"]:
            for path in ["/contact", "/contact-us", "/about", "/about-us"]:
                contact_url = url.rstrip("/") + path
                try:
                    resp2 = requests.get(
                        contact_url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True
                    )
                    if resp2.status_code == 200:
                        soup2 = BeautifulSoup(resp2.text, "html.parser")
                        for tag in soup2(["script", "style", "noscript"]):
                            tag.decompose()
                        text2 = soup2.get_text(separator=" ", strip=True)
                        result["emails"] = extract_emails(soup2, text2)
                        result["phones"] = extract_phones(soup2, text2)
                        if result["emails"] or result["phones"]:
                            logger.info("Found contact info on %s", contact_url)
                            break
                except requests.RequestException:
                    continue

    except requests.RequestException as e:
        logger.warning("Failed to fetch %s: %s", url, e)

    return result


def process_dot_number(dot_number: str) -> dict:
    """Process a single DOT number: lookup company, find website, extract contacts.

    Returns a dict with all extracted fields.
    """
    logger.info("Processing DOT# %s", dot_number)
    record = {
        "dot_number": dot_number,
        "company_name": "",
        "website_url": "",
        "email_address": "",
        "phone_number": "",
        "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Step 1: Look up company name from FMCSA
    company_name = lookup_company_name(dot_number)
    record["company_name"] = company_name
    logger.info("DOT# %s -> Company: %s", dot_number, company_name or "(not found)")

    # Step 2: Search for official website
    website_url = search_company_website(dot_number, company_name)
    record["website_url"] = website_url
    if not website_url:
        logger.warning("No website found for DOT# %s", dot_number)
        return record

    # Step 3: Fetch website and extract contact info
    contact_info = fetch_and_extract(website_url)
    record["email_address"] = "; ".join(contact_info["emails"]) if contact_info["emails"] else ""
    record["phone_number"] = "; ".join(contact_info["phones"]) if contact_info["phones"] else ""

    logger.info(
        "DOT# %s -> Emails: %d, Phones: %d",
        dot_number,
        len(contact_info["emails"]),
        len(contact_info["phones"]),
    )
    return record


def main():
    """CLI entry point. Parses arguments and orchestrates the extraction pipeline."""
    parser = argparse.ArgumentParser(
        description="Extract contact information (email, phone) for trucking companies by DOT number.",
        epilog="Example: python dot_contact_extractor.py --dot-numbers 1234567 2345678 --output-csv contacts.csv",
    )
    parser.add_argument(
        "--dot-numbers",
        nargs="+",
        required=True,
        help="One or more USDOT numbers to look up (space-separated).",
    )
    parser.add_argument(
        "--output-csv",
        default="dot_contacts.csv",
        help="Path for the output CSV file (default: dot_contacts.csv).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    results = []
    for dot in args.dot_numbers:
        dot_clean = dot.strip().lstrip("0")
        if not dot_clean.isdigit():
            logger.error("Invalid DOT number: %s (skipping)", dot)
            continue
        record = process_dot_number(dot_clean)
        results.append(record)

    # Write CSV
    fieldnames = [
        "dot_number",
        "company_name",
        "website_url",
        "email_address",
        "phone_number",
        "extraction_date",
    ]
    try:
        with open(args.output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        logger.info("Wrote %d records to %s", len(results), args.output_csv)
    except OSError as e:
        logger.error("Failed to write CSV: %s", e)
        sys.exit(1)

    # Print summary
    print(f"\nProcessed {len(results)} DOT number(s).")
    found = sum(1 for r in results if r["email_address"] or r["phone_number"])
    print(f"Contact info found for {found}/{len(results)} carriers.")
    print(f"Output saved to: {args.output_csv}")


if __name__ == "__main__":
    main()
