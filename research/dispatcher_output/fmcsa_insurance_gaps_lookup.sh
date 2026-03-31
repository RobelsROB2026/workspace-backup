#!/usr/bin/env bash
#
# FMCSA Insurance Filing Gaps Lookup
#
# Queries the FMCSA Socrata API (data.transportation.gov) to find motor carriers
# with insurance filing gaps — carriers whose BIPD or cargo insurance filings
# are missing, pending, or lapsed relative to their active authority status.
#
# Dataset: FMCSA Census — Active & Authorized Motor Carriers
# Endpoint: https://data.transportation.gov/resource/az4b-hbig.json
#
# Requires: curl, jq

set -euo pipefail

API_BASE="https://data.transportation.gov/resource/az4b-hbig.json"
DEFAULT_LIMIT=500
DEFAULT_STATE=""
DEFAULT_GAP_ONLY=false
APP_TOKEN="${SOCRATA_APP_TOKEN:-}"

usage() {
    cat <<'USAGE'
Usage: fmcsa_insurance_gaps_lookup.sh [OPTIONS]

Query the FMCSA Socrata API for carriers and detect insurance filing gaps.

Options:
  -s STATE    Filter by physical state (2-letter code, e.g. TX)
  -l LIMIT    Max results to return (default: 500, max: 50000)
  -g          Show only carriers with insurance filing gaps
  -d DOT      Look up a single carrier by DOT number
  -m MC       Look up a single carrier by MC/MX number
  -o FILE     Write results to FILE (default: stdout)
  -t TOKEN    Socrata app token (or set SOCRATA_APP_TOKEN env var)
  -h          Show this help message

Insurance Gap Detection:
  A carrier is flagged as having a gap when any of these are true:
    - BIPD insurance filing status is not "Yes"
    - Cargo insurance filing status is not "Yes"
    - Bond/surety filing status is not "Yes" (for brokers/freight forwarders)
    - MCS-150 form date is older than 2 years (biennial update overdue)

Examples:
  # Find all Texas carriers with insurance gaps
  fmcsa_insurance_gaps_lookup.sh -s TX -g

  # Look up a specific carrier by DOT number
  fmcsa_insurance_gaps_lookup.sh -d 1234567

  # Save first 1000 Florida results to a file
  fmcsa_insurance_gaps_lookup.sh -s FL -l 1000 -o fl_carriers.json

  # Show only gap carriers, pipe through less
  fmcsa_insurance_gaps_lookup.sh -g | less
USAGE
    exit 0
}

die() { printf 'Error: %s\n' "$1" >&2; exit 1; }

# --- Dependency check ---
for cmd in curl jq; do
    command -v "$cmd" >/dev/null 2>&1 || die "'$cmd' is required but not installed"
done

# --- Parse arguments ---
LIMIT="$DEFAULT_LIMIT"
STATE="$DEFAULT_STATE"
GAP_ONLY="$DEFAULT_GAP_ONLY"
DOT_NUMBER=""
MC_NUMBER=""
OUTPUT=""

while getopts ":s:l:gd:m:o:t:h" opt; do
    case $opt in
        s) STATE="$OPTARG" ;;
        l) LIMIT="$OPTARG" ;;
        g) GAP_ONLY=true ;;
        d) DOT_NUMBER="$OPTARG" ;;
        m) MC_NUMBER="$OPTARG" ;;
        o) OUTPUT="$OPTARG" ;;
        t) APP_TOKEN="$OPTARG" ;;
        h) usage ;;
        :) die "Option -$OPTARG requires an argument" ;;
        *) die "Unknown option -$OPTARG. Use -h for help." ;;
    esac
done

# --- Input validation ---
if [[ -n "$STATE" ]]; then
    STATE="${STATE^^}"
    [[ "$STATE" =~ ^[A-Z]{2}$ ]] || die "State must be a 2-letter code (e.g. TX)"
fi

if [[ -n "$LIMIT" ]]; then
    [[ "$LIMIT" =~ ^[0-9]+$ ]] || die "Limit must be a positive integer"
    (( LIMIT > 0 && LIMIT <= 50000 )) || die "Limit must be between 1 and 50000"
fi

if [[ -n "$DOT_NUMBER" ]]; then
    [[ "$DOT_NUMBER" =~ ^[0-9]+$ ]] || die "DOT number must be numeric"
