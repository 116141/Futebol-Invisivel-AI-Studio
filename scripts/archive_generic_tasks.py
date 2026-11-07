import sqlite3

conn = sqlite3.connect("data/autoviral_memory.db")
c = conn.cursor()

# Arquivar as tarefas antigas que tinham caído no fallback genérico
tarefas_invalidas = [
    'bb00fa1e-980c-4905-a28f-a2547e4c193c',
    '3a8ff2d6-afeb-47df-9cd1-ddbdaf06c0e4',
    'e8536385-2bfb-4067-99bf-ace930bade80',
    '3e84e931-a9d8-4a74-ac4e-46f5d9dd27c7',
    '0d82e48f-ded6-4bbf-bb4d-8c944ee45fdb'
]

for tid in tarefas_invalidas:
    c.execute("UPDATE videos_gerados SET status = 'ARQUIVADO' WHERE task_id = ?", (tid,))

conn.commit()
print(f"Sucesso: {len(tarefas_invalidas)} tarefas com roteiros genéricos foram arquivadas com segurança!")
conn.close()
