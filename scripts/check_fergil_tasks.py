import sqlite3

conn = sqlite3.connect("data/autoviral_memory.db")
c = conn.cursor()
rows = c.execute("SELECT task_id, titulo, status, criado_em FROM videos_gerados WHERE canal='fergil'").fetchall()
print(f"Total tarefas FERGIL: {len(rows)}")
for r in rows:
    print(r)
conn.close()
