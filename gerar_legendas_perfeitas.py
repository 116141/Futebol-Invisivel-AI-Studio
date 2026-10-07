import os
import sys
import json
import subprocess
import imageio_ffmpeg
from loguru import logger
from app.services import voice

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

INPUT_VIDEO = os.path.join(
    "canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos",
    "DOCUMENTARIO_MANCHESTER_CITY_A_FARSA_DOS_BILHOES.mp4"
)
OUTPUT_VIDEO = os.path.join(
    "canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos",
    "DOCUMENTARIO_MANCHESTER_CITY_LEGENDADO.mp4"
)

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

def gerar_legendas_ass():
    logger.info("Gerando legendas sincronizadas...")
    audio_temp = "temp_doc_voice.mp3"
    sm = voice.azure_tts_v1(SCRIPT_TEXT, "pt-BR-AntonioNeural", 1.0, audio_temp)
    if not sm:
        logger.error("Falha ao gerar voz e legendas")
        return None
        
    srt_text = sm.get_srt()
    
    # Converte SRT para formato ASS estilizado para FFmpeg
    # O formato ASS evita todos os bugs de path do Windows e suporta formatação rica
    ass_path = "documentario.ass"
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
    # Agrupa palavras em frases de 4 a 6 palavras para leitura cinematográfica confortável
    import re
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
                    # 00:00:01,234 -> 0:00:01.23
                    h, mn, s = srt_t.split(":")
                    sec, ms = s.split(",")
                    return f"{int(h)}:{mn}:{sec}.{ms[:2]}"
                word_entries.append({
                    "start": to_ass_time(m.group(1)),
                    "end": to_ass_time(m.group(2)),
                    "text": content.strip()
                })
                
    # Agrupa em chunks de 5 palavras
    chunk_size = 5
    for i in range(0, len(word_entries), chunk_size):
        chunk = word_entries[i:i+chunk_size]
        t_start = chunk[0]["start"]
        t_end = chunk[-1]["end"]
        phrase = " ".join([c["text"] for c in chunk])
        events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{phrase}")
        
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))
        
    logger.success(f"Legendas ASS profissionais geradas: {ass_path} ({len(events)} frases agrupadas)")
    if os.path.exists(audio_temp):
        os.remove(audio_temp)
    return ass_path

def queimar_legendas_ass(ass_file):
    logger.info("Queimando legendas no vídeo com FFmpeg (Full HD 1920x1080)...")
    # Usa filtro ass com nome simples
    cmd = [
        FFMPEG, "-y",
        "-i", INPUT_VIDEO,
        "-vf", f"ass={ass_file}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "copy",
        "-movflags", "+faststart",
        OUTPUT_VIDEO
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode == 0:
        logger.success(f"VÍDEO 100% LEGENDADO CRIADO COM SUCESSO: {OUTPUT_VIDEO}")
        os.replace(OUTPUT_VIDEO, INPUT_VIDEO)
        logger.success(f"Arquivo principal atualizado: {INPUT_VIDEO}")
        if os.path.exists(ass_file):
            os.remove(ass_file)
        if os.path.exists("legendas.srt"):
            os.remove("legendas.srt")
    else:
        logger.error(f"Erro FFmpeg: {p.stderr[-400:]}")

if __name__ == "__main__":
    ass = gerar_legendas_ass()
    if ass:
        queimar_legendas_ass(ass)
