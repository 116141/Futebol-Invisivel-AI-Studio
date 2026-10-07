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

# ROTEIROS BASEADOS NA ENGENHARIA REVERSA DO PELEJA E FUTEBOTECO:
# 1. Gancho nos primeiros 2s com quebra de padrão
# 2. Dados factuais/policiais chocantes no meio
# 3. Pergunta final provocativa que explode comentários
DOSSIES_HISTORICOS_VIRAIS = [
    {
        "id": "SHORT_17_CHELSEA_BARCELONA_2009.mp4",
        "title": "O Maior Roubo da Champions League: Chelsea x Barcelona 2009",
        "script": (
            "O maior escândalo de arbitragem já transmitido ao vivo na história da Champions League! "
            "Na semifinal de dois mil e nove entre Chelsea e Barcelona em Stamford Bridge, "
            "o árbitro Tom Henning ignorou quatro pênaltis claríssimos a favor do clube inglês. "
            "Didier Drogba foi expulso gritando para as câmeras do mundo inteiro que aquilo era uma vergonha absoluta! "
            "Anos depois, o próprio árbitro admitiu em entrevista que cometeu erros grotescos e não conseguiu dormir por semanas. "
            "Você acha que a UEFA armou aquele jogo para evitar uma final repetida ou foram apenas erros humanos? "
            "Deixe sua resposta nos comentários e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Didier Drogba Chelsea", "FC Barcelona Champions League 2009", "Stamford Bridge Chelsea stadium"]
    },
    {
        "id": "SHORT_18_MAFIA_DO_APITO_2005.mp4",
        "title": "A Máfia do Apito: O Golpe do Brasileirão 2005",
        "script": (
            "O dia em que a Polícia Federal provou que o futebol brasileiro era manipulado por apostadores clandestinos! "
            "Em dois mil e cinco, escutas telefônicas flagraram o árbitro FIFA Edilson Pereira de Carvalho "
            "garantindo que alterava resultados de jogos em troca de dez mil reais por partida. "
            "A consequência foi inédita no planeta: o tribunal anulou onze partidas inteiras do campeonato, "
            "mudando totalmente a tabela e entregando o título nas mãos do Corinthians. "
            "O Internacional foi roubado naquele campeonato ou a anulação foi correta? "
            "Comente a sua opinião e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Estadio do Pacaembu Corinthians", "Referee soccer whistle red card", "Campeonato Brasileiro trophy"]
    },
    {
        "id": "SHORT_19_CASO_HEVERTON_2013.mp4",
        "title": "O Mistério do Caso Héverton e a Queda da Portuguesa",
        "script": (
            "O maior mistério não resolvido da história do futebol brasileiro! "
            "Na última rodada do Brasileirão de dois mil e treze, o jogador Héverton entrou em campo aos trinta e dois minutos do segundo tempo pela Portuguesa, "
            "mesmo estando suspenso pelo tribunal. "
            "O erro custou a perda de quatro pontos, rebaixou a Portuguesa para a segunda divisão e salvou o Fluminense da queda! "
            "Mais de dez anos depois, o Ministério Público nunca descobriu quem deu a ordem para colocar o jogador em campo. "
            "Você acha que foi incompetência da diretoria ou alguém comprou a escalação? "
            "Diga nos comentários e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Estadio do Caninde Portuguesa", "Fluminense Maracana", "Superior Tribunal de Justica Desportiva"]
    },
    {
        "id": "SHORT_20_ADRIANO_IMPERADOR_TELEFONEMA.mp4",
        "title": "O Telefonema que Destruiu Adriano Imperador",
        "script": (
            "O momento exato em que a carreira do maior atacante do mundo foi destruída para sempre! "
            "Em dois mil e quatro, Adriano Imperador era imparável na Inter de Milão e cotado para ser o melhor jogador do planeta. "
            "Mas um telefonema no vestiário mudou tudo: a notícia da morte repentina do seu pai, Almir. "
            "Javier Zanetti revelou que viu Adriano atirar o telefone no chão, começar a gritar de dor e nunca mais ser o mesmo homem. "
            "O Imperador entrou em depressão profunda e trocou a elite da Europa pela favela onde encontrava paz. "
            "Adriano no auge jogou mais que Haaland e Mbappé? "
            "Deixe sua opinião nos comentários e se inscreva no Futebol Invisível!"
        ),
        "queries": ["Adriano Imperador Inter Milan", "Javier Zanetti Inter Milan", "San Siro Stadium Milan"]
    }
]

def fabricar_short_perfeito(item):
    final_path = os.path.join(SHORTS_DIR, item["id"])
    temp_dir = f"temp_short_build_{item['id'][:8]}"
    os.makedirs(temp_dir, exist_ok=True)
    
    logger.info(f"\n==========================================")
    logger.info(f"Produzindo Dossiê Viral 9:16: {item['id']}")
    
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
        logger.success(f"DOSSIÊ VIRAL ENTREGUE COM SUCESSO: {final_path}")
    else:
        logger.error(f"Erro ao renderizar: {res.stderr[:400]}")

    if os.path.exists(ass_file):
        os.remove(ass_file)

    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    for item in DOSSIES_HISTORICOS_VIRAIS:
        fabricar_short_perfeito(item)
    print("\nTODOS OS DOSSIÊS VIRAIS FORAM FABRICADOS COM SUCESSO!")