fi

if [[ -n "$MC_NUMBER" ]]; then
    [[ "$MC_NUMBER" =~ ^[0-9]+$ ]] || die "MC number must be numeric"
fi

# --- Build SoQL query ---
build_query() {
    local where_clauses=()

    if [[ -n "$DOT_NUMBER" ]]; then
        where_clauses+=("dot_number='${DOT_NUMBER}'")
    fi

    if [[ -n "$MC_NUMBER" ]]; then
        where_clauses+=("mc_mx_ff_number='${MC_NUMBER}'")
    fi

    if [[ -n "$STATE" ]]; then
        where_clauses+=("phy_state='${STATE}'")
    fi

    # Always filter for active authorized carriers
    where_clauses+=("entity_type='CARRIER'")
    where_clauses+=("operating_status='AUTHORIZED'")

    local where=""
    if (( ${#where_clauses[@]} > 0 )); then
        where=$(IFS=" AND "; echo "${where_clauses[*]}")
    fi

    local params="\$limit=${LIMIT}"
    if [[ -n "$where" ]]; then
        params+="&\$where=$(jq -rn --arg w "$where" '$w | @uri')"
    fi
    params+="&\$order=dot_number"

    echo "$params"
}

# --- Execute API request ---
fetch_data() {
    local query_params
    query_params="$(build_query)"
    local url="${API_BASE}?${query_params}"

    local curl_opts=(-sS --fail --connect-timeout 15 --max-time 60)
    if [[ -n "$APP_TOKEN" ]]; then
        curl_opts+=(-H "X-App-Token: ${APP_TOKEN}")
    fi

    local http_response
    local http_code
    local tmpfile
    tmpfile=$(mktemp)
    trap "rm -f '$tmpfile'" EXIT

    http_code=$(curl "${curl_opts[@]}" -o "$tmpfile" -w '%{http_code}' "$url" 2>/dev/null) || {
        local exit_code=$?
        rm -f "$tmpfile"
        case $exit_code in
            6)  die "Could not resolve host data.transportation.gov — check DNS/network" ;;
            7)  die "Connection refused by data.transportation.gov" ;;
            28) die "Request timed out (60s). Try a smaller --limit or narrower filter" ;;
            22) die "HTTP error from API (code: $(cat "$tmpfile" 2>/dev/null || echo 'unknown'))" ;;
            *)  die "curl failed with exit code $exit_code" ;;
        esac
    }

    case "$http_code" in
        200) ;;
        403) rm -f "$tmpfile"; die "HTTP 403 Forbidden — you may need a Socrata app token (-t or SOCRATA_APP_TOKEN)" ;;
        429) rm -f "$tmpfile"; die "HTTP 429 Rate Limited — wait a moment and retry, or provide an app token" ;;
        4*) rm -f "$tmpfile"; die "HTTP ${http_code} client error" ;;
        5*) rm -f "$tmpfile"; die "HTTP ${http_code} server error — FMCSA API may be down" ;;
        *)  rm -f "$tmpfile"; die "Unexpected HTTP status: ${http_code}" ;;
    esac

    # Validate JSON
    if ! jq empty "$tmpfile" 2>/dev/null; then
        rm -f "$tmpfile"
        die "API returned invalid JSON"
    fi

    local count
    count=$(jq 'length' "$tmpfile")
    if (( count == 0 )); then
        rm -f "$tmpfile"
        die "No carriers found matching your criteria"
    fi

    printf '%s carriers returned from API\n' "$count" >&2
    cat "$tmpfile"
    rm -f "$tmpfile"
}

