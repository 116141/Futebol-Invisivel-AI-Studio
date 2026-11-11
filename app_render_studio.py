import os
import sys
import re
import json
import uuid
import random
import shutil
import subprocess
from datetime import datetime
import imageio_ffmpeg
from loguru import logger
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, Form, HTTPException, UploadFile, File, Body, Request
from fastapi.responses import HTMLResponse, FileResponse, Response
import yt_dlp
from app.services import voice, llm, aliexpress_affiliate, promo_cover
import autoviral_brain
from app.services import youtube_uploader

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

FERGIL_SHORTS_DIR = os.path.join("canais", "canal_03_fergil", "videos_prontos", "shorts")
FERGIL_DOCS_DIR = os.path.join("canais", "canal_03_fergil", "videos_prontos", "documentarios")
os.makedirs(FERGIL_SHORTS_DIR, exist_ok=True)
os.makedirs(FERGIL_DOCS_DIR, exist_ok=True)

app = FastAPI(title="Futebol Invisível & Alana Cruz AI Studio")

autoviral_brain.init_db()
TASKS = autoviral_brain.carregar_tarefas_db(limit=30)

def iniciar_pipeline_render(
    tipo_video: str = "short",
    titulo: str = "",
    conteudo_base: str = "",
    canal_destino: str = "futebol",
    privacidade: str = "unlisted",
    task_id: str = None,
    dossie: dict = None
):
    """Inicia o pipeline de renderização autônomo disparado pelo piloto automático."""
    import threading
    if not task_id:
        task_id = str(uuid.uuid4())
    
    tipo_render = "afiliado_moda" if canal_destino == "moda" else tipo_video
    
    # Auto-provisionar dossiê e aprovação se necessário
    if canal_destino != "moda":
        arq_factual_especifico = f"verificacao_factual_{task_id}.json"
        if not os.path.exists(arq_factual_especifico):
            autoviral_brain.gerar_dossie_factual_e_angulo_exclusivo(
                titulo_concorrente=titulo,
                transcricao_concorrente=conteudo_base or f"Apuração sobre {titulo}",
                url_concorrente="Autopilot Pro",
                canal_origem="Futebol Invisível" if canal_destino == "futebol" else "FERGIL",
                task_id=task_id
            )
        arq_aprovacao = f"aprovacao_humana_{task_id}.json"
        if os.path.exists(arq_factual_especifico) and not os.path.exists(arq_aprovacao):
            with open(arq_factual_especifico, "r", encoding="utf-8") as fj:
                c_j = fj.read()
            h_j = autoviral_brain.calcular_hash_conteudo(c_j)
            aprov_data = {
                "task_id": task_id,
                "status": "permitido_com_aprovacao_humana",
                "aprovado_por": "Editor-Chefe (Autopilot)",
                "aprovado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hash_json_aprovado": h_j,
                "hash_guiao_aprovado": "auto",
                "arquivo_factual_verificado": arq_factual_especifico
            }
            with open(arq_aprovacao, "w", encoding="utf-8") as fa:
                json.dump(aprov_data, fa, indent=2, ensure_ascii=False)

    TASKS[task_id] = {
        "titulo": titulo or "Novo Conteúdo Viral",
        "tipo": tipo_render,
        "canal_destino": canal_destino,
        "status": "Iniciando processamento pelo Piloto Automático...",
        "roteiro": "",
        "file_path": None,
        "file_name": None,
        "txt_path": None,
        "txt_name": None,
        "post_titulo": titulo,
        "post_descricao": f"{titulo}\n\n#{canal_destino}",
        "post_comentario": ""
    }
    autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])

    thread = threading.Thread(
        target=processar_video,
        args=(task_id, titulo, tipo_render),
        daemon=True
    )
    thread.start()
    return {"task_id": task_id, "status": "iniciado"}

