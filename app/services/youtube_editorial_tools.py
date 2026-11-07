"""youtube_editorial_tools.py - Camada de integração Python com as YouTube Agent Skills.

Disponibiliza ferramentas consultivas para o fluxo editorial do Futebol Invisível:
1. avaliar_ganchos_editorial(ganchos: List[str]) -> List[Dict]
2. avaliar_par_titulo_capa(titulo: str, texto_capa: Optional[str] = None) -> Dict
3. analisar_retencao_csv(caminho_csv: str, duracao_segundos: Optional[float] = None) -> Dict

REGRAS DE ARQUITETURA E SEGURANÇA:
- Reutiliza diretamente os scripts originais em .agents/skills/ (sem clonar lógica).
- Operação 100% determinística, local e segura (sem chamadas de rede, sem APIs pagas).
- Consultiva: NÃO aprova fatos, NÃO altera roteiros por conta própria e NÃO inicia renderização.
"""

import os
import sys
import json
import re
from typing import List, Dict, Optional, Any
from loguru import logger

# Caminhos base para as skills instaladas em .agents/skills/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS_DIR = os.path.join(BASE_DIR, ".agents", "skills")

PATH_YT_SCRIPT = os.path.join(SKILLS_DIR, "yt-script")
PATH_YT_PACKAGE = os.path.join(SKILLS_DIR, "yt-package")
PATH_YT_RETENTION = os.path.join(SKILLS_DIR, "yt-retention")


def _garantir_caminho_modulo(path: str):
    """Adiciona o caminho da skill ao sys.path se ainda não estiver presente."""
    abs_path = os.path.abspath(path)
    if abs_path not in sys.path:
        sys.path.insert(0, abs_path)


def avaliar_ganchos_editorial(ganchos: List[str]) -> List[Dict[str, Any]]:
    """
    Avalia uma lista de ganchos textuais reutilizando yt-script/hookscore.py.

    Retorna uma lista estruturada de avaliações:
    - hook: texto do gancho
    - properties: {SPECIFICITY, ADDRESS, STAKES, CURIOSITY, BREVITY} (0 a 100)
    - verdict: score ponderado (0 a 100)
    - band: "STRONG" | "WORKABLE" | "WEAK"
    - formula: fórmula narrativa identificada
    - weakest: fraqueza principal e sugestão de correção
    - alerta_factual: lembrete de que a pontuação não valida a veracidade dos fatos.

    Tratamento: ganchos vazios são ignorados ou retornam estrutura com erro.
    """
    if not isinstance(ganchos, list):
        return []

    _garantir_caminho_modulo(PATH_YT_SCRIPT)
    try:
        import hookscore
    except Exception as e:
        logger.error(f"Não foi possível importar hookscore de {PATH_YT_SCRIPT}: {e}")
        return [{"erro": f"Módulo hookscore indisponível: {e}"}]

    resultados = []
    for g in ganchos:
        if not g or not isinstance(g, str) or not g.strip():
            resultados.append({
                "hook": "",
                "verdict": 0,
                "band": "INVALID",
                "erro": "Gancho vazio ou inválido."
            })
            continue

        texto = g.strip()
        try:
            parts, verdict, name, hits = hookscore.score(texto)
            low_prop = min(parts, key=parts.get)
            sugestao_fix = hookscore.FIX.get(low_prop, "Revisar concisão e impacto")

            resultados.append({
                "hook": texto,
                "properties": parts,
                "verdict": int(verdict),
                "band": hookscore.band(verdict),
                "formula": name,
                "matched_patterns": int(hits),
                "weakest_property": low_prop,
                "sugestao_ajuste": f"{low_prop}: {sugestao_fix}",
                "alerta_editorial": "A pontuação mede concisão e estrutura; NÃO substitui a verificação de fontes nem garante viralização."
            })
        except Exception as err:
            logger.warning(f"Erro ao pontuar gancho '{texto[:30]}': {err}")
            resultados.append({
                "hook": texto,
                "verdict": 0,
                "band": "ERROR",
                "erro": str(err)
            })

    # Ordena pelo maior veredicto técnico
    resultados.sort(key=lambda r: r.get("verdict", 0), reverse=True)
    return resultados


def avaliar_par_titulo_capa(titulo: str, texto_capa: Optional[str] = None) -> Dict[str, Any]:
    """
    Avalia a complementaridade de um título e texto de thumbnail reutilizando yt-package/title.py.

    Retorna:
    - title: título avaliado
    - thumb: texto de capa avaliado
    - score: pontuação técnica de 0 a 100
    - chars: quantidade de caracteres
    - issues: lista de problemas detectados (repetição, tamanho para mobile/desktop, etc.)
    - good: lista de pontos positivos identificados
    - recomendacao: parecer editorial consultivo
    """
    if not titulo or not isinstance(titulo, str) or not titulo.strip():
        return {
            "title": "",
            "score": 0,
            "erro": "Título ausente ou inválido.",
            "issues": [("empty", "O título não pode estar vazio.")]
        }

    _garantir_caminho_modulo(PATH_YT_PACKAGE)
    try:
        import title as yt_title
    except Exception as e:
        logger.error(f"Não foi possível importar title de {PATH_YT_PACKAGE}: {e}")
        return {"erro": f"Módulo yt-package indisponível: {e}"}

    t_clean = titulo.strip()
    c_clean = texto_capa.strip() if (texto_capa and isinstance(texto_capa, str)) else None

    try:
        res = yt_title.check(t_clean, c_clean)
        res["thumb"] = c_clean
        res["alerta_editorial"] = "O score é consultivo. Evite repetir na capa palavras já presentes no título."
        return res
    except Exception as err:
        logger.warning(f"Erro ao avaliar título '{t_clean[:30]}': {err}")
        return {
            "title": t_clean,
            "thumb": c_clean,
            "score": 0,
            "erro": str(err)
        }


