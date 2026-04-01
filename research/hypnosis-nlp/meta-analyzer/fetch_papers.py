import requests
import json
import time
import sys

def fetch_semantic_scholar(query, limit=100):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,year,authors,citationCount,influentialCitationCount,publicationTypes,journal"
    }
    print(f"Querying Semantic Scholar for: {query}")
    for attempt in range(5):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 429:
                wait_time = (attempt + 1) * 30
                print(f"Rate limited (429). Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except Exception as e:
            if "429" in str(e):
                wait_time = (attempt + 1) * 30
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            print(f"Error fetching data: {e}")
            return []
    return []

def run_fetch(phase=1):
    if phase == 1:
        queries = [
            "Ericksonian hypnosis mechanism",
            "neuro-linguistic programming anchoring neurology",
            "hypnotic suggestibility default mode network",
            "hypnosis predictive coding active inference",
            "hypnotic trance EEG fMRI",
            "pattern interrupt psychology neurology"
        ]
        out_file = "corpus.json"
        exclude_ids = set()
    else:
        queries = [
            "hypnotic prosody and vocal tone",
            "biobehavioral synchrony hypnosis",
            "therapist expectancy effect hypnosis",
            "interpersonal neurobiology hypnosis"
        ]
        out_file = "phase2_corpus.json"
        exclude_ids = set()
        try:
            with open("corpus.json", "r") as f:
                phase1 = json.load(f)
                exclude_ids = {p.get("paperId") for p in phase1}
        except Exception:
            pass

    all_papers = []
    seen_ids = set(exclude_ids)
    
    for q in queries:
        papers = fetch_semantic_scholar(q, limit=100)
        for p in papers:
            if p.get('paperId') not in seen_ids and p.get('abstract'):
                seen_ids.add(p.get('paperId'))
                all_papers.append(p)
        print("Waiting 15 seconds before next query to avoid 429...")
        time.sleep(15)
        
    print(f"Successfully fetched {len(all_papers)} unique papers with abstracts.")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_papers, f, indent=2)
    print(f"Saved to {out_file}")

if __name__ == "__main__":
    phase = 2 if len(sys.argv) > 1 and sys.argv[1] == "2" else 1
    run_fetch(phase)
