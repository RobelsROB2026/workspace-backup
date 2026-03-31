#!/usr/bin/env python3
"""
Mass scraper for free hypnosis/hypnotherapy scripts.
Targets multiple public sources to build a 100+ script corpus.
"""

import os
import re
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
MIN_SCRIPT_LENGTH = 300  # chars — skip very short pages
SEEN_HASHES = set()
TOTAL_SAVED = 0

# Load hashes of existing scripts to avoid duplicates
for f in os.listdir(SCRIPTS_DIR):
    if f.endswith('.txt'):
        path = os.path.join(SCRIPTS_DIR, f)
        with open(path, 'r', errors='ignore') as fh:
            SEEN_HASHES.add(hashlib.md5(fh.read().strip().encode()).hexdigest())


def slugify(text, max_len=60):
    text = re.sub(r'[^\w\s-]', '', text.lower().strip())
    text = re.sub(r'[\s_]+', '_', text)
    return text[:max_len]


def save_script(title, text, category="uncategorized"):
    global TOTAL_SAVED
    text = text.strip()
    if len(text) < MIN_SCRIPT_LENGTH:
        return False
    h = hashlib.md5(text.encode()).hexdigest()
    if h in SEEN_HASHES:
        return False
    SEEN_HASHES.add(h)

    slug = slugify(title) if title else f"script_{h[:8]}"
    fname = f"{slug}.txt"
    fpath = os.path.join(SCRIPTS_DIR, fname)

    # Avoid overwriting
    if os.path.exists(fpath):
        fname = f"{slug}_{h[:6]}.txt"
        fpath = os.path.join(SCRIPTS_DIR, fname)

    with open(fpath, 'w') as f:
        f.write(text)

    TOTAL_SAVED += 1
    print(f"  [{TOTAL_SAVED}] Saved: {fname} ({len(text)} chars) [{category}]")
    return True


