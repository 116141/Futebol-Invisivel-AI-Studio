import re
from loguru import logger
from app.services import youtube_uploader
from app.services import amazon_affiliate

def extrair_link_produto_ou_afiliado(descricao: str) -> str:
    """Extrai links do AliExpress ou encurtados da descrição do vídeo."""
    if not descricao:
        return ""
    padrao = r'(https?://(?:[a-zA-Z0-9-]+\.)?(?:aliexpress\.com|s\.click\.aliexpress\.com|amzn\.to|amazon\.[a-z\.]+)/[^\s]+)'
    matches = re.findall(padrao, descricao)
    if matches:
        return matches[0].rstrip('.,;)')
    links_gerais = re.findall(r'https?://[^\s]+', descricao)
    return links_gerais[0].rstrip('.,;)') if links_gerais else ""

def gerar_texto_comentario_otimizado(titulo: str, descricao: str, canal: str = "moda") -> str:
    """Gera comentário de alta conversão ou gancho de debate combinando pergunta e link de afiliado Amazon."""
    # Se já houver link de produto na descrição (ex: moda/aliexpress), prioriza
    link = extrair_link_produto_ou_afiliado(descricao)
    canal_norm = canal.lower()

    if canal_norm == "moda":
        oferta_amz = amazon_affiliate.selecionar_oferta_inteligente(titulo, "moda")
        link_amz = oferta_amz["link"] if oferta_amz else amazon_affiliate.gerar_link_afiliado_amazon(titulo)
        
        if link:
            return (
                f"✨ Meninas, separamos as opções oficiais com desconto antes que esgote:\n\n"
                f"📦 Entrega Rápida (Amazon): {link_amz}\n"
                f"👗 Direto da Fábrica: {link}\n\n"
                f"Qual versão vocês preferem? Deixem nos comentários! 💖👇"
            )
        else:
            coment_amz = amazon_affiliate.gerar_comentario_afiliado_amazon(titulo, "moda")
            if coment_amz:
                return coment_amz
            return "✨ Meninas, qual cor ou tamanho vocês gostariam de ver no próximo vídeo? Deixem aqui nos comentários! 💖"
    
    # Canais FERGIL e FUTEBOL: Usa o motor inteligente de afiliados da Amazon
    coment_amz = amazon_affiliate.gerar_comentario_afiliado_amazon(titulo, canal)
    if coment_amz:
        return coment_amz

    if "fergil" in canal_norm:
        return "💼 Qual a sua visão estratégica sobre este caso? Deixe sua análise nos comentários e inscreva-se na @FERGIL para dominar seus negócios! 👇🚀"
    else:
        tit_lower = titulo.lower()
        if "vini" in tit_lower or "vinicius" in tit_lower:
            return "🚨 Na sua opinião: O Vini Jr foi injustiçado nessa decisão ou a diretoria agiu certo nos bastidores? Deixe seu comentário sincero abaixo! 👇⚽"
        elif "yamal" in tit_lower or "lamine" in tit_lower:
            return "🔥 Com a idade dele, você acha que o Lamine Yamal vai superar a era Messi/CR7 ou a pressão vai pesar? Comente sua visão! 👇"
        elif "modric" in tit_lower:
            return "⚽ Lance inacreditável: foi falha técnica de posicionamento ou mérito total do goleiro? Deixe seu palpite nos comentários! 👇"
        elif "cr7" in tit_lower or "cristiano" in tit_lower:
            return "🏆 O que você faria se estivesse no lugar dele nessa situação? Concorda com a postura do Cristiano? Comente aqui embaixo! 👇"
        elif "messi" in tit_lower:
            return "👀 Esse detalhe de vestiário explica muita coisa... Você concorda com essa reação do Messi? Opine abaixo! 👇"
        else:
            palavras = [p for p in titulo.split() if len(p) > 3][:4]
            assunto = " ".join(palavras) if palavras else "esse caso"
            return f"👀 E para você: qual é a sua opinião sobre {assunto}? Foi decisão certa ou erro grave da diretoria? Comente abaixo! 👇⚽"

