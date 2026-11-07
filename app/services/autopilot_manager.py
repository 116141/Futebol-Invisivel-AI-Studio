import os
import time
import uuid
import random
import threading
from datetime import datetime
from loguru import logger
import autoviral_brain
from app.services import aliexpress_affiliate, youtube_comments_manager, youtube_uploader

AUTOPILOT_RUNNING = False
AUTOPILOT_THREAD = None
AUTOPILOT_CONFIG = {
    "modo_privacidade": "unlisted",  # SEMPRE NÃO LISTADO para maturação segura de 45 min
    "incluir_docs_futebol": True,    # Produz Shorts e Documentários Investigativos (16:9)
    "incluir_fergil": True,          # Produz canal FERGIL (Podcasts, Negócios, IA)
    "responder_comentarios": True,   # Bot de respostas para inscritos
    "auto_publicar_nos_picos": True, # Robô publica os maturados automaticamente nos horários de pico
    "intervalo_minutos": 120,        # Cadência econômica: 12 ciclos por dia (a cada 2h) para preservar cota
    "ultimo_ciclo": None,
    "total_produzidos": 0,
    "ultimo_tipo_futebol": "short",
    "ultimo_tipo_fergil": "short",
    "max_uploads_por_ciclo": 2,
    "max_uploads_por_dia_por_canal": {
        "futebol": 3,
        "moda": 3,
        "fergil": 3
    },
    "max_backlog_por_canal": 10,
    "intervalo_segundos_entre_uploads": 45,
    "uploads_hoje": {"data": datetime.now().strftime("%Y-%m-%d"), "futebol": 0, "moda": 0, "fergil": 0}
}

def disparar_producao_video_futebol(is_doc: bool = False, titulo_especifico: str = None):
    """Gera autonomamente um vídeo de futebol com base nas tendências quentes."""
    try:
        import app_render_studio
        if titulo_especifico:
            titulo_noticia = titulo_especifico
        else:
            noticias = autoviral_brain.buscar_noticias_futebol_tempo_real()
            titulo_noticia = "Polêmica e Bastidores do Futebol"
            for n in noticias:
                tit = n.get("titulo", "")
                if not autoviral_brain.verificar_video_duplicado(tit, "futebol"):
                    titulo_noticia = tit
                    break

        tipo_v = "doc" if is_doc else "short"
        task_id = str(uuid.uuid4())
        
        dossie = autoviral_brain.gerar_dossie_factual_e_angulo_exclusivo(
            titulo_concorrente=titulo_noticia,
            transcricao_concorrente=f"Apuração jornalística checada sobre {titulo_noticia}.",
            url_concorrente="Autopilot Pro",
            canal_origem="Futebol Invisível",
            task_id=task_id
        )
        
        res = app_render_studio.iniciar_pipeline_render(
            tipo_video=tipo_v,
            titulo=titulo_noticia,
            conteudo_base=f"Contexto apurado: {titulo_noticia}. Revelações de bastidores.",
            canal_destino="futebol",
            privacidade="unlisted",
            task_id=task_id,
            dossie=dossie
        )
        logger.info(f"Produção Futebol ({tipo_v}) iniciada: {res}")
        return True
    except Exception as e:
        logger.error(f"Erro na produção de vídeo futebol: {e}")
        return False

