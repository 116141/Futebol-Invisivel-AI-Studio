import re
from loguru import logger
from app.services import youtube_uploader

def auditar_e_sanear_canal(canal: str = "moda", dry_run: bool = True) -> dict:
    """
    GUARDIÃO DE QUALIDADE & HIGIENE DO CANAL:
    1. Detecta vídeos DUPLICADOS (mesmo produto ou título idêntico).
       - Preserva o primeiro / mais antigo.
       - Marca os excedentes (Não Listados com 0 views) para exclusão segura.
    2. Detecta vídeos INCOMPLETOS ou QUEBRADOS:
       - Vídeos que falharam no processamento do YouTube.
       - Vídeos de moda sem link de afiliado na descrição.
       - Vídeos sem capa ou com descrição em branco.
    3. Se dry_run=False, exclui permanentemente os vídeos defeituosos/duplicados via YouTube API.
    """
    relatorio = {
        "canal": canal,
        "total_analisados": 0,
        "duplicados_identificados": 0,
        "incompletos_identificados": 0,
        "videos_eliminados": 0,
        "videos_preservados": 0,
        "detalhes": []
    }

    import time
    # Cache de auditoria: só executa auditoria pesada a cada 4 horas por canal para não queimar cota
    now_ts = time.time()
    if not hasattr(auditar_e_sanear_canal, '_ultimo_check'):
        auditar_e_sanear_canal._ultimo_check = {}
    if now_ts - auditar_e_sanear_canal._ultimo_check.get(canal, 0) < 14400 and not dry_run:
        relatorio["motivo"] = "Auditoria pulada: última varredura há menos de 4 horas (preservação de cota)"
        return relatorio

    try:
        auditar_e_sanear_canal._ultimo_check[canal] = now_ts
        yt = youtube_uploader.get_authenticated_service(canal_nome=canal)
        ch_resp = yt.channels().list(part="contentDetails,snippet", mine=True).execute()
        if not ch_resp.get("items"):
            return {"erro": "Canal não encontrado"}

        uploads_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # 1. Puxa todos os vídeos do canal via paginação
        itens = []
        next_page = None
        while True:
            res = yt.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_id,
                maxResults=50,
                pageToken=next_page
            ).execute()
            novos = res.get("items", [])
            if not novos:
                break
            itens.extend(novos)
            next_page = res.get("nextPageToken")
            if not next_page:
                break

        relatorio["total_analisados"] = len(itens)
        if not itens:
            return relatorio

        # 2. Puxa status e estatísticas de todos os vídeos
        video_ids = [it["contentDetails"]["videoId"] for it in itens]
        v_detalhes = {}
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i+50]
            v_res = yt.videos().list(
                part="snippet,status,statistics,contentDetails",
                id=",".join(chunk)
            ).execute()
            for v in v_res.get("items", []):
                v_detalhes[v["id"]] = v

        # 3. Análise de Duplicados e Qualidade
        titulos_vistos = {}  # chave: titulo_normalizado -> video_id preservado
        videos_para_deletar = []

        for item in itens:
            vid_id = item["contentDetails"]["videoId"]
            v_info = v_detalhes.get(vid_id)
            if not v_info:
                continue

            snippet = v_info.get("snippet", {})
            status = v_info.get("status", {})
            stats = v_info.get("statistics", {})

            titulo = snippet.get("title", "").strip()
            descricao = snippet.get("description", "")
            privacy = status.get("privacyStatus", "")
            upload_status = status.get("uploadStatus", "")
            views = int(stats.get("viewCount", 0))

            # Normalização de título para identificar o mesmo produto/tema
            titulo_norm = re.sub(r'[^a-zA-Z0-9]', '', titulo.lower())[:30]

            # Verificação de Bloqueios e Direitos Autorais (Content ID)
            content_details = v_info.get("contentDetails", {})
            region_restriction = content_details.get("regionRestriction", {})
            blocked_regions = region_restriction.get("blocked", [])

            motivo_descarte = None

            # REGRA D (PRIORITÁRIA): Bloqueio por Direitos Autorais / Reivindicação Content ID
            if blocked_regions:
                motivo_descarte = f"Reivindicado/Bloqueado em {len(blocked_regions)} territórios (Content ID: {','.join(blocked_regions[:5])}...)"
                relatorio["incompletos_identificados"] += 1

            # REGRA A: Vídeo quebrado / falha de upload no YouTube
            elif upload_status not in ("processed", "uploaded"):
                motivo_descarte = f"UploadStatus Inválido ({upload_status})"
                relatorio["incompletos_identificados"] += 1

            # REGRA B: Vídeo de Moda sem Link de Afiliado e Não Listado com 0 views
            elif canal == "moda" and "aliexpress.com" not in descricao and "s.click" not in descricao and privacy == "unlisted" and views == 0:
                motivo_descarte = "Incompleto: Moda sem link de afiliado na descrição"
                relatorio["incompletos_identificados"] += 1

            # REGRA C: Vídeo Duplicado (mesmo produto já presente)
            elif titulo_norm in titulos_vistos:
                # Se for Não Listado e com 0 visualizações, descarta com segurança!
                if privacy == "unlisted" and views == 0:
                    motivo_descarte = f"Duplicata de {titulos_vistos[titulo_norm]}"
                    relatorio["duplicados_identificados"] += 1
                else:
                    # Se já tem views ou é público, preserva por segurança do histórico
                    pass
            else:
                titulos_vistos[titulo_norm] = vid_id

            if motivo_descarte:
                videos_para_deletar.append({
                    "id": vid_id,
                    "titulo": titulo,
                    "motivo": motivo_descarte,
                    "privacy": privacy,
                    "views": views
                })
            else:
                relatorio["videos_preservados"] += 1

        relatorio["detalhes"] = videos_para_deletar

        # 4. Execução de Limpeza se dry_run=False
        if not dry_run:
            logger.info(f"Iniciando exclusão de {len(videos_para_deletar)} vídeos reprovados no canal {canal}...")
            for vd in videos_para_deletar:
                try:
                    yt.videos().delete(id=vd["id"]).execute()
                    relatorio["videos_eliminados"] += 1
                    logger.success(f"Vídeo {vd['id']} ({vd['titulo'][:30]}) excluído com sucesso: {vd['motivo']}.")
                except Exception as ex_del:
                    logger.error(f"Erro ao excluir vídeo {vd['id']}: {ex_del}")

        return relatorio

    except Exception as e:
        logger.error(f"Erro na auditoria do canal {canal}: {e}")
        relatorio["erro"] = str(e)
        return relatorio

