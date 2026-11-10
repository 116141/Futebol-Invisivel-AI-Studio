class QuotaExceededException(Exception):
    pass

import os
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from loguru import logger

# Importações dos serviços existentes
try:
    from app.services import youtube_uploader, telegram_reporter
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from app.services import youtube_uploader, telegram_reporter

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/autoviral_memory.db"))

# HORÁRIOS ESTRATÉGICOS DE CABO VERDE (CVT = UTC-1)
# UTC = CVT + 1 hora
HORARIOS_PICOS_CABO_VERDE = [
    {"hora": 11, "minuto": 30, "tipo_preferido": "short", "rotulo": "Manhã BR (09:30) / Almoço PT (12:30) - Short"},
    {"hora": 14, "minuto": 30, "tipo_preferido": "doc",   "rotulo": "1º DOCUMENTÁRIO: Almoço BR (12:30) / Tarde PT (15:30)"},
    {"hora": 17, "minuto": 30, "tipo_preferido": "short", "rotulo": "Tarde BR (15:30) / Saída PT (18:30) - Short"},
    {"hora": 20, "minuto": 0,  "tipo_preferido": "short", "rotulo": "Saída BR (18:00) / Prime PT (21:00) - Short"},
    {"hora": 22, "minuto": 30, "tipo_preferido": "doc",   "rotulo": "2º DOCUMENTÁRIO: Horário Nobre Brasil (20:30)"}
]

