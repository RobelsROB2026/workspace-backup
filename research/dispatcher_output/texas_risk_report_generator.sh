#!/usr/bin/env bash
#
# texas_risk_report_generator.sh
#
# Queries the FMCSA Socrata API for motor carriers with crash history,
# then generates per-carrier Risk Report markdown files.
#
# Dependencies: curl, jq
# API: https://data.transportation.gov/resource/az4b-hbig.json

set -euo pipefail

# ─── Defaults ───────────────────────────────────────────────────────
STATE_CODE="TX"
MIN_FLEET=1
MAX_FLEET=5
LIMIT=20
OUTPUT_DIR="./risk_reports"
APP_TOKEN=""

# ─── Usage ──────────────────────────────────────────────────────────
usage() {
    cat <<'USAGE'
Usage: texas_risk_report_generator.sh [OPTIONS]

Query FMCSA Socrata API for small-fleet motor carriers with recent crash
history and generate per-carrier Risk Report markdown files.

Options:
  --state-code CODE   Two-letter state code (default: TX)
  --min-fleet N       Minimum power units (default: 1)
  --max-fleet N       Maximum power units (default: 5)
  --limit N           Max number of records to return (default: 20)
  --output-dir DIR    Directory for report files (default: ./risk_reports)
  --app-token TOKEN   Socrata app token for higher rate limits (optional)
  -h, --help          Show this help message

Examples:
  # Default: Texas carriers, 1-5 power units, last 24 months crashes
  ./texas_risk_report_generator.sh

  # Florida carriers, up to 10 units, 50 results
  ./texas_risk_report_generator.sh --state-code FL --max-fleet 10 --limit 50

  # With app token for higher rate limits
  ./texas_risk_report_generator.sh --app-token YOUR_TOKEN_HERE
USAGE
    exit 0
}

# ─── Parse arguments ────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --state-code)
            STATE_CODE="$2"; shift 2 ;;
        --min-fleet)
            MIN_FLEET="$2"; shift 2 ;;
        --max-fleet)
            MAX_FLEET="$2"; shift 2 ;;
        --limit)
            LIMIT="$2"; shift 2 ;;
        --output-dir)
            OUTPUT_DIR="$2"; shift 2 ;;
        --app-token)
            APP_TOKEN="$2"; shift 2 ;;
        -h|--help)
            usage ;;
        *)
            echo "Error: Unknown option '$1'" >&2
            echo "Run with --help for usage information." >&2
            exit 1 ;;
    esac
done

# ─── Input validation ──────────────────────────────────────────────
validate() {
    # State code: 2 uppercase letters
    if ! [[ "$STATE_CODE" =~ ^[A-Z]{2}$ ]]; then
        echo "Error: --state-code must be a 2-letter uppercase state code (got '$STATE_CODE')" >&2
        exit 1
    fi
    # Numeric checks
    for pair in "min-fleet:$MIN_FLEET" "max-fleet:$MAX_FLEET" "limit:$LIMIT"; do
        name="${pair%%:*}"
        val="${pair#*:}"
        if ! [[ "$val" =~ ^[0-9]+$ ]] || [[ "$val" -lt 1 ]]; then
            echo "Error: --${name} must be a positive integer (got '$val')" >&2
            exit 1
        fi
    done
    if [[ "$MIN_FLEET" -gt "$MAX_FLEET" ]]; then
        echo "Error: --min-fleet ($MIN_FLEET) cannot exceed --max-fleet ($MAX_FLEET)" >&2
        exit 1
    fi
}

validate

# ─── Dependency check ──────────────────────────────────────────────
for cmd in curl jq; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: '$cmd' is required but not installed." >&2
        exit 1
    fi
done

# ─── Build the SoQL query ──────────────────────────────────────────
WHERE_CLAUSE="phy_state='${STATE_CODE}' AND tot_pwr_units>=${MIN_FLEET} AND tot_pwr_units<=${MAX_FLEET} AND crash_date>=date_sub('now', interval 24 months)"

# URL-encode the $where value (percent-encode spaces, quotes, parens, etc.)
urlencode() {
    local string="$1"
    local length=${#string}
    local encoded=""
    for (( i = 0; i < length; i++ )); do
        local c="${string:i:1}"
        case "$c" in
            [a-zA-Z0-9.~_-]) encoded+="$c" ;;
            *) encoded+=$(printf '%%%02X' "'$c") ;;
        esac
    done
    echo "$encoded"
}

ENCODED_WHERE=$(urlencode "$WHERE_CLAUSE")

API_URL="https://data.transportation.gov/resource/az4b-hbig.json?\$where=${ENCODED_WHERE}&\$limit=${LIMIT}&\$order=crash_date%20DESC"

