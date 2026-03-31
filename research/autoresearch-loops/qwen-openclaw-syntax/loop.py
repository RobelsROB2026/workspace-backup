#!/usr/bin/env python3
import json
import subprocess
import os
import requests
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:4b"

def test_qwen(prompt_path):
    with open(prompt_path, 'r') as f:
        system_prompt = f.read()
    
    with open('tasks.json', 'r') as f:
        tasks = json.load(f)

    score = 0
    total = len(tasks)
    
    for task in tasks:
        user_prompt = f"TASK: {task[\'request\']}\nOutput ONLY valid JSON representing the OpenClaw tool call. Your entire response MUST be inside a ```json block."
        
        payload = {
            "model": MODEL,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,

            "options": {"num_ctx": 4096}
        }
        
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
            result = resp.json()['response']
            
            cleaned = result.replace("```json\n", "").replace("\n```", "").replace("```", "").strip()
            data = json.loads(cleaned)
            tool_name = data.get('name') or data.get('tool')
            
            if tool_name == task['expected_tool']:
                params = data.get('parameters', {})
                success = True
                for k, v in task['required_params'].items():
                    if k not in params:
                        success = False
                if success:
                    score += 1
        except Exception as e:
            pass
            
    return score / total

def mutate_prompt(baseline_path, score):
    with open(baseline_path, 'r') as f:
        old_prompt = f.read()
    
    mutation_request = (
        "You are a prompt engineer for a local Qwen model. "
        f"The current system prompt is: {old_prompt} "
        f"It currently scores {score*100}% on OpenClaw tool-calling tasks. "
        "Rewrite it to be clearer about JSON schemas. It must explicitly tell Qwen to output a JSON object with 'name' and 'parameters' keys. "
        "Return ONLY the new system prompt text. Do NOT use markdown code blocks. NO XML. NO EXPLANATIONS. NO TOOLS."
    )
    
    try:
        cmd = ["claude", "-p", mutation_request, "--tools", "disabled"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.stdout.strip()

    except Exception:
        return old_prompt

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if not os.path.exists("baseline_prompt.txt"):
        with open("baseline_prompt.txt", "w") as f:
            f.write("You are an AI assistant. Output tool calls as JSON with 'name' and 'parameters'.")

    round_num = 1
    best_score = 0.0
    
    print("Starting Qwen OpenClaw Syntax Optimization Loop...")
    while True:
        print(f"\n--- Round {round_num} ---")
        
        baseline_score = test_qwen("baseline_prompt.txt")
        print(f"Baseline Score: {baseline_score*100:.0f}%")
        
        if baseline_score > best_score:
            best_score = baseline_score
            print("NEW HIGH SCORE! Saved.")
            
        if best_score >= 1.0:
            print("Optimization Complete: 100% Success Rate achieved.")
            break
            
        print("Mutating prompt with Claude...")
        new_prompt = mutate_prompt("baseline_prompt.txt", baseline_score)
        
        with open("candidate_prompt.txt", "w") as f:
            f.write(new_prompt)
            
        print("Testing candidate...")
        candidate_score = test_qwen("candidate_prompt.txt")
        print(f"Candidate Score: {candidate_score*100:.0f}%")
        
        if candidate_score > baseline_score:
            print("Candidate won! Replacing baseline.")
            os.rename("candidate_prompt.txt", "baseline_prompt.txt")
            best_score = candidate_score
        else:
            print("Candidate lost. Discarding.")
            
        round_num += 1
        time.sleep(2)

if __name__ == "__main__":
    main()
