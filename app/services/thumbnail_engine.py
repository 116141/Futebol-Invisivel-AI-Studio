import os
import re
import json
import urllib.request
import urllib.parse
from typing import Optional, Dict
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from loguru import logger
import autoviral_brain
from app.services import youtube_uploader
from googleapiclient.http import MediaFileUpload

THUMBNAIL_DIR = "storage/thumbnails"
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

def _obter_fonte(tamanho: int, estilo: str = "impact") -> ImageFont.FreeTypeFont:
    caminhos = [
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        os.path.join("resource", "fonts", "BeVietnamPro-Bold.ttf")
    ]
    for c in caminhos:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, tamanho)
            except Exception:
                continue
    return ImageFont.load_default()

def _desenhar_texto_com_borda(draw, pos, texto, font, cor_texto, cor_borda=(0, 0, 0), stroke_w=8):
    x, y = pos
    for dx in range(-stroke_w, stroke_w + 1):
        for dy in range(-stroke_w, stroke_w + 1):
            if dx*dx + dy*dy <= stroke_w*stroke_w:
                draw.text((x + dx, y + dy), texto, font=font, fill=cor_borda)
    draw.text(pos, texto, font=font, fill=cor_texto)

def gerar_prompt_capa_ia(titulo: str, canal: str = "futebol", is_doc: bool = True) -> Dict[str, str]:
    """
    Formula o prompt temático hiper-realista e as chamadas de texto estratégicas
    para o gerador de imagem, evitando qualquer repetição.
    """
    limpo = re.sub(r'[^a-zA-Z0-9À-ÖØ-öø-ÿ\s]', ' ', titulo)
    palavras = [p for p in limpo.split() if len(p) > 2]
    protagonista = " ".join(palavras[:2]) if len(palavras) >= 2 else titulo[:25]
    
    aspect_ratio = "16:9" if is_doc else "9:16"
    
    if canal == "futebol":
        prompt_visual = (
            f"Professional YouTube thumbnail for dramatic sports documentary ({aspect_ratio}), ultra-realistic 8k. "
            f"Center focus on intense emotional face expression of {protagonista}, cinematic split lighting (cold blue and intense red/golden highlights). "
            f"Background features locker room tension, confidential secret dossier with 'TOP SECRET / CONFIDENCIAL' stamps, contract papers and tactical board with red strings. "
            f"Photorealistic sports photography, high contrast, extreme detail, blockbuster movie poster quality."
        )
        palavras_chaves = [p.upper() for p in palavras if p.upper() not in ("PARA", "COM", "QUE", "UMA", "NUM", "SOBRE", "EM", "DO", "DA", "NO", "NA")]
        l1 = palavras_chaves[0] if palavras_chaves else "BOMBA"
        l2 = palavras_chaves[1] if len(palavras_chaves) > 1 else "REVELADO!"
        if len(palavras_chaves) > 2 and len(l1) + len(l2) < 14:
            l2 = f"{l2} {palavras_chaves[2]}"
        
        texto_banner = f"{l1} {l2}?!"
        subtitulo = "O PLANO SECRETO" if is_doc else "A VERDADE DOS BASTIDORES"
    else:
        # Moda Alana Cruz
        prompt_visual = (
            f"Luxury fashion editorial YouTube Shorts thumbnail (9:16 vertical), ultra-chic 8k photorealistic. "
            f"Elegant young woman modeling trendy outfit: {protagonista}, walking in luxury penthouse / high-end boutique setting. "
            f"Golden hour soft glamorous lighting, magazine cover aesthetic (Vogue/Harper's Bazaar style), vibrant colors, impeccable fabric textures."
        )
        texto_banner = f"PERFEITO! ✨"
        subtitulo = "LOOK DE LUXO BARATO"

    return {
        "prompt": prompt_visual,
        "texto_banner": texto_banner[:24].upper(),
        "subtitulo": subtitulo[:28].upper(),
        "protagonista": protagonista,
        "aspect_ratio": aspect_ratio
    }

