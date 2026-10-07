import os
import sys
import glob
import subprocess
from loguru import logger

# Configurações do Vídeo com Materiais 100% Reais
SUBJECT = "Cristiano Ronaldo Abandonou a Seleção? A Verdade da Treta com Jorge Jesus"

SCRIPT = (
    "O maior jogador da história de Portugal acabou de abandonar a concentração da seleção, "
    "e o motivo revoltou o mundo do futebol! Tudo explodiu quando o técnico Jorge Jesus mandou "
    "Cristiano Ronaldo aquecer contra a Noruega, mas deixou o craque de 41 anos no banco até o final. "
    "Jesus disse que ninguém está acima das suas regras táticas. Mas Ronaldo considerou uma humilhação imperdoável, "
    "pegou as malas e foi embora, avisando que vai contar toda a verdade! "
    "São 234 jogos e 146 gols que podem terminar assim. Na sua opinião: Jorge Jesus desrespeitou uma lenda, "
    "ou o Cristiano Ronaldo errou ao abandonar o time? Comente agora e se inscreva no Futebol Invisível!"
)

# Clipes gerados com imagens reais do CR7 e do Jorge Jesus
CLIPS = sorted(glob.glob("clips_cr7/*.mp4"))
materials_arg = ",".join(CLIPS)

def render_real_video():
    logger.info(f"[FUTEBOL INVISÍVEL - 100% REAL] Renderizando vídeo com clipes reais de CR7 e Jorge Jesus...")
    logger.info(f"Materiais utilizados: {materials_arg}")
    
    cmd = [
        sys.executable,
        "cli.py",
        "--video-subject", SUBJECT,
        "--video-script", SCRIPT,
        "--video-source", "local",
        "--video-materials", materials_arg,
        "--voice-name", "pt-BR-AntonioNeural",
        "--video-aspect", "9:16",
        "--video-clip-duration", "4",
        "--video-concat-mode", "sequential",
        "--font-size", "58",
        "--text-fore-color", "#FFFF00",
        "--stroke-color", "#000000",
        "--stroke-width", "1.5"
    ]
    
    subprocess.run(cmd)
    logger.success("VÍDEO 100% REAL RENDERIZADO COM SUCESSO!")

if __name__ == '__main__':
    render_real_video()
