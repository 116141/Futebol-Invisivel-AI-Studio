import os
import sys
import re
import time
import requests
import subprocess
import imageio_ffmpeg
import urllib.request
import urllib.parse
import json
from PIL import Image
from loguru import logger
from app.services import voice

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

DOC_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "doc_calciopoli_completo")
CLIPS_DIR = os.path.join(DOC_DIR, "clips")
VIDEOS_PRONTOS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos")
SHORTS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")

os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(VIDEOS_PRONTOS_DIR, exist_ok=True)
os.makedirs(SHORTS_DIR, exist_ok=True)

CHAPTERS = [
    {
        "chapter": 1,
        "title": "A Era de Ouro do Calcio e os Homens Invisíveis",
        "script": (
            "No final dos anos noventa e início dos anos dois mil, a Série A italiana era o centro do universo do futebol. "
            "Os maiores craques do planeta, estádios lotados e contratos de televisão astronômicos. "
            "A Juventus de Turim desfilava hegemonia, conquistando Scudettos em sequência sob o comando de estrelas lendárias. "
            "Mas longe das câmeras de transmissão, nos corredores escuros de hotéis em Milão e Roma, "
            "um homem exercia um poder absoluto e aterrorizante: Luciano Moggi, o diretor geral da Juventus."
        )
    },
    {
        "chapter": 2,
        "title": "Os Grampos Telefônicos e a Teia da Corrupção",
        "script": (
            "Em dois mil e seis, uma investigação criminal sobre doping acidentalmente interceptou mais de cem mil chamadas telefônicas. "
            "O que a polícia ouviu chocou o mundo. Moggi não apenas sugeria árbitros para as partidas da Juventus; "
            "ele escolhia a dedo quem apitaria, ameaçava juízes que não colaboravam e trancava árbitros no vestiário após derrotas. "
            "Uma rede clandestina de cartões SIM suíços criptografados era distribuída para dirigentes, árbitros e jornalistas "
            "para garantir que a narrativa pública e os resultados em campo fossem totalmente controlados."
        )
    },
    {
        "chapter": 3,
        "title": "O Julgamento do Século e a Queda ao Inferno da Série B",
        "script": (
            "A bomba explodiu poucas semanas antes da Copa do Mundo da Alemanha. "
            "O escândalo batizado de Calciopoli arrastou Juventus, Milan, Fiorentina e Lazio para os tribunais de justiça desportiva. "
            "As punições foram implacáveis e históricas: a poderosa Juventus teve dois títulos cassados "
            "e foi sumariamente rebaixada para a Série B pela primeira vez em cento e nove anos de existência! "
            "Estrelas como Ibrahimovic e Cannavaro abandonaram o barco, enquanto lendas como Del Piero e Buffon "
            "aceitaram descer ao inferno para resgatar a honra do clube."
        )
    },
    {
        "chapter": 4,
        "title": "As Cicatrizes Eternas no Futebol Moderno",
        "script": (
            "Mesmo vinte anos após o escândalo, as feridas do Calciopoli nunca cicatrizaram totalmente no futebol europeu. "
            "A Série A perdeu a liderança financeira para a Premier League e nunca mais recuperou a mesma soberania. "
            "O escândalo provou que até os campeonatos mais ricos do planeta podem ser sequestrados por acordos de bastidores. "
            "E você? Acredita que a corrupção e manipulação de árbitros realmente acabaram no futebol moderno, "
            "ou os métodos apenas ficaram mais sofisticados e invisíveis?"
        )
    }
]

SEARCH_TERMS = [
    "Luciano Moggi Juventus",
    "Juventus FC football match retro",
    "Alessandro Del Piero Juventus",
    "Gianluigi Buffon Juventus Serie B",
    "San Siro Stadio delle Alpi stadium Italian football",
    "Italian police car siren night Rome",
    "Serie A Italian football vintage match",
    "Referee red card football match serious"
]

