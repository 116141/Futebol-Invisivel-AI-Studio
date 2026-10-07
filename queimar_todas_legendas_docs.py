import os
import sys
import re
import subprocess
import imageio_ffmpeg
from loguru import logger
from app.services import voice

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SCRIPTS = {
    "DOCUMENTARIO_NEYMAR_A_PROMESSA_QUEBRADA.mp4": (
        "No início dos anos dois mil e dez, o futebol mundial testemunhou o surgimento de um fenômeno raro. "
        "Com cabelos espetados, dribles desconcertantes e uma alegria contagiante, Neymar Júnior resgatava a essência do futebol brasileiro. "
        "Pelo Santos, ele conquistou a Copa Libertadores e desafiou os maiores clubes do planeta. "
        "Pelé, Zico e Ronaldo apontavam para o jovem menino da Vila e cravavam: ali estava o futuro melhor jogador do mundo, "
        "o homem destinado a trazer o hexacampeonato e enfileirar Bolas de Ouro. "
        "A chegada à Europa confirmou todas as expectativas. Ao lado de Lionel Messi e Luis Suárez no Barcelona, "
        "Neymar formou o trio MSN, considerado o ataque mais devastador da história moderna. "
        "Em dois mil e quinze, ele conquistou a tríplice coroa europeia, marcando o gol do título da Champions League em Berlim. "
        "Dois anos depois, ele foi o arquiteto da maior virada da história da competição contra o PSG. "
        "Mas no dia seguinte, a foto histórica nos jornais não era dele, era de Messi nos braços da torcida. "
        "O ego falou mais alto: Neymar percebeu que, para ser o número um, precisava fugir da sombra do rei. "
        "Em agosto de dois mil e dezessete, o Paris Saint-Germain pagou duzentos e vinte e dois milhões de euros, "
        "quebrando todos os recordes financeiros da história da humanidade. Neymar chegava a Paris com status de imperador. "
        "Mas o sonho rapidamente se transformou em pesadelo. Brigas internas por cobranças de pênaltis com Cavani, "
        "a ascensão supersônica de Kylian Mbappé e, acima de tudo, a fragilidade física. "
        "Metatarsos fraturados, tornozelos rompidos e ausências nos jogos mais decisivos da temporada. "
        "A festa de aniversário anual no Brasil se tornou mais comentada do que suas atuações na Champions League. "
        "A última chance de redenção na Copa do Mundo de dois mil e vinte e dois terminou em tragédia contra a Croácia. "
        "O gol antológico na prorrogação não bastou, e o Brasil caiu nos pênaltis. "
        "Sem mais mercado na elite europeia, Neymar aceitou uma fortuna obscena do Al-Hilal da Arábia Saudita. "
        "Poucas semanas depois, o rompimento do ligamento cruzado anterior encerrou prematuramente sua temporada. "
        "Aos trinta e quatro anos, o homem que nasceu para suceder Pelé e superar Messi se tornou o maior desperdício de talento da era moderna. "
        "Neymar Jr conquistou bilhões, mas perdeu a eternidade."
    ),
    "DOCUMENTARIO_CHAPECOENSE_A_GANANCIA_FATAL.mp4": (
        "No futebol, poucas histórias emocionaram tanto o planeta quanto a ascensão meteórica da Chapecoense. "
        "Em menos de uma década, um clube modesto do interior de Santa Catarina saiu da quarta divisão brasileira "
        "para desafiar os gigantes da América do Sul. Com um futebol de raça, união e humildade, a Chape encantou o país. "
        "Na semifinal da Copa Sul-Americana de dois mil e dezesseis, uma defesa milagrosa do goleiro Danilo no último segundo "
        "garantiu o time na grande final contra o Atlético Nacional. A cidade de Chapecó explodiu em euforia. "
        "Eles estavam a poucos dias de tocar o céu. "
        "Mas o que o mundo não sabia é que uma teia de ganância, negligência e irresponsabilidade selaria o destino daqueles homens. "
        "Para economizar custos com escalas obrigatórias e taxas de combustível, a diretoria e a companhia aérea LaMia "
        "aprovaram um plano de voo no limite extremo da autonomia do avião Avro RJ85. "
        "A distância entre Santa Cruz de la Sierra e Medellín era praticamente idêntica à capacidade máxima dos tanques de combustível. "
        "O piloto e sócio da empresa, Miguel Quiroga, ignorou todos os protocolos internacionais de segurança aérea. "
        "Ele decolou sabendo que não havia uma única gota de combustível de reserva em caso de imprevistos. "
        "Na aproximação do aeroporto de Rionegro em Medellín, a tragédia anunciada começou a se desenrolar. "
        "Com outra aeronave solicitando pouso prioritário, a controladora de tráfego aéreo orientou o voo LaMia a aguardar em círculos. "
        "Quiroga, temendo uma pesada investigação e a perda de sua licença por falta de combustível, demorou preciosos minutos "
        "para declarar formalmente emergência de combustível. "
        "Subitamente, os quatro motores apagaram por pane seca. A escuridão total tomou conta da cabine. "
        "Em silêncio assustador, sem o barulho das turbinas, o avião planou na neblina espessa antes de colidir violentamente "
        "contra a encosta do Cerro El Gordo, a mais de dois mil e quatrocentos metros de altitude. "
        "Setenta e uma vidas foram ceifadas naquela montanha fria da Colômbia. "
        "O choque paralisou o planeta. Horas depois, o Atlético Nacional abriu mão do título em um gesto inesquecível de solidariedade, "
        "e mais de quarenta mil colombianos lotaram o estádio com velas acesas gritando o nome da Chapecoense. "
        "Seis pessoas sobreviveram milagrosamente, entre eles os guerreiros Alan Ruschel, Jakson Follmann e Neto, "
        "que se tornaram símbolos vivos de superação. "
        "Hoje, a dor permanece e as famílias ainda lutam por indenizações e punição aos verdadeiros responsáveis. "
        "A Chapecoense não era apenas um time de futebol; era uma lição de pureza e paixão que a ganância humana jamais conseguirá apagar."
    ),
    "DOCUMENTARIO_ESPANHA_YAMAL_O_NOVO_IMPERIO.mp4": (
        "Durante mais de uma década após o título de dois mil e dez, a Espanha se tornou prisioneira do próprio estilo. "
        "Mil passes por jogo, posse estéril e eliminações vexatórias nas Copas de dois mil e dezoito e vinte e dois. "
        "O mundo dizia que o futebol espanhol estava morto e ultrapassado. "
        "Mas nas categorias de base, uma revolução silenciosa estava sendo forjada. "
        "Longe do toque burocrático, uma nova safra de atacantes velozes, audaciosos e dribladores "
        "começava a quebrar todas as regras do manual europeu. "
        "Com apenas dezesseis anos, um jovem franzino de Rocafonda pegou a bola e mudou a história do esporte. "
        "Lamine Yamal não jogava com medo de veteranos; jogava como quem se diverte na rua. "
        "Ao lado de Nico Williams, a Espanha encontrou duas flechas que destruíram as defesas mais temidas do planeta. "
        "Na Eurocopa, o golaço antológico de Yamal contra a França de Kylian Mbappé calou os críticos "
        "e fez o planeta perceber que um gênio geracional havia nascido para herdar o trono do futebol. "
        "O ápice da nova dinastia veio com a conquista histórica da Copa do Mundo de dois mil e vinte e seis. "
        "Vencendo a Argentina de Messi na grande final, a Fúria Vermelha se sagrou bicampeã mundial com autoridade absoluta. "
        "E agora, na Super Data FIFA de outubro, eles provaram que o domínio é eterno. "
        "Em pleno lendário estádio de Wembley, a Espanha de Yamal enfrentou a badalada Inglaterra de Thomas Tuchel, Kane e Bellingham. "
        "O resultado foi mais uma aula tática: vitória por três a dois, dribles desconcertantes "
        "e a imprensa britânica admitindo que a Espanha joga em outra dimensão. "
        "Enquanto gigantes como Brasil, França e Alemanha buscam desesperadamente reconstruir suas identidades, "
        "a Espanha já tem a espinha dorsal mais jovem e dominante das próximas duas décadas. "
        "Com elenco farto, liderança sólida e o maior jovem talento desde Lionel Messi, "
        "o novo império do futebol está consolidado. "
        "A grande pergunta que fica para os amantes do esporte é simples: "
        "alguém será capaz de derrubar a dinastia espanhola antes da próxima década?"
    ),
    "DOCUMENTARIO_BRASIL_A_FAXINA_DE_ANCELOTTI.mp4": (
        "Desde o pentacampeonato mundial em dois mil e dois, a Seleção Brasileira se transformou em uma máquina de decepções. "
        "Eliminações dolorosas, vexame histórico do sete a um em casa e gerações talentosas que sucumbiram à falta de disciplina e ao comodismo. "
        "A camisa mais pesada do futebol mundial passou a ser tratada por muitos como passarela de vaidades e clube de amigos. "
        "Treinadores caíam um após o outro, mas a estrutura viciada nos bastidores da CBF continuava intocável. "
        "O torcedor brasileiro cansou de sofrer e abandonou o patriotismo verde e amarelo. "
        "Diante do abismo e da pressão popular, a CBF quebrou um tabu centenário e tomou a decisão mais drástica de sua história: "
        "contratar um treinador estrangeiro de elite mundial. Carlo Ancelotti, o técnico mais vitorioso da Champions League, "
        "aceitou o desafio de comandar a reconstrução da Amarelinha. "
        "Don Carlo não trouxe apenas bagagem tática; trouxe autoridade inquestionável, calma de campeão "
        "e a coragem necessária para tomar medidas impopulares que nenhum comandante brasileiro teve peito de adotar. "
        "A primeira atitude de Ancelotti foi uma verdadeira revolução silenciosa nos bastidores. "
        "O fim dos privilégios de celebridade, o fim das visitas de influenciadores e o corte impiedoso de medalhões "
        "que não demonstravam comprometimento físico ou tático. "
        "Nesta Data FIFA de outubro, a lista de convocados e as atuações em campo mandaram um recado fulminante: "
        "não há vaga cativa por nome ou número de seguidores. "
        "Com uma goleada implacável de quatro a zero e intensidade sufocante, "
        "a Seleção Brasileira voltou a competir com seriedade militar. "
        "A transição ainda está em andamento, mas o sinal de alerta para os gigantes europeus já soou. "
        "O futebol brasileiro redescobriu que o talento natural só atinge o ápice quando combinado com organização de nível europeu. "
        "Sob a batuta serena de Carlo Ancelotti e liderada por uma juventude faminta e sem medo de cara feia, "
        "o gigante adormecido da América do Sul finalmente acordou. "
        "E você? Acredita que Don Carlo é o homem que vai trazer o sonhado hexa, "
        "ou a Seleção Brasileira ainda precisa de tempo para curar suas velhas feridas?"
    )
}

