# -*- coding: utf-8 -*-
"""
GERADOR DE CAPAS DE ALTA RETENÇÃO & CTR MÁXIMO (ALANA CRUZ)
Baseado em pesquisa de melhores práticas do YouTube Shorts / TikTok 2026:
1. Enquadramento dentro da Safe-Zone 4:5 (320px a 1580px) para não cortar em buscas móveis e feed.
2. Regra das 3-4 palavras de choque psicológico (contraste com o título, gatilho de status x preço).
3. Saturação calibrada (+50%) e nitidez (+30%) para textura de tecido brilhar na tela de celular.
4. Caixas de contraste translúcidas atrás do texto para legibilidade instantânea em 0.5s.
"""

import os
import subprocess
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = r"canais/canal_04_achadinhos_moda_feminina/lote_5_shorts_api_oficial"

COVERS_DATA = [
    {
        "sid": "SHORT_01",
        "pid": "1005004209840111",
        "video_path": os.path.join(BASE_DIR, "produto_1_1005004209840111", "video_oficial_1005004209840111.mp4"),
        "out_cover": os.path.join(BASE_DIR, "CAPA_ALTA_RETENCAO_01_SLIP_DRESS_CETIM.jpg"),
        "ss_time": "00:00:03",
        "pill_top": "ZARA DUPE 🔥",
        "pill_color": (230, 30, 60, 245),
        "line1": "R$ 400 NA ZARA?",
        "line1_color": "#FFFFFF",
        "line2": "PAGUEI SÓ R$ 49! 😱",
        "line2_color": "#FFE600",
        "badge_sub": "MODELA E NÃO MARCA ✨"
    },
    {
        "sid": "SHORT_02",
        "pid": "1005007388309001",
        "video_path": os.path.join(BASE_DIR, "produto_2_1005007388309001", "video_oficial_1005007388309001.mp4"),
        "out_cover": os.path.join(BASE_DIR, "CAPA_ALTA_RETENCAO_02_ALFAIATARIA_LISTRADA.jpg"),
        "ss_time": "00:00:04",
        "pill_top": "LOOK DE RICA 🤍",
        "pill_color": (30, 30, 35, 245),
        "line1": "ALFAIATARIA",
        "line1_color": "#FFFFFF",
        "line2": "QUE EMAGRECE! ✨",
        "line2_color": "#FFE600",
        "badge_sub": "POSTURA DE MILIONÁRIA"
    },
    {
        "sid": "SHORT_03",
        "pid": "1005006739429289",
        "video_path": os.path.join(BASE_DIR, "produto_3_1005006739429289", "video_oficial_1005006739429289.mp4"),
        "out_cover": os.path.join(BASE_DIR, "CAPA_ALTA_RETENCAO_03_VESTIDO_MIDI_CINTURA.jpg"),
        "ss_time": "00:00:02",
        "pill_top": "EFEITO AMPULHETA ⏳",
        "pill_color": (180, 20, 80, 245),
        "line1": "AFINA A CINTURA",
        "line1_color": "#FFFFFF",
        "line2": "SEM APERTAR! 💕",
        "line2_color": "#00F0FF",
        "badge_sub": "CORTE LINHA A QUE DISFARÇA"
    },
    {
        "sid": "SHORT_04",
        "pid": "1005008783252618",
        "video_path": os.path.join(BASE_DIR, "produto_4_1005008783252618", "video_oficial_1005008783252618.mp4"),
        "out_cover": os.path.join(BASE_DIR, "CAPA_ALTA_RETENCAO_04_BERMUDA_CARGO.jpg"),
        "ss_time": "00:00:03",
        "pill_top": "TREND NA EUROPA 🌍",
        "pill_color": (210, 80, 10, 245),
        "line1": "BERMUDA CARGO",
        "line1_color": "#FFFFFF",
        "line2": "DISFARÇA O QUADRIL! 🔥",
        "line2_color": "#FFE600",
        "badge_sub": "ESTILO GRINGA CHIC"
    },
    {
        "sid": "SHORT_05",
        "pid": "1005004847084064",
        "video_path": os.path.join(BASE_DIR, "produto_5_1005004847084064", "video_oficial_1005004847084064.mp4"),
        "out_cover": os.path.join(BASE_DIR, "CAPA_ALTA_RETENCAO_05_BLAZER_PRETO_LONGO.jpg"),
        "ss_time": "00:00:02",
        "pill_top": "ALTA COSTURA 🖤",
        "pill_color": (15, 15, 20, 245),
        "line1": "TRANSFORMA",
        "line1_color": "#FFFFFF",
        "line2": "QUALQUER LOOK! 💎",
        "line2_color": "#FFD700",
        "badge_sub": "PRETO PODEROSO & CHIC"
    }
]

