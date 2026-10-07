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

DOC_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "doc_manchester_city_completo")
CLIPS_DIR = os.path.join(DOC_DIR, "clips")
VIDEOS_PRONTOS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos")
os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(VIDEOS_PRONTOS_DIR, exist_ok=True)

TITLE = "A Farsa dos Bilhões: O Julgamento Que Pode Destruir o Manchester City"

# Roteiro cinematográfico dividido em 4 Capítulos (~8 a 9 minutos)
CHAPTERS = [
    {
        "chapter": 1,
        "title": "A Ascensão do Dinheiro Infinito",
        "script": (
            "Durante mais de um século, o futebol inglês foi governado por tradição, suor e paciência. "
            "Mas em dois mil e oito, a história mudou para sempre. Um clube modesto e esquecido de Manchester "
            "foi adquirido por Sheikh Mansour e o fundo soberano de Abu Dhabi. Em questão de semanas, "
            "o dinheiro começou a jorrar como nunca se viu no esporte mundial. Estádios foram modernizados, "
            "centros de treinamento galácticos foram construídos e contratações astronômicas abalaram a Europa. "
            "O Manchester City saía da sombra do rival United para se tornar uma potência imparável. "
            "Mas por trás de cada taça erguida e de cada sorriso reluzente nos gramados, "
            "uma teia invisível de contratos secretos, empresas de fachada e manobras contábeis começava a ser tecida."
        ),
        "queries": [
            "Sheikh Mansour buying Manchester City 2008 press conference",
            "Etihad Stadium Manchester City construction modern",
            "Robinho signing Manchester City historic arrival",
            "Manchester City old Maine Road stadium nostalgic",
            "Abu Dhabi United Group Sheikh Mansour luxury",
            "Carlos Tevez Manchester City welcome to Manchester billboard",
            "Manchester City training ground Etihad campus aerial 4k",
            "English Premier League vintage match 2000s football",
            "Manchester City fans celebration old days",
            "Premier League money investment cash football finance"
        ]
    },
    {
        "chapter": 2,
        "title": "A Máquina Quase Perfeita e a Chegada de Guardiola",
        "script": (
            "Com a chegada de Pep Guardiola em dois mil e dezesseis, o Manchester City encontrou o cérebro que faltava. "
            "Guardiola não queria apenas vencer: ele queria humilhar os adversários com um futebol de posse, perfeição tática "
            "e intensidade obsessiva. O clube quebrou a barreira dos cem pontos na Premier League, conquistou a tão sonhada "
            "Champions League e colocou Erling Haaland e Kevin De Bruyne no topo do mundo. "
            "Para quem olhava de fora, parecia a coroação do mérito esportivo. No entanto, nos escritórios da Premier League "
            "em Londres, uma equipe de advogados e auditores fiscais trabalhava em silêncio. "
            "Documentos confidenciais vazados pelo Football Leaks revelavam que os valores de patrocínio "
            "não vinham de empresas reais, mas diretamente do governo dos Emirados Árabes para burlar as regras financeiras."
        ),
        "queries": [
            "Pep Guardiola presentation Manchester City manager 2016",
            "Pep Guardiola tactical board coaching training pitch",
            "Erling Haaland Kevin De Bruyne goal celebration Manchester City",
            "Manchester City Champions League trophy Istanbul night celebration",
            "Rui Pinto Football Leaks hacker documents screen",
            "Premier League audit finance paper files investigation",
            "Etihad Airways sponsorship plane Manchester City logo",
            "Pep Guardiola intense shouting tactical instructions match",
            "Manchester City players trophy parade bus crowd",
            "London financial district Canary Wharf corporate legal"
        ]
    },
    {
        "chapter": 3,
        "title": "O Julgamento do Século: 114 Acusações",
        "script": (
            "Após anos de batalhas jurídicas nos tribunais, a bomba explodiu com força devastadora. "
            "A Premier League apresentou oficialmente cento e quinze acusações formais contra o Manchester City por fraudes financeiras. "
            "E agora, a comissão independente julgou o clube como culpado em cento e catorze delas! "
            "Nunca na história dos esportes modernos uma instituição foi condenada em tantas violações ao mesmo tempo. "
            "O pânico tomou conta dos bastidores da Inglaterra. As punições possíveis são aterrorizantes: "
            "a perda de até sessenta pontos na tabela, a cassação de títulos conquistados na última década, "
            "multas de centenas de milhões de libras e até mesmo o rebaixamento sumário para divisões inferiores. "
            "O clube mais poderoso da atualidade viu seu futuro colocado na beira do abismo."
        ),
        "queries": [
            "Premier League headquarters London entrance building legal",
            "Manchester City stadium empty dark dramatic lighting",
            "Judge courtroom gavel law trial justice financial",
            "Premier League trophy court hearing controversy",
            "Newspaper headlines Manchester City guilty charges 115",
            "English football fans protest money modern football",
            "Erling Haaland sad walking off pitch disappointed",
            "Manchester City legal team lawyers court London suit",
            "Etihad Stadium dark sky thunderstorm dramatic",
            "Financial fair play UEFA rule book documents"
        ]
    },
    {
        "chapter": 4,
        "title": "A Resistência de Guardiola e o Legado Manchado",
        "script": (
            "Diante do maior escândalo da história do futebol, os holofotes se voltaram para Pep Guardiola. "
            "Muitos apostavam que o técnico abandonaria o barco. Mas em uma coletiva histórica, com o olhar firme e a voz embargada, "
            "Guardiola declarou guerra aberta contra os outros dezenove clubes da liga, prometendo que lutará até a última instância. "
            "Mesmo que o City consiga reduzir as penas através de recursos judiciais intermináveis, uma coisa é certa: "
            "o legado que parecia intocável agora carrega uma mancha eterna de dúvida. "
            "E você? Acredita que o Manchester City deve ser punido com o rebaixamento e perda de títulos, "
            "ou tudo isso é apenas um boicote da velha guarda do futebol inglês contra o novo império? "
            "Deixe sua opinião nos comentários, compartilhe este documentário e se inscreva no canal Futebol Invisível."
        ),
        "queries": [
            "Pep Guardiola serious press conference documentary close up",
            "Pep Guardiola angry gesturing microphone press room",
            "Manchester City fans waving flags blue smoke stadium",
            "Premier League table standings points deduction",
            "Pep Guardiola walking alone dark stadium tunnel solitary",
            "Premier League rival managers Arteta Klopp laughing",
            "Manchester City crest logo stadium wall metallic",
            "Football pitch night rain dramatic floodlights cinematic",
            "Etihad Stadium sunset golden hour dramatic clouds",
            "Soccer fans talking debating pub stadium crowd"
        ]
    }
]

