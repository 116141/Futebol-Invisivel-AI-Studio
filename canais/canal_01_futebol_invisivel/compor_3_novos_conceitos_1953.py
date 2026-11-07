# -*- coding: utf-8 -*-
"""
Compositor dos 3 Novos Conceitos de Capa para o Documentário de 1953 (Di Stéfano / El Clásico)
1. Split-Screen Comparison ("O GOLPE DE 1953")
2. The Evidence Anchor ("ROUBADO DO BARÇA?")
3. 3 Elements Thumbnail ("PACTO SECRETO 1953")
Canal: Futebol Invisível (@FutebolInvisivelOficial)
Padrão: 16:9 Widescreen (1920x1080) Full HD - Super CTR
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from loguru import logger

BASE_DIR = os.path.abspath("canais/canal_01_futebol_invisivel")
OUT_DIR = os.path.join(BASE_DIR, "videos_prontos", "documentarios")
LOGO_SRC = os.path.abspath("perfil_futebol_invisivel.jpg")
os.makedirs(OUT_DIR, exist_ok=True)

def get_fonts():
    f_huge = ImageFont.truetype("impact.ttf", 130)
    f_mid = ImageFont.truetype("impact.ttf", 98)
    f_tag = ImageFont.truetype("arialbd.ttf", 36)
    f_badge = ImageFont.truetype("arialbd.ttf", 32)
    return f_huge, f_mid, f_tag, f_badge

def enhance_visuals(img):
    img = ImageEnhance.Color(img).enhance(1.42)
    img = ImageEnhance.Contrast(img).enhance(1.28)
    img = ImageEnhance.Sharpness(img).enhance(1.40)
    return img

def render_cinematic_vignette(img):
    overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Vinheta superior
    for y in range(250):
        alpha = int(190 * (1 - y/250))
        d.line([(0, y), (1920, y)], fill=(0, 0, 0, alpha))
    # Vinheta inferior profunda para títulos
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
        logger.warning(f"Erro ao aplicar watermark: {e}")
        return img

def draw_text_stroke(draw, pos, text, font, fill_color, stroke_color=(0, 0, 0), stroke_width=12):
    x, y = pos
    sx, sy = x + 8, y + 8
    # Sombra projetada
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((sx + dx, sy + dy), text, font=font, fill=(0, 0, 0, 190))
    # Contorno rígido
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    # Cor frontal
    draw.text((x, y), text, font=font, fill=fill_color)

def compor_conceito_1_split_screen(raw_path, out_path):
    logger.info(f"Compondo Concept 1: Split-Screen Comparison -> {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_visuals(img)
    img = render_cinematic_vignette(img)
    img = apply_watermark(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge = get_fonts()
    
    # Tag pericial
    draw.rounded_rectangle([(70, 50), (600, 115)], radius=12, fill=(190, 20, 20))
    draw.text((95, 62), "ARQUIVO DE ESTADO • 1953", fill=(255, 255, 255), font=f_tag)
    
    # Textos principais
    draw_text_stroke(draw, (70, 730), "O GOLPE", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 865), "DE 1953!", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(70, 975), (700, 1030)], radius=10, fill=(255, 222, 0))
    draw.text((90, 985), "COMO DI STÉFANO FOI PARAR EM MADRI ⚠️", fill=(10, 10, 10), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Concept 1 salvo: {out_path}")

def compor_conceito_2_evidence_anchor(raw_path, out_path):
    logger.info(f"Compondo Concept 2: The Evidence Anchor -> {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_visuals(img)
    img = render_cinematic_vignette(img)
    img = apply_watermark(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge = get_fonts()
    
    # Tag pericial
    draw.rounded_rectangle([(70, 50), (620, 115)], radius=12, fill=(20, 70, 190))
    draw.text((95, 62), "PROVA FORENSE DOCUMENTAL", fill=(255, 255, 255), font=f_tag)
    
    # Textos principais
    draw_text_stroke(draw, (70, 730), "ROUBADO DO BARÇA?", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 865), "O CONTRATO SECRETO", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(70, 975), (660, 1030)], radius=10, fill=(210, 20, 20))
    draw.text((90, 985), "O DECRETO SALOMÔNICO DE 1953 🚨", fill=(255, 255, 255), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Concept 2 salvo: {out_path}")

def compor_conceito_3_three_elements(raw_path, out_path):
    logger.info(f"Compondo Concept 3: 3 Elements Thumbnail -> {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_visuals(img)
    img = render_cinematic_vignette(img)
    img = apply_watermark(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge = get_fonts()
    
    # Tag pericial
    draw.rounded_rectangle([(70, 50), (580, 115)], radius=12, fill=(180, 20, 20))
    draw.text((95, 62), "ACORDO SALOMÔNICO 1953", fill=(255, 255, 255), font=f_tag)
    
    # Textos principais
    draw_text_stroke(draw, (70, 730), "PACTO SECRETO 1953", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 865), "A DECISÃO DE FRANCO", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(70, 975), (680, 1030)], radius=10, fill=(255, 215, 0))
    draw.text((90, 985), "O BASTIDOR QUE MUDOU O FUTEBOL ⚠️", fill=(10, 10, 10), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Concept 3 salvo: {out_path}")

if __name__ == '__main__':
    art_dir = r"C:\Users\Uni-CvFCT-EdmilsonGi\.gemini\antigravity\brain\5e1c595d-f303-4a2c-93b1-dcaaf7304f16"
    
    raw_c1 = os.path.join(art_dir, "el_clasico_split_screen_1950s_1792840693594.jpg")
    raw_c2 = os.path.join(art_dir, "evidence_anchor_1953_transfer_1792840696528.jpg")
    raw_c3 = os.path.join(art_dir, "concept3_3elements_thumbnail_1792840701942.jpg")
    
    out_c1 = os.path.join(OUT_DIR, "CAPA_CONCEITO_1_SPLIT_SCREEN_1953.jpg")
    out_c2 = os.path.join(OUT_DIR, "CAPA_CONCEITO_2_EVIDENCE_ANCHOR_1953.jpg")
    out_c3 = os.path.join(OUT_DIR, "CAPA_CONCEITO_3_ELEMENTOS_PACTO_1953.jpg")
    
    logger.info("=== COMPONDO OS 3 NOVOS CONCEITOS VISUAIS DE 1953 ===")
    if os.path.exists(raw_c1):
        compor_conceito_1_split_screen(raw_c1, out_c1)
    if os.path.exists(raw_c2):
        compor_conceito_2_evidence_anchor(raw_c2, out_c2)
    if os.path.exists(raw_c3):
        compor_conceito_3_three_elements(raw_c3, out_c3)
    logger.success("=== TODOS OS 3 CONCEITOS FORAM COMPOSTOS COM SUCESSO! ===")