def analisar_retencao_csv(caminho_csv: str, duracao_segundos: Optional[float] = None) -> Dict[str, Any]:
    """
    Analisa os dados de retenção de um arquivo CSV exportado do YouTube Studio,
    reutilizando a lógica matemática de yt-retention/retention.py.

    Retorna:
    - points: quantidade de pontos lidos
    - start: porcentagem inicial de retenção
    - hook_leak: perda percentual na janela inicial (primeiros 30s ou 10%)
    - end: porcentagem final retida
    - cliffs: momentos com quedas acentuadas (> 0.8% por intervalo)
    - slide_per_unit: taxa de sangria constante no meio do vídeo
    - status: "healthy" | "leaking" | "severe"
    - recomendacao: ação prática recomendada para o editor.

    Tratamento: valida a existência do arquivo, extensão permitida (.csv),
    integridade das colunas e exige >= 8 pontos de dados.
    """
    if not caminho_csv or not isinstance(caminho_csv, str):
        return {"sucesso": False, "erro": "Caminho do arquivo CSV ausente ou inválido."}

    # Validação estrita de extensão para evitar acesso/leitura arbitrária de outros tipos de arquivos
    if not caminho_csv.lower().endswith(".csv"):
        return {"sucesso": False, "erro": "Formato de arquivo não suportado. Apenas arquivos .csv são permitidos."}

    if not os.path.exists(caminho_csv):
        return {"sucesso": False, "erro": f"Arquivo não encontrado: {caminho_csv}"}

    _garantir_caminho_modulo(PATH_YT_RETENTION)
    try:
        import retention as yt_ret
    except Exception as e:
        logger.error(f"Não foi possível importar retention de {PATH_YT_RETENTION}: {e}")
        return {"sucesso": False, "erro": f"Módulo yt-retention indisponível: {e}"}

    try:
        rows = yt_ret.load_csv(caminho_csv)
    except Exception as e_load:
        return {"sucesso": False, "erro": f"Falha na leitura do CSV: {e_load}"}

    if len(rows) < 8:
        return {
            "sucesso": False,
            "erro": f"Amostra insuficiente: o CSV contém apenas {len(rows)} pontos de retenção (mínimo exigido: 8)."
        }

    xs = [r[0] for r in rows]
    ys = [r[1] for r in rows]
    pct_axis = max(xs) <= 100.5
    dur = float(duracao_segundos) if duracao_segundos is not None else None

    def at(x):
        return (x / 100.0 * dur) if (pct_axis and dur) else x

    start = ys[0] or 100.0
    cutoff = 30.0 if not pct_axis else (30.0 / dur * 100 if dur else 10.0)
    hook_end = min((y for x, y in rows if x <= cutoff), default=start)
    hook_leak = round(start - hook_end, 2)

    drops = []
    for i in range(1, len(rows)):
        d = ys[i - 1] - ys[i]
        span = xs[i] - xs[i - 1] or 1
        drops.append((d / span, xs[i - 1], xs[i], d))
    drops.sort(reverse=True)

    cliffs = [
        {
            "from": round(a1, 2),
            "to": round(b1, 2),
            "lost": round(d, 2),
            "at_seconds": round(at(a1), 1) if (not pct_axis or dur) else None
        }
        for _, a1, b1, d in drops[:5] if d > 0.8
    ]

    mid = [d for d, x0, _, _ in [(r[0], r[1], r[2], r[3]) for r in drops] if x0 > cutoff]
    slide = round(sum(mid) / len(mid), 3) if mid else 0.0

    verdict = "healthy" if hook_leak < 25 else "leaking" if hook_leak < 40 else "severe"

    if verdict == "healthy":
        recomendacao = "Abertura sólida (<25% de perda). O foco deve estar no ritmo e nos cortes do miolo."
    elif verdict == "leaking":
        recomendacao = "Vazamento moderado de abertura. Corte palavras de preenchimento e acelere a revelação nos primeiros 3 segundos."
    else:
        recomendacao = "Vazamento severo (>40%). O gancho inicial falhou em confirmar a expectativa do clique."

    return {
        "sucesso": True,
        "points": len(rows),
        "start": round(start, 2),
        "end": round(ys[-1], 2),
        "hook_leak": hook_leak,
        "cliffs": cliffs,
        "slide_per_unit": slide,
        "verdict": verdict,
        "recomendacao": recomendacao
    }