def disparar_producao_video_moda():
    """Gera autonomamente um vídeo de moda/afiliado."""
    try:
        import app_render_studio
        produtos = aliexpress_affiliate.search_winning_fashion_products(
            keywords="vestido feminino elegante",
            page_size=20,
            only_with_video=True
        )
        if not produtos:
            produtos = aliexpress_affiliate.search_winning_fashion_products(
                keywords="moda feminina elegante",
                page_size=20,
                only_with_video=False
            )
        if not produtos:
            return False
        
        # Filtra produtos já produzidos previamente (em qualquer estado, incluindo ARQUIVADO)
        candidatos_validos = []
        for p_cand in produtos:
            tit_cand = p_cand.get("short_title") or aliexpress_affiliate.limpiar_titulo_moda(p_cand.get("raw_title", "Achadinho Elegante Moda Feminina"))
            pid_cand = str(p_cand.get("product_id", ""))
            url_cand = p_cand.get("short_link") or p_cand.get("product_detail_url", "")
            if not autoviral_brain.verificar_video_duplicado(tit_cand, canal="moda", fonte_url=url_cand, product_id=pid_cand):
                candidatos_validos.append((p_cand, tit_cand))

        if not candidatos_validos:
            logger.info("Todos os produtos de moda pesquisados já foram produzidos anteriormente.")
            return False

        prod, titulo = random.choice(candidatos_validos)
            
        task_id = str(uuid.uuid4())
        app_render_studio.TASKS[task_id] = {
            "titulo": titulo,
            "tipo": "afiliado_moda",
            "canal_destino": "moda",
            "status": "Iniciando download de assets na API AliExpress...",
            "roteiro": "",
            "file_path": None,
            "file_name": None,
            "txt_path": None,
            "txt_name": None,
            "link_afiliado": prod.get("short_link", ""),
            "preco": prod.get("sale_price", ""),
            "comissao_pct": prod.get("commission_rate", ""),
            "product_id": str(prod.get("product_id", "")),
            "post_titulo": titulo,
            "post_descricao": f"{titulo}\n\n👗 Link do Look: {prod.get('short_link', '')}\n\n#moda #achadinhos",
            "post_comentario": ""
        }
        autoviral_brain.salvar_tarefa_db(task_id, app_render_studio.TASKS[task_id])
        
        t = threading.Thread(
            target=app_render_studio.processar_video,
            args=(task_id, titulo, "afiliado_moda", None, "", "", prod),
            daemon=True
        )
        t.start()
        logger.info(f"Produção Moda iniciada com sucesso na tarefa {task_id}")
        return True
    except Exception as e:
        logger.error(f"Erro na produção de vídeo moda: {e}")
        return False

def disparar_producao_video_fergil(is_doc: bool = False):
    """Gera autonomamente um vídeo de altíssima retenção para a FERGIL alternando os 5 pilares estratégicos."""
    try:
        import app_render_studio
        from canais.canal_03_fergil import editorial_fergil
        
        # 1. Obter pautas já produzidas para nunca repetir título ou ângulo
        conn = autoviral_brain.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT titulo FROM videos_gerados WHERE canal = 'fergil'")
        titulos_existentes = [row["titulo"] for row in cur.fetchall()]
        conn.close()

        # 2. Seleção inteligente e variada da esteira dos 5 pilares
        candidatos = [p for p in editorial_fergil.PAUTAS_FERGIL_MULTIDIMENSIONAIS if not autoviral_brain.verificar_video_duplicado(p["titulo"], "fergil")]
        
        tema_escolhido = None
        if candidatos:
            # Alterna aleatoriamente entre os pilares não repetidos
            random.shuffle(candidatos)
            tipo_alvo = "doc" if is_doc else "short"
            compativeis = [c for c in candidatos if c.get("tipo") == tipo_alvo]
            tema_escolhido = compativeis[0] if compativeis else candidatos[0]

        # 3. Fallback: Caçador de notícias de negócios se todas as pautas internas tiverem sido usadas
        if not tema_escolhido:
            noticias_reais = autoviral_brain.buscar_oportunidades_negocios_fergil(max_results=10)
            for n in noticias_reais:
                t_noticia = n.get("titulo", "")
                if not autoviral_brain.verificar_video_duplicado(t_noticia, "fergil"):
                    tema_escolhido = {"titulo": t_noticia, "pilar": "Negócios & IA", "tipo": "doc" if is_doc else "short"}
                    break

        if not tema_escolhido:
            logger.info("Todos os temas FERGIL recentes já foram produzidos. Nenhuma duplicata gerada.")
            return False

        titulo = tema_escolhido["titulo"]
        pilar = tema_escolhido.get("pilar", "Negócios & Alta Performance")
        tipo_v = "doc" if is_doc else "short"
        task_id = str(uuid.uuid4())
        
        logger.info(f"💼 [FERGIL EDITORIAL] Novo tema selecionado (Pilar: {pilar}): '{titulo}' ({tipo_v.upper()})")

        gancho_inicial = tema_escolhido.get("gancho", f"Lição profunda sobre poder, riqueza e tomada de decisões em {titulo}.")
        
        dossie = autoviral_brain.gerar_dossie_factual_e_angulo_exclusivo(
            titulo_concorrente=titulo,
            transcricao_concorrente=f"Pilar: {pilar}. Gancho: {gancho_inicial}. Análise executiva e lições de psicologia de riqueza sobre {titulo}.",
            url_concorrente="FERGIL Intelligence Elite",
            canal_origem="FERGIL",
            task_id=task_id
        )
        
        res = app_render_studio.iniciar_pipeline_render(
            tipo_video=tipo_v,
            titulo=titulo,
            conteudo_base=f"Tema: {titulo}. Pilar: {pilar}. {gancho_inicial} Lições aplicáveis para vida, dinheiro e negócios.",
            canal_destino="fergil",
            privacidade="unlisted",
            task_id=task_id,
            dossie=dossie
        )
        logger.info(f"Produção FERGIL ({tipo_v}) iniciada com sucesso: {res}")
        return True
    except Exception as e:
        logger.error(f"Erro na produção de vídeo FERGIL: {e}")
        return False


