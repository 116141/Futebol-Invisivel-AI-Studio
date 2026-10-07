import os
import sys
import re
import subprocess
import imageio_ffmpeg
from loguru import logger
import yt_dlp
from app.services import voice

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TEMP_DIR = "temp_raphinha_video_test"
os.makedirs(TEMP_DIR, exist_ok=True)

SCRIPT_TEXT = (
    "A transformação mais assustadora do futebol europeu! "
    "Raphinha calou todos os críticos e se transformou no jogador mais decisivo do Barcelona sob o comando de Hansi Flick! "
    "Com quatorze gols e liderança absoluta, o brasileiro assumiu a braçadeira de capitão e joga em outro nível. "
    "Para você: Raphinha hoje já joga mais bola que Vinícius Júnior? "
    "Deixe sua resposta nos comentários e se inscreva no Futebol Invisível!"
)

SEARCH_QUERIES = [
    "ytsearch1:Raphinha Barcelona goals 2024 skills",
    "ytsearch1:Raphinha Hansi Flick celebration Barcelona"
]

def download_video_clips():
    logger.info("Pesquisando e baixando vídeos reais de Raphinha no YouTube...")
    downloaded_files = []
    
    # Garante que o ffmpeg está no PATH do processo
    ffmpeg_dir = os.path.dirname(FFMPEG)
    if ffmpeg_dir not in os.environ["PATH"]:
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
        
    ydl_opts = {
        'format': 'best',
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'outtmpl': os.path.join(TEMP_DIR, 'source_%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'max_downloads': 1
    }
    
    for i, q in enumerate(SEARCH_QUERIES):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(q, download=True)
        except Exception as e:
            logger.info(f"Busca/download concluído ou limitado: {e}")
                
    # Coleta todos os arquivos source baixados
    for f in os.listdir(TEMP_DIR):
        if f.startswith("source_") and f.endswith(".mp4"):
            downloaded_files.append(os.path.join(TEMP_DIR, f))
    return downloaded_files

def cut_and_crop_to_9_16(src_file, start_sec, duration, out_file):
    # Recorta para 1080x1920 (crop central) e muta o áudio original
    cmd = [
        FFMPEG, "-y",
        "-ss", str(start_sec),
        "-i", src_file,
        "-t", str(duration),
        "-an", # Muta áudio original (zero strike)
        "-vf", "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
        out_file
    ]
    subprocess.run(cmd, capture_output=True)
    return os.path.exists(out_file) and os.path.getsize(out_file) > 100000

def main():
    logger.info("=== INICIANDO PRODUÇÃO DO SHORT COM CLIPES DE VÍDEO REAIS ===")
    
    # 1. Gerar locução e legendas dinâmicas
    audio_path = os.path.join(TEMP_DIR, "audio.mp3")
    logger.info("Gerando locução documental pt-BR-AntonioNeural...")
    sm = voice.azure_tts_v1(SCRIPT_TEXT, "pt-BR-AntonioNeural", 1.0, audio_path)
    srt_content = sm.get_srt() if sm else ""
    
    # 2. Baixar vídeos
    src_videos = download_video_clips()
    if not src_videos:
        logger.error("Nenhum vídeo pôde ser baixado.")
        return
    
    logger.info(f"Vídeos baixados: {len(src_videos)}")
    
    # 3. Cortar trechos curtos dinâmicos (3 a 4 segundos por corte)
    clip_files = []
    offsets = [8, 15, 25, 35, 45]
    clip_idx = 1
    
    for v in src_videos:
        for off in offsets[:3]:
            c_out = os.path.join(TEMP_DIR, f"clip_{clip_idx:02d}.mp4")
            if cut_and_crop_to_9_16(v, off, 4.0, c_out):
                clip_files.append(c_out)
                clip_idx += 1
            if len(clip_files) >= 6:
                break
        if len(clip_files) >= 6:
            break
            
    logger.info(f"Clipes 9:16 gerados: {len(clip_files)}")
    
    # 4. Concatenar clipes
    concat_txt = os.path.join(TEMP_DIR, "concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in clip_files:
            f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")
            
    concat_video = os.path.join(TEMP_DIR, "combined_clips.mp4")
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", concat_video], capture_output=True)
    
    # 5. Criar legendas ASS em amarelo no terço inferior
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

    ass_file = "temp_video_render.ass"
    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))
        
    # 6. Renderizar Short Final
    final_output = os.path.join(OUTPUT_DIR, "SHORT_TESTE_RAPHINHA_VIDEOS_REAIS.mp4")
    cmd_render = [
        FFMPEG, "-y",
        "-stream_loop", "-1", "-i", concat_video,
        "-i", audio_path,
        "-vf", f"ass={ass_file}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        final_output
    ]
    res = subprocess.run(cmd_render, capture_output=True, text=True)
    
    if os.path.exists(ass_file):
        os.remove(ass_file)
        
    if os.path.exists(final_output) and os.path.getsize(final_output) > 1000000:
        logger.success(f"VÍDEO REAL 100% CONCLUÍDO COM SUCESSO: {final_output}")
    else:
        logger.error(f"Erro ao renderizar: {res.stderr[:400]}")

if __name__ == "__main__":
    main()
