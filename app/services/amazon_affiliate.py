"""
Módulo Inteligente de Afiliados Amazon - Sistema AutoViral
Gera links de alta conversão, contextualizados com o nicho e tema do vídeo.
Tag oficial configurada: edmilsonferg-20
"""

import os
import re
import urllib.parse
from typing import Dict, List, Optional
from loguru import logger

DEFAULT_AMAZON_TAG = "edmilsonferg-20"

def get_amazon_tag() -> str:
    """Recupera a tag de afiliado Amazon do .env ou usa o default oficial."""
    tag = os.environ.get("AMAZON_ASSOCIATE_TAG")
    if not tag and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("AMAZON_ASSOCIATE_TAG="):
                        tag = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
    return tag or DEFAULT_AMAZON_TAG

# Catálogo Curado de Produtos Campeões de Venda por Nicho / Palavra-chave
CATALOGO_AMAZON_CAMPEOES = {
    "futebol": [
        {
            "palavras_chave": ["tática", "guardiola", "mister", "treinador", "campo", "jogo"],
            "produto": "Guardiola Confidencial (Livro Tático)",
            "asin": "8582850073",
            "busca_fallback": "livro guardiola confidencial",
            "cta": "📖 Livro essencial para entender a mente de Guardiola e a tática moderna:"
        },
        {
            "palavras_chave": ["messi", "cr7", "cristiano", "ronaldo", "lenda", "bola de ouro"],
            "produto": "Lendas do Futebol Mundial - Biografias",
            "asin": "858285043X",
            "busca_fallback": "biografia messi cristiano ronaldo",
            "cta": "⭐ A biografia definitiva e bastidores das lendas do futebol:"
        },
        {
            "palavras_chave": ["chuteira", "bola", "gol", "craque", "treino", "futebol"],
            "produto": "Bola Oficial Campo & Treino Profissional",
            "asin": "B0892DMB1B",
            "busca_fallback": "bola oficial futebol campo",
            "cta": "⚽ Equipamento recomendado para treino e alta performance:"
        }
    ],
    "fergil": [
        {
            "palavras_chave": ["ia", "inteligencia artificial", "chatgpt", "futuro", "tech", "tecnologia"],
            "produto": "A Era da Inteligência Artificial (Best-Seller)",
            "asin": "8501119799",
            "busca_fallback": "livro inteligencia artificial futuro tech",
            "cta": "🤖 O livro mais recomendado sobre o futuro da Inteligência Artificial:"
        },
        {
            "palavras_chave": ["dinheiro", "investimento", "mercado", "riqueza", "negocio", "bilionario"],
            "produto": "A Psicologia Financeira - Lições Intemporais",
            "asin": "8595083274",
            "busca_fallback": "livro psicologia financeira morgan housel",
            "cta": "💡 Leitura indispensável sobre negócios, estratégia e visão de longo prazo:"
        },
        {
            "palavras_chave": ["setup", "produtividade", "fone", "gadget", "computador"],
            "produto": "Fone Headset Bluetooth com Cancelamento de Ruído",
            "asin": "B0863TXGM3",
            "busca_fallback": "fone bluetooth cancelamento ruido alta fidelidade",
            "cta": "🎧 O acessório de produtividade e áudio que usamos nas produções:"
        }
    ],
    "moda": [
        {
            "palavras_chave": ["bolsa", "acessorio", "elegante", "look", "couro"],
            "produto": "Bolsa Feminina Elegante Transversal",
            "asin": "B0C7L7QY7P",
            "busca_fallback": "bolsa feminina transversal couro moderna",
            "cta": "👜 Bolsa tendência que combina com qualquer look sofisticado:"
        },
        {
            "palavras_chave": ["vestido", "verao", "outono", "estilo", "tendencia", "midi"],
            "produto": "Vestido Casual Elegante Tendência",
            "asin": "B09B1F2H5Q",
            "busca_fallback": "vestido feminino elegante casual moda",
            "cta": "✨ O modelo destaque da temporada com entrega rápida:"
        },
        {
            "palavras_chave": ["secador", "escova", "cabelo", "alisadora", "modeladora", "beleza"],
            "produto": "Escova Secadora e Modeladora 5 em 1",
            "asin": "B09KG9X58N",
            "busca_fallback": "escova secadora e modeladora cabelo profissional",
            "cta": "💇‍♀️ Escova secadora e modeladora multifuncional campeã de vendas:"
        },
        {
            "palavras_chave": ["sapato", "salto", "sandalia", "conforto", "calcado", "bota"],
            "produto": "Sapato Conforto Salto Bloco Feminino",
            "asin": "B0892DMB1B",
            "busca_fallback": "sapato salto bloco conforto feminino",
            "cta": "👠 Calçado anatômico e elegante para usar o dia inteiro sem cansar:"
        },
        {
            "palavras_chave": ["casaco", "sobretudo", "cardigan", "blazer", "frio", "inverno"],
            "produto": "Casaco Sobretudo Feminino Alfaiataria",
            "asin": "B08KGT6VBN",
            "busca_fallback": "casaco sobretudo feminino elegante",
            "cta": "🧥 Casaco sobretudo elegante com corte clássico e tecido encorpado:"
        }
    ]
}

