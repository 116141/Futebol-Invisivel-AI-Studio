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

# Os 3 temas atualizados da Bola de Ouro 2026 com fotos reais e dados oficiais
BALLON_DOR_VIDEOS = [
    {
        "id": "video_06_kane_vs_yamal_ballon_dor",
        "title": "Harry Kane ou Lamine Yamal? A Guerra Pela Bola de Ouro 2026!",
        "script": (
            "A cerimônia da Bola de Ouro acontece em poucos dias e a votação dos jornalistas está oficialmente encerrada! "
            "De um lado, Harry Kane com uma temporada lendária de sessenta e um gols pelo Bayern de Munique, quebrando todos os recordes. "
            "Do outro lado, o fenômeno Lamine Yamal de dezenove anos, campeão do mundo pela Espanha e o jogador mais decisivo do Barcelona! "
            "A Europa está completamente dividida: o prêmio deve premiar a máquina de gols do Bayern ou a magia do garoto espanhol? "
            "Para você: quem merece erguer a Bola de Ouro em Londres? Kane ou Lamine Yamal? "
            "Comente o seu favorito e se inscreva no canal Futebol Invisível!"
        ),
        "queries": [
            "Ballon d'Or trophy gold official presentation",
            "Harry Kane Bayern Munich celebrating goal 2026",
            "Lamine Yamal Barcelona match action 2026",
            "Harry Kane serious trophy podium",
            "Lamine Yamal Spain World Cup celebration smile",
            "Ballon d'Or ceremony stage London"
        ]
    },
    {
        "id": "video_07_mbappe_injustica_ballon_dor",
        "title": "Mbappé Vai Ser Injustiçado na Bola de Ouro 2026? Os Números Reais!",
        "script": (
            "Kylian Mbappé pode ser a maior vítima da história recente da Bola de Ouro! "
            "O camisa nove do Real Madrid destruiu a temporada: foi artilheiro absoluto da Champions League, "
            "conquistou a Chuteira de Ouro da Copa do Mundo e marcou gols decisivos em todas as finais. "
            "Mesmo com estatísticas individuais impecáveis, os vazamentos colocam Mbappé fora do topo por causa das decisões dos jurados europeus. "
            "Afinal, o que mais o francês precisa fazer para conquistar a sua primeira Bola de Ouro na carreira? "
            "Você acha que Mbappé merece o prêmio ou ele foi superado por Kane e Yamal? Deixe sua opinião e siga o Futebol Invisível!"
        ),
        "queries": [
            "Kylian Mbappe Real Madrid celebrating goal 2026",
            "Kylian Mbappe Champions League trophy golden boot",
            "Kylian Mbappe serious face Real Madrid match",
            "Kylian Mbappe France national team World Cup action",
            "Real Madrid Santiago Bernabeu stadium crowd",
            "Ballon d'Or trophy close up golden shining"
        ]
    },
    {
        "id": "video_08_rodri_dembele_zebra_ballon_dor",
        "title": "Rodri e Dembélé Podem Chocar o Mundo de Novo na Bola de Ouro?",
        "script": (
            "Enquanto o mundo só fala dos atacantes, uma reviravolta silenciosa pode chocar o futebol na Bola de Ouro! "
            "Rodri foi eleito o melhor jogador da Copa do Mundo, controlando o meio-campo com maestria tática absoluta. "
            "E Ousmane Dembélé, o atual dono da Bola de Ouro após o título europeu com o PSG, corre por fora com números impressionantes. "
            "Muitos especialistas afirmam que os jurados da France Football adoram premiar a consistência e os títulos em vez do hype midiático. "
            "Será que teremos uma surpresa histórica em Londres? "
            "Quem é o seu verdadeiro vencedor da temporada? Comente agora e faça parte do canal Futebol Invisível!"
        ),
        "queries": [
            "Rodri Spain football World Cup Golden Ball trophy",
            "Ousmane Dembele Ballon d'Or trophy celebration",
            "Rodri Manchester City Spain tactical pass action",
            "Ousmane Dembele Paris Saint Germain Champions League match",
            "France Football Ballon d'Or ceremony red carpet",
            "Football stadium fans cheering drama"
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

def produce_ballon_dor_batch():
    output_dir = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos")
    os.makedirs(output_dir, exist_ok=True)
    ddgs = DDGS()
    
    for item in BALLON_DOR_VIDEOS:
        logger.info(f"\n{'='*60}\nINICIANDO VÍDEO BOLA DE OURO: {item['title']}\n{'='*60}")
        base_dir = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", item['id'])
        clips_dir = os.path.join(base_dir, "clips")
        os.makedirs(clips_dir, exist_ok=True)
        
        saved_images = []
        for i, q in enumerate(item['queries']):
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
            
        logger.info(f"Imagens reais prontas ({len(saved_images)}). Convertendo em clipes dinâmicos com Ken Burns...")
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
        dest_video = os.path.join(output_dir, f"{item['id']}.mp4")
        
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
        
        import glob
        tasks = sorted(glob.glob("storage/tasks/*/final-1.mp4"), key=os.path.getmtime, reverse=True)
        if tasks:
            import shutil
            shutil.copy(tasks[0], dest_video)
            logger.success(f"VÍDEO DA BOLA DE OURO ENTREGUE: {dest_video}")
            
    logger.success("TRIO DA BOLA DE OURO CONCLUÍDO COM SUCESSO!")

if __name__ == '__main__':
    produce_ballon_dor_batch()
