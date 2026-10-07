import os
import sys
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

DOC_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "doc_brasil_completo")
CLIPS_DIR = os.path.join(DOC_DIR, "clips")
VIDEOS_PRONTOS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos")
SHORTS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")

os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(VIDEOS_PRONTOS_DIR, exist_ok=True)
os.makedirs(SHORTS_DIR, exist_ok=True)

CHAPTERS = [
    {
        "chapter": 1,
        "title": "Duas Décadas de Fracassos e a Cultura dos Privilégios",
        "script": (
            "Desde o pentacampeonato mundial em dois mil e dois, a Seleção Brasileira se transformou em uma máquina de decepções. "
            "Eliminações dolorosas, vexame histórico do sete a um em casa e gerações talentosas que sucumbiram à falta de disciplina e ao comodismo. "
            "A camisa mais pesada do futebol mundial passou a ser tratada por muitos como passarela de vaidades e clube de amigos. "
            "Treinadores caíam um após o outro, mas a estrutura viciada nos bastidores da CBF continuava intocável. "
            "O torcedor brasileiro cansou de sofrer e abandonou o patriotismo verde e amarelo."
        )
    },
    {
        "chapter": 2,
        "title": "A Chegada de Don Carlo: O Primeiro Mestre Estrangeiro",
        "script": (
            "Diante do abismo e da pressão popular, a CBF quebrou um tabu centenário e tomou a decisão mais drástica de sua história: "
            "contratar um treinador estrangeiro de elite mundial. Carlo Ancelotti, o técnico mais vitorioso da Champions League, "
            "aceitou o desafio de comandar a reconstrução da Amarelinha. "
            "Don Carlo não trouxe apenas bagagem tática; trouxe autoridade inquestionável, calma de campeão "
            "e a coragem necessária para tomar medidas impopulares que nenhum comandante brasileiro teve peito de adotar."
        )
    },
    {
        "chapter": 3,
        "title": "A Faxina dos Intocáveis e a Nova Lei da Granja Comary",
        "script": (
            "A primeira atitude de Ancelotti foi uma verdadeira revolução silenciosa nos bastidores. "
            "O fim dos privilégios de celebridade, o fim das visitas de influenciadores e o corte impiedoso de medalhões "
            "que não demonstravam comprometimento físico ou tático. "
            "Nesta Data FIFA de outubro, a lista de convocados e as atuações em campo mandaram um recado fulminante: "
            "não há vaga cativa por nome ou número de seguidores. "
            "Com uma goleada implacável de quatro a zero e intensidade sufocante, "
            "a Seleção Brasileira voltou a competir com seriedade militar."
        )
    },
    {
        "chapter": 4,
        "title": "A Reconquista do Respeito Mundial",
        "script": (
            "A transição ainda está em andamento, mas o sinal de alerta para os gigantes europeus já soou. "
            "O futebol brasileiro redescobriu que o talento natural só atinge o ápice quando combinado com organização de nível europeu. "
            "Sob a batuta serena de Carlo Ancelotti e liderada por uma juventude faminta e sem medo de cara feia, "
            "o gigante adormecido da América do Sul finalmente acordou. "
            "E você? Acredita que Don Carlo é o homem que vai trazer o sonhado hexa, "
            "ou a Seleção Brasileira ainda precisa de tempo para curar suas velhas feridas?"
        )
    }
]

SEARCH_TERMS = [
    "Carlo Ancelotti manager",
    "Vinicius Junior Brazil",
    "Endrick Brazil",
    "Rodrygo Brazil",
    "Casemiro Brazil",
    "Marquinhos Brazil",
    "Neymar Brazil",
    "Brazil national football team match",
    "Brazil football training",
    "Brazil stadium Maracana football"
]

def search_wikimedia_images(query, limit=5):
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
            if thumb and ('jpg' in thumb.lower() or 'jpeg' in thumb.lower() or 'png' in thumb.lower()):
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
    logger.info("Coletando acervo de imprensa esportiva 100% limpo sem marcas d'água...")
    total_images = []
    idx = 1
    for term in SEARCH_TERMS:
        urls = search_wikimedia_images(term, limit=4)
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
    audio_file = os.path.join(DOC_DIR, "audio_brasil.mp3")
    logger.info("Gerando locução profissional pt-BR-AntonioNeural...")
    sm = voice.azure_tts_v1(full_script, "pt-BR-AntonioNeural", 1.0, audio_file)

    ass_file = "brasil_legendas.ass"
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

    concat_list = os.path.join(DOC_DIR, "concat_brasil.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.replace('\\', '/')}'\n")

    combined_video = os.path.join(DOC_DIR, "combined_brasil.mp4")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", combined_video
    ], capture_output=True)

    final_output = os.path.join(VIDEOS_PRONTOS_DIR, "DOCUMENTARIO_BRASIL_A_FAXINA_DE_ANCELOTTI.mp4")
    logger.info("Renderizando documentário da Seleção Brasileira em Full HD...")
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
    logger.success(f"DOCUMENTÁRIO DO BRASIL ENTREGUE EM: {final_output}")

def build_short(image_files):
    logger.info("Produzindo Short conectado do Brasil de Ancelotti...")
    short_temp = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "temp_short_brasil")
    os.makedirs(short_temp, exist_ok=True)
    
    short_script = (
        "Carlo Ancelotti barrou os intocáveis e acabou com a farra na Seleção Brasileira! "
        "Na Data FIFA de outubro, Don Carlo mandou um recado direto: o Brasil não é mais passarela de influenciador. "
        "Comandada por Vini Jr e Endrick, a Seleção goleou com disciplina militar e intensidade europeia. "
        "Como Ancelotti está limpando os bastidores da CBF para buscar o Hexa? "
        "O documentário completo já está no ar no canal! "
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
    
    # Gerando fotos verticais
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

    ass_s = "temp_brasil_short.ass"
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

    final_short = os.path.join(SHORTS_DIR, "SHORT_07_BRASIL_A_FAXINA_DE_ANCELOTTI.mp4")
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
    logger.success(f"SHORT DO BRASIL ENTREGUE EM: {final_short}")

if __name__ == "__main__":
    imgs = collect_archive()
    clips = animate_clips(imgs)
    build_documentary(clips)
    build_short(imgs)
