import sqlite3

conn = sqlite3.connect("data/autoviral_memory.db")
c = conn.cursor()
rows = c.execute("SELECT task_id, canal, titulo, status FROM videos_gerados WHERE canal='futebol' AND status != 'ARQUIVADO'").fetchall()
for r in rows:
    print(r)
conn.close()