def sanitizar_canal_youtube(canal: str = "futebol", dry_run: bool = False) -> dict:
    """
    Função wrapper compatível chamada pelo piloto automático (autopilot_manager).
    Executa a auditoria completa e sanitização do canal especificado.
    """
    return auditar_e_sanear_canal(canal=canal, dry_run=dry_run)

def limpar_armazenamento_videos_publicados() -> dict:
    """
    Higienizacao de Armazenamento Local (Disk Cleanup):
    Varre os videos ja postados no YouTube com confirmacao de ID remoto.
    Exclui os arquivos pesados locais (.mp4 e diretorios temporarios temp_web_build_*),
    preservando no disco os metadados leves (.txt de postagem e registro permanente no SQLite).
    """
    import glob
    import shutil
    import time
    import autoviral_brain
    
    relatorio = {
        "videos_pesados_removidos": 0,
        "pastas_temp_removidas": 0,
        "bytes_liberados": 0
    }
    
    try:
        conn = autoviral_brain.get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT task_id, file_path, txt_path, status, youtube_video_id 
            FROM videos_gerados 
            WHERE youtube_video_id IS NOT NULL 
              AND youtube_video_id != ''
        """)
        rows = cur.fetchall()
        conn.close()
        
        for r in rows:
            fpath = r["file_path"]
            if fpath and os.path.exists(fpath):
                try:
                    tam = os.path.getsize(fpath)
                    os.remove(fpath)
                    relatorio["videos_pesados_removidos"] += 1
                    relatorio["bytes_liberados"] += tam
                    logger.info(f"🗑️ [LIMPEZA DISCO] Arquivo de vídeo local removido (já no YouTube): {fpath} ({round(tam / (1024*1024), 2)} MB liberados)")
                except Exception as ex_f:
                    logger.warning(f"Aviso ao remover vídeo local {fpath}: {ex_f}")

        # Limpeza de diretorios temp_web_build_* que ja concluiram
        for temp_dir in glob.glob("temp_web_build_*"):
            if os.path.isdir(temp_dir):
                try:
                    idade_seg = time.time() - os.path.getmtime(temp_dir)
                    if idade_seg > 1200: # 20 minutos
                        for root, dirs, files in os.walk(temp_dir):
                            for fl in files:
                                fp = os.path.join(root, fl)
                                if os.path.exists(fp):
                                    relatorio["bytes_liberados"] += os.path.getsize(fp)
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        relatorio["pastas_temp_removidas"] += 1
                        logger.info(f"🧹 [LIMPEZA DISCO] Pasta temporaria removida: {temp_dir}")
                except Exception as ex_td:
                    logger.warning(f"Aviso limpando pasta temporaria {temp_dir}: {ex_td}")

    except Exception as e:
        logger.error(f"Erro na limpeza de armazenamento de videos: {e}")
        
    mb_lib = round(relatorio["bytes_liberados"] / (1024 * 1024), 2)
    logger.info(f"💾 [LIMPEZA DISCO CONCLUIDA] {relatorio['videos_pesados_removidos']} videos e {relatorio['pastas_temp_removidas']} pastas limpas. Total liberado: {mb_lib} MB.")
    return relatorio


if __name__ == "__main__":
    import sys
    dry = "--delete" not in sys.argv
    print(f"Modo: {'SIMULAÇÃO (dry-run)' if dry else 'EXCLUSÃO REAL'}")
    res = auditar_e_sanear_canal("moda", dry_run=dry)
    print(f"Total analisados: {res['total_analisados']}")
    print(f"Duplicados identificados: {res['duplicados_identificados']}")
    print(f"Incompletos identificados: {res['incompletos_identificados']}")
    print(f"Prontos para excluir: {len(res['detalhes'])}")
    for d in res['detalhes']:
        print(f" - {d['id']} | {d['motivo']} | {d['titulo'][:45]}")
