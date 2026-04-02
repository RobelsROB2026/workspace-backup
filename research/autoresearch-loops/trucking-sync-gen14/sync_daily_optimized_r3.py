"""
Gen 14 optimizations (builds on Gen13):
  O1-O29: inherited from Gen13
  O30+: See notes/autoresearch_plan.md for trial results
"""
import urllib.request
import urllib.parse
import json
import gzip
import http.client
import ssl
import threading
import psycopg2
import psycopg2.extras
import os
import sys
import datetime
import csv
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")
APP_TOKEN = "RYTtVWM1wzYTCUvpOAOby61jf"

HTTP_TIMEOUT = 30
MAX_BATCH_WORKERS = 20
BATCH_SIZE = 300

_t_start_total = time.perf_counter()

# --- Phase 1 fetching still uses urllib.request (only 3-4 requests, not worth optimizing) ---

def fetch_with_retry(url, req_headers, max_retries=3, base_delay=1.0):
    """Fetch URL with exponential backoff retry. Returns parsed JSON or []."""
    req = urllib.request.Request(url, headers=req_headers)
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as res:
                raw = res.read()
                if res.info().get('Content-Encoding') == 'gzip':
                    raw = gzip.decompress(raw)
                return json.loads(raw)  # O20: skip .decode(), json.loads accepts bytes
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[WARN] Failed after {max_retries} attempts ({url[:80]}...): {e}")
                return []
            delay = base_delay * (2 ** attempt)
            print(f"[RETRY] attempt {attempt+1} failed ({e}), retrying in {delay:.1f}s...")
            time.sleep(delay)
    return []

headers = {'User-Agent': 'AutoPax Data Pipeline', 'X-App-Token': APP_TOKEN, 'Accept-Encoding': 'gzip'}

# O23: Thread-local persistent HTTPS connections for Phase 2
_SSL_CTX = ssl.create_default_context()
_thread_local = threading.local()

def _get_persistent_conn():
    """Get or create a persistent HTTPS connection for this thread."""
    conn = getattr(_thread_local, 'conn', None)
    if conn is None:
        conn = http.client.HTTPSConnection("data.transportation.gov", timeout=HTTP_TIMEOUT, context=_SSL_CTX)
        _thread_local.conn = conn
    return conn

def _persistent_fetch_json(path, max_retries=3, base_delay=1.0):
    """Fetch JSON from data.transportation.gov using persistent connection. Returns parsed JSON or []."""
    req_headers = {
        'User-Agent': 'AutoPax Data Pipeline',
        'X-App-Token': APP_TOKEN,
        'Accept-Encoding': 'gzip',
        'Connection': 'keep-alive',
    }
    for attempt in range(max_retries):
        try:
            conn = _get_persistent_conn()
            conn.request("GET", path, headers=req_headers)
            res = conn.getresponse()
            raw = res.read()
            if res.getheader('Content-Encoding') == 'gzip':
                raw = gzip.decompress(raw)
            if res.status != 200:
                raise Exception(f"HTTP {res.status}")
            return json.loads(raw)
        except Exception as e:
            # Connection may be stale — close and recreate
            try:
                _thread_local.conn.close()
            except Exception:
                pass
            _thread_local.conn = None
            if attempt == max_retries - 1:
                print(f"[WARN] Failed after {max_retries} attempts: {e}")
                return []
            delay = base_delay * (2 ** attempt)
            print(f"[RETRY] attempt {attempt+1} failed ({e}), retrying in {delay:.1f}s...")
            time.sleep(delay)
    return []

# O16: Start DB connections in background while source APIs are fetched
_conn_result = [None, None]  # [conn, error]
_conn2_result = [None, None]  # [conn2, error] for parallel leads INSERT

def _make_db_conn():
    c = psycopg2.connect(
        dbname="postgres",
        user="postgres.xyduftkyfshlvglygbym",
        password=SUPABASE_DB_PASSWORD,
        host="aws-0-us-west-2.pooler.supabase.com",
        port="6543"
    )
    c.autocommit = True
    return c