def responder_comentarios_inscritos_automatico(canal: str = "futebol", max_respostas: int = 5, max_videos_scan: int = 5) -> dict:
    """
    BOT DE RESPOSTAS INTELIGENTE (OTIMIZADO PARA ECONOMIA DE COTA YOUTUBE API):
    Percorre apenas os vídeos mais recentes do canal (padrão: últimos 5 vídeos) para preservar
    a cota diária de 10.000 unidades para uploads e agendamentos.
    """
    relatorio = {
        "canal": canal,
        "comentarios_respondidos": 0,
        "detalhes": []
    }
    try:
        yt = youtube_uploader.get_authenticated_service(canal_nome=canal)
        ch_resp = yt.channels().list(part="contentDetails,snippet", mine=True).execute()
        if not ch_resp.get("items"):
            return {"erro": "Canal não encontrado"}

        meu_canal_id = ch_resp["items"][0]["id"]
        uploads_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # Busca vídeos recentes cobrindo apenas os últimos max_videos_scan
        todos_itens = []
        next_page = None
        while len(todos_itens) < max_videos_scan:
            vids_resp = yt.playlistItems().list(
                part="snippet",
                playlistId=uploads_id,
                maxResults=min(10, max_videos_scan - len(todos_itens)),
                pageToken=next_page
            ).execute()
            novos = vids_resp.get("items", [])
            if not novos:
                break
            todos_itens.extend(novos)
            next_page = vids_resp.get("nextPageToken")
            if not next_page:
                break
        
        for item in todos_itens:
            vid_id = item["snippet"]["resourceId"]["videoId"]
            titulo = item["snippet"]["title"]

            try:
                threads = yt.commentThreads().list(
                    part="snippet,replies",
                    videoId=vid_id,
                    maxResults=15,
                    order="time"
                ).execute()

                for t in threads.get("items", []):
                    top = t["snippet"]["topLevelComment"]["snippet"]
                    comment_id = t["snippet"]["topLevelComment"]["id"]
                    autor_id = top.get("authorChannelId", {}).get("value", "")
                    autor_nome = top.get("authorDisplayName", "Amigo(a)")
                    texto_user = top.get("textDisplay", "").strip()

                    # Não responder se for o nosso próprio comentário
                    if autor_id == meu_canal_id:
                        continue

                    # Verificar se o canal já respondeu nesta thread
                    ja_respondido = False
                    if "replies" in t:
                        for rep in t["replies"].get("comments", []):
                            rep_autor = rep["snippet"].get("authorChannelId", {}).get("value", "")
                            if rep_autor == meu_canal_id:
                                ja_respondido = True
                                break

                    if not ja_respondido and relatorio["comentarios_respondidos"] < max_respostas:
                        # Gera resposta engajadora
                        if canal == "futebol":
                            respostas_futebol = [
                                f"Excelente ponto, @{autor_nome}! Os bastidores desse caso ainda vão render muito. O que mais te chamou atenção?",
                                f"Concordo com a sua visão, @{autor_nome}! É exatamente esse detalhe que quase ninguém na imprensa percebeu. Tamo junto!",
                                f"Visão cirúrgica, @{autor_nome}! Obrigado por fortalecer o debate aqui no Futebol Invisível. Se inscreva para não perder os próximos capítulos!",
                                f"Comentário de mestre, @{autor_nome}! O vestiário sentiu o impacto dessa decisão na hora. Valeu pela participação!"
                            ]
                            import random
                            texto_resposta = random.choice(respostas_futebol)
                        elif canal == "fergil":
                            respostas_fergil = [
                                f"Análise cirúrgica, @{autor_nome}! No jogo dos grandes negócios, quem antecipa os movimentos domina o mercado. Obrigado pela contribuição!",
                                f"Excelente reflexão, @{autor_nome}! É exatamente essa mentalidade de longo prazo que separa os líderes dos amadores. Tamo junto!",
                                f"Visão perspicaz, @{autor_nome}! O valuation e a estratégia por trás desse caso comprovam o seu ponto. Continue acompanhando a FERGIL!"
                            ]
                            import random
                            texto_resposta = random.choice(respostas_fergil)
                        else:
                            # Moda
                            respostas_moda = [
                                f"Muito obrigada pelo carinho, @{autor_nome}! 💕 O link com desconto tá no comentário fixado. Qualquer dúvida me fala!",
                                f"Fica maravilhoso no corpo, @{autor_nome}! ✨ Tenho certeza que você vai amar! Um beijo enorme da Alana!",
                                f"Que bom que gostou, @{autor_nome}! 💖 Já corre no link fixado antes que acabe a promoção!"
                            ]
                            import random
                            texto_resposta = random.choice(respostas_moda)

                        # Enviar resposta via YouTube API
                        try:
                            yt.comments().insert(
                                part="snippet",
                                body={
                                    "snippet": {
                                        "parentId": comment_id,
                                        "textOriginal": texto_resposta
                                    }
                                }
                            ).execute()

                            relatorio["comentarios_respondidos"] += 1
                            relatorio["detalhes"].append({
                                "video_id": vid_id,
                                "autor": autor_nome,
                                "pergunta_user": texto_user,
                                "resposta_enviada": texto_resposta
                            })
                            logger.info(f"Bot respondeu ao comentário de @{autor_nome} no vídeo {vid_id}.")
                        except Exception as e_resp:
                            logger.warning(f"Erro ao responder comentário {comment_id}: {e_resp}")

            except Exception as e_threads:
                continue

    except Exception as e_total:
        err_msg = str(e_total)
        if "quotaExceeded" in err_msg or "exceeded your" in err_msg:
            logger.warning(f"⏸️ [COTA YOUTUBE] Cota diária da API atingida em '{canal}'. Renovação automática às 07:00 (horário de Cabo Verde / 00:00 PST).")
            relatorio["erro"] = "Cota diária da API do YouTube atingida (renova automaticamente à meia-noite PST / 07:00 CV)."
        else:
            logger.error(f"Erro no bot de respostas: {e_total}")
            relatorio["erro"] = err_msg

    return relatorio

