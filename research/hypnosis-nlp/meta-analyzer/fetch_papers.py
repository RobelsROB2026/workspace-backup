import requests
import json
import time

def fetch_semantic_scholar(query, limit=100):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,year,authors,citationCount,influentialCitationCount,publicationTypes,journal"
    }
    
    print(f"Querying Semantic Scholar for: {query}")
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

if __name__ == "__main__":
    queries = [
        "Ericksonian hypnosis mechanism",
        "neuro-linguistic programming anchoring neurology",
        "hypnotic suggestibility default mode network",
        "hypnosis predictive coding active inference",
        "hypnotic trance EEG fMRI",
        "pattern interrupt psychology neurology"
    ]
    
    all_papers = []
    seen_ids = set()
    
    for q in queries:
        papers = fetch_semantic_scholar(q, limit=100)
        for p in papers:
            if p.get('paperId') not in seen_ids and p.get('abstract'):
                seen_ids.add(p.get('paperId'))
                all_papers.append(p)
        print("Waiting 10 seconds before next query to avoid 429...")
        time.sleep(10) # Increased delay to avoid 429
        
    print(f"Successfully fetched {len(all_papers)} unique papers with abstracts.")
    
    with open("corpus.json", "w", encoding="utf-8") as f:
        json.dump(all_papers, f, indent=2)
    print("Saved to corpus.json")
