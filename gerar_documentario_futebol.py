import os
import sys
import json
import time
import requests
import subprocess
import imageio_ffmpeg
from ddgs import DDGS
from PIL import Image
from loguru import logger
from google import genai

GEMINI_API_KEY = "AIzaSyCyPvygTtJiC7E4g9BdFnWkgECUGLNm5ak"
GEMINI_MODELS = [
    "gemini-3.1-flash-lite-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.7-flash"
]

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

ZOOM_EFFECTS_16_9 = [
    "zoompan=z='min(zoom+0.0008,1.15)':d=180:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
    "zoompan=z='max(1.15-0.0008*on,1.0)':d=180:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
    "zoompan=z='min(zoom+0.001,1.18)':d=180:x='iw/3-(iw/zoom/3)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30"
]

def generate_documentary_script(title: str):
    logger.info(f"[DOCUMENTÁRIO 16:9] Gerando roteiro documental para: '{title}'...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Você é o roteirista-chefe de documentários esportivos no estilo ESPN 30 for 30 e Netflix.
    Escreva o roteiro narrado de um mini-documentário de alta profundidade para o YouTube (formato 16:9 horizontal).

    Tema: "{title}"
    Canal: "Futebol Invisível"

    ESTRUTURA DO DOCUMENTÁRIO (4 Atos):
    - Ato 1: O Gancho e a Apresentação do Mistério/Conflito.
    - Ato 2: Os Bastidores e as Revelações Inéditas.
    - Ato 3: O Ponto de Ruptura e a Decisão Tática/Psicológica.
    - Ato 4: A Conclusão Épica, Reflexão sobre o Legado e Chamada para Inscrição no canal Futebol Invisível.

    REGRAS:
    - Narração imersiva, inteligente, jornalística e emocionante (~400 a 500 palavras, cerca de 3 a 4 minutos de documentário piloto).
    - Crie 15 termos de busca em inglês precisos para fotos/cenas reais de alta qualidade que ilustrem cada momento da narrativa.

    Responda em JSON puro:
    {{
        "title": "{title}",
        "script": "Texto narrado completo do documentário sem marcações de cena",
        "search_queries": [
            "query 1", "query 2", "query 3", "query 4", "query 5",
            "query 6", "query 7", "query 8", "query 9", "query 10",
            "query 11", "query 12", "query 13", "query 14", "query 15"
        ]
    }}
    """
    for model in GEMINI_MODELS:
        try:
            res = client.models.generate_content(model=model, contents=prompt)
            text = res.text.strip()
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Tentativa falhou com {model}: {e}")
    raise RuntimeError("Erro ao gerar roteiro do documentário.")

def download_and_crop_16_9(url, out_path):
    headers = {"User-Agent": "Mozilla/5.0"}
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

def produce_documentary(title: str):
    data = generate_documentary_script(title)
    task_id = f"doc_{int(time.time())}"
    base_dir = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", task_id)
    clips_dir = os.path.join(base_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    ddgs = DDGS()
    saved_images = []
    logger.info(f"Buscando {len(data['search_queries'])} fotos reais para o documentário...")
    for i, q in enumerate(data['search_queries']):
        img_out = os.path.join(base_dir, f"cena_{i+1:02d}.jpg")
        try:
            results = list(ddgs.images(q, max_results=6))
        except Exception:
            results = []
        for r in results:
            url = r.get("image")
            if url and download_and_crop_16_9(url, img_out):
                saved_images.append(img_out)
                break
        time.sleep(1)
        
    logger.info(f"Imagens coletadas: {len(saved_images)}. Renderizando clipes 16:9...")
    clips = []
    for i, img in enumerate(saved_images):
        out_clip = os.path.join(clips_dir, f"clip_{i+1:02d}.mp4")
        effect = ZOOM_EFFECTS_16_9[i % len(ZOOM_EFFECTS_16_9)]
        cmd = [
            FFMPEG, "-y",
            "-loop", "1",
            "-i", img,
            "-vf", f"{effect},format=yuv420p",
            "-t", "6",  # 6 segundos por cena para documentário longo
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            out_clip
        ]
        subprocess.run(cmd, capture_output=True)
        clips.append(os.path.abspath(out_clip))
        
    materials_arg = ",".join(clips)
    dest_video = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos", f"{task_id}.mp4")
    
    cmd_cli = [
        sys.executable,
        "cli.py",
        "--video-subject", data['title'],
        "--video-script", data['script'],
        "--video-source", "local",
        "--video-materials", materials_arg,
        "--voice-name", "pt-BR-AntonioNeural",
        "--video-aspect", "16:9",  # Horizontal widescreen clássico
        "--video-clip-duration", "5",
        "--video-concat-mode", "sequential",
        "--font-size", "42",  # Tamanho ideal para tela de TV/PC
        "--text-fore-color", "#FFFFFF",
        "--stroke-color", "#000000",
        "--stroke-width", "1.5"
    ]
    
    logger.info("Renderizando documentário completo em 16:9 Full HD...")
    subprocess.run(cmd_cli)
    
    import glob
    tasks = sorted(glob.glob("storage/tasks/*/final-1.mp4"), key=os.path.getmtime, reverse=True)
    if tasks:
        import shutil
        shutil.copy(tasks[0], dest_video)
        logger.success(f"DOCUMENTÁRIO PRONTO ENTREGUE EM: {dest_video}")
        return dest_video

if __name__ == '__main__':
    doc_title = sys.argv[1] if len(sys.argv) > 1 else "A Queda de Cristiano Ronaldo: O Fim Dramático na Seleção Portuguesa"
    produce_documentary(doc_title)
