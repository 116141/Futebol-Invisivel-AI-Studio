# -*- coding: utf-8 -*-
"""
Gerador Mestre de Super Capas de Altíssimo CTR (16:9 Widescreen e 9:16 Vertical)
Canal: Futebol Invisível (@FutebolInvisivelOficial)
Padrão: Netflix Documentaries / MrBeast / CazéTV
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from loguru import logger

BASE_DIR = os.path.abspath("canais/canal_01_futebol_invisivel")
DOCS_DIR = os.path.join(BASE_DIR, "videos_prontos", "documentarios")
LONG_DIR = os.path.join(BASE_DIR, "videos_prontos", "documentarios_longos")
SHORTS_DIR = os.path.join(BASE_DIR, "videos_prontos", "shorts")
MAT_CLASICO = os.path.join(BASE_DIR, "materiais_fotos_videos", "doc_dossie_el_clasico")
MAT_PAQUETA = os.path.join(BASE_DIR, "materiais_fotos_videos", "super_doc_caso_paqueta")
ART_DIR = r"C:\Users\Uni-CvFCT-EdmilsonGi\.gemini\antigravity\brain\5e1c595d-f303-4a2c-93b1-dcaaf7304f16"
LOGO_SRC = os.path.abspath("perfil_futebol_invisivel.jpg")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(LONG_DIR, exist_ok=True)
os.makedirs(SHORTS_DIR, exist_ok=True)

# ----------------- FONTES NATIVAS WINDOWS -----------------
def get_fonts_16x9():
    f_huge = ImageFont.truetype("impact.ttf", 125)
    f_mid = ImageFont.truetype("impact.ttf", 90)
    f_tag = ImageFont.truetype("arialbd.ttf", 38)
    return f_huge, f_mid, f_tag

def get_fonts_9x16():
    f_huge = ImageFont.truetype("impact.ttf", 112)
    f_mid = ImageFont.truetype("impact.ttf", 86)
    f_tag = ImageFont.truetype("arialbd.ttf", 36)
    f_small = ImageFont.truetype("arialbd.ttf", 32)
    return f_huge, f_mid, f_tag, f_small

# ----------------- PROCESSAMENTO DE IMAGEM -----------------
def enhance_image(img, sat=1.42, con=1.28, sha=1.40):
    img = ImageEnhance.Color(img).enhance(sat)
    img = ImageEnhance.Contrast(img).enhance(con)
    img = ImageEnhance.Sharpness(img).enhance(sha)
    return img

def render_vignette_16x9(img):
    overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Vinheta superior para a tag pericial
    for y in range(250):
        alpha = int(190 * (1 - y/250))
        d.line([(0, y), (1920, y)], fill=(0, 0, 0, alpha))
    # Vinheta inferior profunda para os textos
    for y in range(620, 1080):
        alpha = int(245 * ((y - 620)/460))
        d.line([(0, y), (1920, y)], fill=(4, 6, 10, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def render_vignette_9x16(img):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Vinheta superior
    for y in range(280):
        alpha = int(180 * (1 - y/280))
        d.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    # Vinheta inferior (zona segura: y=1150 até 1920)
    for y in range(1150, 1920):
        ratio = (y - 1150) / 770
        alpha = int(245 * (ratio ** 1.3))
        d.line([(0, y), (1080, y)], fill=(5, 8, 15, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_watermark(img, is_vertical=False):
    if not os.path.exists(LOGO_SRC):
        return img
    try:
        with Image.open(LOGO_SRC) as wm:
            wm = wm.convert("RGBA")
            size = (120, 120) if is_vertical else (125, 125)
            wm = wm.resize(size, Image.LANCZOS)
            
            mask = Image.new("L", size, 0)
            d_mask = ImageDraw.Draw(mask)
            d_mask.ellipse((0, 0, size[0], size[1]), fill=255)
            wm.putalpha(mask)
            
            # Anel dourado externo
            b_size = (size[0] + 10, size[1] + 10)
            border_img = Image.new("RGBA", b_size, (0, 0, 0, 0))
            d_b = ImageDraw.Draw(border_img)
            d_b.ellipse((0, 0, b_size[0]-1, b_size[1]-1), fill=(255, 215, 0, 240))
            border_img.paste(wm, (5, 5), wm)
            
            img_rgba = img.convert("RGBA")
            if is_vertical:
                pos = (1080 - b_size[0] - 40, 55)
            else:
                pos = (1920 - b_size[0] - 50, 45)
            img_rgba.paste(border_img, pos, border_img)
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
                draw.text((sx + dx, sy + dy), text, font=font, fill=(0, 0, 0, 185))
    # Contorno rígido
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    # Cor frontal
    draw.text((x, y), text, font=font, fill=fill_color)

# ==========================================================
# 1. DOCUMENTÁRIO EL CLÁSICO (16:9 - 1920x1080)
# ==========================================================
def render_el_clasico_opcao_1(out_path):
    # Opção A: Dossiê UEFA / 50 Mil Páginas / Banimento
    raw_path = os.path.join(ART_DIR, "raw_el_clasico_super_ctr_1792828961015.jpg")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, 1.40, 1.30, 1.40)
    img = render_vignette_16x9(img)
    img = apply_watermark(img, is_vertical=False)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag = get_fonts_16x9()
    
    # Tag vermelha UEFA
    draw.rectangle([(70, 50), (620, 115)], fill=(220, 20, 20))
    draw.text((95, 60), "DOSSIÊ UEFA CONFIDENCIAL", fill=(255, 255, 255), font=f_tag)
    
    draw_text_stroke(draw, (70, 750), "50 MIL PÁGINAS!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 890), "BANIMENTO DO CLÁSSICO?", f_mid, (255, 255, 255), (0, 0, 0), 10)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ El Clásico Opção 1: {out_path}")

def render_el_clasico_opcao_2(out_path):
    # Opção B: Caso Negreira / € 7,3 Milhões / Auditoria
    raw_path = os.path.join(MAT_CLASICO, "cena_05_auditoria_negreira.jpg")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.32, 1.45)
    img = render_vignette_16x9(img)
    img = apply_watermark(img, is_vertical=False)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag = get_fonts_16x9()
    
    # Tag auditoria Dasnil
    draw.rectangle([(70, 50), (680, 115)], fill=(200, 20, 20))
    draw.text((95, 60), "AUDITORIA FORENSE DASNIL 95", fill=(255, 255, 255), font=f_tag)
    
    draw_text_stroke(draw, (70, 750), "€ 7,3 MILHÕES!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 890), "O ESQUEMA DE NEGREIRA", f_mid, (255, 255, 255), (0, 0, 0), 10)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ El Clásico Opção 2: {out_path}")

def render_el_clasico_opcao_3(out_path):
    # Opção C: Golpe de 1953 / Di Stéfano / Arquivo Secreto
    raw_path = os.path.join(MAT_CLASICO, "cena_03_di_stefano_contrato.jpg")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, 1.35, 1.35, 1.45)
    img = render_vignette_16x9(img)
    img = apply_watermark(img, is_vertical=False)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag = get_fonts_16x9()
    
    # Tag de arquivo secreto
    draw.rectangle([(70, 50), (680, 115)], fill=(180, 20, 20))
    draw.text((95, 60), "ARQUIVO SECRETO DE ESTADO 1953", fill=(255, 255, 255), font=f_tag)
    
    draw_text_stroke(draw, (70, 750), "O ROUBO DO SÉCULO!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 890), "COMO LEVARAM DI STÉFANO", f_mid, (255, 255, 255), (0, 0, 0), 10)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ El Clásico Opção 3: {out_path}")

# ==========================================================
# 2. DOCUMENTÁRIO CASO PAQUETÁ (16:9 - 1920x1080)
# ==========================================================
def render_paqueta_opcao_a(out_path):
    # Ângulo: Golpe da Ilha / Cartão Suspeito
    raw_path = os.path.join(ART_DIR, "raw_paqueta_super_ctr_1792828955391.jpg")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.30, 1.40)
    img = render_vignette_16x9(img)
    img = apply_watermark(img, is_vertical=False)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag = get_fonts_16x9()
    
    draw.rectangle([(70, 50), (620, 115)], fill=(220, 20, 20))
    draw.text((95, 60), "OPERAÇÃO ILHA DE PAQUETÁ", fill=(255, 255, 255), font=f_tag)
    
    draw_text_stroke(draw, (70, 750), "O CARTÃO SUSPEITO!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 890), "A MÁFIA DE APOSTAS DA FA", f_mid, (255, 255, 255), (0, 0, 0), 10)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Paquetá Opção A: {out_path}")

def render_paqueta_opcao_b(out_path):
    # Ângulo: Banimento Vitalício / Tribunal
    raw_path = os.path.join(ART_DIR, "raw_paqueta_super_ctr_1792828955391.jpg")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.30, 1.40)
    img = render_vignette_16x9(img)
    img = apply_watermark(img, is_vertical=False)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag = get_fonts_16x9()
    
    draw.rectangle([(70, 50), (590, 115)], fill=(220, 20, 20))
    draw.text((95, 60), "TRIBUNAL DA FA • LONDRES", fill=(255, 255, 255), font=f_tag)
    
    draw_text_stroke(draw, (70, 750), "BANIMENTO VITALÍCIO!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 890), "ACABOU A CARREIRA?", f_mid, (255, 255, 255), (0, 0, 0), 10)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Paquetá Opção B: {out_path}")

def render_paqueta_opcao_c(out_path):
    # Ângulo: Valor Financeiro / Cancelamento R$ 537 Milhões
    raw_path = os.path.join(ART_DIR, "raw_paqueta_super_ctr_1792828955391.jpg")
    img = Image.open(raw_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.30, 1.40)
    img = render_vignette_16x9(img)
    img = apply_watermark(img, is_vertical=False)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag = get_fonts_16x9()
    
    draw.rectangle([(70, 50), (590, 115)], fill=(20, 70, 190))
    draw.text((95, 60), "NEGOCIAÇÃO CANCELADA", fill=(255, 255, 255), font=f_tag)
    
    draw_text_stroke(draw, (70, 750), "R$ 537 MILHÕES!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 890), "O CONTRATO DO MAN. CITY", f_mid, (255, 255, 255), (0, 0, 0), 10)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Paquetá Opção C: {out_path}")

# ==========================================================
# 3. OUTROS DOCUMENTÁRIOS DO CANAL (16:9 - 1920x1080)
# ==========================================================
def render_calciopoli(out_path):
    raw_p = os.path.join(LONG_DIR, "CAPA_TESTE_A_CALCIOPOLI_MOGGI_JULGAMENTO_16x9.jpg")
    if not os.path.exists(raw_p):
        return
    img = Image.open(raw_p).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, 1.35, 1.25, 1.35)
    img = apply_watermark(img, is_vertical=False)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Calciopoli 16:9: {out_path}")

def render_yamal_304(out_path):
    raw_p = os.path.join(LONG_DIR, "CAPA_A_304_GLORIA_YAMAL.jpg")
    if not os.path.exists(raw_p):
        return
    img = Image.open(raw_p).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.30, 1.45)
    img = apply_watermark(img, is_vertical=False)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Yamal 304 16:9: {out_path}")

def render_sorteios_champions(out_path):
    raw_p = os.path.join(LONG_DIR, "THUMB_UEFA_SORTEIO_16x9.jpg")
    if not os.path.exists(raw_p):
        return
    img = Image.open(raw_p).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.30, 1.40)
    img = render_vignette_16x9(img)
    img = apply_watermark(img, is_vertical=False)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag = get_fonts_16x9()
    
    draw.rectangle([(70, 50), (620, 115)], fill=(20, 70, 190))
    draw.text((95, 60), "INVESTIGAÇÃO DA UEFA", fill=(255, 255, 255), font=f_tag)
    
    draw_text_stroke(draw, (70, 750), "BOLINHAS GELADAS?", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 890), "A FARSA DOS SORTEIOS", f_mid, (255, 255, 255), (0, 0, 0), 10)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Champions Sorteios 16:9: {out_path}")

# ==========================================================
# 4. SUPER CAPAS PARA SHORTS (9:16 - 1080x1920)
# ==========================================================
def render_short_cr7(out_path):
    raw_p = os.path.join(ART_DIR, "cr7_gemini_clean_01_1792762727754.jpg")
    if not os.path.exists(raw_p):
        return
    img = Image.open(raw_p).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.30, 1.50)
    img = render_vignette_9x16(img)
    img = apply_watermark(img, is_vertical=True)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_small = get_fonts_9x16()
    
    # Tag
    draw.rounded_rectangle([(60, 75), (580, 140)], radius=12, fill=(210, 20, 20))
    draw.text((80, 87), "POLÊMICA NA SELEÇÃO • FPF", fill=(255, 255, 255), font=f_small)
    
    # Textos na zona nobre
    draw_text_stroke(draw, (60, 1340), "MULTADO EM € 255!", f_huge, (255, 225, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (60, 1475), "A FÚRIA DE CRISTIANO", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(60, 1590), (620, 1650)], radius=10, fill=(255, 222, 0))
    draw.text((75, 1600), "O MOTIVO SURREAL DO CARTÃO 🚨", fill=(10, 10, 10), font=f_small)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Short CR7 9:16: {out_path}")

def render_short_endrick(out_path):
    raw_p = os.path.join(ART_DIR, "endrick_real_madrid_bernabeu_1792762824413.jpg")
    if not os.path.exists(raw_p):
        return
    img = Image.open(raw_p).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.30, 1.50)
    img = render_vignette_9x16(img)
    img = apply_watermark(img, is_vertical=True)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_small = get_fonts_9x16()
    
    draw.rounded_rectangle([(60, 75), (590, 140)], radius=12, fill=(180, 20, 20))
    draw.text((80, 87), "PRESSÃO NO BERNABÉU • 2026", fill=(255, 255, 255), font=f_small)
    
    draw_text_stroke(draw, (60, 1340), "TITULAR NO CLÁSSICO?", f_huge, (255, 225, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (60, 1475), "A DECISÃO DE ANCELOTTI", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    draw.rounded_rectangle([(60, 1590), (600, 1650)], radius=10, fill=(255, 215, 0))
    draw.text((75, 1600), "O FENÔMENO DE MADRI ⚽", fill=(10, 10, 10), font=f_small)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Short Endrick 9:16: {out_path}")

def render_short_infantino(out_path):
    raw_p = os.path.join(ART_DIR, "gianni_infantino_fifa_world_cup_trophy_png_1792762831431.jpg")
    if not os.path.exists(raw_p):
        return
    img = Image.open(raw_p).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.30, 1.50)
    img = render_vignette_9x16(img)
    img = apply_watermark(img, is_vertical=True)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_small = get_fonts_9x16()
    
    draw.rounded_rectangle([(60, 75), (550, 140)], radius=12, fill=(210, 20, 20))
    draw.text((80, 87), "INVESTIGAÇÃO THE TIMES", fill=(255, 255, 255), font=f_small)
    
    draw_text_stroke(draw, (60, 1340), "ESCÂNDALO NA FIFA!", f_huge, (255, 225, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (60, 1475), "O DOSSIÊ DE INFANTINO", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    draw.rounded_rectangle([(60, 1590), (620, 1650)], radius=10, fill=(255, 40, 40))
    draw.text((75, 1600), "CONTRATOS SECRETOS REVELADOS ⚠️", fill=(255, 255, 255), font=f_small)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Short Infantino 9:16: {out_path}")

def render_short_paqueta_b(out_path):
    raw_p = os.path.join(ART_DIR, "raw_paqueta_short_9x16_ctr_1792829299406.jpg")
    if not os.path.exists(raw_p):
        return
    img = Image.open(raw_p).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.30, 1.50)
    img = render_vignette_9x16(img)
    img = apply_watermark(img, is_vertical=True)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_small = get_fonts_9x16()
    
    draw.rounded_rectangle([(60, 75), (540, 140)], radius=12, fill=(20, 70, 190))
    draw.text((80, 87), "MÁFIA DE APOSTAS DA ILHA", fill=(255, 255, 255), font=f_small)
    
    draw_text_stroke(draw, (60, 1340), "O GOLPE DA ILHA!", f_huge, (255, 225, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (60, 1475), "R$ 537 MILHÕES EM RISCO", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    draw.rounded_rectangle([(60, 1590), (610, 1650)], radius=10, fill=(255, 222, 0))
    draw.text((75, 1600), "ESQUEMA DE CARTÕES AMARELOS 🚨", fill=(10, 10, 10), font=f_small)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Short Paquetá Opção B 9:16: {out_path}")

def render_short_clasico_c(out_path):
    raw_p = os.path.join(MAT_CLASICO, "cena_06_presidentes_guerra.jpg")
    if not os.path.exists(raw_p):
        return
    img = Image.open(raw_p).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = enhance_image(img, 1.45, 1.30, 1.50)
    img = render_vignette_9x16(img)
    img = apply_watermark(img, is_vertical=True)
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_small = get_fonts_9x16()
    
    draw.rounded_rectangle([(60, 75), (550, 140)], radius=12, fill=(220, 20, 20))
    draw.text((80, 87), "GUERRA DE BASTIDORES UEFA", fill=(255, 255, 255), font=f_small)
    
    draw_text_stroke(draw, (60, 1340), "GUERRA DECLARADA!", f_huge, (255, 225, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (60, 1475), "FLORENTINO VS LAPORTA", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    draw.rounded_rectangle([(60, 1590), (610, 1650)], radius=10, fill=(255, 215, 0))
    draw.text((75, 1600), "O CLÁSSICO NUNCA MAIS SERÁ IGUAL ⚠️", fill=(10, 10, 10), font=f_small)
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Short El Clásico Opção C 9:16: {out_path}")

# ==========================================================
# EXECUÇÃO PRINCIPAL
# ==========================================================
if __name__ == '__main__':
    logger.info("=== INICIANDO PRODUÇÃO INTEGRAL DE TODAS AS SUPER CAPAS DO CANAL ===")
    
    # 1. El Clásico (16:9)
    render_el_clasico_opcao_1(os.path.join(DOCS_DIR, "CAPA_OPCAO_01_DOSSIE_UEFA_BANIMENTO.jpg"))
    render_el_clasico_opcao_2(os.path.join(DOCS_DIR, "CAPA_OPCAO_02_CASO_NEGREIRA_AUDITORIA.jpg"))
    render_el_clasico_opcao_3(os.path.join(DOCS_DIR, "CAPA_OPCAO_03_GOLPE_HISTORICO_DI_STEFANO.jpg"))
    
    # 2. Paquetá (16:9)
    render_paqueta_opcao_a(os.path.join(LONG_DIR, "CAPA_TESTE_A_CASO_PAQUETA_O_GOLPE_DA_ILHA_16x9.jpg"))
    render_paqueta_opcao_b(os.path.join(LONG_DIR, "CAPA_TESTE_B_CASO_PAQUETA_BANIMENTO_VITALICIO_16x9.jpg"))
    render_paqueta_opcao_c(os.path.join(LONG_DIR, "CAPA_TESTE_C_CASO_PAQUETA_MEIO_BILHAO_CANCELADO_16x9.jpg"))
    
    # 3. Outros Documentários (16:9)
    render_calciopoli(os.path.join(LONG_DIR, "CAPA_TESTE_A_CALCIOPOLI_MOGGI_JULGAMENTO_16x9.jpg"))
    render_yamal_304(os.path.join(LONG_DIR, "CAPA_A_304_GLORIA_YAMAL.jpg"))
    render_sorteios_champions(os.path.join(LONG_DIR, "CAPA_TESTE_A_SORTEIOS_CHAMPIONS_BOLINHAS_GELADAS_16x9.jpg"))
    
    # 4. Shorts (9:16)
    render_short_cr7(os.path.join(SHORTS_DIR, "CAPA_SHORT_01_CR7_MULTA_255_EUROS.jpg"))
    render_short_endrick(os.path.join(SHORTS_DIR, "CAPA_SHORT_02_ENDRICK_TITULAR_EL_CLASICO.jpg"))
    render_short_infantino(os.path.join(SHORTS_DIR, "CAPA_SHORT_03_DOSSIE_THE_TIMES_INFANTINO.jpg"))
    render_short_paqueta_b(os.path.join(SHORTS_DIR, "CAPA_SHORT_CASO_PAQUETA_VIRAL_9x16.jpg"))
    render_short_clasico_c(os.path.join(SHORTS_DIR, "CAPA_SUPER_CTR_SHORT_EL_CLASICO_OPCAO_C_GUERRA_9x16.jpg"))
    
    logger.success("=== TODAS AS SUPER CAPAS FORAM GERADAS E ATUALIZADAS COM SUCESSO! ===")
