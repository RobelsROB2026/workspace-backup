#!/usr/bin/env python3
"""
Search arXiv and PubMed for peer-reviewed papers on Neuro-Linguistic Programming
and Ericksonian Hypnosis, then save results as a markdown report with abstracts
and citation information.
"""

import argparse
import logging
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

ARXIV_API = "https://export.arxiv.org/api/query"
PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Search arXiv and PubMed for NLP / Ericksonian Hypnosis papers."
    )
    parser.add_argument(
        "--search-terms",
        nargs="+",
        default=["Neuro-Linguistic Programming", "Ericksonian Hypnosis"],
        help="Search terms (default: 'Neuro-Linguistic Programming' 'Ericksonian Hypnosis')",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="nlp_hypnosis_papers.md",
        help="Path for the markdown output file",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="Maximum results per source (default: 20)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------

def build_arxiv_query(terms: list[str], years: int = 5) -> str:
    """Build an arXiv search query string combining terms with OR."""
    parts = [f'ti:"{t}" OR abs:"{t}"' for t in terms]
    return " OR ".join(parts)


def search_arxiv(terms: list[str], max_results: int = 20) -> list[dict]:
    """Query the arXiv API and return parsed paper metadata.

    Args:
        terms: Search terms to query in title/abstract.
        max_results: Cap on number of results returned.

    Returns:
        List of dicts with keys: title, authors, published, abstract,
        link, source.
    """
    query = build_arxiv_query(terms)
    cutoff = datetime.now() - timedelta(days=5 * 365)

    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    log.info("Querying arXiv: %s", query)
    try:
        resp = requests.get(ARXIV_API, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.error("arXiv request failed: %s", exc)
        return []

    root = ET.fromstring(resp.text)
    papers = []
    for entry in root.findall("atom:entry", ARXIV_NS):
        published_str = entry.findtext("atom:published", default="", namespaces=ARXIV_NS)
        try:
            pub_date = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        except ValueError:
            continue

        if pub_date.replace(tzinfo=None) < cutoff:
            continue

        authors = [
            a.findtext("atom:name", default="", namespaces=ARXIV_NS)
            for a in entry.findall("atom:author", ARXIV_NS)
        ]
        title = entry.findtext("atom:title", default="", namespaces=ARXIV_NS).strip().replace("\n", " ")
        abstract = entry.findtext("atom:summary", default="", namespaces=ARXIV_NS).strip().replace("\n", " ")
        link = entry.findtext("atom:id", default="", namespaces=ARXIV_NS).strip()

        papers.append({
            "title": title,
            "authors": authors,
            "published": pub_date.strftime("%Y-%m-%d"),
            "abstract": abstract,
            "link": link,
            "source": "arXiv",
        })

    log.info("arXiv returned %d papers (after date filter).", len(papers))
    return papers


# ---------------------------------------------------------------------------
# PubMed
# ---------------------------------------------------------------------------

def search_pubmed(terms: list[str], max_results: int = 20) -> list[dict]:
    """Query PubMed EUtils for papers matching the search terms.

    Args:
        terms: Search terms combined with OR.
        max_results: Cap on number of results returned.

    Returns:
        List of dicts with keys: title, authors, published, abstract,
        link, source.
    """
    cutoff = datetime.now() - timedelta(days=5 * 365)
    mindate = cutoff.strftime("%Y/%m/%d")
    maxdate = datetime.now().strftime("%Y/%m/%d")

    query = " OR ".join(f'"{t}"' for t in terms)
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "date",
        "mindate": mindate,
        "maxdate": maxdate,
        "datetype": "pdat",
        "retmode": "json",
    }

    log.info("Querying PubMed: %s", query)
    try:
        resp = requests.get(PUBMED_SEARCH, params=search_params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        log.error("PubMed search failed: %s", exc)
        return []

    id_list = data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        log.info("PubMed returned 0 IDs.")
        return []

    log.info("PubMed returned %d IDs; fetching details...", len(id_list))

    fetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "xml",
        "rettype": "abstract",
    }
    try:
        resp = requests.get(PUBMED_FETCH, params=fetch_params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.error("PubMed fetch failed: %s", exc)
        return []

    root = ET.fromstring(resp.text)
    papers = []
    for article in root.findall(".//PubmedArticle"):
        medline = article.find("MedlineCitation")
        if medline is None:
            continue
        art = medline.find("Article")
        if art is None:
            continue

        title = art.findtext("ArticleTitle", default="").strip()

        # Authors
        author_list = art.find("AuthorList")
        authors = []
        if author_list is not None:
            for au in author_list.findall("Author"):
                last = au.findtext("LastName", default="")
                first = au.findtext("ForeName", default="")
                if last:
                    authors.append(f"{last}, {first}".strip(", "))

        # Abstract
        abs_el = art.find("Abstract")
        abstract = ""
        if abs_el is not None:
            parts = [t.text or "" for t in abs_el.findall("AbstractText")]
            abstract = " ".join(parts).strip()

        # Date
        pub_date_el = art.find(".//PubDate")
        year = pub_date_el.findtext("Year", default="") if pub_date_el is not None else ""
        month = pub_date_el.findtext("Month", default="01") if pub_date_el is not None else "01"
        day = pub_date_el.findtext("Day", default="01") if pub_date_el is not None else "01"
        try:
            pub_date = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            # Month may be abbreviated name like "Jan"
            try:
                pub_date = datetime.strptime(f"{year}-{month}-{day}", "%Y-%b-%d").strftime("%Y-%m-%d")
            except ValueError:
                pub_date = year or "Unknown"

        pmid = medline.findtext("PMID", default="")
        link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

        papers.append({
            "title": title,
            "authors": authors,
            "published": pub_date,
            "abstract": abstract,
            "link": link,
            "source": "PubMed",
        })

    log.info("PubMed returned %d papers.", len(papers))
    return papers


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_markdown(papers: list[dict], output_path: str, terms: list[str]) -> None:
    """Write papers to a markdown file with citation info and abstracts.

    Args:
        papers: Combined list of paper dicts from all sources.
        output_path: File path for the markdown output.
        terms: The search terms used (for the report header).
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Research Papers: {' | '.join(terms)}\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} — "
                f"{len(papers)} papers found*\n\n")
        f.write("---\n\n")

        for i, p in enumerate(papers, 1):
            authors_str = "; ".join(p["authors"][:5])
            if len(p["authors"]) > 5:
                authors_str += " et al."

            f.write(f"## {i}. {p['title']}\n\n")
            f.write(f"- **Source:** {p['source']}\n")
            f.write(f"- **Authors:** {authors_str}\n")
            f.write(f"- **Published:** {p['published']}\n")
            f.write(f"- **Link:** {p['link']}\n\n")

            if p["abstract"]:
                f.write(f"### Abstract\n\n{p['abstract']}\n\n")
            else:
                f.write("*No abstract available.*\n\n")

            f.write("---\n\n")

    log.info("Wrote %d papers to %s", len(papers), path)


def main():
    """Entry point: parse args, query both APIs, write markdown report."""
    args = parse_args()

    arxiv_papers = search_arxiv(args.search_terms, max_results=args.max_results)
    pubmed_papers = search_pubmed(args.search_terms, max_results=args.max_results)

    all_papers = arxiv_papers + pubmed_papers

    # Deduplicate by normalized title
    seen = set()
    unique = []
    for p in all_papers:
        key = p["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(p)

    # Sort newest first
    unique.sort(key=lambda p: p["published"], reverse=True)

    if not unique:
        log.warning("No papers found for terms: %s", args.search_terms)

    write_markdown(unique, args.output_file, args.search_terms)
    print(f"Done — {len(unique)} papers saved to {args.output_file}")


if __name__ == "__main__":
    main()
