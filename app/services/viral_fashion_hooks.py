"""
app/services/viral_fashion_hooks.py

Motor de Ganchos Virais e Perguntas ao Algoritmo do YouTube:
Baseado nos maiores outliers de retenção e cliques (CTR) dos feeds de Shorts:
1. Promessa de transformação corporal / caimento ('A peça que MODELA qualquer corpo...')
2. O erro comum / alerta de estilo ('O erro que acaba com o look...')
3. Descoberta de boutique / preço de banana ('Parece de grife de R$ 1.000, mas custou centavos!')
4. Solução de dilema feminino ('A invenção PERFEITA para quem odeia...')
5. Truque infalível de elegância ('O truque simples para ficar elegante sem esforço!')
"""

import random
import re
from typing import Dict, List, Optional
from loguru import logger

FORMULAS_TITULOS_VIRAIS = [
    {
        "id": "modela_corpo",
        "padrao": "A peça que MODELA qualquer corpo sem apertar! ✨",
        "aplicabilidade": ["vestido", "conjunto", "saia", "calca", "calça", "lingerie", "cinta", "meia"]
    },
    {
        "id": "parece_mil_reais",
        "padrao": "Parece de boutique de luxo, mas custou centavos! 😱",
        "aplicabilidade": ["bolsa", "relogio", "relógio", "colar", "joia", "semijoia", "acessorio", "vestido", "sapato"]
    },
    {
        "id": "erro_elegancia",
        "padrao": "O erro que estraga o look elegante de qualquer mulher! ⚠️",
        "aplicabilidade": ["sapato", "salto", "sandalia", "casaco", "sobretudo", "blazer", "vestido"]
    },
    {
        "id": "invencao_perfeita",
        "padrao": "A invenção PERFEITA para o dia a dia que ninguém te conta! 💡",
        "aplicabilidade": ["beleza", "escova", "secador", "organizador", "bolsa", "sapato", "meia"]
    },
    {
        "id": "truque_infalivel",
        "padrao": "O truque INFALÍVEL para parecer elegante sem esforço! ✨",
        "aplicabilidade": ["vestido", "bolsa", "calca", "calça", "camisa", "blazer", "casaco"]
    }
]

def gerar_titulo_viral_shorts(titulo_produto: str, categoria: Optional[str] = None) -> str:
    """
    Gera um título de altíssimo CTR para o feed do YouTube Shorts.
    Prioriza o gancho visual/emocional nos primeiros 35 caracteres.
    """
    t_low = (titulo_produto or "").lower()
    cat = (categoria or "").lower()
    
    # 1. Detecta a categoria se não informada
    if not cat:
        if any(w in t_low for w in ["bolsa", "bag", "carteira", "mochila"]):
            cat = "bolsa"
        elif any(w in t_low for w in ["relogio", "relógio", "brinco", "colar", "joia"]):
            cat = "joia"
        elif any(w in t_low for w in ["sapato", "salto", "sandalia", "sandália", "tenis"]):
            cat = "sapato"
        elif any(w in t_low for w in ["casaco", "sobretudo", "blazer", "cardigan"]):
            cat = "casaco"
        elif any(w in t_low for w in ["escova", "secador", "beleza", "skincare"]):
            cat = "beleza"
        else:
            cat = "vestido"

    # 2. Seleciona fórmulas compatíveis
    compativeis = [f for f in FORMULAS_TITULOS_VIRAIS if any(c in cat for c in f["aplicabilidade"])]
    if not compativeis:
        compativeis = FORMULAS_TITULOS_VIRAIS
        
    formula = random.choice(compativeis)
    gancho = formula["padrao"]
    
    # Adiciona a menção de nicho curta no final mantendo abaixo de 70 caracteres
    titulo_final = f"{gancho} #Shorts"
    if len(titulo_final) > 75:
        titulo_final = titulo_final[:75]
        
    logger.info(f"🎯 [GANCHO VIRAL MODA] Categoria: '{cat}' | Título Gerado: '{titulo_final}'")
    return titulo_final
