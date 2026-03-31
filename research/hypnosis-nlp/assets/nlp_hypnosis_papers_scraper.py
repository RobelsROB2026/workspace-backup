#!/usr/bin/env python3
"""
NLP & Ericksonian Hypnosis Academic Paper Scraper

Searches arXiv and PubMed APIs for peer-reviewed papers on
Neuro-Linguistic Programming and/or Ericksonian Hypnosis within
a specified date range. Outputs results in Markdown or CSV format.
"""

import argparse
import csv
import io
import logging
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

ARXIV_API = "https://export.arxiv.org/api/query"
PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBMED_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

DEFAULT_TERMS = ["Neuro-Linguistic Programming", "Ericksonian Hypnosis"]


@dataclass
class Paper:
    """Represents a single academic paper."""

    title: str
    authors: str
    published: str
    source: str
    abstract: str
    url: str
    journal: str = ""


def build_arxiv_query(terms: list[str], start_year: int, end_year: int) -> str:
    """Build an arXiv API search query string for the given terms and date range.

    Args:
        terms: Search terms to match in title or abstract.
        start_year: Earliest publication year (inclusive).
        end_year: Latest publication year (inclusive).

    Returns:
        URL-encoded query string for arXiv API.
    """
    term_parts = [f'ti:"{t}" OR abs:"{t}"' for t in terms]
    query = " OR ".join(term_parts)
    # arXiv submittedDate filter uses YYYYMMDDHHMMSS format
    date_filter = f"submittedDate:[{start_year}01010000 TO {end_year}12312359]"
    return f"({query}) AND {date_filter}"


