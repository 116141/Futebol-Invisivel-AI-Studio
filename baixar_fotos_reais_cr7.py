import os
import requests
from ddgs import DDGS
from PIL import Image
from loguru import logger
import time

DEST_DIR = "materiais_cr7"
os.makedirs(DEST_DIR, exist_ok=True)

# 6 buscas simples e diretas
SCENES = [
    ("01_cr7_portugal", "Cristiano Ronaldo Portugal national team"),
    ("02_jorge_jesus", "Jorge Jesus treinador"),
    ("03_cr7_banco", "Cristiano Ronaldo bench Portugal"),
    ("04_jorge_jesus_regras", "Jorge Jesus coletiva"),
    ("05_cr7_gols", "Cristiano Ronaldo Portugal celebration"),
    ("06_torcida_portugal", "Portugal fans stadium football")
]

def download_and_crop(url, out_path):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code == 200 and len(res.content) > 5000:
        temp_file = out_path + ".tmp"
        with open(temp_file, "wb") as f:
            f.write(res.content)
        
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
    return False

def fetch_all():
    ddgs = DDGS()
    saved_files = []
    
    for name, query in SCENES:
        out_file = os.path.join(DEST_DIR, f"{name}.jpg")
        if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
            logger.info(f"Já existe: {out_file}")
            saved_files.append(out_file)
            continue
            
        logger.info(f"Buscando imagem real para: {query}...")
        try:
            results = list(ddgs.images(query, max_results=8))
        except Exception as e:
            logger.warning(f"Timeout no search para {query}, tentando fallback...")
            time.sleep(1)
            try:
                results = list(ddgs.images(query, max_results=5))
            except Exception:
                results = []
                
        success = False
        for r in results:
            img_url = r.get("image")
            if not img_url:
                continue
            try:
                if download_and_crop(img_url, out_file):
                    logger.success(f"Foto salva com sucesso: {out_file}")
                    saved_files.append(out_file)
                    success = True
                    break
            except Exception:
                continue
        time.sleep(1)
            
    return saved_files

if __name__ == '__main__':
    saved = fetch_all()
    print(f"\nFotos reais prontas: {len(saved)} de {len(SCENES)}")