def gerar_capa_tematica_profissional(
    video_id: str,
    titulo: str,
    canal: str = "futebol",
    is_doc: bool = True,
    imagem_base_path: Optional[str] = None
) -> Optional[str]:
    """
    Gera uma miniatura personalizada ultra-profissional e sob medida para o tema do vídeo.
    Se uma imagem base limpa (frame ou foto) for fornecida, aprimora e adiciona o grafismo cinematográfico.
    Salva o arquivo pronto para upload no YouTube.
    """
    try:
        dados_capa = gerar_prompt_capa_ia(titulo, canal=canal, is_doc=is_doc)
        output_filename = f"thumb_{canal}_{video_id}.jpg"
        output_path = os.path.join(THUMBNAIL_DIR, output_filename)
        
        largura, altura = (1280, 720) if is_doc else (720, 1280)
        
        # 1. Obter imagem base (se fornecida ou foto do Wikipedia / frame)
        canvas = None
        if imagem_base_path and os.path.exists(imagem_base_path):
            try:
                base = Image.open(imagem_base_path).convert("RGB")
                # Redimensiona mantendo proporção e corta o centro
                canvas = base.resize((largura, altura), Image.LANCZOS)
            except Exception as e_img:
                logger.warning(f"Erro abrindo imagem base: {e_img}")
        
        if canvas is None:
            # Tenta buscar foto oficial das personalidades citadas no título
            palavras_tit = re.findall(r'[A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)?', titulo)
            foto_baixada = None
            for ent in palavras_tit:
                if ent.lower() in ("para", "com", "uma", "sobre", "futebol", "shorts", "dossiê", "documentário"):
                    continue
                q = urllib.parse.quote(ent)
                urls_wiki = [
                    f"https://pt.wikipedia.org/w/api.php?action=query&titles={q}&prop=pageimages&format=json&pithumbsize=1280",
                    f"https://en.wikipedia.org/w/api.php?action=query&titles={q}&prop=pageimages&format=json&pithumbsize=1280"
                ]
                for url_w in urls_wiki:
                    try:
                        req_w = urllib.request.Request(url_w, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req_w, timeout=4) as resp_w:
                            d_w = json.loads(resp_w.read().decode("utf-8"))
                        pages = d_w.get("query", {}).get("pages", {})
                        for pid, pdata in pages.items():
                            if "thumbnail" in pdata and pdata["thumbnail"].get("source"):
                                img_url = pdata["thumbnail"]["source"]
                                f_temp = os.path.join(THUMBNAIL_DIR, f"temp_{video_id}.jpg")
                                req_img = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                                with urllib.request.urlopen(req_img, timeout=6) as r_img, open(f_temp, "wb") as f_out:
                                    f_out.write(r_img.read())
                                if os.path.exists(f_temp) and os.path.getsize(f_temp) > 10000:
                                    foto_baixada = f_temp
                                    break
                    except Exception:
                        pass
                if foto_baixada:
                    break
            
            if foto_baixada and os.path.exists(foto_baixada):
                base = Image.open(foto_baixada).convert("RGB")
                # Aplica enquadramento no rosto
                canvas = base.resize((largura, altura), Image.LANCZOS)
                try:
                    os.remove(foto_baixada)
                except Exception:
                    pass
            else:
                # Gradiente dramático de fallback caso não haja foto externa
                canvas = Image.new("RGB", (largura, altura), (15, 20, 30))
                draw_bg = ImageDraw.Draw(canvas)
                for i in range(largura):
                    r = int(10 + (i / largura) * 35)
                    b = int(40 - (i / largura) * 20)
                    draw_bg.line([(i, 0), (i, altura)], fill=(r, 15, b))

        # 2. Tratamento Cinematográfico (Contraste + Saturação de Cores)
        enhancer = ImageEnhance.Contrast(canvas)
        canvas = enhancer.enhance(1.25)
        enhancer_c = ImageEnhance.Color(canvas)
        canvas = enhancer_c.enhance(1.20)
        
        # 3. Adicionar Overlay de Luz Dramática e Sombra para Leitura
        overlay = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        
        if is_doc:
            # Gradiente horizontal escuro na esquerda para destacar os textos em 16:9
            for x in range(int(largura * 0.55)):
                alpha = int(220 * (1 - (x / (largura * 0.55))))
                ov_draw.line([(x, 0), (x, altura)], fill=(0, 0, 0, alpha))
        else:
            # Gradiente vertical escuro no topo e rodapé para 9:16
            for y in range(int(altura * 0.35)):
                alpha = int(220 * (1 - (y / (altura * 0.35))))
                ov_draw.line([(0, y), (largura, y)], fill=(0, 0, 0, alpha))
            for y in range(int(altura * 0.65), altura):
                alpha = int(230 * ((y - altura * 0.65) / (altura * 0.35)))
                ov_draw.line([(0, y), (largura, y)], fill=(0, 0, 0, alpha))
                
        canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(canvas)
        
        # 4. Tipografia de Alto Impacto (Padrão YouTube Virais)
        if is_doc:
            font_badge = _obter_fonte(28, "impact")
            font_xl = _obter_fonte(85, "impact")
            font_sub = _obter_fonte(42, "impact")
            
            # Badge de Dossiê / Exclusivo
            draw.rectangle([50, 45, 480, 95], fill=(210, 25, 25))
            draw.text((65, 52), "🔴 DOSSIÊ CONFIDENCIAL", font=font_badge, fill=(255, 255, 255))
            
            # Título Chamativo Gigante
            _desenhar_texto_com_borda(draw, (50, 120), dados_capa["texto_banner"], font_xl, cor_texto=(255, 235, 20), stroke_w=10)
            _desenhar_texto_com_borda(draw, (50, 240), dados_capa["subtitulo"], font_sub, cor_texto=(255, 255, 255), stroke_w=8)
            
            # Logo ou Marca d'Água no Canto Superior Direito
            _desenhar_texto_com_borda(draw, (largura - 320, 45), "FUTEBOL INVISÍVEL", font_badge, cor_texto=(230, 230, 230), stroke_w=4)
        else:
            font_badge = _obter_fonte(32, "impact")
            font_xl = _obter_fonte(78, "impact")
            font_sub = _obter_fonte(48, "impact")
            
            draw.rectangle([40, 60, largura - 40, 130], fill=(210, 25, 25) if canal == "futebol" else (220, 20, 100))
            badge_txt = "🔥 BASTIDORES EXPLOSIVOS" if canal == "futebol" else "✨ ACHADINHO DE LUXO"
            draw.text((65, 75), badge_txt, font=font_badge, fill=(255, 255, 255))
            
            _desenhar_texto_com_borda(draw, (40, 160), dados_capa["texto_banner"], font_xl, cor_texto=(255, 235, 20), stroke_w=10)
            _desenhar_texto_com_borda(draw, (40, altura - 180), dados_capa["subtitulo"], font_sub, cor_texto=(255, 255, 255), stroke_w=8)

        # 5. Salva na máxima qualidade
        canvas.save(output_path, "JPEG", quality=95)
        logger.success(f"Capa temática profissional criada para '{titulo[:30]}': {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Erro gerando capa temática para {video_id}: {e}")
        return None

