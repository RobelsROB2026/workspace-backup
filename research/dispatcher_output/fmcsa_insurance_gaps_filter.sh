#!/usr/bin/env bash
#
# fmcsa_insurance_gaps_filter.sh
# Query FMCSA census data via the Socrata API and filter for carriers
# with insurance filing gaps or lapsed insurance status.
#
# Data source: https://data.transportation.gov/resource/az4b-hbig.json

set -euo pipefail

readonly BASE_URL="https://data.transportation.gov/resource/az4b-hbig.json"
readonly DEFAULT_LIMIT=1000
readonly CURL_TIMEOUT=30
readonly CURL_RETRIES=3

# Defaults
LIMIT="$DEFAULT_LIMIT"
OFFSET=0
STATE=""
APP_TOKEN=""
OUTPUT_FORMAT="tsv"   # tsv or json
LAPSED_ONLY=false
WHERE_EXTRA=""

usage() {
    cat <<'USAGE'
Usage: fmcsa_insurance_gaps_filter.sh [OPTIONS]

Query FMCSA census data from the Socrata Open Data API and filter for
carriers with insurance filing gaps or lapsed insurance status.

Options:
  -l, --limit NUM        Max rows to return (default: 1000)
  -o, --offset NUM       Offset for pagination (default: 0)
  -s, --state CODE       Filter by physical state (2-letter code, e.g. TX)
  -t, --token TOKEN      Socrata app token (optional, raises throttle limits)
  -w, --where CLAUSE     Additional SoQL $where clause (AND-ed with defaults)
  -f, --format FORMAT    Output format: tsv (default) or json
      --lapsed-only      Show only carriers whose BIPD insurance is lapsed
  -h, --help             Show this help message

Environment:
  SOCRATA_APP_TOKEN      Used as app token if -t is not supplied

Examples:
  # Basic query — carriers with insurance issues, TSV output
  ./fmcsa_insurance_gaps_filter.sh

  # Texas carriers only, lapsed insurance, JSON output
  ./fmcsa_insurance_gaps_filter.sh -s TX --lapsed-only -f json

  # Paginate through results
  ./fmcsa_insurance_gaps_filter.sh -l 500 -o 500

  # Add a custom SoQL filter
  ./fmcsa_insurance_gaps_filter.sh -w "nbr_power_unit > 10"
USAGE
}

die() { echo "Error: $*" >&2; exit 1; }

# ---------- argument parsing ----------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -l|--limit)   LIMIT="${2:?missing value for $1}";  shift 2 ;;
        -o|--offset)  OFFSET="${2:?missing value for $1}"; shift 2 ;;
        -s|--state)   STATE="${2:?missing value for $1}";  shift 2 ;;
        -t|--token)   APP_TOKEN="${2:?missing value for $1}"; shift 2 ;;
        -w|--where)   WHERE_EXTRA="${2:?missing value for $1}"; shift 2 ;;
        -f|--format)  OUTPUT_FORMAT="${2:?missing value for $1}"; shift 2 ;;
        --lapsed-only) LAPSED_ONLY=true; shift ;;
        -h|--help)    usage; exit 0 ;;
        *)            die "unknown option: $1 (try --help)" ;;
    esac
done

# Validate
[[ "$OUTPUT_FORMAT" == "tsv" || "$OUTPUT_FORMAT" == "json" ]] \
    || die "format must be 'tsv' or 'json'"
[[ "$LIMIT" =~ ^[0-9]+$ ]]  || die "limit must be a positive integer"
[[ "$OFFSET" =~ ^[0-9]+$ ]] || die "offset must be a non-negative integer"

# Use env var as fallback for app token
APP_TOKEN="${APP_TOKEN:-${SOCRATA_APP_TOKEN:-}}"

# ---------- build SoQL $where clause ----------
# Insurance-gap filter logic:
#   BIPD_INSURANCE_REQUIRED = 'Y' but BIPD_INSURANCE_ON_FILE < BIPD_INSURANCE_REQUIRED
#   or INSURANCE_BIPD_ON_FILE is missing / 0 while required
#   The dataset exposes bipd_insurance_required, bipd_insurance_on_file,
#   and bond_insurance_on_file among other fields.
#
# We look for carriers where:
#   1. bipd_insurance_required = 'Y'  AND  bipd_insurance_on_file != 'Y'
#      (required but not on file — filing gap)
#   2. OR bond_insurance_required = 'Y'  AND  bond_insurance_on_file != 'Y'
#      (bond/surety required but not on file)

