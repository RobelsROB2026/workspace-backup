# Trucking Insurance Lead CRM Tool

Command-line CRM for tracking trucking company insurance leads and interactions.

## Setup

No external dependencies required -- uses Python 3 standard library only. The SQLite database (`trucking_crm.db`) is created automatically on first run in the same directory as the script.

```bash
chmod +x trucking_crm_tool.py
```

## Usage

### Add a lead

```bash
python trucking_crm_tool.py add "ABC Trucking" \
  --dot 1234567 --mc 987654 --state TX \
  --phone "555-123-4567" --email "info@abctrucking.com" \
  --source "web" --status new
```

### List leads

```bash
python trucking_crm_tool.py list
python trucking_crm_tool.py list --status quoted --state TX
python trucking_crm_tool.py list --source referral
```

### Show lead details (with interaction history)

```bash
python trucking_crm_tool.py show 1
```

### Update a lead

```bash
python trucking_crm_tool.py update 1 --status contacted --phone "555-999-0000"
```

### Delete a lead

```bash
python trucking_crm_tool.py delete 1
```

### Log an interaction

Types: `call`, `email`, `meeting`, `quote`, `note`, `voicemail`

```bash
python trucking_crm_tool.py log 1 call \
  --notes "Discussed fleet size, needs liability + cargo" \
  --contact "John Smith"
```

### List interactions for a lead

```bash
python trucking_crm_tool.py interactions 1
```

### Import leads from CSV

```bash
python trucking_crm_tool.py import leads.csv
```

CSV must have a `company_name` column. Optional columns: `dot_number`, `mc_number`, `state`, `phone`, `email`, `lead_source`, `status`.

Example CSV:

```csv
company_name,dot_number,mc_number,state,phone,email,lead_source,status
ABC Trucking,1234567,987654,TX,555-123-4567,info@abc.com,web,new
XYZ Freight,2345678,876543,CA,555-987-6543,contact@xyz.com,referral,new
```

## Lead Statuses

`new` | `contacted` | `quoted` | `follow_up` | `won` | `lost` | `inactive`

## Database

SQLite database stored at `trucking_crm.db` (same directory as the script). Two tables:

- **leads** -- company info, DOT/MC numbers, status, source
- **interactions** -- timestamped log of calls, emails, meetings, quotes, notes
