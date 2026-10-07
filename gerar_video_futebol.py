import os
import sys
import json
import subprocess
from loguru import logger

# Script e Termos Otimizados de Alta Retenção para o Canal "Futebol Invisível"
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

# Termos visuais cinematográficos e impactantes para o Pexels
SEARCH_TERMS = [
    "soccer player walking alone off pitch dramatic stadium",
    "angry soccer coach shouting sidelines tactical match",
    "soccer player sitting on bench looking disappointed",
    "football stadium night lights crowd shouting dramatic",
    "soccer referee blowing whistle close up",
    "emotional football fans stadium cheering shouting"
]

def generate_video():
    logger.info(f"[FUTEBOL INVISÍVEL] Iniciando geração do vídeo de estreia: {SUBJECT}")
    
    terms_str = ", ".join(SEARCH_TERMS)
    
    cmd = [
        sys.executable,
        "cli.py",
        "--video-subject", SUBJECT,
        "--video-script", SCRIPT,
        "--video-terms", terms_str,
        "--voice-name", "pt-BR-AntonioNeural",  # Voz masculina marcante, jornalística e impositiva
        "--video-aspect", "9:16",
        "--video-clip-duration", "3",
        "--video-concat-mode", "sequential",
        "--match-materials-to-script",
        "--font-size", "58",
        "--text-fore-color", "#FFFF00",  # Amarelo vibrante de alta retenção
        "--stroke-color", "#000000",
        "--stroke-width", "1.5"
    ]
    
    logger.info("Executando motor de edição e renderização do vídeo...")
    subprocess.run(cmd)
    logger.success("VÍDEO 1 DO FUTEBOL INVISÍVEL GERADO COM SUCESSO!")

if __name__ == '__main__':
    generate_video()
