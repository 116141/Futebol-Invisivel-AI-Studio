import sqlite3

conn = sqlite3.connect("data/autoviral_memory.db")
c = conn.cursor()

# Manter a mais antiga (b644254b) e arquivar as outras 3 cópias do Larry Ellison
duplicadas_fergil = [
    'd00e5376-65bf-4d53-a5a2-f4b67689e118',
    '386f5436-20b1-43ed-bd6e-f2f134137ce0',
    '4ad49b83-da9e-4bae-a47a-457400dea8a5'
]

for tid in duplicadas_fergil:
    c.execute("UPDATE videos_gerados SET status = 'ARQUIVADO' WHERE task_id = ?", (tid,))

conn.commit()
print(f"Sucesso: {len(duplicadas_fergil)} cópias repetidas do Larry Ellison arquivadas na DB!")
conn.close()