# --- Gap detection and formatting ---
# Determines if a carrier has an insurance filing gap based on available fields.
# The jq filter checks BIPD, cargo, bond filings and MCS-150 staleness.
JQ_GAP_DETECT='
def has_gap:
    ((.bipd_insurance_required // "N") == "Y" and (.bipd_insurance_on_file // "N") != "Y")
    or ((.cargo_insurance_required // "N") == "Y" and (.cargo_insurance_on_file // "N") != "Y")
    or ((.bond_insurance_required // "N") == "Y" and (.bond_insurance_on_file // "N") != "Y")
    or ((.mcs_150_form_date // null) != null
        and ((.mcs_150_form_date | split("T")[0] | strptime("%Y-%m-%d") | mktime) < (now - 63072000)));

def gap_reasons:
    [
        (if (.bipd_insurance_required // "N") == "Y" and (.bipd_insurance_on_file // "N") != "Y"
         then "BIPD insurance not on file" else empty end),
        (if (.cargo_insurance_required // "N") == "Y" and (.cargo_insurance_on_file // "N") != "Y"
         then "Cargo insurance not on file" else empty end),
        (if (.bond_insurance_required // "N") == "Y" and (.bond_insurance_on_file // "N") != "Y"
         then "Bond/surety not on file" else empty end),
        (if (.mcs_150_form_date // null) != null
            and ((.mcs_150_form_date | split("T")[0] | strptime("%Y-%m-%d") | mktime) < (now - 63072000))
         then "MCS-150 overdue (>2 years)" else empty end)
    ] | join("; ");
'

JQ_FORMAT='
.[] | {
    carrier_name:    (.legal_name // "N/A"),
    dot_number:      (.dot_number // "N/A"),
    mc_number:       (.mc_mx_ff_number // "N/A"),
    fleet_size:      ((.total_power_units // "0") + " power units, " + (.total_drivers // "0") + " drivers"),
    phone:           (.telephone_number // "N/A"),
    address:         ([.phy_street, .phy_city, .phy_state, .phy_zip] | map(select(. != null)) | join(", ")),
    bipd_required:   (.bipd_insurance_required // "N"),
    bipd_on_file:    (.bipd_insurance_on_file // "N"),
    cargo_required:  (.cargo_insurance_required // "N"),
    cargo_on_file:   (.cargo_insurance_on_file // "N"),
    bond_required:   (.bond_insurance_required // "N"),
    bond_on_file:    (.bond_insurance_on_file // "N"),
    mcs150_date:     (.mcs_150_form_date // "N/A" | split("T")[0]),
    has_gap:         has_gap,
    gap_reasons:     gap_reasons
}
'

process_results() {
    local raw_json="$1"

    local jq_program="${JQ_GAP_DETECT} ${JQ_FORMAT}"

    if [[ "$GAP_ONLY" == true ]]; then
        jq_program="${JQ_GAP_DETECT} [${JQ_FORMAT}] | map(select(.has_gap)) | .[]"
    fi

    local result
    result=$(echo "$raw_json" | jq -r "$jq_program" 2>/dev/null) || die "Failed to parse API response fields"

    if [[ -z "$result" || "$result" == "null" ]]; then
        if [[ "$GAP_ONLY" == true ]]; then
            printf 'No carriers with insurance filing gaps found.\n' >&2
            exit 0
        fi
        die "No results after processing"
    fi

    echo "$result"
}

format_table() {
    # Pretty-print the JSON stream as a readable report
    jq -r '
        "═══════════════════════════════════════════════════════════",
        "Carrier:      " + .carrier_name,
        "DOT#:         " + .dot_number,
        "MC/MX#:       " + .mc_number,
        "Fleet:        " + .fleet_size,
        "Phone:        " + .phone,
        "Address:      " + .address,
        "BIPD Ins:     Required=" + .bipd_required + "  On File=" + .bipd_on_file,
        "Cargo Ins:    Required=" + .cargo_required + "  On File=" + .cargo_on_file,
        "Bond/Surety:  Required=" + .bond_required + "  On File=" + .bond_on_file,
        "MCS-150 Date: " + .mcs150_date,
        "Insurance Gap: " + (if .has_gap then "*** YES ***" else "No" end),
        (if .gap_reasons != "" then "Gap Reasons:  " + .gap_reasons else empty end)
    '
}

# --- Main ---
main() {
    local raw_json
    raw_json="$(fetch_data)"

    local processed
    processed="$(process_results "$raw_json")"

    local output_data
    output_data="$(echo "$processed" | format_table)"

    # Summary
    local total gap_count
    total=$(echo "$processed" | jq -s 'length')
    gap_count=$(echo "$processed" | jq -s '[.[] | select(.has_gap)] | length')
    printf '\n%s carriers displayed, %s with insurance filing gaps\n\n' "$total" "$gap_count" >&2

    if [[ -n "$OUTPUT" ]]; then
        echo "$output_data" > "$OUTPUT"
        printf 'Results written to %s\n' "$OUTPUT" >&2
    else
        echo "$output_data"
    fi
}

main
