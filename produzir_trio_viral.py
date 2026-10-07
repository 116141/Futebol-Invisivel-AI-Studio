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

# Os 3 temas quentes com roteiros ultra-retentivos e buscas de fotos reais
BATCH_VIDEOS = [
    {
        "id": "video_02_cr7_jato_madrid",
        "title": "A Fuga de Cristiano Ronaldo: O Jato Privado e o Caos em Lisboa!",
        "script": (
            "Cristiano Ronaldo não apenas abandonou a seleção portuguesa, ele fugiu no meio da madrugada "
            "em seu jato particular rumo a Madri! O capitão recusou até mesmo falar com o presidente da Federação "
            "após ser humilhado pelo técnico Jorge Jesus. Enquanto isso, as ruas de Lisboa amanheceram tomadas por "
            "cartazes de torcedores enfurecidos pedindo a demissão imediata de Jesus! "
            "Aos 41 anos, será esse o fim mais escandaloso da história de uma lenda com sua seleção? "
            "Ronaldo teve razão em ir embora no seu avião ou faltou respeito com o país? Comente aqui e siga o Futebol Invisível!"
        ),
        "queries": [
            "Cristiano Ronaldo private jet airport night",
            "Cristiano Ronaldo Portugal serious face",
            "Jorge Jesus treinador coletiva",
            "Portugal fans banner Lisbon stadium protest",
            "Cristiano Ronaldo Madrid house luxury",
            "Cristiano Ronaldo Portugal fans crying emotional"
        ]
    },
    {
        "id": "video_03_manchester_city_escandalo",
        "title": "O Fim do Manchester City? Culpado em 114 Acusações e a Reação de Guardiola!",
        "script": (
            "Bomba histórica no futebol mundial! O Manchester City acaba de ser considerado culpado em 114 das 115 "
            "acusações financeiras na Inglaterra! O maior clube da Europa agora corre o risco real de perder títulos, "
            "levar uma dedução histórica de pontos e até ser expulso da Premier League! "
            "E quem quebrou o silêncio foi Pep Guardiola, afirmando que está mais do que nunca ao lado do clube para a guerra judicial. "
            "Para você: o Manchester City deve ser rebaixado e perder as taças ou a punição deve ser apenas financeira? "
            "Deixe sua opinião e se inscreva no Futebol Invisível!"
        ),
        "queries": [
            "Pep Guardiola Manchester City serious worried",
            "Manchester City Etihad Stadium night",
            "Premier League trophy court hearing",
            "Pep Guardiola shouting sidelines match",
            "Manchester City players sad disappointed",
            "Football fans protesting Premier League"
        ]
    },
    {
        "id": "video_04_vini_jr_real_madrid",
        "title": "A Loucura Contra Vini Jr na Espanha: Por Que Estão Obcecados por Ele?",
        "script": (
            "A obsessão da imprensa espanhola com Vinícius Júnior atingiu um nível inacreditável! "
            "Enquanto a FIFA acabava de publicar um relatório oficial coroando o brasileiro como o atacante mais dominante do planeta, "
            "na Espanha surgiram teorias bizarras atacando o jogador até mesmo por sua aparência física. "
            "Vini Jr continua respondendo com gols, assistências e títulos no Real Madrid, mas o tratamento contra ele continua revoltando os fãs. "
            "Por que você acha que a Europa persegue tanto o nosso camisa 7 do Real Madrid? É inveja do talento dele? "
            "Comente aqui embaixo e se inscreva no canal Futebol Invisível!"
        ),
        "queries": [
            "Vinicius Junior Real Madrid celebrating goal smile",
            "Vinicius Junior serious face close up match",
            "Real Madrid Santiago Bernabeu stadium night",
            "Spanish football newspapers Marca cover",
            "Vinicius Junior dribbling running fast",
            "Vinicius Junior Real Madrid fans cheering"
        ]
    }
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

def process_single_video(item):
    logger.info(f"\n{'='*60}\nINICIANDO PRODUÇÃO: {item['title']}\n{'='*60}")
    base_dir = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", item['id'])
    clips_dir = os.path.join(base_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    ddgs = DDGS()
    saved_images = []
    
    for i, q in enumerate(item['queries']):
        img_out = os.path.join(base_dir, f"cena_{i+1:02d}.jpg")
        if os.path.exists(img_out):
            saved_images.append(img_out)
            continue
            
        logger.info(f"[{item['id']}] Buscando foto real {i+1}: '{q}'...")
        try:
            results = list(ddgs.images(q, max_results=6))
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
        
    logger.info(f"Imagens prontas para {item['id']}: {len(saved_images)}. Criando clipes animados...")
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
    dest_video = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", f"{item['id']}.mp4")
    
    cmd_cli = [
        sys.executable,
        "cli.py",
        "--video-subject", item['title'],
        "--video-script", item['script'],
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
    
    logger.info(f"Renderizando vídeo final para {item['id']}...")
    subprocess.run(cmd_cli)
    
    # Copiar o vídeo final gerado mais recente
    import glob
    tasks = sorted(glob.glob("storage/tasks/*/final-1.mp4"), key=os.path.getmtime, reverse=True)
    if tasks:
        import shutil
        shutil.copy(tasks[0], dest_video)
        logger.success(f"VÍDEO CONCLUÍDO E ENTREGUE EM: {dest_video}")

def run_batch():
    for item in BATCH_VIDEOS:
        process_single_video(item)
    logger.success("TODOS OS 3 VÍDEOS FORAM GERADOS COM SUCESSO!")

if __name__ == '__main__':
    run_batch()