def make_high_ctr_cover(item):
    raw_frame = item["out_cover"].replace(".jpg", "_raw.jpg")
    cmd = [FFMPEG, "-y", "-ss", item["ss_time"], "-i", item["video_path"], "-vframes", "1", "-q:v", "2", raw_frame]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if not os.path.exists(raw_frame):
        # fallback frame
        cmd = [FFMPEG, "-y", "-ss", "00:00:01", "-i", item["video_path"], "-vframes", "1", "-q:v", "2", raw_frame]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    img = Image.open(raw_frame).convert("RGB")
    img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
    
    # 1. Color Grading Otimizado para Mobile (Saturação +50%, Contraste +25%, Nitidez +30%)
    img = ImageEnhance.Color(img).enhance(1.50)
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = ImageEnhance.Sharpness(img).enhance(1.30)
    
    draw = ImageDraw.Draw(img, "RGBA")
    
    # 2. Vinheta Suave Superior e Inferior para não brigar com a modelo
    for y in range(0, 380):
        alpha = int(140 * ((380 - y) / 380))
        draw.line([(0, y), (1080, y)], fill=(8, 8, 12, alpha))
        
    for y in range(1100, 1920):
        alpha = int(220 * ((y - 1100) / 820))
        draw.line([(0, y), (1080, y)], fill=(6, 6, 10, alpha))
        
    # 3. Caixa de Destaque Semitransparente na SAFE-ZONE CENTRAL (Y=1200 a Y=1580)
    # Garante 100% de legibilidade mesmo em miniaturas minúsculas no smartphone
    draw.rounded_rectangle([60, 1220, 1020, 1580], radius=35, fill=(10, 10, 15, 215), outline=(255, 255, 255, 60), width=3)
    
    try:
        font_pill = ImageFont.truetype("arialbd.ttf", 46)
        font_hero = ImageFont.truetype("arialbd.ttf", 76)
        font_sub = ImageFont.truetype("arialbd.ttf", 44)
    except Exception:
        font_pill = font_hero = font_sub = ImageFont.load_default()
        
    # 4. Top Pill dentro da Safe Zone (Y=340 para NUNCA cortar no 4:5)
    draw.rounded_rectangle([200, 330, 880, 420], radius=45, fill=item["pill_color"], outline=(255, 255, 255, 120), width=2)
    draw.text((540, 375), item["pill_top"], fill="white", font=font_pill, anchor="mm")
    
    # 5. Headlines de Impacto (Contraste Máximo dentro da caixa central)
    # Linha 1 (Branca com Sombra)
    draw.text((540, 1310), item["line1"], fill=item["line1_color"], font=font_hero, anchor="mm", stroke_width=7, stroke_fill="black")
    
    # Linha 2 (Dourada / Amarela / Ciano com Sombra)
    draw.text((540, 1420), item["line2"], fill=item["line2_color"], font=font_hero, anchor="mm", stroke_width=7, stroke_fill="black")
    
    # Linha 3 (Sub-badge explicativa rápida)
    draw.text((540, 1515), item["badge_sub"], fill="#E0E0E0", font=font_sub, anchor="mm", stroke_width=3, stroke_fill="black")
    
    # 6. Salvar em altíssima qualidade JPEG
    img.save(item["out_cover"], quality=98)
    if os.path.exists(raw_frame):
        os.remove(raw_frame)
    print(f"✅ Nova Capa de Alta Retenção Gerada: {item['out_cover']}")

def main():
    print("🎨 Renderizando Capas de Alta Retenção & CTR Baseadas em Pesquisa Científica de Plataforma...")
    for item in COVERS_DATA:
        make_high_ctr_cover(item)
    print("\n🎉 Todas as 5 capas otimizadas com sucesso!")

if __name__ == "__main__":
    main()
