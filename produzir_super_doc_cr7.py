import os
import sys
import time
import requests
import subprocess
import imageio_ffmpeg
from ddgs import DDGS
from PIL import Image
from loguru import logger
from app.services import voice

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

DOC_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "doc_cr7_queda_completo")
CLIPS_DIR = os.path.join(DOC_DIR, "clips")
VIDEOS_PRONTOS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos")
os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(VIDEOS_PRONTOS_DIR, exist_ok=True)

TITLE = "O Preço da Imortalidade: A Queda e os Bastidores de Cristiano Ronaldo"

CHAPTERS = [
    {
        "chapter": 1,
        "title": "A Obsessão Pela Perfeição e o Auge",
        "script": (
            "Durante mais de quinze anos, o mundo do futebol se ajoelhou diante de uma máquina incansável. "
            "Cristiano Ronaldo desafiou os limites da biologia humana, conquistou cinco Bolas de Ouro, "
            "cinco Champions League e se tornou o maior artilheiro da história do esporte mais popular do planeta. "
            "Para Cristiano, o segundo lugar nunca foi uma opção: era uma ofensa pessoal. "
            "Sua disciplina espartana, seus treinos nas madrugadas e sua fome insaciável de glória "
            "construíram uma lenda que parecia indestrutível. Mas o tempo é o único adversário que nenhum atleta consegue vencer."
        ),
        "queries": [
            "Cristiano Ronaldo Ballon d'Or 2017 trophy Real Madrid smiling",
            "Cristiano Ronaldo bicycle kick Juventus Turin Champions League",
            "Cristiano Ronaldo intense training gym muscle fitness sweating",
            "Cristiano Ronaldo Real Madrid Champions League trophy celebration Kyiv",
            "Cristiano Ronaldo young Sporting Lisbon Manchester United debut 2003",
            "Cristiano Ronaldo Euro 2016 trophy Portugal celebration tear",
            "Santiago Bernabeu stadium crowded cheering full Real Madrid",
            "Cristiano Ronaldo famous siuu celebration crowd reaction",
            "Cristiano Ronaldo focused eyes determination close up match",
            "Cristiano Ronaldo statue Madeira museum trophies"
        ]
    },
    {
        "chapter": 2,
        "title": "A Ruptura em Manchester e o Início do Fim",
        "script": (
            "O retorno apoteótico ao Manchester United em dois mil e vinte e um prometia ser o conto de fadas definitivo. "
            "Mas o que se viu foi o início do pesadelo. Um clube em ruínas, sem liderança e sem rumo, "
            "colidiu de frente com o ego gigantesco de Cristiano. A chegada de Erik ten Hag selou o destino do craque: "
            "CR7 foi relegado ao banco de reservas, um território que ele jamais aceitou habitar. "
            "A histórica entrevista com Piers Morgan detonou todas as pontes com Old Trafford, "
            "e Cristiano deixou o maior palco do futebol europeu pela porta dos fundos, isolado e incompreendido."
        ),
        "queries": [
            "Cristiano Ronaldo sitting bench Manchester United Erik ten Hag cold",
            "Cristiano Ronaldo Piers Morgan interview TV studio explosive",
            "Cristiano Ronaldo walking off pitch tunnel Old Trafford angry",
            "Erik ten Hag serious press conference Manchester United manager",
            "Old Trafford stadium Manchester United rain gloomy dark",
            "Cristiano Ronaldo frustration gestures shouting match United",
            "Manchester United dressing room lockers empty dark",
            "Cristiano Ronaldo Portugal bench World Cup 2022 Morocco",
            "Cristiano Ronaldo crying World Cup tunnel Morocco defeat Qatar",
            "Newspaper headlines Cristiano Ronaldo leaves Manchester United contract terminated"
        ]
    },
    {
        "chapter": 3,
        "title": "O Exílio Dourado na Arábia Saudita",
        "script": (
            "A transferência bilionária para o Al-Nassr, na Arábia Saudita, chocou o planeta. "
            "Com um contrato que superava os duzentos milhões de euros por ano, Cristiano não levou apenas seus gols: "
            "ele arrastou consigo o centro das atenções do futebol global para o deserto. "
            "Mesmo quebrando recordes de gols na Liga Saudita, a realidade começou a cobrar o seu preço. "
            "As derrotas dolorosas para o rival Al-Hilal e os conflitos públicos com técnicos e árbitros "
            "revelavam a agonia de quem não aceita o declínio natural do próprio corpo. "
            "O dinheiro infinito de Riad podia comprar luxo e poder, mas não podia devolver a juventude."
        ),
        "queries": [
            "Cristiano Ronaldo presentation Al Nassr yellow jersey Riyadh stadium fireworks",
            "Cristiano Ronaldo Al Nassr celebration goal yellow shirt crowd",
            "Cristiano Ronaldo angry referee Saudi Pro League argument",
            "Cristiano Ronaldo Al Nassr losing Al Hilal sad disappointed",
            "Saudi Pro League stadium modern Riyadh night lights",
            "Jorge Jesus Al Hilal manager celebrating victory derby",
            "Cristiano Ronaldo private jet luxury lifestyle Riyadh mansion",
            "Cristiano Ronaldo drinking water intense heat Saudi match",
            "Al Nassr fans holding Cristiano Ronaldo banner flags",
            "Cristiano Ronaldo shaking head disbelief pitch Saudi"
        ]
    },
    {
        "chapter": 4,
        "title": "O Crepúsculo do Rei e o Juízo da História",
        "script": (
            "Hoje, a novela sobre o adeus de Cristiano Ronaldo da seleção portuguesa e os atritos de bastidores "
            "mostram o dilema final dos imortais: a incapacidade de reconhecer a hora de parar. "
            "Enquanto uma nova geração de craques avança para conquistar a Bola de Ouro de dois mil e vinte e seis, "
            "Cristiano trava sua última batalha contra o esquecimento. "
            "Mesmo com o peso das polêmicas recentes, o legado de CR7 já está cravado para a eternidade. "
            "E você? Acredita que Cristiano Ronaldo deveria se aposentar no topo para preservar sua imagem, "
            "ou ele está certo em lutar até o último segundo de fôlego nos gramados? "
            "Deixe sua resposta nos comentários, compartilhe este documentário e se inscreva no canal Futebol Invisível."
        ),
        "queries": [
            "Cristiano Ronaldo serious portrait dramatic lighting black background close up",
            "Portugal national football team training Roberto Martinez",
            "Cristiano Ronaldo sunset silhouette football pitch nostalgic",
            "Ballon d'Or trophy glowing gold podium stage 2026",
            "Lamine Yamal Kylian Mbappe modern football stars match",
            "Cristiano Ronaldo looking up stadium lights thoughtful emotion",
            "Football boots grass vintage cinematic depth of field",
            "Portugal fans cheering stadium flags Lisbon",
            "Cristiano Ronaldo waving goodbye fans emotional applause",
            "Cristiano Ronaldo iconic jersey number 7 back view tunnel"
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
        logger.info(f"\nColetando fotos reais para o Capítulo {chap['chapter']}: {chap['title']}...")
        chap_folder = os.path.join(DOC_DIR, f"capitulo_{chap['chapter']}")
        os.makedirs(chap_folder, exist_ok=True)
        for i, q in enumerate(chap['queries']):
            out_file = os.path.join(chap_folder, f"cena_{i+1:02d}.jpg")
            if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
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
        if not os.path.exists(out_clip) or os.path.getsize(out_clip) < 5000:
            effect = ZOOM_EFFECTS[i % len(ZOOM_EFFECTS)]
            cmd = [
                FFMPEG, "-y",
                "-loop", "1",
                "-i", img,
                "-vf", f"{effect},format=yuv420p",
                "-t", "6",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p",
                out_clip
            ]
            subprocess.run(cmd, capture_output=True)
        clips.append(os.path.abspath(out_clip))
    return clips

def build_full_documentary():
    # 1. Coleta das fotos reais
    images = collect_massive_archive()
    
    # 2. Animação de todas as fotos
    clips = animate_all_clips(images)
    
    # 3. Geração de áudio e legendas sincronizadas
    full_script = " ".join([chap['script'] for chap in CHAPTERS])
    audio_file = os.path.join(DOC_DIR, "audio_cr7.mp3")
    logger.info("Gerando voz profissional pt-BR-AntonioNeural e legendas...")
    sm = voice.azure_tts_v1(full_script, "pt-BR-AntonioNeural", 1.0, audio_file)
    if not sm:
        logger.error("Falha ao gerar voz com Edge-TTS")
        return
        
    # Gera arquivo ASS estilizado com palavras agrupadas
    ass_file = os.path.join(DOC_DIR, "legendas_cr7.ass")
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H0000FFFF,&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,40,40,65,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    import re
    srt_text = sm.get_srt()
    blocks = srt_text.strip().split("\n\n")
    events = []
    word_entries = []
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) >= 3:
            timing = lines[1]
            content = " ".join(lines[2:])
            m = re.match(r"(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)", timing)
            if m:
                def to_ass_time(srt_t):
                    h, mn, s = srt_t.split(":")
                    sec, ms = s.split(",")
                    return f"{int(h)}:{mn}:{sec}.{ms[:2]}"
                word_entries.append({
                    "start": to_ass_time(m.group(1)),
                    "end": to_ass_time(m.group(2)),
                    "text": content.strip()
                })
    for i in range(0, len(word_entries), 5):
        chunk = word_entries[i:i+5]
        t_start = chunk[0]["start"]
        t_end = chunk[-1]["end"]
        phrase = " ".join([c["text"] for c in chunk])
        events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{phrase}")
        
    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))
    logger.success(f"Legendas ASS geradas com sucesso: {len(events)} frases agrupadas!")

    # 4. Concatenação dos clipes
    concat_list = os.path.join(DOC_DIR, "concat_clips.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.replace('\\', '/')}'\n")
            
    combined_video = os.path.join(DOC_DIR, "combined_cr7.mp4")
    logger.info("Concatenando clipes em vídeo cinematográfico...")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", combined_video
    ], capture_output=True)

    # 5. Renderização final com áudio, legendas embutidas, marca d'água oficial do canal e faststart
    final_output = os.path.join(VIDEOS_PRONTOS_DIR, "DOCUMENTARIO_CR7_O_PRECO_DA_IMORTALIDADE.mp4")
    logger.info("Renderizando documentário legendado com marca d'água oficial em 16:9 Full HD...")
    
    # Cria marca d'água circular do Futebol Invisível
    from PIL import Image, ImageDraw
    logo_file = "perfil_futebol_invisivel.jpg"
    watermark_file = "watermark_cr7.png"
    if os.path.exists(logo_file):
        with Image.open(logo_file) as img:
            img = img.convert("RGBA")
            size = (110, 110)
            img = img.resize(size, Image.LANCZOS)
            mask = Image.new("L", size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size[0], size[1]), fill=210)
            img.putalpha(mask)
            img.save(watermark_file, "PNG")

    # Filtro unificado: legendas ASS + overlay da logo no canto superior direito
    filter_graph = f"[0:v]ass=legendas_cr7.ass[v_sub];[1:v]format=rgba,colorchannelmixer=aa=0.85[wm];[v_sub][wm]overlay=W-w-35:30"
    
    cmd_final = [
        FFMPEG, "-y",
        "-i", combined_video,
        "-i", watermark_file,
        "-i", audio_file,
        "-filter_complex", filter_graph,
        "-map", "[v_sub]" if not os.path.exists(watermark_file) else "[0:v]", # fallback
        "-map", "2:a",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        final_output
    ]
    p = subprocess.run(cmd_final, capture_output=True, text=True)
    if p.returncode == 0:
        logger.success(f"DOCUMENTÁRIO DE CR7 ENTREGUE COM SUCESSO EM: {final_output}")
        # Limpeza automática imediata de fotos, clipes e temporários para economizar disco
        import shutil
        shutil.rmtree(DOC_DIR, ignore_errors=True)
        logger.success("Limpeza concluída! Apenas o vídeo final foi preservado no computador.")
    else:
        logger.error(f"Erro na renderização final: {p.stderr[-500:]}")

if __name__ == "__main__":
    build_full_documentary()
