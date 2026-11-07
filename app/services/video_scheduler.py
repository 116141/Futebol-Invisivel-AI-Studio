import os
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from loguru import logger
import autoviral_brain
from app.services import youtube_uploader, telegram_reporter

# FUSO HORÁRIO DE CABO VERDE (CVT = UTC-1)
# Nossos maiores públicos: Brasil (UTC-3: São Paulo/Rio) e Portugal (WET/UTC+0 / WEST/UTC+1).
# 
# ESTRATÉGIA DE ALTA PERFORMANCE (2 DOCUMENTÁRIOS + 3 A 4 SHORTS):
# 1. 11:30 (CV) -> 09:30 BR / 12:30 PT: 1º Short da manhã (Abertura de dia)
# 2. 14:30 (CV) -> 12:30 BR / 15:30 PT: 1º DOCUMENTÁRIO (Almoço Brasil / Tarde Portugal)
# 3. 17:30 (CV) -> 15:30 BR / 18:30 PT: 2º Short da tarde (Aquecimento)
# 4. 20:00 (CV) -> 18:00 BR / 21:00 PT: 3º Short do início da noite (Volta do trabalho)
# 5. 22:30 (CV) -> 20:30 BR / 23:30 PT: 2º DOCUMENTÁRIO (Horário Nobre / Prime Time Brasil)
HORARIOS_PICOS_CABO_VERDE = [
    {"hora": 11, "minuto": 30, "tipo_preferido": "short", "rotulo": "Manhã BR (09:30) / Almoço PT (12:30) - Short"},
    {"hora": 14, "minuto": 30, "tipo_preferido": "doc",   "rotulo": "1º DOCUMENTÁRIO: Almoço BR (12:30) / Tarde PT (15:30)"},
    {"hora": 17, "minuto": 30, "tipo_preferido": "short", "rotulo": "Tarde BR (15:30) / Saída PT (18:30) - Short"},
    {"hora": 20, "minuto": 0,  "tipo_preferido": "short", "rotulo": "Saída BR (18:00) / Prime PT (21:00) - Short"},
    {"hora": 22, "minuto": 30, "tipo_preferido": "doc",   "rotulo": "2º DOCUMENTÁRIO: Horário Nobre Brasil (20:30)"}
]

TEMPO_MINIMO_MATURACAO_MINUTOS = 45  # Tempo ideal para o YouTube processar HD, Content ID e legendas