def _connect_db():
    try:
        _conn_result[0] = _make_db_conn()
    except Exception as e:
        _conn_result[1] = e

def _connect_db2():
    try:
        _conn2_result[0] = _make_db_conn()
    except Exception as e:
        _conn2_result[1] = e

def _fetch_new_ventures():
    # NOTE: No $select — returns ALL fields including company profile data (O19)
    yesterday = (datetime.date.today() - datetime.timedelta(days=3)).strftime("%Y%m%d")
    url = f"https://data.transportation.gov/resource/az4n-8mr2.json?$where=add_date>='{yesterday}'&$limit=10000"
    return fetch_with_retry(url, headers)

def _fetch_renewals():
    target_date = datetime.date.today() - datetime.timedelta(days=275)
    expiring_date = target_date.strftime("%m/%d/%Y")
    url = f"https://data.transportation.gov/resource/qh9u-swkp.json?effective_date={urllib.parse.quote(expiring_date)}&$limit=10000"
    return fetch_with_retry(url, headers)

def _fetch_cancellations():
    """Returns list of (dot, insurer, cancel_date) tuples for current-year cancellations."""
    view_url = "https://data.transportation.gov/api/views/xkmg-ff2t.json"
    req_view = urllib.request.Request(view_url, headers=headers)
    results = []
    try:
        with urllib.request.urlopen(req_view, timeout=HTTP_TIMEOUT) as res:
            raw_meta = res.read()
            if res.info().get('Content-Encoding') == 'gzip' or raw_meta[:2] == b'\x1f\x8b':
                raw_meta = gzip.decompress(raw_meta)
            meta = json.loads(raw_meta)  # O20
            blob_id = meta.get('blobId')
            blob_name = meta.get('blobFilename')
        file_url = f"https://data.transportation.gov/api/views/xkmg-ff2t/files/{blob_id}?download=true&filename={blob_name}"
        req_file = urllib.request.Request(file_url, headers=headers)
        with urllib.request.urlopen(req_file, timeout=HTTP_TIMEOUT) as res:
            raw_bytes = res.read()
            if res.info().get('Content-Encoding') == 'gzip' or raw_bytes[:2] == b'\x1f\x8b':
                raw_bytes = gzip.decompress(raw_bytes)
            raw_text = raw_bytes.decode('utf-8', errors='ignore')
            reader = csv.reader(io.StringIO(raw_text))
            current_year = str(datetime.date.today().year)
            for row in reader:
                if len(row) > 16:
                    if row[3] == "Cancelled" and current_year in row[13]:
                        dot = ''.join(filter(str.isdigit, row[1].strip())).lstrip('0')
                        if dot:
                            results.append((dot, row[16].strip(), row[13].strip()))
    except Exception as e:
        print(f"Error fetching cancellations: {e}")
    return results

# O1+O16+O29: Fetch all 3 sources AND 2 DB connections concurrently
_t_sources = time.perf_counter()
with ThreadPoolExecutor(max_workers=5) as src_exec:
    f_db  = src_exec.submit(_connect_db)
    f_db2 = src_exec.submit(_connect_db2)
    f_nv  = src_exec.submit(_fetch_new_ventures)
    f_rw  = src_exec.submit(_fetch_renewals)
    f_can = src_exec.submit(_fetch_cancellations)
    raw_nv  = f_nv.result()
    raw_rw  = f_rw.result()
    raw_can = f_can.result()
    f_db.result()
    f_db2.result()
_t_sources_elapsed = time.perf_counter() - _t_sources
print(f"[PERF] Phase 1 (parallel source fetch+2x DB connect): {_t_sources_elapsed*1000:.0f}ms")

if _conn_result[1]:
    print(f"Failed to connect: {_conn_result[1]}")
    sys.exit(1)
conn = _conn_result[0]
conn2 = _conn2_result[0]  # may be None if conn2 failed; fallback to serial
if _conn2_result[1]:
    print(f"[WARN] conn2 failed ({_conn2_result[1]}), falling back to serial INSERTs")
