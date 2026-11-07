# -*- coding: utf-8 -*-
"""
Compositor Oficial de Super Capas para Shorts (Vertical 9:16 - 1080x1920)
Canal: Futebol Invisível (@FutebolInvisivelOficial)
Padrão: Altíssimo CTR no Feed de Shorts
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from loguru import logger

BASE_DIR = os.path.abspath("canais/canal_01_futebol_invisivel")
SHORTS_DIR = os.path.join(BASE_DIR, "videos_prontos", "shorts")
LOGO_SRC = os.path.abspath("perfil_futebol_invisivel.jpg")
os.makedirs(SHORTS_DIR, exist_ok=True)

def get_fonts_vertical():
    f_huge = ImageFont.truetype("impact.ttf", 108)
    f_sub = ImageFont.truetype("impact.ttf", 82)
    f_tag = ImageFont.truetype("arialbd.ttf", 36)
    return f_huge, f_sub, f_tag

def enhance_vertical(img):
    img = ImageEnhance.Color(img).enhance(1.42)
    img = ImageEnhance.Contrast(img).enhance(1.28)
    img = ImageEnhance.Sharpness(img).enhance(1.40)
    return img

def render_vignette_vertical(img):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Vinheta superior para a tag e logo
    for y in range(320):
        alpha = int(190 * (1 - y/320))
        d.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    # Vinheta inferior profunda para os textos de impacto
    for y in range(1200, 1920):
        alpha = int(248 * ((y - 1200)/720))
        d.line([(0, y), (1080, y)], fill=(3, 5, 10, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_watermark_vertical(img):
    if not os.path.exists(LOGO_SRC):
        return img
    with Image.open(LOGO_SRC) as wm:
        wm = wm.convert("RGBA")
        wm_size = (120, 120)
        wm = wm.resize(wm_size, Image.LANCZOS)
        mask = Image.new("L", wm_size, 0)
        d_mask = ImageDraw.Draw(mask)
        d_mask.ellipse((0, 0, wm_size[0], wm_size[1]), fill=230)
        wm.putalpha(mask)
        
        img_rgba = img.convert("RGBA")
        img_rgba.paste(wm, (1080 - 120 - 40, 50), wm)
        return img_rgba.convert("RGB")

def draw_text_stroke(draw, pos, text, font, fill_color, stroke_color=(0, 0, 0), stroke_width=12):
    x, y = pos
    sx, sy = x + 8, y + 8
    # Sombra
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((sx + dx, sy + dy), text, font=font, fill=(0, 0, 0, 180))
    # Contorno
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    # Cor frontal
    draw.text((x, y), text, font=font, fill=fill_color)

def compor_super_capa_short_paqueta(raw_img_path, out_path):
    logger.info(f"Compondo Super Capa Short do Paquetá a partir de: {raw_img_path}")
    img = Image.open(raw_img_path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = enhance_vertical(img)
    img = render_vignette_vertical(img)
    img = apply_watermark_vertical(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_sub, f_tag = get_fonts_vertical()
    
    # Tag vermelha de inquérito
    draw.rectangle([(50, 60), (560, 125)], fill=(220, 20, 20))
    draw.text((75, 72), "PREMIER LEAGUE INVESTIGAÇÃO", fill=(255, 255, 255), font=f_tag)
    
    # Textos gigantes de alto CTR
    draw_text_stroke(draw, (50, 1480), "BANIDO DO FUTEBOL?", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (50, 1610), "R$ 537 MILHÕES!", f_sub, (255, 255, 255), (0, 0, 0), 10)
    draw_text_stroke(draw, (50, 1720), "O CARTÃO SUSPEITO 🚨", f_tag, (255, 60, 60), (0, 0, 0), 6)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Super Capa Short Paquetá salva: {out_path}")

def compor_super_capa_short_clasico(raw_img_path, out_path):
    logger.info(f"Compondo Super Capa Short do El Clásico a partir de: {raw_img_path}")
    img = Image.open(raw_img_path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = enhance_vertical(img)
    img = render_vignette_vertical(img)
    img = apply_watermark_vertical(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_sub, f_tag = get_fonts_vertical()
    
    # Tag vermelha da UEFA
    draw.rectangle([(50, 60), (530, 125)], fill=(220, 20, 20))
    draw.text((75, 72), "DOSSIÊ UEFA CONFIDENCIAL", fill=(255, 255, 255), font=f_tag)
    
    # Textos gigantes de alto CTR
    draw_text_stroke(draw, (50, 1480), "50 MIL PÁGINAS!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (50, 1610), "BANIMENTO DO CLÁSSICO?", f_sub, (255, 255, 255), (0, 0, 0), 10)
    draw_text_stroke(draw, (50, 1720), "O GOLPE DE NYON ⚠️", f_tag, (255, 60, 60), (0, 0, 0), 6)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Super Capa Short El Clásico salva: {out_path}")

if __name__ == '__main__':
    logger.info("Script de composição de capas de Shorts pronto.")
