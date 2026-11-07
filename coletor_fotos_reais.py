import os
import sys
import time
import json
import urllib.request
import urllib.parse
from PIL import Image
from loguru import logger

def download_and_crop(url: str, out_path: str) -> bool:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            if len(content) < 8000:
                return False
                
            temp_file = out_path + ".tmp"
            with open(temp_file, "wb") as f:
                f.write(content)
                
            with Image.open(temp_file) as img:
                img = img.convert("RGB")
                w, h = img.size
                target_ratio = 1080 / 1920
                current_ratio = w / h
                
                if current_ratio > target_ratio:
                    new_w = int(h * target_ratio)
                    left = (w - new_w) // 2
                    img = img.crop((left, 0, left + new_w, h))
                else:
                    new_h = int(w / target_ratio)
                    top = (h - new_h) // 2
                    img = img.crop((0, top, w, top + new_h))
                    
                img = img.resize((1080, 1920), Image.LANCZOS)
                img.save(out_path, "JPEG", quality=95)
                
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return True
    except Exception as e:
        logger.warning(f"Falha ao processar imagem de {url}: {e}")
        return False

def search_wikimedia_images(query: str, max_results: int = 3) -> list:
    """
    Busca imagens reais no Wikimedia Commons através da API pública oficial.
    Alta precisão editorial, sem bloqueios de rate-limit.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    encoded_q = urllib.parse.quote(query)
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={encoded_q}&gsrnamespace=6&gsrlimit={max_results}&prop=imageinfo&iiprop=url&format=json"
    
    req = urllib.request.Request(url, headers=headers)
    image_urls = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for p in pages.values():
                ii = p.get("imageinfo")
                if ii and len(ii) > 0:
                    raw_url = ii[0].get("url")
                    if raw_url:
                        # Remove parâmetros de query tipo ?utm_source=...
                        clean_url = raw_url.split("?")[0]
                        ext = clean_url.lower().split(".")[-1]
                        if ext in ["jpg", "jpeg", "png"]:
                            image_urls.append(raw_url)
    except Exception as e:
        logger.warning(f"Erro na busca Wikimedia para '{query}': {e}")
        
    return image_urls

def collect_editorial_materials(queries: list, target_dir: str) -> list:
    """
    Coleta fotos reais 100% relacionadas para cada query do roteiro.
    """
    os.makedirs(target_dir, exist_ok=True)
    downloaded = []
    
    for i, q in enumerate(queries):
        scene_file = os.path.join(target_dir, f"cena_{i+1:02d}.jpg")
        logger.info(f"Buscando foto real ({i+1}/{len(queries)}): '{q}'...")
        urls = search_wikimedia_images(q, max_results=3)
        
        success = False
        for u in urls:
            if download_and_crop(u, scene_file):
                logger.success(f"Foto oficial salva: {scene_file}")
                downloaded.append(scene_file)
                success = True
                break
                
        if not success:
            logger.warning(f"Nenhuma foto baixada para '{q}'.")
            
        time.sleep(0.3)
        
    return downloaded

if __name__ == "__main__":
    test_queries = [
        "Vinicius Junior Real Madrid",
        "Ballon d Or trophy",
        "Florentino Perez Real Madrid",
        "Santiago Bernabeu stadium",
        "Carlo Ancelotti Real Madrid"
    ]
    out_dir = "canais/canal_01_futebol_invisivel/materiais_fotos_videos/teste_wikimedia"
    res = collect_editorial_materials(test_queries, out_dir)
    print("Total coletadas com sucesso:", len(res))
