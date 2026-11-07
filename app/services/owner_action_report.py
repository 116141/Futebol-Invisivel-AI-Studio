import sys
import os

# Adiciona a raiz do projeto ao path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import re
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger
import autoviral_brain

try:
    from app.services import telegram_reporter, aliexpress_affiliate
except Exception:
    telegram_reporter = None
    aliexpress_affiliate = None


def coletar_dados_acao_proprietario() -> Dict[str, Any]:
    """
    Varre a base de dados, arquivos locais e métricas para consolidar
    tudo o que requer atenção ou intervenção manual do proprietário.
    """
    tz_cv = timezone(timedelta(hours=-1))
    agora_cv = datetime.now(tz_cv)
    hoje_cv_str = agora_cv.strftime("%Y-%m-%d")

    conn = autoviral_brain.get_conn()
    cur = conn.cursor()

    # 1. Obter todas as tarefas ativas (não arquivadas)
    cur.execute("""
        SELECT task_id, canal, tipo, titulo, file_path, txt_path, status, criado_em, 
               youtube_video_id, upload_falha_detalhes, link_afiliado
        FROM videos_gerados
        WHERE status != 'ARQUIVADO'
        ORDER BY criado_em DESC
    """)
    tarefas_ativas = [dict(row) for row in cur.fetchall()]

    # 2. Obter capas registradas
    cur.execute("SELECT video_id, canal, caminho_capa FROM capas_personalizadas_geradas")
    capas_registradas = {row["video_id"]: row["caminho_capa"] for row in cur.fetchall()}

    # 3. Obter status dos canais (bloqueios, quotas, erros de upload)
    cur.execute("""
        SELECT canal, bloqueado, bloqueado_ate, ultimo_erro_codigo, ultimo_erro_motivo, ultimo_erro_mensagem
        FROM canal_upload_status
    """)
    status_canais = {row["canal"]: dict(row) for row in cur.fetchall()}

    # 4. Obter publicações de hoje
    cur.execute("""
        SELECT canal, slot_id, data_cv, video_id, publicado_em
        FROM publicacoes_pico_log
        WHERE data_cv = ?
        ORDER BY publicado_em ASC
    """, (hoje_cv_str,))
    publicados_hoje_pico = [dict(row) for row in cur.fetchall()]

    # 5. Métricas do YouTube
    cur.execute("""
        SELECT video_id, canal, formato, titulo, views, likes, upload_date, url, atualizado_em
        FROM metricas_youtube
    """)
    metricas_videos = {row["video_id"]: dict(row) for row in cur.fetchall()}

    conn.close()

    # ESTRUTURAÇÃO DAS SEÇÕES
    capas_necessarias = []
    espera_aprovacao = []
    prontos_publicar = []
    erros_problemas = []
    publicados_hoje = []
    baixo_desempenho = []

    # Analisar bloqueios e credenciais de canais como problemas globais
    for c_nome, c_info in status_canais.items():
        if c_info.get("bloqueado"):
            erros_problemas.append({
                "categoria": "Canal Bloqueado / Limite",
                "canal": c_nome.upper(),
                "task_id": "GLOBAL",
                "erro": f"Bloqueado até {c_info.get('bloqueado_ate')} ({c_info.get('ultimo_erro_motivo')}: {c_info.get('ultimo_erro_mensagem')})"
            })
        elif c_info.get("ultimo_erro_motivo") == "OAUTH_INVALID":
            erros_problemas.append({
                "categoria": "Credenciais Expiradas",
                "canal": c_nome.upper(),
                "task_id": "GLOBAL",
                "erro": "OAuth RefreshError detectado. Necessário reconectar conta do YouTube."
            })

    # Analisar tarefas ativas
    for t in tarefas_ativas:
        tid = t["task_id"]
        canal = (t["canal"] or "").lower()
        titulo = t["titulo"] or ""
        st = t["status"] or ""
        fpath = t["file_path"] or ""
        txtpath = t["txt_path"] or ""
        criado = t["criado_em"] or ""

        # Verificar se houve erro de upload ou renderização
        if "ERRO" in st or "FALHA" in st or "DUPLICADO_SUSPEITO" in st:
            erros_problemas.append({
                "categoria": "Falha de Upload / Processamento",
                "canal": canal.upper(),
                "task_id": tid,
                "erro": f"Status: {st} | Detalhes: {t.get('upload_falha_detalhes') or 'Sem detalhes adicionais'}"
            })
            continue

        # Verificar se o arquivo MP4 físico existe
        mp4_existe = os.path.isfile(fpath) if fpath else False

        # Verificar thumbnail personalizada
        tem_capa = False
        if tid in capas_registradas or (fpath and os.path.isfile(fpath.replace(".mp4", "_capa.jpg"))):
            tem_capa = True
        elif fpath and (os.path.isfile(fpath.replace(".mp4", ".jpg")) or os.path.isfile(fpath.replace(".mp4", ".png"))):
            tem_capa = True

        # Documentários longos ou vídeos FERGIL exigem capa obrigatoriamente
        is_doc = t.get("tipo") == "doc" or canal == "fergil" or "documentário" in titulo.lower()

        # Sensibilidade / Moderação Editorial (Conteúdo sensível para aprovação manual)
        motivo_sensivel = None
        if canal == "fergil":
            # Vídeos de finanças/patrimônio ou figuras públicas exigem olhar do proprietário
            if any(palavra in titulo.lower() for palavra in ["bilhões", "perdeu", "fraude", "escândalo", "ações", "queda", "oracle", "musk", "ellison"]):
                motivo_sensivel = "Conteúdo financeiro de alta repercussão / figura pública (FERGIL)"
        elif "copyright" in titulo.lower() or "polêmica" in titulo.lower():
            motivo_sensivel = "Potencial risco de copyright ou diretrizes"

        if motivo_sensivel and st not in ["POSTADO NO YOUTUBE", "CONCLUÍDO"]:
            espera_aprovacao.append({
                "canal": canal.upper(),
                "task_id": tid,
                "titulo": titulo,
                "motivo": motivo_sensivel
            })

        # 1. Vídeos à Espera de Capa
        if mp4_existe and not tem_capa and is_doc and st not in ["POSTADO NO YOUTUBE", "CONCLUÍDO"]:
            capas_necessarias.append({
                "canal": canal.upper(),
                "task_id": tid,
                "titulo": titulo,
                "data": criado[:10] if criado else "N/A",
                "prioridade": "ALTA" if canal == "fergil" else "MÉDIA",
                "motivo": "Thumbnail personalizada ausente para formato de destaque"
            })

        # 3. Vídeos Prontos para Publicar
        if mp4_existe and st in ["RENDERIZADO_AGUARDANDO_UPLOAD", "CONCLUÍDO"] and not t.get("youtube_video_id"):
            # Para canais que precisam de capa (ex: FERGIL/Docs), só está 100% pronto se tiver capa
            if not is_doc or tem_capa:
                prontos_publicar.append({
                    "canal": canal.upper(),
                    "task_id": tid,
                    "titulo": titulo,
                    "tipo": t.get("tipo", "video")
                })

    # 5. Vídeos Publicados Hoje
    for pub in publicados_hoje_pico:
        v_meta = metricas_videos.get(pub["video_id"], {})
        publicados_hoje.append({
            "hora": pub["publicado_em"][11:16] if len(pub.get("publicado_em", "")) >= 16 else "N/A",
            "canal": pub["canal"].upper(),
            "task_id": pub.get("slot_id", "N/A"),
            "titulo": v_meta.get("titulo") or f"Vídeo ID: {pub['video_id']}",
            "link": f"https://youtu.be/{pub['video_id']}",
            "views": v_meta.get("views", 0)
        })

    # 6. Vídeos com Baixo Desempenho (> 24h com views < 100)
    for vid_id, m in metricas_videos.items():
        upload_date_str = m.get("upload_date") or ""
        views = m.get("views", 0)
        if upload_date_str:
            try:
                dt_up = datetime.fromisoformat(upload_date_str.replace("Z", "+00:00"))
                horas_no_ar = (datetime.now(timezone.utc) - dt_up).total_seconds() / 3600
                if horas_no_ar >= 24 and views < 100:
                    baixo_desempenho.append({
                        "video_id": vid_id,
                        "canal": m.get("canal", "").upper(),
                        "titulo": m.get("titulo", "Sem título"),
                        "views": views,
                        "horas": int(horas_no_ar),
                        "acao": "Trocar thumbnail ou reescrever título"
                    })
            except Exception:
                pass

    # Contagem de Produzidos Hoje
    produzidos_hoje = [t for t in tarefas_ativas if (t.get("criado_em") or "").startswith(hoje_cv_str)]

    # Cálculo estimativo de receita de afiliados ou canais
    receita_eur = "€0,00"
    if aliexpress_affiliate:
        try:
            vendas = aliexpress_affiliate.obter_relatorio_vendas(dias=1)
            if vendas:
                total_comissao = sum(float(v.get("comissao_estimada", 0)) for v in vendas)
                receita_eur = f"€{total_comissao:.2f}"
        except Exception:
            pass

    tem_acao_obrigatoria = bool(capas_necessarias or espera_aprovacao or erros_problemas)

    return {
        "data_cv": hoje_cv_str,
        "produzidos_hoje_count": len(produzidos_hoje),
        "publicados_hoje_count": len(publicados_hoje),
        "capas_pendentes_count": len(capas_necessarias),
        "espera_aprovacao_count": len(espera_aprovacao),
        "prontos_publicar_count": len(prontos_publicar),
        "problemas_count": len(erros_problemas),
        "receita_estimada": receita_eur,
        "tem_acao_obrigatoria": tem_acao_obrigatoria,
        "capas_necessarias": capas_necessarias,
        "espera_aprovacao": espera_aprovacao,
        "prontos_publicar": prontos_publicar,
        "erros_problemas": erros_problemas,
        "publicados_hoje": publicados_hoje,
        "baixo_desempenho": baixo_desempenho
    }


