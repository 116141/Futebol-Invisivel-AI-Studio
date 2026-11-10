import re
from loguru import logger

def gerar_descricao_inteligente(titulo: str, canal: str = "futebol", tipo: str = "doc") -> str:
    """
    Gera uma descrição de alto nível profissional, jornalística e humana:
    1. Sem capítulos fictícios (00:00, 01:10) que não batem com o vídeo.
    2. Sem tags internas técnicas vazando ([task_id:...]).
    3. Com gancho narrativo forte e chamada para ação no canal certo.
    """
    # 1. Tenta gerar via IA (Gemini / Groq)
    try:
        from app.services import llm
        prompt = f"""Você é o editor-chefe do canal esportivo/investigativo '{canal.upper()}'.
Escreva uma descrição profissional, magnética e de altíssima retenção para o YouTube para o seguinte vídeo:
Título: {titulo}
Formato: {'Documentário Investigativo' if tipo == 'doc' else 'Short'}

REGRAS OBRIGATÓRIAS:
- Escreva 2 parágrafos curtos e envolventes explicando o impacto e o contexto desse assunto de forma intrigante.
- NUNCA crie minutagens ou capítulos fictícios (ex: 00:00, 01:10, 02:20). É terminantemente proibido.
- NUNCA inclua dados técnicos do sistema como task_id ou hashes.
- Finalize com uma chamada persuasiva para o público comentar a opinião dele e se inscrever no canal.
- Adicione 4 a 6 hashtags relevantes no final (ex: #futebol #championsleague ou #negocios #fergil).
- Responda APENAS com o texto final da descrição pronto para publicar."""

        desc_ia = llm._generate_response(prompt)
        if desc_ia and not desc_ia.strip().startswith("Error:") and len(desc_ia.strip()) > 80:
            # Higienização de segurança
            desc_limpa = re.sub(r'\[task_id:[^\]]+\]', '', desc_ia)
            desc_limpa = re.sub(r'\d{2}:\d{2}\s*-\s*[^\n]+', '', desc_limpa)
            return desc_limpa.strip()
    except Exception as e:
        logger.warning(f"IA indisponível para descrição, usando gerador editorial dinâmico: {e}")

    # 2. Fallback Editorial Dinâmico de Alta Qualidade (Nunca mais o template engessado)
    if canal == "futebol":
        if tipo == "doc":
            return (
                f"🚨 INVESTIGAÇÃO FUTEBOL INVISÍVEL | {titulo}\n\n"
                f"Neste dossiê especial, vamos a fundo nos bastidores que as transmissões oficiais "
                f"e as coletivas de imprensa tentam abafar. Analisamos os impactos dentro e fora de campo, "
                f"as movimentações da diretoria e como esta crise mexe diretamente com o vestiário e o futuro da temporada.\n\n"
                f"Entenda os detalhes não revelados, as cláusulas em debate e a reação dos principais envolvidos "
                f"nesta reviravolta que promete agitar os jornais esportivos nos próximos dias.\n\n"
                f"💬 Qual é a sua leitura sobre esta apuração? Deixe sua visão sincera nos comentários abaixo!\n"
                f"🔔 Inscreva-se no canal @FutebolInvisivelOficial para não perder os próximos dossiês semanais.\n\n"
                f"#futebol #futebolinvisivel #futebolbrasileiro #championsleague #investigacao #bastidores"
            )
        else:
            return (
                f"🚨 {titulo}!\n\n"
                f"Os bastidores esquentaram e o clima ficou pesado! Acompanhe a apuração completa "
                f"no Futebol Invisível com todos os detalhes e revelações exclusivas.\n\n"
                f"💬 Deixe sua opinião sincera nos comentários e INSCREVA-SE no canal para os próximos desdobramentos!\n\n"
                f"#futebol #shorts #futebolbrasileiro #futebolinvisivel #curiosidades"
            )
    elif canal == "fergil":
        if tipo == "doc":
            return (
                f"💼 FERGIL DOSSIÊ EXECUTIVO | {titulo}\n\n"
                f"Uma análise aprofundada sobre as engrenagens ocultas do dinheiro, mentalidade de alta performance "
                f"e as decisões estratégicas que separam os amadores dos maiores impérios do mercado moderno.\n\n"
                f"Decodificamos os princípios práticos para construir liberdade, patrimônio sólido e vantagem competitiva "
                f"em um cenário econômico em constante mutação.\n\n"
                f"💬 Qual insight desse caso chamou mais a sua atenção? Compartilhe sua visão nos comentários.\n"
                f"🚀 Inscreva-se no canal FERGIL para insights diários sobre negócios, IA e mentalidade financeira.\n\n"
                f"#fergil #negocios #financas #mentalidade #sucesso #investimentos #inteligenciaartificial"
            )
        else:
            return (
                f"💡 {titulo}\n\n"
                f"O insight que muda a sua perspectiva sobre negócios, finanças e tomada de decisão estratégica.\n\n"
                f"🚀 Comente sua visão abaixo e inscreva-se na FERGIL para elevar o seu jogo mental!\n\n"
                f"#fergil #shorts #negocios #mentalidade #investimentos #sucesso"
            )
    else:
        # Moda / Afiliados
        return (
            f"✨ Achadinho Elegante: {titulo} ✨\n\n"
            f"Peça indispensável para quem busca elegância, caimento impecável e acabamento de alto padrão.\n"
            f"Perfeita para valorizar o corpo e elevar qualquer produção com sofisticação e conforto.\n\n"
            f"🛍️ Confira o link oficial promocional nos comentários fixados!\n"
            f"💕 Inscreva-se no canal Alana Cruz para mais achados exclusivos de moda feminina.\n\n"
            f"#modafeminina #vestidofesta #achadinhos #elegancia #lookdodia #alanacruz #shorts"
        )

def limpar_descricao_legada(descricao_original: str, titulo: str, canal: str = "futebol", tipo: str = "doc") -> str:
    """
    Higieniza qualquer descrição antiga antes de enviar ou agendar no YouTube:
    - Remove minutagens falsas (00:00, 01:10, 02:20).
    - Remove o marcador técnico [task_id:...].
    - Remove cabeçalhos duplicados.
    """
    if not descricao_original or len(descricao_original.strip()) < 30:
        return gerar_descricao_inteligente(titulo, canal=canal, tipo=tipo)

    # 1. Remove vazamento de task_id
    texto = re.sub(r'\[task_id:[^\]]+\]', '', descricao_original)

    # 2. Remove blocos de capítulos falsos
    texto = re.sub(r'📌\s*CAPÍTULOS[^\n]*\n(?:[0-9]{2}:[0-9]{2}\s*-[^\n]*\n?)+', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'^[0-9]{2}:[0-9]{2}\s*-[^\n]*\n?', '', texto, flags=re.MULTILINE)

    # 3. Remove frases engessadas antigas
    texto = texto.replace("revelamos a verdade oculta e os bastidores confidenciais que as transmissões oficiais e as coletivas de imprensa não mostram.", "trazemos os bastidores apurados e a análise profunda deste momento decisivo.")

    # 4. Normaliza quebras de linha excessivas
    texto = re.sub(r'\n{3,}', '\n\n', texto).strip()

    if len(texto) < 60:
        return gerar_descricao_inteligente(titulo, canal=canal, tipo=tipo)

    return texto
