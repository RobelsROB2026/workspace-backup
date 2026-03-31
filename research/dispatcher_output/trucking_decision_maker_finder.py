#!/usr/bin/env python3
"""
Trucking Decision Maker Finder

Searches LinkedIn via Google Search (site:linkedin.com/in) to find decision makers
(Owner, President, CEO, Director) at trucking companies. Extracts profile details
including name, title, location, and profile URL.

Usage:
    python trucking_decision_maker_finder.py --company-name "ABC Trucking"
    python trucking_decision_maker_finder.py --company-name "ABC Trucking" --state TX --limit 5
    python trucking_decision_maker_finder.py --company-name "ABC Trucking" --output-format json
"""

import argparse
import json
import logging
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass, asdict
from typing import List, Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not installed. Run:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ROLE_KEYWORDS = ["Owner", "President", "CEO", "Director", "Founder", "VP"]
GOOGLE_SEARCH_URL = "https://www.google.com/search"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
# Delay between requests to be respectful
REQUEST_DELAY_SECONDS = 2.0


@dataclass
class DecisionMaker:
    """Represents a decision maker found on LinkedIn."""

    full_name: str
    current_title: str
    company: str
    location: str
    profile_url: str
    connection_count: str
    source_query: str


def build_search_query(
    company_name: str,
    state: Optional[str] = None,
    cargo_type: Optional[str] = None,
) -> str:
    """Build a Google search query targeting LinkedIn profiles of decision makers.

    Args:
        company_name: Name of the trucking company.
        state: Optional US state abbreviation to narrow results.
        cargo_type: Optional cargo type to include in the query.

    Returns:
        A Google-dork-style search query string.
    """
    roles = " OR ".join(ROLE_KEYWORDS)
    query = f'site:linkedin.com/in "{company_name}" {roles}'
    if state:
        query += f" {state}"
    if cargo_type:
        query += f' "{cargo_type}"'
    return query