def auditar_e_fixar_comentarios_canal(canal: str = "moda", max_videos: int = 8) -> dict:
    relatorio = {
        "canal": canal,
        "videos_analisados": 0,
        "comentarios_criados": 0,
        "ja_tinham_comentario": 0,
        "detalhes": []
    }

    try:
        yt = youtube_uploader.get_authenticated_service(canal_nome=canal)
        ch_resp = yt.channels().list(part="contentDetails,snippet", mine=True).execute()
        if not ch_resp.get("items"):
            return {"erro": "Nenhum canal associado a esta credencial de autenticação."}

        meu_canal_id = ch_resp["items"][0]["id"]
        uploads_playlist_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # Busca todos os vídeos do canal via paginação (até max_videos)
        itens = []
        next_page_token = None
        while len(itens) < max_videos:
            vids_resp = yt.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_videos - len(itens)),
                pageToken=next_page_token
            ).execute()
            novos = vids_resp.get("items", [])
            if not novos:
                break
            itens.extend(novos)
            next_page_token = vids_resp.get("nextPageToken")
            if not next_page_token:
                break

        relatorio["videos_analisados"] = len(itens)

        for item in itens:
            vid_id = item["snippet"]["resourceId"]["videoId"]
            titulo = item["snippet"]["title"]
            descricao = item["snippet"]["description"]

            tem_comentario_proprio = False
            try:
                threads = yt.commentThreads().list(
                    part="snippet",
                    videoId=vid_id,
                    maxResults=10
                ).execute()

                for t in threads.get("items", []):
                    top = t["snippet"]["topLevelComment"]["snippet"]
                    autor_channel_id = top.get("authorChannelId", {}).get("value", "")
                    if autor_channel_id == meu_canal_id:
                        tem_comentario_proprio = True
                        break
            except Exception as e_threads:
                tem_comentario_proprio = False

            if tem_comentario_proprio:
                relatorio["ja_tinham_comentario"] += 1
                relatorio["detalhes"].append({
                    "video_id": vid_id,
                    "titulo": titulo,
                    "status": "JaPossuiComentarioProprio"
                })
            else:
                texto_comentario = gerar_texto_comentario_otimizado(titulo, descricao, canal=canal)
                try:
                    novo_comentario = yt.commentThreads().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "videoId": vid_id,
                                "topLevelComment": {
                                    "snippet": {
                                        "textOriginal": texto_comentario
                                    }
                                }
                            }
                        }
                    ).execute()

                    comment_id = novo_comentario.get("id")
                    relatorio["comentarios_criados"] += 1
                    relatorio["detalhes"].append({
                        "video_id": vid_id,
                        "titulo": titulo,
                        "status": "ComentarioCriadoEPostado",
                        "texto_comentario": texto_comentario,
                        "comment_id": comment_id
                    })
                except Exception as ex_post:
                    relatorio["detalhes"].append({
                        "video_id": vid_id,
                        "titulo": titulo,
                        "status": f"ErroAoPostar: {str(ex_post)}"
                    })

    except Exception as e:
        relatorio["erro"] = str(e)

    return relatorio