echo "=============================================="
echo " FMCSA Crash Risk Report Generator"
echo "=============================================="
echo ""
echo "Parameters:"
echo "  State:       $STATE_CODE"
echo "  Fleet size:  $MIN_FLEET - $MAX_FLEET power units"
echo "  Limit:       $LIMIT records"
echo "  Output:      $OUTPUT_DIR"
echo ""
echo "Query: $WHERE_CLAUSE"
echo ""

# ─── Query the API ──────────────────────────────────────────────────
echo "Querying FMCSA Socrata API..."

CURL_ARGS=(-s -f -w "\n%{http_code}")
if [[ -n "$APP_TOKEN" ]]; then
    CURL_ARGS+=(-H "X-App-Token: ${APP_TOKEN}")
fi

RESPONSE=$(curl "${CURL_ARGS[@]}" "$API_URL" 2>&1) || {
    echo "Error: API request failed." >&2
    echo "Response: $RESPONSE" >&2
    echo "" >&2
    echo "Troubleshooting:" >&2
    echo "  - Check your internet connection" >&2
    echo "  - The Socrata API may be temporarily unavailable" >&2
    echo "  - Try reducing --limit or adjusting filters" >&2
    exit 1
}

# Split response body from HTTP status code
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" -lt 200 || "$HTTP_CODE" -ge 300 ]]; then
    echo "Error: API returned HTTP $HTTP_CODE" >&2
    echo "$BODY" | jq . 2>/dev/null || echo "$BODY" >&2
    exit 1
fi

# Validate JSON
if ! echo "$BODY" | jq empty 2>/dev/null; then
    echo "Error: API returned invalid JSON" >&2
    echo "${BODY:0:500}" >&2
    exit 1
fi

RECORD_COUNT=$(echo "$BODY" | jq 'length')
echo "Received $RECORD_COUNT records."

if [[ "$RECORD_COUNT" -eq 0 ]]; then
    echo "No carriers found matching the criteria. Try adjusting filters."
    exit 0
fi

# ─── Group records by DOT number ───────────────────────────────────
# A single carrier may appear multiple times (once per crash event).
# Group them so each report aggregates all crash records.

# Get unique DOT numbers
DOT_NUMBERS=$(echo "$BODY" | jq -r '[.[].dot_number] | unique | .[]' 2>/dev/null)
CARRIER_COUNT=$(echo "$DOT_NUMBERS" | wc -l | tr -d ' ')

echo "Found $CARRIER_COUNT unique carriers."
echo ""

# ─── Create output directory ────────────────────────────────────────
mkdir -p "$OUTPUT_DIR"

# ─── Helper: safe extract ───────────────────────────────────────────
# Extracts a field from JSON, returning "N/A" if missing/null
jq_safe() {
    local json="$1"
    local field="$2"
    local val
    val=$(echo "$json" | jq -r ".[0].${field} // empty" 2>/dev/null)
    if [[ -z "$val" || "$val" == "null" ]]; then
        echo "N/A"
    else
        echo "$val"
    fi
}

# ─── Generate reports ──────────────────────────────────────────────
REPORT_NUM=0

