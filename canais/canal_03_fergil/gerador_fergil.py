"""
Gerador Autônomo de Vídeos do Canal FERGIL
Nicho: Podcasts, Negócios, Dinheiro, Inteligência Artificial e Mentalidade
Fórmula:
- Locução Profunda (EdgeTTS: pt-BR-AntonioNeural ou pt-BR-FabioNeural)
- Imagens Hiper-Realistas Geradas por IA (Cinematográficas, Tons Escuros/Neon)
- Legendas Dinâmicas Palavra por Palavra com Destaque
- Montagem FFmpeg em 9:16 (Shorts) ou 16:9 (Documentários)
- Upload Direto no YouTube como Não Listado + Maturação
"""

import os
import sys
import json
import uuid
import subprocess
from datetime import datetime
from loguru import logger
import imageio_ffmpeg

from app.services import voice, youtube_uploader
from canais.canal_03_fergil import editorial_fergil

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

DIR_SHORTS = os.path.join("canais", "canal_03_fergil", "videos_prontos", "shorts")
DIR_DOCS = os.path.join("canais", "canal_03_fergil", "videos_prontos", "documentarios")

ROTEIROS_PILOTO = [
    {
        "id": "fergil_short_01",
        "titulo": "A Regra dos 5 Segundos de Elon Musk Para Decisões Milionárias",
        "tipo": "short",
        "duracao_alvo": 35,
        "nicho": "Mentalidade & Liderança",
        "tags": ["fergil", "elonmusk", "mentalidade", "negocios", "produtividade", "shorts"],
        "descricao": "Como Elon Musk decide problemas de alto risco em poucos segundos sem hesitar. Inscreva-se na FERGIL para mais insights de alto valor.",
        "roteiro": (
            "A maioria das pessoas passa semanas adiando uma conversa ou uma decisão que poderia mudar sua vida financeira. "
            "Elon Musk foi questionado em um podcast sobre como ele gerencia cinco empresas bilionárias sem entrar em colapso. "
            "A resposta dele chocou os entrevistadores: 'Se uma decisão não pode matar a empresa hoje, você tem exatamente cinco segundos para executá-la ou descartá-la.' "
            "A indecisão custa mais caro do que o erro. "
            "O erro te dá dados; a dúvida só te dá arrependimento. "
            "Se você quer sair da média e dominar sua mente e seus negócios, inscreva-se na FERGIL e comece a agir hoje."
        )
    },
    {
        "id": "fergil_doc_01",
        "titulo": "O Erro de 1 Bilhão: Por Que Steve Jobs Foi Demitido da Própria Empresa",
        "tipo": "doc",
        "duracao_alvo": 90,
        "nicho": "Estratégia & Negócios",
        "tags": ["fergil", "stevejobs", "apple", "negocios", "estrategia", "documentario"],
        "descricao": "O bastidor real e a lição dolorosa por trás da demissão de Steve Jobs da Apple em 1985. Análise executiva da FERGIL.",
        "roteiro": (
            "Em maio de 1985, o homem que inventou o futuro dos computadores pessoais foi convidado a se retirar do seu próprio escritório. "
            "Steve Jobs não foi derrotado pela concorrência. Ele foi derrubado pelo homem que ele mesmo contratou para administrar a Apple: John Sculley. "
            "Jobs acreditava que a perfeição artística do produto estava acima de qualquer métrica financeira. "
            "O conselho de administração escolheu os lucros a curto prazo. "
            "Jobs passou os meses seguintes em isolamento, sentindo-se um fracasso público. "
            "Mas anos depois, ele revelou o segredo dessa queda: 'Ser demitido da Apple foi a melhor coisa que já me aconteceu. O peso de ser bem-sucedido foi substituído pela leveza de ser um iniciante novamente.' "
            "Foi durante esse exílio que ele criou a NeXT e comprou a Pixar, retornando para salvar a Apple da falência total e transformá-la na empresa mais valiosa do planeta. "
            "A maior lição de negócios de Jobs é brutal: você nunca é grande demais para ser humilhado, mas sua visão tem que ser forte demais para ser destruída. "
            "Inscreva-se na FERGIL. Ideias que transformam."
        )
    }
]

def obter_tema_piloto(tipo: str = "short") -> dict:
    for t in ROTEIROS_PILOTO:
        if t["tipo"] == tipo:
            return t
    return ROTEIROS_PILOTO[0]

if __name__ == "__main__":
    print("Módulo gerador da FERGIL pronto!")
    t = obter_tema_piloto("short")
    print("Tema Carregado:", t["titulo"])
