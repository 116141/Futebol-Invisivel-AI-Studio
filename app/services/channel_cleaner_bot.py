import re
from loguru import logger
from app.services import youtube_uploader, smart_metadata_cleaner, aliexpress_affiliate

def extrair_item_id_aliexpress(url_ou_texto: str) -> str:
    """Extrai o product ID numérico de uma URL ou texto do AliExpress."""
    if not url_ou_texto:
        return ""
    m = re.search(r'(?:item/|productId=)(\d+)', url_ou_texto)
    if m:
        return m.group(1)
    return ""

def converter_url_para_curta_oficial(url: str) -> str:
    """Converte qualquer link longo do AliExpress em https://s.click.aliexpress.com/e/..."""
    if not url:
        return ""
    if "s.click.aliexpress.com/e/" in url:
        return url.strip()
    
    item_id = extrair_item_id_aliexpress(url)
    if item_id:
        clean_url = f"https://pt.aliexpress.com/item/{item_id}.html"
        short = aliexpress_affiliate.generate_short_affiliate_link(clean_url)
        if short and "s.click.aliexpress.com" in short:
            return short
    return aliexpress_affiliate.generate_short_affiliate_link(url)

def varrer_e_corrigir_metadados_canais(canais=None, dry_run=False, limite_videos=30):
    """
    Robô de Higienização & Correção em Lote de Metadados:
    1. Varre os vídeos dos canais especificados (futebol, fergil, moda).
    2. Converte links longos de produto em links curtos oficiais limpos (https://s.click.aliexpress.com/e/...).
    3. Remove marcadores técnicos vazados ([task_id:...]).
    4. Remove capítulos/minutagens falsas (00:00, 01:10) que não batem com o vídeo.
    5. Corrige e remove duplicações de links promocionais ou de afiliados.
    6. Atualiza diretamente via YouTube Data API v3 (videos().update) se dry_run=False.
    """
    if canais is None:
        canais = ["futebol", "fergil", "moda"]
        
    relatorio = {
        "canais_processados": [],
        "total_analisados": 0,
        "videos_com_problema": 0,
        "videos_corrigidos": 0,
        "detalhes": []
    }
    
    for canal in canais:
        canal_res = {
            "canal": canal,
            "analisados": 0,
            "corrigidos": 0,
            "erros": []
        }
        relatorio["canais_processados"].append(canal_res)
        
        try:
            yt = youtube_uploader.get_authenticated_service(canal_nome=canal)
            ch_resp = yt.channels().list(part="contentDetails,snippet", mine=True).execute()
            if not ch_resp.get("items"):
                canal_res["erros"].append("Canal não encontrado ou token inválido")
                continue
                
            uploads_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            nome_canal = ch_resp["items"][0].get("snippet", {}).get("title", canal.upper())
            logger.info(f"[{canal.upper()}] Varrendo canal '{nome_canal}' no YouTube...")
            
            # Puxa os vídeos mais recentes até o limite
            itens = []
            next_page = None
            while len(itens) < limite_videos:
                res = yt.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=uploads_id,
                    maxResults=min(50, limite_videos - len(itens)),
                    pageToken=next_page
                ).execute()
                novos = res.get("items", [])
                if not novos:
                    break
                itens.extend(novos)
                next_page = res.get("nextPageToken")
                if not next_page:
                    break
                    
            canal_res["analisados"] = len(itens)
            relatorio["total_analisados"] += len(itens)
            
            if not itens:
                logger.info(f"[{canal.upper()}] Nenhum vídeo encontrado.")
                continue
                
            video_ids = [it["contentDetails"]["videoId"] for it in itens]
            v_detalhes = {}
            for i in range(0, len(video_ids), 50):
                chunk = video_ids[i:i+50]
                v_res = yt.videos().list(
                    part="snippet,status",
                    id=",".join(chunk)
                ).execute()
                for v in v_res.get("items", []):
                    v_detalhes[v["id"]] = v
                    
            for vid_id in video_ids:
                v_info = v_detalhes.get(vid_id)
                if not v_info:
                    continue
                    
                snippet = v_info.get("snippet", {})
                status = v_info.get("status", {})
                titulo = snippet.get("title", "")
                descricao_atual = snippet.get("description", "")
                
                # Determinar o tipo (short ou doc)
                is_short = "#shorts" in titulo.lower() or "#shorts" in descricao_atual.lower()
                tipo = "short" if is_short else "doc"
                
                # Limpeza e sanitização da descrição
                desc_nova = smart_metadata_cleaner.limpar_descricao_legada(
                    descricao_original=descricao_atual,
                    titulo=titulo,
                    canal=canal,
                    tipo=tipo
                )
                
                # Tratamento específico para Moda: Encurtar link do produto para s.click.aliexpress.com
                if canal == "moda":
                    # Procura qualquer link longo do AliExpress na descrição
                    links_encontrados = re.findall(r'https?://(?:pt\.)?aliexpress\.com/item/[^\s]+', desc_nova)
                    for l_longo in links_encontrados:
                        l_curto = converter_url_para_curta_oficial(l_longo)
                        if l_curto and "s.click.aliexpress.com" in l_curto:
                            desc_nova = desc_nova.replace(l_longo, l_curto)
                            
                    # Remove duplicatas se houver
                    if "Link oficial com desconto exclusivo:" in desc_nova and "🔗 Link Promocional:" in desc_nova:
                        desc_nova = re.sub(r'\n+🔗\s*Link Promocional:\s*https?://[^\s]+', '', desc_nova)
                
                # Checa se houve alteração significativa
                modificado = (desc_nova.strip() != descricao_atual.strip())
                
                if modificado:
                    relatorio["videos_com_problema"] += 1
                    detalhe = {
                        "canal": canal,
                        "video_id": vid_id,
                        "titulo": titulo[:50],
                        "alterado": False
                    }
                    
                    if not dry_run:
                        try:
                            body_update = {
                                "id": vid_id,
                                "snippet": {
                                    "title": titulo,
                                    "description": desc_nova,
                                    "categoryId": snippet.get("categoryId", "17"),
                                    "tags": snippet.get("tags", [])
                                }
                            }
                            yt.videos().update(
                                part="snippet",
                                body=body_update
                            ).execute()
                            
                            canal_res["corrigidos"] += 1
                            relatorio["videos_corrigidos"] += 1
                            detalhe["alterado"] = True
                            logger.success(f"[{canal.upper()}] Vídeo {vid_id} atualizado com link limpo e curto com sucesso!")
                        except Exception as e_up:
                            logger.error(f"Erro ao atualizar vídeo {vid_id} no YouTube: {e_up}")
                            detalhe["erro"] = str(e_up)
                    else:
                        detalhe["alterado"] = False
                        
                    relatorio["detalhes"].append(detalhe)

            if canal_res["corrigidos"] == 0 and not canal_res["erros"]:
                logger.info(f"[{canal.upper()}] Todos os {canal_res['analisados']} vídeos verificados já estão 100% corretos e higienizados!")
                    
        except Exception as e_canal:
            logger.error(f"Erro ao varrer canal {canal}: {e_canal}")
            canal_res["erros"].append(str(e_canal))
            
    return relatorio
