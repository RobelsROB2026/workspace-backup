# Autoresearch Loop — Benchmark Report

**Date**: 2026-03-21  
**Script**: `sync_daily_optimized.py`  
**Duration**: 10.1 minutes | 20 iterations  

## Summary

| Metric | Value |
|--------|-------|
| Baseline RPM | 124,973 |
| Final RPM | 166,557 |
| Total Improvement | +33.3% |
| Hypotheses Tested | 20 |
| Adopted | 3 |

## Results by Iteration

| # | Hypothesis | RPM | Δ% | Adopted |
|---|-----------|-----|-----|---------|
| baseline | baseline | 124,973 | — | ✅ |
| gen1 | split_cte | 125,633 | +0.5% | ❌ |
| gen2 | reduce_update_cols | 143,100 | +14.5% | ✅ |
| gen3 | leads_update_type_only | 123,962 | -13.4% | ❌ |
| gen4 | skip_unchanged_leads | 78,051 | -45.5% | ❌ |
| gen5 | workers_16 | 159,289 | +11.3% | ✅ |
| gen6 | httpx_phase2 | 26,103 | -83.6% | ❌ |
| gen7 | mogrify_parallel | 166,557 | +4.6% | ✅ |
| gen8 | workers_20 | 156,398 | -6.1% | ❌ |
| gen9 | batch_400 | 143,138 | -14.1% | ❌ |
| gen10 | batch_600 | 156,582 | -6.0% | ❌ |
| gen11 | httpx_phase1 | 34,608 | -79.2% | ❌ |
| gen12 | leads_do_nothing | 131,634 | -21.0% | ❌ |
| gen13 | gzip_only | 158,073 | -5.1% | ❌ |
| gen14 | reduce_http_timeout | 152,626 | -8.4% | ❌ |
| gen15 | parallel_db_writes | SKIP | — | ⏭ |
| gen16 | workers_8 | SKIP | — | ⏭ |
| gen17 | prefilter_batch_dots | 120,123 | -27.9% | ❌ |
| gen18 | pipeline_phase2 | 120,662 | -27.6% | ❌ |
| gen19 | batch_400_workers_16 | 129,407 | -22.3% | ❌ |
| gen20 | combined_best | SKIP | — | ⏭ |

## Adopted Hypotheses

- **reduce_update_cols**: Reduce ON CONFLICT UPDATE cols (drop cargo_class + oos_rate) (+14.5%)
- **workers_16**: MAX_BATCH_WORKERS=16 (more Phase 2 threads) (+11.3%)
- **mogrify_parallel**: Parallel mogrify across 2 threads (CPU-bound SQL building) (+4.6%)
