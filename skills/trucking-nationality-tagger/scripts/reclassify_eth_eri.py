"""
reclassify_eth_eri.py — Re-classify leads currently tagged Ethiopian or Eritrean.

Queries leads where tags contain 'Ethiopian' or 'Eritrean', re-runs Gemini CoT
classification, then removes old Ethiopian/Eritrean tags and appends the new
classification (or just removes if result is 'null').
"""

import os
import sys
import json
import time
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from google import genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv(os.path.expanduser("~/research/trucking/.env"))
load_dotenv()  # fallback to cwd

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.0-flash"

BATCH_SIZE = 30
MAX_WORKERS = 10

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

NATIONALITIES = ["Ethiopian", "Eritrean", "Indian", "Pakistani"]
OLD_TAGS = ["Ethiopian", "Eritrean"]


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def fetch_eth_eri_leads(conn):
    """Fetch leads tagged Ethiopian OR Eritrean."""
    sql = """
        SELECT
            l.id,
            l.tags,
            COALESCE(c.legal_name, '') AS company_name,
            COALESCE(c.email,       '') AS email
        FROM public.leads l
        LEFT JOIN public.companies c ON c.dot_number = l.dot_number
        WHERE (COALESCE(l.tags, '{}') @> ARRAY['Ethiopian']
            OR COALESCE(l.tags, '{}') @> ARRAY['Eritrean'])
          AND (c.legal_name IS NOT NULL OR c.email IS NOT NULL)
        ORDER BY l.created_at;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()


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
- IMPORTANT: These leads were previously classified as Ethiopian or Eritrean. Re-evaluate each one fresh — do NOT assume the previous classification was correct.

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
            print(f"  [BATCH {batch_num}] API={api_ms:.0f}ms | {len(results)} results")
            return batch_num, results
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


def apply_updates(conn, results):
    """For each lead: remove Ethiopian/Eritrean tags, append new classification if not null."""
    updated = 0
    removed_only = 0
    reclassified = 0
    unchanged = 0

    with conn.cursor() as cur:
        for item in results:
            lead_id = item["id"]
            new_nat = item.get("nationality")
            reasoning = item.get("reasoning", "")
            is_null = (new_nat == "null" or new_nat is None or new_nat not in NATIONALITIES)

            if is_null:
                # Remove Ethiopian and Eritrean tags, don't add anything
                cur.execute("""
                    UPDATE public.leads
                    SET tags = array_remove(array_remove(COALESCE(tags, '{}'), 'Ethiopian'), 'Eritrean')
                    WHERE id = %s::uuid;
                """, (lead_id,))
                removed_only += 1
                print(f"  [-] {lead_id[:8]}... REMOVED Eth/Eri tags | {reasoning}")
            else:
                # Remove old Ethiopian/Eritrean, add new classification
                cur.execute("""
                    UPDATE public.leads
                    SET tags = array(
                        SELECT DISTINCT unnest(
                            array_append(
                                array_remove(array_remove(COALESCE(tags, '{}'), 'Ethiopian'), 'Eritrean'),
                                %s
                            )
                        )
                    )
                    WHERE id = %s::uuid;
                """, (new_nat, lead_id))
                reclassified += 1
                print(f"  [~] {lead_id[:8]}... -> {new_nat} | {reasoning}")
            updated += 1

        conn.commit()

    return updated, removed_only, reclassified


def run(dry_run=False):
    t_start = time.perf_counter()

    conn = get_connection()
    t_fetch = time.perf_counter()
    rows = fetch_eth_eri_leads(conn)
    fetch_ms = (time.perf_counter() - t_fetch) * 1000
    total = len(rows)
    print(f"[DB] Fetched {total} leads tagged Ethiopian/Eritrean in {fetch_ms:.0f}ms")
    conn.close()

    if total == 0:
        print("No leads to reclassify.")
        return

    client = genai.Client(api_key=GEMINI_API_KEY)
    batches = [rows[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    total_batches = len(batches)

    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"[RECLASSIFY] Mode={mode} | Model={MODEL} | {total} leads | {total_batches} batches")

    all_results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_batch = {
            executor.submit(process_batch, client, batch, idx + 1, total_batches): idx + 1
            for idx, batch in enumerate(batches)
        }
        for future in as_completed(future_to_batch):
            batch_num = future_to_batch[future]
            try:
                b_num, results = future.result()
                all_results.extend(results)
            except Exception as e:
                print(f"  [BATCH {batch_num}] Fatal: {e}")

    print(f"\n[RECLASSIFY] Got {len(all_results)} classification results")

    if dry_run:
        for item in all_results:
            nat = item.get("nationality", "null")
            reasoning = item.get("reasoning", "")
            print(f"  [DRY] {item['id'][:8]}... -> {nat} | {reasoning}")
        print(f"[DRY RUN] No DB changes made.")
    else:
        conn = get_connection()
        conn.autocommit = False
        updated, removed, reclassified = apply_updates(conn, all_results)
        conn.close()
        print(f"\n[RECLASSIFY DONE] Updated {updated} leads: {reclassified} reclassified, {removed} tags removed (null)")

    total_s = time.perf_counter() - t_start
    print(f"[RECLASSIFY] Total time: {total_s:.1f}s")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
