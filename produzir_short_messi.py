import os
import sys
import time
import requests
import subprocess
import imageio_ffmpeg
import urllib.parse
from ddgs import DDGS
from PIL import Image
from loguru import logger
from app.services import voice

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SHORTS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")
TEMP_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "temp_short_messi")
os.makedirs(SHORTS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

TITLE = "O Segredo de Messi que Quase Destruiu Sua Carreira!"
SCRIPT = (
    "Você sabia que Lionel Messi quase encerrou sua carreira antes de se tornar campeão do mundo? "
    "Em dois mil e dezesseis, após perder duas finais seguidas da Copa América e a Copa de 2014, "
    "Messi chorou em rede nacional e anunciou que nunca mais vestiria a camisa da Argentina. "
    "Ele era vaiado na sua própria terra e chamado de mercenário. "
    "Mas a redenção veio em dose dupla: o título no Maracanã e a lendária taça no Catar! "
    "O documentário completo da vida e do fim da era Messi já está no ar no canal! "
    "Clique no link do primeiro comentário fixado para assistir agora e se inscreva no Futebol Invisível!"
)

QUERIES = [
    "Lionel Messi crying tear Argentina Copa America final 2016",
    "Lionel Messi sad Argentina 2014 World Cup final Germany",
    "Lionel Messi kneeling grass head down weeping",
    "Lionel Messi lifting Copa America 2021 Maracana trophy",
    "Lionel Messi kissing FIFA World Cup trophy Qatar 2022 golden bisht",
    "Lionel Messi Inter Miami stadium cheering fans crowd"
]

ZOOM_EFFECTS = [
    "zoompan=z='min(zoom+0.0018,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/4-(ih/zoom/4)':s=1080x1920:fps=30",
    "zoompan=z='max(1.25-0.0018*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.0018,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
    "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    "zoompan=z='max(1.22-0.0015*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30"
]

BLOCKED_DOMAINS = [
    "alamy", "gettyimages", "shutterstock", "istockphoto", 
    "stock.adobe", "depositphotos", "dreamstime", "123rf"
]

def is_domain_clean(url):
    domain = urllib.parse.urlparse(url).netloc.lower()
    return not any(b in domain for b in BLOCKED_DOMAINS)

def download_and_crop_9_16(url, out_path):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=12)
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

def format_time_ass(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def generate_short():
    logger.info("Iniciando produção do Short conectado ao Documentário de Messi...")
    ddgs = DDGS()
    saved_images = []
    
    for i, q in enumerate(QUERIES):
        img_out = os.path.join(TEMP_DIR, f"foto_{i+1:02d}.jpg")
        if os.path.exists(img_out) and os.path.getsize(img_out) > 10000:
            saved_images.append(img_out)
            continue
            
        clean_q = f"{q} -alamy -getty -shutterstock -stock -watermark"
        logger.info(f"Buscando foto limpa [{i+1}/{len(QUERIES)}]: {q}...")
        try:
            results = list(ddgs.images(clean_q, max_results=15))
        except Exception:
            results = []
            
        for r in results:
            url = r.get("image")
            if url and is_domain_clean(url):
                if download_and_crop_9_16(url, img_out):
                    logger.success(f"Foto vertical 9:16 salva: {img_out}")
                    saved_images.append(img_out)
                    break
        time.sleep(1)

    # Criando clipes animados
    clips = []
    for i, img in enumerate(saved_images):
        out_clip = os.path.join(TEMP_DIR, f"clip_{i+1:02d}.mp4")
        effect = ZOOM_EFFECTS[i % len(ZOOM_EFFECTS)]
        cmd = [
            FFMPEG, "-y",
            "-loop", "1",
            "-i", img,
            "-vf", f"{effect},format=yuv420p",
            "-t", "6",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            out_clip
        ]
        subprocess.run(cmd, capture_output=True)
        clips.append(out_clip)

    concat_file = os.path.join(TEMP_DIR, "concat.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")

    video_base = os.path.join(TEMP_DIR, "video_base.mp4")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file, "-c", "copy", video_base
    ], capture_output=True)

    # Áudio narrado
    audio_file = os.path.join(TEMP_DIR, "audio_short.mp3")
    sm = voice.azure_tts_v1(SCRIPT, "pt-BR-AntonioNeural", 1.0, audio_file)
    
    # Legendas ASS em formato 9:16 (vertical grande no centro/baixo)
    ass_file = os.path.join(TEMP_DIR, "legendas_short.ass")
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Impact,82,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,40,40,320,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    
    events = []
    if sm and hasattr(sm, 'offset'):
        words = list(sm.offset)
        step = 4
        for i in range(0, len(words), step):
            chunk = words[i:i+step]
            t_start = chunk[0][0] / 1000.0
            t_end = chunk[-1][1] / 1000.0
            text_str = " ".join([c[2].upper() for c in chunk])
            events.append(f"Dialogue: 0,{format_time_ass(t_start)},{format_time_ass(t_end)},Default,,0,0,0,,{text_str}\n")
    else:
        # Fallback de legendas caso sm não retorne offsets
        events.append(f"Dialogue: 0,0:00:00.00,0:00:30.00,Default,,0,0,0,,A HISTÓRIA SECRETA DE MESSI\n")

    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(header + "".join(events))

    final_short = os.path.join(SHORTS_DIR, "SHORT_03_MESSI_A_REDENCAO_FINAL.mp4")
    logger.info("Renderizando Short final 9:16 com legendas e logo...")
    cmd_render = [
        FFMPEG, "-y",
        "-i", video_base,
        "-i", audio_file,
        "-vf", f"ass={ass_file}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        final_short
    ]
    subprocess.run(cmd_render, capture_output=True)
    
    # Limpeza
    import shutil
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    logger.success(f"SHORT ENTREGUE COM SUCESSO: {final_short}")

if __name__ == "__main__":
    generate_short()
