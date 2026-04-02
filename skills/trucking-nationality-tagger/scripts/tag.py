import os
import sys
import json
import time
import queue
import threading
import psycopg2
import psycopg2.extras
from collections import defaultdict
from dotenv import load_dotenv
from google import genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load .env from the trucking research folder
load_dotenv(os.path.expanduser("~/research/trucking/.env"))

if not os.getenv("DATABASE_URL"):
    load_dotenv(os.path.expanduser("~/.openclaw/workspace/projects/AutoPax-Trucking-CRM/.env.local"))

# Fallback to current process env if not in .env file
DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.1-flash-lite-preview"

NATIONALITIES = ["Ethiopian", "Eritrean", "Indian", "Pakistani"]
BATCH_SIZE = 30
MAX_WORKERS = 10

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def ensure_tags_column(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'tags';
        """)
        if cur.fetchone(): return
    try:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS tags text[] DEFAULT '{}';")
        conn.commit()
    except Exception as e:
        conn.rollback()

def fetch_leads(conn, limit=None):
    tags_to_check = NATIONALITIES + ["NotApplicable"]
    nationality_check = " AND ".join([f"NOT (COALESCE(l.tags, '{{}}') @> ARRAY['{n}'])" for n in tags_to_check])
    limit_clause = f"LIMIT {limit}" if limit else ""
    daily_clause = ""
    sql = f"""
        SELECT
            l.id,
            COALESCE(c.legal_name, '') AS company_name,
            COALESCE(c.email,       '') AS email
        FROM public.leads l
        LEFT JOIN public.companies c ON c.dot_number = l.dot_number
        WHERE ({nationality_check})
          AND (c.legal_name IS NOT NULL OR c.email IS NOT NULL)
          {daily_clause}
        ORDER BY l.created_at DESC
        {limit_clause};
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()

def db_writer_thread(write_queue, stop_event):
    """
    Drains the queue and performs bulk updates by nationality.
    """
    conn = get_connection()
    try:
        while not stop_event.is_set() or not write_queue.empty():
            updates = []
            try:
                # Accumulate work for up to 0.5s
                while len(updates) < 500:
                    updates.append(write_queue.get(timeout=0.5))
            except queue.Empty:
                pass

            if updates:
                by_nat = defaultdict(list)
                for lead_id, nat in updates:
                    by_nat[nat].append(lead_id)
                
                with conn.cursor() as cur:
                    for nat, ids in by_nat.items():
                        cur.execute("""
                            UPDATE public.leads
                            SET tags = array(
                                SELECT DISTINCT unnest(array_append(COALESCE(tags, '{}'), %s))
                            )
                            WHERE id = ANY(%s::uuid[]);
                        """, (nat, ids))
                conn.commit()
                for _ in range(len(updates)):
                    write_queue.task_done()
    finally:
        conn.close()

def build_prompt(batch):
    rows = "\n".join(f'{i+1}. id={r["id"]} | company={r["company_name"]} | email={r["email"]}' for i, r in enumerate(batch))
    return f"""You are a data analyst classifying trucking company owners by national origin.

For each record, determine if the owner's name or email STRONGLY indicates one of these origins:
- Ethiopian
- Eritrean
- Indian
- Pakistani

Rules:
- High confidence only.
- Match at most ONE nationality.
- If no strong match, set nationality to null.

Records:
{rows}

Respond with a JSON array only:
[{{"id": "<id>", "nationality": "<Ethiopian|Eritrean|Indian|Pakistani|null>"}}]"""

def process_batch(client, batch_rows, batch_num, total_batches, write_queue):
    prompt = build_prompt(batch_rows)
    print(f"[BATCH {batch_num}/{total_batches}] Request sent...")
    
    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    http_options={'timeout': 120000},
                ),
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
            
            results = json.loads(raw)
            match_count = 0
            for item in results:
                nat = item.get("nationality")
                if not nat or nat == "null":
                    nat = "NotApplicable"
                if nat in NATIONALITIES or nat == "NotApplicable":
                    write_queue.put((item["id"], nat))
                    match_count += 1 if nat != "NotApplicable" else 0
            return batch_num, match_count
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "quota" in err or "exhausted" in err or "504" in err or "timeout" in err or "deadline" in err:
                wait = (attempt + 1) * 30
                print(f"  [BATCH {batch_num}] Rate limit / Timeout hit. Sleeping {wait}s...")
                time.sleep(wait)
                continue
            print(f"  [BATCH {batch_num}] ERROR: {e}")
            return batch_num, 0
    return batch_num, 0

def run(limit=None):
    if limit is None:
        limit = 5000
    if not DATABASE_URL or not GEMINI_API_KEY:
        print("ERROR: DATABASE_URL and GEMINI_API_KEY must be set in the environment or ~/research/trucking/.env.")
        sys.exit(1)

    conn = get_connection()
    ensure_tags_column(conn)
    rows = fetch_leads(conn, limit=limit)
    total = len(rows)
    print(f"[DB] Fetched {total} untagged leads to classify.")
    conn.close()

    if total == 0: return

    write_queue = queue.Queue()
    stop_event = threading.Event()
    writer = threading.Thread(target=db_writer_thread, args=(write_queue, stop_event))
    writer.start()

    client = genai.Client(api_key=GEMINI_API_KEY)
    batches = [rows[i : i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    total_batches = len(batches)
    tagged_count = 0
    
    print(f"Firing up to {MAX_WORKERS} concurrent requests for {total_batches} batches...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_batch, client, batch, idx + 1, total_batches, write_queue)
            for idx, batch in enumerate(batches)
        ]
        
        for future in as_completed(futures):
            try:
                _, count = future.result()
                tagged_count += count
            except Exception as e:
                print(f"  Fatal exception in worker: {e}")

    stop_event.set()
    writer.join()

    print(f"\n[DONE] Processed {total} leads. Tagged {tagged_count}.")

if __name__ == "__main__":
    limit_arg = None
    for arg in sys.argv[1:]:
        if arg.isdigit():
            limit_arg = int(arg)
    if "--all" in sys.argv:
        limit_arg = 35000 # Just pull everything
    run(limit=limit_arg)
