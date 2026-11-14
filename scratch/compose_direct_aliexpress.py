import os
import sys
sys.path.append('.')
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def obter_fonte(tamanho: int) -> ImageFont.FreeTypeFont:
    caminhos = [
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\arialbd.ttf"
    ]
    for c in caminhos:
        if os.path.exists(c):
            return ImageFont.truetype(c, tamanho)
    return ImageFont.load_default()

def desenhar_texto_3d_luxo(draw, pos, texto, font, cor_face, cor_extrusao=(170, 15, 15), cor_borda=(0, 0, 0), profundidade=14):
    x, y = pos
    for d in range(profundidade + 4, profundidade + 20, 2):
        draw.text((x + d, y + d), texto, font=font, fill=(0, 0, 0, 80))
    for step in range(profundidade, 0, -1):
        for dx in range(-3, 4):
            draw.text((x + dx, y + step), texto, font=font, fill=cor_extrusao)
    for dx in range(-7, 8):
        for dy in range(-7, 8):
            if dx*dx + dy*dy <= 49:
                draw.text((x + dx, y + dy), texto, font=font, fill=cor_borda)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx*dx + dy*dy <= 16:
                draw.text((x + dx, y + dy), texto, font=font, fill=cor_extrusao)
    draw.text((x, y), texto, font=font, fill=cor_face)

def compor_capa_direta_aliexpress(
    caminho_foto_produto: str,
    linha1: str,
    linha2: str,
    preco_str: str,
    caminho_saida: str,
    badge_str: str = "✨ ACHADINHO DE LUXO"
):
    """
    Usa a foto REAL e profissional do AliExpress com o seu próprio fundo original!
    Ajusta no formato 9:16 vertical (1536x2752) com blur de fundo elegante nas laterais/topo,
    aplicando apenas os textos 3D superiores e o rodapé oficial de conversão.
    SEM RECORTES DESTRUTIVOS, SEM PALCO FALSO.
    """
    W, H = 1536, 2752
    
    # 1. Carrega a foto original do AliExpress
    prod_img = Image.open(caminho_foto_produto).convert("RGB")
    pw, ph = prod_img.size
    
    # 2. Fundo cinematográfico derivado da própria foto (Fast Blur em baixa resolução)
    bg_ratio = W / H
    prod_ratio = pw / ph
    
    if prod_ratio > bg_ratio:
        scale_bg = H / ph
    else:
        scale_bg = W / pw
        
    bg_w = int(pw * scale_bg)
    bg_h = int(ph * scale_bg)
    bg_img = prod_img.resize((bg_w, bg_h), Image.BILINEAR)
    
    bg_x = (bg_w - W) // 2
    bg_y = (bg_h - H) // 2
    bg_cropped = bg_img.crop((bg_x, bg_y, bg_x + W, bg_y + H))
    
    # Fast blur: reduz 4x, aplica blur e re-expande (0.05 segundos)
    bg_small = bg_cropped.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(10))
    bg_blur = bg_small.resize((W, H), Image.BICUBIC)
    
    # Escurece o fundo desfocado para dar destaque total à foto principal
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    canvas.paste(bg_blur, (0, 0))
    
    dark_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 110))
    canvas = Image.alpha_composite(canvas, dark_overlay)
    
    # 3. Coloca a foto REAL do produto em alta resolução no centro
    area_disponivel_h = int(H * 0.72) # Área entre o título e o rodapé
    area_disponivel_w = W
    
    scale_fit = min(area_disponivel_w / pw, area_disponivel_h / ph)
    fit_w = int(pw * scale_fit)
    fit_h = int(ph * scale_fit)
    
    prod_sharp = prod_img.resize((fit_w, fit_h), Image.LANCZOS)
    
    # Sombra suave sob a foto real
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_sh = ImageDraw.Draw(shadow)
    pos_x = (W - fit_w) // 2
    pos_y = int(H * 0.17) + (area_disponivel_h - fit_h) // 2
    
    d_sh.rectangle([pos_x - 12, pos_y - 12, pos_x + fit_w + 12, pos_y + fit_h + 12], fill=(0, 0, 0, 150))
    shadow_small = shadow.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(8)).resize((W, H), Image.BICUBIC)
    canvas = Image.alpha_composite(canvas, shadow_small)
    
    canvas.paste(prod_sharp, (pos_x, pos_y))
    
    # 4. Gradiente Superior Suave para leitura da tipografia 3D
    top_grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_tg = ImageDraw.Draw(top_grad)
    for y in range(int(H * 0.22)):
        alpha = int(180 * (1 - y / (H * 0.22)))
        d_tg.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas, top_grad)
    
    # 5. Badge Superior Elegante
    if badge_str:
        f_badge = obter_fonte(44)
        bb_b = f_badge.getbbox(badge_str)
        bw = (bb_b[2] - bb_b[0]) + 40
        bh = (bb_b[3] - bb_b[1]) + 20
        bx = (W - bw) // 2
        by = 50
        d_b = ImageDraw.Draw(canvas)
        d_b.rectangle([bx, by, bx + bw, by + bh], fill=(220, 20, 20, 240), outline=(255, 230, 40, 255), width=3)
        d_b.text((bx + 20, by + 10), badge_str, font=f_badge, fill=(255, 255, 255))
    
    # 6. Linha 1 Topo: Amarelo Ouro 3D
    f_l1 = obter_fonte(145)
    bb1 = f_l1.getbbox(linha1)
    x1 = (W - (bb1[2] - bb1[0])) // 2
    y1 = 135
    desenhar_texto_3d_luxo(ImageDraw.Draw(canvas), (x1, y1), linha1, f_l1, cor_face=(255, 225, 10), cor_extrusao=(170, 20, 20), profundidade=16)
    
    # 7. Linha 2 Topo: Branco Neve 3D com chanfro vermelho
    f_l2 = obter_fonte(185)
    bb2 = f_l2.getbbox(linha2)
    x2 = (W - (bb2[2] - bb2[0])) // 2
    y2 = y1 + (bb1[3] - bb1[1]) + 30
    desenhar_texto_3d_luxo(ImageDraw.Draw(canvas), (x2, y2), linha2, f_l2, cor_face=(255, 255, 255), cor_extrusao=(180, 15, 15), profundidade=18)
    
    # 8. Preço Chamativo no Topo Direito (3D Ouro)
    f_pr = obter_fonte(78)
    bb_pr = f_pr.getbbox(preco_str)
    x_pr = W - (bb_pr[2] - bb_pr[0]) - 50
    y_pr = y2 + (bb2[3] - bb2[1]) + 25
    desenhar_texto_3d_luxo(ImageDraw.Draw(canvas), (x_pr, y_pr), preco_str, f_pr, cor_face=(255, 235, 10), cor_extrusao=(160, 20, 20), profundidade=10)
    
    # 9. Rodapé Oficial de Conversão
    footer_path = "resource/templates/boutique_full_footer.png"
    if os.path.exists(footer_path):
        ft = Image.open(footer_path).convert("RGBA")
        ft_w = W
        ft_h = int(ft.height * (ft_w / ft.width))
        ft = ft.resize((ft_w, ft_h), Image.LANCZOS)
        canvas.paste(ft, (0, H - ft_h), ft)
        
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    canvas.convert("RGB").save(caminho_saida, "JPEG", quality=95)
    print(f"Capa Direta Salva com Sucesso: {caminho_saida}")

