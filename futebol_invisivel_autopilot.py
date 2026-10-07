import os
import sys
import json
import glob
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

ZOOM_EFFECTS = [
    "zoompan=z='min(zoom+0.0015,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/4-(ih/zoom/4)':s=1080x1920:fps=30",
    "zoompan=z='max(1.2-0.0015*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.0015,1.2)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.002,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.0012,1.18)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
]

def generate_script_and_queries(title: str):
    logger.info(f"[FUTEBOL INVISÍVEL - IA] Analisando tema e gerando roteiro: '{title}'...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Você é o roteirista-chefe do canal do YouTube Shorts e TikTok 'Futebol Invisível'.
    O canal é especializado em polêmicas de bastidores, segredos táticos e histórias reais dos maiores jogadores e técnicos do mundo.

    Tema do Vídeo: "{title}"

    REGRAS DO ROTEIRO:
    1. Gancho irresistível nos primeiros 3 segundos (retenção altíssima).
    2. Narrativa jornalística, dramática e envolvente (estilo documentário esportivo investigativo).
    3. Duração da fala: entre 40 a 50 segundos (~90 a 115 palavras).
    4. Pergunta provocativa no final que force o espectador a debater nos comentários e se inscrever no canal 'Futebol Invisível'.
    5. Crie EXATAMENTE 6 termos de busca precisos no DuckDuckGo para encontrar fotos REAIS dos protagonistas/eventos citados.

    Responda EXCLUSIVAMENTE em formato JSON puro:
    {{
        "subject": "{title}",
        "script": "Texto narrado completo sem marcações de cena",
        "search_queries": [
            "Query 1 precisa para foto real",
            "Query 2 precisa para foto real",
            "Query 3 precisa para foto real",
            "Query 4 precisa para foto real",
            "Query 5 precisa para foto real",
            "Query 6 precisa para foto real"
        ]
    }}
    """
    
    data = None
    for model in GEMINI_MODELS:
        try:
            res = client.models.generate_content(model=model, contents=prompt)
            text = res.text.strip()
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            data = json.loads(text)
            logger.success(f"Roteiro e buscas gerados com sucesso via {model}!")
            break
        except Exception as e:
            logger.warning(f"Tentativa com {model} falhou: {e}")
            
    if not data:
        raise RuntimeError("Erro ao gerar roteiro via Gemini.")
    return data

def download_and_crop_image(url, out_path):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=12)
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
    except Exception:
        pass
    return False

def collect_real_materials(queries, task_id):
    mat_dir = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", task_id)
    os.makedirs(mat_dir, exist_ok=True)
    ddgs = DDGS()
    saved_images = []
    
    for i, q in enumerate(queries):
        out_file = os.path.join(mat_dir, f"cena_{i+1:02d}.jpg")
        logger.info(f"Buscando foto real para Cena {i+1}: '{q}'...")
        try:
            results = list(ddgs.images(q, max_results=8))
        except Exception:
            time.sleep(1)
            try:
                results = list(ddgs.images(q, max_results=5))
            except Exception:
                results = []
                
        success = False
        for r in results:
            img_url = r.get("image")
            if not img_url:
                continue
            if download_and_crop_image(img_url, out_file):
                logger.success(f"Foto real 9:16 salva: {out_file}")
                saved_images.append(out_file)
                success = True
                break
        time.sleep(1)
        
    return saved_images

def animate_real_clips(images, task_id):
    clips_dir = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", task_id, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    generated_clips = []
    
    for i, img_path in enumerate(images):
        out_clip = os.path.join(clips_dir, f"clip_{i+1:02d}.mp4")
        effect = ZOOM_EFFECTS[i % len(ZOOM_EFFECTS)]
        
        cmd = [
            FFMPEG, "-y",
            "-loop", "1",
            "-i", img_path,
            "-vf", f"{effect},format=yuv420p",
            "-t", "4",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            out_clip
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            generated_clips.append(os.path.abspath(out_clip))
            
    return generated_clips

def produce_video(title: str):
    task_id = str(int(time.time()))
    data = generate_script_and_queries(title)
    
    print("\n" + "="*50)
    print("ROTEIRO GERADO PELO SISTEMA:")
    print(data['script'])
    print("="*50 + "\n")
    
    images = collect_real_materials(data['search_queries'], task_id)
    if not images:
        raise RuntimeError("Não foi possível baixar fotos reais para o tema.")
        
    clips = animate_real_clips(images, task_id)
    materials_arg = ",".join(clips)
    
    output_target_name = f"{task_id}_{title.replace(' ', '_')[:30]}.mp4"
    output_dir = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos")
    os.makedirs(output_dir, exist_ok=True)
    
    cmd = [
        sys.executable,
        "cli.py",
        "--video-subject", data['subject'],
        "--video-script", data['script'],
        "--video-source", "local",
        "--video-materials", materials_arg,
        "--voice-name", "pt-BR-AntonioNeural",
        "--video-aspect", "9:16",
        "--video-clip-duration", "4",
        "--video-concat-mode", "sequential",
        "--font-size", "58",
        "--text-fore-color", "#FFFF00",
        "--stroke-color", "#000000",
        "--stroke-width", "1.5"
    ]
    
    logger.info("Renderizando vídeo final com voz jornalística e legendas dinâmicas...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    # Mover vídeo para a pasta do canal
    for line in res.stdout.split("\n"):
        if "final-1.mp4" in line and os.path.exists(line.strip()):
            dest = os.path.join(output_dir, output_target_name)
            import shutil
            shutil.copy(line.strip(), dest)
            logger.success(f"VÍDEO FINAL ENTREGUE EM: {dest}")
            return dest
            
    # Fallback busca direta no storage
    tasks = sorted(glob.glob("storage/tasks/*/final-1.mp4"), key=os.path.getmtime, reverse=True)
    if tasks:
        dest = os.path.join(output_dir, output_target_name)
        import shutil
        shutil.copy(tasks[0], dest)
        logger.success(f"VÍDEO FINAL ENTREGUE EM: {dest}")
        return dest

if __name__ == '__main__':
    video_title = sys.argv[1] if len(sys.argv) > 1 else "Cristiano Ronaldo Abandonou a Seleção? A Verdade da Treta com Jorge Jesus"
    produce_video(video_title)
