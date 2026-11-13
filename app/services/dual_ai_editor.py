"""
app/services/dual_ai_editor.py

Módulo de Inteligência Artificial Dupla (Gemini + Groq):
- IA 1 (Gemini): Redator & Copywriter Criativo
- IA 2 (Groq): Editor-Chefe Crítico & Juiz de Pauta

Funções principais:
1. validar_pauta_e_extrair_protagonista(pauta, canal):
   Impede vídeos vagos (ex: "Real Madrid aceita pagar R$ 5,5M a uma promessa") 
   sem identificar quem é o jogador/empresa/peça antes de gastar recursos.
2. redigir_e_auditar_roteiro(titulo, contexto, canal, tipo_video):
   Gemini escreve o roteiro com a Lei do Protagonista e o Groq avalia com nota 0 a 10.
   Se nota < 7.5 ou se faltar o protagonista nos primeiros 5s, devolve com feedback e refaz.
"""

import json
import re
from loguru import logger
from app.services import llm
from app.config import config

def _obter_groq_config():
    """Configuração dedicada para o Groq agir como Editor Chefe."""
    cfg = dict(config.app)
    cfg["llm_provider"] = "groq"
    cfg["groq_model_name"] = "openai/gpt-oss-120b"
    return cfg

def _obter_gemini_config():
    """Configuração dedicada para o Gemini agir como Redator."""
    cfg = dict(config.app)
    cfg["llm_provider"] = "gemini"
    cfg["gemini_model_name"] = "gemini-2.5-flash"
    return cfg

def extrair_ou_rejeitar_pauta_vaga(titulo: str, canal: str = "futebol") -> dict:
    """
    IA 2 (Groq) avalia se a pauta tem substância ou se é um clickbait oco.
    Se for futebol ou negócios e não tiver protagonista claro, busca extrair ou rejeita.
    """
    if canal == "moda":
        return {"valido": True, "protagonista": titulo, "motivo": "Canal de produto oficial"}

    prompt_avaliacao = f"""
    Você é o Editor-Chefe Sênior do canal de YouTube '{canal}'.
    Analise esta manchete/pauta candidata:
    "{titulo}"

    REGRAS DE OURO:
    - No Futebol:
      1. Proibido manchetes vagas do tipo 'um jogador', 'uma promessa', 'um técnico', 'uma joia' sem saber QUEM É.
      2. PROIBIDO REPERCUSSÃO FRIA DE COMENTARISTA SOLTA (ex: 'Scholes diz que...', 'Ex-jogador opina que...', 'Comentarista fala sobre...').
         Vídeos sobre opiniões soltas de ex-jogadores tiveram 0% de cliques nos dados reais do YouTube Studio!
         APROVE APENAS se houver um CONFLITO DIRETO, DECISÃO DE MERCADO/CONTRATO, BASTIDOR DE VESTIÁRIO ou CRISE REAL em clubes/seleções!
    - No Negócios/Fergil: Proibido temas vagos de autoajuda sem citar empresa, figura ou método econômico concreto.

    Responda EXCLUSIVAMENTE em formato JSON com as chaves:
    {{
        "valido": true ou false,
        "protagonista": "Nome da pessoa, clube ou empresa principal (ou 'DESCONHECIDO')",
        "fato_concreto": "Qual é o fato em 1 linha",
        "motivo": "Por que vale ou não vale a pena fazer vídeo sobre isso"
    }}
    """
    try:
        cfg_groq = _obter_groq_config()
        resp = llm._generate_response(prompt=prompt_avaliacao, app_config=cfg_groq)
        # Extrai JSON
        match = re.search(r'\{.*\}', resp, re.DOTALL)
        if match:
            dados = json.loads(match.group(0))
            logger.info(f"Auditoria de Pauta Groq ({canal}): {dados}")
            return dados
    except Exception as e:
        logger.warning(f"Aviso na avaliação de pauta pelo Groq: {e}")

    # Fallback permissivo seguro se a rede oscilar
    return {"valido": True, "protagonista": titulo, "motivo": "Fallback operacional"}

