"""
Agent Reach Scout - Coletor de Inteligência, Notícias Quentes e Bastidores
Inspirado na arquitetura do 'Agent Reach', este módulo extrai:
1. Pautas quentes e debates de bastidores em tempo real (Google News Esportes / Business RSS, feeds internacionais e discussões).
2. Aspas e análises profundas para enriquecer os roteiros de documentários e shorts investigativos.
"""

import os
import re
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger

HEADERS_BROWSER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, text/xml, */*",
}

def extrair_termos_chave(texto: str) -> str:
    """Extrai as 2 ou 3 palavras mais relevantes para garantir que a busca encontre resultados precisos."""
    palavras = re.findall(r'[a-zA-ZÀ-ÿ]{4,}', texto)
    stopwords = {"para", "como", "onde", "qual", "quem", "pelo", "pela", "sobre", "hoje", "jogo", "futebol", "crise", "documentario", "investigativo"}
    relevantes = [p for p in palavras if p.lower() not in stopwords]
    return " ".join(relevantes[:3]) if relevantes else texto[:30]

def scout_noticias_profundas(query: str, categoria: str = "futebol", limit: int = 4) -> List[Dict]:
    """
    Agent Reach: Busca em feeds RSS de alta credibilidade jornalística (Globo Esporte, BBC, Marca, Reuters, Bloomberg).
    """
    items_coletados = []
    termo_limpo = extrair_termos_chave(query)
    
    if categoria == "futebol":
        q = f"{termo_limpo} when:2d"
    else:
        q = f"{termo_limpo} when:3d"
        
    q_enc = urllib.parse.quote(q)
    rss_url = f"https://news.google.com/rss/search?q={q_enc}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    try:
        req = urllib.request.Request(rss_url, headers=HEADERS_BROWSER)
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        for item in root.findall(".//item")[:limit]:
            t = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub_date = item.findtext("pubDate") or ""
            desc = item.findtext("description") or ""
            
            # Limpa HTML da descrição
            desc_limpa = desc.replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
            
            items_coletados.append({
                "origem": "Agent Reach RSS Intelligence",
                "titulo": t,
                "resumo": desc_limpa,
                "link": link,
                "publicado_em": pub_date
            })
    except Exception as e:
        logger.warning(f"Agent Reach Scout erro: {e}")
        
    return items_coletados

def enriquecer_pauta_com_agent_reach(tema: str, canal: str = "futebol") -> Dict:
    """
    Cruza o tema do vídeo com apurações em tempo real para encontrar
    os bastidores e causas ocultas que transformam o vídeo numa aula investigativa.
    """
    noticias_cruzadas = scout_noticias_profundas(query=tema, categoria=canal, limit=3)
    pontos_de_vista = [n["titulo"] for n in noticias_cruzadas]
    
    return {
        "tema": tema,
        "bastidores_encontrados": len(pontos_de_vista) > 0,
        "pontos_de_vista": pontos_de_vista,
        "diretriz_narrativa": (
            f"Fatos recentes e ângulos investigativos apurados pelo Agent Reach: "
            f"{' | '.join(pontos_de_vista[:2])}" if pontos_de_vista else "Aprofunde a análise com ênfase nas causas ocultas, dados e impacto tático/financeiro."
        )
    }
