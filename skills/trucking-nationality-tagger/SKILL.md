# Trucking Nationality Tagger

Classifies trucking company leads based on owner names and emails using Gemini (`gemini-3.1-flash-lite-preview`).

It runs a multi-threaded Python script that queries a PostgreSQL/Supabase `leads` table and assigns a `tags` array (e.g. `[Ethiopian]`, `[Indian]`) based on high-confidence regex-like name heuristics inside Gemini.

## Usage
Use this skill when you need to bulk-tag unassigned leads by nationality. This should ideally be run nightly *after* the new search drops new leads into the database.

It is safe to re-run, as it only queries leads where the array does not already contain a known nationality tag.

```bash
# Run a dry-run / test for 30 leads only
python3 scripts/tag.py 30

# Run on the entire backlog
python3 scripts/tag.py
```

## Env Vars Required
- `DATABASE_URL` (Supabase Postgres string)
- `GEMINI_API_KEY` (Google Gemini Token)
