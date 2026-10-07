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

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VIDEO_ID = "video_05_portugal_sem_cr7_fim_novela"
TITLE = "Portugal Joga Melhor Sem Cristiano Ronaldo? O Fim da Novela Após 2 Vitórias!"

SCRIPT = (
    "Dois jogos sem Cristiano Ronaldo, duas vitórias e classificação antecipada para os quartos de final! "
    "Os números de Portugal sem o capitão chocaram o futebol mundial. "
    "Primeiro, uma goleada histórica de 4 a 2 contra a Dinamarca. "
    "Depois, vitória dramática sobre a Noruega para carimbar a vaga, com Gonçalo Ramos, Vitinha e João Félix dando um show de intensidade! "
    "Jorge Jesus provou que suas convicções táticas funcionam, deixando o retorno de Cristiano aos 41 anos cada vez mais distante. "
    "Para você: é o ponto final definitivo de Cristiano Ronaldo na seleção de Portugal? "
    "Comente o que você acha e se inscreva agora no Futebol Invisível!"
)

QUERIES = [
    "Portugal national team celebration goal match 2026",
    "Goncalo Ramos Joao Felix Portugal celebrate",
    "Jorge Jesus treinador sorrindo comemorando Portugal",
    "Cristiano Ronaldo serious watching Portugal match",
    "Portugal fans waving flag stadium cheering victory",
    "Cristiano Ronaldo Portugal jersey sad walk away"
]

ZOOM_EFFECTS = [
    "zoompan=z='min(zoom+0.0015,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/4-(ih/zoom/4)':s=1080x1920:fps=30",
    "zoompan=z='max(1.2-0.0015*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.0015,1.2)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.002,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.0012,1.18)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
]

def download_and_crop(url, out_path):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200 and len(res.content) > 5000:
            temp = out_path + ".tmp"
            with open(temp, "wb") as f:
                f.write(res.content)
            with Image.open(temp) as img:
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
            if os.path.exists(temp):
                os.remove(temp)
            return True
    except Exception:
        pass
    return False

def generate_finale_video():
    logger.info(f"Produzindo o desfecho final da novela CR7: {TITLE}")
    base_dir = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", VIDEO_ID)
    clips_dir = os.path.join(base_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    ddgs = DDGS()
    saved_images = []
    
    for i, q in enumerate(QUERIES):
        img_out = os.path.join(base_dir, f"cena_{i+1:02d}.jpg")
        if os.path.exists(img_out):
            saved_images.append(img_out)
            continue
            
        logger.info(f"Buscando foto real {i+1}: '{q}'...")
        try:
            results = list(ddgs.images(q, max_results=8))
        except Exception:
            results = []
            
        success = False
        for r in results:
            url = r.get("image")
            if url and download_and_crop(url, img_out):
                saved_images.append(img_out)
                success = True
                break
        time.sleep(1)
        
    logger.info(f"Imagens reais coletadas: {len(saved_images)}. Criando animação dinâmica...")
    clips = []
    for i, img in enumerate(saved_images):
        out_clip = os.path.join(clips_dir, f"clip_{i+1:02d}.mp4")
        if not os.path.exists(out_clip):
            effect = ZOOM_EFFECTS[i % len(ZOOM_EFFECTS)]
            cmd = [
                FFMPEG, "-y",
                "-loop", "1",
                "-i", img,
                "-vf", f"{effect},format=yuv420p",
                "-t", "4",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p",
                out_clip
            ]
            subprocess.run(cmd, capture_output=True)
        clips.append(os.path.abspath(out_clip))
        
    materials_arg = ",".join(clips)
    dest_video = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "05_Portugal_Sem_CR7_Fim_Da_Novela.mp4")
    
    cmd_cli = [
        sys.executable,
        "cli.py",
        "--video-subject", TITLE,
        "--video-script", SCRIPT,
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
    
    logger.info("Renderizando o vídeo do desfecho com narração e legendas dinâmicas...")
    subprocess.run(cmd_cli)
    
    import glob
    tasks = sorted(glob.glob("storage/tasks/*/final-1.mp4"), key=os.path.getmtime, reverse=True)
    if tasks:
        import shutil
        shutil.copy(tasks[0], dest_video)
        logger.success(f"VÍDEO DO FIM DA NOVELA ENTREGUE EM: {dest_video}")

if __name__ == '__main__':
    generate_finale_video()
