from app.services import dual_ai_editor, llm
import json
import re

def gerar_parametros_busca_broll_ia(roteiro: str, titulo: str, canal: str) -> dict:
    """
    A IA (Groq) atua como DIRETOR DE FOTOGRAFIA & B-ROLL CINEMATOGRÁFICO:
    Garante aderência cirúrgica entre o confronto real do título e os vídeos do YouTube.
    """
    if canal == "moda":
        return {"protagonista": titulo, "queries": []}

    prompt = f"""
    Você é o Diretor de Imagem e B-Roll de um canal de YouTube profissional de futebol ('{canal}').
    Estamos no ano de 2026.
    Leia o título da matéria: "{titulo}".

    REGRAS INEGOCIÁVEIS:
    1. CONFRONTO EXATO: As buscas DEVEM ser do confronto ou clubes EXATOS do título (ex: se o jogo for 'Inter de Milão x Como', as buscas DEVEM ser de 'Inter vs Como highlights goals Serie A').
    2. PROIBIÇÃO ABSOLUTA DE OUTROS TIMES: NUNCA crie buscas envolvendo outros adversários (ex: não inclua Barcelona, Fiorentina, Real Madrid).
    3. PROIBIÇÃO DE COLETIVAS: NUNCA use termos de entrevista, coletiva ou podcast. Apenas lances e gols na grama!

    Responda EXCLUSIVAMENTE em formato JSON:
    {{
        "protagonista": "Nome do time ou jogador central",
        "queries": [
            "termo exato do jogo highlights goals HD",
            "termo alternativo com os mesmos times Serie A HD"
        ]
    }}
    """
    try:
        cfg = dual_ai_editor._obter_groq_config()
        resp = llm._generate_response(prompt=prompt, app_config=cfg)
        match = re.search(r'\{.*\}', resp, re.DOTALL)
        if match:
            dados = json.loads(match.group(0))
            limpas = []
            for q in dados.get("queries", []):
                q_clean = re.sub(r'(?i)\b(press conference|conference|interview|entrevista|coletiva|podcast|react|classic|clássico|retro|199\d|200\d|201\d)\b', '', q).strip()
                if q_clean:
                    limpas.append(q_clean)
            dados["queries"] = limpas
            return dados
    except Exception as e:
        pass

    return {"protagonista": "Inter de Milão", "queries": ["Inter Como highlights serie a HD", "Inter vs Como goals highlights HD"]}
