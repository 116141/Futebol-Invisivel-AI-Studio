with open("app/services/autopilot_manager.py", "r", encoding="utf-8") as f:
    text = f.read()

# Substituir a função disparar_producao_video_fergil para usar o novo motor editorial multidimensional
target_func = '''def disparar_producao_video_fergil(is_doc: bool = False):
    """Gera autonomamente um vídeo de alta retenção para a FERGIL (Negócios, Podcasts, IA)."""
    try:
        import app_render_studio
        from canais.canal_03_fergil import editorial_fergil
        
        # 1. Caçador em tempo real: varre notícias recentes de negócios, bilionários e IA
        noticias_reais = autoviral_brain.buscar_oportunidades_negocios_fergil(max_results=10)
        tema_escolhido = None
        for n in noticias_reais:
            t_noticia = n.get("titulo", "")
            if not autoviral_brain.verificar_video_duplicado(t_noticia, "fergil"):
                tema_escolhido = {"titulo": t_noticia, "nicho": "Negócios & IA", "tipo": "short"}
                break

        # 2. Se nenhuma notícia recente passar no filtro de duplicidade, usa a esteira editorial
        if not tema_escolhido:
            temas = editorial_fergil.TEMAS_PILOTO_FERGIL
            for t in temas:
                if not autoviral_brain.verificar_video_duplicado(t["titulo"], "fergil"):
                    tema_escolhido = t
                    break
                    
        if not tema_escolhido:
            logger.info("Todos os temas FERGIL recentes já foram produzidos.")
            return False

        titulo = tema_escolhido["titulo"]
        tipo_v = "doc" if is_doc else "short"
        task_id = str(uuid.uuid4())
        
        dossie = autoviral_brain.gerar_dossie_factual_e_angulo_exclusivo(
            titulo_concorrente=titulo,
            transcricao_concorrente=f"Reflexão executiva profunda sobre {titulo} e psicologia de negócios.",
            url_concorrente="FERGIL Intelligence",
            canal_origem="FERGIL",
            task_id=task_id
        )
        
        res = app_render_studio.iniciar_pipeline_render(
            tipo_video=tipo_v,
            titulo=titulo,
            conteudo_base=f"Tema: {titulo}. Lições de bastidor, poder, finanças e mentalidade aplicáveis.",
            canal_destino="fergil",
            privacidade="unlisted",
            task_id=task_id,
            dossie=dossie
        )
        logger.info(f"Produção FERGIL ({tipo_v}) iniciada: {res}")
        return True
    except Exception as e:
        logger.error(f"Erro na produção de vídeo FERGIL: {e}")
        return False'''

new_func = '''def disparar_producao_video_fergil(is_doc: bool = False):
    """Gera autonomamente um vídeo de altíssima retenção para a FERGIL alternando os 5 pilares estratégicos."""
    try:
        import app_render_studio
        from canais.canal_03_fergil import editorial_fergil
        
        # 1. Obter pautas já produzidas para nunca repetir título ou ângulo
        conn = autoviral_brain.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT titulo FROM videos_gerados WHERE canal = 'fergil'")
        titulos_existentes = [row["titulo"] for row in cur.fetchall()]
        conn.close()

        # 2. Seleção inteligente e variada da esteira dos 5 pilares
        candidatos = [p for p in editorial_fergil.PAUTAS_FERGIL_MULTIDIMENSIONAIS if not autoviral_brain.verificar_video_duplicado(p["titulo"], "fergil")]
        
        tema_escolhido = None
        if candidatos:
            # Alterna aleatoriamente entre os pilares não repetidos
            random.shuffle(candidatos)
            tipo_alvo = "doc" if is_doc else "short"
            compativeis = [c for c in candidatos if c.get("tipo") == tipo_alvo]
            tema_escolhido = compativeis[0] if compativeis else candidatos[0]

        # 3. Fallback: Caçador de notícias de negócios se todas as pautas internas tiverem sido usadas
        if not tema_escolhido:
            noticias_reais = autoviral_brain.buscar_oportunidades_negocios_fergil(max_results=10)
            for n in noticias_reais:
                t_noticia = n.get("titulo", "")
                if not autoviral_brain.verificar_video_duplicado(t_noticia, "fergil"):
                    tema_escolhido = {"titulo": t_noticia, "pilar": "Negócios & IA", "tipo": "doc" if is_doc else "short"}
                    break

        if not tema_escolhido:
            logger.info("Todos os temas FERGIL recentes já foram produzidos. Nenhuma duplicata gerada.")
            return False

        titulo = tema_escolhido["titulo"]
        pilar = tema_escolhido.get("pilar", "Negócios & Alta Performance")
        tipo_v = "doc" if is_doc else "short"
        task_id = str(uuid.uuid4())
        
        logger.info(f"💼 [FERGIL EDITORIAL] Novo tema selecionado (Pilar: {pilar}): '{titulo}' ({tipo_v.upper()})")

        gancho_inicial = tema_escolhido.get("gancho", f"Lição profunda sobre poder, riqueza e tomada de decisões em {titulo}.")
        
        dossie = autoviral_brain.gerar_dossie_factual_e_angulo_exclusivo(
            titulo_concorrente=titulo,
            transcricao_concorrente=f"Pilar: {pilar}. Gancho: {gancho_inicial}. Análise executiva e lições de psicologia de riqueza sobre {titulo}.",
            url_concorrente="FERGIL Intelligence Elite",
            canal_origem="FERGIL",
            task_id=task_id
        )
        
        res = app_render_studio.iniciar_pipeline_render(
            tipo_video=tipo_v,
            titulo=titulo,
            conteudo_base=f"Tema: {titulo}. Pilar: {pilar}. {gancho_inicial} Lições aplicáveis para vida, dinheiro e negócios.",
            canal_destino="fergil",
            privacidade="unlisted",
            task_id=task_id,
            dossie=dossie
        )
        logger.info(f"Produção FERGIL ({tipo_v}) iniciada com sucesso: {res}")
        return True
    except Exception as e:
        logger.error(f"Erro na produção de vídeo FERGIL: {e}")
        return False'''

if target_func in text:
    text = text.replace(target_func, new_func, 1)
    with open("app/services/autopilot_manager.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: autopilot_manager.py atualizado com a esteira dos 5 pilares do FERGIL!")
else:
    print("FAILED: target_func not found in autopilot_manager.py")