ZOOM_EFFECTS = [
    "zoompan=z='min(zoom+0.0006,1.14)':d=180:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
    "zoompan=z='max(1.14-0.0006*on,1.0)':d=180:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
    "zoompan=z='min(zoom+0.0008,1.15)':d=180:x='iw/3-(iw/zoom/3)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
    "zoompan=z='min(zoom+0.0007,1.12)':d=180:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1920x1080:fps=30"
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

def collect_massive_archive():
    ddgs = DDGS()
    total_images = []
    
    for chap in CHAPTERS:
        logger.info(f"\nColetando 10 imagens reais para o Capítulo {chap['chapter']}: {chap['title']}...")
        chap_folder = os.path.join(DOC_DIR, f"capitulo_{chap['chapter']}")
        os.makedirs(chap_folder, exist_ok=True)
        
        for i, q in enumerate(chap['queries']):
            out_file = os.path.join(chap_folder, f"cena_{i+1:02d}.jpg")
            if os.path.exists(out_file):
                total_images.append(out_file)
                continue
                
            logger.info(f"Capítulo {chap['chapter']} [{i+1}/10]: '{q}'...")
            try:
                results = list(ddgs.images(q, max_results=8))
            except Exception:
                results = []
                
            for r in results:
                url = r.get("image")
                if url and download_and_crop_16_9(url, out_file):
                    logger.success(f"Foto Full HD 16:9 salva: {out_file}")
                    total_images.append(out_file)
                    break
            time.sleep(1)
            
    logger.success(f"\nACERVO COMPLETO DE FOTOS REAIS: {len(total_images)} imagens!")
    return total_images

def animate_all_clips(images):
    clips = []
    logger.info("Transformando todas as fotos em clipes cinematográficos de TV...")
    for i, img in enumerate(images):
        out_clip = os.path.join(CLIPS_DIR, f"clip_{i+1:03d}.mp4")
        if not os.path.exists(out_clip):
            effect = ZOOM_EFFECTS[i % len(ZOOM_EFFECTS)]
            cmd = [
                FFMPEG, "-y",
                "-loop", "1",
                "-i", img,
                "-vf", f"{effect},format=yuv420p",
                "-t", "6",  # 6 segundos por cena com movimento fluido
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p",
                out_clip
            ]
            subprocess.run(cmd, capture_output=True)
        clips.append(os.path.abspath(out_clip))
    return clips

def run_master_documentary():
    # 1. Coleta das 40 fotos reais
    images = collect_massive_archive()
    
    # 2. Animação de todas as fotos em clipes 16:9
    clips = animate_all_clips(images)
    materials_arg = ",".join(clips)
    
    # 3. Roteiro unificado de 8 minutos
    full_script = " ".join([chap['script'] for chap in CHAPTERS])
    
    output_video = os.path.join(VIDEOS_PRONTOS_DIR, "DOCUMENTARIO_MANCHESTER_CITY_A_FARSA_DOS_BILHOES.mp4")
    
    cmd_cli = [
        sys.executable,
        "cli.py",
        "--video-subject", TITLE,
        "--video-script", full_script,
        "--video-source", "local",
        "--video-materials", materials_arg,
        "--voice-name", "pt-BR-AntonioNeural",
        "--video-aspect", "16:9",
        "--video-clip-duration", "6",
        "--video-concat-mode", "sequential",
        "--font-size", "44",
        "--text-fore-color", "#FFFFFF",
        "--stroke-color", "#000000",
        "--stroke-width", "1.5"
    ]
    
    logger.info("\nIniciando renderização do Grande Documentário de 8 minutos em 16:9 Full HD...")
    subprocess.run(cmd_cli)
    
    import glob
    tasks = sorted(glob.glob("storage/tasks/*/final-1.mp4"), key=os.path.getmtime, reverse=True)
    if tasks:
        import shutil
        shutil.copy(tasks[0], output_video)
        logger.success(f"DOCUMENTÁRIO MASTER ENTREGUE COM SUCESSO EM: {output_video}")
        
        # LIMPEZA AUTOMÁTICA DE MEMÓRIA / DISCO
        logger.info("Executando limpeza automática de memória (fotos, clips e caches temporários)...")
        try:
            if os.path.exists(DOC_DIR):
                shutil.rmtree(DOC_DIR)
                logger.success("Pasta de fotos e clipes temporários removida!")
            for t in glob.glob("storage/tasks/*"):
                try:
                    shutil.rmtree(t)
                except Exception:
                    pass
            logger.success("Cache intermediário de renderização limpo com sucesso! Apenas o vídeo final foi mantido.")
        except Exception as e:
            logger.warning(f"Aviso durante a limpeza de memória: {e}")

if __name__ == '__main__':
    run_master_documentary()