cursor = conn.cursor()
print("Connected to Supabase. Starting Gen14 Daily Sync...")

leads_to_insert = {}
all_dots = set()

# O19: Parse New Ventures — extract company profile directly from source data
nv_company_rows = []

def _parse_company_from_raw(c, insurer=None):
    """Build company tuple from a raw API record (az4n-8mr2 format)."""
    power_units = c.get('power_units', '0')
    if not power_units or not str(power_units).isdigit():
        power_units = 0
    else:
        power_units = int(power_units)
    add_date_str = c.get('add_date')
    sql_date = None
    if add_date_str and len(str(add_date_str)) == 8 and str(add_date_str).isdigit():
        add_date_str = str(add_date_str)
        sql_date = f"{add_date_str[:4]}-{add_date_str[4:6]}-{add_date_str[6:]}"
    dot = c.get('dot_number', '').strip().lstrip('0')
    return dot, (dot, c.get('legal_name'), c.get('dba_name'),
        c.get('phy_street'), c.get('phy_city'), c.get('phy_state'), c.get('phy_zip'),
        c.get('phone'), c.get('email_address'), sql_date, power_units,
        insurer, None, None)

for nv in raw_nv:
    dot = str(nv.get('dot_number', '')).strip()
    dot = ''.join(filter(str.isdigit, dot)).lstrip('0')
    if dot:
        leads_to_insert[dot] = {'type': 'New Venture', 'notes': f"Added on {nv.get('add_date')}", 'insurer': None}
        all_dots.add(dot)
        _, row = _parse_company_from_raw(nv, insurer=None)
        nv_company_rows.append(row)
print(f"Found {len(raw_nv)} New Ventures ({len(nv_company_rows)} company rows extracted from source).")

for rw in raw_rw:
    dot = str(rw.get('dot_number', '')).strip()
    dot = ''.join(filter(str.isdigit, dot)).lstrip('0')
    if dot and dot not in leads_to_insert:
        insurer = rw.get('name_company', 'Unknown')
        leads_to_insert[dot] = {'type': '90-Day Renewal', 'notes': f"Current Insurer: {insurer}", 'insurer': insurer}
        all_dots.add(dot)
print(f"Found {len(raw_rw)} 90-Day Renewals.")

cancel_count = 0
for (dot, insurer, cancel_date) in raw_can:
    if dot and dot not in leads_to_insert:
        leads_to_insert[dot] = {'type': 'Recent Cancellation', 'notes': f"Cancelled on {cancel_date} by {insurer}", 'insurer': insurer}
        all_dots.add(dot)
        cancel_count += 1
print(f"Found {cancel_count} Recent Cancellations.")
print(f"Total Unique High-Intent Leads Today: {len(all_dots)}")

if len(all_dots) == 0:
    print("No leads to process. Exiting.")
    sys.exit(0)

# O19: Batch-fetch only non-NV DOTs
nv_dots = {row[0] for row in nv_company_rows}
batch_dots = [d for d in all_dots if d not in nv_dots]
print(f"[O19] NV DOTs reused from source: {len(nv_dots)} | Remaining to batch-fetch: {len(batch_dots)}")

_SELECT_COLS = "dot_number,legal_name,dba_name,phy_street,phy_city,phy_state,phy_zip,phone,email_address,add_date,power_units"

def _build_batch_path(batch):
    """Build URL path (not full URL) for persistent connection."""
    dot_str = ",".join([f"'{d.strip()}'" for d in batch if d.strip().isalnum()])
    if not dot_str:
        return None
    where_clause = f"dot_number in ({dot_str})"
    return f"/resource/az4n-8mr2.json?$select={_SELECT_COLS}&$where={urllib.parse.quote(where_clause)}&$limit={BATCH_SIZE}"

# O23: Phase 2 uses persistent connections
def _fetch_company_batch_persistent(batch):
    path = _build_batch_path(batch)
    if not path:
        return []
    return _persistent_fetch_json(path)