if __name__ == "__main__":
    itens = [
        {
            "img": "canais/canal_04_achadinhos_moda_feminina/novos_produtos_virais/blazer_luxo.jpg",
            "l1": "CONJUNTO ALFAIATARIA",
            "l2": "DE LUXO!",
            "preco": "Apenas R$ 208,42!",
            "out": "canais/canal_04_achadinhos_moda_feminina/capa_direta_blazer_luxo.jpg"
        },
        {
            "img": "canais/canal_04_achadinhos_moda_feminina/novos_produtos_virais/calca_alfaiataria.jpg",
            "l1": "CALÇA ALFAIATARIA",
            "l2": "DE LUXO!",
            "preco": "Apenas R$ 153,61!",
            "out": "canais/canal_04_achadinhos_moda_feminina/capa_direta_calca_luxo.jpg"
        },
        {
            "img": r"C:\Users\Uni-CvFCT-EdmilsonGi\.gemini\antigravity\brain\b901018f-b028-48f4-8dbc-57b0a2faea06\sapato_bigtree.jpg",
            "l1": "SCARPIN DE SALTO",
            "l2": "PERFEITO!",
            "preco": "Apenas R$ 76,68!",
            "out": "canais/canal_04_achadinhos_moda_feminina/capa_direta_scarpin_luxo.jpg"
        },
        {
            "img": r"C:\Users\Uni-CvFCT-EdmilsonGi\.gemini\antigravity\brain\b901018f-b028-48f4-8dbc-57b0a2faea06\temp_prod_1005008929627083.jpg",
            "l1": "A BOLSA PERFEITA",
            "l2": "DE LUXO!",
            "preco": "Apenas R$ 89,90!",
            "out": "canais/canal_04_achadinhos_moda_feminina/capa_direta_bolsa_luxo.jpg"
        }
    ]
    
    for it in itens:
        compor_capa_direta_aliexpress(it["img"], it["l1"], it["l2"], it["preco"], it["out"])
