import os

with open("app/services/video_scheduler.py", "rb") as f:
    text = f.read().decode("utf-8")

# Let's inspect the auto_liberar_videos_se_no_horario_pico function
old_block = '''def auto_liberar_videos_se_no_horario_pico(canal: str = "futebol", tolerancia_minutos: int = 25) -> Optional[Dict]:
    """
    Verifica se a hora atual de Cabo Verde coincide com os picos estratégicos (2 Docs + 3 Shorts).
    Garante que só libera se definition == 'hd' e minutos >= 45.
    """
    agora = datetime.now()
    hora_atual = agora.hour
    minuto_atual = agora.minute
    minutos_do_dia = hora_atual * 60 + minuto_atual
    
    slot_atingido = None
    for slot in HORARIOS_PICOS_CABO_VERDE:
        minutos_slot = slot["hora"] * 60 + slot["minuto"]
        if abs(minutos_do_dia - minutos_slot) <= tolerancia_minutos:
            slot_atingido = slot
            break
            
    if not slot_atingido:
        logger.info(f"[{canal.upper()}] Hora atual CV ({hora_atual:02d}:{minuto_atual:02d}) fora de pico.")
        return None
        
    logger.info(f"⏰ [{canal.upper()}] PICO ATINGIDO EM CABO VERDE: {slot_atingido['hora']:02d}:{slot_atingido['minuto']:02d} ({slot_atingido['rotulo']})!")
    dados_esteira = auditar_esteira_e_maturacao(canal)
    prontos = dados_esteira.get("prontos_para_publicar", [])
    
    if not prontos:
        logger.warning(f"[{canal.upper()}] Janela de pico aberta, mas nenhum vídeo completou maturação HD de 45 min.")
        return None
        
    tipo_alvo = slot_atingido.get("tipo_preferido", "short")
    video_escolhido = None
    
    # Busca exatamente o tipo desejado pelo horário (doc no horário de doc, short no horário de short)
    for p in prontos:
        if (tipo_alvo == "doc" and p["is_doc"]) or (tipo_alvo == "short" and not p["is_doc"]):
            video_escolhido = p
            break
            
    if not video_escolhido:
        video_escolhido = prontos[0]
        
    vid_id = video_escolhido["id"]
    logger.info(f"🚀 LIBERANDO VÍDEO NO PICO: '{video_escolhido['titulo']}' (ID: {vid_id}, Tipo: {slot_atingido['tipo_preferido'].upper()}, Res: {video_escolhido['resolucao']}) para PÚBLICO!")
    
    sucesso = publicar_video_no_youtube(vid_id, canal=canal)
    if sucesso:
        try:
            msg_telegram = (
                f"🚀 *VÍDEO PUBLICADO NO PICO DE AUDIÊNCIA!*\n\n"
                f"📺 *Canal:* `{canal.upper()}`\n"
                f"⏰ *Horário Cabo Verde:* `{slot_atingido['hora']:02d}:{slot_atingido['minuto']:02d}`\n"
                f"🎯 *Formato:* `{'DOCUMENTÁRIO INVESTIGATIVO (16:9)' if video_escolhido['is_doc'] else 'SHORT VERTICAL (9:16)'}`\n"
                f"🌍 *Momento da Audiência:* `{slot_atingido['rotulo']}`\n"
                f"🎬 *Título:* _{video_escolhido['titulo']}_\n"
                f"✨ *Qualidade:* `{video_escolhido['resolucao']}` (HD nativo garantido)\n"
                f"⏳ *Tempo de Maturação:* `{video_escolhido['minutos_maturacao']} min em esteira`\n"
                f"🔗 *Link:* https://youtu.be/{vid_id}\n\n"
                f"🟢 _O algoritmo já possui HD e legendas indexadas para entrega máxima!_"
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
        
    return None'''

new_block = '''def auto_liberar_videos_se_no_horario_pico(canal: str = "futebol", tolerancia_minutos: int = 25) -> Optional[Dict]:
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
                f"🚀 *VÍDEO PUBLICADO NO PICO DE AUDIÊNCIA!*\n\n"
                f"📺 *Canal:* `{canal.upper()}`\n"
                f"⏰ *Horário Cabo Verde:* `{slot_atingido['hora']:02d}:{slot_atingido['minuto']:02d}`\n"
                f"🎯 *Formato:* `{'DOCUMENTÁRIO INVESTIGATIVO (16:9)' if video_escolhido['is_doc'] else 'SHORT VERTICAL (9:16)'}`\n"
                f"🌍 *Momento da Audiência:* `{slot_atingido['rotulo']}`\n"
                f"🎬 *Título:* _{video_escolhido['titulo']}_\n"
                f"✨ *Qualidade:* `{video_escolhido['resolucao']}` (HD nativo garantido)\n"
                f"⏳ *Tempo de Maturação:* `{video_escolhido['minutos_maturacao']} min em esteira`\n"
                f"🔗 *Link:* https://youtu.be/{vid_id}\n\n"
                f"🟢 _O algoritmo já possui HD e legendas indexadas para entrega máxima!_"
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
        
    return None'''

# Normalize newlines
text_clean = text.replace("\r\n", "\n")
old_block_clean = old_block.replace("\r\n", "\n")
new_block_clean = new_block.replace("\r\n", "\n")

if old_block_clean in text_clean:
    updated = text_clean.replace(old_block_clean, new_block_clean)
    with open("app/services/video_scheduler.py", "wb") as f:
        f.write(updated.encode("utf-8"))
    print("SUCCESS: video_scheduler.py patched!")
else:
    print("FAILED: old block not matched")
