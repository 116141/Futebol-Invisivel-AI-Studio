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
    1. EXCLUSIVAMENTE FUTEBOL DE CAMPO (SOCCER / FOOTBALL): SEMPRE adicione a palavra 'football' ou 'soccer' em CADA query de busca para que o YouTube NUNCA retorne jogos de basquete (EuroBasket/FIBA), handebol, vôlei ou futsal!
    2. ANTI-CONTENT ID (PROIBIDO TRANSMISSÃO OFICIAL): NUNCA use termos como 'highlights', 'official', 'Premier League', 'Serie A', 'LaLiga', 'Nations League', 'GW10', 'matchday' ou 'extended highlights'.
    3. APENAS GRAVAÇÕES DE ESTÁDIO / FÃS / SKILLS: Use SEMPRE termos como 'fan view stadium', 'from the stands', 'skills and goals comp', 'tactical cam' ou 'warm up stadium'.
    4. CONFRONTO OU PROTAGONISTA EXATO: Use o nome dos clubes ou jogadores do título + 'football'.

    Responda EXCLUSIVAMENTE em formato JSON:
    {{
        "protagonista": "Nome do time ou jogador central",
        "queries": [
            "Nome do Jogador ou Time football skills comp HD",
            "Nome do Time football fan view stadium atmosphere HD"
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
                q_clean = re.sub(r'(?i)\b(press conference|conference|interview|entrevista|coletiva|podcast|react|classic|clássico|retro|highlights|official|gw\d+|matchday|199\d|200\d|201\d)\b', '', q).strip()
                if q_clean:
                    if "football" not in q_clean.lower() and "soccer" not in q_clean.lower() and "futebol" not in q_clean.lower():
                        q_clean = f"{q_clean} football"
                    limpas.append(q_clean)
            dados["queries"] = limpas
            return dados
    except Exception as e:
        pass

    return {"protagonista": "Futebol", "queries": ["Lamine Yamal football skills comp HD", "Real Madrid football fan view stadium HD"]}
