#!/usr/bin/env bash
#
# fmcsa_insurance_gap_filter.sh
#
# Pulls FMCSA census data from the Socrata API at
# data.transportation.gov/resource/az4b-hbig.json, filters for carriers
# with insurance MCS-150 filing gaps, and produces a formatted report.
#
# Dependencies: curl, python3

set -euo pipefail

readonly BASE_URL="https://data.transportation.gov/resource/az4b-hbig.json"
readonly SCRIPT_NAME="$(basename "$0")"
readonly SOCRATA_PAGE_LIMIT=1000
readonly CURL_TIMEOUT=30
readonly CURL_RETRIES=3

# ── Logging ──────────────────────────────────────────────────────────────────
log_info()  { echo "[INFO]  $(date '+%Y-%m-%d %H:%M:%S') $*" >&2; }
log_warn()  { echo "[WARN]  $(date '+%Y-%m-%d %H:%M:%S') $*" >&2; }
log_error() { echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2; }
die() { log_error "$@"; exit 1; }

# ── Help ─────────────────────────────────────────────────────────────────────
show_help() {
    cat <<EOF
$SCRIPT_NAME — FMCSA Insurance Gap Filter

Pull FMCSA census data from the Socrata Open Data API and identify motor
carriers whose MCS-150 insurance filing dates are older than a configurable
threshold, indicating potential insurance coverage gaps.

USAGE
    $SCRIPT_NAME [OPTIONS]

OPTIONS
    --api-key KEY        Socrata application token (raises throttle limits).
                         Falls back to \$SOCRATA_APP_TOKEN env var.
    --state CODE         Filter by carrier physical state (2-letter, e.g. TX).
    --days-gap DAYS      Min days since last filing to flag a gap (default: 90).
    --output-format FMT  Output format: "table" (default) or "csv".
    -h, --help           Show this help and exit.

REPORT COLUMNS
    Carrier Name, DOT Number, MC Number, State, Last Insurance Filing Date,
    Days Since Filing, Fleet Size, Phone, Email

EXAMPLES
    # All carriers with gaps > 90 days, table output
    ./$SCRIPT_NAME --api-key \$SOCRATA_APP_TOKEN

    # Texas carriers, 180-day gap threshold, CSV output
    ./$SCRIPT_NAME --api-key abc123 --state TX --days-gap 180 --output-format csv

    # Using environment variable for API key
    export SOCRATA_APP_TOKEN=abc123
    ./$SCRIPT_NAME --state CA --output-format csv > ca_gaps.csv
EOF
}

# ── Argument parsing ─────────────────────────────────────────────────────────
API_KEY=""
STATE=""
DAYS_GAP=90
OUTPUT_FORMAT="table"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --api-key)
            [[ -n "${2:-}" ]] || die "missing value for $1"
            API_KEY="$2"; shift 2 ;;
        --state)
            [[ -n "${2:-}" ]] || die "missing value for $1"
            STATE="$2"; shift 2 ;;
        --days-gap)
            [[ -n "${2:-}" ]] || die "missing value for $1"
            DAYS_GAP="$2"; shift 2 ;;
        --output-format)
            [[ -n "${2:-}" ]] || die "missing value for $1"
            OUTPUT_FORMAT="$2"; shift 2 ;;
        -h|--help)
            show_help; exit 0 ;;
        --)
            shift; break ;;
        -*)
            die "unknown option: $1 (try --help)" ;;
        *)
            die "unexpected argument: $1 (try --help)" ;;
    esac
done

# ── Validate inputs ──────────────────────────────────────────────────────────
[[ "$DAYS_GAP" =~ ^[0-9]+$ ]] || die "--days-gap must be a positive integer, got: $DAYS_GAP"

if [[ -n "$STATE" ]]; then
    STATE="${STATE^^}"
    [[ "$STATE" =~ ^[A-Z]{2}$ ]] || die "--state must be a 2-letter state code, got: $STATE"
fi

case "$OUTPUT_FORMAT" in
    table|csv) ;;
    *) die "--output-format must be 'table' or 'csv', got: $OUTPUT_FORMAT" ;;
esac

API_KEY="${API_KEY:-${SOCRATA_APP_TOKEN:-}}"

for cmd in curl python3; do
    command -v "$cmd" >/dev/null 2>&1 || die "required command not found: $cmd"
