import sqlite3

conn = sqlite3.connect("data/autoviral_memory.db")
c = conn.cursor()
r = c.execute("SELECT task_id, titulo, roteiro, post_descricao FROM videos_gerados WHERE task_id='bb00fa1e-980c-4905-a28f-a2547e4c193c'").fetchone()
if r:
    print("TASK:", r[0])
    print("TITULO:", r[1])
    print("ROTEIRO:\n", r[2])
    print("\nDESCRICAO:\n", r[3])
conn.close()