def init_tabela_agendamentos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS agendamentos_youtube (
            video_id TEXT PRIMARY KEY,
            canal TEXT,
            tipo TEXT,
            titulo TEXT,
            slot_id TEXT,
            data_agendada TEXT,
            horario_cv TEXT,
            horario_utc_iso TEXT,
            agendado_em TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def slot_ja_ocupado(canal: str, data_cv: str, slot_id: str) -> bool:
    """Verifica se o slot já foi publicado ou já está agendado no YouTube."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 1. Verifica se já foi publicado no histórico
    cur.execute('SELECT count(*) FROM publicacoes_pico_log WHERE canal = ? AND data_cv = ? AND slot_id = ?', (canal, data_cv, slot_id))
    if cur.fetchone()[0] > 0:
        conn.close()
        return True
        
    # 2. Verifica se já está agendado
    cur.execute('SELECT count(*) FROM agendamentos_youtube WHERE canal = ? AND data_agendada = ? AND slot_id = ? AND status = "AGENDADO"', (canal, data_cv, slot_id))
    if cur.fetchone()[0] > 0:
        conn.close()
        return True
        
    conn.close()
    return False

def registrar_agendamento_db(video_id: str, canal: str, tipo: str, titulo: str, slot_id: str, data_cv: str, horario_cv: str, horario_utc_iso: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    agora_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute('''
        INSERT OR REPLACE INTO agendamentos_youtube 
        (video_id, canal, tipo, titulo, slot_id, data_agendada, horario_cv, horario_utc_iso, agendado_em, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, "AGENDADO")
    ''', (video_id, canal, tipo, titulo, slot_id, data_cv, horario_cv, horario_utc_iso, agora_iso))
    conn.commit()
    conn.close()

def auditar_e_sanitizar_metadados(snippet: dict, tipo: str, canal: str = "futebol") -> dict:
    """
    Garante compliance de SEO e regras estritas do YouTube:
    1. Título conciso sem repetições bobas e < 95 caracteres.
    2. Tags limpas (sem caracteres especiais proibidos, máximo 400 chars).
    3. Descrição inteligente higienizada (sem capítulos falsos e sem [task_id:...]).
    """
    from app.services import smart_metadata_cleaner

    titulo = snippet.get("title", "").strip()
    titulo = re.sub(r'[\<\>\|\"]', '', titulo)
    if len(titulo) > 95:
        titulo = titulo[:92] + "..."
    snippet["title"] = titulo

    descricao_original = snippet.get("description", "")
    descricao_inteligente = smart_metadata_cleaner.limpar_descricao_legada(
        descricao_original=descricao_original,
        titulo=titulo,
        canal=canal,
        tipo=tipo
    )
    if "#shorts" not in descricao_inteligente.lower() and tipo == "short":
        descricao_inteligente += "\n\n#shorts"
    snippet["description"] = descricao_inteligente

    tags = snippet.get("tags", [])
    tags_validas = []
    total_len = 0
    for t in tags:
        t_clean = re.sub(r'[\<\>\|\"]', '', t).strip()
        if t_clean and len(t_clean) <= 30 and (total_len + len(t_clean)) < 350:
            tags_validas.append(t_clean)
            total_len += len(t_clean)
    if not tags_validas:
        tags_validas = ["futebol", "shorts" if tipo == "short" else "documentario"]
    snippet["tags"] = tags_validas
    
    return snippet

def encontrar_proximos_slots_livres(canal: str, qtd_slots: int = 10) -> List[Dict]:
    """
    Calcula os slots de pico cronologicamente a partir do momento atual em Cabo Verde.
    Se o horário do dia de hoje já passou ou já está ocupado, pula para os próximos slots ou para o dia seguinte!
    """
    tz_cv = timezone(timedelta(hours=-1))
    agora_cv = datetime.now(tz_cv)
    
    slots_livres = []
    dia_offset = 0
    
    while len(slots_livres) < qtd_slots and dia_offset < 30: # até 30 dias no futuro
        data_base = (agora_cv + timedelta(days=dia_offset)).date()
        data_str = data_base.strftime("%Y-%m-%d")
        
        for slot in HORARIOS_PICOS_CABO_VERDE:
            slot_id = f"{slot['hora']:02d}_{slot['minuto']:02d}"
            horario_slot_cv = datetime(
                data_base.year, data_base.month, data_base.day,
                slot['hora'], slot['minuto'], tzinfo=tz_cv
            )
            
            # Se o slot já passou no tempo atual de hoje, ignora
            # Adiciona margem de segurança de pelo menos 15 minutos para agendamento
            if horario_slot_cv <= (agora_cv + timedelta(minutes=15)):
                continue
                
            # Verifica se já está ocupado por publicação ou agendamento
            if slot_ja_ocupado(canal, data_str, slot_id):
                continue
                
            # Horário UTC para a API do YouTube
            horario_utc = horario_slot_cv.astimezone(timezone.utc)
            # O YouTube exige o formato ISO 8601 exato com Z: YYYY-MM-DDTHH:MM:SS.sZ
            horario_utc_iso = horario_utc.strftime("%Y-%m-%dT%H:%M:00.000Z")
            
            slots_livres.append({
                "data_cv": data_str,
                "slot_id": slot_id,
                "hora_cv": f"{slot['hora']:02d}:{slot['minuto']:02d}",
                "tipo_preferido": slot["tipo_preferido"],
                "rotulo": slot["rotulo"],
                "horario_cv_dt": horario_slot_cv,
                "horario_utc_iso": horario_utc_iso
            })
            
            if len(slots_livres) >= qtd_slots:
                break
                
        dia_offset += 1
        
    return slots_livres

def agendar_video_no_youtube(video_id: str, publish_at_iso: str, canal: str = "futebol") -> bool:
    """
    Aplica o agendamento nativo do YouTube Data API v3.
    Para agendar no YouTube, o vídeo deve ter privacyStatus='private' e publishAt='ISO_UTC_DATE'.
    """
    try:
        yt = youtube_uploader.get_authenticated_service(canal)
        
        # 1. Recupera snippet atual para auditar
        res_v = yt.videos().list(part="snippet,status", id=video_id).execute()
        if not res_v.get("items"):
            logger.warning(f"Vídeo {video_id} não existe mais no YouTube (já publicado ou removido). Arquivando do agendador.")
            # Marca como ARQUIVADO no banco para não tentar de novo
            try:
                conn_del = sqlite3.connect(DB_PATH)
                conn_del.execute("UPDATE videos_gerados SET status = 'ARQUIVADO' WHERE youtube_video_id = ?", (video_id,))
                conn_del.commit()
                conn_del.close()
            except Exception:
                pass
            return False
            
        video_data = res_v["items"][0]
        snippet = video_data.get("snippet", {})
        
        # Determina tipo pelo snippet
        is_short = "#shorts" in snippet.get("title", "").lower() or "#shorts" in snippet.get("description", "").lower()
        snippet_sanitizado = auditar_e_sanitizar_metadados(snippet, tipo="short" if is_short else "doc", canal=canal)
        
        # 2. Executa o update com agendamento nativo
        body_update = {
            "id": video_id,
            "status": {
                "privacyStatus": "private",
                "publishAt": publish_at_iso
            },
            "snippet": snippet_sanitizado
        }
        
        update_res = yt.videos().update(
            part="status,snippet",
            body=body_update
        ).execute()
        
        logger.success(f"Vídeo {video_id} agendado no YouTube com sucesso para: {publish_at_iso}")
        return True
    except Exception as e:
        err_str = str(e).lower()
        if "quotaexceeded" in err_str or "quota" in err_str:
            logger.error(f"🛑 [COTA YOUTUBE] Cota diária atingida ao tentar agendar {video_id}. O YouTube reinicia a cota às 00:00 PST. Pausando tentativas de agendamento por hoje.")
            raise QuotaExceededException("Cota diária da API do YouTube excedida.")
        else:
            logger.error(f"Erro ao agendar vídeo {video_id} no YouTube: {e}")
        return False

def executar_fluxo_auto_agendamento(canal: str = "futebol") -> List[Dict]:
    """
    Fluxo Completo Inteligente:
    1. Busca todos os vídeos já gerados e postados como UNLISTED que ainda não foram agendados/publicados.
    2. Identifica os próximos slots de pico disponíveis (hoje ou próximos dias).
    3. Audita metadados e envia comando de agendamento automático para o YouTube.
    4. Registra no banco de dados e notifica no Telegram.
    """
    init_tabela_agendamentos()
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Busca vídeos unlisted que ainda não foram publicados e nem agendados
    cur.execute('''
        SELECT task_id, canal, tipo, titulo, youtube_video_id, criado_em 
        FROM videos_gerados 
        WHERE canal = ? 
          AND youtube_video_id IS NOT NULL 
          AND length(youtube_video_id) > 5 
          AND youtube_video_id NOT IN (SELECT video_id FROM publicacoes_pico_log)
          AND youtube_video_id NOT IN (SELECT video_id FROM agendamentos_youtube WHERE status = 'AGENDADO')
        ORDER BY rowid ASC
    ''', (canal,))
    videos_prontos = cur.fetchall()
    conn.close()
    
    if not videos_prontos:
        logger.info(f"[{canal.upper()}] Nenhum vídeo pendente para agendamento.")
        return []
        
    logger.info(f"[{canal.upper()}] Encontrados {len(videos_prontos)} vídeos prontos na esteira aguardando agendamento!")
    
    # Descobre os próximos slots de pico livres
    slots_livres = encontrar_proximos_slots_livres(canal, qtd_slots=len(videos_prontos) * 2)
    if not slots_livres:
        logger.warning(f"[{canal.upper()}] Nenhum slot de pico livre encontrado.")
        return []
        
    agendados_sucesso = []
    
    for v in videos_prontos:
        task_id, c_nome, tipo, titulo, vid_id, criado_em = v
        is_doc = (tipo == "doc")
        
        # Encontra o slot ideal compatível com o formato (FIFO)
        slot_escolhido = None
        for s in slots_livres:
            if (is_doc and s["tipo_preferido"] == "doc") or (not is_doc and s["tipo_preferido"] == "short"):
                slot_escolhido = s
                break
                
        # Se não houver slot do tipo exato livre de imediato, pega o primeiro disponível
        if not slot_escolhido:
            if not slots_livres:
                logger.warning(f"[{canal.upper()}] Todos os slots de pico calculados foram esgotados.")
                break
            slot_escolhido = slots_livres[0]
            
        slots_livres.remove(slot_escolhido)
        
        logger.info(f"📅 Agendando '{titulo[:40]}...' (ID: {vid_id}) para {slot_escolhido['data_cv']} às {slot_escolhido['hora_cv']} CV ({slot_escolhido['horario_utc_iso']})")
        
        try:
            sucesso = agendar_video_no_youtube(vid_id, slot_escolhido["horario_utc_iso"], canal=canal)
        except QuotaExceededException:
            logger.warning(f"[{canal.upper()}] Cota atingida. Interrompendo esteira de agendamento para este canal até a renovação da cota.")
            break
        if sucesso:
            registrar_agendamento_db(
                video_id=vid_id,
                canal=canal,
                tipo=tipo,
                titulo=titulo,
                slot_id=slot_escolhido["slot_id"],
                data_cv=slot_escolhido["data_cv"],
                horario_cv=slot_escolhido["hora_cv"],
                horario_utc_iso=slot_escolhido["horario_utc_iso"]
            )
            
            # Notifica Telegram
            try:
                msg = (
                    "📅 *VÍDEO AGENDADO NO YOUTUBE (MODO PILOTO 100% AUTÔNOMO)*\n\n"
                    f"📺 *Canal:* `{canal.upper()}`\n"
                    f"🎬 *Título:* _{titulo}_\n"
                    f"🎯 *Formato:* `{'DOCUMENTÁRIO' if is_doc else 'SHORT'}`\n"
                    f"📆 *Data de Lançamento:* `{slot_escolhido['data_cv']}`\n"
                    f"⏰ *Horário de Pico:* `{slot_escolhido['hora_cv']} (Cabo Verde)`\n"
                    f"🌍 *Público-Alvo:* `{slot_escolhido['rotulo']}`\n"
                    f"🔗 *Link Agendado:* https://youtu.be/{vid_id}\n\n"
                    "🛡️ _Mesmo que o servidor ou PC seja desligado, o YouTube publicará automaticamente no segundo exato!_"
                )
                telegram_reporter.enviar_mensagem_telegram(msg)
            except Exception:
                pass
                
            agendados_sucesso.append({
                "video_id": vid_id,
                "titulo": titulo,
                "tipo": tipo,
                "data": slot_escolhido["data_cv"],
                "horario_cv": slot_escolhido["hora_cv"],
                "rotulo": slot_escolhido["rotulo"]
            })
            
    return agendados_sucesso

if __name__ == "__main__":
    init_tabela_agendamentos()
    resultado = executar_fluxo_auto_agendamento("futebol")
    print(f"Total de vídeos agendados com sucesso: {len(resultado)}")
