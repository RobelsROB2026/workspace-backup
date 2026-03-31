#!/usr/bin/env bash
#
# texas_small_fleet_crash_risk.sh
# Queries FMCSA Socrata API for Texas motor carriers (1-5 power units)
# with crash history, then generates a markdown risk report.
#

set -euo pipefail

API_BASE="https://data.transportation.gov/resource/az4b-hbig.json"
OUTPUT_DIR="$HOME/research/dispatcher_output"
REPORT_FILE="$OUTPUT_DIR/texas_small_fleet_crash_risk_report.md"
TEMP_FILE=$(mktemp)
MAX_RETRIES=3
RETRY_DELAY=5
PAGE_LIMIT=50

cleanup() { rm -f "$TEMP_FILE"; }
trap cleanup EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2; }

# --- API query with retry logic ---
fetch_carriers() {
    local attempt=0
    local http_code

    while (( attempt < MAX_RETRIES )); do
        attempt=$((attempt + 1))
        log "API request attempt $attempt/$MAX_RETRIES ..."

        http_code=$(curl -s -w '%{http_code}' -o "$TEMP_FILE" \
            --get "$API_BASE" \
            --data-urlencode "\$where=phy_state='TX' AND (tot_pwr_units>=1 AND tot_pwr_units<=5) AND has_crash_flag='Y'" \
            --data-urlencode "\$limit=$PAGE_LIMIT" \
            --connect-timeout 15 \
            --max-time 30 \
            2>/dev/null) || http_code="000"

        # Rate limiting detection (Socrata returns 429)
        if [[ "$http_code" == "429" ]]; then
            log "RATE LIMITED (429). Waiting ${RETRY_DELAY}s before retry ..."
            sleep "$RETRY_DELAY"
            RETRY_DELAY=$((RETRY_DELAY * 2))
            continue
        fi

        # Server errors
        if [[ "$http_code" =~ ^5[0-9]{2}$ ]]; then
            log "Server error ($http_code). Retrying in ${RETRY_DELAY}s ..."
            sleep "$RETRY_DELAY"
            continue
        fi

        # Connection failure
        if [[ "$http_code" == "000" ]]; then
            log "Connection failed. Retrying in ${RETRY_DELAY}s ..."
            sleep "$RETRY_DELAY"
            continue
        fi

        # Client error (not rate limit)
        if [[ "$http_code" =~ ^4[0-9]{2}$ ]]; then
            log "Client error ($http_code). Response:"
            cat "$TEMP_FILE" >&2
            return 1
        fi

        # Success
        if [[ "$http_code" == "200" ]]; then
            # Validate JSON structure
            if ! python3 -c "import json,sys; d=json.load(sys.stdin); assert isinstance(d,list)" < "$TEMP_FILE" 2>/dev/null; then
                log "Malformed JSON response. Retrying ..."
                sleep "$RETRY_DELAY"
                continue
            fi
            local count
            count=$(python3 -c "import json,sys; print(len(json.load(sys.stdin)))" < "$TEMP_FILE")
            log "Success: received $count carrier records."
            return 0
        fi

        log "Unexpected HTTP $http_code. Retrying ..."
        sleep "$RETRY_DELAY"
    done

    log "ERROR: All $MAX_RETRIES attempts failed."
    return 1
}