def gerar_link_afiliado_amazon(termo_busca: str, asin: Optional[str] = None, tag: Optional[str] = None) -> str:
    """
    Gera uma URL de afiliado Amazon formatada.
    Se tiver ASIN, direciona para o produto exato; caso contrário, para a busca otimizada com comissão.
    """
    aff_tag = tag or get_amazon_tag()
    if asin and len(asin) == 10:
        return f"https://www.amazon.com/dp/{asin}?tag={aff_tag}"
    query = urllib.parse.quote_plus(termo_busca)
    return f"https://www.amazon.com/s?k={query}&tag={aff_tag}"

def selecionar_oferta_inteligente(titulo: str, canal: str) -> Optional[Dict[str, str]]:
    """
    Analisa o título e o nicho do vídeo e escolhe a recomendação de produto com maior chance de venda.
    """
    canal_norm = canal.lower()
    if "futebol" in canal_norm:
        cat_key = "futebol"
    elif "fergil" in canal_norm:
        cat_key = "fergil"
    else:
        cat_key = "moda"

    produtos = CATALOGO_AMAZON_CAMPEOES.get(cat_key, [])
    tit_lower = titulo.lower()

    # Procura match contextual
    for item in produtos:
        for kw in item["palavras_chave"]:
            if kw in tit_lower:
                link = gerar_link_afiliado_amazon(
                    termo_busca=item["busca_fallback"],
                    asin=item.get("asin")
                )
                return {
                    "cta": item["cta"],
                    "produto": item["produto"],
                    "link": link
                }

    # Fallback para o primeiro item de destaque do canal
    if produtos:
        item = produtos[0]
        link = gerar_link_afiliado_amazon(
            termo_busca=item["busca_fallback"],
            asin=item.get("asin")
        )
        return {
            "cta": item["cta"],
            "produto": item["produto"],
            "link": link
        }

    return None

def gerar_comentario_afiliado_amazon(titulo: str, canal: str) -> str:
    """
    Monta o texto completo para fixar no topo do YouTube:
    Combina uma pergunta engajadora (para reter o público) + oferta com link de afiliado.
    """
    oferta = selecionar_oferta_inteligente(titulo, canal)
    canal_norm = canal.lower()

    if not oferta:
        return ""

    if "futebol" in canal_norm:
        return (
            f"🔥 O que acharam deste lance/caso? Concordam com a análise? Deixem o palpite aqui embaixo! 👇⚽\n\n"
            f"{oferta['cta']}\n"
            f"👉 {oferta['link']}"
        )
    elif "fergil" in canal_norm:
        return (
            f"🚀 Qual a sua visão estratégica sobre este documentário? Comente abaixo! 👇💼\n\n"
            f"{oferta['cta']}\n"
            f"👉 {oferta['link']}"
        )
    else:
        return (
            f"✨ Meninas, o que acharam dessa tendência? Usariam no dia a dia? 💖👇\n\n"
            f"{oferta['cta']}\n"
            f"👉 {oferta['link']}"
        )
