# -*- coding: utf-8 -*-
"""
Compositor Oficial das 3 Super Capas de Alto CTR:
OPERAÇÃO PENALIDADE MÁXIMA: AS ESCUTAS SECRETAS DA MÁFIA DAS APOSTAS NO BRASIL
1. Conceito 1: O Ecrã do Escândalo (Mensagens WhatsApp & Cartão Amarelo)
2. Conceito 2: A Cela e o Relvado (Dualidade Crime vs Carreira)
3. Conceito 3: Dossiê Criminal Pericial (Estilo Noir Investigativo)
Canal: Futebol Invisível (@FutebolInvisivelOficial)
Formato: 16:9 Widescreen (1920x1080) Full HD
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from loguru import logger

BASE_DIR = os.path.abspath("canais/canal_01_futebol_invisivel")
MAT_DIR = os.path.join(BASE_DIR, "materiais_fotos_videos", "super_doc_penalidade_maxima")
LONG_DIR = os.path.join(BASE_DIR, "videos_prontos", "documentarios_longos")
LOGO_SRC = os.path.abspath("perfil_futebol_invisivel.jpg")

os.makedirs(LONG_DIR, exist_ok=True)

def get_fonts():
    f_huge = ImageFont.truetype("impact.ttf", 128)
    f_mid = ImageFont.truetype("impact.ttf", 96)
    f_tag = ImageFont.truetype("arialbd.ttf", 36)
    f_badge = ImageFont.truetype("arialbd.ttf", 32)
    f_chat = ImageFont.truetype("arialbd.ttf", 28)
    f_chat_bold = ImageFont.truetype("impact.ttf", 38)
    return f_huge, f_mid, f_tag, f_badge, f_chat, f_chat_bold

def enhance_visuals(img, sat=1.45, con=1.30, sha=1.45):
    img = ImageEnhance.Color(img).enhance(sat)
    img = ImageEnhance.Contrast(img).enhance(con)
    img = ImageEnhance.Sharpness(img).enhance(sha)
    return img

def render_cinematic_vignette(img):
    overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Vinheta superior
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

# ==========================================================
# 1. CONCEITO 1: O ECRÃ DO ESCÂNDALO (MENSAGENS & CARTÃO)
# ==========================================================
def render_conceito_1():
    out_path = os.path.join(LONG_DIR, "CAPA_PENALIDADE_MAXIMA_CONCEITO_1_O_ECRA_DO_ESCANDALO_16x9.jpg")
    logger.info(f"Renderizando Conceito 1: O Ecrã do Escândalo -> {out_path}")
    
    # Base: Usar a imagem com árbitro e cartão ou frame de tensão
    base_src = os.path.join(LONG_DIR, "CAPA_TESTE_B_PENALIDADE_MAXIMA_100_MIL_CARTAO_16x9.jpg")
    if not os.path.exists(base_src):
        base_src = os.path.join(MAT_DIR, "frame_90s.jpg")
    
    img = Image.open(base_src).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_visuals(img, sat=1.45, con=1.30, sha=1.45)
    img = render_cinematic_vignette(img)
    img = apply_watermark(img)
    
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge, f_chat, f_chat_bold = get_fonts()
    
    # Renderizar mockup realista de notificação de WhatsApp / PIX no terço esquerdo
    # Caixa de mensagem flutuante pericial
    box_x1, box_y1, box_x2, box_y2 = 70, 150, 830, 390
    draw.rounded_rectangle([(box_x1-4, box_y1-4), (box_x2+4, box_y2+4)], radius=18, fill=(0, 0, 0, 220))
    draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=16, fill=(15, 30, 25))
    
    # Cabeçalho da conversa (verde WhatsApp)
    draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y1 + 55)], radius=14, fill=(7, 94, 84))
    draw.text((box_x1 + 25, box_y1 + 12), "WHATSAPP • INTERCEPTAÇÃO GAECO", fill=(255, 255, 255), font=f_badge)
    
    # Balão da mensagem interceptada
    b_msg_x1, b_msg_y1, b_msg_x2, b_msg_y2 = box_x1 + 25, box_y1 + 75, box_x2 - 25, box_y2 - 20
    draw.rounded_rectangle([(b_msg_x1, b_msg_y1), (b_msg_x2, b_msg_y2)], radius=12, fill=(5, 75, 45))
    
    draw.text((b_msg_x1 + 20, b_msg_y1 + 18), "🚨 PIX CONFIRMADO: R$ 20.000,00", fill=(255, 222, 0), font=f_chat_bold)
    draw.text((b_msg_x1 + 20, b_msg_y1 + 68), "\"TOMA O AMARELO ANTES DOS 30'!\"", fill=(255, 255, 255), font=f_chat_bold)
    draw.text((b_msg_x1 + 20, b_msg_y1 + 115), "Comprovante enviado • Operação Penalidade Máxima", fill=(180, 220, 200), font=f_chat)
    
    # Tag pericial superior
    draw.rounded_rectangle([(70, 50), (620, 115)], radius=12, fill=(190, 20, 20))
    draw.text((95, 62), "PROVAS DO MINISTÉRIO PÚBLICO", fill=(255, 255, 255), font=f_tag)
    
    # Textos de alto impacto na base
    draw_text_stroke(draw, (70, 730), "ESCUTAS VAZADAS!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 865), "O GOLPE DO PIX", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(70, 975), (690, 1030)], radius=10, fill=(255, 222, 0))
    draw.text((90, 985), "A MÁFIA QUE COMPROU O BRASILEIRÃO 🚨", fill=(10, 10, 10), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Conceito 1 Salvo: {out_path}")

# ==========================================================
# 2. CONCEITO 2: A CELA E O RELVADO (DUALIDADE CRIME VS CARREIRA)
# ==========================================================
def render_conceito_2():
    out_path = os.path.join(LONG_DIR, "CAPA_PENALIDADE_MAXIMA_CONCEITO_2_A_CELA_E_O_RELVADO_16x9.jpg")
    logger.info(f"Renderizando Conceito 2: A Cela e o Relvado -> {out_path}")
    
    # Composição Split-Screen
    # Lado esquerdo: Túnel / Jogador (frame_45s.jpg ou frame_200s.jpg)
    # Lado direito: Perícia policial / Algemas (frame_320s.jpg ou CAPA_TESTE_A)
    f_left = os.path.join(MAT_DIR, "frame_45s.jpg")
    f_right = os.path.join(LONG_DIR, "CAPA_TESTE_A_PENALIDADE_MAXIMA_CHEFE_APOSTAS_16x9.jpg")
    if not os.path.exists(f_right):
        f_right = os.path.join(MAT_DIR, "frame_320s.jpg")
        
    im_l = Image.open(f_left).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    im_r = Image.open(f_right).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    
    # Cortar metade esquerda e metade direita
    split_img = Image.new("RGB", (1920, 1080))
    split_img.paste(im_l.crop((0, 0, 960, 1080)), (0, 0))
    split_img.paste(im_r.crop((960, 0, 1920, 1080)), (960, 0))
    
    # Costura brilhante no meio
    d_split = ImageDraw.Draw(split_img)
    for w in range(-4, 5):
        alpha = int(220 * (1 - abs(w)/5))
        d_split.line([(960 + w, 0), (960 + w, 1080)], fill=(255, 215, 0))
    
    split_img = enhance_visuals(split_img, sat=1.42, con=1.30, sha=1.40)
    split_img = render_cinematic_vignette(split_img)
    split_img = apply_watermark(split_img)
    
    draw = ImageDraw.Draw(split_img)
    f_huge, f_mid, f_tag, f_badge, _, _ = get_fonts()
    
    # Tag pericial
    draw.rounded_rectangle([(70, 50), (620, 115)], radius=12, fill=(20, 70, 190))
    draw.text((95, 62), "OPERAÇÃO PENALIDADE MÁXIMA", fill=(255, 255, 255), font=f_tag)
    
    # Carimbo BANIDO PELA FIFA sobre o lado direito
    draw.rounded_rectangle([(1100, 180), (1680, 260)], radius=14, fill=(180, 20, 20))
    draw.text((1140, 195), "BANIDO PELA FIFA GLOBALMENTE ⚠️", fill=(255, 255, 255), font=f_badge)
    
    # Textos de alto impacto
    draw_text_stroke(draw, (70, 730), "EXPULSOS DO FUTEBOL!", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 865), "A LISTA NEGRA DA FIFA", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(70, 975), (710, 1030)], radius=10, fill=(210, 20, 20))
    draw.text((90, 985), "DE JOGADOR A RÉU: O FIM DA CARREIRA ⚖️", fill=(255, 255, 255), font=f_badge)
    
    split_img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Conceito 2 Salvo: {out_path}")

# ==========================================================
# 3. CONCEITO 3: DOSSIÊ CRIMINAL PERICIAL (ESTILO NOIR)
# ==========================================================
def render_conceito_3():
    out_path = os.path.join(LONG_DIR, "CAPA_PENALIDADE_MAXIMA_CONCEITO_3_DOSSIE_NOIR_16x9.jpg")
    logger.info(f"Renderizando Conceito 3: Dossiê Criminal Pericial -> {out_path}")
    
    base_src = os.path.join(LONG_DIR, "CAPA_TESTE_C_PENALIDADE_MAXIMA_MAIOR_ESCANDALO_16x9.jpg")
    if not os.path.exists(base_src):
        base_src = os.path.join(MAT_DIR, "frame_380s.jpg")
        
    img = Image.open(base_src).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    img = enhance_visuals(img, sat=1.35, con=1.32, sha=1.45)
    img = render_cinematic_vignette(img)
    img = apply_watermark(img)
    
    draw = ImageDraw.Draw(img)
    f_huge, f_mid, f_tag, f_badge, _, _ = get_fonts()
    
    # Tag pericial
    draw.rounded_rectangle([(70, 50), (640, 115)], radius=12, fill=(180, 20, 20))
    draw.text((95, 62), "INVESTIGAÇÃO CRIMINAL GAECO", fill=(255, 255, 255), font=f_tag)
    
    # Selo de Auditoria Criminal no topo direito
    draw.rounded_rectangle([(1200, 170), (1750, 245)], radius=12, fill=(200, 20, 20))
    draw.text((1230, 185), "INQUÉRITO POLICIAL CONFIDENCIAL", fill=(255, 255, 255), font=f_badge)
    
    # Textos principais
    draw_text_stroke(draw, (70, 730), "O ESQUEMA", f_huge, (255, 222, 0), (0, 0, 0), 12)
    draw_text_stroke(draw, (70, 865), "FOI REVELADO!", f_mid, (255, 255, 255), (0, 0, 0), 10)
    
    # Sub-tarja neon
    draw.rounded_rectangle([(70, 975), (710, 1030)], radius=10, fill=(255, 215, 0))
    draw.text((90, 985), "COMO A QUADRILHA OPERAVA NO WHATSAPP ⚠️", fill=(10, 10, 10), font=f_badge)
    
    img.save(out_path, "JPEG", quality=98)
    logger.success(f"✓ Conceito 3 Salvo: {out_path}")

if __name__ == '__main__':
    logger.info("=== COMPONDO OS 3 CONCEITOS ESTRATÉGICOS DA OPERAÇÃO PENALIDADE MÁXIMA ===")
    render_conceito_1()
    render_conceito_2()
    render_conceito_3()
    logger.success("=== TODAS AS 3 CAPAS DA PENALIDADE MÁXIMA FORAM GERADAS COM SUCESSO! ===")
