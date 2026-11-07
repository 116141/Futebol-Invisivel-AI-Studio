"""
Script de triagem e arquivamento controlado.
Executa em modo SIMULAÇÃO por padrão (dry_run=True).
Apenas aplica as alterações no banco se invocado com --aplicar.
"""

import sys
import os
import re

# Garante raiz do projeto no PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import autoviral_brain

def normalizar_titulo(tit: str) -> str:
    if not tit:
        return ""
    t = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27ff]', '', tit)
    t = re.sub(r'[^\w\s]', '', t.lower())
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def executar_triagem(dry_run: bool = True):
    conn = autoviral_brain.get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT task_id, canal, tipo, titulo, file_path, criado_em, sha256, status
        FROM videos_gerados
        ORDER BY canal, criado_em ASC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    grupos_por_canal = {"futebol": {}, "moda": {}}
    for r in rows:
        canal = r.get("canal") or "futebol"
        if canal not in grupos_por_canal:
            grupos_por_canal[canal] = {}
        t_norm = normalizar_titulo(r.get("titulo") or "")
        if t_norm not in grupos_por_canal[canal]:
            grupos_por_canal[canal][t_norm] = []
        grupos_por_canal[canal][t_norm].append(r)

    tarefas_para_arquivar = []
    tarefas_para_manter = []

    # 1. Futebol: arquivar acervo antigo
    for t_norm, itens in grupos_por_canal.get("futebol", {}).items():
        for it in itens:
            tarefas_para_arquivar.append(it["task_id"])

    # 2. Moda: manter exatamente 1 original por produto único e arquivar os demais duplicados
    for t_norm, itens in grupos_por_canal.get("moda", {}).items():
        for idx, it in enumerate(itens):
            if idx == 0:
                tarefas_para_manter.append(it["task_id"])
            else:
                tarefas_para_arquivar.append(it["task_id"])

    print("=" * 70)
    modo_str = "SIMULAÇÃO (DRY RUN - Nenhuma alteração feita)" if dry_run else "EXECUÇÃO REAL (APLICANDO NA DB)"
    print(f"  PLANO DE ARQUIVAMENTO: {modo_str}")
    print("=" * 70)
    print(f"Tarefas a ARQUIVAR: {len(tarefas_para_arquivar)} (Futebol: 63, Moda duplicados: 20)")
    print(f"Tarefas a MANTER:   {len(tarefas_para_manter)} (Moda produtos únicos)")
    print("=" * 70)

    if not dry_run:
        afetados = autoviral_brain.arquivar_tarefas(tarefas_para_arquivar)
        print(f"✅ Sucesso: {afetados} tarefas movidas para o estado ARQUIVADO na base de dados.")
    else:
        print("ℹ️ Para aplicar de verdade, execute com a flag: --aplicar")

if __name__ == "__main__":
    aplicar_flag = "--aplicar" in sys.argv
    executar_triagem(dry_run=not aplicar_flag)
