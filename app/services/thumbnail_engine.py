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

def _desenhar_texto_com_sombra(draw, pos, texto, font, cor_texto, cor_sombra=(0,0,0), offset=(5,5), stroke_w=4, cor_borda=(0,0,0)):
    x, y = pos
    ox, oy = offset
    if offset != (0, 0):
        for dx in range(-stroke_w, stroke_w + 1):
            for dy in range(-stroke_w, stroke_w + 1):
                if dx*dx + dy*dy <= stroke_w*stroke_w:
                    draw.text((x + ox + dx, y + oy + dy), texto, font=font, fill=cor_sombra)
    for dx in range(-stroke_w, stroke_w + 1):
        for dy in range(-stroke_w, stroke_w + 1):
            if dx*dx + dy*dy <= stroke_w*stroke_w:
                draw.text((x + dx, y + dy), texto, font=font, fill=cor_borda)
    draw.text((x, y), texto, font=font, fill=cor_texto)

def _criar_banner_inclinado(texto: str, largura_canvas: int, angulo: float = -3.5) -> Image.Image:
    """Cria uma faixa retangular vermelha inclinada com texto amarelo brilhante estilo vitrine."""
    f_ban = _obter_fonte(int(largura_canvas * 0.080))
    bb_b = f_ban.getbbox(texto)
    bw = (bb_b[2] - bb_b[0]) + int(largura_canvas * 0.10)
    bh = (bb_b[3] - bb_b[1]) + int(largura_canvas * 0.045)
    
    ban_img = Image.new("RGBA", (bw + 50, bh + 40), (0, 0, 0, 0))
    d_b = ImageDraw.Draw(ban_img)
    d_b.rectangle([18, 14, 18 + bw, 14 + bh], fill=(0, 0, 0, 200))
    d_b.rectangle([10, 8, 10 + bw, 8 + bh], fill=(215, 20, 25, 255), outline=(255, 220, 40, 255), width=5)
    _desenhar_texto_com_sombra(d_b, (10 + int(largura_canvas * 0.045), 8 + int(largura_canvas * 0.012)), texto, f_ban, (255, 235, 10), stroke_w=5, cor_borda=(80, 0, 0))
    return ban_img.rotate(angulo, resample=Image.BICUBIC, expand=True)


