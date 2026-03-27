"""
tag_optimized.py — Optimized tagger built on Gen3 architecture with:

  O1: Chain of Thought reasoning — model explains its reasoning before classifying
  O2: Upgraded model to gemini-3.1-flash-preview (from flash-lite)
  O3: Cheat sheet for Eritrean/Ethiopian/Indian/Pakistani name indicators
  O4: Strict JSON response_schema — eliminates markdown/parsing issues

  Inherited from Gen3:
    G3-O1: Dedicated DB writer thread with accumulating queue
    G3-O2: Sentinel-based graceful writer shutdown with final flush
    G2-O2: Shared write connection
    G2-O3: Bulk UPDATE by nationality group (ANY(ids::uuid[]))
"""

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

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3-flash-preview"

NATIONALITIES = ["Ethiopian", "Eritrean", "Indian", "Pakistani"]
BATCH_SIZE = 30
MAX_WORKERS = 10
WRITER_DRAIN_INTERVAL = 0.5

_SENTINEL = object()

# O4: Strict response schema — forces structured JSON output, no markdown
RESPONSE_SCHEMA = types.Schema(
    type="ARRAY",
    items=types.Schema(
        type="OBJECT",
        properties={
            "id": types.Schema(type="STRING", description="The lead UUID"),
            "reasoning": types.Schema(type="STRING", description="Brief chain-of-thought reasoning for the classification"),
            "nationality": types.Schema(
                type="STRING",
                description="Detected nationality or null",
                enum=["Ethiopian", "Eritrean", "Indian", "Pakistani", "null"],
            ),
        },
        required=["id", "reasoning", "nationality"],
    ),
)

DRY_RUN = False


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
    nationality_check = " AND ".join([f"NOT (COALESCE(l.tags, '{{}}') @> ARRAY['{n}'])" for n in NATIONALITIES])
    limit_clause = f"LIMIT {limit}" if limit else ""
    sql = f"""
        SELECT
            l.id,
            COALESCE(c.legal_name, '') AS company_name,
            COALESCE(c.email,       '') AS email
        FROM public.leads l
        LEFT JOIN public.companies c ON c.dot_number = l.dot_number
        WHERE ({nationality_check})
          AND (c.legal_name IS NOT NULL OR c.email IS NOT NULL)
        ORDER BY l.created_at
        {limit_clause};
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()


def _db_writer_thread(update_queue, stats):
    """G3-O1: Dedicated writer thread with accumulating queue."""
    conn = get_connection()
    conn.autocommit = False
    total_db_ms = 0.0
    total_writes = 0
    total_updates = 0

    stop_after_flush = False
    while True:
        accumulated = []
        try:
            item = update_queue.get(timeout=WRITER_DRAIN_INTERVAL)
            if item is _SENTINEL:
                break
            accumulated.append(item)
            while True:
                try:
                    item = update_queue.get_nowait()
                    if item is _SENTINEL:
                        stop_after_flush = True
                        break
                    accumulated.append(item)
                except queue.Empty:
                    break
        except queue.Empty:
            continue

        if not accumulated:
            if stop_after_flush:
                break
            continue

        by_nat = defaultdict(list)
        for updates in accumulated:
            for lead_id, nationality in updates:
                by_nat[nationality].append(lead_id)

        if by_nat:
            n_updates = sum(len(v) for v in by_nat.values())
            t_db = time.perf_counter()
            try:
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
                db_ms = (time.perf_counter() - t_db) * 1000
                total_db_ms += db_ms
                total_writes += 1
                total_updates += n_updates
                print(f"  [WRITER] Flushed {n_updates} updates ({len(by_nat)} nat groups, {len(accumulated)} batches) -> {db_ms:.0f}ms")
            except Exception as e:
                conn.rollback()
                print(f"  [WRITER] DB error: {e}")

        if stop_after_flush:
            break

    conn.close()
    stats['db_ms'] = total_db_ms
    stats['writes'] = total_writes
    stats['updates'] = total_updates


def build_prompt(batch):
    rows = "\n".join(f'{i+1}. id={r["id"]} | company={r["company_name"]} | email={r["email"]}' for i, r in enumerate(batch))
    return f"""You are a data analyst classifying trucking company owners by national origin based on company names and email addresses.

