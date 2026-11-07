# -*- coding: utf-8 -*-
"""
Compositor Oficial dos 3 Novos Conceitos de Capa para Shorts (Vertical 9:16 - 1080x1920)
Documentário/Short: O Caso Di Stéfano / El Clásico de 1953
Canal: Futebol Invisível (@FutebolInvisivelOficial)
Padrão: Altíssimo CTR no Feed de Shorts e Zona Segura Rigorosa
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from loguru import logger

BASE_DIR = os.path.abspath("canais/canal_01_futebol_invisivel")
SHORTS_DIR = os.path.join(BASE_DIR, "videos_prontos", "shorts")
LOGO_SRC = os.path.abspath("perfil_futebol_invisivel.jpg")
os.makedirs(SHORTS_DIR, exist_ok=True)

def get_fonts_vertical():
    f_huge = ImageFont.truetype("impact.ttf", 116)
    f_mid = ImageFont.truetype("impact.ttf", 88)
    f_tag = ImageFont.truetype("arialbd.ttf", 36)
    f_badge = ImageFont.truetype("arialbd.ttf", 32)
    return f_huge, f_mid, f_tag, f_badge

def enhance_vertical(img):
    img = ImageEnhance.Color(img).enhance(1.45)
    img = ImageEnhance.Contrast(img).enhance(1.28)
    img = ImageEnhance.Sharpness(img).enhance(1.45)
    return img

def render_vignette_vertical(img):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Vinheta superior
    for y in range(280):
        alpha = int(185 * (1 - y/280))
        d.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    # Vinheta inferior profunda (y=1150 a 1920)
    for y in range(1150, 1920):
        ratio = (y - 1150) / 770
        alpha = int(245 * (ratio ** 1.3))
        d.line([(0, y), (1080, y)], fill=(4, 7, 14, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_watermark_vertical(img):
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
            img_rgba.paste(border_img, (1080 - b_size[0] - 40, 60), border_img)
            return img_rgba.convert("RGB")
    except Exception as e:
        logger.warning(f"Erro watermark vertical: {e}")
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

def compor_short_conceito_1(raw_path, out_path):
    logger.info(f"Compondo Short Concept 1 (Split-Screen) -> {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = enhance_vertical(img)
    img = render_vignette_vertical(img)
    img = apply_watermark_vertical(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge = get_fonts_vertical()
    
    # Tag
    draw.rounded_rectangle([(60, 75), (580, 140)], radius=12, fill=(190, 20, 20))
    draw.text((80, 87), "ARQUIVO DE ESTADO • 1953", fill=(255, 255, 255), font=f_tag)
    
    # Textos na Zona Segura (y=1320 a 1620)
    draw_text_stroke(draw, (60, 1340), "O GOLPE", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (60, 1475), "DE 1953!", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(60, 1590), (640, 1650)], radius=10, fill=(255, 222, 0))
    draw.text((75, 1600), "A DISPUTA QUE MUDOU O FUTEBOL ⚠️", fill=(10, 10, 10), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Short Concept 1 Salvo: {out_path}")

def compor_short_conceito_2(raw_path, out_path):
    logger.info(f"Compondo Short Concept 2 (The Evidence Anchor) -> {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = enhance_vertical(img)
    img = render_vignette_vertical(img)
    img = apply_watermark_vertical(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge = get_fonts_vertical()
    
    # Tag
    draw.rounded_rectangle([(60, 75), (590, 140)], radius=12, fill=(20, 70, 190))
    draw.text((80, 87), "PROVA FORENSE HISTÓRICA", fill=(255, 255, 255), font=f_tag)
    
    # Textos na Zona Segura
    draw_text_stroke(draw, (60, 1340), "ROUBADO DO BARÇA?", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (60, 1475), "O CONTRATO SECRETO", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(60, 1590), (630, 1650)], radius=10, fill=(210, 20, 20))
    draw.text((75, 1600), "O DECRETO SALOMÔNICO DE 1953 🚨", fill=(255, 255, 255), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Short Concept 2 Salvo: {out_path}")

def compor_short_conceito_3(raw_path, out_path):
    logger.info(f"Compondo Short Concept 3 (3 Elements Thumbnail) -> {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = enhance_vertical(img)
    img = render_vignette_vertical(img)
    img = apply_watermark_vertical(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge = get_fonts_vertical()
    
    # Tag
    draw.rounded_rectangle([(60, 75), (560, 140)], radius=12, fill=(180, 20, 20))
    draw.text((80, 87), "ACORDO SALOMÔNICO 1953", fill=(255, 255, 255), font=f_tag)
    
    # Textos na Zona Segura
    draw_text_stroke(draw, (60, 1340), "PACTO SECRETO 1953", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (60, 1475), "A DECISÃO DE FRANCO", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(60, 1590), (640, 1650)], radius=10, fill=(255, 215, 0))
    draw.text((75, 1600), "O BASTIDOR QUE MUDOU O CLÁSSICO ⚠️", fill=(10, 10, 10), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Short Concept 3 Salvo: {out_path}")

if __name__ == '__main__':
    art_dir = r"C:\Users\Uni-CvFCT-EdmilsonGi\.gemini\antigravity\brain\5e1c595d-f303-4a2c-93b1-dcaaf7304f16"
    
    raw_s1 = os.path.join(art_dir, "el_clasico_1950s_split_thumbnail_png_1792840867255.jpg")
    raw_s2 = os.path.join(art_dir, "evidence_anchor_1953_1792840873540.jpg")
    raw_s3 = os.path.join(art_dir, "di_stefano_concept3_thumbnail_png_1792840882811.jpg")
    
    out_s1 = os.path.join(SHORTS_DIR, "CAPA_SHORT_CONCEITO_1_SPLIT_SCREEN_1953_9x16.jpg")
    out_s2 = os.path.join(SHORTS_DIR, "CAPA_SHORT_CONCEITO_2_EVIDENCE_ANCHOR_1953_9x16.jpg")
    out_s3 = os.path.join(SHORTS_DIR, "CAPA_SHORT_CONCEITO_3_ELEMENTOS_PACTO_1953_9x16.jpg")
    
    logger.info("=== COMPONDO OS 3 NOVOS CONCEITOS VISUAIS PARA SHORTS (9:16) ===")
    if os.path.exists(raw_s1):
        compor_short_conceito_1(raw_s1, out_s1)
    if os.path.exists(raw_s2):
        compor_short_conceito_2(raw_s2, out_s2)
    if os.path.exists(raw_s3):
        compor_short_conceito_3(raw_s3, out_s3)
    logger.success("=== TODOS OS 3 CONCEITOS PARA SHORTS FORAM COMPOSTOS COM SUCESSO! ===")

