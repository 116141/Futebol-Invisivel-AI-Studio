import sqlite3
from datetime import datetime, timezone, timedelta

conn = sqlite3.connect("data/autoviral_memory.db")
c = conn.cursor()
status_fergil = c.execute("SELECT canal, bloqueado, bloqueado_ate FROM canal_upload_status WHERE canal='fergil'").fetchone()
print("Status FERGIL:", status_fergil)

tz_cv = timezone(timedelta(hours=-1))
agora_cv = datetime.now(tz_cv)
print("Hora atual Cabo Verde:", agora_cv.strftime("%Y-%m-%d %H:%M:%S"))

if status_fergil and status_fergil[2]:
    dt_bloq = datetime.fromisoformat(status_fergil[2])
    agora_naive = agora_cv.replace(tzinfo=None)
    if agora_naive >= dt_bloq:
        print("O BLOQUEIO DO FERGIL JÁ EXPIROU! O CANAL ESTÁ LIBERADO.")
        c.execute("UPDATE canal_upload_status SET bloqueado = 0 WHERE canal='fergil'")
        conn.commit()
    else:
        diff = (dt_bloq - agora_naive).total_seconds() / 60
        print(f"Faltam {diff:.1f} minutos para expirar o bloqueio do FERGIL.")
conn.close()