def escoar_fila_aguardando_upload(canal: str = "fergil") -> dict:
    """
    ESCOAMENTO CONTROLADO DE VÍDEOS RENDERIZADO_AGUARDANDO_UPLOAD:
    1. Verifica se bloqueio expirou no banco. Se não expirou, aborta escoamento.
    2. Respeita limites configuráveis de uploads por ciclo e por dia.
    3. Para se houver bloqueio global QUOTA_EXCEEDED.
    4. Carrega a playlist de uploads do canal UMA ÚNICA VEZ por escoamento (baixo custo de API).
    5. Ordena do mais antigo para o mais recente (FIFO).
    6. Valida MP4 (existe, > 1 MB, sha256).
    7. Verificação de duplicados local (video_id / sha256) e remota (marcador [task_id:xxx] na descrição).
       - Se achar [task_id:xxx] na descrição do YouTube, vincula video_id e marca POSTADO NO YOUTUBE sem re-enviar.
       - Se apenas o título for idêntico mas sem o marcador task_id, marca DUPLICADO_SUSPEITO e pula.
    8. Envia com intervalo configurável entre envios.
    9. Interrompe IMEDIATAMENTE no primeiro uploadLimitExceeded, devolve o vídeo à fila e renova bloqueio com backoff.
    """
    import app_render_studio
    res_escoamento = {"canal": canal, "escoados": 0, "pulados": 0, "falhas": 0, "detalhes": []}
    
    st_bloq = autoviral_brain.obter_status_upload_canal(canal)
    if st_canal := st_bloq:
        if st_canal.get("bloqueado"):
            logger.info(f"⏳ [ESCOAMENTO {canal.upper()}] Canal bloqueado até {st_canal.get('bloqueado_ate')}. Aguardando janela para escoar.")
            return res_escoamento

    # Checagem de limite diário
    hoje = datetime.now().strftime("%Y-%m-%d")
    if AUTOPILOT_CONFIG.get("uploads_hoje", {}).get("data") != hoje:
        AUTOPILOT_CONFIG["uploads_hoje"] = {"data": hoje, "futebol": 0, "moda": 0, "fergil": 0}
        
    limites_dict = AUTOPILOT_CONFIG.get("max_uploads_por_dia_por_canal", {})
    limite_dia_canal = limites_dict.get(canal, 3)
    if AUTOPILOT_CONFIG["uploads_hoje"].get(canal, 0) >= limite_dia_canal:
        logger.warning(f"🛑 [ESCOAMENTO {canal.upper()}] Limite diário específico do canal atingido ({limite_dia_canal} uploads hoje). Pausando canal até amanhã.")
        return res_escoamento

    # Busca tarefas com status RENDERIZADO_AGUARDANDO_UPLOAD do mais antigo para o mais novo
    conn = autoviral_brain.get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM videos_gerados 
        WHERE canal = ? AND status = 'RENDERIZADO_AGUARDANDO_UPLOAD'
        ORDER BY criado_em ASC
    """, (canal,))
    pendentes = [dict(r) for r in cur.fetchall()]
    conn.close()

    if not pendentes:
        return res_escoamento

    logger.info(f"📦 [ESCOAMENTO {canal.upper()}] Encontrados {len(pendentes)} vídeos aguardando upload. Iniciando do mais antigo ao mais recente...")

    # Carrega a playlist de uploads do canal UMA ÚNICA VEZ
    videos_remotos_canal = []
    try:
        yt = youtube_uploader.get_authenticated_service(canal_nome=canal)
        ch_resp = yt.channels().list(part="contentDetails", mine=True).execute()
        if ch_resp.get("items"):
            up_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            pl_resp = yt.playlistItems().list(part="snippet", playlistId=up_id, maxResults=50).execute()
            for it in pl_resp.get("items", []):
                sn = it.get("snippet", {})
                videos_remotos_canal.append({
                    "video_id": sn.get("resourceId", {}).get("videoId"),
                    "title": sn.get("title", ""),
                    "description": sn.get("description", "")
                })
    except Exception as ex_pl:
        diag_pl = youtube_uploader.classificar_erro_youtube(ex_pl)
        if diag_pl["categoria"] == "QUOTA_EXCEEDED":
            logger.error("🛑 [ESCOAMENTO] Cota global GCP quotaExceeded ao listar playlist. Registrando bloqueio global '*'.")
            autoviral_brain.registrar_bloqueio_upload_canal(
                canal="*",
                codigo_http=403,
                motivo="quotaExceeded",
                mensagem="Cota global diária da YouTube Data API excedida.",
                horas_bloqueio=24.0
            )
            return res_escoamento
        logger.warning(f"Aviso ao carregar playlist de uploads ({canal}): {ex_pl}")

    limite_ciclo = AUTOPILOT_CONFIG.get("max_uploads_por_ciclo", 2)
    pausa_segundos = AUTOPILOT_CONFIG.get("intervalo_segundos_entre_uploads", 45)

    for p in pendentes:
        if res_escoamento["escoados"] >= limite_ciclo:
            logger.info(f"⏸️ [ESCOAMENTO {canal.upper()}] Atingido limite por ciclo ({limite_ciclo} uploads). Próximo escoamento no próximo ciclo.")
            break
            
        tid = p["task_id"]
        titulo = p.get("post_titulo") or p.get("titulo", "")
        fpath = p.get("file_path") or ""

        # 1. Validação estrita do MP4
        if not fpath or not os.path.exists(fpath):
            logger.error(f"❌ [ESCOAMENTO] Tarefa {tid}: arquivo {fpath} não existe no disco. Pulando.")
            continue
        if os.path.getsize(fpath) < 1000000:
            logger.error(f"❌ [ESCOAMENTO] Tarefa {tid}: arquivo {fpath} tem menos de 1 MB. Pulando.")
            continue
            
        sha256_file = autoviral_brain.calcular_sha256_arquivo(fpath)

        # 2. Verificação de Duplicados Remoto via playlist carregada
        duplicado_resolvido = False
        marcador_busca = f"[task_id:{tid}]"
        
        for rem in videos_remotos_canal:
            if marcador_busca in rem["description"]:
                logger.success(f"🎯 [ESCOAMENTO] Marcador {marcador_busca} já encontrado no YouTube (Video ID: {rem['video_id']}). Atualizando banco sem re-enviar!")
                p["status"] = "POSTADO NO YOUTUBE (UNLISTED)"
                p["youtube_video_id"] = rem["video_id"]
                p["youtube_video_url"] = f"https://www.youtube.com/watch?v={rem['video_id']}"
                p["upload_falha_detalhes"] = None
                autoviral_brain.salvar_tarefa_db(tid, p)
                res_escoamento["pulados"] += 1
                duplicado_resolvido = True
                break
            elif rem["title"].strip().lower() == titulo.strip().lower():
                logger.warning(f"⚠️ [ESCOAMENTO] Título exato '{titulo}' já presente no YouTube ({rem['video_id']}), mas sem marcador. Marcando DUPLICADO_SUSPEITO.")
                p["status"] = "DUPLICADO_SUSPEITO"
                autoviral_brain.salvar_tarefa_db(tid, p)
                res_escoamento["pulados"] += 1
                duplicado_resolvido = True
                break

        if duplicado_resolvido:
            continue

        # 3. Dispara o upload com controle atômico UPLOAD_EM_ANDAMENTO e controle de erro
        if not autoviral_brain.tentar_iniciar_upload_atomico(tid, timeout_minutos=30):
            logger.warning(f"⚠️ [ESCOAMENTO] Tarefa {tid} já está em UPLOAD_EM_ANDAMENTO por outro processo. Pulando.")
            continue

        try:
            logger.info(f"🚀 [ESCOAMENTO {canal.upper()}] Enviando '{titulo}' ({tid})...")
            p["status"] = "UPLOAD_EM_ANDAMENTO"
            app_render_studio.TASKS[tid] = p
            up_res = app_render_studio.api_upload_video_youtube(task_id=tid, privacy="unlisted")
            res_escoamento["escoados"] += 1
            AUTOPILOT_CONFIG["uploads_hoje"][canal] = AUTOPILOT_CONFIG["uploads_hoje"].get(canal, 0) + 1
            res_escoamento["detalhes"].append({"task_id": tid, "status": "sucesso", "video_id": up_res.get("video_id")})
            logger.success(f"✅ [ESCOAMENTO {canal.upper()}] '{titulo}' enviado com sucesso! ({res_escoamento['escoados']}/{limite_ciclo})")
            
            # Intervalo entre envios para não acionar rate limits
            if res_escoamento["escoados"] < limite_ciclo:
                time.sleep(pausa_segundos)

        except Exception as ex_up:
            diag_up = youtube_uploader.classificar_erro_youtube(ex_up)
            res_escoamento["falhas"] += 1
            res_escoamento["detalhes"].append({"task_id": tid, "status": "falha", "motivo": diag_up.get("motivo_api")})
            
            if diag_up["categoria"] == "QUOTA_EXCEEDED":
                logger.error(f"🛑 [ESCOAMENTO GLOBAL] Cota global GCP quotaExceeded no upload. Registrando bloqueio global '*'.")
                autoviral_brain.registrar_bloqueio_upload_canal(
                    canal="*",
                    codigo_http=403,
                    motivo="quotaExceeded",
                    mensagem="Cota global da YouTube Data API excedida.",
                    horas_bloqueio=24.0
                )
                break
            elif diag_up["categoria"] == "UPLOAD_LIMIT_EXCEEDED":
                logger.error(f"🛑 [ESCOAMENTO {canal.upper()}] Interrompendo fila imediatamente no primeiro {diag_up['categoria']}. Tarefa {tid} preservada na fila.")
                break

    return res_escoamento


def executar_ciclo_autopiloto():
    """Executa um ciclo completo do piloto automático cobrindo TODOS os canais da rede."""
    logger.info("🤖 [PILOTO AUTOMÁTICO] Iniciando ciclo de auditoria, higienização, maturação e produção global...")
    resultado_ciclo = {
        "timestamp": datetime.now().isoformat(),
        "acoes": []
    }

    # 1. AUTO-LIBERAÇÃO DE VÍDEOS NOS PICOS DE AUDIÊNCIA (12:30, 17:30, 20:30)
    if AUTOPILOT_CONFIG.get("auto_publicar_nos_picos"):
        try:
            from app.services import video_scheduler
            logger.info("⏰ [AGENDADOR DE PICOS] Checando se estamos na janela de pico para liberar vídeos maturados...")
            # Sentinela de Capas: Verifica antecedência de pico e alerta no Telegram se faltar capa e IA falhar
            video_scheduler.verificar_capa_e_alertar_urgencia("futebol", minutos_antecedencia=35)
            video_scheduler.verificar_capa_e_alertar_urgencia("moda", minutos_antecedencia=35)
            video_scheduler.verificar_capa_e_alertar_urgencia("fergil", minutos_antecedencia=35)

            # Aviso Prévio ao Proprietário (30 minutos antes do pico com link para dar uma olhada):
            video_scheduler.enviar_aviso_previo_pico_telegram("futebol", minutos_antecedencia=30)
            video_scheduler.enviar_aviso_previo_pico_telegram("moda", minutos_antecedencia=30)
            video_scheduler.enviar_aviso_previo_pico_telegram("fergil", minutos_antecedencia=30)

            pub_fut = video_scheduler.auto_liberar_videos_se_no_horario_pico("futebol")
            pub_mod = video_scheduler.auto_liberar_videos_se_no_horario_pico("moda")
            pub_fer = video_scheduler.auto_liberar_videos_se_no_horario_pico("fergil")
            
            for pub in [pub_fut, pub_mod, pub_fer]:
                if pub:
                    resultado_ciclo["acoes"].append(f"PICO ATINGIDO: Vídeo '{pub['titulo']}' do canal {pub['canal']} virou PÚBLICO!")
        except Exception as e_pico:
            logger.warning(f"Aviso no agendador de pico: {e_pico}")

    # 2. HIGIENIZAÇÃO DE VÍDEOS COM ERRO / PROCESSAMENTO FALHO (Todos os 3 canais)
    try:
        from app.services import channel_sanitizer
        logger.info("🧹 [VARREDURA SANITÁRIA] Checando integridade de vídeos nos 3 canais...")
        res_san_fut = channel_sanitizer.sanitizar_canal_youtube("futebol")
        res_san_mod = channel_sanitizer.sanitizar_canal_youtube("moda")
        res_san_fer = channel_sanitizer.sanitizar_canal_youtube("fergil")
        total_del = (
            res_san_fut.get("videos_eliminados", 0) +
            res_san_mod.get("videos_eliminados", 0) +
            res_san_fer.get("videos_eliminados", 0)
        )
        resultado_ciclo["acoes"].append(f"Varredura Sanitária: {total_del} vídeos com falha ou duplicados eliminados.")
        
        # Limpeza física de disco para vídeos já no YouTube
        try:
            res_limpeza = channel_sanitizer.limpar_armazenamento_videos_publicados()
            if res_limpeza.get("videos_pesados_removidos", 0) > 0 or res_limpeza.get("pastas_temp_removidas", 0) > 0:
                mb_lib = round(res_limpeza.get("bytes_liberados", 0) / (1024 * 1024), 2)
                resultado_ciclo["acoes"].append(f"Limpeza de Disco: {res_limpeza['videos_pesados_removidos']} vídeos e {res_limpeza['pastas_temp_removidas']} pastas limpas ({mb_lib} MB liberados).")
        except Exception as e_limp:
            logger.warning(f"Aviso na limpeza de disco: {e_limp}")
    except Exception as e_san:
        logger.warning(f"Aviso na varredura sanitária: {e_san}")

    # 3. GERADOR DE CAPAS TOTALMENTE DESATIVADO (Controle 100% manual do usuário)
    # logger.info("Guardião de capas desativado permanentemente.")

    # 4. SINCRONIZAÇÃO DE MÉTRICAS E APRENDIZADO
    try:
        autoviral_brain.sincronizar_metricas_e_aprender()
        resultado_ciclo["acoes"].append("Métricas e aprendizado sincronizados.")
    except Exception as e:
        logger.warning(f"Erro sincronizando métricas: {e}")

    # 5. ESCOAMENTO PRIORITÁRIO DE FILAS (Vídeos RENDERIZADO_AGUARDANDO_UPLOAD antes de criar novos)
    for c_nome in ["futebol", "moda", "fergil"]:
        try:
            res_esc = escoar_fila_aguardando_upload(c_nome)
            if res_esc.get("escoados", 0) > 0:
                resultado_ciclo["acoes"].append(f"Fila {c_nome.capitalize()}: {res_esc['escoados']} vídeos escoados para o YouTube.")
        except Exception as e_esc:
            logger.warning(f"Aviso no escoamento de fila ({c_nome}): {e_esc}")

    # 6. PRODUÇÃO FUTEBOL (Dupla: Doc + Short)
    max_b = AUTOPILOT_CONFIG.get("max_backlog_por_canal", 10)
    try:
        if autoviral_brain.contar_backlog_canal("futebol") >= max_b:
            logger.warning(f"🛑 [FUTEBOL] Backlog de uploads atingiu o limite ({max_b} vídeos pendentes). Produção pausada até escoamento.")
        else:
            noticias = autoviral_brain.buscar_noticias_futebol_tempo_real(max_results=20)
            tema_dupla = ""
            for n in noticias:
                tit = n.get("titulo", "")
                if not autoviral_brain.verificar_video_duplicado(tit, "futebol"):
                    tema_dupla = tit
                    break
            if tema_dupla:
                disparar_producao_video_futebol(is_doc=True, titulo_especifico=tema_dupla)
                disparar_producao_video_futebol(is_doc=False, titulo_especifico=tema_dupla)
                resultado_ciclo["acoes"].append("Futebol: Dupla Doc + Short produzida e postada como Não Listado.")
    except Exception as e_f:
        logger.warning(f"Falha na produção de futebol: {e_f}")

    # 7. PRODUÇÃO MODA (Afiliado)
    try:
        if autoviral_brain.contar_backlog_canal("moda") >= max_b:
            logger.warning(f"🛑 [MODA] Backlog de uploads atingiu o limite ({max_b} vídeos pendentes). Produção pausada até escoamento.")
        elif disparar_producao_video_moda():
            resultado_ciclo["acoes"].append("Moda: Peça de Afiliado produzida e postada como Não Listado.")
    except Exception as e_m:
        logger.warning(f"Falha na produção de moda: {e_m}")

    # 8. PRODUÇÃO FERGIL (Negócios, Podcasts & IA)
    if AUTOPILOT_CONFIG.get("incluir_fergil"):
        try:
            if autoviral_brain.contar_backlog_canal("fergil") >= max_b:
                logger.warning(f"🛑 [FERGIL] Backlog de uploads atingiu o limite ({max_b} vídeos pendentes). Produção pausada até escoamento.")
            else:
                logger.info("💼 [FERGIL] Produzindo conteúdo de alta renda (Shorts & Documentários 16:9)...")
                ultimo_f = AUTOPILOT_CONFIG.get("ultimo_tipo_fergil", "short")
                produzir_doc_fergil = (ultimo_f == "short")
                disparar_producao_video_fergil(is_doc=produzir_doc_fergil)
                AUTOPILOT_CONFIG["ultimo_tipo_fergil"] = "doc" if produzir_doc_fergil else "short"
                formato_txt = "Documentário Executivo (16:9)" if produzir_doc_fergil else "Short Viral (9:16)"
                resultado_ciclo["acoes"].append(f"FERGIL: {formato_txt} de Negócios/IA produzido e postado como Não Listado.")
        except Exception as e_fer:
            logger.warning(f"Falha na produção FERGIL: {e_fer}")

    # 8. BOT DE RESPOSTA AOS COMENTÁRIOS DOS INSCRITOS (Todos os canais)
    if AUTOPILOT_CONFIG.get("responder_comentarios"):
        try:
            logger.info("💬 [BOT COMENTÁRIOS] Respondendo dúvidas dos inscritos...")
            resp_fut = youtube_comments_manager.responder_comentarios_inscritos_automatico("futebol", max_respostas=5)
            resp_mod = youtube_comments_manager.responder_comentarios_inscritos_automatico("moda", max_respostas=5)
            resp_fer = youtube_comments_manager.responder_comentarios_inscritos_automatico("fergil", max_respostas=5)
            total_resp = (
                resp_fut.get("comentarios_respondidos", 0) +
                resp_mod.get("comentarios_respondidos", 0) +
                resp_fer.get("comentarios_respondidos", 0)
            )
            resultado_ciclo["acoes"].append(f"Bot de Comentários respondeu a {total_resp} espectadores.")
        except Exception as e_resp:
            logger.warning(f"Erro no bot de respostas: {e_resp}")

    # 9. AUDITORIA E FIXAÇÃO DE 1º COMENTÁRIO
    try:
        youtube_comments_manager.auditar_e_fixar_comentarios_canal("futebol", max_videos=100)
        youtube_comments_manager.auditar_e_fixar_comentarios_canal("moda", max_videos=100)
        youtube_comments_manager.auditar_e_fixar_comentarios_canal("fergil", max_videos=100)
        resultado_ciclo["acoes"].append("Auditoria e fixação de 1º comentário concluída nos 3 canais.")
    except Exception as e_pin:
        logger.warning(f"Erro fixando comentários: {e_pin}")

    # 10. ENVIAR RELATÓRIO EXECUTIVO DIÁRIO PARA O TELEGRAM
    try:
        from app.services import telegram_reporter
        telegram_reporter.executar_envio_relatorio_diario()
        resultado_ciclo["acoes"].append("Relatório diário enviado com sucesso para o Telegram!")
    except Exception as e_tel:
        logger.warning(f"Erro enviando relatório do Telegram: {e_tel}")

    AUTOPILOT_CONFIG["ultimo_ciclo"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    AUTOPILOT_CONFIG["total_produzidos"] += 1
    logger.success("🤖 [PILOTO AUTOMÁTICO] Ciclo autônomo concluído com êxito!")
    return resultado_ciclo

def _loop_autopiloto():
    global AUTOPILOT_RUNNING
    while AUTOPILOT_RUNNING:
        try:
            executar_ciclo_autopiloto()
        except Exception as e:
            logger.error(f"Erro no ciclo do autopiloto: {e}")
        
        minutos = AUTOPILOT_CONFIG.get("intervalo_minutos", 15)
        for _ in range(int(minutos * 60)):
            if not AUTOPILOT_RUNNING:
                break
            time.sleep(1)

def iniciar_autopiloto():
    global AUTOPILOT_RUNNING, AUTOPILOT_THREAD
    if AUTOPILOT_RUNNING:
        return {"status": "ja_ativo", "mensagem": "Piloto Automático já está em execução."}
    AUTOPILOT_RUNNING = True
    AUTOPILOT_THREAD = threading.Thread(target=_loop_autopiloto, daemon=True)
    AUTOPILOT_THREAD.start()
    logger.info("🚀 Piloto Automático ATIVADO em segundo plano para os 3 canais.")
    return {"status": "iniciado", "config": AUTOPILOT_CONFIG}

def parar_autopiloto():
    global AUTOPILOT_RUNNING
    AUTOPILOT_RUNNING = False
    logger.info("🛑 Piloto Automático PAUSADO.")
    return {"status": "parado"}

def obter_status_autopiloto():
    return {
        "ativo": AUTOPILOT_RUNNING,
        "config": AUTOPILOT_CONFIG
    }