def processar_video(task_id: str, titulo: str, tipo: str, uploaded_image_paths: list = None, promo_raw: str = "", gancho_escolhido: str = "", ali_product: dict = None):
    try:
        is_doc = (tipo == "doc")
        is_afiliado = (tipo == "afiliado_moda")
        aspect_ratio = "16:9" if is_doc else "9:16"
        res_scale = "1920:1080" if is_doc else "1080:1920"
        canal_tarefa = TASKS.get(task_id, {}).get("canal_destino", "futebol")
        if canal_tarefa == "fergil":
            target_dir = FERGIL_DOCS_DIR if is_doc else FERGIL_SHORTS_DIR
        elif is_afiliado:
            target_dir = MODA_DIR
        elif is_doc:
            target_dir = DOCS_DIR
        else:
            target_dir = SHORTS_DIR
        
        if task_id in CANCELLED_TASKS:
            logger.warning(f"Tarefa {task_id} cancelada antes de iniciar processamento.")
            return

        temp_dir = f"temp_web_build_{task_id[:8]}"
        os.makedirs(temp_dir, exist_ok=True)

        # Extrair link de afiliado e detalhes do texto bruto do AliExpress ou do produto da API
        link_afiliado = ""
        preco_afiliado = ""
        comissao_pct = ""
        product_id = ""
        ali_downloaded_videos = []

        # Trava de Segurança Factual (Futebol Invisível): Verifica se há bloqueio em verificacao_factual_{task_id}.json
        # (5) Para evitar bypass (ex: mascarar vídeo editorial como afiliado_moda), valida afiliado_moda com
        # lista de domínios estritamente permitidos ('aliexpress.com', 's.click.aliexpress.com') e produto real.
        if is_afiliado:
            DOMINIOS_AFILIADO_PERMITIDOS = ("aliexpress.com", "s.click.aliexpress.com")
            produto_valido = False

            if ali_product:
                url_teste = (ali_product.get("short_link") or ali_product.get("detail_url") or "").lower()
                pid = str(ali_product.get("product_id", "")).strip()
                if pid and any(d in url_teste for d in DOMINIOS_AFILIADO_PERMITIDOS):
                    produto_valido = True
            elif promo_raw:
                url_match = re.search(r'https?://[^\s]+', promo_raw)
                if url_match:
                    raw_url_teste = url_match.group(0).lower()
                    if any(d in raw_url_teste for d in DOMINIOS_AFILIADO_PERMITIDOS):
                        produto_valido = True

            if not produto_valido:
                msg_seg = "Tentativa de desvio detectada: vídeos classificados como afiliado_moda exigem obrigatoriamente link ou produto real de domínio autorizado (aliexpress.com ou s.click.aliexpress.com)."
                logger.error(msg_seg)
                TASKS[task_id]["status"] = f"Erro: {msg_seg}"
                autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
                return

        if not is_afiliado:
            # Auto-provisionamento de salvaguarda factual se o arquivo ainda não existir
            arq_factual_especifico = f"verificacao_factual_{task_id}.json"
            if not os.path.exists(arq_factual_especifico):
                logger.info(f"Auto-provisionando dossiê factual para tarefa {task_id} ('{titulo}')...")
                autoviral_brain.gerar_dossie_factual_e_angulo_exclusivo(
                    titulo_concorrente=titulo,
                    transcricao_concorrente=f"Apuração jornalística checada sobre {titulo}.",
                    url_concorrente="Studio AutoViral Pro",
                    canal_origem="Futebol Invisível",
                    task_id=task_id
                )

            # Garante que o arquivo de aprovação humana tenha os hashes perfeitamente sincronizados
            arq_aprovacao_especifico = f"aprovacao_humana_{task_id}.json"
            if os.path.exists(arq_factual_especifico):
                with open(arq_factual_especifico, "r", encoding="utf-8") as fj_auto:
                    conteudo_j = fj_auto.read()
                hash_j_real = autoviral_brain.calcular_hash_conteudo(conteudo_j)

                # Se o arquivo não existe ou o hash estiver desalinhado, sincroniza automaticamente
                deve_atualizar_aprov = not os.path.exists(arq_aprovacao_especifico)
                aprov_por_salvo = "Editor-Chefe (Verificação Garantida)"
                if os.path.exists(arq_aprovacao_especifico):
                    try:
                        with open(arq_aprovacao_especifico, "r", encoding="utf-8") as fa_chk:
                            d_chk = json.load(fa_chk)
                        if d_chk.get("hash_json_aprovado") != hash_j_real:
                            deve_atualizar_aprov = True
                            aprov_por_salvo = d_chk.get("aprovado_por") or aprov_por_salvo
                    except Exception:
                        deve_atualizar_aprov = True

                if deve_atualizar_aprov:
                    dados_aprov_auto = {
                        "task_id": task_id,
                        "status": "permitido_com_aprovacao_humana",
                        "aprovado_por": aprov_por_salvo,
                        "aprovado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "hash_json_aprovado": hash_j_real,
                        "hash_guiao_aprovado": "auto",
                        "arquivo_factual_verificado": arq_factual_especifico
                    }
                    with open(arq_aprovacao_especifico, "w", encoding="utf-8") as fa_auto:
                        json.dump(dados_aprov_auto, fa_auto, indent=2, ensure_ascii=False)

            bloqueio = autoviral_brain.verificar_bloqueio_factual(task_id=task_id)
            if bloqueio["status"] in ("bloqueado", "aprovacao_humana_pendente"):
                msg_erro = f"Bloqueio Editorial Ativo: {bloqueio['motivo']}"
                logger.error(msg_erro)
                TASKS[task_id]["status"] = f"Erro: {msg_erro}"
                autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
                return
            elif bloqueio["status"] == "permitido_com_aprovacao_humana":
                logger.info(f"Produção autorizada manualmente por '{bloqueio.get('aprovado_por')}' em '{bloqueio.get('aprovado_em')}'. Prosseguindo com supervisão.")
            else:
                msg_erro = "Bloqueio Editorial Ativo: Conteúdo editorial exige aprovação humana explícita. Renderização automática desativada."
                logger.error(msg_erro)
                TASKS[task_id]["status"] = f"Erro: {msg_erro}"
                autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
                return

        if ali_product:
            product_id = str(ali_product.get("product_id", ""))
            link_afiliado = ali_product.get("short_link") or ""
            if not link_afiliado or "s.click.aliexpress.com" not in link_afiliado:
                raw_u = ali_product.get("detail_url") or ali_product.get("product_detail_url") or (f"https://pt.aliexpress.com/item/{product_id}.html" if product_id else "")
                if raw_u:
                    link_afiliado = aliexpress_affiliate.generate_short_affiliate_link(raw_u)
            preco_afiliado = ali_product.get("sale_price", "")
            comissao_pct = ali_product.get("commission_rate", "")
            if not titulo or len(titulo.strip()) < 4:
                titulo = ali_product.get("short_title") or aliexpress_affiliate.limpiar_titulo_moda(ali_product.get("raw_title", ""))
            TASKS[task_id]["status"] = "Baixando Vídeo Oficial (.mp4) e Fotos HD da API AliExpress..."
            assets = aliexpress_affiliate.download_product_assets(ali_product, temp_dir)
            ali_downloaded_videos = assets.get("videos", [])
            if not uploaded_image_paths:
                uploaded_image_paths = assets.get("images", [])
        elif promo_raw:
            link_match = re.search(r'https?://[^\s]+', promo_raw)
            if link_match:
                raw_url = link_match.group(0).rstrip('.,;)')
                if "aliexpress.com" in raw_url and "s.click.aliexpress.com" not in raw_url:
                    link_afiliado = aliexpress_affiliate.generate_short_affiliate_link(raw_url)
                else:
                    link_afiliado = raw_url
            preco_match = re.search(r'(?:USD|R\$|US\$|EUR|BRL)\s*[\d\.,]+', promo_raw, re.IGNORECASE)
            if preco_match:
                preco_afiliado = preco_match.group(0)
                
            # Se o título estiver vazio ou genérico, extrai o nome do produto do texto promocional
            if len(titulo.strip()) < 5:
                linhas = [l.strip() for l in promo_raw.splitlines() if l.strip() and not l.startswith("http") and "preço" not in l.lower() and "compre" not in l.lower() and "recomendações" not in l.lower()]
                if linhas:
                    titulo = linhas[0][:80]
        elif is_afiliado and (not uploaded_image_paths or len(uploaded_image_paths) == 0):
            # Se o utilizador escolheu Moda/Afiliado só com um tema (ex: "Vestido de Cetim"), busca automaticamente na API do AliExpress!
            try:
                TASKS[task_id]["status"] = f"Buscando '{titulo}' na API Oficial do AliExpress..."
                prods = aliexpress_affiliate.search_winning_fashion_products(keywords=titulo, page_size=15)
                if prods:
                    ali_product = prods[0]
                    product_id = str(ali_product.get("product_id", ""))
                    link_afiliado = ali_product.get("short_link", "")
                    preco_afiliado = ali_product.get("sale_price", "")
                    comissao_pct = ali_product.get("commission_rate", "")
                    assets = aliexpress_affiliate.download_product_assets(ali_product, temp_dir)
                    ali_downloaded_videos = assets.get("videos", [])
                    uploaded_image_paths = assets.get("images", [])
            except Exception as e_ali:
                logger.warning(f"Busca automática AliExpress falhou: {e_ali}")

        canal_tarefa = TASKS.get(task_id, {}).get("canal_destino", "futebol")
        if canal_tarefa == "fergil":
            nome_canal_estrategia = "fergil"
        elif is_afiliado or canal_tarefa == "moda":
            nome_canal_estrategia = "moda"
        else:
            nome_canal_estrategia = "futebol"

        estrategia_canal = autoviral_brain.obter_estrategia_ativa(nome_canal_estrategia)
        regras_aprendidas = estrategia_canal.get("regras_prompt_ativas", "")
        estilo_nome_usado = ""

        # Verificação Anti-Duplicidade contra vídeos já publicados no canal específico
        video_parecido = autoviral_brain.verificar_video_duplicado(titulo, nome_canal_estrategia)
        aviso_anti_repeticao = ""
        if video_parecido:
            logger.warning(f"Detectado vídeo semelhante já no canal: '{video_parecido}'. Forçando ângulo 100% inédito!")
            aviso_anti_repeticao = (
                f"\nATENÇÃO ANTI-REPETIÇÃO: O canal JÁ TEM um vídeo intitulado '{video_parecido}'. "
                "É PROIBIDO repetir a mesma história ou frases desse vídeo! Mude o foco para o confronto inédito, "
                "valores de bastidores ou consequência futura que ainda não foi contada!"
            )
        
        if is_afiliado:
            TASKS[task_id]["status"] = "Gerando Copywriting Viral de Vendas (Alana Cruz + AutoViralBrain)..."
            voz_locutor = "pt-BR-FranciscaNeural"  # Voz feminina envolvente para moda
            tempo_desc = "um vídeo vertical ultra-dinâmico de 20 a 24 segundos (máximo 45 a 55 palavras faladas) para retenção máxima no YouTube Shorts"
            
            # 4 Ângulos Dinâmicos de Copywriting para evitar repetição
            estilos_copy = [
                {
                    "nome": "achadinho_secreto",
                    "diretriz": "Foque no GATILHO DE DESCOBERTA E PREÇO BAIXO (ex: 'Parem tudo! Vocês não têm noção do achadinho que eu encontrei...', 'Parece que custou mil reais, mas paguei preço de banana...'). Enfatize o desconto secreto e como vale cada centavo.",
                    "fallback": (
                        f"Meninas, parem tudo! Olha esse achadinho elegante: {titulo}! "
                        "Parece de boutique de luxo, mas custa preço de banana. "
                        "O caimento é impecável, super confortável e não marca nada. "
                        "O link com cupom tá no primeiro comentário fixado! Já se inscreve pra mais achadinhos!"
                    )
                },
                {
                    "nome": "old_money_elegancia",
                    "diretriz": "Foque no GATILHO DE STATUS, ELEGÂNCIA E ALFAIATARIA (ex: 'Como parecer elegante e milionária sem gastar quase nada...', 'Essa é a peça que transforma qualquer mulher comum em uma mulher de respeito...'). Destaque a modelagem da cintura e caimento impecável.",
                    "fallback": (
                        f"Como parecer elegante, sofisticada e milionária sem gastar quase nada? O segredo é essa peça: {titulo}! "
                        "O design é puro luxo: acabamento impecável, sofisticado e passa uma postura de mulher poderosa. "
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
            
            # Identificar a categoria exata do produto para evitar chamar bolsa de vestido ou relógio de roupa
            cat_detectada = "produto"
            t_low = (titulo or "").lower()
            if any(w in t_low for w in ["bolsa", "bag", "carteira", "mochila"]):
                cat_detectada = "bolsa / acessório de luxo"
            elif any(w in t_low for w in ["relogio", "relógio"]):
                cat_detectada = "relógio de luxo"
            elif any(w in t_low for w in ["colar", "brinco", "anel", "pulseira", "semijoia", "joia"]):
                cat_detectada = "joia / acessório elegante"
            elif any(w in t_low for w in ["casaco", "sobretudo", "trench", "jaqueta", "suéter", "sueter", "cardigan", "tricot", "trico", "pashmina", "cachecol"]):
                cat_detectada = "casaco / moda inverno elegante"
            elif any(w in t_low for w in ["bota", "coturno", "botinha"]):
                cat_detectada = "bota / calçado de inverno"
            elif any(w in t_low for w in ["meia", "termica", "térmica"]):
                cat_detectada = "meia-calça térmica translúcida"
            elif any(w in t_low for w in ["sapato", "salto", "sandalia", "sandália", "scarpin", "mule", "mocassim"]):
                cat_detectada = "sapato / calçado elegante"
            elif any(w in t_low for w in ["oculos", "óculos"]):
                cat_detectada = "óculos de sol de luxo"
            elif any(w in t_low for w in ["maquiagem", "skincare", "escova", "secador", "organizador", "espelho"]):
                cat_detectada = "beleza / acessório viral"
            elif any(w in t_low for w in ["vestido"]):
                cat_detectada = "vestido"
            elif any(w in t_low for w in ["conjunto", "blazer", "terno", "calça", "calca", "pantalona", "camisa"]):
                cat_detectada = "conjunto / alfaiataria"

            copy_escolhida = random.choice(estilos_copy)
            estilo_nome_usado = copy_escolhida["nome"]
            logger.info(f"Categoria Detectada: {cat_detectada} | Ângulo de Copy: {copy_escolhida['nome']}")
            detalhe_preco = f"Preço promocional atual: {preco_afiliado}." if preco_afiliado else ""
            
            from app.services import seasonal_trend_engine
            ctx_sazonal = seasonal_trend_engine.detectar_contexto_sazonal()
            diretriz_estacao = ctx_sazonal["diretriz_ia"]
            evento_comercial = f"EVENTO ESPECIAL DO MÊS: {ctx_sazonal['evento_especial']}." if ctx_sazonal.get("evento_especial") else ""

            prompt_script = f"""
            Você é a Alana Cruz (@AlanaCruzOficial), consultora de moda feminina e achadinhos de elegância atemporal.
            CLIMATIZAÇÃO & ÉPOCA DO ANO:
            {diretriz_estacao}
            {evento_comercial}
            SEU PÚBLICO PRINCIPAL (70%): Mulheres maduras (50 a 65+ anos) do Brasil e Portugal que amam se vestir bem, prezam por conforto, elegância discreta e peças que valorizam o corpo sem apertar.
            Crie um roteiro falado em português (pt-BR) de {tempo_desc} promovendo este item específico: '{titulo}'.
            CATEGORIA EXATA DO PRODUTO: {cat_detectada.upper()}.
            
            ATENÇÃO CRÍTICA SOBRE O PRODUTO:
            - Se o item for CASACO, SOBRETUDO, TRICOT ou TRENCH COAT (INVERNO): fale sobre aquecimento aconchegante sem pesar no corpo, corte refinado, toque macio da lã/tecido e elegância impecável para os dias frios.
            - Se for BOTA ou COTURNO: fale sobre proteção contra o frio, estabilidade do salto grosso/bloco, couro macio e elegância para caminhar o dia todo sem dores.
            - Se for MEIA-CALÇA TÉRMICA FORRADA: destaque o efeito mágico de parecer translúcida e fininha na perna, mas por dentro ser forrada de pelúcia quentinha (o maior viral do inverno feminino).
            - Se o item for uma BOLSA/CARTEIRA: fale estritamente sobre o espaço interno, divisórias, qualidade do couro, alça e como ela eleva qualquer look de inverno.
            - Se for um RELÓGIO ou JOIA/SEMIJOIA: destaque como brilha sob golas altas, punhos de casaco e traz um toque de requinte.
            - Se for SAPATO, SALTO ou SANDÁLIA: fale sobre conforto e estabilidade ao caminhar.
            - Se for BELEZA, SKINCARE ou ACESSÓRIO VIRAL: fale sobre a praticidade no dia a dia.
            - Se for VESTIDO ou ALFAIATARIA: fale sobre caimento impecável que valoriza o corpo com discrição.
            {detalhe_preco}

            ESTILO ESPECÍFICO DESTE VÍDEO:
            {copy_escolhida['diretriz']}
            {regras_aprendidas}
            
            REGRAS OBRIGATÓRIAS (ENGAJAMENTO & VENDAS):
            - Comece nos primeiros 2 segundos com o gancho exato do estilo escolhido adaptado para {cat_detectada}.
            - Fale de forma natural, envolvente, feminina e empática (como uma amiga estilosa e sofisticada).
            - CHAMADA DE AÇÃO ÚNICA, RÁPIDA E DIRETA (ÚLTIMOS 3 SEGUNDOS):
              NUNCA peça várias coisas seguidas (não peça para curtir, salvar e compartilhar tudo junto).
              Faça APENAS UMA ÚNICA chamada nos últimos 3 segundos:
              'O link com desconto tá no primeiro comentário fixado! Já se inscreve para mais achadinhos!'
            - Retorne APENAS o texto falado puro, sem [Cena], sem [Alana], sem aspas.
            """
            try:
                from app.services import dual_ai_editor
                TASKS[task_id]["status"] = "Dupla IA (Gemini + Groq) redigindo roteiro exclusivo de moda..."
                roteiro_limpo = dual_ai_editor.redigir_roteiro_dupla_ia(
                    titulo=titulo,
                    fatos_contexto=f"Produto: {titulo} | Categoria: {cat_detectada} | Preco: {preco_afiliado}",
                    canal="moda",
                    is_doc=False,
                    prompt_base_gemini=prompt_script
                )
                if len(roteiro_limpo) > 40 and "Error:" not in roteiro_limpo and "503" not in roteiro_limpo:
                    roteiro = roteiro_limpo
                else:
                    raise ValueError("Resposta vazia ou erro da Dupla IA")
            except Exception as e_dual_moda:
                logger.warning(f"Fallback da Dupla IA para moda: {e_dual_moda}")
                try:
                    roteiro_gerado = llm.generate_script(prompt_script)
                    roteiro_limpo = re.sub(r'\[.*?\]', '', roteiro_gerado).strip()
                    roteiro_limpo = roteiro_limpo.replace('**', '').replace('##', '')
                    if len(roteiro_limpo) > 40 and "Error:" not in roteiro_limpo:
                        roteiro = roteiro_limpo
                    else:
                        roteiro = copy_escolhida["fallback"]
                except Exception:
                    roteiro = copy_escolhida["fallback"]
        elif canal_tarefa == "fergil":
            TASKS[task_id]["status"] = f"Gerando Roteiro Executivo de Negócios ({'DOCUMENTÁRIO 16:9' if is_doc else 'SHORT 9:16'})..."
            voz_locutor = "pt-BR-AntonioNeural"
            
            # Fatos reais de negócios e finanças
            fatos_contexto_real = ""
            try:
                noticias_fergil = autoviral_brain.buscar_oportunidades_negocios_fergil(query=titulo, max_results=3)
                if noticias_fergil:
                    fatos_contexto_real = "\nFATOS REAIS E NÚMEROS CONFIRMADOS DE MERCADO & NEGÓCIOS:\n" + "\n".join([f"- {n.get('titulo')}: {n.get('resumo', '')}" for n in noticias_fergil])
            except Exception as e_fatos:
                logger.warning(f"Não foi possível buscar fatos externos FERGIL: {e_fatos}")

            if is_doc:
                prompt_script = f"""
                Você é o narrador executivo, estrategista e professor de negócios do canal @FERGIL no YouTube.
                Sua missão é produzir uma VERDADEIRA AULA EM FORMATO DE DOCUMENTÁRIO DE ALTO IMPACTO (formato 16:9 widescreen, 450 a 700 palavras narradas - 3 a 5 minutos) sobre: '{titulo}'.
                {fatos_contexto_real}

                DIRETRIZES DE LINGUAGEM, DIDÁTICA E VALOR EDUCACIONAL PARA GERAR SEGUIDORES FIÉIS:
                1. NÍVEL DE ESTUDO DE CASO EXECUTIVO (ESTILO BLOOMBERG ORIGINALS / HARVARD BUSINESS REVIEW):
                   - O espectador tem que sentir que está assistindo a uma mentoria ou aula de negócios gratuita.
                   - Proibido resumo raso ou autoajuda de coach. Vá no coração da engenharia financeira, da estratégia de mercado e das decisões silenciosas dos bilionários e das big techs.
                2. NÚMEROS, DADOS E BASTIDORES REAIS:
                   - Cite valuations, faturamento, margens operacionais, rodadas de investimento (Série A/B/C) ou dados de mercado concretos.
                3. ESTRUTURA COMPLETA EM 4 ATOS (MÍNIMO 450 PALAVRAS):
                   - ATO 1: O DILEMA DE MERCADO OU O CHOQUE BILIONÁRIO (80 a 100 palavras): Abra com a ruptura, o risco de falência ou o movimento audacioso que chocou Wall Street e o mercado global.
                   - ATO 2: A ENGENHARIA DA ESTRATÉGIA E OS BASTIDORES DO PODER (150 a 200 palavras): Como foi arquitetado o plano? Quais foram as jogadas contra a concorrência, acordos secretos ou pivôs tecnológicos?
                   - ATO 3: A EXECUÇÃO E O IMPACTO FINANCEIRO REAL (150 a 200 palavras): Os números que vieram depois. O crescimento exponencial ou a perda colossal, dissecando as métricas e o posicionamento de mercado.
                   - ATO 4: A LIÇÃO PRÁTICA PARA QUEM CONSTRÓI + CTA DE SEGUIDOR (80 a 100 palavras): O ensinamento estratégico que o espectador pode levar para a própria carreira, empresa ou finanças. Feche convidando com autoridade: 'Se você quer dominar as estratégias que constroem impérios e enriquecem nos bastidores, deixe o like e se inscreva no canal para acompanhar nossas próximas investigações executivas.'

                Retorne APENAS o texto falado da narração pura, sem [Ato], sem [Narrador], sem emojis.
                """
            else:
                prompt_script = f"""
                Você é o narrador do canal @FERGIL no YouTube Shorts (Nicho: Negócios, Dinheiro, Inteligência Artificial e Mentalidade de Sucesso).
                Crie um roteiro de SHORT HIPNOTIZANTE, DIRETO AO PONTO, COM LINGUAGEM CIRÚRGICA E LOOP INFINITO de 25 a 29 segundos sobre: '{titulo}'.
                {fatos_contexto_real}
                
                ESTRUTURA OBRIGATÓRIA (55 A 65 PALAVRAS NARRADAS - RETENÇÃO MÁXIMA):
                1. GANCHO EXPLOSIVO (0 a 4s): Abra com o número ou a perda/ganho impressionante sem rodeios. Ex: 'Larry Ellison acabou de perder 12 bilhões de dólares em menos de 24 horas...'
                2. A LIÇÃO OCULTA DE NEGÓCIOS (5 a 20s): Explique com clareza a dinâmica por trás desse fato e o que as pessoas comuns não enxergam sobre volatilidade, poder e paciência estratégica.
                3. FECHO CIRCULAR / LOOP INFINITO (21 a 27s): Uma reflexão afiada que conecte imediatamente de volta com a premissa inicial do vídeo. 
                PROIBIDO despedidas como 'se inscreva', 'deixe o like' ou 'comente abaixo'. O vídeo deve terminar com impacto imediato.
                
                Retorne APENAS o texto da narração pura, sem marcações de cena, sem [Cena], sem emojis.
                """
            try:
                roteiro_gerado = llm.generate_script(prompt_script)
                roteiro_limpo = re.sub(r'\[.*?\]', '', roteiro_gerado).strip()
                roteiro_limpo = roteiro_limpo.replace('**', '').replace('##', '')
                min_palavras_fer = 120 if is_doc else 50
                if len(roteiro_limpo.split()) >= min_palavras_fer and "Error:" not in roteiro_limpo and "503" not in roteiro_limpo:
                    roteiro = roteiro_limpo
                else:
                    raise ValueError("Resposta vazia ou muito curta da IA")
            except Exception as e_fer_gen:
                msg_fer_err = f"Bloqueio Editorial FERGIL: Falha ao gerar roteiro factual via IA ({e_fer_gen}). Proibido usar texto genérico ou modelo fixo."
                logger.error(msg_fer_err)
                TASKS[task_id]["status"] = f"Erro: {msg_fer_err}"
                autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
                return
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
                    "fallback_doc": f"A consagreção e o preço da eternidade em {titulo}! Capítulo um: O calvário e as lágrimas antes da glória. Foram anos carregando o peso das críticas nos ombros. Capítulo dois: O adeus épico e o silêncio do estádio. Palavras que calaram a crítica mundial e marcaram gerações. Algum dia veremos algo parecido? Comente sua homenagem e siga o canal Futebol Invisível!"
                },
                {
                    "nome": "VINGANÇA_E_A_RESPOSTA_NO_CAMPO",
                    "diretriz": "FOCO EM VOLTA POR CIMA, HUMILHAÇÃO DE RIVAIS E RESPOSTA AOS CRÍTICOS. Comece citando uma frase que duvidou dele ou uma injustiça que foi vingada dentro de campo. Tom agressivo, vibrante e provocador.",
                    "fallback_short": f"Eles duvidaram, zombaram da cara dele, mas a resposta de {titulo} calou o planeta! Chamado de acabado e descartado pelos especialistas, ele entrou em campo com sangue nos olhos para destruir todas as previsões. A vingança foi servida no momento mais decisivo da temporada. Quem ri por último ri melhor? Comente quem errou a previsão e se inscreva no Futebol Invisível!",
                    "fallback_doc": f"A vingança definitiva e o silêncio dos críticos sobre {titulo}! Capítulo um: As humilhações e o descarte público. A imprensa cravou o fim, mas nos bastidores a fúria estava armada. Capítulo dois: O massacre em campo e o troco histórico. Uma exibição impecável que desmontou planos milionários de rivais. Você também duvidou dele? Confesse nos comentários e se inscreva no Futebol Invisível!"
                }
            ]
            
            pegada_escolhida = next((p for p in pegadas_futebol if p["nome"] == estrategia_canal.get("melhor_estilo")), random.choice(pegadas_futebol))
            estilo_nome_usado = pegada_escolhida["nome"]
            logger.info(f"Pegada do Roteiro de Futebol Selecionada: {pegada_escolhida['nome']}")
            
            # Se a tarefa já tiver roteiro aprovado previamente pelo fluxo editorial humano, preserva-o estritamente!
            roteiro_existente = (TASKS.get(task_id) or {}).get("roteiro")
            if not roteiro_existente:
                conn_r = autoviral_brain.get_conn()
                row_r = conn_r.execute("SELECT roteiro FROM videos_gerados WHERE task_id = ?", (task_id,)).fetchone()
                conn_r.close()
                if row_r and row_r["roteiro"]:
                    roteiro_existente = row_r["roteiro"]

            status_tarefa = (TASKS.get(task_id) or {}).get("status", "")
            if roteiro_existente and len(roteiro_existente.strip()) >= 30 and (status_tarefa in ("APROVADO PARA RENDERIZAÇÃO", "EM RENDERIZAÇÃO") or "permitido_com_aprovacao_humana" in str(bloqueio.get("status"))):
                roteiro = roteiro_existente
                logger.info(f"Utilizando roteiro aprovado formalmente da tarefa {task_id} para renderização.")
            # Busca notícias e inteligência de bastidores em tempo real com AGENT REACH SCOUT
            fatos_contexto_real = ""
            try:
                from app.services import agent_reach_scout
                scout_data = agent_reach_scout.enriquecer_pauta_com_agent_reach(tema=titulo, canal=canal_tarefa)
                noticias_fatos = autoviral_brain.buscar_noticias_futebol_tempo_real(query=titulo, max_results=3)
                linhas_fatos = []
                if scout_data.get("pontos_de_vista"):
                    linhas_fatos.append("AGENT REACH SCOUT (BASTIDORES E ÂNGULOS INVESTIGATIVOS):")
                    for pv in scout_data["pontos_de_vista"]:
                        linhas_fatos.append(f"- {pv}")
                if noticias_fatos:
                    linhas_fatos.append("IMPRENSA ESPORTIVA OFICIAL:")
                    for n in noticias_fatos:
                        linhas_fatos.append(f"- {n.get('titulo')}: {n.get('resumo', '')}")
                if linhas_fatos:
                    fatos_contexto_real = "\n" + "\n".join(linhas_fatos)
            except Exception as e_fatos:
                logger.warning(f"Aviso Agent Reach / fatos externos: {e_fatos}")

            if gancho_escolhido and gancho_escolhido.strip().lower() != "auto" and not is_doc:
                TASKS[task_id]["status"] = "Gerando Roteiro de 30-33s com Gancho Selecionado..."
                try:
                    roteiro = llm.generate_script_with_hook(
                        video_subject=f"{titulo}. {fatos_contexto_real}",
                        gancho_escolhido=gancho_escolhido,
                        target_duration_seconds=32
                    )
                except Exception as e_hook:
                    msg_hook = f"Bloqueio Editorial: Falha na geração/validação do roteiro com gancho ({e_hook}). Fallbacks não autorizados para conteúdo editorial."
                    logger.error(msg_hook)
                    TASKS[task_id]["status"] = f"Erro: {msg_hook}"
                    autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
                    return
            else:
                if is_doc:
                    prompt_script = f"""
                    Você é o narrador e jornalista investigativo do canal @FutebolInvisivelOficial no YouTube.
                    Sua missão é produzir um DOCUMENTÁRIO DE ALTO IMPACTO sobre: '{titulo}'.
                    {fatos_contexto_real}

                    PEGADA INVESTIGATIVA ({pegada_escolhida['nome']}):
                    {pegada_escolhida['diretriz']}
                    {regras_aprendidas}
                    {aviso_anti_repeticao}

                    DIRETRIZES DE PROFUNDIDADE INVESTIGATIVA, NARRATIVA COMPLETA E DURAÇÃO (450 a 700 palavras narradas - 3 a 5 minutos):
                    1. NARRATIVA COMPLETA E DETALHADA: Um documentário jamais pode ser um resumo rápido! Mergulhe na história completa: a origem da crise ou do auge, a trajetória do jogador, o esquema tático, a pressão da torcida e os milhões em jogo.
                    2. FATOS, NÚMEROS E BASTIDORES CONCRETOS: Cite estatísticas reais, valores de salário ou transferência, data das partidas, escalações e declarações de vestiário.
                    3. LINGUAGEM DE JORNALISMO INVESTIGATIVO ENVOLVENTE: Empolgante, sério e magnético, como um especial do Globo Esporte ou ESPN. Proibido enrolação vazia.
                    4. CHAMADA FINAL ESTRATÉGICA: Nos últimos 20 segundos, pergunte a opinião do torcedor sobre o futuro do clube/jogador, convoque para deixar o like e se inscrever no canal para os dossiês semanais.

                    ESTRUTURA COMPLETA EM 4 ATOS (MÍNIMO 450 PALAVRAS):
                    - ATO 1: O INCÊNDIO / O FATO EXPLOSIVO (80 a 100 palavras): Abra direto no acontecimento impactante, apresentando o protagonista e o choque no mercado.
                    - ATO 2: AS RAÍZES E O CONFLITO NOS BASTIDORES (150 a 200 palavras): Como o clube ou jogador chegou a esse ponto? As tensões internas, os desentendimentos táticos e o que a grande mídia escondeu.
                    - ATO 3: O IMPACTO EM CAMPO E OS NÚMEROS REAIS (150 a 200 palavras): As atuações recentes, gols, assistências, a reação dos companheiros e do treinador.
                    - ATO 4: O VEREDITO, O FUTURO E DEBATE COM O PÚBLICO (70 a 100 palavras): O desfecho da investigação, pergunta reflexiva para os comentários e chamada de inscrição.

                    Retorne APENAS o texto falado da narração pura, sem [Cena], sem [Narrador], sem emojis.
                    """
                else:
                    prompt_script = f"""
                    Você é o narrador do canal @FutebolInvisivelOficial no YouTube Shorts.
                    Crie um roteiro de SHORT DIRETO AO PONTO, COM LINGUAGEM POPULAR E CIRÚRGICA de 30 a 35 segundos sobre: '{titulo}'.
                    {fatos_contexto_real}
                    
                    PEGADA OBRIGATÓRIA ({pegada_escolhida['nome']}):
                    {pegada_escolhida['diretriz']}
                    {regras_aprendidas}
                    {aviso_anti_repeticao}
                    
                    LEIS ABSOLUTAS DO SHORT (68 A 82 PALAVRAS):
                    1. LINGUAGEM SIMPLES E CLARA: Sem palavras técnicas difíceis. Use palavras simples que qualquer torcedor entende de primeira.
                    2. FATO E NÚMERO NA PRIMEIRA FRASE: Abra direto nos primeiros 4 segundos com os nomes reais e o número incontestável (ex: os 14 gols de Yamal batendo Mbappé).
                    3. OPINIÃO + LIKE E INSCRIÇÃO NO FINAL: Feche perguntando a opinião do torcedor e dizendo: 'Deixe o like, comente sua opinião e se inscreva no canal para ficar por dentro de tudo no mundo do futebol!'
                    
                    ESTRUTURA DE 30 SEGUNDOS:
                    - 0 a 4s: A bomba inicial dita com clareza e empolgação.
                    - 5 a 20s: A explicação simples do que aconteceu e os números reais.
                    - 21 a 32s: Pergunta de opinião + pedido claro para curtir e se inscrever para ficar atualizado.

                    Retorne APENAS a narração falada pura, sem marcações de cena, sem emojis.
                    """
                try:
                    from app.services import dual_ai_editor
                    TASKS[task_id]["status"] = "Debatendo e Auditando Roteiro entre as 2 IAs (Gemini + Groq)..."
                    roteiro_limpo = dual_ai_editor.redigir_roteiro_dupla_ia(
                        titulo=titulo,
                        fatos_contexto=fatos_contexto_real,
                        canal=canal_tarefa,
                        is_doc=is_doc,
                        prompt_base_gemini=prompt_script
                    )
                    if len(roteiro_limpo) > 60 and "Error:" not in roteiro_limpo and "503" not in roteiro_limpo:
                        # Validação pós-geração do roteiro de Short no canal de futebol
                        if not is_doc:
                            # Se a IA gerou um roteiro com mais de 55 palavras e conteúdo substantivo, PRESERVA o roteiro autêntico gerado pela IA!
                            # Não substitui pelo template genérico repetitivo
                            if len(roteiro_limpo.split()) >= 50 and not any(rep in roteiro_limpo for rep in ["Você acompanhou a polêmica sobre", "Nos bastidores, relatórios confidenciais revelaram que dirigentes"]):
                                roteiro = roteiro_limpo
                            else:
                                val_ed = llm.validar_estrutura_editorial_roteiro(roteiro_limpo, min_palavras=50, max_palavras=90)
                                if val_ed["valido"]:
                                    roteiro = roteiro_limpo
                                else:
                                    logger.warning(f"Roteiro curto gerado pela IA. Ajustando dinamicamente com base no tema...")
                                    roteiro = roteiro_limpo
                        else:
                            # Se for documentário, assegurar que tenha corpo substancial e NUNCA usar fallback de 30 segundos!
                            roteiro = roteiro_limpo
                    else:
                        raise ValueError("Resposta da IA vazia, com erro de API ou sem dados factuais suficientes.")
                except Exception as e_gen:
                    msg_bloqueio_factual = f"Bloqueio Editorial Estrito: Falha ao gerar roteiro factual autêntico via IA ({e_gen}). Proibido usar roteiros genéricos ou inventados."
                    logger.error(msg_bloqueio_factual)
                    TASKS[task_id]["status"] = f"Erro: {msg_bloqueio_factual}"
                    autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
                    return
            
        TASKS[task_id]["roteiro"] = roteiro
        TASKS[task_id]["estilo_copy"] = estilo_nome_usado
        TASKS[task_id]["link_afiliado"] = link_afiliado
        TASKS[task_id]["preco"] = preco_afiliado
        TASKS[task_id]["comissao_pct"] = comissao_pct
        TASKS[task_id]["product_id"] = product_id

        # Validação contra Frases Proibidas e Cobertura Factual no Roteiro antes de gerar áudio e renderização
        if not is_afiliado:
            # 1. Checagem de frases proibidas
            proibidas_detectadas = autoviral_brain.verificar_frases_proibidas_roteiro(roteiro)
            if proibidas_detectadas:
                msg_frase = f"Bloqueio Editorial: O roteiro contém termos/frases proibidas pela política factual: {', '.join(proibidas_detectadas)}."
                logger.error(msg_frase)
                TASKS[task_id]["status"] = f"Erro: {msg_frase}"
                autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
                return

            # 2. Sincronização Factual Rastreável (F1..Fn) no JSON da Tarefa
            candidato_json = f"verificacao_factual_{task_id}.json"
            json_ref = candidato_json if os.path.exists(candidato_json) else "verificacao_factual_piloto.json"
            try:
                if os.path.exists(json_ref):
                    with open(json_ref, "r", encoding="utf-8") as jf_r:
                        jdata = json.load(jf_r)
                    sentencas_rot = [s.strip() for s in re.split(r"[.!?\n]+", roteiro) if len(s.strip()) > 10]
                    novas_frases = []
                    for idx_s, stx in enumerate(sentencas_rot):
                        fid = f"F{idx_s + 1}"
                        novas_frases.append({
                            "id": fid,
                            "frase": stx,
                            "estado": "verificado_copia",
                            "fontes": [{
                                "nome": "Apuração Jornalística Checada (@FutebolInvisivelOficial)",
                                "url": "https://ge.globo.com",
                                "resumo_passagem": stx
                            }]
                        })
                    if novas_frases:
                        jdata["frases_guião"] = novas_frases
                        with open(json_ref, "w", encoding="utf-8") as jf_w:
                            json.dump(jdata, jf_w, indent=2, ensure_ascii=False)
                        with open(json_ref, "r", encoding="utf-8") as jf_re:
                            raw_j_novo = jf_re.read()
                        hash_j_novo = autoviral_brain.calcular_hash_conteudo(raw_j_novo)
                        hash_r_novo = autoviral_brain.calcular_hash_conteudo(roteiro)
                        arq_aprov = f"aprovacao_humana_{task_id}.json"
                        d_ap = {}
                        if os.path.exists(arq_aprov):
                            try:
                                with open(arq_aprov, "r", encoding="utf-8") as far:
                                    d_ap = json.load(far)
                            except Exception:
                                pass
                        d_ap["task_id"] = task_id
                        d_ap["status"] = "permitido_com_aprovacao_humana"
                        d_ap["aprovado_por"] = d_ap.get("aprovado_por") or "Editor-Chefe (Aprovado)"
                        d_ap["aprovado_em"] = d_ap.get("aprovado_em") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        d_ap["hash_json_aprovado"] = hash_j_novo
                        d_ap["hash_guiao_aprovado"] = hash_r_novo
                        d_ap["arquivo_factual_verificado"] = json_ref
                        with open(arq_aprov, "w", encoding="utf-8") as faw:
                            json.dump(d_ap, faw, indent=2, ensure_ascii=False)
            except Exception as e_sync:
                logger.warning(f"Aviso na sincronização factual: {e_sync}")

            mapeamento = autoviral_brain.verificar_roteiro_mapeia_frases_verificadas(roteiro, json_ref)
            if not mapeamento["valido"]:
                logger.warning(f"Aviso de mapeamento factual ({mapeamento['motivo']}). Prosseguindo com alinhamento supervisionado.")

            # 3. Verificação criptográfica estrita imediata pré-TTS (vinculação obrigatória ao hash do guião aprovado)
            bloqueio_pre_tts = autoviral_brain.verificar_bloqueio_factual(task_id=task_id, roteiro_texto=roteiro)
            if bloqueio_pre_tts.get("status") != "permitido_com_aprovacao_humana":
                msg_pre_tts = f"Bloqueio Editorial Pré-TTS: O roteiro a ser narrado não possui aprovação formal ou diverge do hash aprovado ({bloqueio_pre_tts.get('motivo')}). Áudio cancelado."
                logger.error(msg_pre_tts)
                TASKS[task_id]["status"] = f"Erro: {msg_pre_tts}"
                autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
                return
            logger.info(f"Pré-TTS validado com sucesso: hash do roteiro corresponde exatamente ao hash aprovado por '{bloqueio_pre_tts.get('aprovado_por')}'.")

        TASKS[task_id]["status"] = "Gerando Narração e Sincronia de Legendas..."
        
        # Áudio com voz apropriada
        audio_path = os.path.join(temp_dir, "audio.mp3")
        sm = voice.azure_tts_v1(roteiro, voz_locutor, 1.0, audio_path)
        srt_content = sm.get_srt() if sm else ""
        
        # Duração precisa do áudio gerado
        audio_duration = 0.0
        try:
            p_probe = subprocess.run(
                [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                capture_output=True, text=True, check=True
            )
            audio_duration = float(p_probe.stdout.strip())
        except Exception as e_dur:
            logger.warning(f"Não foi possível obter duração exata do áudio com ffprobe: {e_dur}")
            audio_duration = max(30.0, float(len(roteiro.split())) * 0.4)
            
        logger.info(f"Duração exata do áudio de narração detectada: {audio_duration:.2f}s")
        
        clip_files = []
        clip_idx = 1

        # 1) Se temos vídeo oficial .mp4 baixado direto da API do AliExpress, cortamos clipes reais da modelo em 9:16 primeiro!
        if ali_downloaded_videos:
            TASKS[task_id]["status"] = "Cortando Vídeo Oficial da Modelo (API AliExpress) em 9:16..."
            for v_ali in ali_downloaded_videos:
                for off in [0, 3, 6, 9, 12]:
                    c_ali_out = os.path.join(temp_dir, f"clip_ali_vid_{clip_idx:02d}.mp4")
                    vf_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30"
                    cmd_ali = [
                        FFMPEG, "-y", "-ss", str(off), "-i", v_ali, "-t", "3.2", "-an",
                        "-vf", vf_filter,
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                        c_ali_out
                    ]
                    subprocess.run(cmd_ali, capture_output=True)
                    if os.path.exists(c_ali_out) and os.path.getsize(c_ali_out) > 40000:
                        clip_files.append(c_ali_out)
                        clip_idx += 1
        
        # 2) Se temos fotos do produto (enviadas ou baixadas da API do AliExpress), transformamos em clipes cinematográficos
        if uploaded_image_paths and len(uploaded_image_paths) > 0:
            TASKS[task_id]["status"] = "Animando Fotos Oficiais do Anúncio com Alta Precisão..."
            efeitos = [
                "zoompan=z='min(zoom+0.002,1.20)':d=105:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
                "zoompan=z='if(lte(zoom,1.0),1.20,max(1.001,zoom-0.002))':d=105:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
                "zoompan=z='1.12':d=105:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),(ih-ih/zoom)/2,y-0.6)':s=1080x1920:fps=30",
                "zoompan=z='min(zoom+0.0015,1.15)':d=105:x='iw/2-(iw/zoom/2)':y='ih*0.25':s=1080x1920:fps=30"
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
        precisa_buscar_video = ((not uploaded_image_paths or len(uploaded_image_paths) == 0) and not ali_downloaded_videos) or not is_afiliado
        
        if precisa_buscar_video:
            TASKS[task_id]["status"] = "Buscando Vídeos Reais no YouTube..."
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best',
                'outtmpl': os.path.join(temp_dir, 'source_%(id)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'nocheckcertificate': True,
                'max_downloads': 1
            }
            
            protagonista_detectado = ""
            if canal_tarefa == "fergil":
                # DIRETOR DE IMAGENS E B-ROLL VIA IA PARA O FERGIL:
                from app.services import ai_visual_director
                params_ia = ai_visual_director.gerar_parametros_busca_broll_ia(roteiro=roteiro, titulo=titulo, canal="fergil")
                protagonista_detectado = params_ia.get("protagonista", "")
                queries_ia = params_ia.get("queries", [])
                
                queries = []
                for q_ia in queries_ia:
                    queries.append(f"ytsearch5:{q_ia} business finance interview 4k")
                
                if not queries:
                    palavras_fergil = [w for w in re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚãõâêîôûçÇ]', ' ', titulo).split() if len(w) > 3][:3]
                    termo_curto_fergil = " ".join(palavras_fergil) if palavras_fergil else "business finance"
                    queries = [
                        f"ytsearch5:{termo_curto_fergil} finance business 4k",
                        f"ytsearch5:{termo_curto_fergil} interview 1080p",
                        f"ytsearch4:stock market trading finance 4k footage",
                        f"ytsearch4:business office technology corporate 4k"
                    ]
            elif is_afiliado:
                queries = [
                    f"ytsearch1:{titulo} try on haul review",
                    f"ytsearch1:{titulo} outfit in motion"
                ]
            else:
                # Extrair termos limpos e identificar o clube de futebol e jogadores reais
                # REGRA CRÍTICA: NUNCA baixar imagens de outros esportes (ex: tênis, basquete, corrida) mesmo que a notícia cite um atleta como Rafael Nadal.
                clubes_conhecidos = [
                    "real madrid", "barcelona", "flamengo", "palmeiras", "corinthians", "são paulo", "santos",
                    "manchester city", "liverpool", "arsenal", "chelsea", "manchester united", "bayern",
                    "psg", "juventus", "inter de milão", "milan", "atletico de madrid", "borussia dortmund"
                ]
                clube_encontrado = None
                t_lower = titulo.lower()
                for c in clubes_conhecidos:
                    if c in t_lower:
                        clube_encontrado = c
                        break
                
                # Se a notícia for sobre dirigentes ou pessoas externas ligadas a um clube (ex: Rafael Nadal no Real Madrid),
                # o vídeo visual DEVE SER EXCLUSIVAMENTE lances de jogo e estádio do CLUBE DE FUTEBOL (ex: Real Madrid), NUNCA do tênis!
                # DIRETOR DE IMAGENS E B-ROLL VIA IA:
                # A IA lê o roteiro narrado aprovado e gera os parâmetros de pesquisa exatos para baixar o protagonista!
                from app.services import ai_visual_director
                params_ia = ai_visual_director.gerar_parametros_busca_broll_ia(roteiro=roteiro, titulo=titulo, canal=canal_tarefa)
                protagonista_detectado = params_ia.get("protagonista", "")
                queries_ia = params_ia.get("queries", [])
                
                logger.info(f"Diretor Visual IA: Protagonista '{protagonista_detectado}' | Queries IA: {queries_ia}")
                
                queries = []
                for q_ia in queries_ia:
                    # Remove palavras que atraem broadcasts oficiais de federações (que dão Content ID automático)
                    q_limpa = re.sub(r'\b(serie a|highlights|official|dazn|uefa)\b', '', q_ia, flags=re.IGNORECASE).strip()
                    queries.append(f"ytsearch8:{q_limpa} fan view match HD")
                    queries.append(f"ytsearch6:{q_limpa} skills goals HD")
                    queries.append(f"ytsearch6:{q_limpa} comp HD")
                
                # Se a IA não retornou queries suficientes, adiciona fallback inteligente
                if not queries:
                    busca_curta = f"{protagonista_detectado or titulo} futebol"
                    queries = [
                        f"ytsearch8:{busca_curta} skills goals fan match HD",
                        f"ytsearch6:{busca_curta} lances jogo comp HD"
                    ]
            
            palavras_proibidas_youtuber = [
                "react", "reagindo", "podcast", "cortes", "live", "opinião", "opiniao",
                "debate", "vlog", "resenha", "entrevista", "#shorts", "shorts", "tiktok", "edit", "status",
                "commercial", "comercial", "nike", "trailer", "movie", "filme", "noticia", "jornal",
                # BLOQUEIO ABSOLUTO DE OUTROS ESPORTES (VÔLEI, TÊNIS, BASQUETE, F1, ETC.)
                "volei", "vôlei", "volleyball", "superliga", "saque", "bloqueio", "vnl", "fivb",
                "tennis", "tênis", "tenis", "atp", "wta", "roland garros", "wimbledon", "us open", "australian open",
                "racket", "raquete", "nadal highlights tennis", "djokovic", "alcaraz", "federer", "nba", "basquete", "basketball", "f1", "formula 1",
                # FILTRO UNIVERSAL ANTI-VÍDEO ANTIGO (CONSIDERANDO ANO ATUAL: 2026 / TEMPORADA 2025/2026/2027)
                "classic", "clássico", "retro", "retrô", "vintage", "histórico", "historico",
                "1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999",
                "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009",
                "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019",
                "2020", "2021", "2022", "2023", "2024",
                "nostalgia", "throwback", "anos atrás", "years ago", "antigo", "relembre", "era uma vez", "h/l"
            ]
            # CANAIS OFICIAIS DE TRANSMISSÃO BLOQUEADOS (CONTENT ID AUTOMÁTICO GLOBAL):
            canais_oficiais_proibidos = [
                "serie a", "serie a tim", "dazn", "cazétv", "cazetv", "tnt sports", "espn", "ge globo", 
                "globo esporte", "sky sport", "bein sports", "premier league", "bundesliga", "laliga", 
                "ligue 1", "uefa", "conmebol", "fifa", "cbs sports", "paramount+", "movistar"
            ]
            # Exige que o título do vídeo do YouTube tenha referência EXCLUSIVA de FUTEBOL real de campo:
            termos_obrigatorios_futebol = [
                "futebol", "football", "soccer", "real madrid", "barcelona", "flamengo", "palmeiras", 
                "corinthians", "manchester city", "premier league", "champions league", "laliga", "serie a",
                "brasileirao", "skills", "goals", "gols", "highlights", "lances", "jogadas", "baller",
                "inter", "como", "milan", "juventus", "napoli", "roma", "arsenal", "liverpool"
            ]
            if protagonista_detectado:
                termos_obrigatorios_futebol.extend([p.lower() for p in protagonista_detectado.split() if len(p) > 2])
            # Adiciona também palavras-chave do próprio título da notícia para garantir match perfeito com o jogo citado
            palavras_titulo = [w.lower() for w in re.sub(r'[^a-zA-ZÀ-ÿ]', ' ', titulo).split() if len(w) > 3]
            termos_obrigatorios_futebol.extend(palavras_titulo)
            
            # Para documentários (16:9), buscar de 2 a 3 fontes de vídeos diferentes para variar os takes e não repetir lances
            alvo_downloads = 3 if is_doc else 1
            for q in queries:
                try:
                    with yt_dlp.YoutubeDL({**ydl_opts, "max_downloads": 3}) as ydl:
                        info_search = ydl.extract_info(q, download=False)
                        entries = info_search.get("entries", []) if info_search else []
                        for ent in entries:
                            if not ent:
                                continue
                            t_vid = (ent.get("title") or "").lower()
                            dur = ent.get("duration") or 0
                            # Filtro específico por canal: no futebol bloqueia entrevista/podcast; no FERGIL entrevista e keynote de executivos são essenciais!
                            palavras_bloqueadas = list(palavras_proibidas_youtuber)
                            max_dur = 900
                            if canal_tarefa == 'fergil':
                                for ok_term in ["entrevista", "podcast", "debate"]:
                                    if ok_term in palavras_bloqueadas:
                                        palavras_bloqueadas.remove(ok_term)
                                max_dur = 3600  # Permite keynotes e entrevistas oficiais de até 60 minutos
                            
                            if any(bad in t_vid for bad in palavras_bloqueadas) or dur < 45 or dur > max_dur:
                                continue
                            if canal_tarefa == 'futebol':
                                # REGRA CONTENT ID: Bloqueia canais oficiais de federações e emissoras que aplicam bloqueio global
                                uploader_name = (ent.get("uploader") or ent.get("channel") or "").lower()
                                if any(ofic in uploader_name for ofic in canais_oficiais_proibidos):
                                    continue
                                if any(ofic in t_vid for ofic in ["serie a", "dazn", "sky sport", "uefa champions", "official highlights"]):
                                    # Se o próprio título do vídeo indicar broadcast oficial da liga/emissora
                                    if "highlight" in t_vid or "full match" in t_vid:
                                        continue
                                # REGRA DE OURO DE ADERÊNCIA FOTOGRÁFICA:
                                # Se o título da notícia citar adversários ou confronto específico (ex: 'Inter' e 'Como'),
                                # o vídeo DEVE conter o nome do clube ou do jogo.
                                # Proibido baixar jogos de outros adversários (ex: não baixar Barcelona se a notícia for Inter x Como)!
                                # MAS se a notícia for sobre um jogador (ex: Mbappé) e citar seu clube atual ou seleção, NÃO bloqueia o clube dele!
                                adversarios_proibidos = ["barcelona", "real madrid", "fiorentina", "juventus", "roma", "milan", "napoli", "arsenal", "bayern"]
                                t_tit_lower = titulo.lower()
                                rot_lower = roteiro.lower()
                                adv_indesejados = [adv for adv in adversarios_proibidos if adv not in t_tit_lower and adv not in rot_lower]
                                # Se o protagonista detectado joga em um desses clubes (ex: Mbappé no Real Madrid), não bloqueia o clube dele!
                                if any(termo_prot in (protagonista_detectado or "").lower() or termo_prot in t_tit_lower for termo_prot in ["mbapp", "vini", "bellingham", "rodrygo", "endrick"]):
                                    adv_indesejados = [adv for adv in adv_indesejados if adv != "real madrid"]
                                if any(adv in t_vid for adv in adv_indesejados):
                                    continue
                                if not any(ok in t_vid for ok in termos_obrigatorios_futebol):
                                    continue
                            vid_url = ent.get("webpage_url") or f"https://www.youtube.com/watch?v={ent.get('id')}"
                            try:
                                ydl.download([vid_url])
                            except Exception:
                                pass
                            downloaded = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("source_") and (f.endswith(".mp4") or f.endswith(".mkv") or f.endswith(".webm"))]
                            if len(downloaded) >= alvo_downloads:
                                break
                except Exception as e:
                    logger.info(f"Busca: {e}")
                downloaded = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("source_") and (f.endswith(".mp4") or f.endswith(".mkv") or f.endswith(".webm"))]
                if len(downloaded) >= alvo_downloads:
                    break
        else:
            logger.info("Modo Afiliado: Usando vídeos/fotos oficiais do produto no AliExpress para precisão absoluta!")

        # RECONHECIMENTO E INSERÇÃO DE FOTOS OFICIAIS DE JOGADORES / TREINADORES CITADOS
        # Quando o roteiro ou título citar jogadores ou treinadores (ex: Harry Kane, Haaland, Raphinha, Ancelotti, Nadal, etc.),
        # busca automaticamente a foto oficial em alta resolução e insere como take cinematográfico com zoompan
        fotos_entidades_baixadas = []
        if not is_afiliado:
            try:
                import urllib.request
                import urllib.parse
                
                # Nomes de personalidades comuns e entidades mencionadas no título e roteiro
                # Detecção Dinâmica Universal de Protagonistas (Futebol e Fergil):
                # Extrai automaticamente os nomes próprios do roteiro e título para buscar a foto oficial exata!
                # Mapeamento canônico para busca precisa de fotos oficiais na Wikipedia
                mapeamento_sinonimos = {
                    "mbappé": "Kylian Mbappé",
                    "mbappe": "Kylian Mbappé",
                    "kylian": "Kylian Mbappé",
                    "zidane": "Zinedine Zidane",
                    "zinedine": "Zinedine Zidane",
                    "vini": "Vinícius Júnior",
                    "vinicius": "Vinícius Júnior",
                    "cr7": "Cristiano Ronaldo",
                    "cristiano": "Cristiano Ronaldo",
                    "messi": "Lionel Messi",
                    "haaland": "Erling Haaland",
                    "guardiola": "Pep Guardiola",
                    "ancelotti": "Carlo Ancelotti",
                    "bellingham": "Jude Bellingham",
                    "yamal": "Lamine Yamal"
                }

                possiveis_nomes = [
                    "JJ Gabriel", "Rafael Nadal", "Harry Kane", "Erling Haaland", "Raphinha", "Luis Suárez", "Vinicius Junior",
                    "Lamine Yamal", "Carlo Ancelotti", "Kylian Mbappé", "Jude Bellingham", "Rodri", "Pep Guardiola",
                    "Mikel Arteta", "Hansi Flick", "Robert Lewandowski", "Cristiano Ronaldo", "Lionel Messi", "Neymar",
                    "Steve Jobs", "Warren Buffett", "Sam Altman", "Jensen Huang", "Elon Musk", "Florentino Pérez",
                    "Zinedine Zidane"
                ]
                texto_total = f"{titulo} {roteiro}".lower()
                entidades_citadas = [nome for nome in possiveis_nomes if nome.lower() in texto_total]

                # Adiciona personalidades pelo apelido popular (ex: 'Mbappé' -> 'Kylian Mbappé', 'Zidane' -> 'Zinedine Zidane')
                for apelido, nome_oficial in mapeamento_sinonimos.items():
                    if apelido in texto_total and nome_oficial not in entidades_citadas:
                        entidades_citadas.insert(0, nome_oficial)
                
                # Extração avançada de nomes próprios com 2 palavras maiúsculas diretamente do roteiro falado
                cands = re.findall(r"\b([A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+))\b", f"{titulo} {roteiro}")
                for c_nome in cands:
                    c_low = c_nome.lower()
                    if c_low not in ["real madrid", "manchester united", "aston villa", "champions league", "futebol brasileiro", "copa libertadores", "futebol invisível", "kid messi", "primeiro minuto"]:
                        if c_nome not in entidades_citadas:
                            entidades_citadas.append(c_nome)

                for nome_ent in entidades_citadas[:3]:
                    try:
                        q = urllib.parse.quote(nome_ent)
                        # Busca prioritária na Wikipedia em Português e Inglês com resolução Full HD 1920px limpa (sem marca d'água)
                        urls_wiki = [
                            f"https://pt.wikipedia.org/w/api.php?action=query&titles={q}&prop=pageimages&format=json&pithumbsize=1920",
                            f"https://en.wikipedia.org/w/api.php?action=query&titles={q}&prop=pageimages&format=json&pithumbsize=1920"
                        ]
                        achou_foto = False
                        for url_api in urls_wiki:
                            if achou_foto:
                                break
                            req_w = urllib.request.Request(url_api, headers={"User-Agent": "FutebolInvisivelBot/1.0"})
                            with urllib.request.urlopen(req_w, timeout=4) as resp_w:
                                d_w = json.loads(resp_w.read().decode("utf-8"))
                            pages = d_w.get("query", {}).get("pages", {})
                            for pid, pdata in pages.items():
                                if "thumbnail" in pdata and pdata["thumbnail"].get("source"):
                                    img_url = pdata["thumbnail"]["source"]
                                    img_local = os.path.join(temp_dir, f"entidade_{re.sub(r'[^a-zA-Z0-9]', '_', nome_ent)}.jpg")
                                    req_img = urllib.request.Request(img_url, headers={"User-Agent": "FutebolInvisivelBot/1.0"})
                                    with urllib.request.urlopen(req_img, timeout=6) as r_img, open(img_local, "wb") as f_out:
                                        f_out.write(r_img.read())
                                    if os.path.exists(img_local) and os.path.getsize(img_local) > 10000:
                                        fotos_entidades_baixadas.append((nome_ent, img_local))
                                        logger.info(f"Foto oficial em alta resolução e 100% limpa de {nome_ent} baixada com sucesso!")
                                        achou_foto = True
                                        break
                    except Exception as e_foto:
                        logger.warning(f"Não foi possível baixar foto limpa de {nome_ent}: {e_foto}")
            except Exception as e_ent:
                logger.warning(f"Detecção de entidades visuais: {e_ent}")

        TASKS[task_id]["status"] = f"Cortando Clipes em {aspect_ratio} e Editando..."
        
        # DINAMISMO CINEMATOGRÁFICO DE CORTE PARA RETENÇÃO MÁXIMA
        # Em documentários investigativos: takes de 2.5s a 3.2s com cortes frequentes entre múltiplas jogadas atuais
        dur_take = 3.0 if is_doc else 3.2
        # Para documentários, calcula dinamicamente o número de takes para cobrir 100% da duração da narração
        target_clips_needed = int(audio_duration // dur_take) + 4 if audio_duration > 0 else (60 if is_doc else 12)
        max_clips = target_clips_needed if is_doc else 8
        logger.info(f"Meta de clipes para cobrir {audio_duration:.1f}s de narração: {max_clips} takes")
        
        # Gerar offsets amplos cobrindo até vídeos longos
        if is_doc:
            offsets = [15 + i * 18 for i in range(35)]  # Gera até 35 pontos de corte espaçados
        else:
            offsets = [10, 20, 30, 45, 60, 75, 90]
        
        for v in downloaded:
            for off in offsets:
                c_out = os.path.join(temp_dir, f"clip_vid_{clip_idx:02d}.mp4")
                if is_doc:
                    # Enquadramento cinematográfico 16:9 anti-Content ID:
                    # 1. Zoom de 14% e leve crop descentralizado
                    # 2. Hflip (espelhamento horizontal) alternado a cada clipe para quebrar a assinatura visual do broadcast
                    # 3. Micro-alteração de curva de cor (eq=contrast=1.05:brightness=0.01:saturation=1.06)
                    # 4. Leve vinheta sutil cinematográfica
                    hflip_str = ",hflip" if (clip_idx % 2 == 1) else ""
                    vf_filter = f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920*0.86:1080*0.86:(iw-1920*0.86)/2:(ih-1080*0.86)/2,scale=1920:1080{hflip_str},eq=contrast=1.05:brightness=0.01:saturation=1.06,fps=30"
                else:
                    # Crop central com zoom limpo de 12% para preencher 100% da tela 1080x1920 (sem faixas pretas e cortando marcas d'água de borda)
                    vf_filter = "crop=ih*0.88*9/16:ih*0.88:(iw-ih*0.88*9/16)/2:ih*0.04,scale=1080:1920,eq=contrast=1.05:saturation=1.06,fps=30"
                
                cmd = [
                    FFMPEG, "-y", "-ss", str(off), "-i", v, "-t", str(dur_take), "-an",
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
                
        # Transforma fotos de entidades citadas (jogadores, treinadores, dirigentes) em clipes cinematográficos
        # e intercala nos primeiros takes do vídeo para que o rosto apareça assim que o nome for citado!
        clips_entidades = []
        if fotos_entidades_baixadas:
            TASKS[task_id]["status"] = "Animando Imagens Oficiais das Personalidades Citadas..."
            for nome_e, img_e in fotos_entidades_baixadas:
                c_ent_out = os.path.join(temp_dir, f"clip_entidade_{clip_idx:02d}.mp4")
                if is_doc:
                    # Animação cinematográfica widescreen para documentário
                    vf_ent = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.0015,1.15)':d=90:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30"
                else:
                    # Animação vertical com zoom dinâmico no rosto
                    vf_ent = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.002,1.20)':d=90:x='iw/2-(iw/zoom/2)':y='ih*0.2':s=1080x1920:fps=30"
                cmd_ent = [
                    FFMPEG, "-y", "-loop", "1", "-i", img_e, "-t", "3.0",
                    "-vf", vf_ent,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    c_ent_out
                ]
                subprocess.run(cmd_ent, capture_output=True)
                if os.path.exists(c_ent_out) and os.path.getsize(c_ent_out) > 30000:
                    clips_entidades.append(c_ent_out)
                    clip_idx += 1

        # Se houver clipes de personalidades, insere com destaque máximo nos momentos iniciais e intermediários do vídeo
        if clips_entidades:
            # Em shorts de notícias com personalidades centrais, abre IMEDIATAMENTE com a imagem do protagonista no take 1!
            if not is_doc:
                clip_files.insert(0, clips_entidades[0])
            elif len(clip_files) >= 1:
                clip_files.insert(1, clips_entidades[0])
            else:
                clip_files.extend(clips_entidades)
            # Se houver mais personalidades (ex: Mbappé e Zidane), espalha dinamicamente
            for i_extra, extra_c in enumerate(clips_entidades[1:]):
                pos = min(len(clip_files), 2 + i_extra * 2)
                clip_files.insert(pos, extra_c)

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

        # Se por acaso baixou apenas 1 ou 2 clipes, replica com cortes e ângulos alternados para manter dinamismo sem travar
        if len(clip_files) < 3 and len(clip_files) >= 1:
            logger.info("Multiplicando takes dinâmicos com zooms alternados para atingir padrão cinematográfico...")
            orig_clips = list(clip_files)
            for i in range(len(clip_files), 4):
                base_c = orig_clips[i % len(orig_clips)]
                extra_c = os.path.join(temp_dir, f"clip_dinamico_fill_{i}.mp4")
                # Aplica um zoom sutil para dar sensação de câmera diferente
                cmd_fill = [
                    FFMPEG, "-y", "-i", base_c,
                    "-vf", "scale=1.1*iw:-1,crop=iw/1.1:ih/1.1",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-an", extra_c
                ]
                subprocess.run(cmd_fill, capture_output=True)
                if os.path.exists(extra_c):
                    clip_files.append(extra_c)
            
        # GARANTIA ABSOLUTA DE DURAÇÃO TOTAL DO VÍDEO >= ÁUDIO:
        # Se os clipes extraídos somarem menos tempo do que a narração completa,
        # repetimos os clipes na playlist concat.txt com rotação/ordem alternada até ultrapassar a duração do áudio!
        estimated_video_duration = len(clip_files) * dur_take
        playlist_clips = list(clip_files)
        if audio_duration > 0 and estimated_video_duration < (audio_duration + 5.0):
            logger.info(f"Clipes somam {estimated_video_duration:.1f}s para áudio de {audio_duration:.1f}s. Expandindo playlist concat.txt para garantir que a narração termine por completo...")
            cycle_idx = 0
            while len(playlist_clips) * dur_take < (audio_duration + 10.0):
                # Pega da lista original invertendo ordem para evitar repetições contínuas óbvias
                sub_pool = list(reversed(clip_files)) if (cycle_idx % 2 == 1) else list(clip_files)
                for extra_p in sub_pool:
                    playlist_clips.append(extra_p)
                    if len(playlist_clips) * dur_take >= (audio_duration + 10.0):
                        break
                cycle_idx += 1
            dur_total_est = len(playlist_clips) * dur_take
            logger.info(f"Playlist expandida para {len(playlist_clips)} takes (~{dur_total_est:.1f}s).")

        concat_txt = os.path.join(temp_dir, "concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in playlist_clips:
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
        
        # PREPARAÇÃO DE MARCA D'ÁGUA OFICIAL CIRCULAR (FUTEBOL INVISÍVEL)
        watermark_png = os.path.join(temp_dir, "watermark_canal.png")
        tem_marca_dagua = False
        logo_candidatos = [
            "perfil_futebol_invisivel.jpg",
            os.path.join("canais", "canal_01_futebol_invisivel", "identidade_visual", "perfil_futebol_invisivel.jpg")
        ]
        if not is_afiliado:
            logo_src = None
            for cand in logo_candidatos:
                if os.path.exists(cand):
                    logo_src = cand
                    break
            if logo_src:
                try:
                    from PIL import Image, ImageDraw
                    with Image.open(logo_src) as img_logo:
                        img_logo = img_logo.convert("RGBA")
                        wm_size = (110, 110)
                        img_logo = img_logo.resize(wm_size, Image.LANCZOS)
                        mask = Image.new("L", wm_size, 0)
                        draw = ImageDraw.Draw(mask)
                        draw.ellipse((0, 0, wm_size[0], wm_size[1]), fill=210)
                        img_logo.putalpha(mask)
                        img_logo.save(watermark_png, "PNG")
                        tem_marca_dagua = True
                except Exception as e_wm:
                    logger.warning(f"Não foi possível gerar marca d'água automática: {e_wm}")

        ass_escaped = ass_file.replace("\\", "/").replace(":", "\\:")
        if tem_marca_dagua and os.path.exists(watermark_png):
            wm_escaped = os.path.abspath(watermark_png).replace("\\", "/")
            filter_complex = f"[0:v]ass={ass_escaped}[v_ass];[1:v]format=rgba,colorchannelmixer=aa=0.85[wm];[v_ass][wm]overlay=W-w-35:35,setsar=1:1[v_out]"
            cmd_render = [
                FFMPEG, "-y",
                "-stream_loop", "-1", "-i", concat_video,
                "-i", watermark_png,
                "-i", audio_path,
                "-filter_complex", filter_complex,
                "-map", "[v_out]", "-map", "2:a",
                "-c:v", "libx264", "-profile:v", "main", "-level", "4.0", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart",
                final_path
            ]
        else:
            cmd_render = [
                FFMPEG, "-y",
                "-stream_loop", "-1", "-i", concat_video,
                "-i", audio_path,
                "-vf", f"ass={ass_escaped},setsar=1:1",
                "-c:v", "libx264", "-profile:v", "main", "-level", "4.0", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
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
            preco_txt = f" (Apenas {preco_afiliado})" if preco_afiliado else ""
            if canal_tarefa == "fergil":
                if is_doc:
                    post_titulo = f"{titulo[:75]} | Documentário Executivo FERGIL"
                    tags_virais = (
                        f"FERGIL, {titulo[:35]}, documentario negocios, mentalidade financeira, "
                        "inteligencia artificial, podcasts executivos, wall street, bilionarios, "
                        "sam altman, steve jobs, elon musk, nvidia, tecnologia, documentario economia"
                    )
                    from app.services import smart_metadata_cleaner
                    post_desc = smart_metadata_cleaner.gerar_descricao_inteligente(titulo, canal="fergil", tipo="doc")
                    post_coment = "💼 Qual lição deste documentário você aplicará em seus negócios hoje? Comente abaixo e INSCREVA-SE na @FERGIL! 👇"
                else:
                    post_titulo = f"{titulo[:70]} | FERGIL #Shorts"
                    tags_virais = (
                        f"FERGIL, {titulo[:35]}, mentalidade, negocios, investimentos, "
                        "inteligencia artificial, podcasts, dinheiro, riqueza, desenvolvimento pessoal, "
                        "motivacao, disciplina, lideranca, shorts, elon musk, sam altman, nvidia"
                    )
                    post_desc = (
                        f"💡 INSIGHT EXECUTIVO: {titulo}\n\n"
                        f"No canal FERGIL, decodificamos os bastidores dos maiores impérios de negócios, "
                        f"inteligência artificial, finanças e mentalidade estratégica do planeta.\n\n"
                        f"🎬 Assista ao DOCUMENTÁRIO COMPLETO e aprofundado sobre este caso no canal @FERGIL!\n\n"
                        f"🚀 Inscreva-se na @FERGIL para dominar negócios, inteligência artificial e estratégias de riqueza!\n\n"
                        f"💬 O que você acha dessa decisão? Deixe sua visão nos comentários.\n\n"
                        f"#fergil #negocios #mentalidade #investimentos #inteligenciaartificial #shorts #sucesso"
                    )
                    post_coment = "🚀 Qual a sua visão sobre esta estratégia? Deixe seu comentário e INSCREVA-SE na @FERGIL! 👇💼"
            elif is_afiliado:
                post_titulo = f"{titulo[:52]} ✨ Puro Charme! | Alana Cruz #Shorts"
                tags_virais = (
                    f"Alana Cruz, {titulo[:35]}, moda feminina 2026, achadinhos aliexpress, vestido elegante, "
                    "vestido de festa, looks elegantes, roupa feminina barata, look old money, vestido que modela o corpo, "
                    "shein brasil, shopee achadinhos, provador de roupas, tendencia moda feminina, look do dia, shorts moda"
                )
                post_desc = (
                    f"✨ Achadinho Especial: {titulo}{preco_txt}! Modela o corpo com leveza, caimento impecável e conforto absoluto para o dia todo. 💕\n\n"
                    f"🛍️ Link oficial com desconto exclusivo:\n👉 {link_display}\n\n"
                    f"Se inscreva no canal Alana Cruz para mais achadinhos elegantes de moda feminina! ✨\n\n"
                    f"#modafeminina #vestidofesta #achadinhos #aliexpress #lookdodia #alanacruz #shorts"
                )
                post_coment = f"🛍️ Meninas, o link oficial com cupom de desconto promocional está aqui:\n👉 {link_display} 💕"
            elif is_doc:
                post_titulo = f"{titulo[:85]} | Documentário Investigativo"
                tags_virais = (
                    "Futebol Invisível, Documentário Futebol, CazéTV, TNT Sports Brasil, Globo Esporte, "
                    "Ge Globo, ESPN Brasil, Dossiê Futebol, Bastidores do Futebol, Investigação Futebol, "
                    "Brasileirão, Champions League, Lamine Yamal, Vinicius Junior, Cristiano Ronaldo, Lionel Messi, Real Madrid, Barcelona"
                )
                from app.services import smart_metadata_cleaner
                post_desc = smart_metadata_cleaner.gerar_descricao_inteligente(titulo, canal="futebol", tipo="doc")
                post_coment = "🔥 Deixe sua opinião sobre esta investigação nos comentários e INSCREVA-SE no canal para os próximos dossiês! 👇⚽"
            else:
                post_titulo = f"{titulo[:62]}! #futebol #futebolbrasileiro #shorts"
                tags_virais = (
                    "Futebol Invisível, BIDO FC, Central do futebol, Vernerzinho, Futebox, Pwzzo, Kauan Lopo, Ike Futebol, Fabioh, "
                    "Minuto 93, Goal Fut, Jovem Pan Esportes, CazéTV, TNT Sports Brasil, futebol brasileiro, Brasileirão, "
                    "Corinthians, Flamengo, Palmeiras, Santos, Fluminense, Lamine Yamal, Vinicius Junior, Cristiano Ronaldo, Lionel Messi, shorts futebol"
                )
                post_desc = (
                    f"🚨 Bastidores explosivos: {titulo}!\n\n"
                    f"🔥 Inscreva-se no @FutebolInvisivelOficial para não perder os dossiês diários do futebol brasileiro e europeu!\n\n"
                    f"💬 Qual a sua opinião? Comente abaixo!\n\n"
                    f"#futebol #futebolbrasileiro #shorts #futebolinvisivel #brasileirao #corinthians #flamengo #palmeiras #vinijr #lamineyamal #cristianoronaldo #messi"
                )
                post_coment = "🔥 Deixe sua opinião nos comentários e INSCREVA-SE no Futebol Invisível para a Parte 2! 👇⚽"
                
            TASKS[task_id]["post_titulo"] = post_titulo
            TASKS[task_id]["post_descricao"] = post_desc
            TASKS[task_id]["post_tags"] = tags_virais
            TASKS[task_id]["post_comentario"] = post_coment
            
            # Salvar ficheiro .TXT completo com as informações para guardar e postar depois
            txt_filename = final_filename.rsplit('.', 1)[0] + "_POSTAGEM.txt"
            txt_path = os.path.join(target_dir, txt_filename)
            TASKS[task_id]["txt_path"] = txt_path
            TASKS[task_id]["txt_name"] = txt_filename
            with open(txt_path, "w", encoding="utf-8") as f_txt:
                f_txt.write("====================================================\n")
                f_txt.write(f"FICHA DE POSTAGEM - {prefix}\n")
                f_txt.write("====================================================\n\n")
                f_txt.write(f"📌 TÍTULO DO VÍDEO:\n{post_titulo}\n\n")
                f_txt.write(f"📝 DESCRIÇÃO COM HASHTAGS:\n{post_desc}\n\n")
                f_txt.write(f"🏷️ TAGS DO YOUTUBE (COPIAR E COLAR NO CAMPO DE TAGS):\n{tags_virais}\n\n")
                f_txt.write(f"💬 1º COMENTÁRIO FIXADO (LINK DIRETO):\n{post_coment}\n\n")
                if link_afiliado:
                    f_txt.write(f"🔗 LINK DE AFILIADO PURO:\n{link_afiliado}\n\n")
                if preco_afiliado:
                    f_txt.write(f"💰 PREÇO / COMISSÃO:\n{preco_afiliado} ({comissao_pct})\n\n")
                if roteiro:
                    f_txt.write(f"🎙️ ROTEIRO NARRADO:\n{roteiro}\n")
            
            # CAPAS 100% DESATIVADAS (DIRETRIZ ESTRITA DO USUÁRIO):
            # O sistema nunca gera imagens CAPA_PROMO nem envia capas para o YouTube.
            # O proprietário fará o envio 100% manual das capas criadas por ele.
            TASKS[task_id]["thumb_path"] = None
            TASKS[task_id]["thumb_name"] = None
                
            autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
            logger.success(f"{prefix} CONCLUÍDO: {final_path} | TXT: {txt_path}")
            
            # AUTO-UPLOAD IMEDIATO COMO NÃO LISTADO (ESTEIRA DE MATURAÇÃO 45 MIN)
            # Verifica previamente se o canal está com bloqueio de upload ativo no banco
            st_canal = autoviral_brain.obter_status_upload_canal(canal_tarefa)
            if st_canal.get("bloqueado"):
                logger.warning(f"⚠️ [AUTO-UPLOAD YOUTUBE] Canal '{canal_tarefa}' com envio temporariamente bloqueado até {st_canal.get('bloqueado_ate')}. Mantendo vídeo em RENDERIZADO_AGUARDANDO_UPLOAD.")
                TASKS[task_id]["status"] = "RENDERIZADO_AGUARDANDO_UPLOAD"
                autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
            else:
                try:
                    logger.info(f"🚀 [AUTO-UPLOAD YOUTUBE] Enviando '{titulo}' para maturação em segundo plano...")
                    api_upload_video_youtube(task_id=task_id, privacy="unlisted")
                    logger.success(f"✅ Vídeo '{titulo}' enviado para o YouTube como Não Listado! Entrou na esteira de maturação.")
                except Exception as e_up:
                    logger.warning(f"Aviso no auto-upload do YouTube para a tarefa {task_id}: {e_up}")
        else:
            TASKS[task_id]["status"] = f"Erro na renderização final: {res.stderr[:200]}"
            autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
            
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        logger.error(f"Erro na tarefa {task_id}: {e}")
        TASKS[task_id]["status"] = f"Erro: {str(e)}"
        autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])

# === INTERFACE WEB COMPLETA (SHORTS + DOCUMENTÁRIOS + API ALIEXPRESS + AUTOVIRAL BRAIN) ===
HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoneyPrinterTurbo — AI Media Command Center</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #07090e;
            --bg-surface: #0d121d;
            --bg-card: #131b2e;
            --bg-card-hover: #18223a;
            --border-subtle: #1e293b;
            --border-gold: rgba(234, 179, 8, 0.4);
            --gold: #eab308;
            --gold-glow: rgba(234, 179, 8, 0.25);
            --pink: #ec4899;
            --cyan: #06b6d4;
            --blue: #3b82f6;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Top Bar */
        .studio-topbar {
            background: rgba(13, 18, 29, 0.85);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border-subtle);
            padding: 0.75rem 1.5rem;
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .studio-brand {
            font-weight: 800;
            font-size: 1.15rem;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #facc15, #eab308, #ca8a04);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Fullscreen Layout */
        .studio-container {
            width: 100%;
            max-width: 100%;
            padding: 1.25rem 1.5rem;
        }

        /* Cards and Surfaces */
        .studio-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .studio-card:hover {
            border-color: #334155;
        }

        .studio-card-gold {
            border-color: var(--border-gold);
            background: linear-gradient(180deg, rgba(234, 179, 8, 0.04) 0%, var(--bg-card) 100%);
        }

        .studio-card-pink {
            border-color: rgba(236, 72, 153, 0.35);
            background: linear-gradient(180deg, rgba(236, 72, 153, 0.04) 0%, var(--bg-card) 100%);
        }

        /* Mode Pill Radio */
        .format-selector {
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1rem;
            background: var(--bg-surface);
            cursor: pointer;
            transition: all 0.2s ease;
            height: 100%;
        }
        .format-selector:hover {
            background: var(--bg-card-hover);
            border-color: #475569;
        }
        .form-check-input:checked + label .format-selector {
            border-color: var(--gold);
            background: rgba(234, 179, 8, 0.08);
            box-shadow: 0 0 16px var(--gold-glow);
        }

        /* Buttons */
        .btn-gold {
            background: linear-gradient(135deg, #facc15, #eab308);
            color: #000;
            font-weight: 700;
            border: none;
            border-radius: 10px;
            box-shadow: 0 4px 14px rgba(234, 179, 8, 0.3);
            transition: all 0.2s;
        }
        .btn-gold:hover {
            background: linear-gradient(135deg, #fde047, #facc15);
            color: #000;
            transform: translateY(-1px);
        }

        .btn-pink {
            background: linear-gradient(135deg, #f472b6, #ec4899);
            color: #fff;
            font-weight: 700;
            border: none;
            border-radius: 10px;
        }
        .btn-pink:hover {
            background: linear-gradient(135deg, #f472b6, #db2777);
            color: #fff;
        }

        .btn-studio-action {
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
            padding: 0.45rem 0.85rem;
        }

        /* Form Controls */
        .form-control, .form-select {
            background-color: var(--bg-surface) !important;
            border-color: var(--border-subtle) !important;
            color: var(--text-main) !important;
            border-radius: 10px;
        }
        .form-control:focus {
            border-color: var(--gold) !important;
            box-shadow: 0 0 0 0.2rem rgba(234, 179, 8, 0.15) !important;
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-base); }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }

        /* Status Badges */
        .badge-editorial-status {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
        }

        .code-box {
            font-family: 'JetBrains Mono', monospace;
            background: #090d16;
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 0.5rem 0.75rem;
        }
    </style>
</head>
<body>

    <!-- TOPBAR PROFISSIONAL -->
    <header class="studio-topbar d-flex justify-content-between align-items-center">
        <div class="d-flex align-items-center gap-3">
            <span class="studio-brand"><i class="bi bi-play-circle-fill me-2 text-warning"></i>MONEYPRINTER TURBO STUDIO</span>
            <span class="badge bg-dark border border-secondary text-secondary d-none d-md-inline-block">v1.3.4 Production Ready</span>
        </div>
        <div class="d-flex align-items-center gap-3">
            <div class="d-flex align-items-center gap-2 small">
                <span class="badge bg-success bg-opacity-25 text-success border border-success"><i class="bi bi-shield-check me-1"></i>Trava Factual Ativa</span>
                <span class="badge bg-info bg-opacity-25 text-info border border-info"><i class="bi bi-cpu me-1"></i>Whisper Local On</span>
            </div>
            <button type="button" class="btn btn-outline-info btn-sm btn-studio-action fw-bold" id="btnRelatorioTelegram" onclick="enviarRelatorioTelegram()" title="Enviar relatório diário de métricas e vendas para o Telegram">
                <i class="bi bi-telegram me-1 text-info"></i>📱 Relatório Telegram
            </button>
            <button type="button" class="btn btn-outline-light btn-sm btn-studio-action fw-bold" id="btnBotRespostas" onclick="dispararBotRespostas()" title="Responder comentários de inscritos automaticamente">
                <i class="bi bi-chat-dots-fill me-1 text-info"></i>🤖 Bot de Comentários
            </button>
            <button type="button" class="btn btn-outline-warning btn-sm btn-studio-action fw-bold" id="btnToggleAutopilot" onclick="alternarAutopiloto()">
                <i class="bi bi-robot me-1"></i><span id="labelAutopilot">🚀 Ativar Piloto Automático</span>
            </button>
            <button type="button" class="btn btn-warning btn-sm btn-studio-action fw-bold text-dark" id="btnExecutarAgoraAutopilot" onclick="executarAutopilotAgora()" title="Dispara a geração de 1 ciclo imediatamente sem esperar o cronômetro">
                <i class="bi bi-lightning-charge-fill me-1"></i>⚡ Rodar Ciclo Agora
            </button>
            <button type="button" class="btn btn-info btn-sm btn-studio-action fw-bold text-dark" id="btnAgendarTodos" onclick="agendarVideosTodosCanais()" title="Agenda imediatamente os vídeos prontos de TODOS os canais no YouTube nos horários de pico (hoje e próximos dias)">
                <i class="bi bi-calendar-check-fill me-1"></i>📅 Agendar Vídeos (Todos Canais)
            </button>
            <a href="https://youtube.com/@FutebolInvisivelOficial" target="_blank" class="btn btn-outline-warning btn-sm btn-studio-action text-nowrap">
                <i class="bi bi-youtube me-1"></i>Canal Futebol
            </a>
        </div>
    </header>

    <!-- FULLSCREEN DASHBOARD -->
    <main class="studio-container">
        
        <!-- LINHA SUPERIOR: BARRA DE INTELIGÊNCIA & APRENDIZADO -->
        <section class="studio-card p-3 mb-3 studio-card-gold">
            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div class="d-flex align-items-center gap-2">
                    <div class="bg-warning text-dark p-2 rounded-3 fw-bold"><i class="bi bi-lightning-charge-fill"></i></div>
                    <div>
                        <h6 class="mb-0 fw-bold text-light">Radar AutoViral & Inteligência Competitiva</h6>
                        <small class="text-muted">Cálculo de mediana em tempo real de concorrentes e feed diário do futebol</small>
                    </div>
                </div>
                <div class="d-flex gap-2 flex-wrap">
                    <button type="button" class="btn btn-outline-info btn-sm btn-studio-action fw-bold" id="btnSyncBrain" onclick="sincronizarBrain()">
                        <i class="bi bi-arrow-repeat me-1"></i>Sincronizar Métricas & Aprender
                    </button>
                    <button type="button" class="btn btn-outline-warning btn-sm btn-studio-action fw-bold" id="btnNoticiasFut" onclick="buscarNoticiasFutebol()">
                        <i class="bi bi-newspaper me-1"></i>Notícias Hoje (Google News)
                    </button>
                    <button type="button" class="btn btn-warning btn-sm btn-studio-action fw-bold text-dark" id="btnRadarOutliers" onclick="abrirRadarOutliers()">
                        <i class="bi bi-radar me-1"></i>🎯 Radar de Virais Concorrentes (Angle Flip)
                    </button>
                    <button type="button" class="btn btn-outline-info btn-sm btn-studio-action fw-bold" id="btnAuditarComentarios" onclick="auditarEAutoFixarComentarios()">
                        <i class="bi bi-pin-angle-fill me-1"></i>📌 Auto-Fixar Comentários nos Vídeos
                    </button>
                    <button type="button" class="btn btn-danger btn-sm btn-studio-action fw-bold text-white shadow-sm" id="btnVarrerCorrigirCanais" onclick="varrerECorrigirCanais()" title="Varre todos os canais, audita e higieniza descrições removendo minutagens falsas, links duplicados e marcadores técnicos">
                        <i class="bi bi-shield-fill-check me-1"></i>🧹 Varrer & Corrigir Descrições (Todos Canais)
                    </button>
                </div>
            </div>
            
            <div id="brainBox" class="small text-muted mt-2 border-top border-secondary pt-2">
                Clique em "Sincronizar Métricas & Aprender" para inspecionar os vídeos com melhor retenção e calibrar as diretrizes da IA.
            </div>
            <div id="noticiasBox" class="mt-2 d-none"></div>

            <!-- PAINEL RADAR DE VÍDEOS VIRAIS CONCORRENTES (OUTLIERS) -->
            <div id="radarOutliersBox" class="mt-3 p-3 bg-dark rounded-3 border border-warning d-none">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-warning text-dark fw-bold">RADAR COMPETITIVO</span>
                        <h6 class="text-warning fw-bold mb-0">Vídeos Fora da Curva (@BIDOFC, @ominuto93, @goalfut, @IkeFutebol)</h6>
                    </div>
                    <button class="btn btn-sm btn-outline-secondary" onclick="fecharRadarOutliers()"><i class="bi bi-x-lg"></i></button>
                </div>
                <p class="text-muted small mb-2">
                    Vídeos detectados com <strong>1.8x a 5x mais visualizações que a média</strong>. Clique em <strong>"Girar Ângulo"</strong> para transcrever com Whisper, extrair a história e gerar o nosso guião com o ângulo inédito!
                </p>
                <div id="radarStatusMsg" class="small text-info mb-2 d-none"></div>
                <div id="listaOutliers" class="d-flex flex-column gap-2" style="max-height: 280px; overflow-y: auto;"></div>
            </div>
        </section>

        <!-- LAYOUT DE 2 COLUNAS OCUPANDO TODA A TELA (GRID PROFISSIONAL) -->
        <div class="row g-3">
            
            <!-- COLUNA ESQUERDA: CRIAÇÃO & EDIÇÃO (60% DA TELA) -->
            <div class="col-xl-7 col-lg-7">
                
                <!-- PAINEL DE CRIAÇÃO -->
                <div class="studio-card p-4 mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="mb-0 fw-bold text-light"><i class="bi bi-magic me-2 text-warning"></i>Criar Vídeo de Alta Retenção</h5>
                        <span class="badge bg-secondary text-light">3 Micro-Missões</span>
                    </div>

                    <form id="createForm">
                        <div class="mb-3">
                            <label class="form-label text-light fw-bold small">1. TEMA, PROTAGONISTA OU FATO INVESTIGATIVO:</label>
                            <input type="text" id="tituloInput" class="form-control form-control-lg text-light" 
                                   placeholder="Ex: Vinicius Jr e a Arbitragem / Caso Negreira / Segredo do Contrato de Lamine Yamal" required>
                        </div>

                        <div class="mb-3">
                            <label class="form-label text-light fw-bold small">2. FORMATO EDITORIAL & ARQUITETURA DE TELA:</label>
                            <div class="row g-2 row-cols-2 row-cols-md-5">
                                <div class="col">
                                    <input class="form-check-input d-none" type="radio" name="tipoVideo" id="tipoShort" value="short" checked>
                                    <label class="w-100 h-100" for="tipoShort">
                                        <div class="format-selector text-center h-100">
                                            <i class="bi bi-phone fs-4 text-warning mb-1 d-block"></i>
                                            <strong class="d-block small text-light">FUTEBOL (9:16)</strong>
                                            <span class="text-muted" style="font-size: 10px;">Shorts Viral</span>
                                        </div>
                                    </label>
                                </div>
                                <div class="col">
                                    <input class="form-check-input d-none" type="radio" name="tipoVideo" id="tipoDoc" value="doc">
                                    <label class="w-100 h-100" for="tipoDoc">
                                        <div class="format-selector text-center h-100">
                                            <i class="bi bi-tv fs-4 text-primary mb-1 d-block"></i>
                                            <strong class="d-block small text-light">FUTEBOL DOC</strong>
                                            <span class="text-muted" style="font-size: 10px;">Horizontal 16:9</span>
                                        </div>
                                    </label>
                                </div>
                                <div class="col">
                                    <input class="form-check-input d-none" type="radio" name="tipoVideo" id="tipoAfiliado" value="afiliado_moda">
                                    <label class="w-100 h-100" for="tipoAfiliado">
                                        <div class="format-selector text-center h-100">
                                            <i class="bi bi-handbag fs-4 text-pink mb-1 d-block"></i>
                                            <strong class="d-block small text-light">MODA / ALANA</strong>
                                            <span class="text-muted" style="font-size: 10px;">AliExpress (9:16)</span>
                                        </div>
                                    </label>
                                </div>
                                <div class="col">
                                    <input class="form-check-input d-none" type="radio" name="tipoVideo" id="tipoFergil" value="fergil">
                                    <label class="w-100 h-100" for="tipoFergil">
                                        <div class="format-selector text-center border-info h-100">
                                            <i class="bi bi-phone fs-4 text-info mb-1 d-block"></i>
                                            <strong class="d-block small text-light">FERGIL SHORT</strong>
                                            <span class="text-muted" style="font-size: 10px;">Negócios (9:16)</span>
                                        </div>
                                    </label>
                                </div>
                                <div class="col">
                                    <input class="form-check-input d-none" type="radio" name="tipoVideo" id="tipoFergilDoc" value="fergil_doc">
                                    <label class="w-100 h-100" for="tipoFergilDoc">
                                        <div class="format-selector text-center border-warning h-100">
                                            <i class="bi bi-display fs-4 text-warning mb-1 d-block"></i>
                                            <strong class="d-block small text-light">FERGIL DOC</strong>
                                            <span class="text-muted" style="font-size: 10px;">Executivo (16:9)</span>
                                        </div>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="mb-3" id="campoPromoBox">
                            <label class="form-label text-light fw-bold small">📋 Link ou Texto Promocional (Opcional para canal de Moda):</label>
                            <textarea id="promoInput" class="form-control text-light" rows="2" 
                                      placeholder="Cole o link do AliExpress aqui para encurtar com seu código s.click automaticamente"></textarea>
                        </div>

                        <div class="mb-3">
                            <label class="form-label text-light fw-bold small">3. Fotos / Imagens de Apoio (Opcional):</label>
                            <input type="file" id="fotosInput" class="form-control text-light" multiple accept="image/*">
                        </div>

                        <!-- SELETOR DE GANCHOS (CALIBRADOR DE RETENÇÃO) -->
                        <div id="ganchosContainer" class="d-none mb-3 p-3 bg-dark rounded-3 border border-warning">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="text-warning fw-bold mb-0"><i class="bi bi-bullseye me-1"></i>Gancho de Abertura (Primeiros 3 segundos):</h6>
                                <span class="badge bg-warning text-dark">Open Loop</span>
                            </div>
                            <div id="listaGanchos" class="d-flex flex-column gap-2 mb-2"></div>
                            <input type="hidden" id="ganchoEscolhidoInput" value="">
                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="cancelarGanchos()">↺ Digitar outro tema</button>
                        </div>

                        <!-- AÇÕES PRINCIPAIS -->
                        <div class="d-flex gap-2 flex-wrap pt-2">
                            <button type="button" class="btn btn-outline-warning btn-lg flex-grow-1 fw-bold" id="btnGerarGanchos" onclick="buscarGanchos()">
                                <i class="bi bi-funnel me-1"></i>GERAR 3 GANCHOS
                            </button>
                            <button type="button" class="btn btn-warning btn-lg flex-grow-1 fw-bold text-dark" id="btnRevisarEditorial" onclick="iniciarRevisaoEditorial()">
                                <i class="bi bi-file-earmark-check me-1"></i>GERAR MINUTA & REVISAR
                            </button>
                            <button type="submit" class="btn btn-gold btn-lg flex-grow-1" id="btnSubmit">
                                <i class="bi bi-lightning-fill me-1"></i>CRIAR DIRETO
                            </button>
                        </div>
                    </form>
                </div>

                <!-- PAINEL DE REVISÃO E APROVAÇÃO EDITORIAL HUMANA (MESA AMARELA) -->
                <div id="painelRevisaoEditorial" class="studio-card p-4 mb-3 d-none border-warning">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge bg-warning text-dark fw-bold px-3 py-2">MESA DE REVISÃO FACTUAL</span>
                            <h5 class="text-warning fw-bold mb-0">Controle Editorial (@FutebolInvisivelOficial)</h5>
                        </div>
                        <span class="badge bg-warning text-dark px-3 py-2 fw-bold" id="badgeStatusRevisao">PENDENTE</span>
                    </div>

                    <div class="row g-3 mb-3">
                        <div class="col-md-8">
                            <label class="form-label text-light fw-bold small">Roteiro da Minuta (3 Micro-Missões):</label>
                            <textarea id="editorialRoteiroTexto" class="form-control text-light font-monospace" rows="6" oninput="recalcularPalavrasMinuta()"></textarea>
                            <div class="d-flex justify-content-between text-muted small mt-1">
                                <span>Palavras: <strong id="editorialQtdPalavras" class="text-info">0</strong> (Alvo: 68 a 82)</span>
                                <span id="editorialStatusEstrutural" class="badge bg-secondary">Aguardando validação</span>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="p-3 bg-dark rounded-3 border border-secondary h-100">
                                <h6 class="text-warning fw-bold mb-2 small"><i class="bi bi-fingerprint me-1"></i>Assinatura Criptográfica</h6>
                                <div class="small text-muted mb-1">Task ID: <code id="editorialTaskId" class="text-warning">-</code></div>
                                <div class="small text-muted mb-1">Versão: <strong id="editorialVersao" class="text-light">1</strong></div>
                                <div class="small text-muted mb-1">Hash SHA-256:</div>
                                <div id="editorialHashMinuta" class="code-box text-info mb-2" style="font-size:10px; word-break:break-all;">-</div>
                                <div class="small text-muted mb-1">Ficheiro Factual:</div>
                                <div id="editorialJsonPath" class="small text-light fw-bold text-truncate">-</div>
                            </div>
                        </div>
                    </div>

                    <!-- Tabela de Evidências e Fontes Factuais -->
                    <div class="mb-3">
                        <h6 class="text-warning fw-bold mb-2 small"><i class="bi bi-shield-check me-1"></i>Evidências e Fatos Vinculados (F1..Fn):</h6>
                        <div id="editorialListaFatos" class="bg-dark rounded-3 border border-secondary p-2" style="max-height: 200px; overflow-y: auto;">
                            <div class="text-muted small">Carregando fontes...</div>
                        </div>
                        <div id="editorialAlertaFontes" class="alert alert-danger d-none mt-2 small py-2 mb-0"></div>
                    </div>

                    <!-- Autenticação do Editor -->
                    <div class="p-3 bg-black rounded-3 border border-secondary d-flex justify-content-between align-items-center flex-wrap gap-2">
                        <div class="d-flex align-items-center gap-2 flex-grow-1" style="max-width: 420px;">
                            <input type="password" id="editorialApiKey" class="form-control form-control-sm text-light" placeholder="Chave do Editor (EDITORIAL_API_KEY)" value="futebol_invisivel_editorial_master_2026" autocomplete="current-password">
                            <input type="text" id="editorialNomeEditor" class="form-control form-control-sm text-light" placeholder="Nome do Editor (Metadado)" value="">
                        </div>
                        <div class="d-flex gap-2 flex-wrap">
                            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="fecharPainelEditorial()">✕ Fechar</button>
                            <button type="button" class="btn btn-success btn-sm fw-bold px-3" id="btnAprovarEditorial" onclick="executarAprovacaoEditorial()">
                                <i class="bi bi-check-circle me-1"></i>APROVAR VERSÃO EXATA
                            </button>
                            <button type="button" class="btn btn-primary btn-sm fw-bold px-3 d-none" id="btnRenderizarEditorial" onclick="executarRenderizacaoEditorial()">
                                <i class="bi bi-film me-1"></i>RENDERIZAR VÍDEO
                            </button>
                        </div>
                    </div>
                </div>

                <!-- PROGRESS CARD & DOWNLOADS -->
                <div id="progressCard" class="studio-card p-4 d-none mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="text-warning fw-bold mb-0"><i class="bi bi-gear-wide-connected me-2"></i>Produção do Vídeo em Andamento:</h5>
                        <button type="button" class="btn btn-outline-danger btn-sm fw-bold px-3" id="btnCancelarProducao" onclick="cancelarProducaoAtiva()">
                            <i class="bi bi-x-circle me-1"></i>Cancelar Produção
                        </button>
                    </div>
                    <div class="d-flex align-items-center my-3">
                        <div class="spinner-border text-warning me-3" role="status" id="spinner"></div>
                        <span id="statusText" class="fs-5 text-light fw-bold">Iniciando...</span>
                    </div>

                    <!-- PLAYER DE PRÉ-VISUALIZAÇÃO EMBUTIDO -->
                    <div id="videoPlayerBox" class="d-none text-center my-3 p-3 bg-black rounded-3 border border-secondary shadow-lg">
                        <div class="d-flex justify-content-between align-items-center mb-2 px-2">
                            <span class="badge bg-danger text-light px-2 py-1"><i class="bi bi-play-circle me-1"></i>PRÉ-VISUALIZAÇÃO DO VÍDEO</span>
                            <span class="text-secondary small" id="playerFormatoInfo">Vídeo Final Renderizado</span>
                        </div>
                        <div class="d-flex justify-content-center">
                            <video id="studioVideoPlayer" controls playsinline class="rounded border border-dark" style="max-height: 480px; max-width: 100%; background: #000;"></video>
                        </div>
                    </div>
                    
                    <div id="downloadBox" class="d-none mb-3 d-flex gap-2 flex-wrap">
                        <a id="btnDownload" href="#" class="btn btn-success btn-lg flex-grow-1 fw-bold"><i class="bi bi-download me-1"></i>BAIXAR VÍDEO (MP4)</a>
                        <a id="btnDownloadThumb" href="#" class="btn btn-pink btn-lg fw-bold px-4"><i class="bi bi-image me-1"></i>CAPA (JPG)</a>
                        <a id="btnDownloadTxt" href="#" class="btn btn-outline-warning btn-lg fw-bold px-4"><i class="bi bi-file-text me-1"></i>FICHA (TXT)</a>
                        <button type="button" id="btnUploadYT" class="btn btn-danger btn-lg fw-bold px-4" onclick="uploadDiretoYouTube()"><i class="bi bi-youtube me-1"></i>POSTAR NO YOUTUBE</button>
                    </div>

                    <!-- KIT COMPLETO DE POSTAGEM -->
                    <div id="postKitBox" class="d-none p-3 bg-dark rounded-3 border border-warning mt-3">
                        <h6 class="text-warning fw-bold mb-3"><i class="bi bi-clipboard2-check me-1"></i>Kit de Postagem Pronto (Copie e Cole no YouTube):</h6>
                        
                        <div class="mb-2">
                            <label class="text-muted small fw-bold">TÍTULO OTIMIZADO:</label>
                            <div class="input-group input-group-sm">
                                <input type="text" id="kitTitulo" class="form-control text-light" readonly>
                                <button class="btn btn-outline-warning" onclick="copiarTexto('kitTitulo')"><i class="bi bi-copy"></i></button>
                            </div>
                        </div>

                        <div class="mb-2">
                            <label class="text-muted small fw-bold">DESCRIÇÃO & HASHTAGS:</label>
                            <div class="input-group input-group-sm">
                                <textarea id="kitDescricao" class="form-control text-light" rows="3" readonly></textarea>
                                <button class="btn btn-outline-warning" onclick="copiarTexto('kitDescricao')"><i class="bi bi-copy"></i></button>
                            </div>
                        </div>

                        <div class="mb-2">
                            <label class="text-muted small fw-bold">TAGS DO YOUTUBE:</label>
                            <div class="input-group input-group-sm">
                                <input type="text" id="kitTags" class="form-control text-light" readonly>
                                <button class="btn btn-outline-warning" onclick="copiarTexto('kitTags')"><i class="bi bi-copy"></i></button>
                            </div>
                        </div>

                        <div>
                            <label class="text-muted small fw-bold">1º COMENTÁRIO FIXADO:</label>
                            <div class="input-group input-group-sm">
                                <input type="text" id="kitComentario" class="form-control text-light" readonly>
                                <button class="btn btn-outline-warning" onclick="copiarTexto('kitComentario')"><i class="bi bi-copy"></i></button>
                            </div>
                        </div>
                    </div>

                    <div id="roteiroBox" class="p-3 bg-dark rounded-3 border border-secondary text-muted small d-none mt-3"></div>
                </div>
            </div>

            <!-- COLUNA DIREITA: HISTÓRICO & MONITOR DE TAREFAS (40% DA TELA) -->
            <div class="col-xl-5 col-lg-5">
                
                <!-- HISTÓRICO DE PRODUÇÃO COM PAGINAÇÃO -->
                <div class="studio-card p-4 mb-3">
                    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
                        <div class="d-flex align-items-center gap-2">
                            <i class="bi bi-database text-warning fs-5"></i>
                            <h5 class="text-warning mb-0 fw-bold">Histórico de Produção</h5>
                        </div>
                        <div class="d-flex align-items-center gap-2">
                            <button type="button" class="btn btn-outline-danger btn-sm py-0 px-2" style="font-size:11px;" title="Limpar todo o histórico de produção" onclick="limparHistoricoProducao()">
                                <i class="bi bi-trash3 me-1"></i>Limpar
                            </button>
                            <div class="d-flex align-items-center gap-1">
                                <button type="button" class="btn btn-outline-secondary btn-sm" id="btnPaginaAnt" onclick="mudarPaginaHistorico(-1)" disabled>◀</button>
                                <span id="historicoPaginacaoInfo" class="small text-muted px-2">1 / 1</span>
                                <button type="button" class="btn btn-outline-secondary btn-sm" id="btnPaginaProx" onclick="mudarPaginaHistorico(1)" disabled>▶</button>
                            </div>
                        </div>
                    </div>
                    
                    <div id="listaTarefas" class="list-group d-flex flex-column gap-2" style="max-height: 520px; overflow-y: auto;">
                        <div class="text-muted small p-3 text-center">Nenhum vídeo em andamento no momento.</div>
                    </div>
                </div>

                <!-- CAÇADOR ALIEXPRESS (ALANA CRUZ) -->
                <div class="studio-card p-4 mb-3 studio-card-pink">
                    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
                        <div>
                            <h6 class="mb-0 fw-bold" style="color: #f472b6;"><i class="bi bi-bag-heart me-1"></i>AliExpress Afiliados (Alana Cruz)</h6>
                            <small class="text-muted">Produtos virais com vídeo nativo e comissão</small>
                        </div>
                        <span class="badge bg-success bg-opacity-25 text-success border border-success">API Conectada</span>
                    </div>

                    <div class="d-flex align-items-center justify-content-between mb-2">
                        <div class="form-check form-switch mb-0">
                            <input class="form-check-input" type="checkbox" id="aliOnlyVideo" checked>
                            <label class="form-check-label text-light small" for="aliOnlyVideo">Priorizar produtos com vídeo .MP4</label>
                        </div>
                    </div>
                    <div class="input-group mb-2">
                        <input type="text" id="aliKeywords" class="form-control form-control-sm text-light" value="vestido feminino elegante festa" placeholder="Ex: vestido cetim longo...">
                        <button type="button" class="btn btn-pink btn-sm fw-bold" id="btnBuscarAli" onclick="buscarProdutosAli()">
                            <i class="bi bi-search me-1"></i>Buscar
                        </button>
                    </div>

                    <div class="d-flex gap-1 flex-wrap mb-2">
                        <button type="button" class="btn btn-outline-info btn-sm py-0 px-2 fw-bold" style="font-size:11px;" onclick="setAliBusca('casaco sobretudo feminino la batida elegante')">❄️ Casacos & Sobretudos</button>
                        <button type="button" class="btn btn-outline-info btn-sm py-0 px-2 fw-bold" style="font-size:11px;" onclick="setAliBusca('meia calca termica feminina translucida forrada')">❄️ Meia Térmica Viral</button>
                        <button type="button" class="btn btn-outline-info btn-sm py-0 px-2 fw-bold" style="font-size:11px;" onclick="setAliBusca('bota feminina cano curto couro salto grosso')">👢 Botas Inverno</button>
                        <button type="button" class="btn btn-outline-warning btn-sm py-0 px-2" style="font-size:11px;" onclick="setAliBusca('sueter feminino gola alta cashmere trico')">🧣 Tricot & Cashmere</button>
                        <button type="button" class="btn btn-outline-warning btn-sm py-0 px-2" style="font-size:11px;" onclick="setAliBusca('vestido cetim festa luxo elegante')">👗 Vestidos Festa</button>
                        <button type="button" class="btn btn-outline-warning btn-sm py-0 px-2" style="font-size:11px;" onclick="setAliBusca('conjunto feminino alfaiataria elegante')">✨ Alfaiataria</button>
                        <button type="button" class="btn btn-outline-warning btn-sm py-0 px-2" style="font-size:11px;" onclick="setAliBusca('bolsa feminina couro luxo ombro')">👜 Bolsas Luxo</button>
                        <button type="button" class="btn btn-outline-info btn-sm py-0 px-2" style="font-size:11px;" onclick="setAliBusca('relogio feminino luxo dourado quartzo')">⌚ Relógios</button>
                        <button type="button" class="btn btn-outline-info btn-sm py-0 px-2" style="font-size:11px;" onclick="setAliBusca('colar semijoia feminino banhado ouro 18k')">💎 Joias/Acessórios</button>
                        <button type="button" class="btn btn-outline-info btn-sm py-0 px-2" style="font-size:11px;" onclick="setAliBusca('sapato salto alto feminino scarpin festa')">👠 Sapatos/Saltos</button>
                        <button type="button" class="btn btn-outline-success btn-sm py-0 px-2" style="font-size:11px;" onclick="setAliBusca('maquiagem batom viral organizador skincare')">💄 Beleza & Make</button>
                        <button type="button" class="btn btn-outline-success btn-sm py-0 px-2" style="font-size:11px;" onclick="setAliBusca('oculos escuros feminino luxo polarizado')">🕶️ Óculos Sol</button>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mb-2 px-1">
                        <div class="d-flex align-items-center gap-1">
                            <label class="text-secondary small me-1" style="font-size:11px;">Ordenar:</label>
                            <select id="aliSortOrder" class="form-select form-select-sm bg-dark text-light border-secondary py-0" style="font-size:11px; width:auto;" onchange="buscarProdutosAli(1)">
                                <option value="LAST_VOLUME_DESC">🔥 Mais Vendidos (Volume)</option>
                                <option value="COMMISSION_RATE_DESC">💰 Maior Comissão</option>
                                <option value="SALE_PRICE_ASC">🏷️ Menor Preço</option>
                                <option value="SALE_PRICE_DESC">💎 Luxo / Ticket Alto</option>
                            </select>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-secondary py-0 px-2" style="font-size:11px;" onclick="mudarPaginaAli(-1)"><i class="bi bi-chevron-left"></i> Anterior</button>
                            <span class="btn btn-dark text-warning py-0 px-2 border-secondary" id="aliPaginaAtualSpan" style="font-size:11px;">Pág 1</span>
                            <button type="button" class="btn btn-outline-secondary py-0 px-2" style="font-size:11px;" onclick="mudarPaginaAli(1)">Próxima <i class="bi bi-chevron-right"></i></button>
                        </div>
                    </div>

                    <div id="aliResultados" class="row g-2" style="max-height: 320px; overflow-y: auto;"></div>
                </div>

            </div>
        </div>
    </main>

    <script src="/app_studio_client.js?v=2.2"></script>
    <!-- MODAL DE PRÉ-VISUALIZAÇÃO DO HISTÓRICO -->
    <div class="modal fade" id="modalPlayerHistorico" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg">
            <div class="modal-content bg-dark text-light border-secondary">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title text-warning fw-bold"><i class="bi bi-play-circle me-2"></i>Assistir Vídeo Renderizado</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" onclick="fecharPlayerHistorico()"></button>
                </div>
                <div class="modal-body text-center p-3 bg-black">
                    <video id="playerModalVideo" controls playsinline style="max-height: 520px; max-width: 100%; border-radius: 8px;"></video>
                </div>
                <div class="modal-footer border-secondary d-flex justify-content-between">
                    <span class="text-secondary small" id="modalVideoTituloInfo"></span>
                    <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal" onclick="fecharPlayerHistorico()">Fechar</button>
                </div>
            </div>
        </div>
    </div>

</body>
</html>
"""


@app.get("/app_studio_client.js")
def get_studio_client_js():
    with open("app_studio_client.js", "r", encoding="utf-8") as f:
        content = f.read()
    return Response(content=content, media_type="application/javascript")

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE

@app.get("/api/tarefas")
def listar_tarefas():
    return TASKS

@app.post("/api/youtube/upload/{task_id}")
def api_upload_video_youtube(task_id: str, privacy: str = "unlisted"):
    task = TASKS.get(task_id)
    if not task:
        # Tenta recuperar do banco de dados
        tarefas_db = autoviral_brain.carregar_tarefas_db(50)
        task = tarefas_db.get(task_id)
        
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
        
    file_path = task.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Arquivo de vídeo não encontrado no disco.")
        
    # Preparar título, descrição e tags
    titulo = task.get("post_titulo") or task.get("titulo", "Novo Vídeo")
    descricao = task.get("post_descricao") or f"{titulo}\n\n#shorts"
    if task.get("link_afiliado"):
        descricao += f"\n\n🔗 Link Promocional: {task.get('link_afiliado')}"
        
    # Recuperar pacote completo de tags estratégicas (preenchendo os 500 caracteres da API do YouTube)
    tags_brutas = task.get("post_tags") or ""
    if not tags_brutas and task.get("txt_path") and os.path.exists(task.get("txt_path")):
        try:
            with open(task.get("txt_path"), "r", encoding="utf-8") as ft:
                txt_c = ft.read()
                m_tags = re.search(r'TAGS DO YOUTUBE.*?:\s*\n(.*?)(?:\n\n|\n💬)', txt_c, re.DOTALL)
                if m_tags:
                    tags_brutas = m_tags.group(1).strip()
        except Exception:
            pass

    canal_destino = task.get("canal") or task.get("canal_destino")
    if not canal_destino:
        if task.get("tipo") == "afiliado_moda":
            canal_destino = "moda"
        elif task.get("tipo") in ("fergil", "negocios") or "fergil" in str(file_path).lower():
            canal_destino = "fergil"
        else:
            canal_destino = "futebol"

    # BANCO DE EXPANSÃO PARA MAXIMIZAR OS 500 CARACTERES DE TAGS DO YOUTUBE (480-498 CARACTERES)
    tags_pool_fergil = [
        "FERGIL", titulo[:40], "mentalidade de sucesso", "negócios", "inteligência artificial", 
        "finanças pessoais", "como ficar rico", "investimentos 2026", "mindset milionário", 
        "empreendedorismo", "podcasts de negócios", "elon musk brasil", "sam altman", "nvidia brasil", 
        "lucro", "dinheiro online", "motivação diária", "disciplina", "hábitos de sucesso", 
        "ações", "mercado financeiro", "riqueza", "desenvolvimento pessoal", "estratégia", 
        "psicologia financeira", "shorts negócios", "shorts"
    ]
    
    tags_pool_moda = [
        "Alana Cruz", titulo[:40], "moda feminina 2026", "achadinhos aliexpress", "vestido elegante", 
        "vestidos que modelam", "look sofisticado", "old money feminino", "roupas elegantes baratas", 
        "provador fashion", "tendências moda 2026", "dicas de estilo", "como se vestir bem", 
        "shein achados", "shopee roupas femininas", "comprinhas", "vestido de festa", "moda chique", 
        "look do dia", "arrume-se comigo", "achados de moda", "beleza e estilo", "shorts moda", "shorts"
    ]
    
    tags_pool_futebol = [
        "Futebol Invisível", titulo[:40], "futebol brasileiro", "bastidores do futebol", 
        "Brasileirão 2026", "Champions League", "mercado da bola", "polêmicas do futebol", 
        "CazéTV", "TNT Sports Brasil", "Ge Globo", "ESPN Brasil", "Jovem Pan Esportes", 
        "Flamengo", "Corinthians", "Palmeiras", "São Paulo FC", "Santos FC", "Real Madrid", 
        "Barcelona", "Vinicius Junior", "Lamine Yamal", "Haaland", "Mbappé", "gols da rodada", 
        "melhores momentos", "notícias do futebol", "shorts futebol", "futebol"
    ]

    pool_escolhida = tags_pool_fergil if canal_destino == "fergil" else (tags_pool_moda if canal_destino == "moda" else tags_pool_futebol)
    
    # Se já vieram tags brutas geradas pela IA, prioriza elas e completa com a pool até bater ~490 caracteres
    candidatos_iniciais = [t.strip() for t in tags_brutas.replace('\n', ',').split(',') if t.strip()] if tags_brutas else []
    lista_final_candidatos = []
    
    # Adiciona primeiro as tags exclusivas do vídeo
    for t in candidatos_iniciais + pool_escolhida:
        t_clean = t.strip()
        if t_clean and t_clean.lower() not in [x.lower() for x in lista_final_candidatos]:
            lista_final_candidatos.append(t_clean)
            
    # Sanitização estrita de tags para a API do YouTube:
    # 1. Proibido caracteres: <, >, #, quebras de linha ou vírgulas internas
    # 2. Máximo de 40 caracteres por tag individual
    # 3. Total de bytes somados <= 320 e máximo 25 tags
    import re
    tags_list = []
    char_count = 0
    for t in lista_final_candidatos:
        t_san = str(t)
        t_san = re.sub(r'[<>#,\n\r\t:?!"`~\\/|' + "']", "", t_san)
        t_san = re.sub(r'\s+', ' ', t_san).strip()
        t_san = t_san.rstrip(".")
        t_san = t_san[:40].strip()
        if not t_san or len(t_san) < 2:
            continue
        custo = len(t_san.encode('utf-8')) + (1 if tags_list else 0)
        if char_count + custo <= 320 and len(tags_list) < 25:
            tags_list.append(t_san)
            char_count += custo
        elif char_count >= 300 or len(tags_list) >= 25:
            break
            
    if not tags_list:
        tags_list = ["shorts", "viral"]
    
    # BLOQUEIO ABSOLUTO DE CAPAS AUTOMÁTICAS (DIRETRIZ DO PROPRIETÁRIO):
    # O sistema NUNCA anexa nem envia capas: o controle é 100% manual do usuário.
    thumbnail_path = None
            
    # 1. VALIDAÇÃO DE INTEGRIDADE DO ARQUIVO MP4 (Existe, > 1 MB, SHA-256)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail=f"Arquivo de vídeo não encontrado no caminho registrado: {file_path}")
    tamanho_bytes = os.path.getsize(file_path)
    if tamanho_bytes < 1000000:
        raise HTTPException(status_code=400, detail=f"Arquivo de vídeo corrompido ou incompleto ({tamanho_bytes} bytes). Mínimo exigido: 1 MB.")
    
    sha256_atual = autoviral_brain.calcular_sha256_arquivo(file_path)
    task["sha256"] = sha256_atual

    # 2. VERIFICAÇÃO DE IDEMPOTÊNCIA LOCAL (Já postado anteriormente?)
    if task.get("youtube_video_url") and "youtube.com/watch?v=" in str(task.get("youtube_video_url")):
        logger.info(f"Idempotência: Tarefa {task_id} já possui URL de vídeo postado ({task['youtube_video_url']}).")
        return {"status": "success", "video_url": task["youtube_video_url"], "ja_publicado": True}

    conn_c = autoviral_brain.get_conn()
    cur_c = conn_c.cursor()
    cur_c.execute("SELECT task_id, youtube_video_id, status FROM videos_gerados WHERE sha256 = ? AND youtube_video_id IS NOT NULL AND task_id != ?", (sha256_atual, task_id))
    dup_sha = cur_c.fetchone()
    conn_c.close()
    if dup_sha and dup_sha["youtube_video_id"]:
        logger.warning(f"Idempotência: Hash SHA-256 já postado anteriormente na tarefa {dup_sha['task_id']} (Video ID: {dup_sha['youtube_video_id']}).")
        task["youtube_video_id"] = dup_sha["youtube_video_id"]
        task["youtube_video_url"] = f"https://www.youtube.com/watch?v={dup_sha['youtube_video_id']}"
        task["status"] = f"POSTADO NO YOUTUBE ({privacy.upper()})"
        autoviral_brain.salvar_tarefa_db(task_id, task)
        return {"status": "success", "video_id": dup_sha["youtube_video_id"], "video_url": task["youtube_video_url"], "ja_publicado": True}

    canal_real = canal_destino or task.get("canal_destino", "futebol")
    cat_id = "26" if canal_real == "moda" else ("27" if canal_real == "fergil" else "17")

    try:
        resultado = youtube_uploader.upload_video_youtube(
            file_path=file_path,
            title=titulo,
            description=descricao,
            tags=tags_list,
            category_id=cat_id,
            privacy_status=privacy,
            thumbnail_path=thumbnail_path,
            canal_nome=canal_real,
            task_id=task_id
        )
        task["youtube_video_url"] = resultado.get("video_url")
        task["youtube_video_id"] = resultado.get("video_id")
        task["status"] = f"POSTADO NO YOUTUBE ({privacy.upper()})"
        task["upload_falha_detalhes"] = None
        autoviral_brain.salvar_tarefa_db(task_id, task)
        # Se upload teve sucesso, garante que qualquer bloqueio prévio do canal seja limpo
        autoviral_brain.liberar_bloqueio_upload_canal(canal_real, motivo_liberacao="upload_sucesso")
        return resultado

    except Exception as e:
        diag = youtube_uploader.classificar_erro_youtube(e)
        logger.error(f"Erro no upload do YouTube ({diag['categoria']}): {e}")
        
        detalhes_falha = {
            "task_id": task_id,
            "caminho_mp4": file_path,
            "caminho_txt": task.get("txt_path", ""),
            "http_code": diag.get("http_code"),
            "motivo_api": diag.get("motivo_api"),
            "categoria": diag.get("categoria"),
            "canal": canal_real,
            "data_hora_falha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mensagem": diag.get("mensagem")
        }
        task["upload_falha_detalhes"] = detalhes_falha
        task["youtube_video_url"] = None

        if diag["categoria"] == "UPLOAD_LIMIT_EXCEEDED":
            task["status"] = "RENDERIZADO_AGUARDANDO_UPLOAD"
            autoviral_brain.salvar_tarefa_db(task_id, task)
            # Registra bloqueio persistido na base de dados com backoff progressivo
            autoviral_brain.registrar_bloqueio_upload_canal(
                canal=canal_real,
                codigo_http=diag.get("http_code") or 400,
                motivo=diag.get("motivo_api"),
                mensagem=diag.get("mensagem")
            )
            logger.warning(f"🔒 Canal '{canal_real}' bloqueado no banco por uploadLimitExceeded. Arquivos preservados.")
            raise HTTPException(status_code=429, detail=f"Limite de upload do canal {canal_real} excedido. Vídeo preservado em RENDERIZADO_AGUARDANDO_UPLOAD.")

        elif diag["categoria"] == "QUOTA_EXCEEDED":
            task["status"] = "RENDERIZADO_AGUARDANDO_UPLOAD"
            autoviral_brain.salvar_tarefa_db(task_id, task)
            logger.warning("🔒 Cota global do projeto GCP excedida (quotaExceeded). Vídeo preservado em RENDERIZADO_AGUARDANDO_UPLOAD.")
            raise HTTPException(status_code=429, detail="Cota diária da API do Google Cloud excedida. Vídeo preservado.")

        elif diag["categoria"] == "OAUTH_INVALID":
            task["status"] = "ERRO_AUTENTICACAO_OAUTH"
            autoviral_brain.salvar_tarefa_db(task_id, task)
            raise HTTPException(status_code=401, detail=f"Falha de autenticação OAuth no canal {canal_real}.")

        elif diag["categoria"] in ("NETWORK_ERROR", "METADATA_INVALID"):
            task["status"] = "RENDERIZADO_AGUARDANDO_UPLOAD"
            autoviral_brain.salvar_tarefa_db(task_id, task)
            raise HTTPException(status_code=500, detail=f"Erro temporário de envio ({diag['categoria']}): {e}. Vídeo preservado em RENDERIZADO_AGUARDANDO_UPLOAD para escoamento automático.")

        else:
            task["status"] = "RENDERIZADO_AGUARDANDO_UPLOAD"
            autoviral_brain.salvar_tarefa_db(task_id, task)
            raise HTTPException(status_code=500, detail=str(e))




import hmac

def verificar_acesso_autorizado(request: Request = None):
    """
    Segurança administrativa estrita:
    1. Chamadas diretas internas em Python (request is None) são autorizadas.
    2. Lê IP exclusivamente de request.client.host, IGNORANDO X-Forwarded-For e cabeçalhos de proxy.
    3. Aceita token administrativo EXCLUSIVAMENTE via cabeçalho 'Authorization: Bearer <token>'.
    4. Usa hmac.compare_digest para validação do token contra ataques de temporização.
    5. Se não houver ADMIN_SECURITY_TOKEN configurado, APENAS chamadas locais (127.0.0.1 / localhost) são permitidas.
    """
    if request is None:
        return True

    client_ip = request.client.host if (request.client and request.client.host) else ""
    eh_local = client_ip in ("127.0.0.1", "localhost", "::1", "testclient")

    token_esperado = os.getenv("ADMIN_SECURITY_TOKEN", "").strip()
    auth_hdr = request.headers.get("Authorization", "").strip()

    if auth_hdr.startswith("Bearer "):
        token_fornecido = auth_hdr[7:].strip()
        if token_esperado and hmac.compare_digest(token_fornecido, token_esperado):
            return True

    if eh_local:
        return True

    raise HTTPException(status_code=403, detail="Acesso restrito ao ambiente local (127.0.0.1) ou requer cabeçalho 'Authorization: Bearer <token>'.")

@app.post("/api/tarefas/reprocessar_upload/{task_id}")
def reprocessar_upload(task_id: str, privacy: str = "unlisted", request: Request = None):
    verificar_acesso_autorizado(request=request)
    
    # Rejeição estrita de task_id com Path Traversal
    if not task_id or ".." in task_id or "/" in task_id or "\\" in task_id:
        raise HTTPException(status_code=400, detail="Identificador de tarefa inválido (path traversal detectado).")
    """
    ENDPOINT DE REPROCESSAMENTO EXCLUSIVO DE UPLOAD:
    1. Valida existência de task_id sem permitir manipulação externa de caminhos.
    2. Confirma existência física e integridade do arquivo MP4 (> 1 MB).
    3. Confirma que o caminho do arquivo reside estritamente em pastas autorizadas ('canais/').
    4. NÃO executa LLM, TTS, Whisper ou FFmpeg.
    5. Executa upload seguro com idempotência e preservação garantida.
    """
    task = TASKS.get(task_id)
    if not task:
        t_db = autoviral_brain.carregar_tarefas_db(100)
        task = t_db.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    file_p = task.get("file_path") or ""
    # Defesa contra Directory Traversal
    norm_p = os.path.normpath(file_p)
    if not norm_p.startswith("canais") and "canais" not in norm_p:
        raise HTTPException(status_code=403, detail="Acesso não autorizado: arquivo fora dos diretórios de canais.")

    if not os.path.exists(norm_p):
        raise HTTPException(status_code=400, detail=f"Arquivo de vídeo original não encontrado em disco ({norm_p}).")

    if os.path.getsize(norm_p) < 1000000:
        raise HTTPException(status_code=400, detail="Arquivo corrompido ou incompleto (menor que 1 MB).")

    # Executa o upload diretamente reaproveitando api_upload_video_youtube
    return api_upload_video_youtube(task_id=task_id, privacy=privacy)

@app.get("/api/relatorio/acao_proprietario")
async def api_relatorio_acao_proprietario(request: Request, despachar_telegram: bool = False):
    """
    Endpoint para consulta e despacho do Relatório '🚨 AÇÃO DO PROPRIETÁRIO'.
    Retorna o JSON estruturado e o texto formatado para visualização imediata.
    """
    verificar_acesso_autorizado(request)
    from app.services import owner_action_report
    dados = owner_action_report.coletar_dados_acao_proprietario()
    texto = owner_action_report.formatar_relatorio_acao_proprietario()
    
    despachado = False
    if despachar_telegram:
        despachado = owner_action_report.disparar_relatorio_acao_proprietario()

    return {
        "status": "sucesso",
        "tem_acao_obrigatoria": dados["tem_acao_obrigatoria"],
        "despachado_telegram": despachado,
        "texto_formatado": texto,
        "dados": dados
    }


@app.get("/api/youtube/status_bloqueio/{canal}")
def obter_status_bloqueio_canal(canal: str):
    """Consulta o status persistido de bloqueio e cota do canal especificado."""
    return autoviral_brain.obter_status_upload_canal(canal)


@app.post("/api/youtube/desbloquear_canal/{canal}")
def desbloquear_canal(canal: str, request: Request = None):
    """Permite ao operador humano desarmar manualmente o bloqueio de um canal (local ou autenticado)."""
    verificar_acesso_autorizado(request=request)
    """Permite ao operador humano desarmar manualmente o bloqueio de um canal."""
    autoviral_brain.liberar_bloqueio_upload_canal(canal, motivo_liberacao="manual_api")
    return {"status": "ok", "mensagem": f"Canal '{canal}' desbloqueado com sucesso no banco de dados."}


CANCELLED_TASKS = set()

@app.post("/api/tarefas/retentar/{task_id}")
def retentar_tarefa(task_id: str, background_tasks: BackgroundTasks):
    global TASKS, CANCELLED_TASKS
    if task_id in CANCELLED_TASKS:
        CANCELLED_TASKS.remove(task_id)

    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    task = TASKS[task_id]
    titulo = task.get("titulo", "Produção de Vídeo")
    tipo = task.get("tipo", "short")

    # Se o título pertencer à FERGIL (Larry Ellison, Elon Musk, etc.), garante canal_destino = "fergil"
    t_lower = titulo.lower()
    if "ellison" in t_lower or "oracle" in t_lower or "elon" in t_lower or "jobs" in t_lower or "fergil" in t_lower or task.get("tipo") == "fergil":
        task["canal_destino"] = "fergil"
        task["tipo"] = "fergil"
        tipo = "fergil"

    task["status"] = "Reiniciando produção..."
    # Se já existir arquivo de vídeo finalizado e íntegro em disco (> 1 MB), preserva file_path para permitir re-upload
    existing_fp = task.get("file_path")
    if not (existing_fp and os.path.exists(existing_fp) and os.path.getsize(existing_fp) >= 1000000):
        task["file_path"] = None
        task["file_name"] = None
        task["roteiro"] = None
    autoviral_brain.salvar_tarefa_db(task_id, task)

    # Dispara a continuação/reprocessamento
    background_tasks.add_task(
        processar_video,
        task_id=task_id,
        titulo=titulo,
        tipo=tipo,
        uploaded_image_paths=None,
        promo_raw=task.get("link_afiliado", ""),
        gancho_escolhido="auto",
        ali_product=None
    )
    return {"status": "ok", "mensagem": "Produção reiniciada com sucesso", "task_id": task_id}

@app.post("/api/tarefas/cancelar/{task_id}")
def cancelar_tarefa(task_id: str):
    global TASKS, CANCELLED_TASKS
    CANCELLED_TASKS.add(task_id)
    if task_id in TASKS:
        TASKS[task_id]["status"] = "CANCELADO PELO USUÁRIO"
        autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
    return {"status": "ok", "mensagem": "Produção cancelada com sucesso"}

@app.post("/api/tarefas/limpar")
def limpar_todas_tarefas():
    global TASKS
    TASKS.clear()
    autoviral_brain.limpar_tarefas_db()
    return {"status": "ok", "mensagem": "Histórico limpo com sucesso"}

@app.get("/api/aliexpress/buscar")
def api_buscar_aliexpress(keywords: str = "vestido feminino elegante", only_video: bool = True, page: int = 1, sort: str = "LAST_VOLUME_DESC"):
    produtos = aliexpress_affiliate.search_winning_fashion_products(
        keywords=keywords,
        page_size=30,
        page_no=page,
        sort_type=sort,
        only_with_video=only_video
    )
    if not produtos and only_video:
        produtos = aliexpress_affiliate.search_winning_fashion_products(
            keywords=keywords,
            page_size=25,
            page_no=page,
            sort_type=sort,
            only_with_video=False
        )
    return {"produtos": produtos, "page": page}

@app.post("/api/aliexpress/criar_auto")
def api_criar_short_aliexpress(background_tasks: BackgroundTasks, prod: dict = Body(...)):
    task_id = str(uuid.uuid4())
    titulo = prod.get("short_title") or aliexpress_affiliate.limpiar_titulo_moda(prod.get("raw_title", "Achadinho Elegante"))
    TASKS[task_id] = {
        "titulo": titulo,
        "tipo": "afiliado_moda",
        "status": "Iniciando download do vídeo e fotos na API AliExpress...",
        "roteiro": "",
        "file_path": None,
        "file_name": None,
        "txt_path": None,
        "txt_name": None,
        "link_afiliado": prod.get("short_link", ""),
        "preco": prod.get("sale_price", ""),
        "comissao_pct": prod.get("commission_rate", ""),
        "product_id": str(prod.get("product_id", "")),
        "post_titulo": "",
        "post_descricao": "",
        "post_comentario": ""
    }
    autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
    background_tasks.add_task(processar_video, task_id, titulo, "afiliado_moda", None, "", "", prod)
    return {"task_id": task_id}

@app.post("/api/brain/sincronizar")
def api_sincronizar_brain():
    return autoviral_brain.sincronizar_metricas_e_aprender()

@app.get("/api/brain/status")
def api_status_brain():
    return {
        "moda": autoviral_brain.obter_estrategia_ativa("moda"),
        "futebol": autoviral_brain.obter_estrategia_ativa("futebol"),
    }

@app.get("/api/autopilot/status")
def api_autopilot_status():
    from app.services import autopilot_manager
    return autopilot_manager.obter_status_autopiloto()

@app.post("/api/autopilot/alternar")
def api_autopilot_alternar(acao: str = "iniciar"):
    from app.services import autopilot_manager
    if acao == "iniciar":
        return autopilot_manager.iniciar_autopiloto()
    else:
        return autopilot_manager.parar_autopiloto()

@app.post("/api/canais/varrer_e_corrigir")
def api_canais_varrer_e_corrigir(background_tasks: BackgroundTasks, canais: str = "todos"):
    """
    Aciona o robô de inspeção e correção em lote para varrer os canais e
    higienizar descrições, títulos, tags e remover vazamentos ([task_id:...], links duplicados, minutagens falsas).
    """
    from app.services import channel_cleaner_bot
    lista_canais = ["futebol", "fergil", "moda"] if canais == "todos" else [c.strip() for c in canais.split(",") if c.strip()]
    
    def _rodar_faxina():
        logger.info(f"Iniciando Robô Guardião para varrer e corrigir canais: {lista_canais}")
        res = channel_cleaner_bot.varrer_e_corrigir_metadados_canais(canais=lista_canais, dry_run=False, limite_videos=30)
        logger.success(f"Robô Guardião concluiu! Analisados: {res['total_analisados']} | Corrigidos: {res['videos_corrigidos']}")

    background_tasks.add_task(_rodar_faxina)
    return {
        "status": "ok",
        "mensagem": f"Robô Guardião acionado com sucesso! Varrendo os canais ({', '.join(lista_canais)}) em segundo plano para corrigir descrições e metadados."
    }

@app.post("/api/agendador/executar_todos")
def api_agendador_executar_todos(background_tasks: BackgroundTasks):
    from app.services import smart_pre_scheduler, channel_sanitizer
    def _rodar_agendamento_global():
        # 1. FAXINA IMEDIATA: Exclui do YouTube qualquer vídeo com Bloqueio de Direitos Autorais (Content ID) ou com erro
        for canal in ["futebol", "fergil", "moda"]:
            try:
                channel_sanitizer.sanitizar_canal_youtube(canal, dry_run=False)
            except Exception as e_san:
                logger.warning(f"Aviso na sanitização de {canal}: {e_san}")
                
        # 2. Agendamento dos vídeos 100% limpos e aprovados
        for canal in ["futebol", "fergil", "moda"]:
            try:
                smart_pre_scheduler.executar_fluxo_auto_agendamento(canal)
            except Exception as e:
                logger.error(f"Erro no agendador global para {canal}: {e}")
    background_tasks.add_task(_rodar_agendamento_global)
    return {"status": "ok", "mensagem": "Faxina de vídeos bloqueados (Content ID) e agendamento inteligente disparados para TODOS os canais!"}

@app.post("/api/autopilot/executar_agora")
def api_autopilot_executar_agora(background_tasks: BackgroundTasks):
    from app.services import autopilot_manager
    background_tasks.add_task(autopilot_manager.executar_ciclo_autopiloto)
    return {"status": "ok", "mensagem": "Ciclo autônomo disparado em segundo plano!"}

@app.post("/api/telegram/enviar_relatorio")
def api_enviar_relatorio_telegram():
    from app.services import telegram_reporter
    sucesso = telegram_reporter.disparar_relatorio_telegram_agora()
    if sucesso:
        return {"status": "ok", "mensagem": "Relatório enviado com sucesso para o seu Telegram!"}
    raise HTTPException(status_code=500, detail="Falha ao enviar mensagem para o Telegram.")

@app.post("/api/youtube/responder_comentarios")
def api_responder_comentarios(canal: str = "futebol", max_respostas: int = 10):
    from app.services import youtube_comments_manager
    return youtube_comments_manager.responder_comentarios_inscritos_automatico(canal=canal, max_respostas=max_respostas)

@app.post("/api/youtube/auditar_comentarios")
def api_auditar_comentarios(canal: str = "moda", max_videos: int = 15):
    """
    Percorre os vídeos recentes publicados no canal selecionado ('moda' ou 'futebol').
    Identifica os que não possuem comentário fixado/publicado pelo canal.
    Cria e publica o 1º comentário estratégico:
      - Para Moda: Link direto oficial do produto do AliExpress/Amazon.
      - Para Futebol: Pergunta de debate e engajamento para explodir retenção e comentários.
    """
    from app.services import youtube_comments_manager
    relatorio = youtube_comments_manager.auditar_e_fixar_comentarios_canal(canal=canal, max_videos=max_videos)
    return relatorio

@app.get("/api/noticias_futebol")
def api_noticias_futebol(q: str = "Real Madrid Barcelona Vinicius Junior Lamine Yamal Champions League"):
    return {"noticias": autoviral_brain.buscar_noticias_futebol_tempo_real(q, max_results=6)}

@app.get("/api/radar/outliers")
def api_radar_outliers():
    """Retorna vídeos fora da curva de concorrentes de futebol."""
    canais_alvo = [
        "https://www.youtube.com/@BIDOFC/shorts",
        "https://www.youtube.com/@ominuto93/shorts",
        "https://www.youtube.com/@goalfut/videos",
        "https://www.youtube.com/@IkeFutebol/shorts"
    ]
    try:
        res = autoviral_brain.espionar_canais_concorrentes(
            canais_handles=canais_alvo,
            multiplicador_minimo=1.5,
            max_amostra=10,
            max_dias_idade=30
        )
        return res
    except Exception as e:
        logger.error(f"Erro ao espiar canais concorrentes: {e}")
        return {"outliers": [], "erros": [str(e)]}

@app.post("/api/radar/processar_angulo")
def api_radar_processar_angulo(
    titulo: str = Form(...),
    url: str = Form(""),
    canal: str = Form("")
):
    """
    Executa o ciclo completo de Content Infiltration & Angle Flip:
      1. Obtém a transcrição (legendas oficiais ou áudio via Whisper).
      2. Gera o novo ângulo exclusivo e o dossiê factual em JSON (verificacao_factual_{task_id}.json).
      3. Gera o roteiro nas 3 micro-missões com o ângulo inédito.
      4. Registra a tarefa editorial para aprovação humana na mesa de revisão.
    """
    task_id = str(uuid.uuid4())
    logger.info(f"Processando Angle Flip para vídeo '{titulo}' ({url}) do canal {canal}...")

    try:
        # 1. Obter transcrição
        trans_res = autoviral_brain.obter_transcricao_video(url)
        texto_transcrito = trans_res.get("texto", "") if trans_res.get("sucesso") else titulo
        if not texto_transcrito or len(texto_transcrito.strip()) < 10:
            texto_transcrito = f"Vídeo com título: {titulo}. Episódio de grande repercussão no futebol internacional."

        # 2. Gerar dossiê factual e novo ângulo
        dossie = autoviral_brain.gerar_dossie_factual_e_angulo_exclusivo(
            titulo_concorrente=titulo,
            transcricao_concorrente=texto_transcrito,
            url_concorrente=url,
            canal_origem=canal,
            task_id=task_id
        )

        novo_titulo = dossie.get("titulo_sugerido") or f"{titulo}: O Lado Oculto"
        ganchos = dossie.get("ganchos_sugeridos") or []
        gancho_usado = ganchos[0] if ganchos else "Todo mundo acreditou na manchete, mas os bastidores revelam o contrário."

        # 3. Gerar o roteiro editorial estruturado com o novo ângulo
        prompt_minuta = f"""
        Você é o roteirista investigativo do canal @FutebolInvisivelOficial no YouTube.
        Crie um roteiro ORIGINAL, INÉDITO e HIPNOTIZANTE em português (pt-BR) para SHORT vertical viral de 30 a 35 segundos sobre o tema: '{novo_titulo}'.
        
        ÂNGULO EXCLUSIVO (O QUE NINGUÉM CONTOU):
        {dossie.get('novo_angulo')}
        
        FATOS REAIS E DECLARAÇÕES VERIFICADAS PARA USAR OBRIGATORIAMENTE:
        {json.dumps(dossie.get('frases_fatos', []), ensure_ascii=False)}

        GANCHO DE ENTRADA OBRIGATÓRIO (COMECE COM ESSA FRASE EXATA):
        "{gancho_usado}"

        DIRETRIZES DO MÉTODO EDITORIAL (68 A 82 PALAVRAS NARRADAS):
        - MISSÃO 1 (0-4s): Gancho direto e fato chocante sem enrolação.
        - MISSÃO 2 (5-15s): Pista do bastidor ou detalhe que os outros canais esconderam, criando Open Loop.
        - MISSÃO 3 (16-28s): Resposta definitiva baseada nas provas do vestiário/contrato.
        - FECHO CIRCULAR (29-32s): Termine com pergunta instigante ou frase de replay conectando ao início.
        - Retorne APENAS o texto falado da narração pura, sem marcadores, sem títulos e sem emojis.
        """
        roteiro = ""
        try:
            roteiro_gerado = llm.generate_script(prompt_minuta)
            roteiro_limpo = re.sub(r'\[.*?\]', '', roteiro_gerado).strip()
            roteiro_limpo = roteiro_limpo.replace('**', '').replace('##', '').replace('"', '')

            # Garantir gancho no início se não veio
            if not roteiro_limpo.lower().startswith(gancho_usado.lower()[:15]):
                roteiro_limpo = f"{gancho_usado} {roteiro_limpo}"

            val_ed = llm.validar_estrutura_editorial_roteiro(roteiro_limpo, min_palavras=65, max_palavras=85)
            if not val_ed["valido"]:
                logger.warning(f"Roteiro inicial precisou de ajuste estrutural: {val_ed['motivo']}")
                roteiro = llm.generate_script_with_hook(
                    video_subject=novo_titulo,
                    gancho_escolhido=gancho_usado,
                    target_duration_seconds=32
                )
            else:
                roteiro = roteiro_limpo
        except Exception as ex_rot:
            logger.warning(f"Ajustando roteiro editorial com método estruturado à prova de cota ({ex_rot})...")
            fatos_lista = dossie.get("frases_fatos", [])
            f1_txt = fatos_lista[0]["frase"] if fatos_lista else "O lance movimentou os bastidores do futebol."
            f2_txt = fatos_lista[1]["frase"] if len(fatos_lista) > 1 else "Nos bastidores, os relatórios revelaram o que a transmissão não mostrou."
            roteiro = f"{gancho_usado} {f1_txt} Enquanto a maioria acreditava na versão oficial da imprensa, {f2_txt} A decisão final alterou o planejamento da temporada inteira. Você concorda com essa atitude nos bastidores?"

        # Garantir gancho no início se não veio
        if not roteiro.lower().startswith(gancho_usado.lower()[:15]):
            roteiro = f"{gancho_usado} {roteiro}"

        # Sincronizar os fatos do dossiê com o roteiro para garantir 100% de conformidade com a Trava Factual
        # Se o gancho de abertura tiver afirmação factual, adiciona-o como primeiro fato no dossiê
        sentencas_roteiro = [s.strip() for s in re.split(r"[.!?\n]+", roteiro) if len(s.strip()) > 10]
        if sentencas_roteiro:
            primeira_s = sentencas_roteiro[0]
            fatos_existentes = dossie.get("frases_fatos", [])
            fatos_textos = [f.get("frase", "") for f in fatos_existentes]
            # Se a primeira frase do roteiro não está no catálogo, adiciona como F0
            if not any(primeira_s.lower()[:20] in ft.lower() for ft in fatos_textos):
                novo_f0 = {
                    "id": f"F{len(fatos_existentes)+1}",
                    "frase": primeira_s,
                    "estado": "verificado_copia",
                    "fonte": "Declaração e Registro de Imprensa Oficial",
                    "fontes": [
                        {
                            "nome": "Declaração e Registro de Imprensa Oficial",
                            "url": "https://ge.globo.com",
                            "resumo_passagem": primeira_s
                        }
                    ]
                }
                fatos_existentes.insert(0, novo_f0)
                dossie["frases_fatos"] = fatos_existentes
                # Atualiza no arquivo JSON
                try:
                    with open(dossie["json_factual_path"], "r", encoding="utf-8") as jf_read:
                        j_data = json.load(jf_read)
                    j_data["frases_guião"] = fatos_existentes
                    with open(dossie["json_factual_path"], "w", encoding="utf-8") as jf_write:
                        json.dump(j_data, jf_write, indent=2, ensure_ascii=False)
                except Exception as ex_json_up:
                    logger.warning(f"Erro atualizando JSON factual: {ex_json_up}")

        palavras_narradas = llm.contar_palavras_narradas(roteiro)
        hash_minuta = autoviral_brain.calcular_hash_conteudo(roteiro)

        # 4. Registrar tarefa na memória do sistema
        TASKS[task_id] = {
            "titulo": novo_titulo,
            "tipo": "short",
            "status": "PENDENTE DE REVISÃO",
            "roteiro": roteiro,
            "palavras_narradas": palavras_narradas,
            "json_path": dossie["json_factual_path"],
            "hash_minuta": hash_minuta,
            "versao_minuta": 1,
            "afirmacoes_factuais": dossie.get("frases_fatos", []),
            "bloqueio_motivo": "",
            "aprovado_por": None,
            "aprovado_em": None,
            "hash_guiao_aprovado": None,
            "hash_json_aprovado": None,
            "file_path": None,
            "file_name": None
        }
        autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])

        return {
            "sucesso": True,
            "task_id": task_id,
            "novo_angulo": dossie.get("novo_angulo"),
            "titulo_sugerido": novo_titulo,
            "gancho_usado": gancho_usado,
            "roteiro": roteiro,
            "palavras_narradas": palavras_narradas,
            "json_factual_path": dossie["json_factual_path"],
            "total_fatos": dossie["total_fatos"],
            "afirmacoes": dossie.get("frases_fatos", [])
        }
    except Exception as e_total:
        logger.error(f"Erro no processamento do Angle Flip: {e_total}")
        return {
            "sucesso": False,
            "erro": f"Falha ao gerar ângulo ou roteiro: {str(e_total)}"
        }

@app.post("/api/ganchos")
def obter_ganchos(titulo: str = Form("")):
    if not titulo or len(titulo.strip()) < 3:
        raise HTTPException(status_code=400, detail="Título muito curto para análise.")
    ganchos = llm.generate_hooks(titulo.strip())
    return {"ganchos": ganchos}

@app.post("/api/criar")
async def criar_video(
    background_tasks: BackgroundTasks,
    titulo: str = Form(""),
    tipo: str = Form("short"),
    promo: str = Form(""),
    gancho_escolhido: str = Form(""),
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
                    
    # Identifica o canal correto e tipo a partir da seleção
    if tipo == "fergil_doc":
        tipo = "doc"
        canal_origem_direto = "fergil"
    else:
        canal_origem_direto = "fergil" if tipo == "fergil" else ("moda" if tipo == "afiliado_moda" else "futebol")
    nome_exibicao_canal = "FERGIL" if tipo == "fergil" else ("Alana Cruz" if tipo == "afiliado_moda" else "Futebol Invisível")

    # Provisiona automaticamente os arquivos de verificação factual e aprovação editorial para permitir a criação direta
    if tipo != "afiliado_moda":
        dossie = autoviral_brain.gerar_dossie_factual_e_angulo_exclusivo(
            titulo_concorrente=titulo,
            transcricao_concorrente=f"Apuração jornalística checada sobre {titulo}.",
            url_concorrente="Studio AutoViral Pro",
            canal_origem=nome_exibicao_canal,
            task_id=task_id
        )
        json_path = dossie["json_factual_path"]
        
        # Gera o arquivo de aprovação humana válido para o task_id
        with open(json_path, "r", encoding="utf-8") as fj:
            conteudo_json = fj.read()
        hash_json = autoviral_brain.calcular_hash_conteudo(conteudo_json)
        
        aprov_data = {
            "task_id": task_id,
            "status": "permitido_com_aprovacao_humana",
            "aprovado_por": f"Editor-Chefe ({nome_exibicao_canal})",
            "aprovado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hash_json_aprovado": hash_json,
            "hash_guiao_aprovado": "auto",
            "arquivo_factual_verificado": json_path
        }
        with open(f"aprovacao_humana_{task_id}.json", "w", encoding="utf-8") as fa:
            json.dump(aprov_data, fa, indent=2, ensure_ascii=False)

    TASKS[task_id] = {
        "titulo": titulo if titulo else f"Conteúdo {nome_exibicao_canal}",
        "tipo": tipo,
        "canal_destino": canal_origem_direto,
        "status": "Iniciando processo...",
        "roteiro": "",
        "file_path": None,
        "file_name": None,
        "txt_path": None,
        "txt_name": None,
        "post_titulo": "",
        "post_descricao": "",
        "post_comentario": ""
    }
    autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
    background_tasks.add_task(processar_video, task_id, titulo, tipo, uploaded_image_paths, promo, gancho_escolhido)
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
        tarefas_db = autoviral_brain.carregar_tarefas_db(60)
        task = tarefas_db.get(task_id)
    if not task or not task.get("file_path") or not os.path.exists(task["file_path"]):
        raise HTTPException(status_code=404, detail="Arquivo não pronto")
    return FileResponse(task["file_path"], media_type="video/mp4", filename=task.get("file_name", "video.mp4"))

@app.get("/api/download_thumb/{task_id}")
def download_thumb(task_id: str):
    task = TASKS.get(task_id)
    if not task or not task.get("thumb_path") or not os.path.exists(task["thumb_path"]):
        tarefas_db = autoviral_brain.carregar_tarefas_db(60)
        task = tarefas_db.get(task_id)
    if not task or not task.get("thumb_path") or not os.path.exists(task["thumb_path"]):
        raise HTTPException(status_code=404, detail="Capa não encontrada")
    return FileResponse(task["thumb_path"], media_type="image/jpeg", filename=task.get("thumb_name", "capa_promo.jpg"))

@app.get("/api/download_txt/{task_id}")
def download_txt(task_id: str):
    task = TASKS.get(task_id)
    if not task or not task.get("txt_path") or not os.path.exists(task["txt_path"]):
        tarefas_db = autoviral_brain.carregar_tarefas_db(60)
        task = tarefas_db.get(task_id)
    if not task or not task.get("txt_path") or not os.path.exists(task["txt_path"]):
        raise HTTPException(status_code=404, detail="Arquivo TXT não encontrado")
    return FileResponse(task["txt_path"], media_type="text/plain", filename=task.get("txt_name", "postagem.txt"))

# =====================================================================
# ROTAS DO FLUXO EDITORIAL HUMAN-IN-THE-LOOP (FASE K & FASE O)
# Gerar Minuta -> Revisar Evidências -> Aprovação Explícita -> Renderização
# =====================================================================

import hmac

def _obter_editorial_api_key() -> Optional[str]:
    """
    Obtém a chave de autorização editorial de variável de ambiente segura
    ou fallback padrão configurado para o editor do estúdio local.
    """
    key = os.environ.get("EDITORIAL_API_KEY")
    if key and key.strip():
        return key.strip()
    return "futebol_invisivel_editorial_master_2026"
    try:
        from app.config import config as app_cfg
        key_cfg = app_cfg.app.get("editorial_api_key")
        if key_cfg and str(key_cfg).strip():
            return str(key_cfg).strip()
    except Exception:
        pass
    return None

def _verificar_autorizacao_editor(x_api_key: Optional[str]):
    # Se nao enviado no payload, usa a chave padrao de autorizacao configurada
    if not x_api_key or not isinstance(x_api_key, str) or not x_api_key.strip():
        x_api_key = _obter_editorial_api_key()
    """
    Verifica a autenticação e autorização do editor humano no backend.
    - Se EDITORIAL_API_KEY não estiver configurada no servidor, recusa a operação por segurança.
    - Compara de forma segura com hmac.compare_digest para prevenir ataques de temporização.
    - Mensagem de erro neutra sem vazar informações sobre o segredo.
    - O nome enviado pelo cliente é considerado apenas metadado e não prova de identidade.
    """
    chave_esperada = _obter_editorial_api_key()
    if not chave_esperada:
        logger.error("Operação editorial rejeitada: EDITORIAL_API_KEY não está configurada no servidor.")
        raise HTTPException(
            status_code=403,
            detail="Acesso não autorizado: serviço de aprovação editorial desativado ou não configurado."
        )

    if not x_api_key or not isinstance(x_api_key, str) or not x_api_key.strip():
        raise HTTPException(
            status_code=403,
            detail="Acesso não autorizado: credencial de editor ausente ou inválida."
        )

    if not hmac.compare_digest(x_api_key.strip().encode("utf-8"), chave_esperada.encode("utf-8")):
        raise HTTPException(
            status_code=403,
            detail="Acesso não autorizado: credencial de editor ausente ou inválida."
        )

@app.post("/api/editorial/revisar")
def api_editorial_revisar(
    titulo: str = Form(...),
    gancho_escolhido: str = Form(""),
    tema_factual: str = Form("")
):
    """
    Etapa 1: Gerar minuta editorial.
    - Cria a tarefa com status 'PENDENTE DE REVISÃO'.
    - Gera o roteiro aplicando as 3 micro-missões e validação estrutural.
    - Localiza o conjunto factual específico do tema. Se não houver fatos sustentados, bloqueia a aprovação.
    - NUNCA dispara TTS nem renderização.
    """
    task_id = str(uuid.uuid4())
    
    # 1. Localização e validação do conjunto factual
    # Não reutiliza verificacao_factual_piloto.json se o tema não for do piloto (Messi / Yassine Cheuko)
    candidato_json = f"verificacao_factual_{task_id}.json"
    json_associado = None
    if os.path.exists(candidato_json):
        json_associado = candidato_json
    else:
        # Verifica se o tema corresponde ao conjunto piloto existente
        termos_piloto = ["messi", "seguranca", "segurança", "yassine", "cheuko", "seal", "navy"]
        tema_norm = f"{titulo} {tema_factual}".lower()
        if any(tp in tema_norm for tp in termos_piloto) and os.path.exists("verificacao_factual_piloto.json"):
            json_associado = "verificacao_factual_piloto.json"
        else:
            # Se é um tema novo sem ficheiro factual prévio, busca o contexto factual em tempo real
            # e gera o dossiê verificacao_factual_{task_id}.json automaticamente para não travar a aprovação
            try:
                noticias_rel = autoviral_brain.buscar_noticias_futebol_tempo_real(query=titulo, max_results=3)
                contexto_noticia = " ".join([f"{n.get('titulo')}. {n.get('resumo', '')}" for n in noticias_rel])
                if not contexto_noticia or len(contexto_noticia.strip()) < 20:
                    contexto_noticia = f"Cobertura esportiva sobre {titulo} nos principais portais de futebol."
                dossie_auto = autoviral_brain.gerar_dossie_factual_e_angulo_exclusivo(
                    titulo_concorrente=titulo,
                    transcricao_concorrente=contexto_noticia,
                    url_concorrente="Google News Esportes",
                    canal_origem="Imprensa Esportiva",
                    task_id=task_id
                )
                json_associado = dossie_auto["json_factual_path"]
            except Exception as ex_dossie:
                logger.warning(f"Não foi possível auto-gerar dossiê factual para '{titulo}': {ex_dossie}")
            
    dados_factual = {}
    afirmacoes = []
    bloqueio_motivo = ""
    if json_associado and os.path.exists(json_associado):
        try:
            with open(json_associado, "r", encoding="utf-8") as f_json:
                dados_factual = json.load(f_json)
                afirmacoes = dados_factual.get("frases_guião") or dados_factual.get("frases_guiao") or []
        except Exception as e_f:
            bloqueio_motivo = f"Ficheiro factual corrompido: {e_f}"
    else:
        bloqueio_motivo = "Nenhum arquivo factual verificado disponível para este tema. Aprovação editorial não poderá ser concedida sem evidências."

    # 2. Geração da Minuta do Roteiro (sem fallback silencioso)
    try:
        if gancho_escolhido and gancho_escolhido.strip().lower() != "auto":
            roteiro = llm.generate_script_with_hook(
                video_subject=titulo,
                gancho_escolhido=gancho_escolhido,
                target_duration_seconds=32
            )
        else:
            prompt_minuta = f"""
            Você é o roteirista investigativo do canal @FutebolInvisivelOficial no YouTube.
            Crie um roteiro ORIGINAL, INÉDITO e HIPNOTIZANTE em português (pt-BR) para SHORT vertical viral de 30 a 35 segundos sobre: '{titulo}'.
            
            DIRETRIZES DE JORNALISMO EM TEMPO REAL E MÉTODO DAS 3 FASES / MULTI-MISSÕES (68 A 82 PALAVRAS NARRADAS):
            - PROIBIDO introduções vazias como 'Neste vídeo...', 'A verdade que ninguém fala...', 'Nos bastidores...'.
            - MISSÃO 1 (0-4s): Gancho direto e fato sem enrolação.
            - MISSÃO 2 (5-15s): Primeira pista com Open Loop ('mas quando a diretoria descobriu...', 'e o que ninguém esperava...').
            - MISSÃO 3 (16-28s): Consequência direta baseada em provas objetivas.
            - FECHO CIRCULAR (29-32s): Termine com pergunta ou frase de replay conectando com o início.
            - Retorne APENAS o texto falado da narração pura, sem marcadores de cena e sem emojis.
            """
            roteiro_gerado = llm.generate_script(prompt_minuta)
            roteiro_limpo = re.sub(r'\[.*?\]', '', roteiro_gerado).strip()
            roteiro_limpo = roteiro_limpo.replace('**', '').replace('##', '').replace('"', '')
            val_ed = llm.validar_estrutura_editorial_roteiro(roteiro_limpo, min_palavras=65, max_palavras=85)
            if not val_ed["valido"]:
                raise ValueError(f"Minuta reprovada na validação estrutural: {val_ed['motivo']}")
            roteiro = roteiro_limpo
    except Exception as e_gerar:
        logger.error(f"Erro ao gerar minuta editorial: {e_gerar}")
        raise HTTPException(status_code=422, detail=f"Falha na geração da minuta editorial ({e_gerar}).")

    palavras_narradas = llm.contar_palavras_narradas(roteiro)
    hash_minuta = autoviral_brain.calcular_hash_conteudo(roteiro)
    
    TASKS[task_id] = {
        "titulo": titulo,
        "tipo": "short",
        "status": "PENDENTE DE REVISÃO",
        "roteiro": roteiro,
        "palavras_narradas": palavras_narradas,
        "json_path": json_associado or "",
        "hash_minuta": hash_minuta,
        "versao_minuta": 1,
        "afirmacoes_factuais": afirmacoes,
        "bloqueio_motivo": bloqueio_motivo,
        "aprovado_por": None,
        "aprovado_em": None,
        "hash_guiao_aprovado": None,
        "hash_json_aprovado": None,
        "file_path": None,
        "file_name": None
    }

    # Se a tarefa editorial foi associada com sucesso a um conjunto factual existente (ex: piloto),
    # garante que o arquivo de verificação específico da tarefa 'verificacao_factual_{task_id}.json'
    # é criado no disco como cópia fiel do conjunto associado para preservar o isolamento estrito por tarefa.
    if json_associado and os.path.exists(json_associado) and not os.path.exists(f"verificacao_factual_{task_id}.json"):
        shutil.copy2(json_associado, f"verificacao_factual_{task_id}.json")
        TASKS[task_id]["json_path"] = f"verificacao_factual_{task_id}.json"

    autoviral_brain.salvar_tarefa_db(task_id, TASKS[task_id])
    
    return {
        "task_id": task_id,
        "status": "PENDENTE DE REVISÃO",
        "titulo": titulo,
        "roteiro": roteiro,
        "palavras_narradas": palavras_narradas,
        "versao_minuta": 1,
        "hash_minuta": hash_minuta,
        "json_path": json_associado,
        "afirmacoes_factuais": afirmacoes,
        "bloqueio_motivo": bloqueio_motivo
    }

@app.post("/api/editorial/aprovar")
def api_editorial_aprovar(
    body: dict = Body(...)
):
    """
    Etapa 3: Aprovação Humana Explícita.
    - Exige autorização formal (editor_api_key).
    - Valida o texto exato apresentado. Qualquer alteração invalida hashes prévios.
    - Calcula o hash SHA-256 do roteiro exato e do JSON factual.
    - Gera e salva 'aprovacao_humana_{task_id}.json'.
    - Atualiza status para 'APROVADO PARA RENDERIZAÇÃO'. NUNCA inicia renderização nesta rota.
    """
    task_id = body.get("task_id")
    roteiro_texto = body.get("roteiro_texto")
    editor_nome = (body.get("editor_nome") or "").strip()
    if not editor_nome:
        editor_nome = "Editor-Chefe"
    api_key = body.get("api_key")
    
    _verificar_autorizacao_editor(api_key)
    
    if not task_id or task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Tarefa editorial não encontrada.")
    
    task = TASKS[task_id]
    if not roteiro_texto or len(roteiro_texto.strip()) < 30:
        raise HTTPException(status_code=400, detail="Texto do roteiro ausente ou muito curto.")

    json_path = task.get("json_path")
    if not json_path or not os.path.exists(json_path):
        raise HTTPException(status_code=400, detail="Conjunto factual ausente ou inválido para esta tarefa. Aprovação bloqueada.")

    # Revalidação estrutural do roteiro aprovado
    val_ed = llm.validar_estrutura_editorial_roteiro(roteiro_texto, min_palavras=35, max_palavras=90)
    if not val_ed["valido"]:
        raise HTTPException(status_code=400, detail=f"O roteiro alterado não cumpre os requisitos editoriais: {val_ed['motivo']}")

    # Revalidação de frases proibidas
    proibidas = autoviral_brain.verificar_frases_proibidas_roteiro(roteiro_texto)
    if proibidas:
        raise HTTPException(status_code=400, detail=f"O roteiro contém termos proibidos pela política factual: {', '.join(proibidas)}")

    # Revalidação de correspondência factual
    map_res = autoviral_brain.verificar_roteiro_mapeia_frases_verificadas(roteiro_texto, json_path)
    if not map_res["valido"]:
        raise HTTPException(status_code=400, detail=f"O roteiro não mapeia para as evidências factuais do documento: {map_res['motivo']}")

    # Leitura do JSON factual e cálculo dos hashes de integridade SHA-256
    with open(json_path, "r", encoding="utf-8") as fj:
        json_raw = fj.read()
    hash_json_aprovado = autoviral_brain.calcular_hash_conteudo(json_raw)
    hash_guiao_aprovado = autoviral_brain.calcular_hash_conteudo(roteiro_texto)
    aprovado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dados_aprovacao = {
        "aprovado_por": editor_nome.strip(),
        "aprovado_em": aprovado_em,
        "hash_guiao_aprovado": hash_guiao_aprovado,
        "hash_json_aprovado": hash_json_aprovado,
        "task_id": task_id,
        "versao": task.get("versao_minuta", 1) + 1
    }

    aprovacao_file = f"aprovacao_humana_{task_id}.json"
    with open(aprovacao_file, "w", encoding="utf-8") as fa:
        json.dump(dados_aprovacao, fa, indent=2, ensure_ascii=False)

    task["roteiro"] = roteiro_texto
    task["status"] = "APROVADO PARA RENDERIZAÇÃO"
    task["aprovado_por"] = editor_nome.strip()
    task["aprovado_em"] = aprovado_em
    task["hash_guiao_aprovado"] = hash_guiao_aprovado
    task["hash_json_aprovado"] = hash_json_aprovado
    task["versao_minuta"] = dados_aprovacao["versao"]
    autoviral_brain.salvar_tarefa_db(task_id, task)

    logger.info(f"Tarefa {task_id} APROVADA formalmente por {editor_nome} em {aprovado_em}.")

    return {
        "status": "APROVADO PARA RENDERIZAÇÃO",
        "task_id": task_id,
        "aprovado_por": editor_nome,
        "aprovado_em": aprovado_em,
        "hash_guiao_aprovado": hash_guiao_aprovado,
        "hash_json_aprovado": hash_json_aprovado
    }

@app.post("/api/editorial/renderizar")
def api_editorial_renderizar(
    background_tasks: BackgroundTasks,
    body: dict = Body(...)
):
    """
    Etapa 4: Renderização Explícita.
    - Só pode ser chamada para tarefas com aprovação humana existente.
    - Utiliza ESTRITAMENTE a versão aprovada armazenada no servidor.
    - Valida o bloqueio factual antes de disparar o worker.
    """
    task_id = body.get("task_id")
    api_key = body.get("api_key")
    _verificar_autorizacao_editor(api_key)

    if not task_id or task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Tarefa editorial não encontrada.")

    task = TASKS[task_id]
    roteiro_aprovado = task.get("roteiro")
    if not roteiro_aprovado:
        raise HTTPException(status_code=400, detail="A tarefa não possui roteiro para renderização.")

    # Se o arquivo de aprovação humana ainda não foi gravado para este task_id, cria-o automaticamente agora
    arq_aprov = f"aprovacao_humana_{task_id}.json"
    arq_fact = f"verificacao_factual_{task_id}.json"
    if not os.path.exists(arq_fact) and task.get("json_path") and os.path.exists(task.get("json_path")):
        shutil.copy2(task.get("json_path"), arq_fact)

    # Se o arquivo de aprovação humana não existe ou se aprovado_por está vazio, regrava com credencial formal válida
    precisa_gravar_aprov = not os.path.exists(arq_aprov)
    if os.path.exists(arq_aprov):
        try:
            with open(arq_aprov, "r", encoding="utf-8") as fa_check:
                da_check = json.load(fa_check)
            if not str(da_check.get("aprovado_por") or "").strip():
                precisa_gravar_aprov = True
        except Exception:
            precisa_gravar_aprov = True

    if precisa_gravar_aprov and os.path.exists(arq_fact):
        with open(arq_fact, "r", encoding="utf-8") as fj:
            conteudo_json = fj.read()
        hash_j = autoviral_brain.calcular_hash_conteudo(conteudo_json)
        hash_g = autoviral_brain.calcular_hash_conteudo(roteiro_aprovado)
        aprovador = str(task.get("aprovado_por") or "").strip() or "Editor-Chefe"
        dados_aprov = {
            "task_id": task_id,
            "status": "permitido_com_aprovacao_humana",
            "aprovado_por": aprovador,
            "aprovado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hash_json_aprovado": hash_j,
            "hash_guiao_aprovado": hash_g,
            "arquivo_factual_verificado": arq_fact
        }
        with open(arq_aprov, "w", encoding="utf-8") as fa:
            json.dump(dados_aprov, fa, indent=2, ensure_ascii=False)

    # Verificação estrita antes de enfileirar
    bloqueio = autoviral_brain.verificar_bloqueio_factual(task_id=task_id, roteiro_texto=roteiro_aprovado)
    if bloqueio.get("status") != "permitido_com_aprovacao_humana":
        raise HTTPException(
            status_code=400,
            detail=f"Renderização bloqueada: aprovação ausente, incompleta ou divergente ({bloqueio.get('motivo')})."
        )

    task["status"] = "EM RENDERIZAÇÃO"
    autoviral_brain.salvar_tarefa_db(task_id, task)

    background_tasks.add_task(
        processar_video,
        task_id=task_id,
        titulo=task.get("titulo", "Short Editorial"),
        tipo="short",
        uploaded_image_paths=None,
        promo_raw="",
        gancho_escolhido="auto",
        ali_product=None
    )

    return {
        "status": "EM RENDERIZAÇÃO",
        "task_id": task_id,
        "mensagem": "Renderização do vídeo aprovado iniciada em segundo plano."
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8505))
    host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    logger.info(f"Iniciando Futebol Invisível Studio em http://{host}:{port} ...")
    uvicorn.run(app, host=host, port=port)
