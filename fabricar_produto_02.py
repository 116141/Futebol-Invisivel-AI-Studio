import os
import sys
import glob
import time
import asyncio
import aiohttp
import edge_tts
import imageio_ffmpeg
import subprocess
from PIL import Image

old_init = aiohttp.TCPConnector.__init__
def new_init(self, *args, **kwargs):
    kwargs['resolver'] = aiohttp.ThreadedResolver()
    old_init(self, *args, **kwargs)
aiohttp.TCPConnector.__init__ = new_init

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def resize_crop_9_16(in_path, out_path):
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
        img = img.resize((1080, 1920), Image.BILINEAR)
        img.save(out_path, "JPEG", quality=92)

async def tts_and_ass(script_text, voice_name, audio_path, ass_path):
    comm = edge_tts.Communicate(script_text, voice_name)
    sub_maker = edge_tts.SubMaker()
    with open(audio_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                sub_maker.feed(chunk)
                
    srt_text = sub_maker.get_srt()
    ass_header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: ViralText,Impact,75,&H0000FFFF,&H000000FF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,6,3,2,60,60,380,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events = []
    for b in [b.strip() for b in srt_text.strip().split("\n\n") if b.strip()]:
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
                words = content.upper().split()
                if len(words) > 5:
                    mid = len(words) // 2
                    txt = " ".join(words[:mid]) + "\\N" + " ".join(words[mid:])
                else:
                    txt = " ".join(words)
                events.append(f"Dialogue: 0,{srt_to_ass(parts[0])},{srt_to_ass(parts[1])},ViralText,,0,0,0,,{txt}")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events))

def gerar_videos_produto_02():
    photos_dir = r"EXpress anuncio\photo02"
    valid_exts = (".jpg", ".jpeg", ".png", ".webp")
    # Dar prioridade às fotos com a modelo vestindo a peça, seguidas das fotos de detalhes
    all_imgs = [os.path.join(photos_dir, f) for f in os.listdir(photos_dir) if f.lower().endswith(valid_exts)]
    model_imgs = [p for p in all_imgs if "pu_leather" in p]
    detail_imgs = [p for p in all_imgs if "pu_leather" not in p]
    
    # Montar a sequência: Modelo -> Detalhes -> Modelo -> Close
    chosen_imgs = (model_imgs[:2] + detail_imgs[:2] + model_imgs[2:] + detail_imgs[2:])[:6]
    print(f"Total de imagens selecionadas para a edição: {len(chosen_imgs)}")

    scripts = {
        "pt": {
            "text": (
                "Para tudo e olha esse conjunto gótico motoqueiro de couro! "
                "Ele vem com corsê estruturado e minissaia com tiras que modelam o corpo inteiro! "
                "Perfeito para balada, rolê à noite ou pra arrasar nas fotos! "
                "E o choque: está por apenas um dólar na promoção relâmpago do AliExpress! "
                "Clica agora no primeiro comentário fixado e garanta o seu antes que esgote!"
            ),
            "voice": "pt-BR-FranciscaNeural",
            "out": "02_PU_Leather_Gothic_Set_PT.mp4"
        },
        "en": {
            "text": (
                "Stop scrolling right now! Look at this viral moto style leather clubwear set! "
                "It features a structured corset top and a strappy bodycon mini skirt that snatches your entire waist! "
                "The quality and fit are absolutely insane for only one dollar on AliExpress! "
                "Tap the link in the pinned comment immediately to get yours before the deal ends!"
            ),
            "voice": "en-US-AvaNeural",
            "out": "02_PU_Leather_Gothic_Set_EN.mp4"
        }
    }

    out_dir = "Videos_Prontos_Alana"
    os.makedirs(out_dir, exist_ok=True)
    bg_music = r"resource\songs\output003.mp3"

    for lang, cfg in scripts.items():
        t0 = time.time()
        print(f"\n🚀 Produzindo vídeo Produto 02 ({lang.upper()})...")
        temp_dir = f"temp_p02_{lang}"
        os.makedirs(temp_dir, exist_ok=True)

        audio_path = os.path.join(temp_dir, "audio.mp3")
        ass_path = os.path.join(temp_dir, "subs.ass")

        # 1. TTS + Legendas
        asyncio.run(tts_and_ass(cfg["text"], cfg["voice"], audio_path, ass_path))

        # Duração
        res = subprocess.run([FFMPEG, "-i", audio_path], capture_output=True, text=True)
        dur = 20.0
        for l in res.stderr.splitlines():
            if "Duration" in l:
                try:
                    t_str = l.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = t_str.split(":")
                    dur = float(h)*3600 + float(m)*60 + float(s)
                except:
                    pass

        # 2. Processar imagens
        cropped = []
        for i, img_path in enumerate(chosen_imgs):
            c_p = os.path.join(temp_dir, f"c_{i}.jpg")
            resize_crop_9_16(img_path, c_p)
            cropped.append(c_p)

        # 3. Clips
        per_dur = dur / len(cropped)
        clips = []
        for i, cp in enumerate(cropped):
            c_mp4 = os.path.join(temp_dir, f"clip_{i}.mp4")
            subprocess.run([
                FFMPEG, "-y", "-loop", "1", "-t", str(per_dur),
                "-i", cp, "-vf", "scale=1080:1920",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", c_mp4
            ], capture_output=True)
            clips.append(c_mp4)

        concat_txt = os.path.join(temp_dir, "concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in clips:
                f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")

        video_base = os.path.join(temp_dir, "base.mp4")
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", video_base], capture_output=True)

        # 4. Render final com Legendas e Áudio
        final_file = os.path.join(out_dir, cfg["out"])
        clean_ass = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")

        cmd_final = [
            FFMPEG, "-y",
            "-i", video_base,
            "-i", audio_path,
            "-i", bg_music,
            "-filter_complex", (
                "[1:a]volume=1.5[v_aud];"
                "[2:a]volume=0.20[m_aud];"
                "[v_aud][m_aud]amix=inputs=2:duration=first[a_mix];"
                f"[0:v]ass='{clean_ass}'[v_out]"
            ),
            "-map", "[v_out]",
            "-map", "[a_mix]",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "21",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(dur),
            final_file
        ]
        subprocess.run(cmd_final, capture_output=True)
        print(f"✅ VÍDEO ENTREGUE EM {time.time() - t0:.1f}s: {final_file}")

if __name__ == "__main__":
    gerar_videos_produto_02()
