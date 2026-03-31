#!/usr/bin/env python3
"""
Hypnotherapy Efficacy Meta-Analysis Pipeline

Queries Google Scholar for hypnotherapy efficacy meta-analyses,
extracts study metadata (title, authors, year, effect sizes, etc.),
and generates a comparative CSV report sorted by condition and effect size.

Supports two modes:
  1. Direct scraping via requests + BeautifulSoup (default, no API key needed)
  2. SerpAPI (set SERPAPI_KEY env var for structured JSON results)

Usage:
    python hypnotherapy_efficacy_pipeline.py \
        --search-terms "hypnotherapy efficacy meta-analysis" \
        --conditions anxiety,pain,smoking \
        --output-csv results.csv \
        --limit 20
"""

import argparse
import csv
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, fields
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCHOLAR_BASE = "https://scholar.google.com/scholar"
SERPAPI_BASE = "https://serpapi.com/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class StudyRecord:
    """Represents one study extracted from search results."""
    study_title: str = ""
    authors: str = ""
    year: str = ""
    journal: str = ""
    condition: str = ""
    sample_size: str = ""
    success_rate_or_effect_size: str = ""
    methodology: str = ""
    notes: str = ""

    @property
    def effect_size_sort_key(self) -> float:
        """Extract a numeric effect size for sorting (descending).

        Tries to parse the first decimal number from the effect-size field.
        Returns 0.0 when nothing numeric is found.
        """
        match = re.search(r"[\d]+\.?\d*", self.success_rate_or_effect_size)
        return float(match.group()) if match else 0.0


CSV_COLUMNS = [f.name for f in fields(StudyRecord)]

# ---------------------------------------------------------------------------
# Scholar scraping helpers
# ---------------------------------------------------------------------------