# --- Generate markdown report from JSON response ---
generate_report() {
    python3 - "$TEMP_FILE" "$REPORT_FILE" << 'PYEOF'
import json, sys, os
from datetime import datetime, timedelta

input_path = sys.argv[1]
output_path = sys.argv[2]

with open(input_path) as f:
    carriers = json.load(f)

if not carriers:
    print("No carriers found matching criteria.", file=sys.stderr)
    sys.exit(1)

now = datetime.now()
cutoff = now - timedelta(days=730)  # ~24 months

def safe(rec, key, default="N/A"):
    v = rec.get(key)
    if v is None or str(v).strip() == "":
        return default
    return str(v).strip()

def risk_level(crash_count, pwr_units):
    try:
        ratio = int(crash_count) / max(int(pwr_units), 1)
    except (ValueError, TypeError):
        return "UNKNOWN"
    if ratio >= 1.0:
        return "CRITICAL"
    elif ratio >= 0.5:
        return "HIGH"
    elif ratio >= 0.25:
        return "MODERATE"
    return "LOW"

def sales_angle(risk, insurance_status, pwr_units):
    angles = []
    if risk in ("CRITICAL", "HIGH"):
        angles.append("Crash history creates urgency — carrier likely facing premium increases or non-renewal risk")
        angles.append("Position safety/compliance consulting as ROI against future losses")
    if insurance_status and "ACTIVE" not in insurance_status.upper():
        angles.append("Insurance gap detected — immediate compliance need; offer bundled policy solutions")
    try:
        if int(pwr_units) <= 3:
            angles.append("Micro-fleet: owner-operator likely wears all hats — emphasize turnkey, low-admin solutions")
    except (ValueError, TypeError):
        pass
    angles.append("Small fleet segment is underserved by major brokers — relationship-first approach recommended")
    return angles

lines = []
lines.append("# Texas Small Fleet Crash Risk Report")
lines.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"**Query:** TX carriers, 1-5 power units, crash flag = Y")
lines.append(f"**Records returned:** {len(carriers)}")
lines.append("")
lines.append("---")
lines.append("")

# Summary table
lines.append("## Summary Table")
lines.append("")
lines.append("| # | Company | DOT# | MC# | Fleet Size | Crashes | Risk |")
lines.append("|---|---------|------|-----|------------|---------|------|")

for i, c in enumerate(carriers, 1):
    name = safe(c, "legal_name", safe(c, "dba_name", "Unknown"))
    dot = safe(c, "dot_number", safe(c, "usdot_number"))
    mc = safe(c, "mc_number", safe(c, "docket_number", "—"))
    pwr = safe(c, "tot_pwr_units", "?")
    crashes = safe(c, "crash_total", safe(c, "crash_count", "0"))
    risk = risk_level(crashes, pwr)
    lines.append(f"| {i} | {name} | {dot} | {mc} | {pwr} | {crashes} | {risk} |")

lines.append("")
lines.append("---")
lines.append("")

# Individual carrier reports
lines.append("## Individual Carrier Reports")
lines.append("")

