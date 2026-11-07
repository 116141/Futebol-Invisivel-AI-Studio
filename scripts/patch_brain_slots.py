import os
import re

with open("autoviral_brain.py", "rb") as f:
    data = f.read().decode("utf-8")

needle = '    cur.execute("""\r\n        CREATE TABLE IF NOT EXISTS canal_upload_status ('
if needle not in data:
    needle = '    cur.execute("""\n        CREATE TABLE IF NOT EXISTS canal_upload_status ('

print("Needle found:", needle in data)

addition = '''    cur.execute("""\r\n        CREATE TABLE IF NOT EXISTS publicacoes_pico_log (\r\n            canal TEXT,\r\n            slot_id TEXT,\r\n            data_cv TEXT,\r\n            video_id TEXT,\r\n            publicado_em TEXT,\r\n            PRIMARY KEY (canal, slot_id, data_cv)\r\n        )\r\n    """)\r\n'''

new_data = data.replace(needle, addition + needle, 1)

helper_funcs = '''

def registrar_publicacao_pico(canal: str, slot_id: str, data_cv: str, video_id: str) -> bool:
    """Registra a liberação ao público de um vídeo no horário de pico, garantindo que o slot não se repita."""
    conn = get_conn()
    cur = conn.cursor()
    agora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur.execute("""
            INSERT INTO publicacoes_pico_log (canal, slot_id, data_cv, video_id, publicado_em)
            VALUES (?, ?, ?, ?, ?)
        """, (canal, slot_id, data_cv, video_id, agora_str))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def slot_pico_ja_executado(canal: str, slot_id: str, data_cv: str) -> bool:
    """Retorna True se um vídeo já foi liberado ao público para este canal, slot e data."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM publicacoes_pico_log
        WHERE canal = ? AND slot_id = ? AND data_cv = ?
    """, (canal, slot_id, data_cv))
    row = cur.fetchone()
    conn.close()
    return bool(row)
'''

# append helpers before final lines or at end
new_data += helper_funcs

with open("autoviral_brain.py", "wb") as f:
    f.write(new_data.encode("utf-8"))

print("Migration applied successfully!")
