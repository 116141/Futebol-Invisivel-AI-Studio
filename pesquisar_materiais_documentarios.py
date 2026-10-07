import os
import time
import requests
from ddgs import DDGS
from PIL import Image
from loguru import logger

# Pesquisa aprofundada de materiais visuais 16:9 Full HD para os 2 Documentários
DOCS_DATA = [
    {
        "name": "doc_manchester_city",
        "folder": os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "documentarios_pesquisa", "doc_manchester_city"),
        "queries": [
            "Manchester City Etihad Stadium night panoramic aerial 4k",
            "Pep Guardiola serious press conference documentary",
            "Premier League trophy court financial fair play hearing",
            "Sheikh Mansour Manchester City owners Abu Dhabi",
            "Erling Haaland Kevin De Bruyne sad pitch documentary",
            "English football fans protest money modern football",
            "Manchester City Champions League celebration gold confetti",
            "Premier League headquarters London entrance building"
        ]
    },
    {
        "name": "doc_cristiano_ronaldo",
        "folder": os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "documentarios_pesquisa", "doc_cristiano_ronaldo"),
        "queries": [
            "Cristiano Ronaldo Portugal Euro 2016 trophy tears emotional",
            "Cristiano Ronaldo Real Madrid Champions League iconic celebration",
            "Cristiano Ronaldo bench Portugal World Cup lonely",
            "Jorge Jesus coach shouting Portugal match dramatic",
            "Cristiano Ronaldo private jet inside luxury travelling",
            "Cristiano Ronaldo training gym hard work obsession",
            "Al Nassr stadium Riyadh crowd Cristiano Ronaldo",
            "Cristiano Ronaldo walking away dark stadium tunnel solitary"
        ]
    }
]

def download_and_crop_16_9(url, out_path):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200 and len(res.content) > 5000:
            temp = out_path + ".tmp"
            with open(temp, "wb") as f:
                f.write(res.content)
            with Image.open(temp) as img:
                img = img.convert("RGB")
                w, h = img.size
                target_ratio = 1920 / 1080
                current_ratio = w / h
                if current_ratio > target_ratio:
                    new_w = int(h * target_ratio)
                    left = (w - new_w) // 2
                    img = img.crop((left, 0, left + new_w, h))
                else:
                    new_h = int(w / target_ratio)
                    top = (h - new_h) // 2
                    img = img.crop((0, top, w, top + new_h))
                img = img.resize((1920, 1080), Image.LANCZOS)
                img.save(out_path, "JPEG", quality=95)
            if os.path.exists(temp):
                os.remove(temp)
            return True
    except Exception:
        pass
    return False

def pre_fetch_materials():
    ddgs = DDGS()
    for doc in DOCS_DATA:
        os.makedirs(doc["folder"], exist_ok=True)
        logger.info(f"\nColetando acervo cinematográfico 16:9 para: {doc['name']}...")
        
        for i, q in enumerate(doc["queries"]):
            out_file = os.path.join(doc["folder"], f"cena_{i+1:02d}.jpg")
            if os.path.exists(out_file):
                continue
            logger.info(f"Buscando [{i+1}/{len(doc['queries'])}]: '{q}'...")
            try:
                results = list(ddgs.images(q, max_results=8))
            except Exception:
                results = []
                
            for r in results:
                url = r.get("image")
                if url and download_and_crop_16_9(url, out_file):
                    logger.success(f"Imagem 16:9 Full HD pronta: {out_file}")
                    break
            time.sleep(1)

if __name__ == '__main__':
    pre_fetch_materials()
