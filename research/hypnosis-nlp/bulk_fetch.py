import requests
import urllib.parse
import os
import time

def fetch_bulk():
    # Only search for open access papers that physically host the full text on Europe PMC
    queries = [
        "hypnosis AND neuroscience", 
        "hypnosis AND cognitive AND mechanism", 
        "hypnotic AND susceptibility AND mechanism"
    ]
    papers_dir = os.path.expanduser("~/.openclaw/workspace/research/hypnosis-nlp/papers")
    os.makedirs(papers_dir, exist_ok=True)
    
    total_downloaded = 0
    max_papers = 50 # Let's pull 50 full texts right now
    
    with open(os.path.expanduser("~/.openclaw/workspace/research/hypnosis-nlp/bulk_sources.md"), "w") as source_log:
        source_log.write("# Bulk Downloaded Papers\n\n")
        
        for query in queries:
            search_query = f"{query} AND (OPEN_ACCESS:Y) AND (HAS_FT:Y)"
            encoded = urllib.parse.quote(search_query)
            url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={encoded}&format=json&resultType=core&pageSize=30"
            
            try:
                print(f"Searching: {search_query}")
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                results = resp.json().get('resultList', {}).get('result', [])
                
                for paper in results:
                    pmcid = paper.get('pmcid')
                    title = paper.get('title', 'Unknown')
                    year = paper.get('pubYear', 'Unknown')
                    
                    if pmcid and not os.path.exists(os.path.join(papers_dir, f"{pmcid}.xml")):
                        # Fetch the actual full text XML (which contains the whole paper body)
                        ft_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
                        ft_resp = requests.get(ft_url, timeout=15)
                        
                        if ft_resp.status_code == 200:
                            file_path = os.path.join(papers_dir, f"{pmcid}.xml")
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(ft_resp.text)
                            
                            source_log.write(f"- **{title}** ({year}) - PMCID: {pmcid}\n")
                            
                            total_downloaded += 1
                            print(f"Downloaded Full Text [{total_downloaded}/{max_papers}]: {pmcid} - {title[:40]}...")
                            time.sleep(0.5) # Polite rate limiting
                            
                    if total_downloaded >= max_papers:
                        break
            except Exception as e:
                print(f"Error searching {query}: {e}")
                
            if total_downloaded >= max_papers:
                break
                
    print(f"\nBulk download complete. Total full texts physically downloaded: {total_downloaded}")

if __name__ == "__main__":
    fetch_bulk()
