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

DOC_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "doc_espanha_completo")
CLIPS_DIR = os.path.join(DOC_DIR, "clips")
VIDEOS_PRONTOS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos")
SHORTS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")

os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(VIDEOS_PRONTOS_DIR, exist_ok=True)
os.makedirs(SHORTS_DIR, exist_ok=True)

CHAPTERS = [
    {
        "chapter": 1,
        "title": "A Queda do Tiki-Taka Tradicional e o Renascimento",
        "script": (
            "Durante mais de uma década após o título de dois mil e dez, a Espanha se tornou prisioneira do próprio estilo. "
            "Mil passes por jogo, posse estéril e eliminações vexatórias nas Copas de dois mil e dezoito e vinte e dois. "
            "O mundo dizia que o futebol espanhol estava morto e ultrapassado. "
            "Mas nas categorias de base, uma revolução silenciosa estava sendo forjada. "
            "Longe do toque burocrático, uma nova safra de atacantes velozes, audaciosos e dribladores "
            "começava a quebrar todas as regras do manual europeu."
        ),
        "queries": [
            "Spain national team disappointed World Cup 2022 penalty Morocco loss",
            "Xavi Andres Iniesta Spain 2010 golden era celebration nostalgic",
            "Luis de la Fuente coach Spain tactical board serious",
            "La Masia Barcelona academy young boys training pitch",
            "Spain fans waving flags red yellow stadium atmosphere",
            "Rodri Manchester City Spain midfield masterclass serious",
            "Dani Carvajal Spain veteran leader running pitch",
            "Pedri Gavi young Spain midfield talent match action",
            "Santiago Bernabeu Camp Nou modern stadium lights aerial",
            "Spain national team locker room jerseys hanging red"
        ]
    },
    {
        "chapter": 2,
        "title": "O Fenômeno Adolescente: Lamine Yamal e Nico Williams",
        "script": (
            "Com apenas dezesseis anos, um jovem franzino de Rocafonda pegou a bola e mudou a história do esporte. "
            "Lamine Yamal não jogava com medo de veteranos; jogava como quem se diverte na rua. "
            "Ao lado de Nico Williams, a Espanha encontrou duas flechas que destruíram as defesas mais temidas do planeta. "
            "Na Eurocopa, o golaço antológico de Yamal contra a França de Kylian Mbappé calou os críticos "
            "e fez o planeta perceber que um gênio geracional havia nascido para herdar o trono do futebol."
        ),
        "queries": [
            "Lamine Yamal smiling Spain red jersey goal celebration euro",
            "Nico Williams Lamine Yamal dancing laughing celebration Spain",
            "Lamine Yamal wonder goal curved shot France Euro semifinal",
            "Kylian Mbappe disappointed looking Lamine Yamal duel pitch",
            "Lamine Yamal doing 304 Rocafonda hand gesture goal celebration",
            "Spain bench coach Luis de la Fuente celebrating arms open",
            "Nico Williams speed dribbling wing defender past running",
            "Lamine Yamal kissing Euro trophy podium golden confetti",
            "Young Lamine Yamal baby photo with Lionel Messi nostalgic",
            "Lamine Yamal portrait looking forward stadium lights halo"
        ]
    },
    {
        "chapter": 3,
        "title": "A Conquista da Copa de 2026 e a Humilhação em Wembley",
        "script": (
            "O ápice da nova dinastia veio com a conquista histórica da Copa do Mundo de dois mil e vinte e seis. "
            "Vencendo a Argentina de Messi na grande final, a Fúria Vermelha se sagrou bicampeã mundial com autoridade absoluta. "
            "E agora, na Super Data FIFA de outubro, eles provaram que o domínio é eterno. "
            "Em pleno lendário estádio de Wembley, a Espanha de Yamal enfrentou a badalada Inglaterra de Thomas Tuchel, Kane e Bellingham. "
            "O resultado foi mais uma aula tática: vitória por três a dois, dribles desconcertantes "
            "e a imprensa britânica admitindo que a Espanha joga em outra dimensão."
        ),
        "queries": [
            "Spain national team lifting 2026 FIFA World Cup trophy confetti golden",
            "Lamine Yamal holding World Cup trophy golden ball award smiling",
            "Wembley stadium London night match England Spain packed crowd",
            "Harry Kane Jude Bellingham looking sad heads down Wembley",
            "Thomas Tuchel England manager frustrated sidelines shouting",
            "Lamine Yamal dribbling past English defenders Wembley pitch",
            "Rodri Ballon d'Or trophy celebration Spain applause",
            "Spain players celebrating goal Wembley stadium fans red flags",
            "Newspaper headlines England defeated Spain Wembley masterclass",
            "Lamine Yamal Nico Williams hugging emotional trophy pitch"
        ]
    },
    {
        "chapter": 4,
        "title": "O Futuro Pertence à Fúria: Ninguém Consegue Parar a Espanha?",
        "script": (
            "Enquanto gigantes como Brasil, França e Alemanha buscam desesperadamente reconstruir suas identidades, "
            "a Espanha já tem a espinha dorsal mais jovem e dominante das próximas duas décadas. "
            "Com elenco farto, liderança sólida e o maior jovem talento desde Lionel Messi, "
            "o novo império do futebol está consolidado. "
            "A grande pergunta que fica para os amantes do esporte é simples: "
            "alguém será capaz de derrubar a dinastia espanhola antes da próxima década?"
        ),
        "queries": [
            "Spain national team lineup singing national anthem red jerseys pride",
            "Lamine Yamal waving fans stadium exit corridor smiling hero",
            "Spain fans celebrating fountain Cibeles Madrid night aerial flares",
            "Football pitch illuminated night stars cinematic dramatic golden",
            "Lamine Yamal boots grass golden ball sunset peaceful",
            "Young Spanish kids street playing football red shirts future",
            "European championship World Cup trophies together golden pedestal",
            "Lamine Yamal iconic celebration silhouette sunset stadium",
            "Luis de la Fuente smiling hugging players team spirit",
            "Spanish flag waving proud blue sky stadium epic"
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
    audio_file = os.path.join(DOC_DIR, "audio_espanha.mp3")
    logger.info("Gerando locução profissional pt-BR-AntonioNeural...")
    sm = voice.azure_tts_v1(full_script, "pt-BR-AntonioNeural", 1.0, audio_file)

    ass_file = "espanha_legendas.ass"
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

    concat_list = os.path.join(DOC_DIR, "concat_espanha.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.replace('\\', '/')}'\n")

    combined_video = os.path.join(DOC_DIR, "combined_espanha.mp4")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", combined_video
    ], capture_output=True)

    final_output = os.path.join(VIDEOS_PRONTOS_DIR, "DOCUMENTARIO_ESPANHA_YAMAL_O_NOVO_IMPERIO.mp4")
    logger.info("Renderizando documentário da Espanha em Full HD...")
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
    logger.success(f"DOCUMENTÁRIO DA ESPANHA ENTREGUE EM: {final_output}")

def build_short():
    logger.info("Produzindo Short conectado da Espanha & Yamal...")
    short_temp = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "temp_short_espanha")
    os.makedirs(short_temp, exist_ok=True)
    
    short_script = (
        "A humilhação em Wembley que chocou o futebol inglês! "
        "Na Data FIFA, a Espanha foi até Londres e venceu a Inglaterra por três a dois com show de Lamine Yamal e Nico Williams! "
        "Aos dezessete anos, Yamal fez a defesa inglesa parecer amadora e provou que é o novo dono do futebol mundial. "
        "Como a Espanha construiu o império mais imparável das próximas duas décadas? "
        "O documentário completo já está no canal! "
        "Clique no link do primeiro comentário fixado para assistir agora e se inscreva no Futebol Invisível!"
    )
    
    short_queries = [
        "Lamine Yamal celebrating goal Spain red jersey smile",
        "Wembley stadium London match England Spain crowd night",
        "Harry Kane Jude Bellingham looking sad Wembley match",
        "Lamine Yamal wonder goal curved shot celebration",
        "Spain national team lifting trophy confetti celebration",
        "Lamine Yamal Nico Williams smiling dancing celebration"
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

    ass_s = "temp_espanha_short.ass"
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

    final_short = os.path.join(SHORTS_DIR, "SHORT_06_ESPANHA_YAMAL_O_NOVO_IMPERIO.mp4")
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
    logger.success(f"SHORT DA ESPANHA ENTREGUE EM: {final_short}")

if __name__ == "__main__":
    imgs = collect_archive()
    clips = animate_clips(imgs)
    build_documentary(clips)
    build_short()
