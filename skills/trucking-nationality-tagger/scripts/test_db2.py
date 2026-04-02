import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.openclaw/workspace/projects/AutoPax-Trucking-CRM/.env.local"))
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()
NATIONALITIES = ["Ethiopian", "Eritrean", "Indian", "Pakistani"]
tags_to_check = NATIONALITIES + ["NotApplicable"]
nationality_check = " AND ".join([f"NOT (COALESCE(l.tags, '{{}}') @> ARRAY['{n}'])" for n in tags_to_check])

cur.execute(f"SELECT count(*) FROM public.leads l LEFT JOIN public.companies c ON c.dot_number = l.dot_number WHERE ({nationality_check}) AND (c.legal_name IS NOT NULL OR c.email IS NOT NULL);")
print("Total untagged leads in DB:", cur.fetchone()[0])
