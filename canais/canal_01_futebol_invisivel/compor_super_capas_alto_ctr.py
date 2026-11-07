# -*- coding: utf-8 -*-
"""
Compositor de Super Capas de Altíssimo CTR (Padrão MrBeast / Netflix / CazéTV)
Canal: Futebol Invisível (@FutebolInvisivelOficial)
Fórmula de Sucesso:
1. Rosto do protagonista gigante (close-up expressivo) com rim-light.
2. Vinheta cinematográfica profunda para contraste total.
3. Tipografia gigante em Amarelo Ouro (#FFDE00) e Branco com contorno preto 12px.
4. Máximo de 2 a 3 palavras gigantes (legíveis em 5cm no celular).
5. Tag pericial vermelha de urgência no topo.
6. Selo circular translúcido do canal no canto superior direito.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from loguru import logger

BASE_DIR = os.path.abspath("canais/canal_01_futebol_invisivel")
LOGO_SRC = os.path.abspath("perfil_futebol_invisivel.jpg")

def get_fonts():
    f_huge = ImageFont.truetype("impact.ttf", 125)
    f_sub = ImageFont.truetype("impact.ttf", 90)
    f_tag = ImageFont.truetype("arialbd.ttf", 38)
    return f_huge, f_sub, f_tag

def enhance_image(img):
    # Cores elétricas e vibrantes
    img = ImageEnhance.Color(img).enhance(1.40)
    # Contraste profundo
    img = ImageEnhance.Contrast(img).enhance(1.28)
    # Nitidez extrema para mobile
    img = ImageEnhance.Sharpness(img).enhance(1.35)
    return img

def render_vignette(img):
    overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Vinheta superior para a tag
    for y in range(250):
        alpha = int(190 * (1 - y/250))
        d.line([(0, y), (1920, y)], fill=(0, 0, 0, alpha))
    # Vinheta inferior profunda para os textos
    for y in range(620, 1080):
        alpha = int(245 * ((y - 620)/460))
        d.line([(0, y), (1920, y)], fill=(4, 6, 10, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_watermark(img):
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
        img_rgba.paste(wm, (1920 - 120 - 45, 45), wm)
        return img_rgba.convert("RGB")

def draw_text_stroke(draw, pos, text, font, fill_color, stroke_color=(0, 0, 0), stroke_width=12):
    x, y = pos
    # Sombra projetada
    sx, sy = x + 8, y + 8
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((sx + dx, sy + dy), text, font=font, fill=(0, 0, 0, 180))
    # Contorno grosso preto
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    # Cor principal
    draw.text((x, y), text, font=font, fill=fill_color)

def compor_capa_paqueta(raw_img_path, out_path):
    logger.info(f"Compondo Super Capa do Paquetá a partir de: {raw_img_path}")
    img = Image.open(raw_img_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img)
    img = render_vignette(img)
    img = apply_watermark(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_sub, f_tag = get_fonts()
    
    # Tag vermelha de inquérito
    draw.rectangle([(70, 50), (620, 115)], fill=(220, 20, 20))
    draw.text((95, 60), "INQUÉRITO PREMIER LEAGUE", fill=(255, 255, 255), font=f_tag)
    
    # Textos gigantes de alto CTR
    draw_text_stroke(draw, (70, 750), "BANIMENTO VITALÍCIO!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 890), "R$ 537 MILHÕES EM JOGO", f_sub, (255, 255, 255), (0, 0, 0), 10)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Super Capa Paquetá Salva: {out_path}")

def compor_capa_el_clasico(raw_img_path, out_path):
    logger.info(f"Compondo Super Capa do El Clásico a partir de: {raw_img_path}")
    img = Image.open(raw_img_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img)
    img = render_vignette(img)
    img = apply_watermark(img)
    draw = ImageDraw.Draw(img)
    f_huge, f_sub, f_tag = get_fonts()
    
    # Tag vermelha da UEFA
    draw.rectangle([(70, 50), (620, 115)], fill=(220, 20, 20))
    draw.text((95, 60), "DOSSIÊ UEFA CONFIDENCIAL", fill=(255, 255, 255), font=f_tag)
    
    # Textos gigantes de alto CTR
    draw_text_stroke(draw, (70, 750), "50 MIL PÁGINAS!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 890), "BANIMENTO DO CLÁSSICO?", f_sub, (255, 255, 255), (0, 0, 0), 10)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Super Capa El Clásico Salva: {out_path}")

if __name__ == '__main__':
    logger.info("Script pronto para composição de alto CTR.")
