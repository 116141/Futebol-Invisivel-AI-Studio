import os
import sys
import json
import subprocess
from google import genai
from loguru import logger

GEMINI_API_KEY = "AIzaSyCyPvygTtJiC7E4g9BdFnWkgECUGLNm5ak"
GEMINI_MODELS = [
    "gemini-3.1-flash-lite-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.7-flash"
]

VIRAL_CONTENT = [
    {
        "type": "HACK_CELULAR",
        "title": "3 Truques Secretos no Celular que Quase Ninguem Conhece",
        "niche": "Hacks de Celular e Produtividade",
        "hook": "Se você tem celular, precisa ativar essas três funções secretas agora mesmo!",
        "is_product": False,
        "scenes_guide": [
            "Pessoa chocada segurando celular na mao em primeiro plano",
            "Dedo arrastando na barra de espaco do teclado virtual do smartphone",
            "Mao dando dois toques atras do celular e acendendo a lanterna",
            "Navegando nos menus e seguranca de configuracao do celular",
            "Criadora de conteudo sorrindo e apontando para a tela"
        ]
    },
    {
        "type": "CURIOSIDADE_TECH",
        "title": "3 Gadgets Futuristas que Ja Existem e Parecem Magica",
        "niche": "Curiosidades / Tecnologia Futurista",
        "hook": "Essas três invenções parecem ter saído direto de um filme de 2030!",
        "is_product": False,
        "scenes_guide": [
            "Pessoa impressionada olhando um dispositivo tecnologico futurista",
            "Anel inteligente e moderno no dedo com luzes e sensores",
            "Dispositivo eletronico compacto traduzindo fala em tempo real",
            "Teclado virtual a laser projetado em cima de uma mesa",
            "Mulher influencer sorrindo e recomendando com o celular"
        ]
    },
    {
        "type": "ACHADINHO_PROJETOR",
        "title": "Mini Projetor 4K Portatil Magcubic",
        "niche": "Achadinhos / Cinema em Casa",
        "hook": "Como transformar qualquer parede branca em um cinema gigante gastando quase nada!",
        "is_product": True,
        "scenes_guide": [
            "Quarto escuro aconchegante com parede vazia",
            "Mini projetor compacto ligado projetando tela enorme",
            "Assistindo filme ou serie em alta definicao na parede da cama",
            "Pessoa deitada na cama comendo pipoca e assistindo cinema no teto",
            "Mulher sorrindo segurando o celular e convidando para comentar"
        ]
    },
    {
        "type": "ACHADINHO_LUA",
        "title": "Luminaria Lua com Levitacao Magnetica",
        "niche": "Achadinhos / Decoracao Inteligente",
        "hook": "O objeto de decoração mais hipnotizante que eu já comprei na minha vida!",
        "is_product": True,
        "scenes_guide": [
            "Pessoa hipnotizada olhando para um objeto brilhante",
            "Globo em formato de lua flutuando e girando no ar sem fios",
            "Luminaria iluminando um quarto moderno e aconchegante a noite",
            "Mao passando por baixo da lua flutuante mostrando a levitacao magnetica",
            "Criadora de conteudo animada recomendando o produto"
        ]
    }
]

def run_auto(index=0):
    item = VIRAL_CONTENT[index % len(VIRAL_CONTENT)]
    logger.info(f"[ALANA CRUZ - VIRAL PRO] Criando video ({item['type']}): {item['title']}")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    if item['is_product']:
        cta_rule = "CTA final imperativo e persuasivo: 'Comente QUERO que eu te envio o link com desconto exclusivo no direct!'"
    else:
        cta_rule = "CTA final de engajamento forte: 'Já salva esse vídeo pra não perder e me segue para mais dicas da Alana Cruz!'"
        
    scenes_text = "\n".join([f"- Cena {i+1}: {desc}" for i, desc in enumerate(item['scenes_guide'])])
    
    prompt = f"""
    Você é a influenciadora digital Alana Cruz. Você é jovem, carismática, dinâmica e especialista em hacks de tecnologia e achadinhos úteis.
    Seus vídeos são VIRAIS no TikTok e Reels: rápidos, diretos ao ponto, com retenção altíssima nos primeiros 3 segundos.

    Tema do Vídeo: {item['title']}
    Nicho: {item['niche']}
    Gancho Inicial Obrigatório: {item['hook']}

    Sequência exata das 5 cenas visuais que devem aparecer na tela:
{scenes_text}

    REGRAS RÍGIDAS DE ROTEIRO:
    1. A narrativa falada DEVE corresponder EXATAMENTE à sequência das 5 cenas acima (Cena 1 = Gancho, Cena 2 = Ponto 1, Cena 3 = Ponto 2, Cena 4 = Ponto 3, Cena 5 = CTA).
    2. Duração do texto: cerca de 25 a 28 segundos de fala fluida e dinâmica (por volta de 55 a 65 palavras).
    3. Para CADA cena, forneça uma frase de busca em INGLÊS precisa, realista e de alta qualidade para encontrar vídeos correspondentes no banco Pexels (termo focado em ações reais e objetos, evite abstrações).

    Responda EXCLUSIVAMENTE em formato JSON:
    {{
        "video_subject": "{item['title']}",
        "script": "Texto corrido falado por Alana sem marcas de corte",
        "video_terms": [
            "search query in english for scene 1",
            "search query in english for scene 2",
            "search query in english for scene 3",
            "search query in english for scene 4",
            "search query in english for scene 5"
        ]
    }}
    """
    
    data = None
    for model_name in GEMINI_MODELS:
        try:
            logger.info(f"Tentando gerar roteiro com o modelo: {model_name}...")
            response = client.models.generate_content(model=model_name, contents=prompt)
            text = response.text.strip()
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            data = json.loads(text)
            logger.success(f"Roteiro gerado com sucesso via {model_name}!")
            break
        except Exception as e:
            logger.warning(f"Erro ao tentar modelo {model_name}: {e}")

    if not data:
        raise RuntimeError("Nenhum modelo conseguiu gerar o roteiro. Verifique a chave ou conexao.")
    print("\n================ ROTEIRO VIRAL DA ALANA CRUZ ================")
    print(data['script'])
    print("\nTERMOS DE BUSCA DAS 5 CENAS (SEQUENCIAIS):")
    for i, term in enumerate(data['video_terms'], 1):
        print(f"  Cena {i}: {term}")
    print("==============================================================\n")
    
    terms_str = ", ".join(data['video_terms'])
    cmd = [
        sys.executable,
        "cli.py",
        "--video-subject", data['video_subject'],
        "--video-script", data['script'],
        "--video-terms", terms_str,
        "--voice-name", "pt-BR-FranciscaNeural",
        "--video-aspect", "9:16",
        "--video-clip-duration", "3",
        "--video-concat-mode", "sequential",
        "--match-materials-to-script",
        "--font-size", "60",
        "--text-fore-color", "#FFFF00",
        "--stroke-color", "#000000",
        "--stroke-width", "1.5"
    ]
    
    logger.info("Iniciando renderização com alinhamento visual sequencial...")
    subprocess.run(cmd)
    logger.success("PROCESSO CONCLUÍDO! Vídeo gerado com sincronia visual e narrativa!")

if __name__ == '__main__':
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run_auto(idx)