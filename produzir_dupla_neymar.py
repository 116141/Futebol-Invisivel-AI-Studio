import os
import sys
import time
import requests
import subprocess
import imageio_ffmpeg
import urllib.parse
from ddgs import DDGS
from PIL import Image, ImageDraw
from loguru import logger
from app.services import voice

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

DOC_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "doc_neymar_completo")
CLIPS_DIR = os.path.join(DOC_DIR, "clips")
VIDEOS_PRONTOS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos")
SHORTS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")

os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(VIDEOS_PRONTOS_DIR, exist_ok=True)
os.makedirs(SHORTS_DIR, exist_ok=True)

TITLE_DOC = "A Promessa Quebrada: Como Neymar Jr Destruiu Seu Próprio Destino"

CHAPTERS = [
    {
        "chapter": 1,
        "title": "O Menino da Vila e o Herdeiro de Pelé",
        "script": (
            "No início dos anos dois mil e dez, o futebol mundial testemunhou o surgimento de um fenômeno raro. "
            "Com cabelos espetados, dribles desconcertantes e uma alegria contagiante, Neymar Júnior resgatava a essência do futebol brasileiro. "
            "Pelo Santos, ele conquistou a Copa Libertadores e desafiou os maiores clubes do planeta. "
            "Pelé, Zico e Ronaldo apontavam para o jovem menino da Vila e cravavam: ali estava o futuro melhor jogador do mundo, "
            "o homem destinado a trazer o hexacampeonato e enfileirar Bolas de Ouro."
        ),
        "queries": [
            "Neymar Jr Santos FC smile celebration Libertadores 2011",
            "Neymar Jr young boy Santos dribbling skills ball",
            "Neymar Jr Pele hugging Santos Vila Belmiro emotional",
            "Neymar Jr Santos trophy lift celebration crowd fans",
            "Neymar Jr mohawk hairstyle Santos iconic match action",
            "Santos fans cheering Vila Belmiro stadium flare smoke",
            "Neymar Jr smiling Santos jersey press conference presentation",
            "Neymar Jr dancing celebration Santos goal pitch",
            "Neymar Jr vs Kashiwa Reysol Club World Cup spectacular goal",
            "Neymar Jr walking tunnel Santos stadium lights portrait"
        ]
    },
    {
        "chapter": 2,
        "title": "A Tríplice Coroa e a Sombra de Messi",
        "script": (
            "A chegada à Europa confirmou todas as expectativas. Ao lado de Lionel Messi e Luis Suárez no Barcelona, "
            "Neymar formou o trio MSN, considerado o ataque mais devastador da história moderna. "
            "Em dois mil e quinze, ele conquistou a tríplice coroa europeia, marcando o gol do título da Champions League em Berlim. "
            "Dois anos depois, ele foi o arquiteto da maior virada da história da competição contra o PSG. "
            "Mas no dia seguinte, a foto histórica nos jornais não era dele, era de Messi nos braços da torcida. "
            "O ego falou mais alto: Neymar percebeu que, para ser o número um, precisava fugir da sombra do rei."
        ),
        "queries": [
            "Neymar Messi Suarez MSN Barcelona celebrating hug goal",
            "Neymar Jr Champions League trophy Berlin 2015 celebration",
            "Neymar Jr 6-1 PSG remontada epic celebration Camp Nou",
            "Lionel Messi celebration PSG 6-1 fans arms open iconic",
            "Neymar Jr Barcelona jersey freekick action Camp Nou match",
            "Camp Nou stadium Barcelona aerial night crowd banner",
            "Neymar Jr serious looking thoughtful Barcelona locker room tunnel",
            "Neymar Jr kissing Champions League gold medal podium",
            "Neymar Jr and Messi smiling training session Barcelona pitch",
            "Neymar Jr walking away Barcelona shadow stadium dark"
        ]
    },
    {
        "chapter": 3,
        "title": "A Gaiola de Ouro em Paris e as Lesões Devastadoras",
        "script": (
            "Em agosto de dois mil e dezessete, o Paris Saint-Germain pagou duzentos e vinte e dois milhões de euros, "
            "quebrando todos os recordes financeiros da história da humanidade. Neymar chegava a Paris com status de imperador. "
            "Mas o sonho rapidamente se transformou em pesadelo. Brigas internas por cobranças de pênaltis com Cavani, "
            "a ascensão supersônica de Kylian Mbappé e, acima de tudo, a fragilidade física. "
            "Metatarsos fraturados, tornozelos rompidos e ausências nos jogos mais decisivos da temporada. "
            "A festa de aniversário anual no Brasil se tornou mais comentada do que suas atuações na Champions League."
        ),
        "queries": [
            "Neymar Jr PSG presentation Parc des Princes jersey fireworks",
            "Neymar Jr Cavani penalty dispute discussion PSG pitch",
            "Neymar Jr crying injured ankle PSG stretcher medical",
            "Neymar Jr crutches red suit birthday party Paris VIP",
            "Kylian Mbappe Neymar Jr serious tension PSG match",
            "Neymar Jr crying Lisbon Champions League final 2020 Bayern loss",
            "Neymar Jr sitting alone turf PSG Parc des Princes disappointed",
            "Parc des Princes Paris stadium night lights aerial ultras",
            "Neymar Jr doctor surgery hospital ankle rehabilitation training",
            "Neymar Jr Paris Saint-Germain jersey head down rain dark"
        ]
    },
    {
        "chapter": 4,
        "title": "A Arábia Saudita, O Cruzado Rompido e o Crepúsculo",
        "script": (
            "A última chance de redenção na Copa do Mundo de dois mil e vinte e dois terminou em tragédia contra a Croácia. "
            "O gol antológico na prorrogação não bastou, e o Brasil caiu nos pênaltis. "
            "Sem mais mercado na elite europeia, Neymar aceitou uma fortuna obscena do Al-Hilal da Arábia Saudita. "
            "Poucas semanas depois, o rompimento do ligamento cruzado anterior encerrou prematuramente sua temporada. "
            "Aos trinta e quatro anos, o homem que nasceu para suceder Pelé e superar Messi se tornou o maior desperdício de talento da era moderna. "
            "Neymar Jr conquistou bilhões, mas perdeu a eternidade."
        ),
        "queries": [
            "Neymar Jr crying Croatia World Cup 2022 Qatar tears grass",
            "Neymar Jr goal Croatia Qatar extra time celebration dance",
            "Alves Marquinhos Neymar devastated ground penalty shootout Brazil",
            "Neymar Jr Al Hilal presentation blue jersey stadium fireworks Riyadh",
            "Neymar Jr injured knee screaming pain Uruguay match Brazil 2023",
            "Neymar Jr rehabilitation gym physical therapy surgery scar",
            "Neymar Jr cruise ship party poker game luxury lifestyle",
            "Brazil national team jersey number 10 Neymar back view tunnel",
            "Neymar Jr looking sky stadium sunset emotional dramatic",
            "Neymar Jr iconic portrait serious dark background legendary"
        ]
    }
]