def google_search(query: str, limit: int = 10) -> List[dict]:
    """Search Google and return a list of result dicts with title, url, snippet.

    Args:
        query: The search query string.
        limit: Maximum number of results to return.

    Returns:
        List of dicts with keys: title, url, snippet.
    """
    results: List[dict] = []
    start = 0
    per_page = 10

    while len(results) < limit:
        params = {
            "q": query,
            "start": start,
            "num": min(per_page, limit - len(results)),
            "hl": "en",
        }
        url = f"{GOOGLE_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        logger.info("Searching Google: %s", query[:80])
        logger.debug("Request URL: %s", url)

        try:
            resp = requests.get(
                GOOGLE_SEARCH_URL,
                params=params,
                headers=REQUEST_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Google search request failed: %s", exc)
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Google wraps each result in a div; links to linkedin are what we want.
        found_any = False
        for g in soup.select("div.g, div[data-hveid]"):
            link_tag = g.select_one("a[href]")
            if not link_tag:
                continue
            href = link_tag.get("href", "")
            # Filter to linkedin profile URLs
            if "linkedin.com/in/" not in href:
                continue

            title = link_tag.get_text(strip=True)
            snippet_tag = g.select_one("div.VwiC3b, span.st, div[data-sncf]")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            results.append({"title": title, "url": href, "snippet": snippet})
            found_any = True
            if len(results) >= limit:
                break

        if not found_any:
            # Also try extracting from all <a> tags as a fallback
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                # Google sometimes wraps URLs in /url?q=...
                if "/url?q=" in href:
                    parsed = urllib.parse.urlparse(href)
                    qs = urllib.parse.parse_qs(parsed.query)
                    href = qs.get("q", [href])[0]
                if "linkedin.com/in/" not in href:
                    continue
                title = a_tag.get_text(strip=True)
                if not title or len(title) < 3:
                    continue
                results.append({"title": title, "url": href, "snippet": ""})
                found_any = True
                if len(results) >= limit:
                    break

        if not found_any:
            logger.warning("No more LinkedIn results found on this page.")
            break

        start += per_page
        if start > 0:
            time.sleep(REQUEST_DELAY_SECONDS)

    logger.info("Found %d LinkedIn result(s) for query.", len(results))
    return results[:limit]


def fetch_linkedin_profile(url: str) -> dict:
    """Fetch a LinkedIn profile page and extract available metadata.

    Note: LinkedIn heavily restricts scraping. This function extracts what is
    available from the public page HTML and meta tags. Results may be partial.

    Args:
        url: Full LinkedIn profile URL.

    Returns:
        Dict with keys: full_name, title, location, connection_count.
    """
    info = {
        "full_name": "",
        "title": "",
        "location": "",
        "connection_count": "",
    }

    logger.info("Fetching LinkedIn profile: %s", url)
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch LinkedIn profile %s: %s", url, exc)
        return info

    soup = BeautifulSoup(resp.text, "html.parser")

    # Try <title> tag: typically "FirstName LastName - Title - Company | LinkedIn"
    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.get_text(strip=True)
        title_text = title_text.replace(" | LinkedIn", "")
        parts = [p.strip() for p in title_text.split(" - ") if p.strip()]
        if len(parts) >= 1:
            info["full_name"] = parts[0]
        if len(parts) >= 2:
            info["title"] = parts[1]

    # Try og:title meta tag
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        content = og_title["content"].replace(" | LinkedIn", "")
        parts = [p.strip() for p in content.split(" - ") if p.strip()]
        if len(parts) >= 1 and not info["full_name"]:
            info["full_name"] = parts[0]
        if len(parts) >= 2 and not info["title"]:
            info["title"] = parts[1]

    # Try og:description for location and connection info
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        desc = og_desc["content"]
        # Often: "Location · 500+ connections · ..."
        loc_match = re.match(r"^([^·]+)", desc)
        if loc_match:
            candidate = loc_match.group(1).strip()
            # Basic heuristic: locations are short and don't start with verbs
            if len(candidate) < 60:
                info["location"] = candidate

        conn_match = re.search(r"(\d[\d,+]*\+?)\s*connections?", desc, re.IGNORECASE)
        if conn_match:
            info["connection_count"] = conn_match.group(1)

    # description meta tag as fallback
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        desc = desc_tag["content"]
        if not info["location"]:
            loc_match = re.match(r"^([^·]+)", desc)
            if loc_match:
                candidate = loc_match.group(1).strip()
                if len(candidate) < 60:
                    info["location"] = candidate
        if not info["connection_count"]:
            conn_match = re.search(
                r"(\d[\d,+]*\+?)\s*connections?", desc, re.IGNORECASE
            )
            if conn_match:
                info["connection_count"] = conn_match.group(1)

    return info


def parse_name_title_from_search(title: str, snippet: str) -> tuple:
    """Extract name and title from a Google search result title/snippet.

    Args:
        title: The search result title.
        snippet: The search result snippet text.

    Returns:
        Tuple of (full_name, current_title).
    """
    full_name = ""
    current_title = ""

    # Google search titles for LinkedIn are usually:
    #   "FirstName LastName - Title - Company | LinkedIn"
    cleaned = title.replace(" | LinkedIn", "").replace("| LinkedIn", "")
    parts = [p.strip() for p in cleaned.split(" - ") if p.strip()]

    if len(parts) >= 1:
        full_name = parts[0]
    if len(parts) >= 2:
        current_title = parts[1]

    # Try to find role keywords in snippet if title didn't yield a title
    if not current_title and snippet:
        for role in ROLE_KEYWORDS:
            if role.lower() in snippet.lower():
                # Try to extract surrounding context
                pattern = rf"(\b\w*\s*{role}\b[^.,;]*)"
                match = re.search(pattern, snippet, re.IGNORECASE)
                if match:
                    current_title = match.group(1).strip()[:100]
                    break

    return full_name, current_title


def extract_location_from_snippet(snippet: str) -> str:
    """Try to extract a location from a Google snippet.

    Args:
        snippet: The Google search result snippet.

    Returns:
        Extracted location string, or empty string.
    """
    if not snippet:
        return ""
    # Common patterns: "City, State" or "City, ST"
    loc_match = re.search(
        r"([A-Z][a-zA-Z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)", snippet
    )
    if loc_match:
        return loc_match.group(1).strip()
    return ""


def find_decision_makers(
    company_name: str,
    state: Optional[str] = None,
    cargo_type: Optional[str] = None,
    limit: int = 10,
) -> List[DecisionMaker]:
    """Find decision makers at a trucking company via Google/LinkedIn search.

    Args:
        company_name: Name of the trucking company to search.
        state: Optional US state to narrow the search.
        cargo_type: Optional cargo type specialization.
        limit: Maximum number of results to return.

    Returns:
        List of DecisionMaker dataclass instances.
    """
    query = build_search_query(company_name, state, cargo_type)
    logger.info("Built search query: %s", query)

    search_results = google_search(query, limit=limit)
    if not search_results:
        logger.warning("No search results found for '%s'.", company_name)
        return []

    decision_makers: List[DecisionMaker] = []

    for result in search_results:
        url = result["url"]
        title = result.get("title", "")
        snippet = result.get("snippet", "")

        # Extract info from search result first
        full_name, current_title = parse_name_title_from_search(title, snippet)
        location = extract_location_from_snippet(snippet)

        # Attempt to enrich from the LinkedIn page itself
        time.sleep(REQUEST_DELAY_SECONDS)
        profile_info = fetch_linkedin_profile(url)

        # Merge: prefer LinkedIn page data when available
        if profile_info["full_name"]:
            full_name = profile_info["full_name"]
        if profile_info["title"]:
            current_title = profile_info["title"]
        if profile_info["location"]:
            location = profile_info["location"]
        connection_count = profile_info.get("connection_count", "")

        # Skip results without a name
        if not full_name or full_name.lower() == "linkedin":
            logger.debug("Skipping result with no usable name: %s", url)
            continue

        dm = DecisionMaker(
            full_name=full_name,
            current_title=current_title,
            company=company_name,
            location=location,
            profile_url=url,
            connection_count=connection_count,
            source_query=query,
        )
        decision_makers.append(dm)
        logger.info("Found: %s — %s", dm.full_name, dm.current_title)

    return decision_makers


def format_text(decision_makers: List[DecisionMaker], company_name: str) -> str:
    """Format decision makers as human-readable text.

    Args:
        decision_makers: List of DecisionMaker instances.
        company_name: The company that was searched.

    Returns:
        Formatted multi-line string.
    """
    lines = [
        f"Decision Makers at: {company_name}",
        "=" * 60,
        f"Results found: {len(decision_makers)}",
        "",
    ]
    for i, dm in enumerate(decision_makers, 1):
        lines.append(f"--- Result {i} ---")
        lines.append(f"  Name:        {dm.full_name}")
        lines.append(f"  Title:       {dm.current_title or 'N/A'}")
        lines.append(f"  Company:     {dm.company}")
        lines.append(f"  Location:    {dm.location or 'N/A'}")
        lines.append(f"  Connections: {dm.connection_count or 'N/A'}")
        lines.append(f"  Profile URL: {dm.profile_url}")
        lines.append("")

    return "\n".join(lines)


def format_json(decision_makers: List[DecisionMaker], company_name: str) -> str:
    """Format decision makers as JSON.

    Args:
        decision_makers: List of DecisionMaker instances.
        company_name: The company that was searched.

    Returns:
        JSON string.
    """
    output = {
        "company": company_name,
        "result_count": len(decision_makers),
        "decision_makers": [asdict(dm) for dm in decision_makers],
    }
    return json.dumps(output, indent=2)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Find decision makers (Owner, President, CEO, Director) at trucking "
            "companies by searching LinkedIn profiles via Google."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  %(prog)s --company-name "Swift Transportation"\n'
            '  %(prog)s --company-name "ABC Trucking" --state TX --limit 5\n'
            '  %(prog)s --company-name "XYZ Logistics" --output-format json\n'
            '  %(prog)s --company-name "Hauler Inc" --cargo-type "flatbed"\n'
        ),
    )
    parser.add_argument(
        "--company-name",
        required=True,
        help="Name of the trucking company to search for.",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="US state abbreviation to narrow search results (e.g., TX, CA).",
    )
    parser.add_argument(
        "--cargo-type",
        default=None,
        help="Cargo type specialization to include in search (e.g., flatbed, reefer).",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="text",
        help="Output format: json or text (default: text).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results to return (default: 10).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging.",
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(
        "Searching for decision makers at '%s'%s",
        args.company_name,
        f" in {args.state}" if args.state else "",
    )

    decision_makers = find_decision_makers(
        company_name=args.company_name,
        state=args.state,
        cargo_type=args.cargo_type,
        limit=args.limit,
    )

    if args.output_format == "json":
        output = format_json(decision_makers, args.company_name)
    else:
        output = format_text(decision_makers, args.company_name)

    print(output)

    if not decision_makers:
        logger.warning("No decision makers found. Try broadening your search.")
        sys.exit(1)


if __name__ == "__main__":
    main()
