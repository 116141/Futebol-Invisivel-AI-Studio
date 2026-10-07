import os
import subprocess
import imageio_ffmpeg
from PIL import Image, ImageDraw
from loguru import logger

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

INPUT_VIDEO = os.path.join(
    "canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos",
    "DOCUMENTARIO_CR7_O_PRECO_DA_IMORTALIDADE.mp4"
)
OUTPUT_TEMP = os.path.join(
    "canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos",
    "DOCUMENTARIO_CR7_COM_MARCA_DAGUA.mp4"
)
LOGO_SRC = "perfil_futebol_invisivel.jpg"
WATERMARK_PNG = "watermark_canal.png"

def criar_marca_dagua_circular_translucida():
    logger.info("Criando marca d'água redonda e translúcida do Futebol Invisível...")
    with Image.open(LOGO_SRC) as img:
        img = img.convert("RGBA")
        size = (110, 110)  # Tamanho ideal discreto e profissional no canto
        img = img.resize(size, Image.LANCZOS)
        
        # Cria máscara circular
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=210)  # Suave transparência
        
        # Borda sutil
        img.putalpha(mask)
        img.save(WATERMARK_PNG, "PNG")
    logger.success(f"Marca d'água oficial criada: {WATERMARK_PNG}")

def aplicar_marca_dagua_no_video():
    logger.info("Aplicando a marca d'água oficial no canto superior direito do vídeo...")
    # overlay: posicionado a 35px da borda direita e 30px do topo com 75% de opacidade
    filter_complex = "[1:v]format=rgba,colorchannelmixer=aa=0.8[wm];[0:v][wm]overlay=W-w-35:30"
    
    cmd = [
        FFMPEG, "-y",
        "-i", INPUT_VIDEO,
        "-i", WATERMARK_PNG,
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "copy",
        "-movflags", "+faststart",
        OUTPUT_TEMP
    ]
    
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode == 0:
        logger.success("Marca d'água oficial aplicada com sucesso!")
        os.replace(OUTPUT_TEMP, INPUT_VIDEO)
        logger.success(f"Vídeo oficial atualizado: {INPUT_VIDEO}")
        if os.path.exists(WATERMARK_PNG):
            os.remove(WATERMARK_PNG)
    else:
        logger.error(f"Erro ao aplicar marca d'água: {p.stderr[-400:]}")

if __name__ == "__main__":
    criar_marca_dagua_circular_translucida()
    aplicar_marca_dagua_no_video()