def aplicar_capa_no_youtube(video_id: str, canal: str, thumbnail_path: str) -> bool:
    """Aplica a thumbnail gerada diretamente no vídeo do YouTube via API."""
    if not os.path.exists(thumbnail_path):
        logger.warning(f"Caminho da thumbnail não existe: {thumbnail_path}")
        return False
    try:
        yt = youtube_uploader.get_authenticated_service(canal)
        yt.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        logger.success(f"Thumbnail aplicada com sucesso no vídeo {video_id} ({canal})!")
        return True
    except Exception as e:
        logger.error(f"Falha ao enviar thumbnail para {video_id}: {e}")
        return False

def auditar_e_gerar_capas_faltantes_canal(canal: str = "futebol", max_videos: int = 50) -> Dict:
    """
    Varre os vídeos do canal. Para qualquer vídeo que esteja Não Listado (ou sem capa personalizada registrada),
    gera automaticamente uma capa única sob medida para o seu tema e faz o upload antes de publicar!
    """
    resultado = {
        "canal": canal,
        "analisados": 0,
        "capas_geradas": 0,
        "erros": 0
    }
    try:
        yt = youtube_uploader.get_authenticated_service(canal)
        res_canal = yt.channels().list(part="contentDetails", mine=True).execute()
        if not res_canal.get("items"):
            return resultado
            
        uploads_id = res_canal["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Puxa os vídeos recentes
        req = yt.playlistItems().list(part="snippet,contentDetails", playlistId=uploads_id, maxResults=min(max_videos, 50))
        res_pl = req.execute()
        itens = res_pl.get("items", [])
        resultado["analisados"] = len(itens)
        
        for item in itens:
            vid_id = item["contentDetails"]["videoId"]
            titulo = item["snippet"]["title"]
            
            # BLINDAGEM MÁXIMA: NUNCA MEXER EM VÍDEOS QUE JÁ ESTÃO PÚBLICOS
            try:
                res_v = yt.videos().list(part="status", id=vid_id).execute()
                v_items = res_v.get("items", [])
                if v_items and v_items[0].get("status", {}).get("privacyStatus") == "public":
                    continue
            except Exception:
                pass
            
            # Checa no banco se já foi gerada capa personalizada oficial para este vídeo
            conn = autoviral_brain.get_conn()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS capas_personalizadas_geradas (
                    video_id TEXT PRIMARY KEY,
                    canal TEXT NOT NULL,
                    titulo TEXT,
                    caminho_capa TEXT,
                    enviado_em TEXT
                )
            """)
            cur.execute("SELECT video_id FROM capas_personalizadas_geradas WHERE video_id = ?", (vid_id,))
            ja_tem = cur.fetchone()
            conn.close()
            
            if ja_tem:
                continue
                
            # Identifica se é Documentário ou Short pela duração e título
            is_doc = ("documentário" in titulo.lower() or "dossiê" in titulo.lower() or "investigação" in titulo.lower())
            
            # Se for Short, formato 9:16 vertical; se for Documentário, formato 16:9 widescreen
            aspect_ratio_txt = "16:9 Widescreen (Documentário)" if is_doc else "9:16 Vertical (Short)"
            logger.info(f"🎨 [CAPAS] Gerando capa profissional sob medida ({aspect_ratio_txt}) para: {vid_id} - '{titulo[:35]}'...")
            caminho_capa = gerar_capa_tematica_profissional(vid_id, titulo, canal=canal, is_doc=is_doc)
            
            if caminho_capa and os.path.exists(caminho_capa):
                sucesso = aplicar_capa_no_youtube(vid_id, canal, caminho_capa)
                if sucesso:
                    resultado["capas_geradas"] += 1
                    conn = autoviral_brain.get_conn()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT OR REPLACE INTO capas_personalizadas_geradas 
                        (video_id, canal, titulo, caminho_capa, enviado_em)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """, (vid_id, canal, titulo, caminho_capa))
                    conn.commit()
                    conn.close()
                else:
                    resultado["erros"] += 1
                    
        return resultado
    except Exception as e:
        logger.error(f"Erro na auditoria de capas do canal {canal}: {e}")
        resultado["erro"] = str(e)
        return resultado
