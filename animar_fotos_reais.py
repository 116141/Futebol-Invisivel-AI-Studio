import os
import sys
import glob
import subprocess
import imageio_ffmpeg
from loguru import logger

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
INPUT_DIR = "materiais_cr7"
OUTPUT_DIR = "clips_cr7"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lista das 6 imagens reais
images = sorted(glob.glob(os.path.join(INPUT_DIR, "*.jpg")))

# Efeitos de câmera para cada cena (Zoom lento para frente, para trás, pan dramático)
ZOOM_EFFECTS = [
    # Cena 1: CR7 Portugal - Zoom in dramático no olhar
    "zoompan=z='min(zoom+0.0015,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
    # Cena 2: Jorge Jesus - Zoom in no rosto furioso
    "zoompan=z='min(zoom+0.002,1.3)':d=120:x='iw/2-(iw/zoom/2)':y='ih/4-(ih/zoom/4)':s=1080x1920:fps=30",
    # Cena 3: CR7 no Banco - Zoom out revelando a tristeza
    "zoompan=z='max(1.2-0.0015*on,1.0)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    # Cena 4: Jorge Jesus coletiva - Zoom lento
    "zoompan=z='min(zoom+0.0015,1.2)':d=120:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
    # Cena 5: CR7 Comemoração - Zoom in triunfal
    "zoompan=z='min(zoom+0.002,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
    # Cena 6: Torcida - Pan cinematográfico
    "zoompan=z='min(zoom+0.0012,1.18)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
]

def make_video_clips():
    generated_clips = []
    for i, img_path in enumerate(images):
        out_clip = os.path.join(OUTPUT_DIR, f"clip_{i+1:02d}.mp4")
        effect = ZOOM_EFFECTS[i % len(ZOOM_EFFECTS)]
        
        logger.info(f"Transformando foto real {os.path.basename(img_path)} em vídeo dinâmico...")
        
        cmd = [
            FFMPEG, "-y",
            "-loop", "1",
            "-i", img_path,
            "-vf", f"{effect},format=yuv420p",
            "-t", "5",  # 5 segundos por clipe
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            out_clip
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            logger.success(f"Vídeo real gerado: {out_clip}")
            generated_clips.append(os.path.abspath(out_clip))
        else:
            logger.error(f"Erro ao converter {img_path}: {res.stderr}")
            
    return generated_clips

if __name__ == '__main__':
    clips = make_video_clips()
    print(f"\nTotal de clipes reais de alta definição gerados: {len(clips)}")