DOCS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios_longos")

def queimar_legendas(video_name, script_text):
    video_path = os.path.join(DOCS_DIR, video_name)
    if not os.path.exists(video_path):
        logger.error(f"Vídeo não encontrado: {video_path}")
        return

    logger.info(f"\n==========================================")
    logger.info(f"Sincronizando e queimando legendas em: {video_name}")
    
    # 1. Gera áudio e obtém SRT perfeito do SubMaker
    audio_tmp = "temp_voice_sync.mp3"
    sm = voice.azure_tts_v1(script_text, "pt-BR-AntonioNeural", 1.0, audio_tmp)
    if not sm:
        logger.error("Falha ao gerar voz")
        return
        
    srt_content = sm.get_srt()
    
    # 2. Converte SRT para ASS agrupando palavras
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
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Arial Black,50,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,30,30,80,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    events = []
    chunk_size = 5
    for i in range(0, len(word_entries), chunk_size):
        chunk = word_entries[i:i+chunk_size]
        t_start = chunk[0]["start"]
        t_end = chunk[-1]["end"]
        phrase = " ".join([c["text"].lower() for c in chunk])
        events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{phrase}")

    ass_file = "sync_legendas.ass"
    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))

    # 3. Queima as legendas no vídeo com FFmpeg
    temp_out = os.path.join(DOCS_DIR, f"LEGENDADO_{video_name}")
    cmd = [
        FFMPEG, "-y",
        "-i", video_path,
        "-vf", f"ass={ass_file}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "copy",
        "-movflags", "+faststart",
        temp_out
    ]
    logger.info("Renderizando vídeo com legendas amarelas...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(temp_out) and os.path.getsize(temp_out) > 5000000:
        os.replace(temp_out, video_path)
        logger.success(f"VÍDEO 100% LEGENDADO E ATUALIZADO: {video_path}")
    else:
        logger.error(f"Erro ao queimar legendas: {res.stderr[:400]}")

    if os.path.exists(ass_file):
        os.remove(ass_file)
    if os.path.exists(audio_tmp):
        os.remove(audio_tmp)

if __name__ == "__main__":
    for vname, script in SCRIPTS.items():
        queimar_legendas(vname, script)