def _compor_capa_vitrine_afiliado(canvas: Image.Image, dados_capa: Dict[str, str]) -> Image.Image:
    """Compõe a vitrine de alta conversão idêntica ao benchmark de bolsas/moda."""
    w, h = canvas.size
    
    # 1. Overlay superior escuro para leitura perfeita do título
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(ov)
    for y in range(int(h * 0.22)):
        alpha = int(170 * (1 - y / (h * 0.22)))
        d_ov.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    canvas_rgba = Image.alpha_composite(canvas.convert("RGBA"), ov)
    
    # 2. Linha 1: Texto Superior Branco em Caixa Alta
    linha1 = dados_capa.get("linha1", "ACHADINHO DE LUXO")
    f_l1 = _obter_fonte(int(h * 0.038))
    bb = f_l1.getbbox(linha1)
    if (bb[2] - bb[0]) > w * 0.85:
        f_l1 = _obter_fonte(int(h * 0.030))
        bb = f_l1.getbbox(linha1)
    x1 = (w - (bb[2] - bb[0])) // 2
    y1 = int(h * 0.030)
    _desenhar_texto_com_sombra(ImageDraw.Draw(canvas_rgba), (x1, y1), linha1, f_l1, (255, 255, 255), stroke_w=6)
    
    # 3. Linha 2: Faixa Inclinada Vermelha com Texto Amarelo
    linha2 = dados_capa.get("linha2_banner", "PERFEITO!")
    ban_rot = _criar_banner_inclinado(linha2, w, angulo=-3.5)
    canvas_rgba.paste(ban_rot, ((w - ban_rot.width) // 2, int(h * 0.082)), ban_rot)
    
    # 4. Selo Circular 'OFERTA LIMITADA!' (Topo Esquerdo)
    selo_path = "resource/templates/selo_sticker.png"
    if os.path.exists(selo_path):
        selo = Image.open(selo_path).convert("RGBA")
        selo_sz = int(w * 0.28)
        selo = selo.resize((selo_sz, selo_sz), Image.LANCZOS)
        canvas_rgba.paste(selo, (int(w * 0.05), int(h * 0.18)), selo)
        
    # 5. Preço em Destaque no Topo Direito
    preco = dados_capa.get("preco", "Apenas R$ 149,90!")
    f_pr = _obter_fonte(int(h * 0.034))
    b_pr = f_pr.getbbox(preco)
    _desenhar_texto_com_sombra(ImageDraw.Draw(canvas_rgba), (w - (b_pr[2] - b_pr[0]) - int(w * 0.06), int(h * 0.21)), preco, f_pr, (255, 235, 10), stroke_w=5)
    
    # 6. Callout 'GARANTA O SEU!' na Direita Inferior
    cta_path = "resource/templates/cta_sticker.png"
    if os.path.exists(cta_path):
        cta = Image.open(cta_path).convert("RGBA")
        cta_w = int(w * 0.38)
        cta_h = int(cta.height * (cta_w / cta.width))
        cta = cta.resize((cta_w, cta_h), Image.LANCZOS)
        canvas_rgba.paste(cta, (w - cta_w - int(w * 0.04), int(h * 0.69)), cta)
    else:
        f_cta = _obter_fonte(int(h * 0.028))
        txt_cta = dados_capa.get("texto_cta", "GARANTA O SEU!")
        b_cta = f_cta.getbbox(txt_cta)
        cw = (b_cta[2] - b_cta[0]) + int(w * 0.08)
        ch = (b_cta[3] - b_cta[1]) + int(h * 0.018)
        cta_img = Image.new("RGBA", (cw + 30, ch + 30), (0, 0, 0, 0))
        d_c = ImageDraw.Draw(cta_img)
        d_c.rectangle([12, 10, 12 + cw, 10 + ch], fill=(0, 0, 0, 180))
        d_c.rectangle([8, 6, 8 + cw, 6 + ch], fill=(255, 225, 10, 255), outline=(0, 0, 0, 255), width=4)
        _desenhar_texto_com_sombra(d_c, (8 + int(w * 0.04), 6 + int(h * 0.005)), txt_cta, f_cta, (0, 0, 0), stroke_w=0, offset=(0,0))
        cta_rot = cta_img.rotate(4, resample=Image.BICUBIC, expand=True)
        canvas_rgba.paste(cta_rot, (w - cta_rot.width - int(w * 0.04), int(h * 0.73)), cta_rot)
    
    # 7. Rodapé de Conversão
    footer_path = "resource/templates/boutique_full_footer.png"
    if os.path.exists(footer_path):
        ft = Image.open(footer_path).convert("RGBA")
        ft_h = int(h * 0.17)
        ft_w = w
        ft = ft.resize((ft_w, ft_h), Image.LANCZOS)
        canvas_rgba.paste(ft, (0, h - ft_h), ft)
        
    return canvas_rgba.convert("RGB")


def _compor_capa_dossie_futebol(canvas: Image.Image, dados_capa: Dict[str, str], is_doc: bool = False) -> Image.Image:
    """Compõe a capa estilo Dossiê Investigativo com corkboard oficial à direita."""
    w, h = canvas.size
    canvas_rgba = canvas.convert("RGBA")
    
    # 1. Aplicar o Corkboard de Investigação na metade direita
    tpl_cork = "resource/templates/dossie_corkboard_doc.png" if is_doc else "resource/templates/dossie_corkboard_short.png"
    if os.path.exists(tpl_cork):
        cork = Image.open(tpl_cork).convert("RGBA")
        if is_doc:
            target_w = int(w * 0.44)
            cork_resized = cork.resize((target_w, h), Image.LANCZOS)
            x_paste = w - target_w
            y_paste = 0
        else:
            target_w = int(w * 0.48)
            target_h = int(h * 0.78)
            cork_resized = cork.resize((target_w, target_h), Image.LANCZOS)
            x_paste = w - target_w
            y_paste = int(h * 0.18)
            
        mask_cork = Image.new("L", cork_resized.size, 255)
        d_mc = ImageDraw.Draw(mask_cork)
        fade_w = int(cork_resized.width * 0.22)
        for fx in range(fade_w):
            alpha = int(255 * (fx / fade_w))
            d_mc.line([(fx, 0), (fx, cork_resized.height)], fill=alpha)
            
        canvas_rgba.paste(cork_resized, (x_paste, y_paste), mask_cork)
        
    # 2. Vinheta e Sombra de Contraste para Tipografia no Topo
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(ov)
    fade_top_h = int(h * 0.32)
    for y in range(fade_top_h):
        alpha = int(220 * (1 - y / fade_top_h))
        d_ov.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    canvas_rgba = Image.alpha_composite(canvas_rgba, ov)
    
    d = ImageDraw.Draw(canvas_rgba)
    
    # 3. Badge Superior de Dossiê
    badge_txt = dados_capa.get("badge_txt", "🔴 DOSSIÊ CONFIDENCIAL")
    f_badge = _obter_fonte(int(h * 0.024) if is_doc else int(h * 0.020))
    bb_badge = f_badge.getbbox(badge_txt)
    badge_w = (bb_badge[2] - bb_badge[0]) + int(w * 0.05)
    badge_h = (bb_badge[3] - bb_badge[1]) + int(h * 0.012)
    
    bx = int(w * 0.05)
    by = int(h * 0.035)
    d.rectangle([bx + 4, by + 4, bx + badge_w + 4, by + badge_h + 4], fill=(0, 0, 0, 180))
    d.rectangle([bx, by, bx + badge_w, by + badge_h], fill=(200, 20, 20, 255), outline=(255, 255, 255, 255), width=2)
    d.text((bx + int(w * 0.025), by + int(h * 0.003)), badge_txt, font=f_badge, fill=(255, 255, 255))
    
    # 4. Linha 1: Título de Alto Impacto em Amarelo Ouro
    tit_amarelo = dados_capa.get("titulo_amarelo", dados_capa.get("texto_banner", "BOMBA NO FUTEBOL!"))
    f_l1 = _obter_fonte(int(h * 0.062) if is_doc else int(h * 0.046))
    bb1 = f_l1.getbbox(tit_amarelo)
    if (bb1[2] - bb1[0]) > w * 0.88:
        f_l1 = _obter_fonte(int(h * 0.048) if is_doc else int(h * 0.038))
        bb1 = f_l1.getbbox(tit_amarelo)
    y_l1 = by + badge_h + int(h * 0.015)
    _desenhar_texto_com_sombra(d, (bx, y_l1), tit_amarelo, f_l1, (255, 225, 10), stroke_w=6)
    
    # 5. Linha 2 e 3: Punchline em Branco e Vermelho
    p_branca = dados_capa.get("punchline_branca", dados_capa.get("subtitulo", "A VERDADE DOS BASTIDORES"))
    f_l2 = _obter_fonte(int(h * 0.045) if is_doc else int(h * 0.036))
    y_l2 = y_l1 + (bb1[3] - bb1[1]) + int(h * 0.012)
    _desenhar_texto_com_sombra(d, (bx, y_l2), p_branca, f_l2, (255, 255, 255), stroke_w=5)
    
    p_vermelha = dados_capa.get("punchline_vermelha", "")
    if p_vermelha:
        f_l3 = _obter_fonte(int(h * 0.045) if is_doc else int(h * 0.036))
        y_l3 = y_l2 + int(h * 0.042)
        _desenhar_texto_com_sombra(d, (bx, y_l3), p_vermelha, f_l3, (235, 30, 30), stroke_w=5)
        
    return canvas_rgba.convert("RGB")


def _compor_capa_executiva_fergil(canvas: Image.Image, dados_capa: Dict[str, str], is_doc: bool = True) -> Image.Image:
    """Compõe a capa corporativa / Wall Street para o canal FERGIL."""
    w, h = canvas.size
    canvas_rgba = canvas.convert("RGBA")
    
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(ov)
    if is_doc:
        for x in range(int(w * 0.60)):
            alpha = int(220 * (1 - x / (w * 0.60)))
            d_ov.line([(x, 0), (x, h)], fill=(8, 14, 25, alpha))
    else:
        for y in range(int(h * 0.35)):
            alpha = int(220 * (1 - y / (h * 0.35)))
            d_ov.line([(0, y), (w, y)], fill=(8, 14, 25, alpha))
    canvas_rgba = Image.alpha_composite(canvas_rgba, ov)
    
    d = ImageDraw.Draw(canvas_rgba)
    
    badge_txt = dados_capa.get("badge_txt", "💼 BASTIDOR EXECUTIVO")
    f_badge = _obter_fonte(int(h * 0.024) if is_doc else int(h * 0.020))
    bb_badge = f_badge.getbbox(badge_txt)
    badge_w = (bb_badge[2] - bb_badge[0]) + int(w * 0.05)
    badge_h = (bb_badge[3] - bb_badge[1]) + int(h * 0.012)
    
    bx = int(w * 0.05)
    by = int(h * 0.040)
    d.rectangle([bx, by, bx + badge_w, by + badge_h], fill=(18, 30, 55, 255), outline=(255, 215, 0, 255), width=2)
    d.text((bx + int(w * 0.025), by + int(h * 0.003)), badge_txt, font=f_badge, fill=(255, 215, 0))
    
    tit = dados_capa.get("titulo_amarelo", dados_capa.get("texto_banner", "PODER & ESTRATÉGIA"))
    f_xl = _obter_fonte(int(h * 0.065) if is_doc else int(h * 0.048))
    y_xl = by + badge_h + int(h * 0.018)
    _desenhar_texto_com_sombra(d, (bx, y_xl), tit, f_xl, (255, 215, 0), stroke_w=6, cor_borda=(10, 15, 30))
    
    sub = dados_capa.get("subtitulo", "ESTUDO DE CASO EXECUTIVO")
    f_sub = _obter_fonte(int(h * 0.038) if is_doc else int(h * 0.032))
    y_sub = y_xl + int(h * 0.075) if is_doc else y_xl + int(h * 0.055)
    _desenhar_texto_com_sombra(d, (bx, y_sub), sub, f_sub, (255, 255, 255), stroke_w=5)
    
    _desenhar_texto_com_sombra(d, (w - int(w * 0.22), by), "FERGIL", f_badge, (220, 220, 220), stroke_w=3)
    
    return canvas_rgba.convert("RGB")


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
    de alto CTR em português, alinhada aos benchmarks de cada canal.
    """
    aspect_ratio = "16:9" if is_doc else "9:16"
    nome_canal_badge = "FERGIL" if canal == "fergil" else ("ALANA CRUZ" if canal == "moda" else "FUTEBOL INVISÍVEL")

    # Tentativa de Direção Artística Dinâmica via Groq (Llama 3.3 70B)
    try:
        from app.services import llm, dual_ai_editor
        
        if canal == "moda":
            prompt_director = f"""
            Você é o Diretor de Arte de Miniaturas de Moda e Achadinhos (Alana Cruz).
            Crie a especificação visual e tipográfica perfeita para o vídeo:
            Título: '{titulo}'
            
            REGRAS VISUAIS:
            1. prompt_imagem (EM INGLÊS): Wide shot of elegant smiling model from waist to knees on an illuminated gold pedestal stage, warm golden bokeh particles, luxury boutique background, top 35% empty dark negative space with gentle sparkling gold dust, photorealistic 8k, NO text, NO letters, NO words, NO watermark.
            2. linha1: 2 a 3 palavras brancas no topo (ex: 'O VESTIDO', 'A BOLSA', 'RELÓGIO DE LUXO', 'O CONJUNTO').
            3. linha2_banner: Palavra de impacto no banner vermelho (ex: 'PERFEITO!', 'DE LUXO!', 'IMPECÁVEL!', 'DESEJO!').
            4. preco: Preço chamativo (ex: 'Apenas R$ 149,90!' ou 'Apenas R$ 108,88!').
            5. texto_cta: 'GARANTA O SEU!' ou 'GARANTA A SUA!'.
            
            Responda EXCLUSIVAMENTE em formato JSON:
            {{
                "prompt_imagem": "...",
                "linha1": "O VESTIDO",
                "linha2_banner": "PERFEITO!",
                "preco": "Apenas R$ 149,90!",
                "texto_cta": "GARANTA O SEU!"
            }}
            """
        elif canal == "futebol":
            prompt_director = f"""
            Você é o Diretor de Arte do canal Futebol Invisível.
            Crie a especificação visual estilo Dossiê Investigativo para:
            Título: '{titulo}' | Formato: {'Documentário 16:9' if is_doc else 'Short 9:16'}
            
            REGRAS VISUAIS:
            1. prompt_imagem (EM INGLÊS): Split sports poster, left side intense emotional portrait of protagonist under dramatic stadium floodlights, heavy rain and smoke, right side crime investigation corkboard with confidential dossiers, red yarn connecting folders, NO text, NO letters, NO words, NO watermark.
            2. titulo_amarelo: 2 a 3 palavras em amarelo ouro de alto impacto (ex: 'HAALAND PRESSIONADO!', 'ABEL COBRA REFORÇOS!', 'VINI JR. DEFENDIDO!').
            3. punchline_branca: Subtítulo em branco (ex: 'A BRIGA SECRETA NOS BASTIDORES', 'DECLARAÇÃO BOMBÁSTICA:').
            4. punchline_vermelha: Complemento em vermelho alerta (ex: 'DO MANCHESTER CITY', '"NÃO AJUDA MAIS"').
            5. badge: '🔴 DOSSIÊ CONFIDENCIAL' ou '🔥 BASTIDOR EXPLOSIVO'.
            
            Responda EXCLUSIVAMENTE em formato JSON:
            {{
                "prompt_imagem": "...",
                "titulo_amarelo": "...",
                "punchline_branca": "...",
                "punchline_vermelha": "...",
                "badge": "🔴 DOSSIÊ CONFIDENCIAL",
                "protagonista": "..."
            }}
            """
        else: # fergil
            prompt_director = f"""
            Você é o Diretor de Arte do canal corporativo FERGIL.
            Crie a especificação visual Wall Street para:
            Título: '{titulo}' | Formato: {'Documentário 16:9' if is_doc else 'Short 9:16'}
            
            Responda EXCLUSIVAMENTE em formato JSON:
            {{
                "prompt_imagem": "...",
                "titulo_amarelo": "QUEDA BILIONÁRIA",
                "subtitulo": "ESTUDO DE CASO EXECUTIVO",
                "badge": "💼 BASTIDOR EXECUTIVO",
                "protagonista": "..."
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
            
            res = {
                "prompt": p_img,
                "nome_canal_badge": nome_canal_badge,
                "aspect_ratio": aspect_ratio
            }
            if canal == "moda":
                res.update({
                    "linha1": str(dados_ia.get("linha1", "ACHADINHO DE LUXO")).strip().upper()[:24],
                    "linha2_banner": str(dados_ia.get("linha2_banner", "PERFEITO!")).strip().upper()[:18],
                    "preco": str(dados_ia.get("preco", "Apenas R$ 149,90!")).strip(),
                    "texto_cta": str(dados_ia.get("texto_cta", "GARANTA O SEU!")).strip().upper()[:18],
                    "badge_txt": "✨ ACHADINHO DE LUXO"
                })
            elif canal == "futebol":
                res.update({
                    "titulo_amarelo": str(dados_ia.get("titulo_amarelo", "BOMBA NO FUTEBOL!")).strip().upper()[:30],
                    "punchline_branca": str(dados_ia.get("punchline_branca", "A VERDADE DOS BASTIDORES")).strip().upper()[:35],
                    "punchline_vermelha": str(dados_ia.get("punchline_vermelha", "")).strip().upper()[:25],
                    "badge_txt": str(dados_ia.get("badge", "🔴 DOSSIÊ CONFIDENCIAL")).strip().upper(),
                    "texto_banner": str(dados_ia.get("titulo_amarelo", "BOMBA!")).strip().upper()[:24],
                    "subtitulo": str(dados_ia.get("punchline_branca", "")).strip().upper()[:28]
                })
            else:
                res.update({
                    "titulo_amarelo": str(dados_ia.get("titulo_amarelo", "PODER & ESTRATÉGIA")).strip().upper()[:28],
                    "subtitulo": str(dados_ia.get("subtitulo", "ESTUDO DE CASO EXECUTIVO")).strip().upper()[:35],
                    "badge_txt": str(dados_ia.get("badge", "💼 BASTIDOR EXECUTIVO")).strip().upper(),
                    "texto_banner": str(dados_ia.get("titulo_amarelo", "QUEDA BILIONÁRIA")).strip().upper()[:24]
                })
                
            logger.info(f"🎨 [DIRETOR IA DE CAPA] Prompt gerado ({canal}): Prompt={p_img[:50]}...")
            return res
            
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
        return {
            "prompt": prompt_visual,
            "titulo_amarelo": f"{l1} {l2}?!",
            "punchline_branca": "A VERDADE DOS BASTIDORES",
            "punchline_vermelha": "DOS BASTIDORES",
            "badge_txt": "🔴 DOSSIÊ CONFIDENCIAL" if is_doc else "🔥 BASTIDOR EXPLOSIVO",
            "texto_banner": f"{l1} {l2}?!",
            "subtitulo": "A VERDADE DOS BASTIDORES",
            "nome_canal_badge": nome_canal_badge,
            "protagonista": protagonista,
            "aspect_ratio": aspect_ratio
        }

    elif canal == "fergil":
        prompt_visual = (
            f"Cinematic executive drama YouTube thumbnail ({aspect_ratio}), ultra-realistic 8k. "
            f"Moody atmospheric lighting, powerful corporate boardroom, luxury skyscrapers glass reflections, focus on {protagonista}, "
            f"Wall Street aesthetic, stock charts, subtle gold accents, dark obsidian and deep navy blue tones, high stakes financial power, NO text, NO letters, NO words."
        )
        palavras_chaves = [p.upper() for p in palavras if p.upper() not in ("PARA", "COM", "QUE", "UMA", "NUM", "SOBRE", "EM", "DO", "DA", "NO", "NA")]
        l1 = palavras_chaves[0] if palavras_chaves else "QUEDA"
        l2 = palavras_chaves[1] if len(palavras_chaves) > 1 else "BILIONÁRIA"
        return {
            "prompt": prompt_visual,
            "titulo_amarelo": f"{l1} {l2}",
            "subtitulo": "ESTUDO DE CASO EXECUTIVO" if is_doc else "MENTALIDADE BILIONÁRIA",
            "badge_txt": "💼 BASTIDOR EXECUTIVO" if is_doc else "♟️ ESTRATÉGIA DE PODER",
            "texto_banner": f"{l1} {l2}",
            "nome_canal_badge": nome_canal_badge,
            "protagonista": protagonista,
            "aspect_ratio": aspect_ratio
        }

    else:
        # Moda Alana Cruz
        prompt_visual = (
            f"Luxury fashion editorial YouTube Shorts thumbnail (9:16 vertical), ultra-chic 8k photorealistic. "
            f"Wide shot of elegant model from waist to knees on an illuminated gold pedestal stage, warm golden bokeh particles, luxury boutique background, top 35% empty dark negative space with gentle sparkling gold dust, NO text, NO letters, NO words, NO watermark."
        )
        return {
            "prompt": prompt_visual,
            "linha1": "ACHADINHO DE LUXO",
            "linha2_banner": "PERFEITO!",
            "preco": "Apenas R$ 149,90!",
            "texto_cta": "GARANTA O SEU!",
            "badge_txt": "✨ ACHADINHO DE LUXO",
            "texto_banner": "PERFEITO! ✨",
            "subtitulo": "LOOK DE LUXO BARATO",
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
            candidatos = []
            if dados_capa.get("protagonista"):
                candidatos.append(dados_capa["protagonista"])
            for ent in palavras_tit:
                if ent.lower() not in ("para", "com", "uma", "sobre", "futebol", "shorts", "dossiê", "documentário", "fergil", "investigação", "puxão", "orelha", "clima", "bomba", "tenso"):
                    if ent not in candidatos:
                        candidatos.append(ent)
            
            foto_baixada = None
            for ent in candidatos:
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
        
        # Composição Especializada por Canal Baseada nos Benchmarks de Alto CTR
        if canal == "moda":
            # Aplica o layout idêntico à vitrine de luxo / boutique (Selo Oferta, Faixa Inclinada, Preço, CTA e Rodapé de Conversão)
            canvas = _compor_capa_vitrine_afiliado(canvas, dados_capa)
        elif canal == "futebol":
            # Aplica o layout Dossiê Investigativo (Painel de cortiça, fios vermelhos, fotos pinadas e carimbos confidenciais)
            canvas = _compor_capa_dossie_futebol(canvas, dados_capa, is_doc=is_doc)
        elif canal == "fergil":
            # Aplica o layout Executivo Wall Street (Azul marinho, grafite, tipografia dourada e badge corporativo)
            canvas = _compor_capa_executiva_fergil(canvas, dados_capa, is_doc=is_doc)
        else:
            canvas = _compor_capa_dossie_futebol(canvas, dados_capa, is_doc=is_doc)

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
