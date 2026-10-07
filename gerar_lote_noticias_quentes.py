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

NOVOS_SHORTS_HOT = [
    {
        "id": "SHORT_10_CR7_REVOLTA_JORGE_JESUS.mp4",
        "title": "A Ruptura de Cristiano Ronaldo com Jorge Jesus",
        "script": (
            "A crise que parou o futebol português e internacional! "
            "Cristiano Ronaldo abandonou o estágio da Seleção após o técnico Jorge Jesus deixá-lo no banco durante toda a partida contra a Noruega. "
            "Segundo fontes apuradas pela imprensa europeia, o camisa sete sentiu-se desrespeitado após aquecer por trinta minutos e não entrar. "
            "Ronaldo foi desrespeitado pelo treinador ou Jorge Jesus tem razão em impor autoridade na equipe? "
            "Deixe sua opinião nos comentários e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Cristiano Ronaldo Portugal national team", "Cristiano Ronaldo Al Nassr training", "Jorge Jesus manager coach"]
    },
    {
        "id": "SHORT_11_VINI_JR_ESCOLHA_CERTA.mp4",
        "title": "Vini Jr fez a escolha certa ao ficar no Real Madrid?",
        "script": (
            "Vinícius Júnior cometeu o maior erro da sua carreira ao recusar a Premier League e ficar no Real Madrid? "
            "Após um início de temporada conturbado e com queda brusca de rendimento de todo o ataque merengue, "
            "jornais europeus começam a questionar se o brasileiro perdeu o protagonismo com a chegada de Kylian Mbappé. "
            "No Real Madrid ele divide espaço, enquanto na Inglaterra seria a estrela absoluta e inquestionável. "
            "Vini Jr acertou em ficar no Real Madrid ou deveria ter ido para a Premier League? "
            "Deixe sua resposta nos comentários e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Vinicius Junior Real Madrid", "Kylian Mbappe Real Madrid", "Santiago Bernabeu match"]
    },
    {
        "id": "SHORT_12_CASO_NEGREIRA_DOSSIE_50MIL.mp4",
        "title": "O Dossiê Secreto do Caso Negreira",
        "script": (
            "O maior escândalo de arbitragem da Espanha chegou aos gabinetes da UEFA! "
            "O Real Madrid formalizou a entrega de um dossiê com cinquenta mil páginas de documentos aos inspetores de ética europeus sobre o Caso Negreira. "
            "A denúncia investiga repasses superiores a sete milhões de euros pagos pelo Barcelona a empresas do vice-presidente da comissão de árbitros. "
            "O Barcelona alega consultoria técnica legal, mas os rivais cobram punições desportivas imediatas. "
            "Houve esquema de arbitragem ou perseguição contra o Barça? "
            "Deixe sua resposta nos comentários e se inscreva no Futebol Invisível!"
        ),
        "queries": ["FC Barcelona Camp Nou", "Real Madrid Santiago Bernabeu", "UEFA Champions League trophy"]
    },
    {
        "id": "SHORT_13_MBAPPE_ESCANDALO_ESTOCOLMO.mp4",
        "title": "A Polêmica de Mbappé em Estocolmo",
        "script": (
            "A viagem polêmica que revoltou a França e a torcida do Real Madrid! "
            "Enquanto a Seleção Francesa entrava em campo pela Nations League, Kylian Mbappé foi poupado por lesão, mas acabou flagrado em uma boate de luxo em Estocolmo! "
            "Jornais franceses como o L'Équipe cobraram publicamente a postura do craque como capitão dos Bleus. "
            "Mbappé alegou direito ao seu descanso, mas a cobrança por comprometimento aumentou na Europa. "
            "Falta de respeito com a Seleção ou perseguição da imprensa contra Mbappé? "
            "Diga nos comentários e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Kylian Mbappe France", "Real Madrid training session", "Didier Deschamps France manager"]
    },
    {
        "id": "SHORT_14_CITY_115_ACUSACOES_VEREDITO.mp4",
        "title": "As 115 Acusações do Manchester City",
        "script": (
            "O julgamento mais aguardado e temido da história da Premier League! "
            "A comissão independente do futebol inglês analisa cento e quinze acusações formais de irregularidades financeiras contra o Manchester City. "
            "As investigações apontam contratos paralelos e receitas inflacionadas para burlar o Fair Play Financeiro ao longo de uma década inteira. "
            "Se for punido, o clube de Pep Guardiola pode enfrentar perda de pontos e até o rebaixamento da liga mais rica do mundo. "
            "O City será punido de verdade ou sairá impune? "
            "Comente a sua opinião e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Etihad Stadium Manchester City", "Pep Guardiola", "Premier League trophy England"]
    },
    {
        "id": "SHORT_15_RAPHINHA_MONSTRO_BARCELONA.mp4",
        "title": "A Explosão Absurda de Raphinha no Barcelona",
        "script": (
            "De quase vendido para o jogador mais decisivo do planeta! "
            "A transformação de Raphinha sob o comando de Hansi Flick no Barcelona é uma das coisas mais assustadoras da Europa! "
            "Com quatorze gols e três assistências nos primeiros oito jogos, o brasileiro assumiu a braçadeira de capitão e renovou até dois mil e trinta! "
            "Ele calou os críticos que queriam sua saída e provou que é um dos melhores do mundo. "
            "Raphinha já joga mais do que Vinícius Júnior nesta temporada? "
            "Deixe sua opinião nos comentários e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Raphinha Barcelona celebration", "Hansi Flick Barcelona manager", "Raphinha Brazil national team"]
    },
    {
        "id": "SHORT_16_MICHAEL_OLISE_NOVO_DONO_BAYERN.mp4",
        "title": "Michael Olise: O Novo Dono do Bayern de Munique",
        "script": (
            "O jogador mais frio e imparável do futebol europeu neste momento! "
            "Michael Olise chegou ao Bayern de Munique e transformou o ataque de Vincent Kompany em uma máquina de gols! "
            "Apelidado de mister indiferente pela sua calma cirúrgica, o francês coleciona atuações perfeitas e assistências geniais para Harry Kane. "
            "Kompany já comparou o talento de Olise ao de Kevin De Bruyne no auge! "
            "Olise já é o melhor ponta da Europa ou ainda é cedo? "
            "Diga nos comentários e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Michael Olise Bayern Munich", "Vincent Kompany Bayern manager", "Harry Kane Bayern Munich"]
    }
]

