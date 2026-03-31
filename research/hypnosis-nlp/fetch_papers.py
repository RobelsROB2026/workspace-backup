import requests
import urllib.parse
import os
import sys
import time

def fetch_dynamic(query):
    papers_dir = os.path.expanduser("~/.openclaw/workspace/research/hypnosis-nlp/papers")
    staging_file = os.path.expanduser("~/.openclaw/workspace/research/hypnosis-nlp/staging_papers.md")
    os.makedirs(papers_dir, exist_ok=True)
    
    # We strictly enforce peer-reviewed Open Access and Full Text available
    search_query = f"{query} AND (OPEN_ACCESS:Y) AND (HAS_FT:Y)"
    encoded = urllib.parse.quote(search_query)
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={encoded}&format=json&resultType=core&pageSize=15"
    
    try:
        print(f"Querying Europe PMC for: {search_query}")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        results = resp.json().get('resultList', {}).get('result', [])
        
        downloaded = 0
        with open(staging_file, "w") as f:
            f.write(f"# Staged Papers for Creative Query: {query}\n\n")
            
            for paper in results:
                pmcid = paper.get('pmcid')
                title = paper.get('title', 'Unknown')
                
                # Check if we already have this paper to avoid duplicates
                if pmcid and not os.path.exists(os.path.join(papers_dir, f"{pmcid}.xml")):
                    ft_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
                    ft_resp = requests.get(ft_url, timeout=15)
                    
                    if ft_resp.status_code == 200:
                        file_path = os.path.join(papers_dir, f"{pmcid}.xml")
                        with open(file_path, "w", encoding="utf-8") as xmlf:
                            xmlf.write(ft_resp.text)
                        
                        f.write(f"- **{title}** (PMCID: {pmcid})\n")
                        print(f"Downloaded new paper: {title[:50]}...")
                        downloaded += 1
                        time.sleep(0.5) # Polite rate limit
                        
                if downloaded >= 3: # Pull exactly 3 highly targeted new full texts per day
                    break
                    
        print(f"\nSuccessfully downloaded {downloaded} novel papers for today's ingest.")
        
    except Exception as e:
        print(f"Error fetching dynamic papers: {e}")

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "hypnosis cognitive anomaly"
    fetch_dynamic(q)