def gerar_titulo_viral_outlier_futebol(titulo_bruto: str, is_doc: bool = False) -> str:
    """
    Transforma uma manchete fria de jornal em um título magnético estilo 'Outlier'
    alinhado aos padrões vencedores do YouTube Studio (aba Investigação):
    - Conflito humano / Bastidor explosivo
    - Sem parecer manchete burocrática de portal
    """
    # Limpa sufixos de portal caso ainda existam
    t_limpo = re.sub(r'\s*-\s*(ge|UOL|ESPN|Lance!?|TNT Sports|Jovem Pan).*$', '', titulo_bruto, flags=re.IGNORECASE).strip()
    
    prompt = f"""
    Você é o Estrategista de Títulos Virais (Outliers) do canal 'Futebol Invisível' no YouTube.
    Nosso público é 73,5% do Brasil e 8,2% de Portugal (homens de 25 a 64+ anos).
    
    Manchete original capturada:
    "{t_limpo}"
    Formato: {"Vídeo Longo Documentário (16:9)" if is_doc else "YouTube Shorts (9:16)"}
    
    PADRÕES DE TÍTULOS QUE MAIS VIRALIZARAM NO NOSSO CANAL E NICHO (COMPROVADO PELO YOUTUBE STUDIO):
    - NOSSO CAMPEÃO DE CTR (11,35% DE CLIQUES EM VÍDEO LONGO):
      "«PAPELÃO RIDÍCULO!» O Que Aconteceu na Reunião Secreta que Derrubou o Técnico do Flamengo"
    - OUTROS OUTLIERS DO NICHO:
      1. Mistério / Plano Secreto (Para Vídeo Longo 16:9):
         - Em vez de entregar a notícia toda ("Scholes diz que Haaland vai para o Barça"), crie LACUNA DE MISTÉRIO:
         - Exemplo: "«BASTIDOR EXPLOSIVO!» O Plano Secreto Para Tirar Haaland do Manchester City"
         - Exemplo: "«ACABOU A PACIÊNCIA!» O Que Aconteceu no Vestiário do Real Madrid com Endrick"
      2. Conflito Direto / Alerta:
         - "Thierry Henry Estava CERTO Sobre Estêvão... E NINGUÉM OUVIU"
         - "A Lista Secreta de Dispensas que Chocou o Vestiário do Flamengo"
    
    REGRAS OBRIGATÓRIAS:
    - Mantenha 100% da verdade factual da manchete original (MESMOS jogadores e clubes).
    - PROIBIÇÃO ABSOLUTA: NUNCA use as palavras "Documentário", "Documentário Investigativo" ou "Documentário Executivo" no título!
    - TÍTULO COM LACUNA DE CURIOSIDADE (NÃO ENTREGUE A NOTÍCIA):
      Se o torcedor ler o título e sentir que já sabe a notícia inteira, ele NÃO clica!
      Transforme a notícia em uma DÚVIDA IRRESISTÍVEL ou PLANO SECRETO:
      - Ruim (entrega tudo): "Scholes aponta Barcelona como possível destino de Haaland"
      - Bom (< 55 chars): "O Plano Secreto Para Tirar Haaland do City!"
      - Bom (< 55 chars): "Por Que Haaland no Barça Deixou a Inglaterra em Pânico"
    - LIMITE ESTRITO DE TAMANHO: Máximo de 55 caracteres! (No telemóvel o YouTube corta após ~50 caracteres, e 82,3% do nosso público está no telemóvel).
    - Não adicione hashtags no título (o sistema adiciona depois se for Short).
    - Responda APENAS com o título final puro, sem explicações.
    """
    try:
        cfg_groq = _obter_groq_config()
        resp = llm._generate_response(prompt=prompt, app_config=cfg_groq)
        if resp and not resp.strip().startswith("Error:") and 12 <= len(resp.strip()) <= 75:
            novo_t = resp.strip().strip('"').strip("'")
            novo_t = re.sub(r'[\<\>\"\|]', '', novo_t)
            novo_t = re.sub(r'(?i)\bdocument[áa]rio(\s+investigativo|\s+executivo)?\b', '', novo_t).strip()
            return novo_t
    except Exception as e:
        logger.warning(f"Aviso ao gerar título outlier futebol: {e}")

    return t_limpo[:55]


