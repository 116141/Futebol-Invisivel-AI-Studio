"""
Script de Limpeza Automática do Sistema AutoViral
Liberta espaço em disco eliminando caches, temporários e lixos sem afetar código ou arquivos vitais.
"""

import os
import shutil
from loguru import logger

def executar_faxina_disco():
    total_libertado = 0

    def apagar(caminho):
        nonlocal total_libertado
        if not os.path.exists(caminho):
            return
        try:
            if os.path.isfile(caminho) or os.path.islink(caminho):
                sz = os.path.getsize(caminho)
                os.remove(caminho)
                total_libertado += sz
            elif os.path.isdir(caminho):
                sz = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(caminho) for f in fs if os.path.isfile(os.path.join(r, f)))
                shutil.rmtree(caminho, ignore_errors=True)
                total_libertado += sz
        except Exception as e:
            logger.debug(f"Ignorado {caminho}: {e}")

    logger.info("Iniciando limpeza de temporários e caches...")

    # 1. Pastas temporarias de render/scraping do projeto
    pastas_temp = [
        "temp_spy_thumbs",
        "temp_web_build_2f385a3e",
        "temp",
        "tmp"
    ]
    for p in pastas_temp:
        apagar(p)

    # 2. Caches do Python / Pip / Puppeteer / HuggingFace
    apagar(os.path.expanduser("~/AppData/Local/pip/cache"))
    apagar(os.path.expanduser("~/.cache/puppeteer"))
    apagar(os.path.expanduser("~/.cache/hyperframes"))

    # 3. Temp do Windows
    temp_win = os.environ.get("TEMP")
    if temp_win and os.path.exists(temp_win):
        for item in os.listdir(temp_win):
            apagar(os.path.join(temp_win, item))

    # 4. Limpar vídeos já publicados e brutos antigos de produção
    pastas_publicadas = [
        "canais/canal_01_futebol_invisivel/videos_publicados",
        "canais/canal_03_fergil/videos_publicados",
        "canais/canal_04_achadinhos_moda_feminina/videos_publicados",
        "canais/canal_01_futebol_invisivel/producao_ativa"
    ]
    for p in pastas_publicadas:
        if os.path.exists(p):
            for item in os.listdir(p):
                apagar(os.path.join(p, item))

    # 5. Arquivos .tmp, .bak soltos
    for root, dirs, files in os.walk("."):
        if any(ign in root for ign in [".git", "venv", ".venv"]):
            continue
        for f in files:
            if f.endswith((".tmp", ".bak")):
                apagar(os.path.join(root, f))

    mb_livre = total_libertado / (1024 * 1024)
    total, used, free = shutil.disk_usage("C:")
    logger.success(f"Faxina concluída! Libertados: {mb_livre:.2f} MB | Espaço livre no Disco C: {free/(1024**3):.2f} GB")

if __name__ == "__main__":
    executar_faxina_disco()
