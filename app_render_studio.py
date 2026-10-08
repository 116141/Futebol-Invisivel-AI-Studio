import os
import sys
import re
import uuid
import random
import shutil
import subprocess
import imageio_ffmpeg
from loguru import logger
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
import yt_dlp
from app.services import voice, llm

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(FFMPEG)
if ffmpeg_dir not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]

SHORTS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "shorts")
DOCS_DIR = os.path.join("canais", "canal_01_futebol_invisivel", "videos_prontos", "documentarios")
MODA_DIR = os.path.join("canais", "canal_04_achadinhos_moda_feminina", "videos_prontos")
os.makedirs(SHORTS_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(MODA_DIR, exist_ok=True)

app = FastAPI(title="Futebol Invisível & Alana Cruz AI Studio")

TASKS = {}

def processar_video(task_id: str, titulo: str, tipo: str, uploaded_image_paths: list = None, promo_raw: str = ""):
    try:
        is_doc = (tipo == "doc")
        is_afiliado = (tipo == "afiliado_moda")
        aspect_ratio = "16:9" if is_doc else "9:16"
        res_scale = "1920:1080" if is_doc else "1080:1920"
        if is_afiliado:
            target_dir = MODA_DIR
        elif is_doc:
            target_dir = DOCS_DIR
        else:
            target_dir = SHORTS_DIR
        
        # Extrair link de afiliado e detalhes do texto bruto do AliExpress se fornecido
        link_afiliado = ""
        preco_afiliado = ""
        if promo_raw:
            link_match = re.search(r'https?://[^\s]+', promo_raw)
            if link_match:
                link_afiliado = link_match.group(0).rstrip('.,;)')
            preco_match = re.search(r'(?:USD|R\$|US\$|EUR)\s*[\d\.,]+', promo_raw, re.IGNORECASE)
            if preco_match:
                preco_afiliado = preco_match.group(0)
                
            # Se o título estiver vazio ou genérico, extrai o nome do produto do texto promocional
            if len(titulo.strip()) < 5:
                linhas = [l.strip() for l in promo_raw.splitlines() if l.strip() and not l.startswith("http") and "preço" not in l.lower() and "compre" not in l.lower() and "recomendações" not in l.lower()]
                if linhas:
                    titulo = linhas[0][:80]
        
        if is_afiliado:
            TASKS[task_id]["status"] = "Gerando Copywriting Viral de Vendas (Moda Feminina)..."
            voz_locutor = "pt-BR-FranciscaNeural"  # Voz feminina envolvente para moda
            tempo_desc = "um vídeo vertical de 35 a 45 segundos para TikTok e Instagram Reels"
            
            # 4 Ângulos Dinâmicos de Copywriting para evitar repetição
            estilos_copy = [
                {
                    "nome": "achadinho_secreto",
                    "diretriz": "Foque no GATILHO DE DESCOBERTA E PREÇO BAIXO (ex: 'Parem tudo! Vocês não têm noção do achadinho que eu encontrei...', 'Parece que custou mil reais, mas paguei preço de banana...'). Enfatize o desconto secreto e como vale cada centavo.",
                    "fallback": (
                        f"Parem tudo, meninas! Vocês não têm noção da perfeição que eu acabei de encontrar: {titulo}! "
                        "Parece que foi comprada numa boutique de luxo caríssima, mas o preço é inacreditável de tão barato! "
                        "O tecido é maravilhoso, não amassa fácil e veste tão bem que todo mundo elogia. "
                        "Achei o link oficial com um cupom de desconto exclusivo! Já deixei liberado no primeiro comentário fixado e na bio. "
                        "Corre para garantir o seu antes que o estoque esgote!"
                    )
                },
                {
                    "nome": "old_money_elegancia",
                    "diretriz": "Foque no GATILHO DE STATUS, ELEGÂNCIA E ALFAIATARIA (ex: 'Como parecer elegante e milionária sem gastar quase nada...', 'Essa é a peça que transforma qualquer mulher comum em uma mulher de respeito...'). Destaque a modelagem da cintura e caimento impecável.",
                    "fallback": (
                        f"Como parecer elegante, sofisticada e milionária sem gastar quase nada? O segredo é essa peça: {titulo}! "
                        "O caimento é pura alta costura: desenha a silhueta, afina a cintura e passa uma postura de puro luxo. "
                        "Dá pra usar em festas, eventos formais ou até num jantar especial. É aquela roupa que te faz ser o centro das atenções! "
                        "O link com desconto garantido está no primeiro comentário fixado e na bio. Aproveita enquanto ainda tem o seu tamanho!"
                    )
                },
                {
                    "nome": "indicacao_amiga",
                    "diretriz": "Foque no TOM DE DESABAFO E CONFISSÃO DE AMIGA (ex: 'Meninas, eu juro que não dava nada por essa roupa, mas quando chegou fiquei chocada...', 'Precisava vir correndo indicar isso pra vocês...'). Foque no toque macio, conforto real e que não aperta.",
                    "fallback": (
                        f"Meninas, confissão sincera: eu não esperava que fosse tão perfeito assim, mas quando vi {titulo}, fiquei apaixonada! "
                        "O toque do tecido é macio dos sonhos, super confortável, não aperta nada e modela o corpo com uma leveza incrível. "
                        "Chegou super rápido e a qualidade é muito acima do esperado. Vale cada centavo! "
                        "Quem quiser o link com o preço promocional, acabei de fixar no primeiro comentário e na bio! Corre antes que acabe!"
                    )
                },
                {
                    "nome": "urgencia_tendencia",
                    "diretriz": "Foque no GATILHO DE TENDÊNCIA VIRAL E ESCASSEZ (ex: 'Essa é oficialmente a peça mais desejada do momento na internet...', 'Se você ainda não tem, precisa garantir antes que saia do ar...'). Crie FOMO (medo de ficar de fora).",
                    "fallback": (
                        f"Essa é oficialmente a peça mais desejada e comentada do momento: {titulo}! "
                        "Todo mundo nas redes sociais tá usando porque simplesmente valoriza demais o corpo e combina com absolutamente tudo. "
                        "É aquela peça curinga que não pode faltar no guarda-roupa de uma mulher estilosa em 2026. "
                        "Mas atenção: as unidades na promoção estão acabando muito rápido! O link oficial está no primeiro comentário fixado e na bio. Não fica sem a sua!"
                    )
                }
            ]
            
            copy_escolhida = random.choice(estilos_copy)
            logger.info(f"Ângulo de Copywriting Selecionado: {copy_escolhida['nome']}")
            
            prompt_script = f"""
            Você é a Alana Cruz, uma influenciadora carismática de moda feminina e achadinhos elegantes.
            Crie um roteiro falado em português (pt-BR) de {tempo_desc} promovendo a peça: '{titulo}'.
            ESTILO ESPECÍFICO DESTE VÍDEO:
            {copy_escolhida['diretriz']}
            
            REGRAS OBRIGATÓRIAS:
            - Comece nos primeiros 2 segundos com o gancho exato do estilo escolhido.
            - Fale de forma natural, envolvente, feminina e empática (como uma amiga estilosa).
            - Termine chamando para clicar no link com desconto no primeiro comentário fixado e na bio.
            - Retorne APENAS o texto falado puro, sem [Cena], sem [Alana], sem aspas.
            """
        else:
            TASKS[task_id]["status"] = "Selecionando Ângulo Investigativo Exclusivo..."
            voz_locutor = "pt-BR-AntonioNeural"
            tempo_desc = "um super documentário investigativo de 2 a 3 minutos com capítulos" if is_doc else "um SHORT vertical viral de 40 a 50 segundos"
            
            # Sistema de 4 Pegadas Diferentes para o Canal de Futebol Não Ficar Repetitivo
            pegadas_futebol = [
                {
                    "nome": "ESCÂNDALO_E_VALORES",
                    "diretriz": "FOCO EM DINHEIRO, MULTAS E ACORDOS SECRETOS. Comece revelando uma quantia astronômica ou cláusula oculta que a diretoria tentou abafar. Use tom jornalístico investigativo sério e direto.",
                    "fallback_short": f"Milhões de euros em jogo e uma cláusula que ninguém podia saber! Os bastidores da negociação envolvendo {titulo} revelam um contrato confidencial que mudou tudo no vestiário. Dirigentes tentaram esconder os números reais, mas a verdade vazou na imprensa europeia. Você aceitaria esse valor? Comente e se inscreva no Futebol Invisível!",
                    "fallback_doc": f"A rota do dinheiro e a verdade oculta sobre {titulo}! Capítulo um: O contrato que a diretoria quis queimar. Nos bastidores do futebol, planilhas financeiras mostram valores astronômicos e comissões ilícitas. Capítulo dois: As consequências no vestiário e a revolta dos atletas. Quem realmente lucrou com isso? Comente e se inscreva no Futebol Invisível!"
                },
                {
                    "nome": "TRAIÇÃO_E_POLÊMICA_INTERNA",
                    "diretriz": "FOCO EM RACHA DE ELENCO, MOTIM E TRAIÇÃO. Comece com um atrito violento entre jogadores ou técnico nos vestiários. Tom tenso, misterioso e chocante.",
                    "fallback_short": f"O clima esquentou nos vestiários e o elenco rachou de vez por causa de {titulo}! Testemunhas relatam discussões acaloradas entre os líderes do time que as câmeras de TV não mostraram. As decisões impostas pela diretoria geraram uma guerra de egos sem volta. De que lado você ficaria? Diga nos comentários e siga o Futebol Invisível!",
                    "fallback_doc": f"A ruptura interna e o motim secreto sobre {titulo}! Capítulo um: Portas fechadas e o estopim da briga. O que parecia um ambiente tranquilo virou um campo de batalha interno. Capítulo dois: O silêncio forçado e as saídas iminentes. Jogadores ameaçaram greve caso a diretoria não recuasse. Essa crise tem conserto? Participe nos comentários e se inscreva no Futebol Invisível!"
                },
                {
                    "nome": "EMOÇÃO_E_LEGADO_HISTÓRICO",
                    "diretriz": "FOCO EM GLÓRIA, LÁGRIMAS, PRESSÃO E ETERNIDADE. Comece narrando o peso de uma decisão, a dor da torcida ou um momento épico inesquecível. Tom épico, solene e comovente.",
                    "fallback_short": f"O dia em que o futebol se curvou e o mundo inteiro se emocionou com {titulo}! Anos de pressão extrema, cobranças cruéis e a resposta definitiva dentro das quatro linhas. O choro e o desabafo diante de multidões provam que a história foi reescrita para sempre. Ele já é uma lenda intocável? Deixe seu tributo e se inscreva no Futebol Invisível!",
                    "fallback_doc": f"A consagração e o preço da eternidade em {titulo}! Capítulo um: O calvário e as lágrimas antes da glória. Foram anos carregando o peso das críticas nos ombros. Capítulo dois: O adeus épico e o silêncio do estádio. Palavras que calaram a crítica mundial e marcaram gerações. Algum dia veremos algo parecido? Comente sua homenagem e siga o canal Futebol Invisível!"
                },
                {
                    "nome": "VINGANÇA_E_A_RESPOSTA_NO_CAMPO",
                    "diretriz": "FOCO EM VOLTA POR CIMA, HUMILHAÇÃO DE RIVAIS E RESPOSTA AOS CRÍTICOS. Comece citando uma frase que duvidou dele ou uma injustiça que foi vingada dentro de campo. Tom agressivo, vibrante e provocador.",
                    "fallback_short": f"Eles duvidaram, zombaram da cara dele, mas a resposta de {titulo} calou o planeta! Chamado de acabado e descartado pelos especialistas, ele entrou em campo com sangue nos olhos para destruir todas as previsões. A vingança foi servida no momento mais decisivo da temporada. Quem ri por último ri melhor? Comente quem errou a previsão e se inscreva no Futebol Invisível!",
                    "fallback_doc": f"A vingança definitiva e o silêncio dos críticos sobre {titulo}! Capítulo um: As humilhações e o descarte público. A imprensa cravou o fim, mas nos bastidores a fúria estava armada. Capítulo dois: O massacre em campo e o troco histórico. Uma exibição impecável que desmontou planos milionários de rivais. Você também duvidou dele? Confesse nos comentários e se inscreva no Futebol Invisível!"
                }
            ]
            
            pegada_escolhida = random.choice(pegadas_futebol)
            logger.info(f"Pegada do Roteiro de Futebol Selecionada: {pegada_escolhida['nome']}")
            
            prompt_script = f"""
            Você é o roteirista investigativo do canal @FutebolInvisivelOficial no YouTube.
            Crie um roteiro ORIGINAL, INÉDITO e HIPNOTIZANTE em português (pt-BR) para {tempo_desc} sobre o tema: '{titulo}'.
            
            PEGADA OBRIGATÓRIA DESTE VÍDEO ({pegada_escolhida['nome']}):
            {pegada_escolhida['diretriz']}
            
            DIRETRIZES ANTI-CONTEÚDO REPETITIVO (CRÍTICO PARA MONETIZAÇÃO DO YOUTUBE):
            - PROIBIDO usar introduções repetitivas como 'A verdade que ninguém fala', 'Nos bastidores...', 'Você não vai acreditar'.
            - Comece nos primeiros 2 segundos com um FATO ESPECÍFICO, uma data, uma cifra milionária, uma frase marcante ou uma ação direta.
            - Desenvolva uma linha narrativa própria conectando eventos reais e o impacto psicológico/financeiro no futebol.
            - Termine de forma dinâmica convidando o espectador a opinar nos comentários e se inscrever no canal Futebol Invisível.
            - Retorne APENAS o texto falado da narração pura, sem marcadores como [Narrador], sem [Cena], sem emojis.
            """
                roteiro_gerado = llm.generate_script(prompt_script)
                roteiro_limpo = re.sub(r'\[.*?\]', '', roteiro_gerado).strip()
                roteiro_limpo = roteiro_limpo.replace('**', '').replace('##', '')
                if len(roteiro_limpo) > 60 and "Error:" not in roteiro_limpo and "503" not in roteiro_limpo:
                    roteiro = roteiro_limpo
                else:
                    raise ValueError("Erro de resposta da IA")
            except Exception:
                roteiro = pegada_escolhida["fallback_doc"] if is_doc else pegada_escolhida["fallback_short"]
            
        TASKS[task_id]["roteiro"] = roteiro
        TASKS[task_id]["status"] = "Gerando Narração e Sincronia de Legendas..."
        
        temp_dir = f"temp_web_build_{task_id[:8]}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Áudio com voz apropriada
        audio_path = os.path.join(temp_dir, "audio.mp3")
        sm = voice.azure_tts_v1(roteiro, voz_locutor, 1.0, audio_path)
        srt_content = sm.get_srt() if sm else ""
        
        clip_files = []
        clip_idx = 1
        
        # Se o usuário enviou imagens do produto, transformamos em clipes cinematográficos de alta fidelidade
        if uploaded_image_paths and len(uploaded_image_paths) > 0:
            TASKS[task_id]["status"] = "Animando Fotos Oficiais do Anúncio com Alta Precisão..."
            # Criar variações de efeitos (zoom in no detalhe, zoom out elegante, panorâmica vertical suave)
            efeitos = [
                "zoompan=z='min(zoom+0.002,1.20)':d=105:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30", # Zoom in central
                "zoompan=z='if(lte(zoom,1.0),1.20,max(1.001,zoom-0.002))':d=105:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30", # Zoom out revelação
                "zoompan=z='1.12':d=105:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),(ih-ih/zoom)/2,y-0.6)':s=1080x1920:fps=30", # Panorâmica sutil
                "zoompan=z='min(zoom+0.0015,1.15)':d=105:x='iw/2-(iw/zoom/2)':y='ih*0.25':s=1080x1920:fps=30" # Foco no decote / parte superior
            ]
            for i, img_p in enumerate(uploaded_image_paths):
                c_img_out = os.path.join(temp_dir, f"clip_img_{clip_idx:02d}.mp4")
                ef = efeitos[i % len(efeitos)]
                cmd_img = [
                    FFMPEG, "-y", "-loop", "1", "-i", img_p, "-t", "3.8",
                    "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{ef}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    c_img_out
                ]
                subprocess.run(cmd_img, capture_output=True)
                if os.path.exists(c_img_out) and os.path.getsize(c_img_out) > 50000:
                    clip_files.append(c_img_out)
                    clip_idx += 1

        # Busca de Vídeos Externos Apenas Quando Necessário ou Altamente Específico
        downloaded = []
        # Se NÃO temos fotos do anúncio OU se for futebol/documentário, a busca no YouTube é obrigatória
        precisa_buscar_video = (not uploaded_image_paths or len(uploaded_image_paths) == 0 or not is_afiliado)
        
        if precisa_buscar_video:
            TASKS[task_id]["status"] = "Buscando Vídeos Reais no YouTube..."
            ydl_opts = {
                'format': 'best',
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                'outtmpl': os.path.join(temp_dir, 'source_%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'max_downloads': 1
            }
            
            if is_afiliado:
                queries = [
                    f"ytsearch1:{titulo} try on haul review",
                    f"ytsearch1:{titulo} outfit in motion"
                ]
            else:
                queries = [
                    f"ytsearch1:{titulo} soccer football highlights",
                    f"ytsearch1:{titulo} match skills goals"
                ]
            for q in queries:
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.extract_info(q, download=True)
                except Exception as e:
                    logger.info(f"Busca: {e}")
                    
            downloaded = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("source_") and f.endswith(".mp4")]
        else:
            logger.info("Modo Afiliado: Fotos oficiais fornecidas pelo usuário. Usando 100% imagens reais do anúncio para precisão absoluta!")

        TASKS[task_id]["status"] = f"Cortando Clipes em {aspect_ratio} e Editando..."
        
        offsets = [10, 20, 30, 45, 60, 75, 90, 110, 130] if is_doc else [10, 20, 30, 45, 60]
        max_clips = 12 if is_doc else 6
        
        for v in downloaded:
            for off in offsets:
                c_out = os.path.join(temp_dir, f"clip_vid_{clip_idx:02d}.mp4")
                if is_doc:
                    vf_filter = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30"
                else:
                    vf_filter = "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30"
                
                cmd = [
                    FFMPEG, "-y", "-ss", str(off), "-i", v, "-t", "3.5", "-an",
                    "-vf", vf_filter,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
                    c_out
                ]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(c_out) and os.path.getsize(c_out) > 50000:
                    clip_files.append(c_out)
                    clip_idx += 1
                if len(clip_files) >= max_clips:
                    break
            if len(clip_files) >= max_clips:
                break
                
        # Se mesmo com fotos ainda faltar clipes para preencher o tempo da narração, duplicar as fotos com ângulos invertidos
        if len(clip_files) < 4 and uploaded_image_paths:
            for i, img_p in enumerate(uploaded_image_paths):
                c_loop_out = os.path.join(temp_dir, f"clip_loop_{clip_idx:02d}.mp4")
                cmd_loop = [
                    FFMPEG, "-y", "-loop", "1", "-i", img_p, "-t", "3.5",
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0018,1.18)':d=105:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    c_loop_out
                ]
                subprocess.run(cmd_loop, capture_output=True)
                if os.path.exists(c_loop_out):
                    clip_files.append(c_loop_out)
                    clip_idx += 1

        if len(clip_files) < 1:
            raise Exception("Não foi possível gerar clipes suficientes.")
            
        concat_txt = os.path.join(temp_dir, "concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in clip_files:
                f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")
                
        concat_video = os.path.join(temp_dir, "combined.mp4")
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", concat_video], capture_output=True)
        
        # Legendas
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

        res_x = 1920 if is_doc else 1080
        res_y = 1080 if is_doc else 1920
        font_size = 54 if is_doc else 80
        margin_v = 70 if is_doc else 400

        header = (
            f"[Script Info]\nScriptType: v4.00+\nPlayResX: {res_x}\nPlayResY: {res_y}\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Default,Impact,{font_size},&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,40,40,{margin_v},1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
        events = []
        chunk_size = 6 if is_doc else 4
        for i in range(0, len(word_entries), chunk_size):
            chunk = word_entries[i:i+chunk_size]
            t_start = chunk[0]["start"]
            t_end = chunk[-1]["end"]
            phrase = " ".join([c["text"].upper() for c in chunk])
            events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{phrase}")

        ass_file = "temp_render_studio.ass"
        with open(ass_file, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events))
            
        # Render Final
        if is_afiliado:
            prefix = "AFILIADO_MODA"
        elif is_doc:
            prefix = "DOCUMENTARIO"
        else:
            prefix = "SHORT"
        TASKS[task_id]["status"] = f"Renderizando {prefix} em Full HD ({aspect_ratio})..."
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', titulo)[:30]
        final_filename = f"{prefix}_{clean_name}_{task_id[:6]}.mp4"
        final_path = os.path.join(target_dir, final_filename)
        
        cmd_render = [
            FFMPEG, "-y",
            "-stream_loop", "-1", "-i", concat_video,
            "-i", audio_path,
            "-vf", f"ass={ass_file}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            final_path
        ]
        res = subprocess.run(cmd_render, capture_output=True, text=True)
        if os.path.exists(ass_file):
            os.remove(ass_file)

        if os.path.exists(final_path) and os.path.getsize(final_path) > 1000000:
            TASKS[task_id]["status"] = "CONCLUÍDO"
            TASKS[task_id]["file_path"] = final_path
            TASKS[task_id]["file_name"] = final_filename
            
            # Pacote Completo de Postagem (1-Clique)
            link_display = link_afiliado if link_afiliado else "https://s.click.aliexpress.com/..."
            if is_afiliado:
                post_titulo = f"{titulo[:65]}! ✨ | Alana Cruz #Shorts"
                post_desc = (
                    f"Meninas, olha essa perfeição: {titulo}! Modela o corpo, caimento impecável e super confortável. 💕\n\n"
                    f"🛍️ Link oficial com desconto exclusivo:\n👉 {link_display}\n\n"
                    f"Se inscreva no canal Alana Cruz para mais achadinhos elegantes de moda feminina! ✨\n\n"
                    f"#modafeminina #vestidofesta #achadinhos #aliexpress #lookdodia #shorts"
                )
                post_coment = f"🛍️ Link oficial com desconto promocional:\n👉 {link_display} 💕"
            else:
                post_titulo = f"{titulo[:70]} | Futebol Invisível #Shorts"
                post_desc = (
                    f"A investigação completa dos bastidores sobre {titulo}! Inscreva-se no canal Futebol Invisível.\n\n"
                    f"#futebol #futebolinvisivel #shorts #polemica #bastidores"
                )
                post_coment = "Deixe sua opinião nos comentários e se inscreva no canal Futebol Invisível!"
                
            TASKS[task_id]["post_titulo"] = post_titulo
            TASKS[task_id]["post_descricao"] = post_desc
            TASKS[task_id]["post_comentario"] = post_coment
            
            # Salvar ficheiro .TXT completo com as informações para guardar e postar depois
            txt_filename = final_filename.rsplit('.', 1)[0] + "_POSTAGEM.txt"
            txt_path = os.path.join(target_dir, txt_filename)
            with open(txt_path, "w", encoding="utf-8") as f_txt:
                f_txt.write("====================================================\n")
                f_txt.write(f"FICHA DE POSTAGEM - {prefix}\n")
                f_txt.write("====================================================\n\n")
                f_txt.write(f"📌 TÍTULO DO VÍDEO:\n{post_titulo}\n\n")
                f_txt.write(f"📝 DESCRIÇÃO COM HASHTAGS:\n{post_desc}\n\n")
                f_txt.write(f"💬 1º COMENTÁRIO FIXADO (LINK DIRETO):\n{post_coment}\n\n")
                if link_afiliado:
                    f_txt.write(f"🔗 LINK DE AFILIADO PURO:\n{link_afiliado}\n\n")
                if roteiro:
                    f_txt.write(f"🎙️ ROTEIRO NARRADO:\n{roteiro}\n")
            
            # Gerar Capa/Thumbnail Cinematográfica Profissional para Documentários
            if is_doc:
                try:
                    thumb_filename = f"CAPA_{clean_name}_{task_id[:6]}.jpg"
                    thumb_path = os.path.join(target_dir, thumb_filename)
                    # Extrai o frame de maior impacto visual do meio do documentário
                    vf_thumb = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,drawbox=y=ih-260:color=black@0.65:width=iw:height=260:t=fill,drawtext=text='FUTEBOL INVISÍVEL':fontcolor=yellow:fontsize=75:x=(w-text_w)/2:y=h-210,drawtext=text='DOCUMENTÁRIO INVESTIGATIVO':fontcolor=white:fontsize=42:x=(w-text_w)/2:y=h-110"
                    cmd_thumb = [
                        FFMPEG, "-y",
                        "-ss", "15",
                        "-i", final_path,
                        "-vframes", "1",
                        "-vf", vf_thumb,
                        "-q:v", "2",
                        thumb_path
                    ]
                    subprocess.run(cmd_thumb, capture_output=True)
                    if os.path.exists(thumb_path):
                        TASKS[task_id]["thumb_path"] = thumb_path
                        TASKS[task_id]["thumb_name"] = thumb_filename
                        logger.info(f"Capa Cinematográfica Gerada: {thumb_path}")
                except Exception as e_thumb:
                    logger.warning(f"Não foi possível gerar thumbnail automática: {e_thumb}")
                
            logger.success(f"{prefix} CONCLUÍDO: {final_path} | TXT: {txt_path}")
        else:
            TASKS[task_id]["status"] = f"Erro na renderização final: {res.stderr[:200]}"
            
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        logger.error(f"Erro na tarefa {task_id}: {e}")
        TASKS[task_id]["status"] = f"Erro: {str(e)}"

# === INTERFACE WEB DUPLA (SHORTS + DOCUMENTÁRIOS) ===
HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Futebol Invisível AI Studio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0b1120; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .card-custom { background: #1e293b; border: 1px solid #334155; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .btn-gold { background: linear-gradient(135deg, #eab308, #ca8a04); color: #000; font-weight: 700; border: none; }
        .btn-gold:hover { background: linear-gradient(135deg, #facc15, #eab308); color: #000; }
        .btn-doc { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: #fff; font-weight: 700; border: none; }
        .btn-doc:hover { background: linear-gradient(135deg, #60a5fa, #2563eb); color: #fff; }
        .glow { text-shadow: 0 0 15px rgba(234, 179, 8, 0.4); }
        .form-check-input:checked { background-color: #eab308; border-color: #eab308; }
    </style>
</head>
<body class="py-5">
    <div class="container" style="max-width: 820px;">
        <div class="text-center mb-5">
            <h1 class="fw-bold glow text-warning">⚽ FUTEBOL INVISÍVEL AI STUDIO</h1>
            <p class="text-secondary fs-5">Fábrica Automática de Documentários (16:9) e Shorts Virais (9:16)</p>
        </div>

        <div class="card card-custom p-4 mb-4">
            <h4 class="mb-3 text-light">🚀 Criar Vídeo Inteligente em 1 Clique</h4>
            <form id="createForm">
                <div class="mb-3">
                    <label class="form-label text-light fw-bold">1. Digite o TEMA, TÍTULO ou PRODUTO:</label>
                    <input type="text" id="tituloInput" class="form-control form-control-lg bg-dark text-light border-secondary" 
                           placeholder="Ex: Vestido Longo Elegante Tendência 2026 / Conjunto Alfaiataria Feminino / Caso Negreira" required>
                </div>

                <div class="mb-4">
                    <label class="form-label text-light fw-bold">2. Escolha o Formato do Conteúdo:</label>
                    <div class="row g-3">
                        <div class="col-md-4">
                            <div class="p-3 bg-dark rounded border border-secondary d-flex align-items-center h-100">
                                <input class="form-check-input me-3" type="radio" name="tipoVideo" id="tipoShort" value="short" checked>
                                <label class="form-check-label text-light" for="tipoShort">
                                    <strong>📱 SHORTS FUTEBOL (9:16)</strong><br>
                                    <small class="text-secondary">Viral rápido (45-55s), cortes dinâmicos.</small>
                                </label>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="p-3 bg-dark rounded border border-secondary d-flex align-items-center h-100">
                                <input class="form-check-input me-3" type="radio" name="tipoVideo" id="tipoDoc" value="doc">
                                <label class="form-check-label text-light" for="tipoDoc">
                                    <strong>🎬 DOCUMENTÁRIO (16:9)</strong><br>
                                    <small class="text-secondary">Horizontal TV investigativo com capítulos.</small>
                                </label>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="p-3 bg-dark rounded border border-secondary d-flex align-items-center h-100" style="border-color: #ec4899 !important;">
                                <input class="form-check-input me-3" type="radio" name="tipoVideo" id="tipoAfiliado" value="afiliado_moda">
                                <label class="form-check-label text-light" for="tipoAfiliado">
                                    <strong class="text-pink" style="color: #f472b6;">🛍️ MODA / AFILIADO (9:16)</strong><br>
                                    <small class="text-secondary">Voz feminina, lookbooks reais, CTA de compra no TikTok/Reels.</small>
                                </label>
                            </div>
                        </div>
                    </div>
                <div class="mb-3" id="campoPromoBox">
                    <label class="form-label text-light fw-bold">📋 Ou cole o Texto Promocional do AliExpress (com o Link e Preço):</label>
                    <textarea id="promoInput" class="form-control bg-dark text-light border-secondary" rows="3" 
                              placeholder="Cole aqui o que você copiou do AliExpress (ex: Principais recomendações... Agora preço: USD 3.18... Clique e compre: https://s.click.aliexpress.com/...)"></textarea>
                    <small class="text-secondary">O estúdio vai ler o produto, o preço e o seu link direto, gerando o roteiro e o kit completo de postagem para copiar e colar!</small>
                </div>

                <div class="mb-4">
                    <label class="form-label text-light fw-bold">3. Fotos Oficiais do Produto (Opcional - Ex: Baixadas do AliExpress):</label>
                    <input type="file" id="fotosInput" class="form-control bg-dark text-light border-secondary" multiple accept="image/*">
                    <small class="text-secondary">Se você anexar as fotos, elas serão animadas em Full HD com efeito Ken Burns e mescladas com os vídeos de pessoas reais em movimento.</small>
                </div>

                <button type="submit" class="btn btn-gold btn-lg w-100" id="btnSubmit">⚡ GERAR VÍDEO COMPLETO AGORA</button>
            </form>
        </div>

        <div class="card card-custom p-4 mb-4">
            <h5 class="text-warning mb-3">📋 Vídeos Sendo Gerados e Prontos (Ao Vivo):</h5>
            <div id="listaTarefas" class="list-group">
                <div class="text-secondary small p-3 text-center">Nenhum vídeo em andamento no momento.</div>
            </div>
        </div>

        <div id="progressCard" class="card card-custom p-4 d-none mb-4">
            <h5 class="text-warning">Status do Vídeo Atual:</h5>
            <div class="d-flex align-items-center my-3">
                <div class="spinner-border text-warning me-3" role="status" id="spinner"></div>
                <span id="statusText" class="fs-5 text-light fw-bold">Iniciando...</span>
            </div>
            
            <div id="downloadBox" class="d-none mb-3 d-flex gap-2">
                <a id="btnDownload" href="#" class="btn btn-success btn-lg flex-grow-1 fw-bold">📥 BAIXAR VÍDEO (MP4)</a>
                <a id="btnDownloadTxt" href="#" class="btn btn-outline-warning btn-lg fw-bold px-4">📄 BAIXAR FICHA (TXT)</a>
            </div>

            <!-- KIT COMPLETO DE POSTAGEM PRONTO (1-CLIQUE) -->
            <div id="postKitBox" class="d-none p-3 bg-dark rounded border border-warning">
                <h5 class="text-warning fw-bold mb-3">🚀 Kit Pronto Para Postar (Copie e Cole):</h5>
                
                <div class="mb-3">
                    <label class="text-secondary small fw-bold">TÍTULO SUGERIDO:</label>
                    <div class="input-group">
                        <input type="text" id="kitTitulo" class="form-control bg-black text-light border-secondary" readonly>
                        <button class="btn btn-outline-warning" onclick="copiarTexto('kitTitulo')">Copiar</button>
                    </div>
                </div>

                <div class="mb-3">
                    <label class="text-secondary small fw-bold">DESCRIÇÃO COM HASHTAGS:</label>
                    <div class="input-group">
                        <textarea id="kitDescricao" class="form-control bg-black text-light border-secondary" rows="4" readonly></textarea>
                        <button class="btn btn-outline-warning" onclick="copiarTexto('kitDescricao')">Copiar</button>
                    </div>
                </div>

                <div class="mb-3">
                    <label class="text-secondary small fw-bold">1º COMENTÁRIO FIXADO (COM SEU LINK DE COMPRA):</label>
                    <div class="input-group">
                        <input type="text" id="kitComentario" class="form-control bg-black text-light border-secondary" readonly>
                        <button class="btn btn-outline-warning" onclick="copiarTexto('kitComentario')">Copiar</button>
                    </div>
                </div>
            </div>

            <div id="roteiroBox" class="p-3 bg-dark rounded border border-secondary text-secondary small d-none mt-3"></div>
        </div>
    </div>

    <script>
        const form = document.getElementById('createForm');
        const progressCard = document.getElementById('progressCard');
        const statusText = document.getElementById('statusText');
        const spinner = document.getElementById('spinner');
        const roteiroBox = document.getElementById('roteiroBox');
        const downloadBox = document.getElementById('downloadBox');
        const btnDownload = document.getElementById('btnDownload');
        const btnSubmit = document.getElementById('btnSubmit');
        const listaTarefas = document.getElementById('listaTarefas');

        async function carregarTarefas() {
            try {
                const res = await fetch('/api/tarefas');
                const tarefas = await res.json();
                const keys = Object.keys(tarefas);
                if (keys.length === 0) {
                    listaTarefas.innerHTML = '<div class="text-secondary small p-3 text-center">Nenhum vídeo gerado ainda.</div>';
                    return;
                }
                let html = '';
                keys.reverse().forEach(id => {
                    const t = tarefas[id];
                    const isPronto = t.status === "CONCLUÍDO";
                    const isErro = t.status.startsWith("Erro");
                    const badgeClass = isPronto ? "bg-success" : (isErro ? "bg-danger" : "bg-warning text-dark");
                    let icon = "📱 SHORT";
                    if (t.tipo === "doc") icon = "🎬 DOC";
                    if (t.tipo === "afiliado_moda") icon = "🛍️ MODA";
                    
                    html += `
                        <div class="list-group-item bg-dark border-secondary text-light p-3 mb-2 rounded d-flex justify-content-between align-items-center flex-wrap gap-2">
                            <div>
                                <span class="badge bg-secondary me-2">${icon}</span>
                                <strong class="fs-6">${t.titulo}</strong><br>
                                <span class="badge ${badgeClass} mt-1">${t.status}</span>
                            </div>
                            <div class="d-flex gap-2">
                                ${isPronto ? `<a href="/api/download/${id}" class="btn btn-success btn-sm fw-bold px-3">📥 MP4</a>` : ''}
                                ${isPronto ? `<a href="/api/download_txt/${id}" class="btn btn-outline-warning btn-sm fw-bold px-2">📄 TXT</a>` : ''}
                            </div>
                        </div>
                    `;
                });
                listaTarefas.innerHTML = html;
            } catch (e) {
                console.error(e);
            }
        }

        setInterval(carregarTarefas, 3000);
        carregarTarefas();

        function copiarTexto(elementId) {
            const el = document.getElementById(elementId);
            el.select();
            document.execCommand('copy');
            alert('Copiado para a área de transferência! Pronto para colar no YouTube/TikTok!');
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const titulo = document.getElementById('tituloInput').value;
            const tipo = document.querySelector('input[name="tipoVideo"]:checked').value;
            const promo = document.getElementById('promoInput') ? document.getElementById('promoInput').value : '';
            const fotosInput = document.getElementById('fotosInput');
            const postKitBox = document.getElementById('postKitBox');

            btnSubmit.disabled = true;
            progressCard.classList.remove('d-none');
            downloadBox.classList.add('d-none');
            postKitBox.classList.add('d-none');
            roteiroBox.classList.add('d-none');
            spinner.classList.remove('d-none');
            statusText.innerText = "Criando tarefa no servidor...";

            const formData = new FormData();
            formData.append('titulo', titulo);
            formData.append('tipo', tipo);
            formData.append('promo', promo);
            if (fotosInput.files) {
                for (let i = 0; i < fotosInput.files.length; i++) {
                    formData.append('fotos', fotosInput.files[i]);
                }
            }

            const res = await fetch('/api/criar', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            const taskId = data.task_id;
            carregarTarefas();

            const interval = setInterval(async () => {
                const check = await fetch(`/api/status/${taskId}`);
                const task = await check.json();
                statusText.innerText = task.status;

                if (task.roteiro) {
                    roteiroBox.innerText = "Roteiro: " + task.roteiro;
                    roteiroBox.classList.remove('d-none');
                }

                if (task.status === "CONCLUÍDO") {
                    clearInterval(interval);
                    spinner.classList.add('d-none');
                    statusText.innerText = "✅ VÍDEO 100% PRONTO EM FULL HD!";
                    btnDownload.href = `/api/download/${taskId}`;
                    const btnDownloadTxt = document.getElementById('btnDownloadTxt');
                    if (btnDownloadTxt) btnDownloadTxt.href = `/api/download_txt/${taskId}`;
                    downloadBox.classList.remove('d-none');

                    if (task.post_titulo) {
                        document.getElementById('kitTitulo').value = task.post_titulo;
                        document.getElementById('kitDescricao').value = task.post_descricao;
                        document.getElementById('kitComentario').value = task.post_comentario;
                        postKitBox.classList.remove('d-none');
                    }

                    btnSubmit.disabled = false;
                    carregarTarefas();
                } else if (task.status.startsWith("Erro")) {
                    clearInterval(interval);
                    spinner.classList.add('d-none');
                    btnSubmit.disabled = false;
                    carregarTarefas();
                }
            }, 3000);
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE

@app.get("/api/tarefas")
def listar_tarefas():
    return TASKS

@app.post("/api/criar")
async def criar_video(
    background_tasks: BackgroundTasks,
    titulo: str = Form(""),
    tipo: str = Form("short"),
    promo: str = Form(""),
    fotos: Optional[List[UploadFile]] = File(None)
):
    task_id = str(uuid.uuid4())
    uploaded_image_paths = []
    
    if fotos:
        upload_dir = f"temp_upload_{task_id[:8]}"
        os.makedirs(upload_dir, exist_ok=True)
        for f in fotos:
            if f.filename:
                dest = os.path.join(upload_dir, f.filename)
                content = await f.read()
                with open(dest, "wb") as buffer:
                    buffer.write(content)
                if os.path.exists(dest) and os.path.getsize(dest) > 1000:
                    uploaded_image_paths.append(dest)
                    
    TASKS[task_id] = {
        "titulo": titulo if titulo else "Produto de Moda",
        "tipo": tipo,
        "status": "Iniciando processo...",
        "roteiro": "",
        "file_path": None,
        "file_name": None,
        "post_titulo": "",
        "post_descricao": "",
        "post_comentario": ""
    }
    background_tasks.add_task(processar_video, task_id, titulo, tipo, uploaded_image_paths, promo)
    return {"task_id": task_id}

@app.get("/api/status/{task_id}")
def status_video(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return TASKS[task_id]

@app.get("/api/download/{task_id}")
def download_video(task_id: str):
    task = TASKS.get(task_id)
    if not task or not task.get("file_path") or not os.path.exists(task["file_path"]):
        raise HTTPException(status_code=404, detail="Arquivo não pronto")
    return FileResponse(task["file_path"], media_type="video/mp4", filename=task["file_name"])

@app.get("/api/download_txt/{task_id}")
def download_txt(task_id: str):
    task = TASKS.get(task_id)
    if not task or not task.get("txt_path") or not os.path.exists(task["txt_path"]):
        raise HTTPException(status_code=404, detail="Arquivo TXT não encontrado")
    return FileResponse(task["txt_path"], media_type="text/plain", filename=task["txt_name"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8505))
    host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    logger.info(f"Iniciando Futebol Invisível Studio em http://{host}:{port} ...")
    uvicorn.run(app, host=host, port=port)
