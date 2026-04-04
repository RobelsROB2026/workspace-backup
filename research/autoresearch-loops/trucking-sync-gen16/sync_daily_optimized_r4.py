"""
Gen 16 optimizations (builds on Gen15):
  O1-O40: inherited from Gen15
  O41+: See notes/autoresearch_plan.md for trial results
"""
import urllib.request
import urllib.parse
import orjson  # O41: ~3-6x faster JSON parsing than stdlib json
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
                return orjson.loads(raw)  # O20: skip .decode(), orjson.loads accepts bytes
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
            return orjson.loads(raw)
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
        c = _make_db_conn()
        # O36: Warm up connection — force pgbouncer to assign a backend
        c.cursor().execute("SELECT 1")
        _conn_result[0] = c
    except Exception as e:
        _conn_result[1] = e

def _connect_db2():
    try:
        c = _make_db_conn()
        # O36: Warm up connection
        c.cursor().execute("SELECT 1")
        _conn2_result[0] = c
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
            meta = orjson.loads(raw_meta)  # O20
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

# O39: Inlined type-specific adapt — avoids hasattr() on every call
_NULL = b"NULL"
def _build_values_fast(rows):
    """Build VALUES bytes from rows — O39 inlined adapt for speed."""
    parts = []
    _a = adapt
    _null = _NULL
    for row in rows:
        vals = []
        for v in row:
            if v is None:
                vals.append(_null)
            elif isinstance(v, int):
                vals.append(str(v).encode())
            elif isinstance(v, str):
                a = _a(v)
                a.encoding = 'utf-8'
                vals.append(a.getquoted())
            else:
                vals.append(_a(v).getquoted())
        parts.append(b"(" + b",".join(vals) + b")")
    return b",".join(parts)

# O35: Pre-split company rows into 2 buffers during fetch for parallel INSERT
# NV rows go to buffer A; fetched rows alternate A/B for even distribution
_comp_rows_a = list(nv_company_rows)  # buffer A starts with NV rows
_comp_rows_b = []  # buffer B
_row_toggle = [0]  # mutable counter for alternation

companies_to_insert = list(nv_company_rows)
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
            # O35: Alternate rows into 2 buffers
            if _row_toggle[0] % 2 == 0:
                _comp_rows_a.append(row)
            else:
                _comp_rows_b.append(row)
            _row_toggle[0] += 1
            upserted_dots.add(dot)
            # O32: Build lead tuple inline during fetch
            lead_data = leads_to_insert.get(dot)
            if lead_data:
                leads_batch.append((str(dot), 'New', lead_data['notes'], lead_data['type']))

_fetch_elapsed = time.perf_counter() - _t_fetch
print(f"[PERF] Phase 2 (batch fetch+parse): {_fetch_elapsed*1000:.0f}ms | {len(batches)} batches")

# O44: INSERT DO NOTHING + separate bulk UPDATE for insurance_provider
# Since ~99.6% of companies already exist, DO NOTHING is cheaper than DO UPDATE
# (Postgres skips the UPDATE path entirely for conflicts with DO NOTHING)
# Then a lightweight UPDATE FROM VALUES only touches insurance_provider
_t_db_combined = time.perf_counter()

