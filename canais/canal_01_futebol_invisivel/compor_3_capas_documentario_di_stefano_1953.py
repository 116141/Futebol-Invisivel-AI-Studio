# -*- coding: utf-8 -*-
"""
Compositor Oficial dos 3 Conceitos de Miniatura para o Documentário:
"O Golpe de 1953: Como Roubaram Di Stéfano do Barcelona" (16:9 - 1920x1080)
1. Conceito 1: O Poster (Tensão Institucional - "O GOLPE DE 1953")
2. Conceito 2: Ecrã Dividido (Duelo de Documentos - "ROUBADO?")
3. Conceito 3: Foco no Protagonista e no Dossiê ("1953: A FARSA!")
Canal: Futebol Invisível (@FutebolInvisivelOficial)
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from loguru import logger

BASE_DIR = os.path.abspath("canais/canal_01_futebol_invisivel")
DOCS_DIR = os.path.join(BASE_DIR, "videos_prontos", "documentarios")
LOGO_SRC = os.path.abspath("perfil_futebol_invisivel.jpg")
os.makedirs(DOCS_DIR, exist_ok=True)

def get_fonts():
    f_huge = ImageFont.truetype("impact.ttf", 130)
    f_mid = ImageFont.truetype("impact.ttf", 98)
    f_tag = ImageFont.truetype("arialbd.ttf", 36)
    f_badge = ImageFont.truetype("arialbd.ttf", 32)
    return f_huge, f_mid, f_tag, f_badge

def enhance_image(img, sat=1.40, con=1.28, sha=1.40):
    img = ImageEnhance.Color(img).enhance(sat)
    img = ImageEnhance.Contrast(img).enhance(con)
    img = ImageEnhance.Sharpness(img).enhance(sha)
    return img

def render_vignette(img):
    overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Vinheta superior para a tag
    for y in range(250):
        alpha = int(190 * (1 - y/250))
        d.line([(0, y), (1920, y)], fill=(0, 0, 0, alpha))
    # Vinheta inferior profunda para os títulos
    for y in range(600, 1080):
        alpha = int(248 * ((y - 600)/480))
        d.line([(0, y), (1920, y)], fill=(3, 5, 10, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_watermark(img):
    if not os.path.exists(LOGO_SRC):
        return img
    try:
        with Image.open(LOGO_SRC) as wm:
            wm = wm.convert("RGBA")
            size = (125, 125)
            wm = wm.resize(size, Image.LANCZOS)
            
            mask = Image.new("L", size, 0)
            d_mask = ImageDraw.Draw(mask)
            d_mask.ellipse((0, 0, size[0], size[1]), fill=255)
            wm.putalpha(mask)
            
            b_size = (size[0] + 10, size[1] + 10)
            border_img = Image.new("RGBA", b_size, (0, 0, 0, 0))
            d_b = ImageDraw.Draw(border_img)
            d_b.ellipse((0, 0, b_size[0]-1, b_size[1]-1), fill=(255, 215, 0, 240))
            border_img.paste(wm, (5, 5), wm)
            
            img_rgba = img.convert("RGBA")
            img_rgba.paste(border_img, (1920 - b_size[0] - 50, 45), border_img)
            return img_rgba.convert("RGB")
    except Exception as e:
        logger.warning(f"Erro watermark: {e}")
        return img

def draw_text_stroke(draw, pos, text, font, fill_color, stroke_color=(0, 0, 0), stroke_width=12):
    x, y = pos
    sx, sy = x + 8, y + 8
    # Sombra
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((sx + dx, sy + dy), text, font=font, fill=(0, 0, 0, 190))
    # Contorno
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    # Cor frontal
    draw.text((x, y), text, font=font, fill=fill_color)

def compor_conceito_1_poster(raw_path, out_path):
    logger.info(f"Compondo Conceito 1: O Poster (Tensão Institucional) -> {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, sat=1.40, con=1.30, sha=1.45)
    img = render_vignette(img)
    img = apply_watermark(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge = get_fonts()
    
    # Tag pericial
    draw.rounded_rectangle([(70, 50), (620, 115)], radius=12, fill=(190, 20, 20))
    draw.text((95, 62), "O GOLPE HISTÓRICO • 1953", fill=(255, 255, 255), font=f_tag)
    
    # Textos de alto impacto
    draw_text_stroke(draw, (70, 730), "O GOLPE", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 865), "DE 1953!", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(70, 975), (700, 1030)], radius=10, fill=(255, 222, 0))
    draw.text((90, 985), "A DISPUTA QUE CORROMPEU DUAS ERAS ⚠️", fill=(10, 10, 10), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Conceito 1 Salvo: {out_path}")

def compor_conceito_2_split_duelo(raw_path, out_path):
    logger.info(f"Compondo Conceito 2: Ecrã Dividido (Duelo de Documentos) -> {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, sat=1.42, con=1.30, sha=1.40)
    img = render_vignette(img)
    img = apply_watermark(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge = get_fonts()
    
    # Tag pericial
    draw.rounded_rectangle([(70, 50), (620, 115)], radius=12, fill=(20, 70, 190))
    draw.text((95, 62), "DUELO DE BASTIDORES UEFA", fill=(255, 255, 255), font=f_tag)
    
    # Textos cortando o centro com contorno vermelho
    draw_text_stroke(draw, (70, 730), "ROUBADO?", f_huge, (255, 255, 255), (200, 20, 20), 14)
    draw_text_stroke(draw, (70, 865), "O DOSSIÊ DO CLÁSSICO", f_mid, (255, 222, 0), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(70, 975), (710, 1030)], radius=10, fill=(210, 20, 20))
    draw.text((90, 985), "A FRATURA DEFINITIVA ENTRE REAL E BARÇA 🚨", fill=(255, 255, 255), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Conceito 2 Salvo: {out_path}")

def compor_conceito_3_protagonista_dossie(raw_path, out_path):
    logger.info(f"Compondo Conceito 3: Foco no Protagonista e Dossiê -> {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, sat=1.30, con=1.35, sha=1.45)
    img = render_vignette(img)
    img = apply_watermark(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge = get_fonts()
    
    # Tag pericial
    draw.rounded_rectangle([(70, 50), (640, 115)], radius=12, fill=(180, 20, 20))
    draw.text((95, 62), "ARQUIVO POLICIAL DESPORTIVO", fill=(255, 255, 255), font=f_tag)
    
    # Textos de impacto
    draw_text_stroke(draw, (70, 730), "1953: A FARSA!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 865), "O ROUBO DE DI STÉFANO", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(70, 975), (700, 1030)], radius=10, fill=(255, 215, 0))
    draw.text((90, 985), "A INVESTIGAÇÃO DOS ARQUIVOS SECRETOS ⚠️", fill=(10, 10, 10), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Conceito 3 Salvo: {out_path}")

if __name__ == '__main__':
    art_dir = r"C:\Users\Uni-CvFCT-EdmilsonGi\.gemini\antigravity\brain\5e1c595d-f303-4a2c-93b1-dcaaf7304f16"
    
    raw_d1 = os.path.join(art_dir, "poster_tensao_institucional_di_stefano_1792841129212.jpg")
    raw_d2 = os.path.join(art_dir, "di_stefano_1953_split_screen_v2_png_1792841153961.jpg")
    raw_d3 = os.path.join(art_dir, "conceito_3_protagonista_dossie_1953_1792841141991.jpg")
    
    out_d1 = os.path.join(DOCS_DIR, "CAPA_DOC_CONCEITO_1_O_POSTER_1953_16x9.jpg")
    out_d2 = os.path.join(DOCS_DIR, "CAPA_DOC_CONCEITO_2_ECRA_DIVIDIDO_1953_16x9.jpg")
    out_d3 = os.path.join(DOCS_DIR, "CAPA_DOC_CONCEITO_3_PROTAGONISTA_DOSSIE_1953_16x9.jpg")
    
    logger.info("=== COMPONDO OS 3 CONCEITOS DO DOCUMENTÁRIO DE 1953 (16:9) ===")
    if os.path.exists(raw_d1):
        compor_conceito_1_poster(raw_d1, out_d1)
    if os.path.exists(raw_d2):
        compor_conceito_2_split_duelo(raw_d2, out_d2)
    if os.path.exists(raw_d3):
        compor_conceito_3_protagonista_dossie(raw_d3, out_d3)
    logger.success("=== TODOS OS 3 CONCEITOS DO DOCUMENTÁRIO FORAM COMPOSTOS COM SUCESSO! ===")

