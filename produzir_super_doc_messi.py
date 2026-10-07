import os
import sys
import time
import requests
import subprocess
import imageio_ffmpeg
from ddgs import DDGS
from PIL import Image, ImageDraw
from loguru import logger
from app.services import voice

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

DOC_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "materiais_fotos_videos", "doc_messi_completo")
CLIPS_DIR = os.path.join(DOC_DIR, "clips")
VIDEOS_PRONTOS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos")
os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(VIDEOS_PRONTOS_DIR, exist_ok=True)

TITLE = "A Glória Eterna: A Jornada Completa de Lionel Messi da Dor à Imortalidade"

CHAPTERS = [
    {
        "chapter": 1,
        "title": "A Sombra de Maradona e a Maldição da Albiceleste",
        "script": (
            "Durante mais de uma década, o maior gênio do futebol viveu no próprio inferno. "
            "Enquanto Lionel Messi enfileirava Bolas de Ouro e taças pelo Barcelona, na sua própria pátria ele era questionado. "
            "Os argentinos diziam que ele não cantava o hino, que faltava a raça de Diego Maradona e que ele era um espanhol disfarçado. "
            "O peso se transformou em tragédia: a final da Copa de dois mil e catorze perdida na prorrogação para a Alemanha, "
            "e duas decisões seguidas da Copa América perdidas nos pênaltis para o Chile. "
            "Em dois mil e dezesseis, após isolar a cobrança e desabar em lágrimas, Messi anunciou que a seleção havia terminado para ele. "
            "Parecia o ponto final mais cruel da história do futebol."
        ),
        "queries": [
            "Lionel Messi sad looking down Argentina 2014 World Cup final Germany",
            "Lionel Messi crying Copa America 2016 final penalty Chile tear",
            "Diego Maradona Lionel Messi World Cup 2010 coaching dramatic",
            "Lionel Messi Barcelona Ballon d'Or trophy smiling prime",
            "Estadio Monumental Buenos Aires Argentina fans dramatic atmosphere",
            "Lionel Messi sitting alone grass pitch disappointed Argentina",
            "Lionel Messi iconic number 10 Argentina jersey back view solitary",
            "Newspaper headlines Argentina Messi renounces national team 2016",
            "Lionel Messi young boy Rosario Newell's Old Boys nostalgic",
            "Lionel Messi walking tunnel dark shadow head down"
        ]
    },
    {
        "chapter": 2,
        "title": "A Reconstrução e o Milagre do Maracanã",
        "script": (
            "Mas o destino reservava um dos maiores capítulos de redenção do esporte. "
            "Com a chegada do técnico Lionel Scaloni, uma nova geração de guerreiros foi convocada com uma única missão: "
            "dar a vida em campo para ver Lionel Messi campeão. Rodrigo De Paul, Emiliano Martínez e Julián Álvarez "
            "não eram apenas companheiros, eram soldados de uma causa sagrada. "
            "Em dois mil e vinte e um, no lendário estádio do Maracanã, a Argentina derrotou o Brasil na final da Copa América. "
            "Vinte e oito anos de seca foram destruídos em solo inimigo. Messi foi jogado para o alto pelos companheiros "
            "em lágrimas de alívio. O monstro que o perseguia finalmente estava morto."
        ),
        "queries": [
            "Lionel Messi lifting Copa America 2021 trophy Maracana celebration",
            "Lionel Messi thrown into the air teammates Argentina Maracana",
            "Emiliano Martinez Dibu intense celebration goalkeeper Argentina",
            "Lionel Scaloni hugging Lionel Messi emotional match pitch",
            "Rodrigo De Paul defending running passionate Argentina jersey",
            "Angel Di Maria goal celebration Maracana Brazil Argentina 2021",
            "Lionel Messi on his knees crying emotional celebration whistle",
            "Argentina national team celebrating locker room trophy singing",
            "Lionel Messi video call family phone on pitch Maracana smiling",
            "Maracana stadium night lights Rio de Janeiro aerial"
        ]
    },
    {
        "chapter": 3,
        "title": "O Voo Supremo no Catar: A Maior Final da História",
        "script": (
            "O ápice da lenda aconteceu nos gramados do Catar em dois mil e vinte e dois. "
            "Aos trinta e cinco anos, Messi jogou com a fúria e a genialidade de um homem com encontro marcado com a história. "
            "A final contra a França de Kylian Mbappé se tornou a mais emocionante de todos os tempos. "
            "Gols nos noventa minutos, drama na prorrogação e uma disputa de pênaltis que parou o coração de bilhões de pessoas. "
            "Quando Montiel converteu o último pênalti, o futebol se curvou definitivamente. "
            "Com o manto real no peito e a taça do mundo nas mãos, Lionel Messi completou o futebol. "
            "O debate sobre o melhor jogador da história parecia encerrado para sempre."
        ),
        "queries": [
            "Lionel Messi kissing FIFA World Cup trophy Lusail Qatar night",
            "Lionel Messi wearing black bisht golden robe lifting World Cup trophy 2022",
            "Lionel Messi celebrating goal Qatar World Cup arms open Lusail",
            "Kylian Mbappe Lionel Messi World Cup final duel drama",
            "Emiliano Martinez save Kolo Muani minute 123 Qatar final",
            "Gonzalo Montiel penalty celebration World Cup champions Argentina",
            "Four million people Buenos Aires Obelisco celebration World Cup parade aerial",
            "Lionel Messi sleeping holding World Cup trophy morning bed",
            "Lionel Messi eighth Ballon d'Or trophy Paris 2023 ceremony",
            "Lionel Messi pointing sky celebration iconic grandmother tribute"
        ]
    },
    {
        "chapter": 4,
        "title": "O Éden de Miami, A Despedida da Albiceleste e a Eternidade",
        "script": (
            "Após vencer tudo na Europa e conquistar sua oitava Bola de Ouro, Messi escolheu a paz do Inter Miami nos Estados Unidos. "
            "Longe da pressão desumana, ele transformou o futebol norte-americano em um espetáculo global ao lado de Luis Suárez. "
            "Em dois mil e vinte e seis, Messi disputou sua sexta Copa do Mundo consecutiva, alcançando marcas históricas inatingíveis. "
            "E hoje, com sua aposentadoria oficial da seleção argentina e mais de cento e vinte gols defendendo seu país, "
            "a caminhada do menino de Rosário que superou a falta de hormônio de crescimento chega ao altar sagrado do esporte. "
            "E você? Acredita que a conquista da Copa do Mundo faz de Lionel Messi o maior jogador de todos os tempos, "
            "ou Pelé, Maradona e Cristiano Ronaldo ainda dividem o trono? "
            "Deixe sua opinião nos comentários, compartilhe este documentário histórico e se inscreva no canal Futebol Invisível."
        ),
        "queries": [
            "Lionel Messi Inter Miami pink jersey presentation stadium crowd fireworks",
            "Lionel Messi Luis Suarez smiling celebrating goal Inter Miami",
            "Lionel Messi serious emotional farewell Argentina national team Monumental",
            "Lionel Messi looking thoughtful stadium lights sunset grass",
            "Inter Miami Chase stadium pink crowd cheering MLS match",
            "Lionel Messi 2026 World Cup match tournament action pitch",
            "Lionel Messi waving goodbye emotional crowd applause tunnel",
            "Pele Maradona Messi Cristiano Ronaldo montage legends football",
            "Lionel Messi boots grass ball golden hour peaceful cinematic",
            "Lionel Messi iconic portrait looking forward legendary black background"
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
        logger.info(f"\nColetando fotos reais limpas para o Capítulo {chap['chapter']}: {chap['title']}...")
        chap_folder = os.path.join(DOC_DIR, f"capitulo_{chap['chapter']}")
        os.makedirs(chap_folder, exist_ok=True)
        for i, q in enumerate(chap['queries']):
            out_file = os.path.join(chap_folder, f"cena_{i+1:02d}.jpg")
            if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
                total_images.append(out_file)
                continue
            # Filtro anti marca d'agua de terceiros
            search_query = f"{q} -alamy -getty -shutterstock -stock -watermark"
            logger.info(f"Capítulo {chap['chapter']} [{i+1}/10]: '{q}'...")
            try:
                results = list(ddgs.images(search_query, max_results=10))
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
    # 1. Coleta das fotos reais limpas
    images = collect_massive_archive()
    
    # 2. Animação de todas as fotos
    clips = animate_all_clips(images)
    
    # 3. Geração de áudio e legendas sincronizadas
    full_script = " ".join([chap['script'] for chap in CHAPTERS])
    audio_file = os.path.join(DOC_DIR, "audio_messi.mp3")
    logger.info("Gerando voz profissional pt-BR-AntonioNeural e legendas...")
    sm = voice.azure_tts_v1(full_script, "pt-BR-AntonioNeural", 1.0, audio_file)
    if not sm:
        logger.error("Falha ao gerar voz com Edge-TTS")
        return
        
    # Gera arquivo ASS estilizado com palavras agrupadas
    ass_file = "legendas_messi.ass"
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
            
    combined_video = os.path.join(DOC_DIR, "combined_messi.mp4")
    logger.info("Concatenando clipes em vídeo cinematográfico...")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", combined_video
    ], capture_output=True)

    # 5. Renderização final com áudio, legendas embutidas e faststart
    final_output = os.path.join(VIDEOS_PRONTOS_DIR, "DOCUMENTARIO_MESSI_A_GLORIA_ETERNA.mp4")
    logger.info("Renderizando documentário legendado final em 16:9 Full HD...")
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
    p = subprocess.run(cmd_final, capture_output=True, text=True)
    if p.returncode == 0:
        logger.success(f"DOCUMENTÁRIO DE MESSI ENTREGUE COM SUCESSO EM: {final_output}")
        # Limpeza automática imediata de fotos, clipes e temporários para economizar disco
        import shutil
        shutil.rmtree(DOC_DIR, ignore_errors=True)
        if os.path.exists(ass_file):
            os.remove(ass_file)
        logger.success("Limpeza concluída! Apenas o vídeo final foi preservado no computador.")
    else:
        logger.error(f"Erro na renderização final: {p.stderr[-500:]}")

if __name__ == "__main__":
    build_full_documentary()