BLOCKED_DOMAINS = [
    "alamy", "gettyimages", "shutterstock", "istockphoto",
    "stock.adobe", "depositphotos", "dreamstime", "123rf"
]

def is_domain_clean(url):
    domain = urllib.parse.urlparse(url).netloc.lower()
    return not any(b in domain for b in BLOCKED_DOMAINS)

def download_and_crop_16_9(url, out_path):
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
                target_ratio = 16 / 9
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

def collect_archive():
    ddgs = DDGS()
    total_images = []
    for chap in CHAPTERS:
        logger.info(f"\n[Capítulo {chap['chapter']}] {chap['title']}...")
        chap_folder = os.path.join(DOC_DIR, f"capitulo_{chap['chapter']}")
        os.makedirs(chap_folder, exist_ok=True)
        for i, q in enumerate(chap['queries']):
            out_file = os.path.join(chap_folder, f"cena_{i+1:02d}.jpg")
            if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
                total_images.append(out_file)
                continue
            search_query = f"{q} -alamy -getty -shutterstock -stock -watermark"
            try:
                results = list(ddgs.images(search_query, max_results=12))
            except Exception:
                results = []
            for r in results:
                url = r.get("image")
                if url and is_domain_clean(url) and download_and_crop_16_9(url, out_file):
                    logger.success(f"Foto limpa salva: {out_file}")
                    total_images.append(out_file)
                    break
            time.sleep(1)
    return total_images

