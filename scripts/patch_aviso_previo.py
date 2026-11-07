import os
import re

with open("app/services/video_scheduler.py", "r", encoding="utf-8") as f:
    text = f.read()

novo_aviso_func = '''
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
            f"👀 *AVISO PRÉVIO: VÍDEO AGENDADO PARA O PRÓXIMO PICO!*\n\n"
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
            f"💡 _Se estiver tudo aprovado, não precisa fazer nada. O robô publicará automaticamente no horário exato do pico!_"
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
'''

# Inserir a função no video_scheduler.py antes de formatar_relatorio_maturacao_telegram
needle = "def formatar_relatorio_maturacao_telegram(canal: str = \"futebol\") -> str:"
if needle in text:
    new_text = text.replace(needle, novo_aviso_func + "\n\n" + needle, 1)
    with open("app/services/video_scheduler.py", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("SUCCESS: video_scheduler.py patched with aviso_previo!")
else:
    print("FAILED: needle not found")
