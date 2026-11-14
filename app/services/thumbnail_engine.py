import os
import re
import json
import random
import subprocess
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


def _extrair_frame_video(video_path: str) -> Optional[Image.Image]:
    """Extrai um frame nítido do vídeo em alta resolução usando FFmpeg."""
    if not video_path or not os.path.exists(video_path):
        return None
    try:
        temp_thumb = os.path.join(THUMBNAIL_DIR, f"temp_frame_{os.getpid()}_{random.randint(1000,9999)}.jpg")
        cmd = [
            "ffmpeg", "-y", "-ss", "00:00:04", "-i", video_path,
            "-vframes", "1", "-q:v", "2", temp_thumb
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
        if os.path.exists(temp_thumb) and os.path.getsize(temp_thumb) > 2000:
            img = Image.open(temp_thumb).convert("RGB")
            try:
                os.remove(temp_thumb)
            except Exception:
                pass
            logger.info(f"📸 Frame real do vídeo extraído com sucesso: {video_path}")
            return img
    except Exception as e:
        logger.debug(f"Aviso ao extrair frame de vídeo: {e}")
    return None


def _gerar_fundo_pollinations(prompt: str, largura: int, altura: int) -> Optional[Image.Image]:
    """Gera arte de fundo cinematográfica 100% gratuita via Pollinations.ai (FLUX/Turbo sem chave de API)."""
    try:
        import io
        clean_p = re.sub(r'[^a-zA-Z0-9\s,]', ' ', prompt)[:200].strip()
        encoded = urllib.parse.quote(clean_p)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width={largura}&height={altura}&model=turbo&nologo=true&seed={random.randint(1, 999999)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=14) as resp:
            data = resp.read()
            if len(data) > 5000:
                img = Image.open(io.BytesIO(data)).convert("RGB")
                logger.info("🎨 Arte cinematográfica de alta resolução gerada via Pollinations.ai ($0.00)!")
                return img
    except Exception as e:
        logger.debug(f"Aviso ao consultar Pollinations.ai: {e}")
    return None


def gerar_prompt_capa_ia(titulo: str, canal: str = "futebol", is_doc: bool = True) -> Dict[str, str]:
    """
    Diretor de Arte com IA: Cria e valida dinamicamente o prompt visual cinematográfico em inglês
    especificamente para motores de difusão (FLUX / Stable Diffusion) e gera a tipografia complementar
    de alto CTR em português.
    """
    aspect_ratio = "16:9" if is_doc else "9:16"
    nome_canal_badge = "FERGIL" if canal == "fergil" else ("ALANA CRUZ" if canal == "moda" else "FUTEBOL INVISÍVEL")

    # Tentativa de Direção Artística Dinâmica via Groq (Llama 3.3 70B)
    try:
        from app.services import llm, dual_ai_editor
        prompt_director = f"""
        Você é o Diretor de Arte de Miniaturas (Thumbnails) do YouTube de maior sucesso do mundo.
        Crie a especificação visual e tipográfica perfeita para o vídeo:
        Título: '{titulo}'
        Canal: {canal} | Formato: {'Documentário 16:9' if is_doc else 'Short 9:16'}

        REGRAS VISUAIS PARA O GERADOR DE IMAGEM (FLUX / STABLE DIFFUSION):
        1. O prompt_imagem DEVE SER EM INGLÊS, altamente cinematográfico (estilo pôster de cinema 8K).
        2. Descreva o protagonista, micro-expressão facial tensa/séria, iluminação dividida (split lighting volumétrica) e cenário atmosférico (chuva leve, névoa, estádio ou vidro de arranha-céu).
        3. REGRA DE COMPOSIÇÃO: O protagonista deve ficar nos dois terços da DIREITA, deixando o terço da ESQUERDA limpo/escuro com espaço negativo para a tipografia.
        4. PROIBIÇÃO ABSOLUTA: Termine sempre instruindo a IA a NÃO desenhar texto ou letras ('photorealistic, cinematic color grading, 85mm lens, shallow depth of field, NO text, NO letters, NO words, NO watermark').
        5. TEXTO DE SOBREPOSIÇÃO (COMPLEMENTAR EM PORTUGUÊS): 2 a 3 palavras curtas de alto impacto que complementam o título sem repeti-lo (ex: 'O ADEUS?!', '1 BILHÃO?!', 'INVESTIGAÇÃO INTERNA').
        6. BADGE (EM PORTUGUÊS): Selo de autoridade do canal (ex: '🔴 DOSSIÊ CONFIDENCIAL', '💼 BASTIDOR EXECUTIVO', '✨ ACHADINHO DE LUXO').

        Responda EXCLUSIVAMENTE em formato JSON:
        {{
            "prompt_imagem": "Hyper-realistic 8k cinematic portrait of...",
            "texto_sobreposicao": "2 a 3 palavras de alto contraste",
            "subtitulo": "subtítulo de contexto curto",
            "badge": "texto do selo superior",
            "protagonista": "nome da figura central"
        }}
        """
        cfg = dual_ai_editor._obter_groq_config()
        resp = llm._generate_response(prompt=prompt_director, app_config=cfg)
        match = re.search(r'\{.*\}', resp, re.DOTALL)
        if match:
            dados_ia = json.loads(match.group(0))
            p_img = str(dados_ia.get("prompt_imagem", "")).strip()
            if "no text" not in p_img.lower():
                p_img += ", photorealistic, cinematic lighting, NO text, NO letters, NO watermark"
            
            t_banner = str(dados_ia.get("texto_sobreposicao", "REVELADO!")).strip().upper()
            t_sub = str(dados_ia.get("subtitulo", "O PLANO SECRETO")).strip().upper()
            t_badge = str(dados_ia.get("badge", "🔴 EXCLUSIVO")).strip().upper()
            prot = str(dados_ia.get("protagonista", titulo[:25])).strip()
            
            logger.info(f"🎨 [DIRETOR IA DE CAPA] Prompt gerado para '{titulo[:30]}...': Texto='{t_banner}' | Prompt={p_img[:50]}...")
            return {
                "prompt": p_img,
                "texto_banner": t_banner[:24],
                "subtitulo": t_sub[:28],
                "badge_txt": t_badge,
                "nome_canal_badge": nome_canal_badge,
                "protagonista": prot,
                "aspect_ratio": aspect_ratio
            }
    except Exception as e_dir:
        logger.warning(f"Aviso no Diretor IA de Capa: {e_dir}. Usando fallback heurístico.")

    # Fallback Heurístico Robusto
    limpo = re.sub(r'[^a-zA-Z0-9À-ÖØ-öø-ÿ\s]', ' ', titulo)
    palavras = [p for p in limpo.split() if len(p) > 2]
    protagonista = " ".join(palavras[:2]) if len(palavras) >= 2 else titulo[:25]
    
    if canal == "futebol":
        prompt_visual = (
            f"Professional sports photojournalism YouTube thumbnail ({aspect_ratio}), ultra-realistic 8k. "
            f"Intense emotional portrait of {protagonista}, dramatic stadium floodlights, lens flare, rain drops, atmospheric smoke, "
            f"confidential dossier stamps and red tactical board lines. Cinematic contrast, extreme detail, blockbuster poster, NO text, NO letters, NO words."
        )
        palavras_chaves = [p.upper() for p in palavras if p.upper() not in ("PARA", "COM", "QUE", "UMA", "NUM", "SOBRE", "EM", "DO", "DA", "NO", "NA")]
        l1 = palavras_chaves[0] if palavras_chaves else "BOMBA"
        l2 = palavras_chaves[1] if len(palavras_chaves) > 1 else "REVELADO!"
        texto_banner = f"{l1} {l2}?!"
        subtitulo = "O PLANO SECRETO" if is_doc else "A VERDADE DOS BASTIDORES"
        badge_txt = "🔴 DOSSIÊ CONFIDENCIAL" if is_doc else "🔥 BASTIDOR EXPLOSIVO"

    elif canal == "fergil":
        prompt_visual = (
            f"Cinematic executive drama YouTube thumbnail ({aspect_ratio}), ultra-realistic 8k. "
            f"Moody atmospheric lighting, powerful corporate boardroom, luxury skyscrapers glass reflections, focus on {protagonista}, "
            f"Wall Street aesthetic, stock charts, subtle gold accents, dark obsidian and deep navy blue tones, high stakes financial power, NO text, NO letters, NO words."
        )
        palavras_chaves = [p.upper() for p in palavras if p.upper() not in ("PARA", "COM", "QUE", "UMA", "NUM", "SOBRE", "EM", "DO", "DA", "NO", "NA")]
        l1 = palavras_chaves[0] if palavras_chaves else "QUEDA"
        l2 = palavras_chaves[1] if len(palavras_chaves) > 1 else "BILIONÁRIA"
        texto_banner = f"{l1} {l2}"
        subtitulo = "ESTUDO DE CASO EXECUTIVO" if is_doc else "MENTALIDADE BILIONÁRIA"
        badge_txt = "💼 BASTIDOR EXECUTIVO" if is_doc else "♟️ ESTRATÉGIA DE PODER"

    else:
        # Moda Alana Cruz
        prompt_visual = (
            f"Luxury fashion editorial YouTube Shorts thumbnail (9:16 vertical), ultra-chic 8k photorealistic. "
            f"Elegant young woman modeling trendy outfit: {protagonista}, walking in luxury penthouse / high-end boutique setting. "
            f"Golden hour soft glamorous lighting, magazine cover aesthetic (Vogue style), vibrant colors, fabric textures, NO text, NO letters, NO words."
        )
        texto_banner = "PERFEITO! ✨"
        subtitulo = "LOOK DE LUXO BARATO"
        badge_txt = "✨ ACHADINHO DE LUXO"

    return {
        "prompt": prompt_visual,
        "texto_banner": texto_banner[:24].upper(),
        "subtitulo": subtitulo[:28].upper(),
        "badge_txt": badge_txt,
        "nome_canal_badge": nome_canal_badge,
        "protagonista": protagonista,
        "aspect_ratio": aspect_ratio
    }


def gerar_capa_tematica_profissional(
    video_id: str,
    titulo: str,
    canal: str = "futebol",
    is_doc: bool = True,
    imagem_base_path: Optional[str] = None,
    video_path: Optional[str] = None,
    caminho_saida_personalizado: Optional[str] = None
) -> Optional[str]:
    """
    Gera uma miniatura personalizada ultra-profissional e sob medida para o tema do vídeo.
    Arquitetura em 3 Camadas a Custo $0.00:
    1. Extração de Frame Real em Alta Resolução do Vídeo renderizado (FFmpeg).
    2. Geração de Arte de Fundo via Pollinations.ai (FLUX / Turbo gratuito e sem limites).
    3. Busca de Foto Oficial em Alta Resolução (Wikipedia/Wikimedia).
    4. Tratamento Cinematográfico e Tipografia de Alto Impacto com Pillow.
    """
    try:
        dados_capa = gerar_prompt_capa_ia(titulo, canal=canal, is_doc=is_doc)
        output_path = caminho_saida_personalizado or os.path.join(THUMBNAIL_DIR, f"thumb_{canal}_{video_id}.jpg")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        largura, altura = (1280, 720) if is_doc else (720, 1280)
        canvas = None

        # Camada 1: Imagem base fornecida diretamente
        if imagem_base_path and os.path.exists(imagem_base_path):
            try:
                base = Image.open(imagem_base_path).convert("RGB")
                canvas = base.resize((largura, altura), Image.LANCZOS)
            except Exception as e_img:
                logger.debug(f"Aviso abrindo imagem base: {e_img}")

        # Camada 2: Extrair frame real em alta definição do próprio vídeo renderizado
        if canvas is None and video_path and os.path.exists(video_path):
            frame_img = _extrair_frame_video(video_path)
            if frame_img:
                canvas = frame_img.resize((largura, altura), Image.LANCZOS)

        # Camada 3: Gerar fundo cinematográfico via IA Gratuita (Pollinations.ai)
        if canvas is None:
            canvas = _gerar_fundo_pollinations(dados_capa["prompt"], largura, altura)

        # Camada 4: Busca de Foto Oficial HD no Wikipedia / Wikimedia
        if canvas is None:
            palavras_tit = re.findall(r'[A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)?', titulo)
            foto_baixada = None
            for ent in palavras_tit:
                if ent.lower() in ("para", "com", "uma", "sobre", "futebol", "shorts", "dossiê", "documentário", "fergil", "investigação"):
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
                canvas = base.resize((largura, altura), Image.LANCZOS)
                try:
                    os.remove(foto_baixada)
                except Exception:
                    pass

        # Camada 5: Fallback gradiente procedural dramático se todas as fontes falharem
        if canvas is None:
            canvas = Image.new("RGB", (largura, altura), (15, 20, 30))
            draw_bg = ImageDraw.Draw(canvas)
            for i in range(largura):
                if canal == "fergil":
                    r = int(12 + (i / largura) * 20)
                    g = int(18 + (i / largura) * 25)
                    b = int(35 + (i / largura) * 40)
                elif canal == "moda":
                    r = int(30 + (i / largura) * 45)
                    g = int(15 + (i / largura) * 15)
                    b = int(30 + (i / largura) * 35)
                else:
                    r = int(10 + (i / largura) * 35)
                    g = 15
                    b = int(40 - (i / largura) * 20)
                draw_bg.line([(i, 0), (i, altura)], fill=(r, g, b))

        # Garante dimensões exatas de tela para a composição gráfica
        if canvas.width != largura or canvas.height != altura:
            canvas = canvas.resize((largura, altura), Image.LANCZOS)

        # Tratamento Cinematográfico (Contraste + Saturação de Cores)
        enhancer = ImageEnhance.Contrast(canvas)
        canvas = enhancer.enhance(1.22)
        enhancer_c = ImageEnhance.Color(canvas)
        canvas = enhancer_c.enhance(1.18)
        
        # Adicionar Overlay de Luz Dramática e Sombra para Leitura
        overlay = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        
        if is_doc:
            # Gradiente horizontal escuro na esquerda para destacar os textos em 16:9
            for x in range(int(largura * 0.58)):
                alpha = int(225 * (1 - (x / (largura * 0.58))))
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
        
        # Cores temáticas por canal
        if canal == "fergil":
            cor_badge_bg = (18, 30, 55)
            cor_badge_texto = (255, 215, 0) # Dourado
            cor_texto_principal = (255, 215, 0) # Dourado vibrante
        elif canal == "moda":
            cor_badge_bg = (210, 30, 90)
            cor_badge_texto = (255, 255, 255)
            cor_texto_principal = (255, 235, 180) # Dourado suave / champanhe
        else:
            cor_badge_bg = (210, 25, 25) # Vermelho alerta
            cor_badge_texto = (255, 255, 255)
            cor_texto_principal = (255, 235, 20) # Amarelo esportivo de alto contraste

        # Tipografia de Alto Impacto
        if is_doc:
            font_badge = _obter_fonte(26, "impact")
            font_xl = _obter_fonte(82, "impact")
            font_sub = _obter_fonte(40, "impact")
            
            # Badge de Dossiê / Exclusivo no topo esquerdo
            badge_largura = 460 if canal != "fergil" else 420
            draw.rectangle([50, 45, 50 + badge_largura, 95], fill=cor_badge_bg)
            draw.text((65, 54), dados_capa["badge_txt"], font=font_badge, fill=cor_badge_texto)
            
            # Título Chamativo Gigante (2-3 palavras complementares)
            _desenhar_texto_com_borda(draw, (50, 115), dados_capa["texto_banner"], font_xl, cor_texto=cor_texto_principal, stroke_w=10)
            _desenhar_texto_com_borda(draw, (50, 235), dados_capa["subtitulo"], font_sub, cor_texto=(255, 255, 255), stroke_w=8)
            
            # Marca do canal no canto superior direito
            _desenhar_texto_com_borda(draw, (largura - 300, 45), dados_capa["nome_canal_badge"], font_badge, cor_texto=(230, 230, 230), stroke_w=4)
        else:
            font_badge = _obter_fonte(32, "impact")
            font_xl = _obter_fonte(74, "impact")
            font_sub = _obter_fonte(44, "impact")
            
            draw.rectangle([40, 60, largura - 40, 130], fill=cor_badge_bg)
            draw.text((65, 75), dados_capa["badge_txt"], font=font_badge, fill=cor_badge_texto)
            
            _desenhar_texto_com_borda(draw, (40, 155), dados_capa["texto_banner"], font_xl, cor_texto=cor_texto_principal, stroke_w=10)
            _desenhar_texto_com_borda(draw, (40, altura - 180), dados_capa["subtitulo"], font_sub, cor_texto=(255, 255, 255), stroke_w=8)

        # Salva na máxima qualidade JPEG
        canvas.save(output_path, "JPEG", quality=95)
        logger.success(f"🎨 [CAPA PRONTA GERADA] '{titulo[:30]}': {output_path}")
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