def fetch(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  WARN: Failed {url}: {e}")
        return None


# ─────────────────────────────────────────────
# Source 1: hypnoscripts.com
# ─────────────────────────────────────────────
def scrape_hypnoscripts():
    print("\n=== Source: hypnoscripts.com ===")
    base = "https://hypnoscripts.com"
    html = fetch(base)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')
    # Find category/script links
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/script/' in href or '/scripts/' in href:
            links.add(urljoin(base, href))

    for link in list(links)[:80]:
        time.sleep(0.5)
        page = fetch(link)
        if not page:
            continue
        psoup = BeautifulSoup(page, 'html.parser')
        title_el = psoup.find('h1') or psoup.find('title')
        title = title_el.get_text(strip=True) if title_el else urlparse(link).path.split('/')[-1]
        # Try to find the main content
        content_el = psoup.find('article') or psoup.find('div', class_=re.compile(r'content|entry|post|script'))
        if content_el:
            text = content_el.get_text('\n', strip=True)
        else:
            text = psoup.get_text('\n', strip=True)
        save_script(title, text, "hypnoscripts.com")


# ─────────────────────────────────────────────
# Source 2: freehypnosisscripts.info (Wayback)
# ─────────────────────────────────────────────
def scrape_freehypnosisscripts():
    print("\n=== Source: freehypnosisscripts.info (via Wayback) ===")
    # Try Wayback Machine CDX API for archived pages
    cdx_url = "http://web.archive.org/cdx/search/cdx"
    params = {
        "url": "freehypnosisscripts.info/*",
        "output": "json",
        "fl": "timestamp,original",
        "filter": "statuscode:200",
        "collapse": "urlkey",
        "limit": "200"
    }
    try:
        r = requests.get(cdx_url, params=params, headers=HEADERS, timeout=20)
        rows = r.json()
    except Exception as e:
        print(f"  Wayback CDX failed: {e}")
        return

    if len(rows) < 2:
        print("  No archived pages found.")
        return

    count = 0
    for row in rows[1:]:  # skip header
        if count >= 60:
            break
        ts, orig = row[0], row[1]
        # Skip non-script pages
        if any(x in orig.lower() for x in ['wp-content', '.css', '.js', '.jpg', '.png', '.gif', 'wp-login', 'feed', 'xmlrpc']):
            continue
        wb_url = f"https://web.archive.org/web/{ts}/{orig}"
        time.sleep(0.5)
        page = fetch(wb_url)
        if not page:
            continue
        soup = BeautifulSoup(page, 'html.parser')
        title_el = soup.find('h1', class_=re.compile(r'entry-title|post-title')) or soup.find('h1') or soup.find('title')
        title = title_el.get_text(strip=True) if title_el else orig.split('/')[-1]
        content_el = soup.find('div', class_=re.compile(r'entry-content|post-content'))
        if not content_el:
            content_el = soup.find('article')
        if content_el:
            text = content_el.get_text('\n', strip=True)
        else:
            continue
        if save_script(title, text, "freehypnosisscripts.info"):
            count += 1


# ─────────────────────────────────────────────
# Source 3: GitHub — search for hypnosis script repos
# ─────────────────────────────────────────────
def scrape_github():
    print("\n=== Source: GitHub code search ===")
    # Search for repos with hypnosis scripts
    queries = [
        "hypnosis+scripts+induction",
        "hypnotherapy+script",
        "ericksonian+hypnosis+script",
        "self+hypnosis+relaxation+script",
    ]
    api_base = "https://api.github.com"
    seen_repos = set()

    for q in queries:
        url = f"{api_base}/search/repositories?q={q}&per_page=10"
        time.sleep(1)
        try:
            r = requests.get(url, headers={**HEADERS, "Accept": "application/vnd.github.v3+json"}, timeout=15)
            data = r.json()
        except Exception as e:
            print(f"  GitHub search failed: {e}")
            continue

        for item in data.get("items", []):
            repo = item["full_name"]
            if repo in seen_repos:
                continue
            seen_repos.add(repo)
            # Get repo contents (look for .txt or .md files)
            tree_url = f"{api_base}/repos/{repo}/git/trees/{item.get('default_branch', 'main')}?recursive=1"
            time.sleep(0.5)
            try:
                tr = requests.get(tree_url, headers={**HEADERS, "Accept": "application/vnd.github.v3+json"}, timeout=15)
                tree = tr.json()
            except:
                continue

            for node in tree.get("tree", []):
                if node["type"] != "blob":
                    continue
                path = node["path"].lower()
                if not (path.endswith('.txt') or path.endswith('.md')):
                    continue
                if any(kw in path for kw in ['script', 'induction', 'hypno', 'trance', 'relax']):
                    raw_url = f"https://raw.githubusercontent.com/{repo}/{item.get('default_branch', 'main')}/{node['path']}"
                    time.sleep(0.3)
                    content = fetch(raw_url)
                    if content:
                        title = os.path.splitext(os.path.basename(node['path']))[0]
                        save_script(title, content, f"github:{repo}")


# ─────────────────────────────────────────────
# Source 4: hypnotherapyscripts.co.uk (free section)
# ─────────────────────────────────────────────
def scrape_hypnotherapy_scripts_uk():
    print("\n=== Source: hypnotherapyscripts.co.uk ===")
    base = "https://www.hypnotherapyscripts.co.uk"
    html = fetch(f"{base}/free-hypnotherapy-scripts/")
    if not html:
        html = fetch(base)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        full = urljoin(base, href)
        if base in full and full != base and 'free' in full.lower():
            links.add(full)
    for link in list(links)[:40]:
        time.sleep(0.5)
        page = fetch(link)
        if not page:
            continue
        psoup = BeautifulSoup(page, 'html.parser')
        title_el = psoup.find('h1') or psoup.find('title')
        title = title_el.get_text(strip=True) if title_el else "unknown"
        content_el = psoup.find('article') or psoup.find('div', class_=re.compile(r'content|entry|post|script'))
        if content_el:
            text = content_el.get_text('\n', strip=True)
            save_script(title, text, "hypnotherapyscripts.co.uk")


# ─────────────────────────────────────────────
# Source 5: Wikimedia / Wikibooks — Hypnosis
# ─────────────────────────────────────────────
def scrape_wikibooks():
    print("\n=== Source: Wikibooks Hypnosis ===")
    url = "https://en.wikibooks.org/wiki/Hypnosis"
    html = fetch(url)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')
    base = "https://en.wikibooks.org"
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/wiki/Hypnosis/' in href:
            links.add(urljoin(base, href))
    for link in list(links)[:30]:
        time.sleep(0.5)
        page = fetch(link)
        if not page:
            continue
        psoup = BeautifulSoup(page, 'html.parser')
        title_el = psoup.find('h1')
        title = title_el.get_text(strip=True) if title_el else "wikibooks_hypnosis"
        content_el = psoup.find('div', class_='mw-parser-output')
        if content_el:
            text = content_el.get_text('\n', strip=True)
            save_script(title, text, "wikibooks")


# ─────────────────────────────────────────────
# Source 6: Archive.org text search
# ─────────────────────────────────────────────
def scrape_archive_org():
    print("\n=== Source: archive.org texts ===")
    search_url = "https://archive.org/advancedsearch.php"
    params = {
        "q": "subject:hypnosis AND mediatype:texts",
        "fl[]": "identifier,title",
        "rows": "50",
        "output": "json",
        "page": "1"
    }
    try:
        r = requests.get(search_url, params=params, headers=HEADERS, timeout=20)
        data = r.json()
    except Exception as e:
        print(f"  Archive.org search failed: {e}")
        return

    docs = data.get("response", {}).get("docs", [])
    for doc in docs[:30]:
        ident = doc.get("identifier", "")
        title = doc.get("title", ident)
        # Try to get the text file
        meta_url = f"https://archive.org/metadata/{ident}/files"
        time.sleep(0.5)
        try:
            mr = requests.get(meta_url, headers=HEADERS, timeout=15)
            files = mr.json().get("result", [])
        except:
            continue

        for finfo in files:
            fname = finfo.get("name", "")
            if fname.endswith('.txt') and finfo.get("size", "0") != "0":
                size = int(finfo.get("size", "0"))
                if size > 500000:  # skip huge files
                    continue
                dl_url = f"https://archive.org/download/{ident}/{fname}"
                time.sleep(0.5)
                content = fetch(dl_url)
                if content:
                    save_script(f"{title}_{fname}", content, "archive.org")
                break  # one file per item


# ─────────────────────────────────────────────
# Source 7: Scraped collections from known free sites
# ─────────────────────────────────────────────
def scrape_misc_free_sites():
    print("\n=== Source: misc free hypnosis sites ===")
    sites = [
        {
            "name": "hypnoticworld.com",
            "index": "https://www.hypnoticworld.com/hypnosis-scripts/",
            "link_pattern": r'/hypnosis-scripts/',
            "content_selector": "article",
        },
        {
            "name": "uncommon-knowledge.co.uk",
            "index": "https://www.uncommon-knowledge.co.uk/hypnosis-scripts/",
            "link_pattern": r'/hypnosis-scripts/',
            "content_selector": "article",
        },
    ]

    for site in sites:
        print(f"\n  Trying {site['name']}...")
        html = fetch(site["index"])
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')
        base = site["index"]
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            full = urljoin(base, href)
            if re.search(site["link_pattern"], full) and full != base:
                links.add(full)

        for link in list(links)[:40]:
            time.sleep(0.7)
            page = fetch(link)
            if not page:
                continue
            psoup = BeautifulSoup(page, 'html.parser')
            title_el = psoup.find('h1') or psoup.find('title')
            title = title_el.get_text(strip=True) if title_el else urlparse(link).path.split('/')[-1]
            sel = site["content_selector"]
            content_el = psoup.find(sel) or psoup.find('div', class_=re.compile(r'content|entry|post'))
            if content_el:
                text = content_el.get_text('\n', strip=True)
                save_script(title, text, site["name"])


# ─────────────────────────────────────────────
# Source 8: Google Custom Search via scraping approach
# Try well-known script listing pages directly
# ─────────────────────────────────────────────
def scrape_direct_script_pages():
    print("\n=== Source: direct script page URLs ===")
    # Known URLs that host free hypnosis scripts
    urls = [
        "https://www.interhypnosis.com/free-hypnosis-scripts/",
        "https://www.interhypnosis.com/hypnosis-scripts/",
        "https://mindmotivations.com/free-hypnosis-scripts/",
        "https://www.yourmentalwealthadvisors.com/hypnosis-scripts/",
        "https://www.yourhypnosisscripts.com/free-hypnosis-scripts",
    ]
    for url in urls:
        time.sleep(0.5)
        html = fetch(url)
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')
        base = url
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            full = urljoin(base, href)
            parsed = urlparse(full)
            if parsed.netloc == urlparse(base).netloc and full != base:
                if any(kw in full.lower() for kw in ['script', 'hypno', 'induction', 'relax', 'confiden', 'anxiety', 'sleep', 'weight', 'smok', 'pain', 'stress', 'phob', 'fear']):
                    links.add(full)

        print(f"  Found {len(links)} links on {urlparse(url).netloc}")
        for link in list(links)[:30]:
            time.sleep(0.7)
            page = fetch(link)
            if not page:
                continue
            psoup = BeautifulSoup(page, 'html.parser')
            title_el = psoup.find('h1') or psoup.find('title')
            title = title_el.get_text(strip=True) if title_el else "unknown"
            content_el = (
                psoup.find('article') or
                psoup.find('div', class_=re.compile(r'entry-content|post-content|script-content|content')) or
                psoup.find('div', id=re.compile(r'content|main'))
            )
            if content_el:
                text = content_el.get_text('\n', strip=True)
                save_script(title, text, urlparse(url).netloc)


# ─────────────────────────────────────────────
# Source 9: Project Gutenberg — hypnosis texts
# ─────────────────────────────────────────────
def scrape_gutenberg():
    print("\n=== Source: Project Gutenberg ===")
    search_url = "https://www.gutenberg.org/ebooks/search/?query=hypnosis+hypnotism&submit_search=Go%21"
    html = fetch(search_url)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/ebooks/' in href and href.split('/')[-1].isdigit():
            links.add(urljoin("https://www.gutenberg.org", href))

    for link in list(links)[:15]:
        book_id = link.rstrip('/').split('/')[-1]
        txt_url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
        time.sleep(0.5)
        content = fetch(txt_url)
        if not content:
            # Try alternate URL
            txt_url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
            content = fetch(txt_url)
        if content:
            # Extract title from first few lines
            lines = content.split('\n')[:50]
            title = "gutenberg_" + book_id
            for line in lines:
                if line.strip().startswith("Title:"):
                    title = line.strip().replace("Title:", "").strip()
                    break
            # For Gutenberg, split long texts into chapter-sized chunks
            # to get more individual "scripts"
            if len(content) > 5000:
                chapters = re.split(r'\n(?:CHAPTER|Chapter|PART|Part|SECTION|Section)\s+[IVXLCDM\d]+', content)
                if len(chapters) > 3:
                    for i, ch in enumerate(chapters[1:], 1):
                        ch_title = f"{title}_ch{i}"
                        save_script(ch_title, ch.strip(), "gutenberg")
                else:
                    save_script(title, content, "gutenberg")
            else:
                save_script(title, content, "gutenberg")


# ─────────────────────────────────────────────
# Source 10: Wayback Machine — hypnoticworld free scripts
# ─────────────────────────────────────────────
def scrape_wayback_hypnoticworld():
    print("\n=== Source: Wayback hypnoticworld.com ===")
    cdx_url = "http://web.archive.org/cdx/search/cdx"
    params = {
        "url": "www.hypnoticworld.com/hypnosis-scripts/*",
        "output": "json",
        "fl": "timestamp,original",
        "filter": "statuscode:200",
        "collapse": "urlkey",
        "limit": "150"
    }
    try:
        r = requests.get(cdx_url, params=params, headers=HEADERS, timeout=20)
        rows = r.json()
    except Exception as e:
        print(f"  Wayback CDX failed: {e}")
        return

    if len(rows) < 2:
        print("  No archived pages found.")
        return

    count = 0
    for row in rows[1:]:
        if count >= 80:
            break
        ts, orig = row[0], row[1]
        if any(x in orig.lower() for x in ['.css', '.js', '.jpg', '.png', '.gif', 'wp-content', 'wp-admin', 'feed']):
            continue
        # Skip index pages — we want individual script pages
        path = urlparse(orig).path.rstrip('/')
        parts = [p for p in path.split('/') if p]
        if len(parts) < 2:
            continue

        wb_url = f"https://web.archive.org/web/{ts}/{orig}"
        time.sleep(0.6)
        page = fetch(wb_url)
        if not page:
            continue
        soup = BeautifulSoup(page, 'html.parser')
        title_el = soup.find('h1') or soup.find('title')
        title = title_el.get_text(strip=True) if title_el else parts[-1]
        content_el = soup.find('article') or soup.find('div', class_=re.compile(r'entry-content|post-content|script-body|content'))
        if content_el:
            text = content_el.get_text('\n', strip=True)
            if save_script(title, text, "wayback:hypnoticworld"):
                count += 1


# ─────────────────────────────────────────────
# Source 11: Wayback — uncommon-knowledge scripts
# ─────────────────────────────────────────────
def scrape_wayback_uncommon():
    print("\n=== Source: Wayback uncommon-knowledge.co.uk ===")
    cdx_url = "http://web.archive.org/cdx/search/cdx"
    params = {
        "url": "www.uncommon-knowledge.co.uk/hypnosis-scripts/*",
        "output": "json",
        "fl": "timestamp,original",
        "filter": "statuscode:200",
        "collapse": "urlkey",
        "limit": "100"
    }
    try:
        r = requests.get(cdx_url, params=params, headers=HEADERS, timeout=20)
        rows = r.json()
    except Exception as e:
        print(f"  Wayback CDX failed: {e}")
        return

    if len(rows) < 2:
        return

    count = 0
    for row in rows[1:]:
        if count >= 50:
            break
        ts, orig = row[0], row[1]
        if any(x in orig.lower() for x in ['.css', '.js', '.jpg', '.png', '.gif', 'wp-content']):
            continue
        path = urlparse(orig).path.rstrip('/')
        parts = [p for p in path.split('/') if p]
        if len(parts) < 2:
            continue

        wb_url = f"https://web.archive.org/web/{ts}/{orig}"
        time.sleep(0.6)
        page = fetch(wb_url)
        if not page:
            continue
        soup = BeautifulSoup(page, 'html.parser')
        title_el = soup.find('h1') or soup.find('title')
        title = title_el.get_text(strip=True) if title_el else parts[-1]
        content_el = soup.find('article') or soup.find('div', class_=re.compile(r'entry-content|post-content|content'))
        if content_el:
            text = content_el.get_text('\n', strip=True)
            if save_script(title, text, "wayback:uncommon-knowledge"):
                count += 1


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    existing = len([f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.txt')])
    print(f"Starting corpus build. Existing scripts: {existing}")
    print(f"Target: 100+ total scripts\n")

    # Run all scrapers
    scrape_hypnoscripts()
    scrape_freehypnosisscripts()
    scrape_wayback_hypnoticworld()
    scrape_wayback_uncommon()
    scrape_github()
    scrape_gutenberg()
    scrape_archive_org()
    scrape_hypnotherapy_scripts_uk()
    scrape_misc_free_sites()
    scrape_direct_script_pages()
    scrape_wikibooks()

    final = len([f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.txt')])
    print(f"\n{'='*50}")
    print(f"DONE. New scripts saved this run: {TOTAL_SAVED}")
    print(f"Total .txt files in corpus: {final}")
    print(f"{'='*50}")