For each record, use chain-of-thought reasoning to determine if the company name or email STRONGLY indicates one of these origins:
- Ethiopian
- Eritrean
- Indian
- Pakistani

=== NAME INDICATOR CHEAT SHEET ===

ETHIOPIAN indicators:
- Amharic-origin names: Abebe, Kebede, Tadesse, Haile, Tesfaye, Getachew, Bekele, Desta, Mulugeta, Girma, Dawit, Yohannes, Fekadu, Mekonnen, Wolde, Gebre, Alemu, Asfaw, Assefa, Tessema, Lemma, Dereje, Berhane, Worku, Zeleke, Hagos, Fikre, Teshome, Mengistu, Negash
- Common company patterns: "[Ethiopian name] Trucking", "[Ethiopian name] Transport"
- Email patterns: Ethiopian given names in email prefixes

ERITREAN indicators:
- Tigrinya-origin names: Berhe, Tekle, Habtom, Ghebre, Weldu, Kidane, Tesfai, Amanuel, Berhane, Semere, Yemane, Tsegay, Gebrehiwet, Mehari, Abrham, Kahsay, Gebremedhin, Russom, Fesshaye, Tewelde, Habte, Asmerom, Ogbamichael, Tesfaldet, Kibreab
- Overlap with Ethiopian: Berhane, Haile can be either — lean Eritrean if paired with Tigrinya markers (Ghebre-, Gebr-, Tesfa-)
- Email patterns: Tigrinya given names in email prefixes

INDIAN indicators:
- Common surnames: Patel, Singh, Kumar, Sharma, Gupta, Verma, Joshi, Reddy, Rao, Chauhan, Gill, Dhillon, Sandhu, Sidhu, Grewal, Brar, Bajwa, Cheema, Randhawa, Saini, Mehta, Shah, Bhatt, Desai, Agarwal, Malhotra, Kapoor, Khanna, Chopra, Bansal
- Sikh names (very common in trucking): deep/preet/jit/inder suffixes (Mandeep, Harpreet, Gurjit, Ravinder)
- Common company patterns: "[Surname] Trucking", "[Surname] Transport", "[Surname] Logistics"
- Email patterns: Indian names in email prefixes, firstname.lastname patterns with Indian names

PAKISTANI indicators:
- Common surnames: Khan, Ahmed, Ali, Hussain, Malik, Iqbal, Butt, Chaudhry, Sheikh, Siddiqui, Mirza, Qureshi, Rizvi, Hashmi, Nawaz, Abbasi, Raza, Bukhari, Zaidi, Awan, Niazi, Baloch, Afridi, Yousaf, Durrani
- Given names: Muhammad/Mohammed (very common prefix), Abdul, Usman, Bilal, Imran, Tariq, Faisal, Waseem, Asif, Shahid, Kamran, Nadeem
- Company patterns: "[Pakistani name] Trucking", "[Pakistani name] Express"
- Email patterns: Pakistani names in email prefixes

=== CLASSIFICATION RULES ===
- High confidence only. If ambiguous between two nationalities, set null.
- Match at most ONE nationality per record.
- If no strong match, set nationality to "null".
- Think step by step: identify name cues, match against indicators, then decide.

Records:
{rows}