if companies_to_insert and leads_batch:
    _t_build = time.perf_counter()

    _COMP_PREFIX = b"INSERT INTO companies (dot_number, legal_name, dba_name, phy_street, phy_city, phy_state, phy_zip, phone, email, add_date, power_units, insurance_provider, cargo_classification, vehicle_oos_rate) VALUES "
    _COMP_SUFFIX_NOTHING = b" ON CONFLICT (dot_number) DO NOTHING"

    # O44: Build insurance update VALUES (only dot + insurer, much smaller)
    _insurer_rows = [(row[0], row[11]) for row in companies_to_insert if row[11] is not None]

    if conn2 and _comp_rows_b:
        # Build company VALUES A/B + leads + insurer update in parallel
        def _build_a():
            return _build_values_fast(_comp_rows_a)
        def _build_b():
            return _build_values_fast(_comp_rows_b)
        def _build_leads():
            return _build_values_fast(leads_batch)
        def _build_insurer():
            if not _insurer_rows:
                return None
            return _build_values_fast(_insurer_rows)
        with ThreadPoolExecutor(max_workers=4) as _bex:
            _fa = _bex.submit(_build_a)
            _fb = _bex.submit(_build_b)
            _fl = _bex.submit(_build_leads)
            _fi = _bex.submit(_build_insurer)
            comp_vals_a = _fa.result()
            comp_vals_b = _fb.result()
            leads_vals = _fl.result()
            insurer_vals = _fi.result()

        comp_sql1 = _COMP_PREFIX + comp_vals_a + _COMP_SUFFIX_NOTHING
        comp_sql2 = _COMP_PREFIX + comp_vals_b + _COMP_SUFFIX_NOTHING
        leads_sql = (
            b"INSERT INTO leads (dot_number, status, agent_notes, lead_type) VALUES " + leads_vals + b" ON CONFLICT (dot_number) DO UPDATE SET status = 'New', lead_type = EXCLUDED.lead_type, updated_at = NOW()"
        )
        insurer_sql = None
        if insurer_vals:
            insurer_sql = (
                b"UPDATE companies SET insurance_provider = v.ins FROM (VALUES " + insurer_vals +
                b") AS v(dot, ins) WHERE companies.dot_number = v.dot"
            )

        # Fire company DO NOTHING INSERTs + insurer UPDATE in parallel
        def _exec_half1():
            cursor.execute(comp_sql1)
        def _exec_half2():
            cur2 = conn2.cursor()
            cur2.execute(comp_sql2)
            # O44: Fire insurer UPDATE on conn2 after company B INSERT
            if insurer_sql:
                cur2.execute(insurer_sql)
            cur2.close()
        with ThreadPoolExecutor(max_workers=2) as _dex:
            _f1 = _dex.submit(_exec_half1)
            _f2 = _dex.submit(_exec_half2)
            _f1.result()
            _f2.result()
        # Fire leads
        cursor.execute(leads_sql)
        _t_build_elapsed = time.perf_counter() - _t_build
        print(f"[PERF] SQL build+exec (O44 DO NOTHING+UPDATE): {_t_build_elapsed*1000:.0f}ms | A={len(_comp_rows_a)} B={len(_comp_rows_b)} ins={len(_insurer_rows)}")
        print(f"UPSERTED {len(companies_to_insert)} companies + {len(leads_batch)} leads via DO NOTHING+UPDATE (O44).")
    else:
        comp_vals = _build_values_fast(companies_to_insert)
        comp_sql = _COMP_PREFIX + comp_vals + _COMP_SUFFIX_NOTHING
        leads_vals = _build_values_fast(leads_batch)
        leads_sql = (
            b"INSERT INTO leads (dot_number, status, agent_notes, lead_type) VALUES " + leads_vals + b" ON CONFLICT (dot_number) DO UPDATE SET status = 'New', lead_type = EXCLUDED.lead_type, updated_at = NOW()"
        )
        cursor.execute(comp_sql)
        # Insurer update
        if _insurer_rows:
            insurer_vals = _build_values_fast(_insurer_rows)
            cursor.execute(
                b"UPDATE companies SET insurance_provider = v.ins FROM (VALUES " + insurer_vals +
                b") AS v(dot, ins) WHERE companies.dot_number = v.dot"
            )
        cursor.execute(leads_sql)
        _t_build_elapsed = time.perf_counter() - _t_build
        print(f"[PERF] SQL build+exec (O44 serial fallback): {_t_build_elapsed*1000:.0f}ms")
        print(f"UPSERTED {len(companies_to_insert)} companies + {len(leads_batch)} leads via serial DO NOTHING+UPDATE.")

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
print(f"GEN16_ELAPSED_SEC {_t_total_elapsed:.3f}")
print(f"GEN16_RPM {rpm:.0f}")
