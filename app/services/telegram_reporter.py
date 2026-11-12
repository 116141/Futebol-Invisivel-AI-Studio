import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import dateutil.parser
from loguru import logger
import autoviral_brain
from app.services import youtube_uploader, aliexpress_affiliate

def init_tabela_historico_canal():
    conn = autoviral_brain.get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historico_crescimento_canal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canal TEXT NOT NULL,
            inscritos INTEGER DEFAULT 0,
            views_totais INTEGER DEFAULT 0,
            videos_totais INTEGER DEFAULT 0,
            data_registro TEXT NOT NULL,
            UNIQUE(canal, data_registro)
        )
    """)
    conn.commit()
    conn.close()

def obter_credenciais_telegram():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    
    if not token or not chat_id:
        caminhos_env = [
            ".env",
            r"C:\Users\Uni-CvFCT-EdmilsonGi\Documents\Projetos_Bots\projects\bot_00_hub_portal\.env"
        ]
        for c in caminhos_env:
            if os.path.exists(c):
                try:
                    with open(c, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("TELEGRAM_BOT_TOKEN="):
                                token = token or line.split("=", 1)[1].strip()
                            elif line.startswith("TELEGRAM_CHAT_ID="):
                                chat_id = chat_id or line.split("=", 1)[1].strip()
                except Exception:
                    pass
    return token, chat_id

def enviar_mensagem_telegram(texto: str) -> bool:
    token, chat_id = obter_credenciais_telegram()
    if not token or not chat_id:
        logger.warning("Credenciais do Telegram não configuradas (.env). Relatório não enviado.")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if res_data.get("ok"):
                logger.success("Relatório executivo enviado com sucesso ao Telegram!")
                return True
            else:
                logger.error(f"Erro Telegram: {res_data}")
                return False
    except Exception as e:
        logger.error(f"Falha de conexão com a API do Telegram: {e}")
        return False

def consultar_grade_agendada_canal(canal_nome: str, data_alvo: str = None) -> list:
    """Consulta os vídeos agendados oficialmente para a data especificada (default hoje)."""
    if not data_alvo:
        data_alvo = datetime.now().strftime("%Y-%m-%d")
        
    agendados = []
    try:
        youtube = youtube_uploader.get_authenticated_service(canal_nome)
        ch_resp = youtube.channels().list(part="contentDetails", mine=True).execute()
        if not ch_resp.get("items"):
            return []
        uploads_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        res = youtube.playlistItems().list(part="snippet,status", playlistId=uploads_id, maxResults=50).execute()
        vid_ids = [it["snippet"]["resourceId"]["videoId"] for it in res.get("items", [])]
        if not vid_ids:
            return []
            
        v_det = youtube.videos().list(part="snippet,status", id=",".join(vid_ids[:50])).execute()
        for v in v_det.get("items", []):
            st = v.get("status", {})
            sn = v.get("snippet", {})
            pub_at = st.get("publishAt")
            titulo = sn.get("title", "")
            vid_id = v.get("id")
            
            if pub_at and data_alvo in pub_at:
                try:
                    dt_utc = dateutil.parser.isoparse(pub_at)
                    # Hora UTC e Hora de Cabo Verde (UTC-1)
                    h_utc = dt_utc.strftime("%H:%M")
                    h_cv = f"{((dt_utc.hour - 1) % 24):02d}:{dt_utc.minute:02d}"
                    agendados.append({
                        "id": vid_id,
                        "titulo": titulo,
                        "horario_utc": h_utc,
                        "horario_cv": h_cv,
                        "dt": dt_utc
                    })
                except Exception:
                    agendados.append({
                        "id": vid_id,
                        "titulo": titulo,
                        "horario_utc": pub_at,
                        "horario_cv": pub_at,
                        "dt": datetime.now()
                    })
                    
        agendados.sort(key=lambda x: x["dt"])
    except Exception as e:
        logger.warning(f"Erro obtendo grade agendada de {canal_nome}: {e}")
        
    return agendados

def consultar_dados_canal_e_crescimento(canal_nome: str) -> dict:
    init_tabela_historico_canal()
    conn = autoviral_brain.get_conn()
    cur = conn.cursor()
    
    inscritos = 0
    views_totais = 0
    videos_totais = 0
    titulo_canal = canal_nome.capitalize()
    
    try:
        youtube = youtube_uploader.get_authenticated_service(canal_nome)
        req = youtube.channels().list(mine=True, part="snippet,statistics")
        res = req.execute()
        if res.get("items"):
            item = res["items"][0]
            titulo_canal = item["snippet"]["title"]
            st = item["statistics"]
            inscritos = int(st.get("subscriberCount", 0))
            views_totais = int(st.get("viewCount", 0))
            videos_totais = int(st.get("videoCount", 0))
    except Exception as e:
        logger.warning(f"Erro consultando API do YouTube para {canal_nome}: {e}")

    hoje = datetime.now().strftime("%Y-%m-%d")
    
    cur.execute(
        "SELECT inscritos, views_totais FROM historico_crescimento_canal WHERE canal = ? AND data_registro < ? ORDER BY data_registro DESC LIMIT 1",
        (canal_nome, hoje)
    )
    ant = cur.fetchone()
    
    delta_sub = 0
    delta_views = 0
    if ant:
        delta_sub = inscritos - ant[0]
        delta_views = views_totais - ant[1]
    
    cur.execute("""
        INSERT OR REPLACE INTO historico_crescimento_canal (
            canal, inscritos, views_totais, videos_totais, data_registro
        ) VALUES (?, ?, ?, ?, ?)
    """, (canal_nome, inscritos, views_totais, videos_totais, hoje))
    conn.commit()
    conn.close()
    
    termometro = "🔥 Em Alta" if delta_views > 1000 or delta_sub > 10 else "🟢 Ativo e Crescendo"
    tendencia = f"+{delta_sub} inscritos | +{delta_views:,} views hoje".replace(",", ".") if delta_views >= 0 else "Estável"
    
    return {
        "titulo": titulo_canal,
        "inscritos": inscritos,
        "views_totais": views_totais,
        "videos_totais": videos_totais,
        "termometro": termometro,
        "tendencia": tendencia
    }

def formatar_relatorio_executivo() -> str:
    hoje_fmt = datetime.now().strftime("%d/%m/%Y")
    hoje_iso = datetime.now().strftime("%Y-%m-%d")
    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
    
    dados_fut = consultar_dados_canal_e_crescimento("futebol")
    dados_mod = consultar_dados_canal_e_crescimento("moda")
    dados_fer = consultar_dados_canal_e_crescimento("fergil")
    
    # Consulta a grade oficial de vídeos agendados para hoje em cada canal
    agendados_fut = consultar_grade_agendada_canal("futebol", hoje_iso)
    agendados_fer = consultar_grade_agendada_canal("fergil", hoje_iso)
    agendados_mod = consultar_grade_agendada_canal("moda", hoje_iso)
    total_agendados_hoje = len(agendados_fut) + len(agendados_fer) + len(agendados_mod)
    
    conn = autoviral_brain.get_conn()
    cur = conn.cursor()
    
    # Produção 24h
    cur.execute("SELECT COUNT(*) FROM videos_gerados WHERE criado_em >= datetime('now', '-1 day')")
    novos_24h = cur.fetchone()[0] or 0
    conn.close()
    
    # Vendas AliExpress
    vendas = []
    try:
        vendas = aliexpress_affiliate.fetch_affiliate_orders()
    except Exception:
        pass

    linhas = [
        "📊 *RELATÓRIO DIÁRIO DE AUDIÊNCIA & GRADE MULTICANAL*",
        f"📅 _{agora}_\n",
        
        f"⏰ *GRADE DE PUBLICAÇÕES AGENDADAS PARA HOJE ({hoje_fmt}):*",
        f"Total programado: `{total_agendados_hoje}` vídeos\n"
    ]
    
    # Bloco Futebol
    linhas.append("⚽ *Canal Futebol Invisível:*")
    if agendados_fut:
        for it in agendados_fut:
            tit_resumido = it["titulo"][:55] + ("..." if len(it["titulo"]) > 55 else "")
            linhas.append(f"  • 🕒 `{it['horario_cv']} (CV)` / `{it['horario_utc']} (UTC)`")
            linhas.append(f"    └ 🎬 _{tit_resumido}_")
    else:
        linhas.append("  • _Nenhum vídeo agendado para hoje (esteira em maturação)._")
    linhas.append("")

    # Bloco FERGIL
    linhas.append("💼 *Canal FERGIL (Tech & Negócios):*")
    if agendados_fer:
        for it in agendados_fer:
            tit_resumido = it["titulo"][:55] + ("..." if len(it["titulo"]) > 55 else "")
            linhas.append(f"  • 🕒 `{it['horario_cv']} (CV)` / `{it['horario_utc']} (UTC)`")
            linhas.append(f"    └ 🎬 _{tit_resumido}_")
    else:
        linhas.append("  • _Nenhum vídeo agendado para hoje._")
    linhas.append("")

    # Bloco Moda
    linhas.append("👗 *Canal Moda (Alana Cruz):*")
    if agendados_mod:
        for it in agendados_mod:
            tit_resumido = it["titulo"][:55] + ("..." if len(it["titulo"]) > 55 else "")
            linhas.append(f"  • 🕒 `{it['horario_cv']} (CV)` / `{it['horario_utc']} (UTC)`")
            linhas.append(f"    └ 🎬 _{tit_resumido}_")
    else:
        linhas.append("  • _Nenhum vídeo agendado para hoje (novas peças na fila)._")
    linhas.append("")

    linhas.extend([
        "📈 *MÉTRICAS & STATUS DOS CANAIS:*",
        f"• *Futebol Invisível:* `{dados_fut['inscritos']}` inscritos | `{dados_fut['views_totais']:,}` views | {dados_fut['termometro']}".replace(",", "."),
        f"• *FERGIL:* `{dados_fer['inscritos']}` inscritos | `{dados_fer['views_totais']:,}` views | {dados_fer['termometro']}".replace(",", "."),
        f"• *Moda Feminina:* `{dados_mod['inscritos']}` inscritos | `{dados_mod['views_totais']:,}` views | {dados_mod['termometro']}".replace(",", "."),
        "",
        "🛍️ *Afiliados & Operação:*",
        f"• *Vendas / Pedidos:* `{len(vendas)}` registrados",
        f"• *Vídeos Produzidos (24h):* `{novos_24h}` vídeos gerados",
        f"• *Tag Amazon:* `edmilsonferg-20` ativa nos comentários",
        "",
        "🚀 _MoneyPrinter Turbo Intelligence Engine_"
    ])

    return "\n".join(linhas)

def disparar_relatorio_telegram_agora() -> bool:
    texto = formatar_relatorio_executivo()
    return enviar_mensagem_telegram(texto)

def executar_envio_relatorio_diario() -> bool:
    return disparar_relatorio_telegram_agora()

if __name__ == "__main__":
    print(formatar_relatorio_executivo())
