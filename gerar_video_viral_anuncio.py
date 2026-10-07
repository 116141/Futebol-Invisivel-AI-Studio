import os
import sys
import asyncio
import aiohttp
import edge_tts
import imageio_ffmpeg
import subprocess
from PIL import Image

# Forçar o aiohttp a usar ThreadedResolver para conexão estável com o Edge TTS
old_init = aiohttp.TCPConnector.__init__
def new_init(self, *args, **kwargs):
    kwargs['resolver'] = aiohttp.ThreadedResolver()
    old_init(self, *args, **kwargs)
aiohttp.TCPConnector.__init__ = new_init

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT_DIR = "Videos_Prontos_Alana"
PHOTOS_DIR = r"EXpress anuncio\photo"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 4 Fotos de alta definição da modelo vestindo o conjunto de lingerie
PHOTOS = [
    os.path.join(PHOTOS_DIR, "S73cc38a7d18243c9a9567cc3db5543bdw.jpg"), # Modelo corpo inteiro
    os.path.join(PHOTOS_DIR, "Sdce432a84d9e4b83a598e848e3c90836S.jpg"), # Selfie espelho detalhe
    os.path.join(PHOTOS_DIR, "S1f07d2ea9d6246ae909231e170836c23R.jpg"), # Close-up busto e gargantilha
    os.path.join(PHOTOS_DIR, "S9c46e9ebbf47456880dfd6853ba869f11.jpg"), # Pose luxo completa
]

SCRIPTS = {
    "pt": {
        "text": (
            "Para tudo e olha essa perfeição! "
            "Se você quer se sentir uma verdadeira deusa empoderada, esse conjunto de renda com cinta-liga e correntes é surreal! "
            "Ele valoriza cada curva do corpo com um toque macio e super sensual. "
            "E o melhor: está com preço de fábrica no link promocional! "
            "Corre agora no primeiro comentário fixado e garanta já o seu antes que esgote!"
        ),
        "voice": "pt-BR-FranciscaNeural",
        "title": "Conjunto Lingerie Renda Luxo",
        "out_name": "01_Lingerie_Viral_Model_TryOn_PT.mp4"
    },
    "en": {
        "text": (
            "Stop scrolling right now! Look at this stunning piece! "
            "If you want to feel like an absolute goddess, this viral luxury lace lingerie set with garter chains is incredible! "
            "It hugs every single curve with premium ultra-soft lace and irresistible details. "
            "And the price? Unbeatable factory deal on AliExpress! "
            "Tap the link in the pinned comment right now to get yours before it sells out!"
        ),
        "voice": "en-US-AvaNeural",
        "title": "Viral Luxury Lace Set TryOn",
        "out_name": "01_Lingerie_Viral_Model_TryOn_EN.mp4"
    }
}

async def generate_speech_and_subtitles(script_text, voice_name, audio_path, ass_path):
    print(f"Gerando voz neural ({voice_name})...")
    comm = edge_tts.Communicate(script_text, voice_name)
    sub_maker = edge_tts.SubMaker()
    
    with open(audio_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                sub_maker.feed(chunk)
                
    srt_text = sub_maker.get_srt()
    
    # Estilo ASS Chamativo (Amarelo vibrante com borda preta grossa e sombra)
    ass_header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: ViralText,Impact,76,&H0000FFFF,&H000000FF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,6,3,2,60,60,380,1\n"
        "Style: HookText,Impact,84,&H000055FF,&H000000FF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,7,4,2,60,60,380,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    
    events = []
    blocks = [b.strip() for b in srt_text.strip().split("\n\n") if b.strip()]
    
    for i, b in enumerate(blocks):
        lines = b.splitlines()
        if len(lines) >= 3:
            timing = lines[1]
            content = " ".join(lines[2:]).strip()
            parts = timing.split(" --> ")
            if len(parts) == 2:
                def srt_to_ass(t):
                    h, m, s = t.split(":")
                    sec, ms = s.split(",")
                    return f"{int(h)}:{m}:{sec}.{ms[:2]}"
                t1 = srt_to_ass(parts[0])
                t2 = srt_to_ass(parts[1])
                style = "HookText" if i == 0 else "ViralText"
                words = content.upper().split()
                if len(words) > 5:
                    mid = len(words) // 2
                    formatted_text = " ".join(words[:mid]) + "\\N" + " ".join(words[mid:])
                else:
                    formatted_text = " ".join(words)
                events.append(f"Dialogue: 0,{t1},{t2},{style},,0,0,0,,{formatted_text}")
                
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events))
    print(f"Legendas geradas com sucesso.")