if [[ "$LAPSED_ONLY" == true ]]; then
    INSURANCE_FILTER="(bipd_insurance_required='Y' AND bipd_insurance_on_file != 'Y')"
else
    INSURANCE_FILTER="((bipd_insurance_required='Y' AND bipd_insurance_on_file != 'Y') OR (bond_insurance_required='Y' AND bond_insurance_on_file != 'Y'))"
fi

WHERE_CLAUSE="$INSURANCE_FILTER"

if [[ -n "$STATE" ]]; then
    STATE_UPPER="${STATE^^}"
    WHERE_CLAUSE="${WHERE_CLAUSE} AND phy_state='${STATE_UPPER}'"
fi

if [[ -n "$WHERE_EXTRA" ]]; then
    WHERE_CLAUSE="${WHERE_CLAUSE} AND (${WHERE_EXTRA})"
fi

# ---------- build URL ----------
# URL-encode $where value
encode() { python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$1"; }

ENCODED_WHERE=$(encode "$WHERE_CLAUSE")

URL="${BASE_URL}?\$where=${ENCODED_WHERE}&\$limit=${LIMIT}&\$offset=${OFFSET}&\$order=dot_number"

# ---------- curl headers ----------
CURL_HEADERS=(-H "Accept: application/json")
if [[ -n "$APP_TOKEN" ]]; then
    CURL_HEADERS+=(-H "X-App-Token: ${APP_TOKEN}")
fi

# ---------- fetch ----------
echo "Querying FMCSA census data..." >&2
echo "Filter: ${WHERE_CLAUSE}" >&2
echo "Limit: ${LIMIT}  Offset: ${OFFSET}" >&2

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

HTTP_CODE=$(curl -s -w "%{http_code}" -o "$TMPFILE" \
    --retry "$CURL_RETRIES" \
    --retry-delay 2 \
    --max-time "$CURL_TIMEOUT" \
    --connect-timeout 10 \
    "${CURL_HEADERS[@]}" \
    "$URL" 2>&1) || {
    die "curl failed — check your network connection"
}

# ---------- response validation ----------
if [[ "$HTTP_CODE" -lt 200 || "$HTTP_CODE" -ge 300 ]]; then
    echo "HTTP $HTTP_CODE response body:" >&2
    cat "$TMPFILE" >&2
    die "API returned HTTP ${HTTP_CODE}"
fi

# Check for empty / null array
ROW_COUNT=$(python3 -c "
import json, sys
data = json.load(open(sys.argv[1]))
if not isinstance(data, list):
    print('error', file=sys.stderr)
    sys.exit(1)
print(len(data))
" "$TMPFILE") || die "unexpected response format (not a JSON array)"

if [[ "$ROW_COUNT" -eq 0 ]]; then
    echo "No carriers matched the filter." >&2
    exit 0
fi

echo "Returned ${ROW_COUNT} carrier record(s)." >&2

# ---------- output ----------
if [[ "$OUTPUT_FORMAT" == "json" ]]; then
    # Pretty-print the JSON
    python3 -m json.tool "$TMPFILE"
else
    # TSV: extract key fields for parseability
    python3 -c "
import csv, json, sys

data = json.load(open(sys.argv[1]))

fields = [
    'dot_number',
    'legal_name',
    'dba_name',
    'phy_street',
    'phy_city',
    'phy_state',
    'phy_zip',
    'telephone',
    'email_address',
    'mc_mx_ff_number',
    'entity_type',
    'operating_status',
    'nbr_power_unit',
    'driver_total',
    'bipd_insurance_required',
    'bipd_insurance_on_file',
    'bond_insurance_required',
    'bond_insurance_on_file',
]

writer = csv.writer(sys.stdout, delimiter='\t', lineterminator='\n')
writer.writerow(fields)
for row in data:
    writer.writerow([row.get(f, '') for f in fields])
" "$TMPFILE"
fi