def auditar_esteira_e_maturacao(canal: str = "futebol", force_refresh: bool = False) -> Dict:
    import time
    now_ts = time.time()
    if not hasattr(auditar_esteira_e_maturacao, '_cache'):
        auditar_esteira_e_maturacao._cache = {}
        auditar_esteira_e_maturacao._cache_ts = {}
        
    # Se ja temos em cache ha menos de 45 minutos e nao foi forcado, retorna cache para economizar cota da API
    if not force_refresh and canal in auditar_esteira_e_maturacao._cache:
        if now_ts - auditar_esteira_e_maturacao._cache_ts.get(canal, 0) < 2700:
            return auditar_esteira_e_maturacao._cache[canal]
    """
    Inspeciona a 'esteira' de vídeos não listados no canal.
    Verifica diretamente na API do YouTube:
    1. Se o uploadStatus é 'processed' (processamento completo).
    2. Se processingStatus é 'succeeded'.
    3. Se o stream HD está confirmado pelo YouTube (definition == 'hd').
    4. Tempo decorrido desde o upload (Maturidade >= 45 min).
    """
    resultado = {
        "canal": canal,
        "total_nao_listados": 0,
        "em_processamento": 0,
        "prontos_para_publicar": [],
        "aguardando_maturacao": [],
        "sugestao_agendamento": []
    }
    
    try:
        yt = youtube_uploader.get_authenticated_service(canal)
        res_canal = yt.channels().list(part="contentDetails", mine=True).execute()
        if not res_canal.get("items"):
            return resultado
            
        uploads_id = res_canal["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        req = yt.playlistItems().list(part="snippet,contentDetails", playlistId=uploads_id, maxResults=50)
        res_pl = req.execute()
        itens = res_pl.get("items", [])
        
        if not itens:
            return resultado
            
        video_ids = [it["contentDetails"]["videoId"] for it in itens]
        
        v_detalhes = {}
        for i in range(0, len(video_ids), 50):
            lote = video_ids[i:i+50]
            req_v = yt.videos().list(part="status,snippet,contentDetails,processingDetails", id=",".join(lote))
            res_v = req_v.execute()
            for v in res_v.get("items", []):
                v_detalhes[v["id"]] = v
                
        agora = datetime.now(timezone.utc)
        
        for it in itens:
            vid_id = it["contentDetails"]["videoId"]
            v_info = v_detalhes.get(vid_id)
            if not v_info:
                continue
                
            status_obj = v_info.get("status", {})
            privacy = status_obj.get("privacyStatus", "")
            upload_status = status_obj.get("uploadStatus", "")
            
            if privacy != "unlisted":
                continue
                
            resultado["total_nao_listados"] += 1
            
            titulo = v_info.get("snippet", {}).get("title", "")
            published_at_str = v_info.get("snippet", {}).get("publishedAt", "")
            
            minutos_no_youtube = 0
            if published_at_str:
                try:
                    dt_pub = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                    minutos_no_youtube = int((agora - dt_pub).total_seconds() / 60)
                except Exception:
                    pass
                    
            proc_details = v_info.get("processingDetails", {})
            proc_status = proc_details.get("processingStatus", "")
            
            content_details = v_info.get("contentDetails", {})
            definition = content_details.get("definition", "sd")
            duration_iso = content_details.get("duration", "")
            is_doc = ("documentário" in titulo.lower() or "dossiê" in titulo.lower() or ("PT" in duration_iso and "M" in duration_iso))
            
            item_esteira = {
                "id": vid_id,
                "titulo": titulo,
                "is_doc": is_doc,
                "resolucao": "1080p HD" if definition == "hd" else "SD (Processando)",
                "minutos_maturacao": minutos_no_youtube,
                "upload_status": upload_status,
                "processing_status": proc_status,
                "url": f"https://youtu.be/{vid_id}"
            }
            
            if upload_status == "processed" and (proc_status == "succeeded" or not proc_status) and definition == "hd":
                if minutos_no_youtube >= TEMPO_MINIMO_MATURACAO_MINUTOS:
                    item_esteira["status_algoritmo"] = "🟢 100% HD Maturado & Indexado (Pronto para Publicar)"
                    resultado["prontos_para_publicar"].append(item_esteira)
                else:
                    item_esteira["status_algoritmo"] = f"⏳ HD Pronto, Aguardando Indexação ({minutos_no_youtube}/45 min)"
                    resultado["aguardando_maturacao"].append(item_esteira)

            else:
                item_esteira["status_algoritmo"] = f"⚙️ Renderizando HD nos Servidores do YouTube ({definition.upper()})"
                resultado["em_processamento"] += 1

        # CRITÉRIO ANTI-ESQUECIMENTO (FIFO - First In, First Out):
        # Ordena a lista de prontos pelo tempo de espera (minutos_maturacao decrescente).
        # Quem está esperando há mais tempo na esteira tem prioridade absoluta para ir ao ar no pico!
        resultado["prontos_para_publicar"].sort(key=lambda x: x.get("minutos_maturacao", 0), reverse=True)

        horarios_disponiveis = list(HORARIOS_PICOS_CABO_VERDE)
        for idx, p in enumerate(resultado["prontos_para_publicar"][:5]):
            slot = horarios_disponiveis[idx % len(horarios_disponiveis)]
            resultado["sugestao_agendamento"].append({
                "video_id": p["id"],
                "titulo": p["titulo"][:45],
                "tipo": "Documentário" if p["is_doc"] else "Short",
                "horario_cabo_verde": f"{slot['hora']:02d}:{slot['minuto']:02d}",
                "publico_alvo": slot["rotulo"]
            })
            
        return resultado
        
    except Exception as e:
        logger.error(f"Erro auditando esteira de maturação: {e}")
        resultado["erro"] = str(e)
        return resultado

def publicar_video_no_youtube(video_id: str, canal: str = "futebol") -> bool:
    """Altera o status de um vídeo maturado de 'unlisted' para 'public'."""
    try:
        yt = youtube_uploader.get_authenticated_service(canal)
        res = yt.videos().update(
            part="status",
            body={
                "id": video_id,
                "status": {
                    "privacyStatus": "public"
                }
            }
        ).execute()
        logger.success(f"Vídeo {video_id} publicado com sucesso no canal {canal}!")
        return True
    except Exception as e:
        logger.error(f"Erro ao publicar vídeo {video_id}: {e}")
        return False

def auto_liberar_videos_se_no_horario_pico(canal: str = "futebol", tolerancia_minutos: int = 25) -> Optional[Dict]:
    """
    Verifica se a hora atual de Cabo Verde coincide com os picos estratégicos (2 Docs + 3 Shorts).
    Garante:
    1. EXCLUSIVAMENTE nos horários de pico (tolerância máxima configurada).
    2. No MÁXIMO 1 liberação por slot de pico por canal por dia (slot tracking rigoroso).
    3. Strict FIFO: o vídeo unlisted mais antigo na esteira (maior minutos_maturacao) tem prioridade.
    4. Garantia de HD nativo (definition == 'hd') e maturação mínima (>= 45 min).
    """
    # Cabo Verde é UTC-1 (sem horário de verão)
    tz_cv = timezone(timedelta(hours=-1))
    agora_cv = datetime.now(tz_cv)
    hora_atual = agora_cv.hour
    minuto_atual = agora_cv.minute
    minutos_do_dia = hora_atual * 60 + minuto_atual
    data_hoje_cv = agora_cv.strftime("%Y-%m-%d")
    
    slot_atingido = None
    for slot in HORARIOS_PICOS_CABO_VERDE:
        minutos_slot = slot["hora"] * 60 + slot["minuto"]
        if abs(minutos_do_dia - minutos_slot) <= tolerancia_minutos:
            slot_atingido = slot
            break
            
    if not slot_atingido:
        logger.info(f"[{canal.upper()}] Hora atual CV ({hora_atual:02d}:{minuto_atual:02d}) fora de horário de pico. Nenhuma liberação permitida.")
        return None

    slot_id = f"{slot_atingido['hora']:02d}_{slot_atingido['minuto']:02d}"
    
    # TRAVA INEGOCIÁVEL 1: No máximo 1 liberação por janela de pico por canal por dia
    if autoviral_brain.slot_pico_ja_executado(canal, slot_id, data_hoje_cv):
        logger.info(f"[{canal.upper()}] Slot de pico {slot_id} já executado hoje ({data_hoje_cv}). Liberação única cumprida, ignorando.")
        return None
        
    logger.info(f"⏰ [{canal.upper()}] PICO ATINGIDO EM CABO VERDE: {slot_atingido['hora']:02d}:{slot_atingido['minuto']:02d} ({slot_atingido['rotulo']})!")
    dados_esteira = auditar_esteira_e_maturacao(canal)
    prontos = dados_esteira.get("prontos_para_publicar", [])
    
    if not prontos:
        logger.warning(f"[{canal.upper()}] Janela de pico aberta, mas nenhum vídeo completou maturação HD de 45 min.")
        return None
        
    # TRAVA INEGOCIÁVEL 2: Strict FIFO (Mais antigo primeiro)
    # auditar_esteira_e_maturacao já ordena por minutos_maturacao descendente (o mais antigo primeiro)
    # Se houver preferência de tipo (doc vs short), filtramos mantendo a ordem estrita FIFO
    tipo_alvo = slot_atingido.get("tipo_preferido", "short")
    video_escolhido = None
    
    for p in prontos:
        if (tipo_alvo == "doc" and p["is_doc"]) or (tipo_alvo == "short" and not p["is_doc"]):
            video_escolhido = p
            break
            
    if not video_escolhido:
        video_escolhido = prontos[0]
        
    vid_id = video_escolhido["id"]
    logger.info(f"🚀 LIBERANDO VÍDEO NO PICO (FIFO): '{video_escolhido['titulo']}' (ID: {vid_id}, Tipo: {slot_atingido['tipo_preferido'].upper()}, Res: {video_escolhido['resolucao']}, Espera: {video_escolhido['minutos_maturacao']} min) para PÚBLICO!")
    
    sucesso = publicar_video_no_youtube(vid_id, canal=canal)
    if sucesso:
        # Registrar o slot como executado no banco para nunca disparar em duplicado
        autoviral_brain.registrar_publicacao_pico(canal, slot_id, data_hoje_cv, vid_id)
        logger.success(f"🔒 [{canal.upper()}] Slot de pico {slot_id} registrado como concluído com sucesso para o vídeo {vid_id}.")
        try:
            msg_telegram = (
                "🚀 *VÍDEO PUBLICADO NO PICO DE AUDIÊNCIA!*\n\n"
                f"📺 *Canal:* `{canal.upper()}`\n"
                f"⏰ *Horário Cabo Verde:* `{slot_atingido['hora']:02d}:{slot_atingido['minuto']:02d}`\n"
                f"🎯 *Formato:* `{'DOCUMENTÁRIO INVESTIGATIVO (16:9)' if video_escolhido['is_doc'] else 'SHORT VERTICAL (9:16)'}`\n"
                f"🌍 *Momento da Audiência:* `{slot_atingido['rotulo']}`\n"
                f"🎬 *Título:* _{video_escolhido['titulo']}_\n"
                f"✨ *Qualidade:* `{video_escolhido['resolucao']}` (HD nativo garantido)\n"
                f"⏳ *Tempo de Maturação:* `{video_escolhido['minutos_maturacao']} min em esteira`\n"
                f"🔗 *Link:* https://youtu.be/{vid_id}\n\n"
                "🟢 _O algoritmo já possui HD e legendas indexadas para entrega máxima!_"
            )
            telegram_reporter.enviar_mensagem_telegram(msg_telegram)
        except Exception:
            pass
            
        return {
            "status": "publicado",
            "canal": canal,
            "video_id": vid_id,
            "titulo": video_escolhido["titulo"],
            "horario_cv": f"{slot_atingido['hora']:02d}:{slot_atingido['minuto']:02d}",
            "rotulo": slot_atingido["rotulo"]
        }
        
    return None

def verificar_capa_e_alertar_urgencia(canal: str = "futebol", minutos_antecedencia: int = 35) -> None:
    """
    SENTINELA DE CAPAS & HORÁRIO DE PICO:
    Se um vídeo já está 100% maturado (HD nativo + processado) e faltam poucos minutos para o horário de pico,
    mas ele ainda NÃO tem capa personalizada aprovada:
    1. Tenta gerar automaticamente uma capa com IA de alta qualidade.
    2. Se a IA estiver expirada ou a API der erro/limite de cota:
       Dispara um ALERTA VERMELHO DE EMERGÊNCIA no Telegram para o dono criar/subir a capa manualmente antes do pico!
    """
    try:
        from app.services import telegram_reporter, thumbnail_engine
        
        agora = datetime.now()
        minutos_agora = agora.hour * 60 + agora.minute
        
        proximo_slot = None
        minutos_ate_pico = 999
        for slot in HORARIOS_PICOS_CABO_VERDE:
            m_slot = slot["hora"] * 60 + slot["minuto"]
            diff = m_slot - minutos_agora
            if 0 < diff <= minutos_antecedencia:
                if diff < minutos_ate_pico:
                    minutos_ate_pico = diff
                    proximo_slot = slot
                    
        if not proximo_slot:
            return  # Não estamos na janela de urgência pré-pico
            
        dados_esteira = auditar_esteira_e_maturacao(canal)
        prontos = dados_esteira.get("prontos_para_publicar", [])
        if not prontos:
            return
            
        tipo_alvo = proximo_slot.get("tipo_preferido", "short")
        video_candidato = None
        for p in prontos:
            if (tipo_alvo == "doc" and p["is_doc"]) or (tipo_alvo == "short" and not p["is_doc"]):
                video_candidato = p
                break
        if not video_candidato:
            video_candidato = prontos[0]
            
        vid_id = video_candidato["id"]
        titulo = video_candidato["titulo"]
        is_doc = video_candidato.get("is_doc", False)
        
        # Checa se existe capa no disco para esse vídeo
        tem_capa_disco = False
        caminhos_teste = [
            f"canais/canal_01_futebol_invisivel/CapasShort/{titulo}.jpg",
            f"canais/canal_01_futebol_invisivel/Capas_IA_Aprovadas/doc_{vid_id}.jpg",
            f"storage/thumbnails/thumb_{canal}_{vid_id}.jpg"
        ]
        for c in caminhos_teste:
            if os.path.exists(c):
                tem_capa_disco = True
                break
                
        # Se não tem capa personalizada pronta
        if not tem_capa_disco:
            logger.warning(f"🚨 [SENTINELA DE CAPAS] Vídeo '{titulo}' ({vid_id}) no pico de {proximo_slot['hora']:02d}:{proximo_slot['minuto']:02d} CV está SEM CAPA!")
            
            sucesso_ia = False
            # Tentativa autônoma de geração com IA
            try:
                logger.info(f"🎨 Tentando gerar capa com IA para '{titulo}'...")
                res_capa = thumbnail_engine.gerar_capa_tematica_profissional(
                    video_id=vid_id,
                    titulo=titulo,
                    canal=canal,
                    is_doc=is_doc
                )
                if res_capa and os.path.exists(res_capa):
                    sucesso_ia = thumbnail_engine.aplicar_capa_no_youtube(vid_id, canal, res_capa)
            except Exception as e_ia:
                logger.error(f"Falha na geração automática de capa com IA: {e_ia}")
                sucesso_ia = False
                
            # Se a IA expirou / falhou / cota esgotada -> DISPARA ALERTA VERMELHO NO TELEGRAM!
            if not sucesso_ia:
                alerta_msg = (
                    f"🚨 *ALERTA VERMELHO DE EMERGÊNCIA — CAPA URGENTE!* 🚨\n\n"
                    f"⏰ *Faltam {minutos_ate_pico} minutos para o Horário de Pico!*\n"
                    f"📺 *Canal:* `{canal.upper()}`\n"
                    f"🎯 *Momento:* `{proximo_slot['hora']:02d}:{proximo_slot['minuto']:02d} (Cabo Verde)` — _{proximo_slot['rotulo']}_\n\n"
                    f"🎬 *Vídeo Pronto:* _{titulo}_\n"
                    f"✨ *Status:* `100% HD Maturado & Indexado`\n"
                    f"⚠️ *PROBLEMA:* *O vídeo está sem capa personalizada e a IA automática não conseguiu gerar (ou cota/token expirado)!*\n\n"
                    f"👉 *AÇÃO NECESSÁRIA AGORA:*\n"
                    f"Suba uma capa manual para este vídeo no YouTube Studio antes do horário de pico para garantir o CTR e a entrega do algoritmo!\n"
                    f"🔗 *Link Direto de Edição:* https://studio.youtube.com/video/{vid_id}/edit"
                )
                telegram_reporter.enviar_mensagem_telegram(alerta_msg)
                logger.warning(f"🔔 Alerta de capa urgente enviado com sucesso via Telegram para o canal {canal}!")
                
    except Exception as e_geral:
        logger.error(f"Erro no sentinela de capas: {e_geral}")



def enviar_aviso_previo_pico_telegram(canal: str = "futebol", minutos_antecedencia: int = 30) -> Optional[Dict]:
    """
    SENTINELA PRÉ-PICO (AVISO ANTECIPADO AO PROPRIETÁRIO):
    30 minutos antes do horário de pico, o bot audita a esteira e envia uma mensagem no Telegram:
    'Olha, no pico das 14:30 vai ser publicado este vídeo. Dê uma olhada (título, capa, link de preview).'
    Evita envios repetidos do mesmo aviso no mesmo dia.
    """
    try:
        from app.services import telegram_reporter
        
        tz_cv = timezone(timedelta(hours=-1))
        agora_cv = datetime.now(tz_cv)
        minutos_agora = agora_cv.hour * 60 + agora_cv.minute
        data_hoje_cv = agora_cv.strftime("%Y-%m-%d")
        
        proximo_slot = None
        minutos_ate_pico = 999
        for slot in HORARIOS_PICOS_CABO_VERDE:
            m_slot = slot["hora"] * 60 + slot["minuto"]
            diff = m_slot - minutos_agora
            if 0 < diff <= minutos_antecedencia:
                if diff < minutos_ate_pico:
                    minutos_ate_pico = diff
                    proximo_slot = slot
                    
        if not proximo_slot:
            return None  # Fora da janela de aviso prévio
            
        slot_id = f"{proximo_slot['hora']:02d}_{proximo_slot['minuto']:02d}"
        
        # Verifica se o vídeo desse slot já foi publicado ou se o aviso já foi registrado
        conn = autoviral_brain.get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS avisos_previos_pico_log (
                canal TEXT,
                slot_id TEXT,
                data_cv TEXT,
                video_id TEXT,
                enviado_em TEXT,
                PRIMARY KEY (canal, slot_id, data_cv)
            )
        """)
        cur.execute("""
            SELECT 1 FROM avisos_previos_pico_log
            WHERE canal = ? AND slot_id = ? AND data_cv = ?
        """, (canal, slot_id, data_hoje_cv))
        ja_avisou = cur.fetchone()
        
        # Também checa se o slot já foi publicado
        cur.execute("""
            SELECT 1 FROM publicacoes_pico_log
            WHERE canal = ? AND slot_id = ? AND data_cv = ?
        """, (canal, slot_id, data_hoje_cv))
        ja_publicou = cur.fetchone()
        conn.close()
        
        if ja_avisou or ja_publicou:
            return None
            
        dados_esteira = auditar_esteira_e_maturacao(canal)
        prontos = dados_esteira.get("prontos_para_publicar", [])
        if not prontos:
            return None
            
        tipo_alvo = proximo_slot.get("tipo_preferido", "short")
        video_escolhido = None
        for p in prontos:
            if (tipo_alvo == "doc" and p["is_doc"]) or (tipo_alvo == "short" and not p["is_doc"]):
                video_escolhido = p
                break
        if not video_escolhido:
            video_escolhido = prontos[0]
            
        vid_id = video_escolhido["id"]
        titulo = video_escolhido["titulo"]
        is_doc = video_escolhido.get("is_doc", False)
        formato_str = "DOCUMENTÁRIO (16:9)" if is_doc else "SHORT (9:16)"
        
        # Monta a mensagem executiva amigável para o proprietário dar uma olhada antes
        msg = (
            "👀 *AVISO PRÉVIO: VÍDEO AGENDADO PARA O PRÓXIMO PICO!*\n\n"
            f"Olá! Daqui a cerca de *{minutos_ate_pico} minutos* teremos pico de audiência e este vídeo está na vez para ser liberado ao público:\n\n"
            f"📺 *Canal:* `{canal.upper()}`\n"
            f"⏰ *Horário do Pico:* `{proximo_slot['hora']:02d}:{proximo_slot['minuto']:02d}` (Cabo Verde)\n"
            f"🎯 *Momento:* _{proximo_slot['rotulo']}_\n"
            f"🎬 *Formato:* `{formato_str}`\n"
            f"📌 *Título:* _{titulo}_\n"
            f"✨ *Qualidade:* `{video_escolhido.get('resolucao', '1080p HD')}`\n"
            f"⏳ *Tempo de Maturação:* `{video_escolhido.get('minutos_maturacao', 0)} min em esteira (100% Indexado)`\n\n"
            f"🔗 *Dê uma olhada antes de ir ao ar:*\n"
            f"• Preview Não-Listado: https://youtu.be/{vid_id}\n"
            f"• Edição / Capa no Studio: https://studio.youtube.com/video/{vid_id}/edit\n\n"
            "💡 _Se estiver tudo aprovado, não precisa fazer nada. O robô publicará automaticamente no horário exato do pico!_"
        )
        sucesso = telegram_reporter.enviar_mensagem_telegram(msg)
        if sucesso:
            # Registra para não reenviar aviso repetido
            conn = autoviral_brain.get_conn()
            cur = conn.cursor()
            agora_str = agora_cv.strftime("%Y-%m-%d %H:%M:%S")
            try:
                cur.execute("""
                    INSERT INTO avisos_previos_pico_log (canal, slot_id, data_cv, video_id, enviado_em)
                    VALUES (?, ?, ?, ?, ?)
                """, (canal, slot_id, data_hoje_cv, vid_id, agora_str))
                conn.commit()
            except Exception:
                pass
            finally:
                conn.close()
                
            logger.info(f"📢 [AVISO PRÉ-PICO] Notificação enviada ao proprietário via Telegram para o canal {canal} (Pico {slot_id}).")
            return {
                "canal": canal,
                "slot_id": slot_id,
                "minutos_ate_pico": minutos_ate_pico,
                "video_id": vid_id,
                "titulo": titulo
            }
            
    except Exception as e:
        logger.error(f"Erro ao enviar aviso prévio de pico: {e}")
        
    return None


def formatar_relatorio_maturacao_telegram(canal: str = "futebol") -> str:
    dados = auditar_esteira_e_maturacao(canal)
    linhas = [
        f"🎯 *ESTEIRA DE MATURAÇÃO & ALGORITMO* ({canal.upper()})",
        f"• *Vídeos na Fila (Não Listados):* `{dados['total_nao_listados']}`",
        f"• *Prontos & 100% HD Maturados:* `{len(dados['prontos_para_publicar'])}`",
        f"• *Aguardando Maturação (45 min):* `{len(dados['aguardando_maturacao'])}`\n",
        "⏰ *HORÁRIOS DE CABO VERDE (2 DOCS + 3 SHORTS):*"
    ]
    if dados["sugestao_agendamento"]:
        for sug in dados["sugestao_agendamento"]:
            linhas.append(f"  └ 🚀 *{sug['horario_cabo_verde']} (CV)* - _{sug['titulo']}_ [{sug['publico_alvo']}]")
    else:
        linhas.append("  └ Nenhum vídeo precisa de publicação imediata no momento.")
        
    linhas.extend([
        "\n💡 *Estratégia de 2 Documentários:*",
        "_1 Documentário no almoço captura quem assiste em pausas ou em Portugal; o 2º no horário nobre pega o público relaxando à noite em casa._"
    ])
    return "\n".join(linhas)

if __name__ == "__main__":
    res = auditar_esteira_e_maturacao("futebol")
    print(f"Total na esteira: {res['total_nao_listados']}")
    print(f"Prontos para publicar em HD: {len(res['prontos_para_publicar'])}")
