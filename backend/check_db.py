import os, psycopg2

conn = psycopg2.connect(os.environ["DB_URL"])
cur = conn.cursor()

cur.execute("select table_name from information_schema.tables where table_schema='public' order by 1")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    cur.execute(f'select count(*) from "{t}"')
    print(f"{t}: {cur.fetchone()[0]} rows")

cur.execute("select extname from pg_extension")
print("extensions:", [r[0] for r in cur.fetchall()])