for i, c in enumerate(carriers, 1):
    name = safe(c, "legal_name", safe(c, "dba_name", "Unknown"))
    dot = safe(c, "dot_number", safe(c, "usdot_number"))
    mc = safe(c, "mc_number", safe(c, "docket_number", "—"))
    pwr = safe(c, "tot_pwr_units", "?")
    drivers = safe(c, "tot_drivers", "?")
    crashes = safe(c, "crash_total", safe(c, "crash_count", "0"))
    fatal = safe(c, "fatal_crash_total", safe(c, "fatal_crashes", "0"))
    injury = safe(c, "injury_crash_total", safe(c, "injury_crashes", "0"))
    tow = safe(c, "towaway_crash_total", safe(c, "tow_crashes", "0"))
    phy_street = safe(c, "phy_street")
    phy_city = safe(c, "phy_city")
    phy_zip = safe(c, "phy_zip")
    phone = safe(c, "phone")
    op_status = safe(c, "op_status", safe(c, "carrier_operation"))
    insurance = safe(c, "insurance_status", safe(c, "bipd_insurance_status", "Unknown"))
    veh_insp = safe(c, "vehicle_inspections", safe(c, "veh_insp_total", "—"))
    drv_insp = safe(c, "driver_inspections", safe(c, "drv_insp_total", "—"))
    veh_oos = safe(c, "vehicle_oos_inspections", safe(c, "veh_oos_total", "—"))
    drv_oos = safe(c, "driver_oos_inspections", safe(c, "drv_oos_total", "—"))
    risk = risk_level(crashes, pwr)

    lines.append(f"### {i}. {name}")
    lines.append("")
    lines.append("#### Carrier Details")
    lines.append(f"- **DOT#:** {dot}")
    lines.append(f"- **MC#:** {mc}")
    lines.append(f"- **Address:** {phy_street}, {phy_city}, TX {phy_zip}")
    lines.append(f"- **Phone:** {phone}")
    lines.append(f"- **Operating Status:** {op_status}")
    lines.append(f"- **Insurance Status:** {insurance}")
    lines.append(f"- **Fleet Size:** {pwr} power units, {drivers} drivers")
    lines.append("")

    lines.append("#### Crash History (24-Month Window)")
    lines.append(f"- **Total Crashes:** {crashes}")
    lines.append(f"- **Fatal Crashes:** {fatal}")
    lines.append(f"- **Injury Crashes:** {injury}")
    lines.append(f"- **Towaway Crashes:** {tow}")
    lines.append("")

    # Crash timeline from available date fields
    crash_dates = []
    for key in sorted(c.keys()):
        if "crash" in key.lower() and "date" in key.lower():
            val = safe(c, key, None)
            if val:
                crash_dates.append(f"  - {key}: {val}")
    if crash_dates:
        lines.append("**Crash Date Fields:**")
        lines.extend(crash_dates)
        lines.append("")

    lines.append("#### Inspection & Violation Summary")
    lines.append(f"- **Vehicle Inspections:** {veh_insp} (OOS: {veh_oos})")
    lines.append(f"- **Driver Inspections:** {drv_insp} (OOS: {drv_oos})")
    lines.append("")

    lines.append(f"#### Risk Assessment: **{risk}**")
    lines.append("")
    factors = []
    try:
        if int(crashes) > 0:
            factors.append(f"Carrier has {crashes} crash(es) on record with only {pwr} power unit(s)")
    except ValueError:
        pass
    try:
        if int(fatal) > 0:
            factors.append(f"FATAL crash history — highest severity indicator")
    except ValueError:
        pass
    if insurance.upper() not in ("ACTIVE", "N/A", "UNKNOWN"):
        factors.append(f"Insurance status is '{insurance}' — potential compliance gap")
    try:
        if veh_oos not in ("—", "0", "N/A") and int(veh_oos) > 0:
            factors.append(f"Vehicle out-of-service events ({veh_oos}) indicate maintenance concerns")
    except ValueError:
        pass
    try:
        if drv_oos not in ("—", "0", "N/A") and int(drv_oos) > 0:
            factors.append(f"Driver out-of-service events ({drv_oos}) indicate compliance issues")
    except ValueError:
        pass
    if not factors:
        factors.append("Standard risk profile for small fleet with crash history")
    for f in factors:
        lines.append(f"- {f}")
    lines.append("")

    lines.append("#### Sales Angle & Recommendations")
    angles = sales_angle(risk, insurance, pwr)
    for a in angles:
        lines.append(f"- {a}")
    lines.append("")
    lines.append("---")
    lines.append("")

# Footer
lines.append("## Methodology")
lines.append("- **Source:** FMCSA Socrata API (`az4b-hbig`)")
lines.append("- **Filters:** `phy_state='TX'`, `tot_pwr_units` 1-5, `has_crash_flag='Y'`")
lines.append(f"- **Report window:** 24 months prior to {now.strftime('%Y-%m-%d')}")
lines.append("- **Risk levels:** CRITICAL (>=1 crash/unit), HIGH (>=0.5), MODERATE (>=0.25), LOW (<0.25)")
lines.append("")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as out:
    out.write("\n".join(lines))

print(f"Report written to {output_path}", file=sys.stderr)
PYEOF
}

# --- Main ---
log "Starting Texas small fleet crash risk query ..."
mkdir -p "$OUTPUT_DIR"

if fetch_carriers; then
    generate_report
    log "Done. Report saved to $REPORT_FILE"
else
    log "FAILED: Could not retrieve carrier data from FMCSA API."
    exit 1
fi