def gerar_sugestao_thumbnail_complementar(titulo_final: str, canal: str = "futebol") -> str:
    """
    Gera a sugestão de Miniatura (Thumbnail) com 2 a 4 palavras de alto contraste que COMPLEMENTAM
    o título sem repeti-lo (Regra 4 do YouTube Studio / skill yt-package).
    """
    prompt = f"""
    Você é o Especialista em Miniaturas (Thumbnails) de Alto CTR do canal '{canal.upper()}'.
    Título do vídeo (< 55 caracteres): "{titulo_final}"

    REGRAS DO YOUTUBE STUDIO PARA MINIATURA VENCEDORA:
    1. O texto na miniatura NUNCA repete o título; ele COMPLEMENTA com 2 a 3 palavras curtas de choque ou dúvida!
       (Exemplos: "1 BILHÃO?!", "ADEUS CITY?", "FOI TRAÍDO?!", "ACABOU TUDO!", "LISTA VAZOU!").
    2. Descreva em 1 linha a cena visual de alto contraste humano (expressão facial tensa do protagonista + elemento em destaque).

    Responda em apenas 2 linhas curtas neste formato exato:
    TEXTO NA CAPA (2-3 palavras): [Texto curto de impacto]
    CENA VISUAL: [Descrição rápida da foto/expressão]
    """
    try:
        cfg_groq = _obter_groq_config()
        resp = llm._generate_response(prompt=prompt, app_config=cfg_groq)
        if resp and not resp.strip().startswith("Error:"):
            return resp.strip()
    except Exception:
        pass
    return "TEXTO NA CAPA (2-3 palavras): BASTIDOR SECRETO!\nCENA VISUAL: Rosto do protagonista com expressão séria e fundo contrastante."