while IFS= read -r DOT; do
    [[ -z "$DOT" ]] && continue
    REPORT_NUM=$((REPORT_NUM + 1))

    # Get all records for this DOT number
    CARRIER_JSON=$(echo "$BODY" | jq "[.[] | select(.dot_number == \"$DOT\")]")
    CRASH_COUNT=$(echo "$CARRIER_JSON" | jq 'length')

    # Extract carrier profile fields (from first record)
    COMPANY_NAME=$(jq_safe "$CARRIER_JSON" "legal_name")
    LEGAL_NAME=$(jq_safe "$CARRIER_JSON" "legal_name")
    DBA_NAME=$(jq_safe "$CARRIER_JSON" "dba_name")
    DOT_NUMBER="$DOT"
    MC_NUMBER=$(jq_safe "$CARRIER_JSON" "mc_mx_ff_numbers")
    FLEET_SIZE=$(jq_safe "$CARRIER_JSON" "tot_pwr_units")
    PHONE=$(jq_safe "$CARRIER_JSON" "telephone")
    EMAIL=$(jq_safe "$CARRIER_JSON" "email_address")
    PHY_STREET=$(jq_safe "$CARRIER_JSON" "phy_street")
    PHY_CITY=$(jq_safe "$CARRIER_JSON" "phy_city")
    PHY_STATE=$(jq_safe "$CARRIER_JSON" "phy_state")
    PHY_ZIP=$(jq_safe "$CARRIER_JSON" "phy_zip")
    PHYSICAL_ADDRESS="${PHY_STREET}, ${PHY_CITY}, ${PHY_STATE} ${PHY_ZIP}"
    INSURANCE_STATUS=$(jq_safe "$CARRIER_JSON" "insurance_status")
    CARRIER_OPERATION=$(jq_safe "$CARRIER_JSON" "carrier_operation")
    TOTAL_DRIVERS=$(jq_safe "$CARRIER_JSON" "tot_drivers")
    OOS_PCT=$(jq_safe "$CARRIER_JSON" "vehicle_oos_rate")
    DRIVER_OOS_PCT=$(jq_safe "$CARRIER_JSON" "driver_oos_rate")

    # Build crash details table
    CRASH_DETAILS=""
    CRASH_DETAILS+="| Date | Location | Fatalities | Injuries | Tow-Aways | Hazmat |"$'\n'
    CRASH_DETAILS+="|------|----------|------------|----------|-----------|--------|"$'\n'

    TOTAL_FATALITIES=0
    TOTAL_INJURIES=0
    TOTAL_TOWAWAYS=0

    while IFS= read -r crash_row; do
        c_date=$(echo "$crash_row" | jq -r '.crash_date // "N/A"' | cut -c1-10)
        c_state=$(echo "$crash_row" | jq -r '.report_state // "N/A"')
        c_fatal=$(echo "$crash_row" | jq -r '.fatalities // "0"')
        c_injur=$(echo "$crash_row" | jq -r '.injuries // "0"')
        c_tow=$(echo "$crash_row" | jq -r '.tow_aways // "0"')
        c_hazmat=$(echo "$crash_row" | jq -r '.hazmat_released // "N"')

        CRASH_DETAILS+="| ${c_date} | ${c_state} | ${c_fatal} | ${c_injur} | ${c_tow} | ${c_hazmat} |"$'\n'

        # Accumulate totals (handle non-numeric gracefully)
        [[ "$c_fatal" =~ ^[0-9]+$ ]] && TOTAL_FATALITIES=$((TOTAL_FATALITIES + c_fatal))
        [[ "$c_injur" =~ ^[0-9]+$ ]] && TOTAL_INJURIES=$((TOTAL_INJURIES + c_injur))
        [[ "$c_tow" =~ ^[0-9]+$ ]] && TOTAL_TOWAWAYS=$((TOTAL_TOWAWAYS + c_tow))
    done < <(echo "$CARRIER_JSON" | jq -c '.[]')

    # ─── Risk scoring ──────────────────────────────────────────────
    RISK_FACTORS=""
    RISK_SCORE=0

    if [[ "$CRASH_COUNT" -ge 3 ]]; then
        RISK_FACTORS+="- **High crash frequency**: ${CRASH_COUNT} crashes in 24 months"$'\n'
        RISK_SCORE=$((RISK_SCORE + 30))
    elif [[ "$CRASH_COUNT" -ge 2 ]]; then
        RISK_FACTORS+="- **Elevated crash frequency**: ${CRASH_COUNT} crashes in 24 months"$'\n'
        RISK_SCORE=$((RISK_SCORE + 20))
    else
        RISK_FACTORS+="- **Crash on record**: ${CRASH_COUNT} crash in 24 months"$'\n'
        RISK_SCORE=$((RISK_SCORE + 10))
    fi

    if [[ "$TOTAL_FATALITIES" -gt 0 ]]; then
        RISK_FACTORS+="- **Fatal crash(es)**: ${TOTAL_FATALITIES} fatalities recorded"$'\n'
        RISK_SCORE=$((RISK_SCORE + 25))
    fi

    if [[ "$TOTAL_INJURIES" -gt 0 ]]; then
        RISK_FACTORS+="- **Injury crash(es)**: ${TOTAL_INJURIES} injuries recorded"$'\n'
        RISK_SCORE=$((RISK_SCORE + 15))
    fi

    if [[ "$FLEET_SIZE" != "N/A" && "$FLEET_SIZE" -le 3 ]] 2>/dev/null; then
        RISK_FACTORS+="- **Very small fleet**: Only ${FLEET_SIZE} power unit(s) -- limited risk distribution"$'\n'
        RISK_SCORE=$((RISK_SCORE + 10))
    fi

    if [[ "$INSURANCE_STATUS" == "N/A" || "$INSURANCE_STATUS" == "" ]]; then
        RISK_FACTORS+="- **Insurance status unknown**: No insurance data on file"$'\n'
        RISK_SCORE=$((RISK_SCORE + 15))
    fi

    # Determine risk level
    if [[ "$RISK_SCORE" -ge 50 ]]; then
        RISK_LEVEL="HIGH"
    elif [[ "$RISK_SCORE" -ge 25 ]]; then
        RISK_LEVEL="MODERATE"
    else
        RISK_LEVEL="LOW"
    fi

    # ─── Sales angle recommendations ───────────────────────────────
    SALES_RECS=""
    SALES_RECS+="### Recommended Approach"$'\n'$'\n'

    if [[ "$RISK_LEVEL" == "HIGH" ]]; then
        SALES_RECS+="This carrier has a **high-risk profile** and likely faces:"$'\n'
        SALES_RECS+="- Premium increases or non-renewal from current insurer"$'\n'
        SALES_RECS+="- Difficulty finding standard-market coverage"$'\n'
        SALES_RECS+="- Potential CSA intervention thresholds"$'\n'$'\n'
        SALES_RECS+="**Positioning:** Lead with loss-control and safety program value. Emphasize your ability to place hard-to-insure risks. Offer telematics/dashcam program to demonstrate commitment to improvement."$'\n'
    elif [[ "$RISK_LEVEL" == "MODERATE" ]]; then
        SALES_RECS+="This carrier has a **moderate-risk profile** and may be experiencing:"$'\n'
        SALES_RECS+="- Rate increases at upcoming renewal"$'\n'
        SALES_RECS+="- Reduced carrier appetite"$'\n'$'\n'
        SALES_RECS+="**Positioning:** Offer competitive quotes with safety-improvement incentives. Highlight fleet management resources and claims advocacy. Time outreach 60-90 days before likely renewal."$'\n'
    else
        SALES_RECS+="This carrier has a **lower-risk profile** but crash history creates an opening:"$'\n'
        SALES_RECS+="- Current insurer may still increase rates based on the incident"$'\n'$'\n'
        SALES_RECS+="**Positioning:** Lead with competitive pricing and bundled coverage options. Emphasize proactive risk management to keep rates favorable long-term."$'\n'
    fi

    SALES_RECS+=$'\n'"### Talking Points"$'\n'$'\n'
    SALES_RECS+="1. Reference their recent crash history as a reason they may be seeing rate pressure"$'\n'
    SALES_RECS+="2. Offer a no-obligation coverage review and quote comparison"$'\n'
    SALES_RECS+="3. Highlight safety and compliance resources included with your program"$'\n'
    SALES_RECS+="4. If fleet size is small (${FLEET_SIZE} units), emphasize personalized service vs. large-agency indifference"$'\n'

    # ─── Write the report ──────────────────────────────────────────
    SAFE_NAME=$(echo "${COMPANY_NAME}" | tr -cs 'a-zA-Z0-9' '_' | sed 's/_$//' | head -c 60)
    FILENAME="${OUTPUT_DIR}/risk_report_DOT${DOT_NUMBER}_${SAFE_NAME}.md"

    REPORT_DATE=$(date '+%Y-%m-%d %H:%M:%S')

    cat > "$FILENAME" <<REPORT