def search_arxiv(
    terms: list[str], start_year: int, end_year: int, max_results: int
) -> list[Paper]:
    """Search arXiv for papers matching the given terms and date range.

    Args:
        terms: Search terms to query.
        start_year: Start of date range.
        end_year: End of date range.
        max_results: Maximum number of results to return.

    Returns:
        List of Paper objects from arXiv.
    """
    query = build_arxiv_query(terms, start_year, end_year)
    params = urllib.parse.urlencode({
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API}?{params}"
    logger.info("Querying arXiv: %s", url)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NLPHypnosisScraper/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except urllib.error.URLError as e:
        logger.error("arXiv request failed: %s", e)
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        logger.error("Failed to parse arXiv XML: %s", e)
        return []

    papers = []
    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        summary_el = entry.find("atom:summary", ns)
        published_el = entry.find("atom:published", ns)
        link_el = entry.find('atom:link[@rel="alternate"]', ns)

        title = " ".join((title_el.text or "").split()) if title_el is not None else ""
        abstract = " ".join((summary_el.text or "").split()) if summary_el is not None else ""
        published = (published_el.text or "")[:10] if published_el is not None else ""
        paper_url = (link_el.attrib.get("href", "") if link_el is not None else "")

        authors = []
        for author_el in entry.findall("atom:author", ns):
            name_el = author_el.find("atom:name", ns)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        if title:
            papers.append(Paper(
                title=title,
                authors="; ".join(authors),
                published=published,
                source="arXiv",
                abstract=abstract,
                url=paper_url,
            ))

    logger.info("arXiv returned %d papers", len(papers))
    return papers


def search_pubmed(
    terms: list[str], start_year: int, end_year: int, max_results: int
) -> list[Paper]:
    """Search PubMed for papers matching the given terms and date range.

    Args:
        terms: Search terms to query.
        start_year: Start of date range.
        end_year: End of date range.
        max_results: Maximum number of results to return.

    Returns:
        List of Paper objects from PubMed.
    """
    term_query = " OR ".join(f'"{t}"' for t in terms)
    full_query = f"({term_query}) AND {start_year}:{end_year}[dp]"

    params = urllib.parse.urlencode({
        "db": "pubmed",
        "term": full_query,
        "retmax": max_results,
        "sort": "relevance",
        "retmode": "xml",
    })
    search_url = f"{PUBMED_ESEARCH}?{params}"
    logger.info("Querying PubMed esearch: %s", search_url)

    try:
        req = urllib.request.Request(search_url, headers={"User-Agent": "NLPHypnosisScraper/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except urllib.error.URLError as e:
        logger.error("PubMed esearch failed: %s", e)
        return []

    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        logger.error("Failed to parse PubMed esearch XML: %s", e)
        return []

    id_list = root.find("IdList")
    if id_list is None:
        logger.warning("No IdList in PubMed response")
        return []

    pmids = [id_el.text for id_el in id_list.findall("Id") if id_el.text]
    if not pmids:
        logger.info("PubMed returned 0 results")
        return []

    logger.info("PubMed found %d IDs, fetching details...", len(pmids))
    return _fetch_pubmed_details(pmids)


def _fetch_pubmed_details(pmids: list[str]) -> list[Paper]:
    """Fetch paper details from PubMed using efetch for abstracts.

    Args:
        pmids: List of PubMed IDs.

    Returns:
        List of Paper objects with full metadata.
    """
    # Use efetch to get full records including abstracts
    batch_size = 200
    papers = []

    for i in range(0, len(pmids), batch_size):
        batch = pmids[i : i + batch_size]
        params = urllib.parse.urlencode({
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
            "rettype": "abstract",
        })
        url = f"{PUBMED_EFETCH}?{params}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NLPHypnosisScraper/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
        except urllib.error.URLError as e:
            logger.error("PubMed efetch failed for batch %d: %s", i, e)
            continue

        try:
            root = ET.fromstring(data)
        except ET.ParseError as e:
            logger.error("Failed to parse PubMed efetch XML: %s", e)
            continue

        for article in root.findall(".//PubmedArticle"):
            paper = _parse_pubmed_article(article)
            if paper:
                papers.append(paper)

        if i + batch_size < len(pmids):
            time.sleep(0.4)  # respect NCBI rate limits

    return papers


def _parse_pubmed_article(article: ET.Element) -> Optional[Paper]:
    """Parse a single PubmedArticle XML element into a Paper.

    Args:
        article: XML element for one PubMed article.

    Returns:
        Paper object, or None if essential fields are missing.
    """
    medline = article.find("MedlineCitation")
    if medline is None:
        return None

    pmid_el = medline.find("PMID")
    pmid = pmid_el.text if pmid_el is not None else ""

    art = medline.find("Article")
    if art is None:
        return None

    title_el = art.find("ArticleTitle")
    title = (title_el.text or "").strip() if title_el is not None else ""
    if not title:
        return None

    # Abstract
    abstract_parts = []
    abstract_el = art.find("Abstract")
    if abstract_el is not None:
        for text_el in abstract_el.findall("AbstractText"):
            label = text_el.attrib.get("Label", "")
            text = "".join(text_el.itertext()).strip()
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
    abstract = " ".join(abstract_parts)

    # Authors
    authors = []
    author_list = art.find("AuthorList")
    if author_list is not None:
        for author_el in author_list.findall("Author"):
            last = author_el.find("LastName")
            first = author_el.find("ForeName")
            if last is not None and last.text:
                name = last.text
                if first is not None and first.text:
                    name += f" {first.text}"
                authors.append(name)

    # Journal
    journal_el = art.find("Journal/Title")
    journal = (journal_el.text or "") if journal_el is not None else ""

    # Date
    pub_date = ""
    date_el = art.find("Journal/JournalIssue/PubDate")
    if date_el is not None:
        year = date_el.find("Year")
        month = date_el.find("Month")
        if year is not None and year.text:
            pub_date = year.text
            if month is not None and month.text:
                pub_date += f"-{month.text}"

    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

    return Paper(
        title=title,
        authors="; ".join(authors),
        published=pub_date,
        source="PubMed",
        abstract=abstract,
        url=url,
        journal=journal,
    )


def format_markdown(papers: list[Paper]) -> str:
    """Format papers as a Markdown document.

    Args:
        papers: List of Paper objects.

    Returns:
        Markdown-formatted string.
    """
    lines = [
        "# Academic Paper Search Results",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total papers found: {len(papers)}\n",
    ]

    for i, p in enumerate(papers, 1):
        lines.append(f"## {i}. {p.title}\n")
        lines.append(f"- **Authors:** {p.authors}")
        lines.append(f"- **Published:** {p.published}")
        lines.append(f"- **Source:** {p.source}")
        if p.journal:
            lines.append(f"- **Journal:** {p.journal}")
        lines.append(f"- **URL:** {p.url}")
        lines.append(f"\n**Abstract:** {p.abstract}\n")
        lines.append("---\n")

    return "\n".join(lines)


def format_csv(papers: list[Paper]) -> str:
    """Format papers as CSV.

    Args:
        papers: List of Paper objects.

    Returns:
        CSV-formatted string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    header = [f.name for f in fields(Paper)]
    writer.writerow(header)
    for p in papers:
        writer.writerow([getattr(p, f.name) for f in fields(Paper)])
    return output.getvalue()


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Search arXiv/PubMed for NLP & Ericksonian Hypnosis papers."
    )
    parser.add_argument(
        "--search-term",
        nargs="+",
        default=DEFAULT_TERMS,
        help='Search terms (default: "Neuro-Linguistic Programming" "Ericksonian Hypnosis")',
    )
    parser.add_argument(
        "--source",
        choices=["arxiv", "pubmed"],
        default="pubmed",
        help="API source (default: pubmed)",
    )
    parser.add_argument(
        "--start-year", type=int, default=2019, help="Start year (default: 2019)"
    )
    parser.add_argument(
        "--end-year", type=int, default=2024, help="End year (default: 2024)"
    )
    parser.add_argument(
        "--max-results", type=int, default=50, help="Max results (default: 50)"
    )
    parser.add_argument(
        "--output-format",
        choices=["markdown", "csv"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Output file path (default: print to stdout)",
    )
    return parser.parse_args(argv)


def main() -> None:
    """Main entry point for the paper scraper."""
    args = parse_args()

    logger.info(
        "Searching %s for %s (%d-%d), max %d results",
        args.source,
        args.search_term,
        args.start_year,
        args.end_year,
        args.max_results,
    )

    if args.source == "arxiv":
        papers = search_arxiv(
            args.search_term, args.start_year, args.end_year, args.max_results
        )
    else:
        papers = search_pubmed(
            args.search_term, args.start_year, args.end_year, args.max_results
        )

    if not papers:
        logger.warning("No papers found.")
        return

    if args.output_format == "markdown":
        output = format_markdown(papers)
    else:
        output = format_csv(papers)

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(output)
        logger.info("Results written to %s", args.output_file)
    else:
        print(output)

    logger.info("Done. %d papers returned.", len(papers))


if __name__ == "__main__":
    main()
