import os
import sys
import re
import time
import requests
import subprocess
import imageio_ffmpeg
import urllib.parse
from PIL import Image
from loguru import logger
from app.services import voice

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SHORTS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")
os.makedirs(SHORTS_DIR, exist_ok=True)

BLOCKED_DOMAINS = ["alamy", "gettyimages", "shutterstock", "istockphoto", "stock.adobe", "depositphotos", "dreamstime", "123rf"]

def is_domain_clean(url):
    domain = urllib.parse.urlparse(url).netloc.lower()
    return not any(b in domain for b in BLOCKED_DOMAINS)

def search_wikimedia(query, limit=6):
    import urllib.request, json
    encoded = urllib.parse.quote(f"filetype:bitmap {query}")
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={encoded}&gsrnamespace=6&gsrlimit={limit}&prop=imageinfo&iiprop=url&iiurlwidth=1080&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'FutebolInvisivelBot/1.0'})
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

def download_and_crop_9_16(url, out_path):
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

ALL_SHORTS = [
    {
        "id": "SHORT_03_MESSI_A_REDENCAO_FINAL.mp4",
        "title": "O Choro e a Renúncia de Messi",
        "script": (
            "Você sabia que Lionel Messi quase encerrou sua carreira antes da glória máxima? "
            "Em dois mil e dezesseis, após perder duas finais seguidas da Copa América e a final de dois mil e catorze, "
            "Messi chorou em rede nacional e anunciou que nunca mais jogaria pela Argentina. "
            "Ele era chamado de mercenário e vaiado na sua própria terra. "
            "Mas a redenção veio em dose dupla: o título no Maracanã e a lendária taça do mundo no Catar! "
            "O documentário completo já está no ar no canal! "
            "Clique no link do primeiro comentário fixado e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Lionel Messi Argentina World Cup", "Lionel Messi Copa America celebration", "Lionel Messi Qatar 2022 trophy"]
    },
    {
        "id": "SHORT_04_NEYMAR_A_PROMESSA_QUEBRADA.mp4",
        "title": "A Queda de Neymar Jr",
        "script": (
            "Como Neymar Júnior destruiu seu próprio destino e jogou fora a chance de ser o melhor do mundo? "
            "Em dois mil e quinze ele conquistou a Champions pelo Barcelona e humilhou a Europa ao lado de Messi. "
            "Mas para ser o número um, ele foi para o PSG pelo maior valor da história da humanidade. "
            "O resultado? Brigas internas, festas polêmicas e lesões graves que destruíram seu corpo. "
            "O documentário completo e revelador da queda de Neymar já está no ar no canal! "
            "Clique no link do primeiro comentário fixado e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Neymar Jr Barcelona", "Neymar Jr PSG presentation", "Neymar Jr Brazil national team"]
    },
    {
        "id": "SHORT_05_CHAPECOENSE_A_GANANCIA_FATAL.mp4",
        "title": "A Ganância do Voo 2933",
        "script": (
            "O maior crime já cometido na história do esporte mundial! "
            "Em dois mil e dezesseis, o avião da Chapecoense caiu na Colômbia por pane seca, tirando a vida de setenta e uma pessoas. "
            "Mas a queda foi provocada deliberadamente por pura ganância de dinheiro! "
            "A companhia aérea decolou sem combustível de reserva para não pagar taxas de abastecimento em outra cidade. "
            "O documentário investigativo com os áudios e segredos da tragédia já está no canal! "
            "Clique no link do primeiro comentário fixado e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Chapecoense 2016", "Cerro Gordo airplane wreckage disaster", "Arena Conda vigil Chapecoense"]
    },
    {
        "id": "SHORT_06_ESPANHA_YAMAL_O_NOVO_IMPERIO.mp4",
        "title": "O Novo Império de Lamine Yamal",
        "script": (
            "A humilhação em Wembley que chocou o futebol inglês nesta Data FIFA! "
            "A Espanha foi até Londres e venceu a Inglaterra por três a dois com uma aula magistral de Lamine Yamal e Nico Williams! "
            "Aos dezessete anos, Yamal fez a defesa inglesa parecer amadora e provou que é o novo dono do futebol mundial. "
            "Como a Espanha construiu o império mais imparável das próximas duas décadas? "
            "O documentário completo já está no canal! "
            "Clique no link do primeiro comentário fixado e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Lamine Yamal Spain", "Nico Williams Spain", "Spain national football team celebration"]
    },
    {
        "id": "SHORT_07_BRASIL_A_FAXINA_DE_ANCELOTTI.mp4",
        "title": "A Faxina de Carlo Ancelotti",
        "script": (
            "Carlo Ancelotti barrou os intocáveis e acabou com a farra na Seleção Brasileira! "
            "Nesta Data FIFA de outubro, Don Carlo mandou um recado direto: o Brasil não é mais passarela de influenciador. "
            "Comandada por Vini Jr e Endrick, a Seleção goleou com disciplina militar e intensidade europeia. "
            "Como Ancelotti está limpando os bastidores da CBF para buscar o Hexa? "
            "O documentário completo já está no ar no canal! "
            "Clique no link do primeiro comentário fixado e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Carlo Ancelotti manager", "Vinicius Junior Brazil", "Endrick Brazil national team"]
    }
]