# Risk Report: ${COMPANY_NAME}

**Generated:** ${REPORT_DATE}
**Risk Level:** ${RISK_LEVEL} (Score: ${RISK_SCORE}/100)

---

## Carrier Profile

| Field | Value |
|-------|-------|
| **Company / Legal Name** | ${LEGAL_NAME} |
| **DBA Name** | ${DBA_NAME} |
| **DOT Number** | ${DOT_NUMBER} |
| **MC/MX/FF Number** | ${MC_NUMBER} |
| **Operation Type** | ${CARRIER_OPERATION} |
| **Fleet Size (Power Units)** | ${FLEET_SIZE} |
| **Total Drivers** | ${TOTAL_DRIVERS} |
| **Phone** | ${PHONE} |
| **Email** | ${EMAIL} |
| **Physical Address** | ${PHYSICAL_ADDRESS} |
| **Insurance Status** | ${INSURANCE_STATUS} |
| **Vehicle OOS Rate** | ${OOS_PCT} |
| **Driver OOS Rate** | ${DRIVER_OOS_PCT} |

---

## Risk Factors

${RISK_FACTORS}

---

## Crash History Summary

- **Total Crashes (24 months):** ${CRASH_COUNT}
- **Total Fatalities:** ${TOTAL_FATALITIES}
- **Total Injuries:** ${TOTAL_INJURIES}
- **Total Tow-Aways:** ${TOTAL_TOWAWAYS}

### Crash Details

${CRASH_DETAILS}

---

## Sales Angle

${SALES_RECS}

---

*Report generated by texas_risk_report_generator.sh*
*Data source: FMCSA / data.transportation.gov*
REPORT

    echo "  [$REPORT_NUM/$CARRIER_COUNT] Generated: $(basename "$FILENAME")  (${RISK_LEVEL} risk, ${CRASH_COUNT} crashes)"

done <<< "$DOT_NUMBERS"

echo ""
echo "=============================================="
echo " Complete: $CARRIER_COUNT reports saved to $OUTPUT_DIR"
echo "=============================================="
echo ""
ls -la "$OUTPUT_DIR"/*.md 2>/dev/null | tail -20