def animate_clips(image_files):
    logger.info("Criando clipes animados de TV em Full HD...")
    clips = []
    effects = [
        "zoompan=z='min(zoom+0.0015,1.2)':d=180:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
        "zoompan=z='max(1.2-0.0012*on,1.0)':d=180:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
        "zoompan=z='min(zoom+0.0018,1.25)':d=180:x='iw/3-(iw/zoom/3)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
        "zoompan=z='min(zoom+0.0015,1.2)':d=180:x='2*iw/3-(2*iw/zoom/3)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30"
    ]
    for i, img in enumerate(image_files):
        out_clip = os.path.join(CLIPS_DIR, f"clip_{i+1:03d}.mp4")
        if not os.path.exists(out_clip) or os.path.getsize(out_clip) < 10000:
            eff = effects[i % len(effects)]
            cmd = [
                FFMPEG, "-y",
                "-loop", "1",
                "-i", img,
                "-vf", f"{eff},format=yuv420p",
                "-t", "6",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p",
                out_clip
            ]
            subprocess.run(cmd, capture_output=True)
        clips.append(os.path.abspath(out_clip))
    return clips

def format_time_ass(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def build_documentary(clips):
    full_script = " ".join([c["script"] for c in CHAPTERS])
    audio_file = os.path.join(DOC_DIR, "audio_neymar.mp3")
    logger.info("Gerando locução profissional pt-BR-AntonioNeural...")
    sm = voice.azure_tts_v1(full_script, "pt-BR-AntonioNeural", 1.0, audio_file)

    ass_file = "neymar_legendas.ass"
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Arial Black,50,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,30,30,80,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    events = []
    if sm and hasattr(sm, 'offset'):
        words = list(sm.offset)
        step = 6
        for i in range(0, len(words), step):
            chunk = words[i:i+step]
            t_start = chunk[0][0] / 1000.0
            t_end = chunk[-1][1] / 1000.0
            text_str = " ".join([c[2].lower() for c in chunk])
            events.append(f"Dialogue: 0,{format_time_ass(t_start)},{format_time_ass(t_end)},Default,,0,0,0,,{text_str}\n")
    
    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(header + "".join(events))

    concat_list = os.path.join(DOC_DIR, "concat_neymar.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.replace('\\', '/')}'\n")

    combined_video = os.path.join(DOC_DIR, "combined_neymar.mp4")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", combined_video
    ], capture_output=True)

    final_output = os.path.join(VIDEOS_PRONTOS_DIR, "DOCUMENTARIO_NEYMAR_A_PROMESSA_QUEBRADA.mp4")
    logger.info("Renderizando documentário legendado do Neymar...")
    cmd_final = [
        FFMPEG, "-y",
        "-i", combined_video,
        "-i", audio_file,
        "-vf", f"ass={ass_file}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        final_output
    ]
    subprocess.run(cmd_final, capture_output=True)

    # Limpeza
    import shutil
    shutil.rmtree(DOC_DIR, ignore_errors=True)
    if os.path.exists(ass_file):
        os.remove(ass_file)
    logger.success(f"DOCUMENTÁRIO DO NEYMAR ENTREGUE EM: {final_output}")

