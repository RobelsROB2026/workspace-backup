# Autoresearch Loop — Benchmark Report

**Date**: 2026-03-21  
**Script**: `sync_daily_optimized.py`  
**Duration**: 8.3 minutes | 20 iterations  

## Summary

| Metric | Value |
|--------|-------|
| Baseline RPM | 83,771 |
| Final RPM | 135,462 |
| Total Improvement | +61.7% |
| Hypotheses Tested | 20 |
| Adopted | 3 |

## Results by Iteration

| # | Hypothesis | RPM | Δ% | Adopted |
|---|-----------|-----|-----|---------|
| baseline | baseline | 83,771 | — | ✅ |
| gen1 | split_cte | SKIP | — | ⏭ |
| gen2 | reduce_update_cols | SKIP | — | ⏭ |
| gen3 | leads_update_type_only | 112,603 | +34.4% | ✅ |
| gen4 | skip_unchanged_leads | 59,530 | -47.1% | ❌ |
| gen5 | workers_16 | SKIP | — | ⏭ |
| gen6 | httpx_phase2 | 21,111 | -81.2% | ❌ |
| gen7 | mogrify_parallel | SKIP | — | ⏭ |
| gen8 | workers_20 | 123,166 | +9.4% | ✅ |
| gen9 | batch_400 | 116,036 | -5.8% | ❌ |
| gen10 | batch_600 | 118,915 | -3.5% | ❌ |
| gen11 | httpx_phase1 | 21,127 | -82.8% | ❌ |
| gen12 | leads_do_nothing | SKIP | — | ⏭ |
| gen13 | gzip_only | 135,462 | +10.0% | ✅ |
| gen14 | reduce_http_timeout | 90,329 | -33.3% | ❌ |
| gen15 | parallel_db_writes | SKIP | — | ⏭ |
| gen16 | workers_8 | SKIP | — | ⏭ |
| gen17 | prefilter_batch_dots | 106,259 | -21.6% | ❌ |
| gen18 | pipeline_phase2 | 112,137 | -17.2% | ❌ |
| gen19 | batch_400_workers_16 | 125,846 | -7.1% | ❌ |
| gen20 | combined_best | SKIP | — | ⏭ |

## Adopted Hypotheses

- **leads_update_type_only**: Minimal leads UPDATE (only lead_type + updated_at) (+34.4%)
- **workers_20**: MAX_BATCH_WORKERS=20 (+9.4%)
- **gzip_only**: Accept-Encoding: gzip only (avoid deflate overhead) (+10.0%)
