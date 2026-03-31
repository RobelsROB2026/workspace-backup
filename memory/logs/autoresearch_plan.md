# Autoresearch Plan — 2026-03-31

## Baseline
- 3 runs: 49,754 / 76,503 / 96,539 RPM (median: 76,503)
- Phase 3+4 (DB upsert) is the biggest bottleneck: 1.2-3.5s

## Hypothesis
**Reduce ON CONFLICT UPDATE columns from 5 to 1 (insurance_provider only)**

The current ON CONFLICT clause updates: legal_name, phy_state, phone, power_units, insurance_provider.
Gen11 FINAL_SUMMARY confirmed this is a "real" improvement: fewer WAL writes and reduced index maintenance.
This change was validated in Gen11 round 2 (+5.3%) but was never applied to the main sync_daily_optimized.py.

Secondary: Parallelize leads mogrify with companies mogrify (currently leads_vals is built single-threaded after companies mogrify completes).

## Expected Outcome
- ~5% improvement in Phase 3+4 time due to reduced write amplification
- Small additional gain from parallelized mogrify