_t_fetch = time.perf_counter()
batches = [batch_dots[i:i+BATCH_SIZE] for i in range(0, len(batch_dots), BATCH_SIZE)]
print(f"Fetching company profiles: {len(batches)} batches (O23: persistent connections)...")

# O30: Manual SQL building with adapt() — skips mogrify template parsing overhead
from psycopg2.extensions import adapt, QuotedString

def _adapt_val(v):
    """Adapt a single Python value to SQL literal bytes."""
    if v is None:
        return b"NULL"
    a = adapt(v)
    if hasattr(a, 'encoding'):
        a.encoding = 'utf-8'
    return a.getquoted()

def _build_values_fast(rows):
    """Build VALUES bytes from rows using direct adapt() — faster than mogrify."""
    parts = []
    for row in rows:
        parts.append(b"(" + b",".join(_adapt_val(v) for v in row) + b")")
    return b",".join(parts)

# O27: Pre-build NV company SQL while batch fetches run
_nv_build_future = None
if nv_company_rows:
    _pre_mex = ThreadPoolExecutor(max_workers=1)
    _nv_build_future = _pre_mex.submit(_build_values_fast, nv_company_rows)

companies_to_insert = list(nv_company_rows)
fetched_company_rows = []
upserted_dots = set(nv_dots)

# O32: Pre-build NV leads immediately (they're already in upserted_dots)
leads_batch = []
for dot in nv_dots:
    data = leads_to_insert.get(dot)
    if data:
        leads_batch.append((str(dot), 'New', data['notes'], data['type']))

with ThreadPoolExecutor(max_workers=MAX_BATCH_WORKERS) as executor:
    futures = {executor.submit(_fetch_company_batch_persistent, b): i for i, b in enumerate(batches)}
    for future in as_completed(futures):
        try:
            batch_companies = future.result()
        except Exception as e:
            print(f"Error in batch {futures[future]}: {e}")
            continue
        for c in (batch_companies or []):
            dot, row = _parse_company_from_raw(c, insurer=leads_to_insert.get(
                c.get('dot_number', '').strip().lstrip('0'), {}).get('insurer'))
            companies_to_insert.append(row)
            fetched_company_rows.append(row)
            upserted_dots.add(dot)
            # O32: Build lead tuple inline during fetch
            lead_data = leads_to_insert.get(dot)
            if lead_data:
                leads_batch.append((str(dot), 'New', lead_data['notes'], lead_data['type']))

_fetch_elapsed = time.perf_counter() - _t_fetch
print(f"[PERF] Phase 2 (batch fetch+parse): {_fetch_elapsed*1000:.0f}ms | {len(batches)} batches")

# O22+O27: Combined upsert with pre-mogrified NV rows
_t_db_combined = time.perf_counter()