def search_wikimedia(query, limit=5):
    encoded = urllib.parse.quote(f"filetype:bitmap {query}")
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={encoded}&gsrnamespace=6&gsrlimit={limit}&prop=imageinfo&iiprop=url&iiurlwidth=1280&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'FutebolInvisivelBot/1.0 (contact@futebolinvisivel.com)'})
    urls = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        for p in data.get('query', {}).get('pages', {}).values():
            ii = p.get('imageinfo', [{}])[0]
            thumb = ii.get('thumburl') or ii.get('url')
            if thumb and any(ext in thumb.lower() for ext in ['.jpg', '.jpeg', '.png']):
                urls.append(thumb)
    except Exception:
        pass
    return urls

def download_and_crop(url, out_path, is_vertical=False):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            content = response.read()
        if len(content) > 5000:
            temp = out_path + ".tmp"
            with open(temp, "wb") as f:
                f.write(content)
            with Image.open(temp) as img:
                img = img.convert("RGB")
                w, h = img.size
                target_ratio = (1080 / 1920) if is_vertical else (16 / 9)
                current_ratio = w / h
                if current_ratio > target_ratio:
                    new_w = int(h * target_ratio)
                    left = (w - new_w) // 2
                    img = img.crop((left, 0, left + new_w, h))
                else:
                    new_h = int(w / target_ratio)
                    top = (h - new_h) // 2
                    img = img.crop((0, top, w, top + new_h))
                target_size = (1080, 1920) if is_vertical else (1920, 1080)
                img = img.resize(target_size, Image.LANCZOS)
                img.save(out_path, "JPEG", quality=95)
            if os.path.exists(temp):
                os.remove(temp)
            return True
    except Exception:
        pass
    return False

def collect_archive():
    logger.info("Coletando acervo de imprensa esportiva limpo para o Calciopoli...")
    total_images = []
    idx = 1
    for term in SEARCH_TERMS:
        urls = search_wikimedia(term, limit=4)
        for u in urls:
            out_file = os.path.join(DOC_DIR, f"foto_{idx:02d}.jpg")
            if download_and_crop(u, out_file, is_vertical=False):
                logger.success(f"Foto limpa [{idx}]: {out_file}")
                total_images.append(out_file)
                idx += 1
                if idx > 25:
                    break
        if idx > 25:
            break
            
    while len(total_images) < 20:
        base = total_images[0] if total_images else "perfil_futebol_invisivel.jpg"
        fallback = os.path.join(DOC_DIR, f"foto_{len(total_images)+1:02d}.jpg")
        with Image.open(base) as im:
            im = im.resize((1920, 1080), Image.LANCZOS)
            im.save(fallback, "JPEG")
        total_images.append(fallback)
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

def build_documentary(clips):
    full_script = " ".join([c["script"] for c in CHAPTERS])
    audio_file = os.path.join(DOC_DIR, "audio_calciopoli.mp3")
    logger.info("Gerando locução profissional pt-BR-AntonioNeural...")
    sm = voice.azure_tts_v1(full_script, "pt-BR-AntonioNeural", 1.0, audio_file)
    srt_content = sm.get_srt() if sm else ""

    blocks = [b.strip() for b in srt_content.strip().split("\n\n") if b.strip()]
    word_entries = []
    for b in blocks:
        lines = b.splitlines()
        if len(lines) >= 3:
            timing = lines[1]
            text = " ".join(lines[2:]).strip()
            m = re.match(r"(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)", timing)
            if m:
                def to_ass_time(srt_t):
                    h, mn, s = srt_t.split(":")
                    sec, ms = s.split(",")
                    return f"{int(h)}:{mn}:{sec}.{ms[:2]}"
                word_entries.append({
                    "start": to_ass_time(m.group(1)),
                    "end": to_ass_time(m.group(2)),
                    "text": text
                })

    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Arial Black,50,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,30,30,80,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    events = []
    chunk_size = 5
    for i in range(0, len(word_entries), chunk_size):
        chunk = word_entries[i:i+chunk_size]
        t_start = chunk[0]["start"]
        t_end = chunk[-1]["end"]
        phrase = " ".join([c["text"].lower() for c in chunk])
        events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{phrase}")

    ass_file = "calciopoli_legendas.ass"
    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))

    concat_list = os.path.join(DOC_DIR, "concat_calciopoli.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.replace('\\', '/')}'\n")

    combined_video = os.path.join(DOC_DIR, "combined_calciopoli.mp4")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", combined_video
    ], capture_output=True)

    final_output = os.path.join(VIDEOS_PRONTOS_DIR, "DOCUMENTARIO_CALCIOPOLI_A_MAFIA_DO_CALCIO.mp4")
    logger.info("Renderizando documentário do Calciopoli em Full HD...")
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

    if os.path.exists(ass_file):
        os.remove(ass_file)
    logger.success(f"DOCUMENTÁRIO DO CALCIOPOLI ENTREGUE EM: {final_output}")

