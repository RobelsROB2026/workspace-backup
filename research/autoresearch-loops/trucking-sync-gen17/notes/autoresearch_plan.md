# Gen16 Autoresearch Plan — 2026-04-02

## Starting Point
- **Gen15 winner**: ~921ms DB upsert, ~230k RPM (best single run: 893ms upsert)
- Key inherited optimizations: O35 (pre-split buffers), O36 (warmup), O39 (inlined adapt), O40 (overlap leads build)
- Network latency is 40-65% of total time
- Data volume: ~10,558 records (5,279 companies + 5,279 leads)

## Available Tools
- `orjson` — fast JSON parsing (available)
- `asyncio` + stdlib `asyncio.open_connection` — async I/O without aiohttp
- No `psycopg3` or `aiohttp` available
- psycopg2 with manual SQL building (current approach is already fastest known)

## Hypotheses

### Round 1: orjson for JSON parsing (O41)
- Replace `json.loads(raw)` with `orjson.loads(raw)` in all fetch paths
- orjson is ~3-6x faster than stdlib json for parsing
- Phase 1 + Phase 2 both parse JSON responses; could save 10-50ms total
- Low risk, high confidence

### Round 2: asyncio Phase 2 batch fetching (O42)
- Replace ThreadPoolExecutor Phase 2 with asyncio + ssl for batch fetches
- Eliminates thread creation/scheduling overhead for 16+ concurrent fetches
- Use asyncio.open_connection with SSL for HTTP/1.1 persistent connections
- Medium risk — need to handle HTTP manually

### Round 3: Memoryview + pre-sized buffer for VALUES build (O43)
- Pre-calculate approximate VALUES size and allocate buffer
- Use memoryview slicing to reduce copies during concatenation
- Alternative: try `io.BytesIO` writer pattern instead of list+join
- Medium risk — Gen15 showed bytearray was slower, but BytesIO may differ

### Round 4: Reduce ON CONFLICT overhead — skip conflict check for leads (O44)
- Most leads are new each day; conflict is rare
- Try: DELETE matching leads first, then plain INSERT (no ON CONFLICT)
- DELETE + INSERT can be faster than INSERT ON CONFLICT when conflicts are rare
- Medium risk — need to verify data integrity

### Round 5: Combined single INSERT for companies (O45)
- Gen15 splits into A/B buffers for parallel INSERT on 2 connections
- The split + coordination overhead may exceed the parallelism benefit for ~5k rows
- Try: single large INSERT on one connection
- Low risk — easy to measure

### Round 6: Batch-build all SQL as one bytes blob (O46)
- Currently: build company A vals, company B vals, leads vals separately
- Try: build all 3 VALUES blobs in one pass over the data
- Reduces Python loop overhead and list allocation
- Low risk