def formatar_relatorio_acao_proprietario() -> str:
    """
    Gera o texto rigoroso do relatório '🚨 AÇÃO DO PROPRIETÁRIO',
    priorizando o que exige intervenção humana direta em menos de 10 segundos.
    """
    d = coletar_dados_acao_proprietario()
    linhas = []

    # CABEÇALHO / RESUMO RÁPIDO (Menos de 10 segundos no WhatsApp/Telegram)
    linhas.append("🚨 *AÇÃO DO PROPRIETÁRIO — HUB CENTRAL*")
    linhas.append(f"📅 *Data:* `{d['data_cv']}` (Fuso Cabo Verde)")
    linhas.append("")
    linhas.append("📋 *RESUMO OPERACIONAL:*")
    linhas.append(f"• 🎬 *Produzidos hoje:* `{d['produzidos_hoje_count']}`")
    linhas.append(f"• 🚀 *Publicados hoje:* `{d['publicados_hoje_count']}`")
    linhas.append(f"• 🖼️ *Capas pendentes:* `{d['capas_pendentes_count']}`")
    linhas.append(f"• 🟡 *Revisão / Aprovação:* `{d['espera_aprovacao_count']}`")
    linhas.append(f"• ⚠️ *Problemas / Erros:* `{d['problemas_count']}`")
    linhas.append(f"• 💰 *Receita Estimada:* `{d['receita_estimada']}`")
    linhas.append(f"👉 *AÇÃO NECESSÁRIA:* *{'SIM (Ver abaixo)' if d['tem_acao_obrigatoria'] else 'NÃO'}*")
    linhas.append("―" * 28)

    # SEÇÃO 1: VÍDEOS À ESPERA DE CAPA
    if d["capas_necessarias"]:
        linhas.append("\n🔴 *CAPA NECESSÁRIA:*")
        for c in d["capas_necessarias"]:
            linhas.append(f"• *Canal:* `{c['canal']}`")
            linhas.append(f"  *task_id:* `{c['task_id']}`")
            linhas.append(f"  *Título:* _{c['titulo']}_")
            linhas.append(f"  *Data:* `{c['data']}` | *Prioridade:* `{c['prioridade']}`")
            linhas.append(f"  *Motivo:* {c['motivo']}\n")

    # SEÇÃO 2: VÍDEOS À ESPERA DE APROVAÇÃO
    if d["espera_aprovacao"]:
        linhas.append("\n🟡 *VÍDEOS À ESPERA DE APROVAÇÃO:*")
        for a in d["espera_aprovacao"]:
            linhas.append(f"• *Canal:* `{a['canal']}`")
            linhas.append(f"  *task_id:* `{a['task_id']}`")
            linhas.append(f"  *Título:* _{a['titulo']}_")
            linhas.append(f"  *Motivo de Alerta:* {a['motivo']}\n")

    # SEÇÃO 4: VÍDEOS COM PROBLEMAS
    if d["erros_problemas"]:
        linhas.append("\n🔴 *VÍDEOS OU SISTEMAS COM PROBLEMAS:*")
        for err in d["erros_problemas"]:
            linhas.append(f"• *Tipo:* `{err['categoria']}` | *Canal:* `{err['canal']}`")
            linhas.append(f"  *task_id:* `{err['task_id']}`")
            linhas.append(f"  *Falha:* {err['erro']}\n")

    # SEÇÃO 3: VÍDEOS PRONTOS PARA PUBLICAR
    if d["prontos_publicar"]:
        linhas.append("\n🟢 *PRONTO PARA PUBLICAR (100% Validado):*")
        for p in d["prontos_publicar"][:6]:
            linhas.append(f"• *Canal:* `{p['canal']}` | *task_id:* `{p['task_id']}`")
            linhas.append(f"  *Título:* _{p['titulo']}_")
        if len(d["prontos_publicar"]) > 6:
            linhas.append(f"  _(e mais {len(d['prontos_publicar']) - 6} vídeos em estoque maturado)_")

    # SEÇÃO 5: VÍDEOS PUBLICADOS HOJE
    if d["publicados_hoje"]:
        linhas.append("\n✅ *PUBLICADOS HOJE:*")
        for pub in d["publicados_hoje"]:
            linhas.append(f"• *Hora:* `{pub['hora']}` | *Canal:* `{pub['canal']}`")
            linhas.append(f"  *Título:* _{pub['titulo']}_")
            linhas.append(f"  *Views atuais:* `{pub['views']}` | 🔗 {pub['link']}")

    # SEÇÃO 6: VÍDEOS COM BAIXO DESEMPENHO (> 24h)
    if d["baixo_desempenho"]:
        linhas.append("\n📉 *VÍDEOS COM BAIXO DESEMPENHO (>24h):*")
        for bd in d["baixo_desempenho"][:3]:
            linhas.append(f"• *Canal:* `{bd['canal']}` | *Título:* _{bd['titulo']}_")
            linhas.append(f"  *Views:* `{bd['views']}` após {bd['horas']}h")
            linhas.append(f"  *Ação sugerida:* `{bd['acao']}`")

    # SEÇÃO 7: RESUMO DE PENDÊNCIAS DO DIA
    linhas.append("\n" + "―" * 28)
    linhas.append("📌 *PENDÊNCIAS DO DIA:*")
    linhas.append(f"• 🔴 Capas por criar: `{d['capas_pendentes_count']}`")
    linhas.append(f"• 🟡 Vídeos para revisão: `{d['espera_aprovacao_count']}`")
    linhas.append(f"• 🟢 Prontos para publicar: `{d['prontos_publicar_count']}`")
    linhas.append(f"• 🔴 Erros / Bloqueios: `{d['problemas_count']}`")
    linhas.append(f"• ✅ Publicados hoje: `{d['publicados_hoje_count']}`")

    # CONCLUSÃO FINAL
    if not d["tem_acao_obrigatoria"]:
        linhas.append("\n✅ *NENHUMA INTERVENÇÃO MANUAL NECESSÁRIA*")
    else:
        linhas.append("\n⚠️ *ATENÇÃO:* Existem itens acima que exigem ação do proprietário antes do próximo ciclo.")

    return "\n".join(linhas)


def disparar_relatorio_acao_proprietario() -> bool:
    """Gera e despacha o relatório de atenção do proprietário via Telegram."""
    if not telegram_reporter:
        logger.error("telegram_reporter não disponível.")
        return False
    texto = formatar_relatorio_acao_proprietario()
    return telegram_reporter.enviar_mensagem_telegram(texto)


if __name__ == "__main__":
    print(formatar_relatorio_acao_proprietario())