def build_short(image_files):
    logger.info("Produzindo Short conectado do Calciopoli...")
    short_temp = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "temp_short_calciopoli")
    os.makedirs(short_temp, exist_ok=True)
    
    short_script = (
        "O dia em que a polícia invadiu os bastidores do futebol e rebaixou o maior clube da Itália! "
        "Em dois mil e seis, o escândalo do Calciopoli revelou grampos telefônicos secretos onde a diretoria da Juventus "
        "escolhia os árbitros, ameaçava juízes e manipulava resultados na Série A! "
        "A punição foi histórica: a Juventus perdeu títulos e caiu para a segunda divisão! "
        "O documentário completo e investigativo desse escândalo mafioso já está no canal! "
        "Clique no link do primeiro comentário fixado para assistir agora e se inscreva no Futebol Invisível!"
    )
    
    short_clips = []
    zoom_effects = [
        "zoompan=z='min(zoom+0.0018,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
        "zoompan=z='max(1.25-0.0018*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/4-(ih/zoom/4)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.0018,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
        "zoompan=z='max(1.22-0.0015*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
    ]
    
    for i, img in enumerate(image_files[:6]):
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
    srt_s = sm_s.get_srt() if sm_s else ""

    ass_s = "temp_calciopoli_short.ass"
    h_s = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Impact,80,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,40,40,400,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    
    blocks_s = [b.strip() for b in srt_s.strip().split("\n\n") if b.strip()]
    words_s = []
    for b in blocks_s:
        lines = b.splitlines()
        if len(lines) >= 3:
            timing = lines[1]
            text = " ".join(lines[2:]).strip()
            m = re.match(r"(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)", timing)
            if m:
                def to_ass_time(srt_t):
                    h, mn, s = srt_t.split(":")
                    sec, ms = s.split(",")
                    return f"{int(h)}:{mn}:{sec}.{ms[:2]}"
                words_s.append({
                    "start": to_ass_time(m.group(1)),
                    "end": to_ass_time(m.group(2)),
                    "text": text
                })

    evs = []
    for i in range(0, len(words_s), 4):
        chk = words_s[i:i+4]
        t1 = chk[0]["start"]
        t2 = chk[-1]["end"]
        txt = " ".join([c["text"].upper() for c in chk])
        evs.append(f"Dialogue: 0,{t1},{t2},Default,,0,0,0,,{txt}")

    with open(ass_s, "w", encoding="utf-8") as f:
        f.write(h_s + "\n".join(evs))

    final_short = os.path.join(SHORTS_DIR, "SHORT_08_CALCIOPOLI_A_MAFIA_DO_CALCIO.mp4")
    cmd_s_render = [
        FFMPEG, "-y", "-i", v_base, "-i", a_short,
        "-vf", f"ass={ass_s}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        final_short
    ]
    subprocess.run(cmd_s_render, capture_output=True)
    if os.path.exists(ass_s):
        os.remove(ass_s)
    import shutil
    shutil.rmtree(DOC_DIR, ignore_errors=True)
    shutil.rmtree(short_temp, ignore_errors=True)
    logger.success(f"SHORT DO CALCIOPOLI ENTREGUE EM: {final_short}")

if __name__ == "__main__":
    imgs = collect_archive()
    clips = animate_clips(imgs)
    build_documentary(clips)
    build_short(imgs)
