# -*- coding: utf-8 -*-
"""
Gerador de Super Capas para Shorts (Vertical 9:16 - 1080x1920)
Canal: Futebol Invisível (@FutebolInvisivelOficial)
Padrão de Engenharia Editorial: Altíssimo CTR no Feed de Shorts e Grade do Canal
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from loguru import logger

BASE_DIR = os.path.abspath("canais/canal_01_futebol_invisivel")
SHORTS_DIR = os.path.join(BASE_DIR, "videos_prontos", "shorts")
LOGO_SRC = os.path.abspath("perfil_futebol_invisivel.jpg")
os.makedirs(SHORTS_DIR, exist_ok=True)

# Fontes Windows
def get_fonts():
    try:
        f_huge = ImageFont.truetype("impact.ttf", 112)
        f_mid = ImageFont.truetype("impact.ttf", 86)
        f_tag = ImageFont.truetype("arialbd.ttf", 36)
        f_small = ImageFont.truetype("arialbd.ttf", 32)
    except Exception:
        f_huge = ImageFont.load_default()
        f_mid = f_huge
        f_tag = f_huge
        f_small = f_huge
    return f_huge, f_mid, f_tag, f_small

def boost_image_visuals(img):
    # Aumenta saturação e contraste para saltar na tela de celulares AMOLED
    img = ImageEnhance.Color(img).enhance(1.45)
    img = ImageEnhance.Contrast(img).enhance(1.28)
    img = ImageEnhance.Sharpness(img).enhance(1.50)
    return img

def render_vignettes(img):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    
    # Vinheta superior suave (para a tag e logo ficarem legíveis)
    for y in range(280):
        alpha = int(180 * (1 - y / 280))
        d.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
        
    # Vinheta inferior profunda (y=1150 até 1920) para o bloco de texto não conflitar com a imagem
    for y in range(1150, 1920):
        ratio = (y - 1150) / 770
        alpha = int(240 * (ratio ** 1.3))
        d.line([(0, y), (1080, y)], fill=(5, 8, 15, alpha))
        
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_watermark(img):
    if not os.path.exists(LOGO_SRC):
        return img
    try:
        with Image.open(LOGO_SRC) as wm:
            wm = wm.convert("RGBA")
            wm_size = (130, 130)
            wm = wm.resize(wm_size, Image.LANCZOS)
            
            # Máscara circular com borda dourada
            mask = Image.new("L", wm_size, 0)
            d_mask = ImageDraw.Draw(mask)
            d_mask.ellipse((0, 0, wm_size[0], wm_size[1]), fill=255)
            wm.putalpha(mask)
            
            # Cria borda dourada ao redor
            border_img = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
            d_border = ImageDraw.Draw(border_img)
            d_border.ellipse((0, 0, 139, 139), fill=(255, 215, 0, 240))
            border_img.paste(wm, (5, 5), wm)
            
            img_rgba = img.convert("RGBA")
            img_rgba.paste(border_img, (1080 - 140 - 45, 60), border_img)
            return img_rgba.convert("RGB")
    except Exception as e:
        logger.warning(f"Erro ao aplicar watermark: {e}")
        return img

def draw_stroked_text(draw, pos, text, font, fill_color, stroke_color=(0, 0, 0), stroke_width=12):
    x, y = pos
    # Sombra projetada deslocada (+8, +8)
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((x + 8 + dx, y + 8 + dy), text, font=font, fill=(0, 0, 0, 190))
    # Contorno rígido
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    # Texto frontal
    draw.text((x, y), text, font=font, fill=fill_color)

def criar_capa_short_paqueta(raw_path, out_path):
    logger.info(f"Gerando Capa Short Paquetá: {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = boost_image_visuals(img)
    img = render_vignettes(img)
    img = apply_watermark(img)
    
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_small = get_fonts()
    
    # Tag de Inquérito / Alerta no topo
    tag_x, tag_y = 60, 75
    draw.rounded_rectangle([(tag_x, tag_y), (tag_x + 520, tag_y + 65)], radius=12, fill=(210, 20, 20))
    draw.text((tag_x + 22, tag_y + 12), "INQUÉRITO DA FA • LONDRES", fill=(255, 255, 255), font=f_small)
    
    # Bloco de Textos de Altíssimo CTR na zona nobre (y=1260 a 1580 - visível em qualquer aparelho sem obstrução)
    draw_stroked_text(draw, (60, 1340), "BANIDO PARA SEMPRE?", f_huge, (255, 225, 0), (0, 0, 0), 12)
    draw_stroked_text(draw, (60, 1475), "O CARTÃO DE R$ 537M!", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon amarela com texto preto
    sub_box_y = 1590
    draw.rounded_rectangle([(60, sub_box_y), (60 + 580, sub_box_y + 60)], radius=10, fill=(255, 222, 0))
    draw.text((75, sub_box_y + 10), "ESTRATÉGIA DE APOSTAS REVELADA ⚠️", fill=(10, 10, 10), font=f_small)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Capa Short Paquetá salva com sucesso: {out_path}")

def criar_capa_short_clasico_laporta(raw_path, out_path):
    logger.info(f"Gerando Capa Short El Clásico (Laporta): {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = boost_image_visuals(img)
    img = render_vignettes(img)
    img = apply_watermark(img)
    
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_small = get_fonts()
    
    # Tag UEFA Confidencial
    tag_x, tag_y = 60, 75
    draw.rounded_rectangle([(tag_x, tag_y), (tag_x + 500, tag_y + 65)], radius=12, fill=(20, 60, 180))
    draw.text((tag_x + 22, tag_y + 12), "DOSSIÊ UEFA • SUÍÇA 2026", fill=(255, 255, 255), font=f_small)
    
    # Bloco de Textos de Altíssimo CTR
    draw_stroked_text(draw, (60, 1340), "50 MIL PÁGINAS!", f_huge, (255, 225, 0), (0, 0, 0), 12)
    draw_stroked_text(draw, (60, 1475), "BANIMENTO DO CLÁSSICO?", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja vermelha
    sub_box_y = 1590
    draw.rounded_rectangle([(60, sub_box_y), (60 + 590, sub_box_y + 60)], radius=10, fill=(220, 20, 20))
    draw.text((75, sub_box_y + 10), "O CASO NEGREIRA CHEGOU A NYON 🚨", fill=(255, 255, 255), font=f_small)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Capa Short El Clásico Laporta salva: {out_path}")

def criar_capa_short_clasico_florentino(raw_path, out_path):
    logger.info(f"Gerando Capa Short El Clásico (Florentino): {out_path}")
    img = Image.open(raw_path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = boost_image_visuals(img)
    img = render_vignettes(img)
    img = apply_watermark(img)
    
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_small = get_fonts()
    
    # Tag
    tag_x, tag_y = 60, 75
    draw.rounded_rectangle([(tag_x, tag_y), (tag_x + 500, tag_y + 65)], radius=12, fill=(180, 20, 20))
    draw.text((tag_x + 22, tag_y + 12), "BASTIDORES DE MADRI • 2026", fill=(255, 255, 255), font=f_small)
    
    # Textos
    draw_stroked_text(draw, (60, 1340), "O GOLPE SECRETO!", f_huge, (255, 225, 0), (0, 0, 0), 12)
    draw_stroked_text(draw, (60, 1475), "A AUDITORIA DA UEFA", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja dourada
    sub_box_y = 1590
    draw.rounded_rectangle([(60, sub_box_y), (60 + 620, sub_box_y + 60)], radius=10, fill=(255, 215, 0))
    draw.text((75, sub_box_y + 10), "COMO O REAL MADRID ENTROU NA AÇÃO ⚠️", fill=(10, 10, 10), font=f_small)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Capa Short El Clásico Florentino salva: {out_path}")

if __name__ == '__main__':
    art_dir = r"C:\Users\Uni-CvFCT-EdmilsonGi\.gemini\antigravity\brain\5e1c595d-f303-4a2c-93b1-dcaaf7304f16"
    
    paqueta_raw = os.path.join(art_dir, "raw_paqueta_short_9x16_ctr_1792829299406.jpg")
    laporta_raw = os.path.join(art_dir, "laporta_press_conference_1792777847315.jpg")
    florentino_raw = os.path.join(art_dir, "florentino_perez_boardroom_signing_1792777840381.jpg")
    
    # Saídas
    out_paqueta = os.path.join(SHORTS_DIR, "CAPA_SUPER_CTR_SHORT_PAQUETA_BANIMENTO_9x16.jpg")
    out_clasico_a = os.path.join(SHORTS_DIR, "CAPA_SUPER_CTR_SHORT_EL_CLASICO_OPCAO_A_LAPORTA_9x16.jpg")
    out_clasico_b = os.path.join(SHORTS_DIR, "CAPA_SUPER_CTR_SHORT_EL_CLASICO_OPCAO_B_FLORENTINO_9x16.jpg")
    
    if os.path.exists(paqueta_raw):
        criar_capa_short_paqueta(paqueta_raw, out_paqueta)
    if os.path.exists(laporta_raw):
        criar_capa_short_clasico_laporta(laporta_raw, out_clasico_a)
    if os.path.exists(florentino_raw):
        criar_capa_short_clasico_florentino(florentino_raw, out_clasico_b)