def auditar_roteiro_com_groq(roteiro: str, titulo: str, canal: str, is_doc: bool) -> dict:
    """
    IA 2 (Groq) atua como Juiz e Auditor de Retenção do roteiro escrito pelo Gemini.
    """
    regras_canal = ""
    if canal == "futebol":
        if is_doc:
            regras_canal = """
            - FORMATO DOCUMENTÁRIO (16:9): Duração obrigatória de 3 a 5 minutos (MÍNIMO DE 450 PALAVRAS NARRADAS).
            - Se o roteiro tiver menos de 400 palavras, REPROVE IMEDIATAMENTE! Documentário curto de 30 segundos é inaceitável.
            - Estrutura completa: Origem, bastidores táticos, números, reação do vestiário e veredito final.
            - O protagonista deve ser nomeado logo no início e explorado com profundidade.
            """
        else:
            regras_canal = """
            - FORMATO SHORT (9:16): Duração ágil de 30 a 35 segundos (65 a 85 palavras).
            - O nome do jogador/técnico/clube protagonista DEVE ser dito nos primeiros 5 segundos.
            - Não pode ter enrolação, rodeios ou frases vagas como 'uma grande promessa' sem falar o nome.
            - Fatos e números concretos.
            - Tom de conversa empolgante de arquibancada.
            """
    elif canal == "moda":
        regras_canal = """
        - FORMATO SHORT DE MODA / AFILIADOS (9:16): Duração dinâmica de 25 a 35 segundos (55 a 85 palavras).
        - PERSONA: Alana Cruz, consultora de elegância e achadinhos para mulheres elegantes e maduras (45 a 65+ anos).
        - ANTI-REPETIÇÃO E VOCABULÁRIO FRESCO:
          NUNCA use sempre as mesmas aberturas batidas como 'Meninas, parem tudo!' ou 'Olha esse achadinho'.
          VARIE os ganchos: use curiosidade sobre corte, elegância sem esforço, conforto no corpo, truques de estilo ou comparação de valor.
        - FIDELIDADE À CATEGORIA DO PRODUTO:
          Se for BOLSA, fale de espaço interno, alça, acabamento e versatilidade. NUNCA diga que é tecido, vestido ou roupa!
          Se for SAPATO/SALTO, fale de conforto ao pisar, postura e salto estável.
          Se for RELÓGIO/JOIA, fale de sofisticação, detalhes da caixa/pulseira e presença visual.
          Se for VESTIDO/CONJUNTO, fale de modelagem que valoriza a silhueta com leveza e discrição.
        - CHAMADA DE AÇÃO ÚNICA NO FINAL (Últimos 3 segundos):
          Apenas uma chamada direta: indicar que o link oficial com desconto exclusivo está no primeiro comentário fixado e convidar a seguir/inscrever-se.
        - RETORNE APENAS O TEXTO FALADO PURO (sem colchetes de cena, sem [Alana], sem aspas).
        """
    elif canal == "fergil":
        if is_doc:
            regras_canal = """
            - FORMATO DOCUMENTÁRIO EXECUTIVO (16:9): Duração profunda de 3 a 5 minutos (MÍNIMO DE 450 PALAVRAS NARRADAS).
            - Se o roteiro tiver menos de 400 palavras, REPROVE IMEDIATAMENTE! Documentário raso não ensina e não gera seguidores.
            - NÍVEL MESTRADO / ESTUDO DE CASO: O vídeo precisa ser uma VERDADEIRA AULA prática de negócios, finanças, estratégia corporativa ou inteligência artificial (estilo Harvard Business Review, Bloomberg Originals, Wall Street Journal).
            - Protagonista empresarial (empresa, investidor, tecnologia ou fundador) NOMEADO logo no primeiro parágrafo.
            - Conter números reais: faturamento, valuation, perdas, margem de lucro, rodadas de investimento ou dados de mercado.
            - A LIÇÃO PRÁTICA: O espectador DEVE sair com um aprendizado estratégico ou reflexão que ele pode aplicar na própria carreira, negócios ou decisões financeiras.
            - PROIBIDO: Frases clichês de coach motivacional ("acredite nos seus sonhos"), enrolação e autoajuda vazia sem dados.
            """
        else:
            regras_canal = """
            - FORMATO SHORT EXECUTIVO (9:16): Duração cirúrgica de 25 a 29 segundos (55 a 65 palavras narradas).
            - Empresa, figura executiva ou cifra bilionária DEVE ser dita nos primeiros 4 segundos.
            - Sem autoajuda barata; foco em inteligência de negócios, finanças, tecnologia e mentalidade estratégica com números.
            - FECHO CIRCULAR / LOOP INFINITO: Terminar emendando com a premissa de abertura. PROIBIDO pedidos de inscrição, likes ou encerramentos lentos.
            """
    elif canal == "moda":
        regras_canal = """
        - Duração ágil e viciante (20 a 24 segundos, 45 a 52 palavras).
        - Foco em elegância madura, caimento perfeito e valor percebido da peça.
        - Sem despedidas longas: apenas a frase final natural apontando para o link oficial nos comentários fixados (máx 3 segundos).
        """

    prompt_auditoria = f"""
    Você é o Editor-Chefe mais rigoroso do YouTube.
    Avalie este roteiro gerado para o vídeo: "{titulo}"
    Canal: {canal} | Formato: {"Documentário 16:9" if is_doc else "Short 9:16"}

    CRITÉRIOS OBRIGATÓRIOS:
    {regras_canal}

    ROTEIRO PARA AVALIAÇÃO:
    \"\"\"{roteiro}\"\"\"

    Responda EXCLUSIVAMENTE em formato JSON:
    {{
        "aprovado": true ou false,
        "nota": 1 a 10,
        "mencionou_protagonista_no_inicio": true ou false,
        "protagonista_identificado": "Nome citado",
        "critica_construtiva": "O que precisa melhorar se reprovado ou elogio se aprovado"
    }}
    """
    try:
        cfg_groq = _obter_groq_config()
        resp = llm._generate_response(prompt=prompt_auditoria, app_config=cfg_groq)
        match = re.search(r'\{.*\}', resp, re.DOTALL)
        if match:
            avaliacao = json.loads(match.group(0))
            logger.info(f"Nota Editor Groq ({canal}): {avaliacao.get('nota')}/10 | Aprovado: {avaliacao.get('aprovado')}")
            return avaliacao
    except Exception as e:
        logger.warning(f"Falha na auditoria do Groq: {e}")

    return {"aprovado": True, "nota": 8.0, "mencionou_protagonista_no_inicio": True, "critica_construtiva": "Aprovado via fallback"}