For each record, provide:
1. "id": the record's UUID
2. "reasoning": brief explanation of what name indicators you see and why you chose the classification
3. "nationality": one of Ethiopian, Eritrean, Indian, Pakistani, or "null"
"""


def process_batch(client, batch_rows, batch_num, total_batches):
    prompt = build_prompt(batch_rows)
    t_api = time.perf_counter()
    print(f"[BATCH {batch_num}/{total_batches}] Request sent...")

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                    http_options={'timeout': 120000},
                ),
            )
            api_ms = (time.perf_counter() - t_api) * 1000
            raw = response.text.strip()

            results = json.loads(raw)
            updates = []
            for item in results:
                nat = item.get("nationality")
                reasoning = item.get("reasoning", "")
                if nat and nat in NATIONALITIES:
                    updates.append((item["id"], nat))
                    if DRY_RUN:
                        print(f"    [CoT] {item['id'][:8]}... -> {nat} | {reasoning}")
            print(f"  [BATCH {batch_num}] API={api_ms:.0f}ms | matches={len(updates)}/{len(batch_rows)}")
            return batch_num, updates
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "quota" in err or "exhausted" in err or "504" in err or "timeout" in err or "deadline" in err:
                wait = (attempt + 1) * 30
                print(f"  [BATCH {batch_num}] Rate limit / Timeout hit. Sleeping {wait}s...")
                time.sleep(wait)
                continue
            print(f"  [BATCH {batch_num}] ERROR: {e}")
            return batch_num, []
    return batch_num, []


def run(full_backfill=False, dry_run=False):
    global DRY_RUN
    DRY_RUN = dry_run

    t_total_start = time.perf_counter()

    conn = get_connection()
    ensure_tags_column(conn)

    limit = None if full_backfill else BATCH_SIZE
    t_fetch = time.perf_counter()
    rows = fetch_leads(conn, limit=limit)
    fetch_ms = (time.perf_counter() - t_fetch) * 1000
    total = len(rows)
    print(f"[DB] Fetched {total} leads in {fetch_ms:.0f}ms")
    conn.close()

    if total == 0: return

    client = genai.Client(api_key=GEMINI_API_KEY)
    batches = [rows[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    total_batches = len(batches)

    mode_label = "DRY RUN" if dry_run else "LIVE"
    print(f"[OPTIMIZED] Mode={mode_label} | Model={MODEL} | BATCH_SIZE={BATCH_SIZE} | MAX_WORKERS={MAX_WORKERS} | {total_batches} batches")
    print(f"[OPTIMIZED] Features: CoT reasoning, name cheat sheet, strict JSON schema")

    if dry_run:
        print(f"[DRY RUN] Will classify but NOT write to database")

    # G3-O1: Start dedicated writer thread (skip in dry run)
    update_queue = queue.Queue() if not dry_run else None
    writer_stats = {}
    writer = None
    if not dry_run:
        writer = threading.Thread(target=_db_writer_thread, args=(update_queue, writer_stats), daemon=True)
        writer.start()

    tagged_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_batch = {
            executor.submit(process_batch, client, batch, idx + 1, total_batches): (batch, idx + 1)
            for idx, batch in enumerate(batches)
        }

        for future in as_completed(future_to_batch):
            batch, batch_num = future_to_batch[future]
            try:
                b_num, updates = future.result()
                if updates:
                    tagged_count += len(updates)
                    if not dry_run:
                        update_queue.put(updates)
                else:
                    print(f"  [BATCH {b_num}] Done. No matches.")
            except Exception as e:
                print(f"  [BATCH {batch_num}] Fatal exception: {e}")

    # Signal writer to stop and wait
    if not dry_run and writer:
        update_queue.put(_SENTINEL)
        writer.join(timeout=60)

    total_s = time.perf_counter() - t_total_start
    leads_per_min = (total / total_s) * 60 if total_s > 0 else 0
    db_ms = writer_stats.get('db_ms', 0)
    n_writes = writer_stats.get('writes', 0)

    print(f"\n[OPTIMIZED DONE] Processed {total} leads in {total_s:.1f}s. Tagged {tagged_count}.")
    print(f"[OPTIMIZED PERF] Throughput: {leads_per_min:.0f} leads/min")
    if not dry_run:
        print(f"[OPTIMIZED PERF] DB writes: {n_writes} flushes, {db_ms:.0f}ms total")
    print(f"OPT_LEADS_PER_MIN {leads_per_min:.0f}")
    print(f"OPT_TAGGED {tagged_count}")


if __name__ == "__main__":
    full = "--all" in sys.argv
    dry = "--dry-run" in sys.argv
    run(full_backfill=full, dry_run=dry)