def build_short():
    logger.info("Produzindo Short conectado ao Documentário do Neymar...")
    short_temp = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "temp_short_neymar")
    os.makedirs(short_temp, exist_ok=True)
    
    short_script = (
        "Como Neymar Jr destruiu seu próprio destino e jogou fora a chance de ser o melhor do mundo? "
        "Em dois mil e quinze ele venceu a Champions com o Barcelona e humilhou a Europa. "
        "Mas para sair da sombra de Messi, ele foi para o PSG pelo maior valor da história. "
        "O resultado? Brigas internas, festas polêmicas e lesões que destruíram seu corpo. "
        "O documentário completo e chocante da queda de Neymar já está no ar no canal! "
        "Clique no link do primeiro comentário fixado para assistir agora e se inscreva no Futebol Invisível!"
    )
    
    short_queries = [
        "Neymar Jr Champions League trophy Berlin 2015 celebration",
        "Neymar Jr 222 million PSG presentation Parc des Princes",
        "Neymar Jr crying injured ankle PSG stretcher medical",
        "Neymar Jr cruise ship party sunglasses luxury lifestyle",
        "Neymar Jr crying Croatia World Cup 2022 Qatar tears grass",
        "Neymar Jr Al Hilal presentation blue jersey stadium"
    ]
    
    ddgs = DDGS()
    saved = []
    for i, q in enumerate(short_queries):
        img_out = os.path.join(short_temp, f"foto_{i+1:02d}.jpg")
        sq = f"{q} -alamy -getty -shutterstock -stock -watermark"
        try:
            results = list(ddgs.images(sq, max_results=12))
        except Exception:
            results = []
        for r in results:
            url = r.get("image")
            if url and is_domain_clean(url):
                # Download vertical
                headers = {"User-Agent": "Mozilla/5.0"}
                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    if res.status_code == 200 and len(res.content) > 5000:
                        temp_p = img_out + ".tmp"
                        with open(temp_p, "wb") as f:
                            f.write(res.content)
                        with Image.open(temp_p) as img:
                            img = img.convert("RGB")
                            w, h = img.size
                            tr = 1080 / 1920
                            if w/h > tr:
                                nw = int(h * tr)
                                left = (w - nw) // 2
                                img = img.crop((left, 0, left + nw, h))
                            else:
                                nh = int(w / tr)
                                top = (h - nh) // 2
                                img = img.crop((0, top, w, top + nh))
                            img = img.resize((1080, 1920), Image.LANCZOS)
                            img.save(img_out, "JPEG", quality=95)
                        if os.path.exists(temp_p):
                            os.remove(temp_p)
                        saved.append(img_out)
                        break
                except Exception:
                    pass
        time.sleep(1)

    # Clipes
    short_clips = []
    zoom_effects = [
        "zoompan=z='min(zoom+0.0018,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
        "zoompan=z='max(1.25-0.0018*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/4-(ih/zoom/4)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.0018,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
        "zoompan=z='max(1.22-0.0015*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
    ]
    for i, img in enumerate(saved):
        c_out = os.path.join(short_temp, f"clip_{i+1:02d}.mp4")
        eff = zoom_effects[i % len(zoom_effects)]
        cmd = [
            FFMPEG, "-y", "-loop", "1", "-i", img,
            "-vf", f"{eff},format=yuv420p", "-t", "6",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", c_out
        ]
        subprocess.run(cmd, capture_output=True)
        short_clips.append(c_out)

    s_concat = os.path.join(short_temp, "concat.txt")
    with open(s_concat, "w", encoding="utf-8") as f:
        for c in short_clips:
            f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")

    v_base = os.path.join(short_temp, "video_base.mp4")
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", s_concat, "-c", "copy", v_base], capture_output=True)

    a_short = os.path.join(short_temp, "audio.mp3")
    sm_s = voice.azure_tts_v1(short_script, "pt-BR-AntonioNeural", 1.0, a_short)

    ass_s = "temp_neymar_short.ass"
    h_s = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Impact,82,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,40,40,320,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    evs = []
    if sm_s and hasattr(sm_s, 'offset'):
        w_list = list(sm_s.offset)
        for i in range(0, len(w_list), 4):
            chk = w_list[i:i+4]
            t1 = chk[0][0] / 1000.0
            t2 = chk[-1][1] / 1000.0
            txt = " ".join([c[2].upper() for c in chk])
            evs.append(f"Dialogue: 0,{format_time_ass(t1)},{format_time_ass(t2)},Default,,0,0,0,,{txt}\n")
    with open(ass_s, "w", encoding="utf-8") as f:
        f.write(h_s + "".join(evs))

    final_short = os.path.join(SHORTS_DIR, "SHORT_04_NEYMAR_A_PROMESSA_QUEBRADA.mp4")
    cmd_s_render = [
        FFMPEG, "-y", "-i", v_base, "-i", a_short,
        "-vf", f"ass={ass_s}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        final_short
    ]
    res = subprocess.run(cmd_s_render, capture_output=True, text=True)
    if not os.path.exists(final_short):
        logger.error(f"Erro FFmpeg short: {res.stderr[:400]}")
    if os.path.exists(ass_s):
        os.remove(ass_s)
    import shutil
    shutil.rmtree(short_temp, ignore_errors=True)
    logger.success(f"SHORT DO NEYMAR ENTREGUE EM: {final_short}")

if __name__ == "__main__":
    imgs = collect_archive()
    clips = animate_clips(imgs)
    build_documentary(clips)
    build_short()