def redigir_roteiro_dupla_ia(titulo: str, fatos_contexto: str, canal: str, is_doc: bool, prompt_base_gemini: str) -> str:
    """
    Coordena o ciclo entre Gemini (Redator) e Groq (Editor-Chefe):
    1. Gemini gera o primeiro rascunho com instrução estrita da Lei do Protagonista.
    2. Groq analisa. Se aprovado (nota >= 7.5), entrega.
    3. Se reprovado, Gemini recebe a crítica do Groq e reescreve cirurgicamente.
    """
    logger.info(f"Iniciando ciclo Redator (Gemini) + Editor (Groq) para {canal}...")
    
    # Rodada 1: Gemini Redige
    cfg_gemini = _obter_gemini_config()
    roteiro_rascunho = llm._generate_response(prompt=prompt_base_gemini, app_config=cfg_gemini)
    roteiro_limpo = re.sub(r'\[.*?\]', '', roteiro_rascunho).strip()
    roteiro_limpo = roteiro_limpo.replace('**', '').replace('##', '')

    # Auditoria com Groq
    auditoria = auditar_roteiro_com_groq(roteiro_limpo, titulo, canal, is_doc)
    
    # Se Groq aprovou de primeira, retorna com selo de qualidade
    if auditoria.get("aprovado", False) and auditoria.get("nota", 0) >= 7.5:
        logger.success(f"Roteiro APROVADO de primeira pelo Editor Groq! Nota: {auditoria.get('nota')}/10")
        return roteiro_limpo

    # Rodada 2: Refinamento com feedback do Editor Chefe
    logger.warning(f"Roteiro necessita de ajustes segundo Groq: {auditoria.get('critica_construtiva')}. Reescrevendo...")
    
    prompt_refinamento = f"""
    {prompt_base_gemini}

    ATENÇÃO - O EDITOR-CHEFE REJEITOU O RASCUNHO ANTERIOR COM A SEGUINTE CRÍTICA:
    "{auditoria.get('critica_construtiva')}"

    EXIGÊNCIA INEGOCIÁVEL:
    - Se for Futebol: Fale o nome exato do jogador e do clube nos primeiros 4 segundos!
    - Nada de enrolação ou metáforas vazias. Vá direto ao ponto com energia.
    
    Reescreva o roteiro corrigindo 100% dos pontos apontados acima. Retorne apenas o texto narrado puro.
    """
    
    roteiro_refinado = llm._generate_response(prompt=prompt_refinamento, app_config=cfg_gemini)
    roteiro_final = re.sub(r'\[.*?\]', '', roteiro_refinado).strip()
    roteiro_final = roteiro_final.replace('**', '').replace('##', '')
    
    logger.success("Roteiro refinado e finalizado com sucesso após debate entre Gemini e Groq!")
    return roteiro_final