def _request_with_retry(url: str, params: dict | None = None,
                        retries: int = 3, backoff: float = 2.0) -> requests.Response:
    """GET *url* with exponential back-off on transient failures."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
            if resp.status_code == 429:
                wait = backoff ** attempt
                logger.warning("Rate-limited (429). Waiting %.1fs before retry %d/%d",
                               wait, attempt, retries)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            wait = backoff ** attempt
            logger.warning("Request failed (%s). Retry %d/%d in %.1fs",
                           exc, attempt, retries, wait)
            time.sleep(wait)
    raise RuntimeError("Unreachable")


def _parse_snippet_for_metadata(snippet: str) -> dict:
    """Heuristically pull effect sizes, sample sizes, and methodology from a snippet."""
    meta: dict = {}

    # Effect sizes: Cohen's d, Hedges' g, odds ratio, risk ratio, SMD, %
    es_patterns = [
        r"(?:Cohen'?s?\s*d|d)\s*[=:]\s*([\d.]+)",
        r"(?:Hedges'?\s*g|g)\s*[=:]\s*([\d.]+)",
        r"(?:odds\s*ratio|OR)\s*[=:]\s*([\d.]+)",
        r"(?:risk\s*ratio|RR)\s*[=:]\s*([\d.]+)",
        r"(?:SMD|standardized\s*mean\s*difference)\s*[=:]\s*([\d.]+)",
        r"(?:effect\s*size)\s*[=:of]*\s*([\d.]+)",
        r"(\d{1,3}(?:\.\d+)?)\s*%\s*(?:success|efficacy|improvement|remission|abstinence)",
    ]
    for pat in es_patterns:
        m = re.search(pat, snippet, re.IGNORECASE)
        if m:
            meta["effect_size"] = m.group(0).strip()
            break

    # Sample size
    m = re.search(r"[Nn]\s*[=:]\s*([\d,]+)|(\d[\d,]+)\s*(?:participants|patients|subjects|samples)",
                  snippet, re.IGNORECASE)
    if m:
        meta["sample_size"] = (m.group(1) or m.group(2)).replace(",", "")

    # Methodology
    meth_keywords = [
        "meta-analysis", "systematic review", "randomized controlled trial",
        "RCT", "controlled trial", "cohort study", "case study",
        "double-blind", "single-blind", "crossover",
    ]
    found = [kw for kw in meth_keywords if kw.lower() in snippet.lower()]
    if found:
        meta["methodology"] = "; ".join(found)

    return meta


def _detect_condition(text: str, conditions: list[str]) -> str:
    """Return the first matching condition found in *text*, or 'general'."""
    lower = text.lower()
    for cond in conditions:
        if cond.lower() in lower:
            return cond
    return "general"


# ---------------------------------------------------------------------------
# Google Scholar direct scraping
# ---------------------------------------------------------------------------

def scrape_scholar_direct(query: str, limit: int) -> list[dict]:
    """Scrape Google Scholar search results page by page.

    Returns a list of raw result dicts with keys:
        title, authors_year_source, snippet, link
    """
    results: list[dict] = []
    start = 0
    per_page = 10  # Scholar returns 10 per page

    while len(results) < limit:
        params = {"q": query, "start": start, "hl": "en"}
        logger.info("Fetching Scholar results (start=%d) ...", start)
        try:
            resp = _request_with_retry(SCHOLAR_BASE, params=params)
        except requests.RequestException as exc:
            logger.error("Failed to fetch Scholar page: %s", exc)
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        entries = soup.select("div.gs_r.gs_or.gs_scl")
        if not entries:
            # Fallback selector
            entries = soup.select("div.gs_ri")
        if not entries:
            logger.warning("No results found on page (start=%d). "
                           "Scholar may be blocking requests.", start)
            break

        for entry in entries:
            if len(results) >= limit:
                break

            title_el = entry.select_one("h3.gs_rt a") or entry.select_one("h3.gs_rt")
            title = title_el.get_text(strip=True) if title_el else ""
            link = title_el.get("href", "") if title_el and title_el.name == "a" else ""

            meta_el = entry.select_one("div.gs_a")
            authors_year_source = meta_el.get_text(strip=True) if meta_el else ""

            snippet_el = entry.select_one("div.gs_rs")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            results.append({
                "title": title,
                "authors_year_source": authors_year_source,
                "snippet": snippet,
                "link": link,
            })

        start += per_page
        # Polite delay between pages
        time.sleep(2)

    logger.info("Scraped %d results via direct Scholar access.", len(results))
    return results


# ---------------------------------------------------------------------------
# SerpAPI pathway
# ---------------------------------------------------------------------------

def scrape_scholar_serpapi(query: str, limit: int, api_key: str) -> list[dict]:
    """Fetch Google Scholar results via SerpAPI.

    Returns the same dict structure as *scrape_scholar_direct*.
    """
    results: list[dict] = []
    start = 0

    while len(results) < limit:
        params = {
            "engine": "google_scholar",
            "q": query,
            "start": start,
            "num": min(limit - len(results), 20),
            "api_key": api_key,
            "hl": "en",
        }
        logger.info("Fetching SerpAPI results (start=%d) ...", start)
        try:
            resp = _request_with_retry(SERPAPI_BASE, params=params)
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            logger.error("SerpAPI request failed: %s", exc)
            break

        organic = data.get("organic_results", [])
        if not organic:
            logger.warning("No organic results from SerpAPI at offset %d.", start)
            break

        for item in organic:
            if len(results) >= limit:
                break
            pub = item.get("publication_info", {})
            results.append({
                "title": item.get("title", ""),
                "authors_year_source": pub.get("summary", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
            })

        start += len(organic)

    logger.info("Fetched %d results via SerpAPI.", len(results))
    return results


# ---------------------------------------------------------------------------
# Result processing
# ---------------------------------------------------------------------------

def _parse_authors_year_source(text: str) -> tuple[str, str, str]:
    """Split a Scholar 'authors - journal, year' string into parts."""
    authors = year = journal = ""
    # Typical format: "A Smith, B Jones - Journal of X, 2021 - publisher"
    parts = text.split(" - ", maxsplit=2)
    if parts:
        authors = parts[0].strip()
    if len(parts) >= 2:
        journal_year = parts[1]
        year_match = re.search(r"\b((?:19|20)\d{2})\b", journal_year)
        if year_match:
            year = year_match.group(1)
            journal = journal_year[:year_match.start()].rstrip(", ")
        else:
            journal = journal_year.strip()
    return authors, year, journal


def build_study_records(raw_results: list[dict],
                        conditions: list[str]) -> list[StudyRecord]:
    """Convert raw scraped results into structured StudyRecord objects."""
    records: list[StudyRecord] = []

    for item in raw_results:
        authors, year, journal = _parse_authors_year_source(
            item.get("authors_year_source", ""))

        snippet = item.get("snippet", "")
        combined_text = f"{item.get('title', '')} {snippet}"
        meta = _parse_snippet_for_metadata(combined_text)

        condition = _detect_condition(combined_text, conditions)

        record = StudyRecord(
            study_title=item.get("title", ""),
            authors=authors,
            year=year,
            journal=journal,
            condition=condition,
            sample_size=meta.get("sample_size", ""),
            success_rate_or_effect_size=meta.get("effect_size", ""),
            methodology=meta.get("methodology", "meta-analysis"),
            notes=snippet[:300] if snippet else "",
        )
        records.append(record)

    return records


def fetch_study_details(records: list[StudyRecord],
                        raw_results: list[dict]) -> list[StudyRecord]:
    """Attempt to fetch full-text pages to enrich metadata.

    Visits the link for each result and tries to extract additional
    effect sizes, sample sizes, and methodology information from the
    abstract or landing page.
    """
    for record, raw in zip(records, raw_results):
        link = raw.get("link", "")
        if not link:
            continue

        logger.info("Fetching study page: %s", link[:80])
        try:
            resp = _request_with_retry(link)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Look for abstract text
            abstract = ""
            for selector in ["div.abstract", "section#abstract",
                             "div[class*='abstract']", "p[class*='abstract']"]:
                el = soup.select_one(selector)
                if el:
                    abstract = el.get_text(" ", strip=True)
                    break
            if not abstract:
                # Fallback: grab first large paragraph
                for p in soup.find_all("p"):
                    text = p.get_text(strip=True)
                    if len(text) > 200:
                        abstract = text
                        break

            if abstract:
                meta = _parse_snippet_for_metadata(abstract)
                if meta.get("effect_size") and not record.success_rate_or_effect_size:
                    record.success_rate_or_effect_size = meta["effect_size"]
                if meta.get("sample_size") and not record.sample_size:
                    record.sample_size = meta["sample_size"]
                if meta.get("methodology") and record.methodology == "meta-analysis":
                    record.methodology = meta["methodology"]
                # Append abstract excerpt to notes if short
                if len(record.notes) < 100:
                    record.notes = abstract[:300]

        except requests.RequestException as exc:
            logger.debug("Could not fetch %s: %s", link[:60], exc)

        # Be polite
        time.sleep(1.5)

    return records


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def write_csv(records: list[StudyRecord], output_path: str) -> None:
    """Write study records to CSV sorted by condition then effect size (desc)."""
    sorted_records = sorted(
        records,
        key=lambda r: (r.condition.lower(), -r.effect_size_sort_key),
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for rec in sorted_records:
            writer.writerow({f.name: getattr(rec, f.name) for f in fields(rec)})

    logger.info("Wrote %d records to %s", len(sorted_records), output_path)


# ---------------------------------------------------------------------------
# Condition-specific queries
# ---------------------------------------------------------------------------

def build_queries(base_terms: str, conditions: list[str]) -> list[tuple[str, str]]:
    """Build per-condition search queries.

    Returns list of (query_string, condition_label) tuples.
    If no conditions are provided, returns a single generic query.
    """
    if not conditions or conditions == [""]:
        return [(base_terms, "general")]
    return [(f"{base_terms} {cond}", cond) for cond in conditions]


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(search_terms: str, conditions: list[str],
                 output_csv: str, limit: int, fetch_details: bool = True) -> None:
    """Execute the full pipeline: search -> extract -> enrich -> CSV."""
    api_key = os.environ.get("SERPAPI_KEY", "")
    use_serpapi = bool(api_key)

    if use_serpapi:
        logger.info("Using SerpAPI (SERPAPI_KEY detected).")
    else:
        logger.info("Using direct Scholar scraping (set SERPAPI_KEY for SerpAPI mode).")

    queries = build_queries(search_terms, conditions)
    per_query_limit = max(1, limit // len(queries))

    all_raw: list[dict] = []
    all_records: list[StudyRecord] = []

    for query_str, cond_label in queries:
        logger.info("--- Searching: %s ---", query_str)

        if use_serpapi:
            raw = scrape_scholar_serpapi(query_str, per_query_limit, api_key)
        else:
            raw = scrape_scholar_direct(query_str, per_query_limit)

        records = build_study_records(raw, conditions)

        # Override condition for records that didn't match any keyword
        for rec in records:
            if rec.condition == "general" and cond_label != "general":
                rec.condition = cond_label

        if fetch_details and raw:
            records = fetch_study_details(records, raw)

        all_raw.extend(raw)
        all_records.extend(records)

    if not all_records:
        logger.warning("No results found. Try broader search terms or check connectivity.")
        return

    # Deduplicate by title
    seen: set[str] = set()
    unique: list[StudyRecord] = []
    for rec in all_records:
        key = rec.study_title.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(rec)
    logger.info("Deduplicated: %d -> %d unique records.", len(all_records), len(unique))

    write_csv(unique, output_csv)
    print(f"\nPipeline complete. {len(unique)} studies written to {output_csv}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Query Google Scholar for hypnotherapy efficacy meta-analyses "
                    "and generate a comparative CSV report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--search-terms",
        default="hypnotherapy efficacy meta-analysis",
        help="Base search query (default: 'hypnotherapy efficacy meta-analysis')",
    )
    parser.add_argument(
        "--conditions",
        default="",
        help="Comma-separated conditions to query, e.g. anxiety,pain,smoking",
    )
    parser.add_argument(
        "--output-csv",
        default="hypnotherapy_efficacy_report.csv",
        help="Output CSV file path (default: hypnotherapy_efficacy_report.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum total results to fetch (default: 20)",
    )
    parser.add_argument(
        "--no-fetch-details",
        action="store_true",
        help="Skip fetching individual study pages for enrichment (faster)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    args = parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    logger.info("Search terms : %s", args.search_terms)
    logger.info("Conditions   : %s", conditions or ["(all)"])
    logger.info("Result limit : %d", args.limit)
    logger.info("Output CSV   : %s", args.output_csv)

    run_pipeline(
        search_terms=args.search_terms,
        conditions=conditions,
        output_csv=args.output_csv,
        limit=args.limit,
        fetch_details=not args.no_fetch_details,
    )


if __name__ == "__main__":
    main()