if companies_to_insert and leads_batch:
    # O30: Build company SQL values first, then overlap INSERT with leads build
    _t_build = time.perf_counter()
    nv_vals = _nv_build_future.result() if _nv_build_future else b""
    fetched_vals = _build_values_fast(fetched_company_rows)
    if nv_vals and fetched_vals:
        comp_vals = nv_vals + b"," + fetched_vals
    elif nv_vals:
        comp_vals = nv_vals
    else:
        comp_vals = fetched_vals
    if _nv_build_future:
        _pre_mex.shutdown(wait=False)

    comp_sql = (
        b"INSERT INTO companies (dot_number, legal_name, dba_name, phy_street, phy_city, phy_state, phy_zip, phone, email, add_date, power_units, insurance_provider, cargo_classification, vehicle_oos_rate) VALUES " + comp_vals + b" ON CONFLICT (dot_number) DO UPDATE SET insurance_provider = COALESCE(EXCLUDED.insurance_provider, companies.insurance_provider)"
    )

    # O31: Fire company INSERT immediately, build leads SQL while DB processes it
    if conn2:
        _comp_exec = ThreadPoolExecutor(max_workers=1)
        _f_comp = _comp_exec.submit(cursor.execute, comp_sql)
        # Build leads SQL while company INSERT executes on DB
        leads_vals = _build_values_fast(leads_batch)
        leads_sql = (
            b"INSERT INTO leads (dot_number, status, agent_notes, lead_type) VALUES " + leads_vals + b" ON CONFLICT (dot_number) DO UPDATE SET status = 'New', lead_type = EXCLUDED.lead_type, updated_at = NOW()"
        )
        _f_comp.result()  # Wait for company INSERT (FK dependency)
        cur2 = conn2.cursor()
        cur2.execute(leads_sql)
        cur2.close()
        _comp_exec.shutdown(wait=False)
        _t_build_elapsed = time.perf_counter() - _t_build
        print(f"[PERF] SQL build+exec (O31 overlap): {_t_build_elapsed*1000:.0f}ms")
        print(f"UPSERTED {len(companies_to_insert)} companies + {len(leads_batch)} leads via overlapped autocommit (O31).")
    else:
        leads_vals = _build_values_fast(leads_batch)
        leads_sql = (
            b"INSERT INTO leads (dot_number, status, agent_notes, lead_type) VALUES " + leads_vals + b" ON CONFLICT (dot_number) DO UPDATE SET status = 'New', lead_type = EXCLUDED.lead_type, updated_at = NOW()"
        )
        cursor.execute(comp_sql)
        cursor.execute(leads_sql)
        _t_build_elapsed = time.perf_counter() - _t_build
        print(f"[PERF] SQL build+exec (serial fallback): {_t_build_elapsed*1000:.0f}ms")
        print(f"UPSERTED {len(companies_to_insert)} companies + {len(leads_batch)} leads via serial autocommit.")

elif companies_to_insert:
    insert_comp_query = """
        INSERT INTO companies (
            dot_number, legal_name, dba_name, phy_street, phy_city, phy_state, phy_zip,
            phone, email, add_date, power_units, insurance_provider, cargo_classification, vehicle_oos_rate
        )
        VALUES %s
        ON CONFLICT (dot_number) DO UPDATE SET
            legal_name = EXCLUDED.legal_name,
            phy_state = EXCLUDED.phy_state,
            phone = EXCLUDED.phone,
            power_units = EXCLUDED.power_units,
            insurance_provider = COALESCE(EXCLUDED.insurance_provider, companies.insurance_provider),
            cargo_classification = COALESCE(EXCLUDED.cargo_classification, companies.cargo_classification),
            vehicle_oos_rate = COALESCE(EXCLUDED.vehicle_oos_rate, companies.vehicle_oos_rate)
    """
    psycopg2.extras.execute_values(cursor, insert_comp_query, companies_to_insert, page_size=5000)
    print(f"UPSERTED {len(companies_to_insert)} company profiles (no leads).")

_t_db_combined_elapsed = time.perf_counter() - _t_db_combined
print(f"[PERF] Phase 3+4 (combined CTE upsert): {_t_db_combined_elapsed*1000:.0f}ms")

cursor.close()
conn.close()
if conn2:
    conn2.close()

_t_total_elapsed = time.perf_counter() - _t_start_total
total_records = len(companies_to_insert) + len(leads_batch)
rpm = (total_records / _t_total_elapsed) * 60 if _t_total_elapsed > 0 else 0

print(f"\n[PERF] Total pipeline time: {_t_total_elapsed:.2f}s")
print(f"[PERF] Phase breakdown: src={_t_sources_elapsed:.2f}s | batch={_fetch_elapsed:.2f}s | cte_upsert={_t_db_combined_elapsed:.3f}s")
print(f"[PERF] Records processed: {total_records} ({len(companies_to_insert)} companies + {len(leads_batch)} leads)")
print(f"[PERF] RPM: {rpm:.0f}")
print(f"GEN14_ELAPSED_SEC {_t_total_elapsed:.3f}")
print(f"GEN14_RPM {rpm:.0f}")