done

# ── Build SoQL query ─────────────────────────────────────────────────────────
WHERE_CLAUSE="bipd_insurance_required='Y'"
if [[ -n "$STATE" ]]; then
    WHERE_CLAUSE="${WHERE_CLAUSE} AND phy_state='${STATE}'"
fi

url_encode() {
    python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$1"
}

# ── Fetch data with pagination ───────────────────────────────────────────────
TMPDIR_WORK="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_WORK"' EXIT

CURL_HEADERS=(-H "Accept: application/json")
if [[ -n "$API_KEY" ]]; then
    CURL_HEADERS+=(-H "X-App-Token: ${API_KEY}")
fi

log_info "Starting FMCSA census data fetch"
log_info "Filter: $WHERE_CLAUSE"
log_info "Days gap threshold: ${DAYS_GAP}"
log_info "Output format: ${OUTPUT_FORMAT}"

OFFSET=0
PAGE=0
TOTAL_FETCHED=0

while true; do
    PAGE=$((PAGE + 1))
    ENCODED_WHERE="$(url_encode "$WHERE_CLAUSE")"
    URL="${BASE_URL}?\$where=${ENCODED_WHERE}&\$limit=${SOCRATA_PAGE_LIMIT}&\$offset=${OFFSET}&\$order=dot_number"

    PAGE_FILE="${TMPDIR_WORK}/page_${PAGE}.json"

    log_info "Fetching page ${PAGE} (offset=${OFFSET})..."

    HTTP_CODE=$(curl -s -w "%{http_code}" -o "$PAGE_FILE" \
        --retry "$CURL_RETRIES" \
        --retry-delay 2 \
        --max-time "$CURL_TIMEOUT" \
        --connect-timeout 10 \
        "${CURL_HEADERS[@]}" \
        "$URL" 2>/dev/null) || die "curl request failed — check network connectivity"

    if [[ "$HTTP_CODE" -lt 200 || "$HTTP_CODE" -ge 300 ]]; then
        log_error "API returned HTTP ${HTTP_CODE}"
        if [[ "$HTTP_CODE" -eq 403 ]]; then
            log_error "Access denied. Provide a valid --api-key or set SOCRATA_APP_TOKEN."
        elif [[ "$HTTP_CODE" -eq 429 ]]; then
            log_error "Rate limited. Provide an --api-key for higher throttle limits."
        fi
        log_error "Response: $(head -c 500 "$PAGE_FILE" 2>/dev/null)"
        die "API request failed with HTTP ${HTTP_CODE}"
    fi

    ROW_COUNT=$(python3 -c "
import json, sys
try:
    data = json.load(open(sys.argv[1]))
    if not isinstance(data, list):
        print(-1)
    else:
        print(len(data))
except Exception:
    print(-1)
" "$PAGE_FILE")

    [[ "$ROW_COUNT" -ne -1 ]] || die "unexpected API response (expected JSON array)"

    TOTAL_FETCHED=$((TOTAL_FETCHED + ROW_COUNT))
    log_info "Page ${PAGE}: ${ROW_COUNT} records (total: ${TOTAL_FETCHED})"

    if [[ "$ROW_COUNT" -lt "$SOCRATA_PAGE_LIMIT" ]]; then
        break
    fi

    OFFSET=$((OFFSET + SOCRATA_PAGE_LIMIT))
done

if [[ "$TOTAL_FETCHED" -eq 0 ]]; then
    log_warn "No carrier records matched the query filters."
    exit 0
fi

log_info "Analyzing insurance filing gaps..."

# ── Process and report ───────────────────────────────────────────────────────
python3 - "$TMPDIR_WORK" "$DAYS_GAP" "$OUTPUT_FORMAT" <<'PYEOF'
import csv
import json
import glob
import sys
import os
import io
from datetime import datetime, timezone

work_dir = sys.argv[1]
min_gap_days = int(sys.argv[2])
output_format = sys.argv[3]

today = datetime.now(timezone.utc).date()

# Merge all page files
records = []
for page_file in sorted(glob.glob(os.path.join(work_dir, "page_*.json"))):
    with open(page_file) as f:
        records.extend(json.load(f))

def parse_date(val):
    """Parse Socrata date fields (ISO 8601 variants)."""
    if not val:
        return None
    val = val.split("+")[0].split("Z")[0]
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None

columns = [
    "carrier_name", "dot_number", "mc_number", "state",
    "last_insurance_filing", "days_since_filing", "fleet_size",
    "phone", "email"
]

flagged = []
for rec in records:
    # Check multiple possible date fields for the insurance/MCS-150 filing
    ins_date_raw = (
        rec.get("mcs_150_form_date")
        or rec.get("mcs150_date")
        or rec.get("bipd_insurance_on_file_date")
        or ""
    )
    ins_date = parse_date(ins_date_raw)

    if ins_date is None:
        # No filing date at all — flag as missing
        gap_days = None
        status_note = "NO DATE ON FILE"
    else:
        gap_days = (today - ins_date).days
        if gap_days < min_gap_days:
            continue  # Within threshold, skip
        status_note = ""

    # Carrier name: prefer legal_name, fall back to dba_name
    name = (rec.get("legal_name") or rec.get("dba_name") or "").strip()

    # Fleet size: sum of power units and drivers, or individual fields
    power_units = rec.get("nbr_power_unit", rec.get("total_power_units", ""))
    drivers = rec.get("driver_total", rec.get("total_drivers", ""))
    if power_units and drivers:
        fleet_size = f"{power_units} units / {drivers} drivers"
    elif power_units:
        fleet_size = f"{power_units} units"
    elif drivers:
        fleet_size = f"{drivers} drivers"
    else:
        fleet_size = ""

    flagged.append({
        "carrier_name": name,
        "dot_number": rec.get("dot_number", ""),
        "mc_number": rec.get("mc_mx_ff_number", rec.get("docket_number", "")),
        "state": rec.get("phy_state", ""),
        "last_insurance_filing": str(ins_date) if ins_date else "N/A",
        "days_since_filing": str(gap_days) if gap_days is not None else "N/A",
        "fleet_size": fleet_size,
        "phone": rec.get("telephone", rec.get("phone", "")),
        "email": rec.get("email_address", rec.get("email", "")),
    })

# Sort: N/A (missing) first, then largest gap descending
def sort_key(r):
    d = r["days_since_filing"]
    if d == "N/A":
        return (0, 0)
    return (1, -int(d))

flagged.sort(key=sort_key)

total = len(flagged)

if total == 0:
    print("No carriers found with insurance filing gaps exceeding the threshold.", file=sys.stderr)
    sys.exit(0)

print(f"[INFO]  Carriers flagged: {total}", file=sys.stderr)

# ── CSV output ───────────────────────────────────────────────────────────────
if output_format == "csv":
    writer = csv.DictWriter(sys.stdout, fieldnames=columns)
    writer.writeheader()
    writer.writerows(flagged)
    sys.exit(0)

# ── Table output ─────────────────────────────────────────────────────────────
# Compute column widths
headers = {
    "carrier_name": "Carrier Name",
    "dot_number": "DOT #",
    "mc_number": "MC #",
    "state": "ST",
    "last_insurance_filing": "Last Filing",
    "days_since_filing": "Days Gap",
    "fleet_size": "Fleet Size",
    "phone": "Phone",
    "email": "Email",
}

widths = {}
for col in columns:
    max_w = len(headers[col])
    for row in flagged:
        max_w = max(max_w, len(str(row[col])))
    # Cap carrier_name and email to reasonable widths
    if col == "carrier_name":
        max_w = min(max_w, 40)
    elif col == "email":
        max_w = min(max_w, 30)
    elif col == "fleet_size":
        max_w = min(max_w, 25)
    widths[col] = max_w

def fmt_row(vals):
    parts = []
    for col in columns:
        v = str(vals[col])
        w = widths[col]
        if col in ("days_since_filing", "dot_number"):
            parts.append(v.rjust(w))  # Right-align numbers
        else:
            parts.append(v[:w].ljust(w))
    return " | ".join(parts)

separator = "-+-".join("-" * widths[c] for c in columns)

print()
print(f"  FMCSA Insurance Filing Gap Report")
print(f"  Generated: {today}  |  Gap threshold: {min_gap_days} days  |  Carriers flagged: {total}")
print()
print(fmt_row(headers))
print(separator)
for row in flagged:
    print(fmt_row(row))
print(separator)
print(f"  Total: {total} carriers")
print()
PYEOF

log_info "Done."
