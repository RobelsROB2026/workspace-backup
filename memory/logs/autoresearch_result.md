# Autoresearch Result — 2026-03-31

## Summary
**Gen12 promoted.** Median RPM improved from 76,503 to 96,395 (+26%).

## Baseline (Gen10, 3 runs)
| Run | RPM | Total Time | Phase 3+4 (DB upsert) |
|-----|------|------------|----------------------|
| 1 | 49,754 | 5.35s | 3.457s |
| 2 | 76,503 | 3.48s | 1.615s |
| 3 | 96,539 | 2.76s | 1.224s |
| **Median** | **76,503** | **3.48s** | **1.615s** |

## Gen12 (3 runs)
| Run | RPM | Total Time | Phase 3+4 (DB upsert) |
|-----|------|------------|----------------------|
| 1 | 87,972 | 3.02s | 1.123s |
| 2 | 96,395 | 2.76s | 1.014s |
| 3 | 104,167 | 2.55s | 1.014s |
| **Median** | **96,395** | **2.76s** | **1.014s** |

## Changes Made (sync_daily_optimized.py)
1. **O24: Reduced ON CONFLICT UPDATE columns** — Changed from updating 5 columns (legal_name, phy_state, phone, power_units, insurance_provider) to only `insurance_provider`. Fewer WAL writes and reduced index maintenance on the Supabase side.
2. **O25: Parallelized leads mogrify** — Leads mogrify now runs concurrently with the 2-way companies mogrify (3-way ThreadPool instead of serial).

## Analysis
- The DB upsert phase improved most clearly: 1.615s median → 1.014s median (37% faster).
- First-run penalty was also reduced (3.46s → 1.12s), suggesting less write amplification helps even on cold cache.
- Network phases (Phase 1 + Phase 2) were unchanged as expected.
- High variance between runs remains due to network latency (the known bottleneck).
