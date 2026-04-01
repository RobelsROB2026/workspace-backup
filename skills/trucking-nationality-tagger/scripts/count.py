import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/research/trucking/.env"))
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()
NATIONALITIES = ["Ethiopian", "Eritrean", "Indian", "Pakistani"]
nationality_check = " AND ".join([f"NOT (COALESCE(l.tags, '{{}}') @> ARRAY['{n}'])" for n in NATIONALITIES])
cur.execute(f"SELECT count(*) FROM leads l LEFT JOIN companies c ON c.dot_number = l.dot_number WHERE ({nationality_check}) AND (c.legal_name IS NOT NULL OR c.email IS NOT NULL)")
print(cur.fetchone()[0])
