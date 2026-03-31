import sys
sys.stdout.reconfigure(line_buffering=True)
import json
import os
import subprocess
import time
from pathlib import Path

# Paths
DIR = Path("~/research/hypnosis-meta-analyzer").expanduser()
CORPUS_PATH = DIR / "corpus.json"
ANOMALIES_PATH = DIR / "anomalies.json"

def run_claude_query(prompt):
    """Run a prompt through the claude CLI and return the output."""
    try:
        # Using a higher turn limit since we are analyzing data
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            print(f"Error running Claude: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Exception running Claude: {e}")
        return None

def extract_anomalies():
    if not CORPUS_PATH.exists():
        print("Corpus not found.")
        return

    with open(CORPUS_PATH, "r") as f:
        corpus = json.load(f)

    anomalies = []
    if ANOMALIES_PATH.exists():
        with open(ANOMALIES_PATH, "r") as f:
            anomalies = json.load(f)
    
    processed_ids = {a['paperId'] for a in anomalies}
    
    print(f"Starting anomaly extraction for {len(corpus)} papers...")
    
    for i, paper in enumerate(corpus):
        pid = paper.get('paperId')
        if pid in processed_ids:
            continue
            
        title = paper.get('title')
        abstract = paper.get('abstract')
        
        print(f"[{i+1}/{len(corpus)}] Analyzing: {title}")
        
        prompt = f"""Analyze the following scientific paper abstract and extract high-value insights for novel hypothesis generation.

Focus EXCLUSIVELY on:
1. "Unexplained Variances": Where did the results deviate from the hypothesis or existing theory?
2. "Incidental Findings": Did the authors mention any side-effects, secondary observations, or strange anomalies that weren't the main focus?
3. "Technical Sidenotes": Are there specific physiological or neurological mechanisms mentioned as "interesting" or "unexpected"?

Format your output as a valid JSON object with the following keys:
- unexplained_variances: (list of strings)
- incidental_findings: (list of strings)
- technical_sidenotes: (list of strings)

If none are found, use empty lists. Do not include any other text.

ABSTRACT:
{abstract}
"""
        response = run_claude_query(prompt)
        
        if response:
            try:
                # Basic JSON cleanup in case Claude includes markdown blocks
                clean_json = response
                if "```json" in clean_json:
                    clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json:
                    clean_json = clean_json.split("```")[1].split("```")[0].strip()
                
                data = json.loads(clean_json)
                paper_anomaly = {
                    "paperId": pid,
                    "title": title,
                    "year": paper.get('year'),
                    "insights": data
                }
                anomalies.append(paper_anomaly)
                
                # Save progress
                with open(ANOMALIES_PATH, "w") as f:
                    json.dump(anomalies, f, indent=2)
                    
            except Exception as e:
                print(f"Failed to parse JSON for {pid}: {e}")
                print(f"Raw response: {response[:200]}...")
        
        # Check for Claude Pro limit resets or just take a breath
        time.sleep(2)

if __name__ == "__main__":
    extract_anomalies()
