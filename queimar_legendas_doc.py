import os
import sys
import asyncio
import edge_tts
import subprocess
import imageio_ffmpeg
from loguru import logger

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

INPUT_VIDEO = os.path.join(
    "canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos",
    "DOCUMENTARIO_MANCHESTER_CITY_A_FARSA_DOS_BILHOES.mp4"
)
OUTPUT_VIDEO = os.path.join(
    "canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos",
    "DOCUMENTARIO_MANCHESTER_CITY_LEGENDADO.mp4"
)
TEMP_DIR = "temp_subtitle_fix"
os.makedirs(TEMP_DIR, exist_ok=True)

SRT_FILE = os.path.join(TEMP_DIR, "legendas.srt")

# Roteiro completo exato do documentário
SCRIPT_TEXT = (
    "Durante mais de um século, o futebol inglês foi governado por tradição, suor e paciência. "
    "Mas em dois mil e oito, a história mudou para sempre. Um clube modesto e esquecido de Manchester "
    "foi adquirido por Sheikh Mansour e o fundo soberano de Abu Dhabi. Em questão de semanas, "
    "o dinheiro começou a jorrar como nunca se viu no esporte mundial. Estádios foram modernizados, "
    "centros de treinamento galácticos foram construídos e contratações astronômicas abalaram a Europa. "
    "O Manchester City saía da sombra do rival United para se tornar uma potência imparável. "
    "Mas por trás de cada taça erguida e de cada sorriso reluzente nos gramados, "
    "uma teia invisível de contratos secretos, empresas de fachada e manobras contábeis começava a ser tecida. "
    "Com a chegada de Pep Guardiola em dois mil e dezesseis, o Manchester City encontrou o cérebro que faltava. "
    "Guardiola não queria apenas vencer: ele queria humilhar os adversários com um futebol de posse, perfeição tática "
    "e intensidade obsessiva. O clube quebrou a barreira dos cem pontos na Premier League, conquistou a tão sonhada "
    "Champions League e colocou Erling Haaland e Kevin De Bruyne no topo do mundo. "
    "Para quem olhava de fora, parecia a coroação do mérito esportivo. No entanto, nos escritórios da Premier League "
    "em Londres, uma equipe de advogados e auditores fiscais trabalhava em silêncio. "
    "Documentos confidenciais vazados pelo Football Leaks revelavam que os valores de patrocínio "
    "não vinham de empresas reais, mas diretamente do governo dos Emirados Árabes para burlar as regras financeiras. "
    "Após anos de batalhas jurídicas nos tribunais, a bomba explodiu com força devastadora. "
    "A Premier League apresentou oficialmente cento e quinze acusações formais contra o Manchester City por fraudes financeiras. "
    "E agora, a comissão independente julgou o clube como culpado em cento e catorze delas! "
    "Nunca na história dos esportes modernos uma instituição foi condenada em tantas violações ao mesmo tempo. "
    "O pânico tomou conta dos bastidores da Inglaterra. As punições possíveis são aterrorizantes: "
    "a perda de até sessenta pontos na tabela, a cassação de títulos conquistados na última década, "
    "multas de centenas de milhões de libras e até mesmo o rebaixamento sumário para divisões inferiores. "
    "O clube mais poderoso da atualidade viu seu futuro colocado na beira do abismo. "
    "Diante do maior escândalo da história do futebol, os holofotes se voltaram para Pep Guardiola. "
    "Muitos apostavam que o técnico abandonaria o barco. Mas em uma coletiva histórica, com o olhar firme e a voz embargada, "
    "Guardiola declarou guerra aberta contra os outros dezenove clubes da liga, prometendo que lutará até a última instância. "
    "Mesmo que o City consiga reduzir as penas através de recursos judiciais intermináveis, uma coisa é certa: "
    "o legado que parecia intocável agora carrega uma mancha eterna de dúvida. "
    "E você? Acredita que o Manchester City deve ser punido com o rebaixamento e perda de títulos, "
    "ou tudo isso é apenas um boicote da velha guarda do futebol inglês contra o novo império? "
    "Deixe sua opinião nos comentários, compartilhe este documentário e se inscreva no canal Futebol Invisível."
)

async def gerar_srt():
    logger.info("Gerando legendas sincronizadas com Edge-TTS SubMaker...")
    submaker = edge_tts.SubMaker()
    communicate = edge_tts.Communicate(SCRIPT_TEXT, "pt-BR-AntonioNeural")
    
    with open(os.path.join(TEMP_DIR, "audio_temp.mp3"), "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
                
    srt_content = submaker.get_srt()
    with open(SRT_FILE, "w", encoding="utf-8") as f:
        f.write(srt_content)
    logger.success(f"Legendas SRT salvas com sucesso em: {SRT_FILE}")

def queimar_legendas_no_video():
    logger.info("Queimando legendas no vídeo com FFmpeg (estilo profissional amarelo com borda preta)...")
    # Usa caminho relativo com barras normais
    srt_clean = "temp_subtitle_fix/legendas.srt"
    
    # Estilo das legendas: Amarelo chamativo, contorno preto espesso, fonte grande e legível em 16:9
    sub_filter = f"subtitles={srt_clean}:force_style='FontSize=24,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2.5,Shadow=1,Alignment=2,MarginV=35'"
    
    cmd = [
        FFMPEG, "-y",
        "-i", INPUT_VIDEO,
        "-vf", sub_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "copy",
        "-movflags", "+faststart",
        OUTPUT_VIDEO
    ]
    
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode == 0:
        logger.success(f"VÍDEO 100% LEGENDADO E PRONTO EM: {OUTPUT_VIDEO}")
        # Substitui o vídeo original pelo legendado perfeito
        if os.path.exists(OUTPUT_VIDEO):
            os.replace(OUTPUT_VIDEO, INPUT_VIDEO)
            logger.success(f"Substituição concluída! Arquivo oficial atualizado: {INPUT_VIDEO}")
        # Limpeza temporária
        import shutil
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        logger.success("Arquivos temporários de legendagem eliminados!")
    else:
        logger.error(f"Erro ao queimar legendas: {p.stderr[-500:]}")

if __name__ == "__main__":
    asyncio.run(gerar_srt())
    queimar_legendas_no_video()