def fabricar_short_perfeito(item):
    final_path = os.path.join(SHORTS_DIR, item["id"])
    temp_dir = f"temp_short_build_{item['id'][:8]}"
    os.makedirs(temp_dir, exist_ok=True)
    
    logger.info(f"\n==========================================")
    logger.info(f"Produzindo Short 9:16 com legendas cravadas: {item['id']}")
    
    # 1. Coletar 6 fotos limpas
    downloaded_images = []
    for q in item["queries"]:
        urls = search_wikimedia(q, limit=4)
        for u in urls:
            out_img = os.path.join(temp_dir, f"img_{len(downloaded_images)+1:02d}.jpg")
            if download_and_crop_9_16(u, out_img):
                downloaded_images.append(out_img)
                if len(downloaded_images) >= 6:
                    break
        if len(downloaded_images) >= 6:
            break

    # Se faltar imagens, duplica com espelhamento para garantir 6 clipes
    while len(downloaded_images) < 6:
        base = downloaded_images[0] if downloaded_images else "perfil_futebol_invisivel.jpg"
        fallback = os.path.join(temp_dir, f"img_{len(downloaded_images)+1:02d}.jpg")
        with Image.open(base) as im:
            im = im.resize((1080, 1920), Image.LANCZOS)
            im.save(fallback, "JPEG")
        downloaded_images.append(fallback)

    # 2. Clipes verticais Ken Burns
    clips = []
    zoom_effects = [
        "zoompan=z='min(zoom+0.0018,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
        "zoompan=z='max(1.25-0.0018*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/4-(ih/zoom/4)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.0018,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
        "zoompan=z='max(1.22-0.0015*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
    ]
    for i, img in enumerate(downloaded_images[:6]):
        c_file = os.path.join(temp_dir, f"clip_{i+1:02d}.mp4")
        eff = zoom_effects[i % len(zoom_effects)]
        cmd = [
            FFMPEG, "-y", "-loop", "1", "-i", img,
            "-vf", f"{eff},format=yuv420p", "-t", "6",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            c_file
        ]
        subprocess.run(cmd, capture_output=True)
        clips.append(c_file)

    concat_txt = os.path.join(temp_dir, "concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")

    video_base = os.path.join(temp_dir, "base.mp4")
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", video_base], capture_output=True)

    # 3. Áudio e legendas automáticas
    audio_file = os.path.join(temp_dir, "audio.mp3")
    sm = voice.azure_tts_v1(item["script"], "pt-BR-AntonioNeural", 1.0, audio_file)
    srt_content = sm.get_srt() if sm else ""

    # Converte SRT para ASS vertical (fonte grande amarela centralizada)
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
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Impact,80,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,40,40,400,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events = []
    chunk_size = 4
    for i in range(0, len(word_entries), chunk_size):
        chunk = word_entries[i:i+chunk_size]
        t_start = chunk[0]["start"]
        t_end = chunk[-1]["end"]
        phrase = " ".join([c["text"].upper() for c in chunk])
        events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{phrase}")

    ass_file = "temp_render_short.ass"
    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))

    # 4. Renderização final
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
        final_path
    ]
    res = subprocess.run(cmd_render, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(final_path) and os.path.getsize(final_path) > 1000000:
        logger.success(f"SHORT 9:16 ENTREGUE COM SUCESSO: {final_path}")
    else:
        logger.error(f"Erro ao renderizar short: {res.stderr[:400]}")

    if os.path.exists(ass_file):
        os.remove(ass_file)
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    for item in ALL_SHORTS:
        fabricar_short_perfeito(item)