def fabricar_short_perfeito(item):
    final_path = os.path.join(SHORTS_DIR, item["id"])
    temp_dir = f"temp_short_build_{item['id'][:8]}"
    os.makedirs(temp_dir, exist_ok=True)
    
    logger.info(f"\n==========================================")
    logger.info(f"Produzindo Short 9:16: {item['id']}")
    
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

    while len(downloaded_images) < 6:
        base = downloaded_images[0] if downloaded_images else "perfil_futebol_invisivel.jpg"
        fallback = os.path.join(temp_dir, f"img_{len(downloaded_images)+1:02d}.jpg")
        with Image.open(base) as im:
            im = im.resize((1080, 1920), Image.LANCZOS)
            im.save(fallback, "JPEG")
        downloaded_images.append(fallback)

    zoom_effects = [
        "zoompan=z='min(zoom+0.0018,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
        "zoompan=z='max(1.25-0.0018*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/4-(ih/zoom/4)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.0018,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
        "zoompan=z='max(1.22-0.0015*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
    ]
    clips = []
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

    audio_file = os.path.join(temp_dir, "audio.mp3")
    sm = voice.azure_tts_v1(item["script"], "pt-BR-AntonioNeural", 1.0, audio_file)
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
    for item in NOVOS_SHORTS_HOT:
        fabricar_short_perfeito(item)
    print("\nTODOS OS 5 SHORTS FORAM FABRICADOS COM SUCESSO!")
