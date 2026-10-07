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

DOC_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "doc_chapecoense_completo")
CLIPS_DIR = os.path.join(DOC_DIR, "clips")
VIDEOS_PRONTOS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos")
SHORTS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")

os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(VIDEOS_PRONTOS_DIR, exist_ok=True)
os.makedirs(SHORTS_DIR, exist_ok=True)

TITLE_DOC = "A Ganância Fatal: A Verdade Sombria por Trás da Tragédia da Chapecoense e do Voo 2933"

CHAPTERS = [
    {
        "chapter": 1,
        "title": "O Conto de Fadas da Arena Condá",
        "script": (
            "No futebol, poucas histórias emocionaram tanto o planeta quanto a ascensão meteórica da Chapecoense. "
            "Em menos de uma década, um clube modesto do interior de Santa Catarina saiu da quarta divisão brasileira "
            "para desafiar os gigantes da América do Sul. Com um futebol de raça, união e humildade, a Chape encantou o país. "
            "Na semifinal da Copa Sul-Americana de dois mil e dezesseis, uma defesa milagrosa do goleiro Danilo no último segundo "
            "garantiu o time na grande final contra o Atlético Nacional. A cidade de Chapecó explodiu em euforia. "
            "Eles estavam a poucos dias de tocar o céu."
        ),
        "queries": [
            "Chapecoense players celebrating Copa Sudamericana 2016 semi final green jerseys",
            "Danilo goalkeeper Chapecoense miracle save emotional match",
            "Arena Conda stadium Chapeco full crowd green white flags",
            "Chapecoense coach Caio Junior smiling celebrating team",
            "Chapecoense team photo lineup 2016 green shirts pitch",
            "Chapecoense fans singing celebrating street Chapeco night",
            "Cleber Santana Chapecoense captain running match action",
            "Chapecoense locker room party singing celebration 2016",
            "Chapecoense players hugging pitch emotional joy tears",
            "Arena Conda stadium lights night aerial drone Santa Catarina"
        ]
    },
    {
        "chapter": 2,
        "title": "O Plano de Voo Assassino e a Economia Macabra",
        "script": (
            "Mas o que o mundo não sabia é que uma teia de ganância, negligência e irresponsabilidade selaria o destino daqueles homens. "
            "Para economizar custos com escalas obrigatórias e taxas de combustível, a diretoria e a companhia aérea LaMia "
            "aprovaram um plano de voo no limite extremo da autonomia do avião Avro RJ85. "
            "A distância entre Santa Cruz de la Sierra e Medellín era praticamente idêntica à capacidade máxima dos tanques de combustível. "
            "O piloto e sócio da empresa, Miguel Quiroga, ignorou todos os protocolos internacionais de segurança aérea. "
            "Ele decolou sabendo que não havia uma única gota de combustível de reserva em caso de imprevistos."
        ),
        "queries": [
            "LaMia Avro RJ85 CP-2933 airplane tarmac airport",
            "Chapecoense players boarding airplane smiling selfie interior cabin",
            "Miguel Quiroga pilot LaMia uniform cockpit serious",
            "Flight radar route map plane Bolivia to Colombia Medellin",
            "Airport tarmac night fuel tanker airplane refueling",
            "Control tower airport air traffic controller radar screen dark",
            "Chapecoense players inside plane seats smiling before takeoff",
            "Airplane flying night sky dark clouds lightning storm",
            "Aviation flight plan paper document clipboard table",
            "Airplane cockpit instruments gauges warning lights night"
        ]
    },
    {
        "chapter": 3,
        "title": "Os Últimos Minutos no Silêncio da Cordilheira",
        "script": (
            "Na aproximação do aeroporto de Rionegro em Medellín, a tragédia anunciada começou a se desenrolar. "
            "Com outra aeronave solicitando pouso prioritário, a controladora de tráfego aéreo orientou o voo LaMia a aguardar em círculos. "
            "Quiroga, temendo uma pesada investigação e a perda de sua licença por falta de combustível, demorou preciosos minutos "
            "para declarar formalmente emergência de combustível. "
            "Subitamente, os quatro motores apagaram por pane seca. A escuridão total tomou conta da cabine. "
            "Em silêncio assustador, sem o barulho das turbinas, o avião planou na neblina espessa antes de colidir violentamente "
            "contra a encosta do Cerro El Gordo, a mais de dois mil e quatrocentos metros de altitude."
        ),
        "queries": [
            "Cerro Gordo Colombia mountain crash site wreckage debris fog mist",
            "Rescue workers searchlights night wreckage airplane accident Colombia",
            "Airplane tail fin Chapecoense crash site Colombian mountain emergency",
            "Emergency ambulances flashing lights rain mud mountain road",
            "Air traffic control audio transcript black box recording dramatic",
            "Firefighters Colombian police rescue operation muddy forest night",
            "Alan Ruschel Jakson Follmann Neto survivors hospital stretcher",
            "Mountain slope trees broken debris scattered disaster site",
            "Flashlights cutting through fog Colombian mountains darkness",
            "Broken aircraft fuselage pieces scattered ground morning mist"
        ]
    },
    {
        "chapter": 4,
        "title": "O Luto Global, Os Milagres e a Cobrança por Justiça",
        "script": (
            "Setenta e uma vidas foram ceifadas naquela montanha fria da Colômbia. "
            "O choque paralisou o planeta. Horas depois, o Atlético Nacional abriu mão do título em um gesto inesquecível de solidariedade, "
            "e mais de quarenta mil colombianos lotaram o estádio com velas acesas gritando o nome da Chapecoense. "
            "Seis pessoas sobreviveram milagrosamente, entre eles os guerreiros Alan Ruschel, Jakson Follmann e Neto, "
            "que se tornaram símbolos vivos de superação. "
            "Hoje, a dor permanece e as famílias ainda lutam por indenizações e punição aos verdadeiros responsáveis. "
            "A Chapecoense não era apenas um time de futebol; era uma lição de pureza e paixão que a ganância humana jamais conseguirá apagar."
        ),
        "queries": [
            "Atanasio Girardot stadium candle vigil Medellin Colombia white shirts",
            "Arena Conda memorial wake coffins green white rain crowd tears",
            "Jakson Follmann Alan Ruschel Neto hugging pitch emotional wheelchair prosthetic",
            "Copa Sudamericana trophy awarded Chapecoense golden lights",
            "Fans crying hugging green jerseys Arena Conda stadium vigil",
            "Green smoke flares stadium tribute memorial Chapecoense",
            "Alan Ruschel emotional return pitch playing football smile",
            "Children holding green white balloons stadium tribute",
            "Chapecoense logo ACF memorial monument flowers stadium",
            "Sun rising over football pitch green grass empty stadium peaceful"
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
    audio_file = os.path.join(DOC_DIR, "audio_chapecoense.mp3")
    logger.info("Gerando locução profissional pt-BR-AntonioNeural...")
    sm = voice.azure_tts_v1(full_script, "pt-BR-AntonioNeural", 1.0, audio_file)

    ass_file = "chapecoense_legendas.ass"
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

    concat_list = os.path.join(DOC_DIR, "concat_chapecoense.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.replace('\\', '/')}'\n")

    combined_video = os.path.join(DOC_DIR, "combined_chapecoense.mp4")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", combined_video
    ], capture_output=True)

    final_output = os.path.join(VIDEOS_PRONTOS_DIR, "DOCUMENTARIO_CHAPECOENSE_A_GANANCIA_FATAL.mp4")
    logger.info("Renderizando documentário da Chapecoense em Full HD...")
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
    logger.success(f"DOCUMENTÁRIO DA CHAPECOENSE ENTREGUE EM: {final_output}")

def build_short():
    logger.info("Produzindo Short conectado da Chapecoense...")
    short_temp = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "temp_short_chapecoense")
    os.makedirs(short_temp, exist_ok=True)
    
    short_script = (
        "O maior crime já cometido na história do futebol mundial! "
        "Em dois mil e dezesseis, o avião da Chapecoense caiu na Colômbia por pane seca, matando setenta e uma pessoas. "
        "Mas você sabia que a queda foi provocada deliberadamente por pura ganância? "
        "A companhia aérea decolou com combustível no limite exato para economizar taxas de abastecimento em outra cidade. "
        "O documentário investigativo completo dos segredos do Voo 2933 já está no canal! "
        "Clique no link do primeiro comentário fixado para assistir agora e se inscreva no Futebol Invisível!"
    )
    
    short_queries = [
        "Chapecoense players celebrating Copa Sudamericana 2016 smiling",
        "LaMia airplane CP-2933 tarmac airport dark",
        "Airplane cockpit instruments warning red alarm night",
        "Cerro Gordo crash site wreckage fog Colombian mountain",
        "Atanasio Girardot candle vigil white crowd Medellin",
        "Chapecoense logo green white memorial monument"
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

    ass_s = "temp_chapecoense_short.ass"
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

    final_short = os.path.join(SHORTS_DIR, "SHORT_05_CHAPECOENSE_A_GANANCIA_FATAL.mp4")
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
    logger.success(f"SHORT DA CHAPECOENSE ENTREGUE EM: {final_short}")

if __name__ == "__main__":
    imgs = collect_archive()
    clips = animate_clips(imgs)
    build_documentary(clips)
    build_short()