def prepare_9_16_image(in_path, out_path):
    with Image.open(in_path) as img:
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

def build_viral_video(lang="pt"):
    cfg = SCRIPTS[lang]
    print(f"\n=======================================================")
    print(f"  PRODUZINDO VÍDEO VIRAL ({lang.upper()}): {cfg['out_name']}")
    print(f"=======================================================")
    
    temp_dir = f"temp_build_{lang}"
    os.makedirs(temp_dir, exist_ok=True)
    
    audio_path = os.path.join(temp_dir, "voice.mp3")
    ass_path = os.path.join(temp_dir, "subtitles.ass")
    
    # 1. Narração e Legendas
    asyncio.run(generate_speech_and_subtitles(cfg["text"], cfg["voice"], audio_path, ass_path))
    
    # Obter duração exata
    res = subprocess.run([FFMPEG, "-i", audio_path], capture_output=True, text=True)
    dur_sec = 14.0
    for l in res.stderr.splitlines():
        if "Duration" in l:
            try:
                t_str = l.split("Duration:")[1].split(",")[0].strip()
                h, m, s = t_str.split(":")
                dur_sec = float(h)*3600 + float(m)*60 + float(s)
            except:
                pass
    print(f"Duração exata do áudio: {dur_sec:.2f}s")
    
    # 2. Processar Imagens
    norm_images = []
    for i, p in enumerate(PHOTOS):
        cropped = os.path.join(temp_dir, f"img_{i}.jpg")
        prepare_9_16_image(p, cropped)
        norm_images.append(cropped)
        
    num_imgs = len(norm_images)
    slide_dur = dur_sec / num_imgs
    clips = []
    
    print(f"Renderizando {num_imgs} cenas da modelo em 1080x1920...")
    for i, img_p in enumerate(norm_images):
        clip_mp4 = os.path.join(temp_dir, f"clip_{i}.mp4")
        cmd_clip = [
            FFMPEG, "-y",
            "-loop", "1",
            "-t", str(slide_dur),
            "-i", img_p,
            "-vf", "scale=1080:1920",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            clip_mp4
        ]
        subprocess.run(cmd_clip, capture_output=True)
        clips.append(clip_mp4)
        
    concat_txt = os.path.join(temp_dir, "concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")
            
    video_slides = os.path.join(temp_dir, "slides.mp4")
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", video_slides], capture_output=True)
    
    # 3. Renderização final: Montagem com Música de Fundo e Legendas Queimadas
    bg_music = r"resource\songs\output001.mp3"
    final_output = os.path.join(OUTPUT_DIR, cfg["out_name"])
    clean_ass = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")
    
    cmd_render = [
        FFMPEG, "-y",
        "-i", video_slides,
        "-i", audio_path,
        "-i", bg_music,
        "-filter_complex", (
            "[1:a]volume=1.5[voice];"
            "[2:a]volume=0.18[music];"
            "[voice][music]amix=inputs=2:duration=first[audio_mix];"
            f"[0:v]ass='{clean_ass}'[v_sub]"
        ),
        "-map", "[v_sub]",
        "-map", "[audio_mix]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(dur_sec),
        "-movflags", "+faststart",
        final_output
    ]
    
    print("Renderizando vídeo final com mixagem e legendas dinâmicas...")
    res = subprocess.run(cmd_render, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(final_output) and os.path.getsize(final_output) > 500000:
        size_mb = os.path.getsize(final_output) / (1024 * 1024)
        print(f"==> SUCESSO! VÍDEO CRIADO: {final_output} ({size_mb:.2f} MB)")
    else:
        print(f"Erro FFmpeg: {res.stderr[:500]}")

if __name__ == "__main__":
    build_viral_video("pt")
    build_viral_video("en")
    print("\nTODOS OS VÍDEOS FORAM GERADOS COM SUCESSO!")
