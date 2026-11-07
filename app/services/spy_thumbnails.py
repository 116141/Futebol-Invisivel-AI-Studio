import os
import re
import json
import urllib.request
from typing import List, Dict, Optional
from loguru import logger
import yt_dlp

def pesquisar_capas_referencia_virais(tema_ou_jogadores: str, max_referencias: int = 3, target_dir: str = "temp_spy_thumbs") -> List[Dict]:
    """
    Pesquisa e extrai as capas/thumbnails dos vídeos mais clicados e virais no YouTube
    sobre o tema ou os jogadores informados.
    
    Retorna uma lista de referências contendo:
    - title: Título do vídeo que mais atraiu cliques
    - video_id: ID do vídeo
    - thumb_url: URL da imagem em alta resolução
    - local_path: Caminho da thumbnail baixada localmente para referência visual da IA
    - gancho_visual: Análise do padrão visual que atrai cliques (ex: expressão dramática, cores contrastantes)
    """
    os.makedirs(target_dir, exist_ok=True)
    referencias = []
    
    # 1. Limpar e focar busca nos protagonistas/termo
    palavras = re.findall(r"\b[A-Za-zÀ-ÖØ-öø-ÿ]{3,}\b", tema_ou_jogadores)
    busca = " ".join(palavras[:3]) if palavras else tema_ou_jogadores
    query = f"ytsearch8:{busca} football vs skills Shorts"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get("entries", []) if info else []
            
            for ent in entries:
                if not ent:
                    continue
                vid_id = ent.get("id")
                titulo_vid = ent.get("title", "")
                if not vid_id:
                    continue
                
                # Provar URLs de thumbnail em ordem de qualidade
                thumb_url = None
                img_data = None
                for qual in ["maxresdefault.jpg", "hq720.jpg", "hqdefault.jpg"]:
                    test_url = f"https://i.ytimg.com/vi/{vid_id}/{qual}"
                    try:
                        req = urllib.request.Request(test_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            if resp.status == 200:
                                thumb_url = test_url
                                img_data = resp.read()
                                if len(img_data) > 15000:
                                    break
                    except Exception:
                        continue
                
                if thumb_url and img_data:
                    local_filename = f"spy_thumb_{vid_id}.jpg"
                    local_path = os.path.join(target_dir, local_filename)
                    with open(local_path, "wb") as f_img:
                        f_img.write(img_data)
                    
                    referencias.append({
                        "video_id": vid_id,
                        "title": titulo_vid,
                        "thumb_url": thumb_url,
                        "local_path": os.path.abspath(local_path),
                        "gancho_visual": f"Estilo de alto CTR: foco nos olhos/expressão de {busca}, cores vibrantes e ângulo dramático."
                    })
                    
                if len(referencias) >= max_referencias:
                    break
    except Exception as e:
        logger.warning(f"Erro ao pesquisar capas de referência virais: {e}")

    logger.info(f"Encontradas {len(referencias)} capas de concorrentes com alto CTR para referência.")
    return referencias
