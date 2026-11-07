import os
import re
import urllib.request
from typing import List, Optional, Dict
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from loguru import logger


def _load_font(size: int, style: str = "bold") -> ImageFont.FreeTypeFont:
    candidates = []
    if style == "bold":
        candidates = [
            os.path.join("resource", "fonts", "BeVietnamPro-Bold.ttf"),
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\impact.ttf",
        ]
    elif style == "impact":
        candidates = [
            r"C:\Windows\Fonts\impact.ttf",
            os.path.join("resource", "fonts", "BeVietnamPro-Bold.ttf"),
            r"C:\Windows\Fonts\arialbd.ttf",
        ]
    elif style == "script":
        candidates = [
            os.path.join("resource", "fonts", "Charm-Bold.ttf"),
            r"C:\Windows\Fonts\georgia.ttf",
            os.path.join("resource", "fonts", "BeVietnamPro-Bold.ttf"),
        ]
    else:
        candidates = [
            os.path.join("resource", "fonts", "BeVietnamPro-Medium.ttf"),
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    words = text.split()
    lines = []
    current = []
    for w in words:
        test_line = " ".join(current + [w])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width or not current:
            current.append(w)
        else:
            lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines[:3]


def _draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    pos: tuple,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    shadow_color: tuple = (0, 0, 0, 230),
    shadow_offset: int = 5,
    stroke_width: int = 3,
    stroke_fill: tuple = (0, 0, 0, 255),
):
    x, y = pos
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color, stroke_width=stroke_width, stroke_fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def gerar_capa_promocional_moda(
    output_path: str,
    titulo_curto: str,
    image_paths: List[str],
    preco: str = "",
    desconto: str = "",
    subtitulo_ia: str = "MODELA O CORPO • PURO LUXO",
) -> Optional[str]:
    """
    Gera uma capa promocional 9:16 (1080x1920) digna de campanha de moda de luxo (Alana Cruz):
    - Usa a foto de estúdio HD real do produto (sem legendas queimadas do vídeo)
    - Melhoria automática de cor, nitidez e contraste de estúdio
    - Moldura secundária VIP (detalhe do tecido/costas) se houver 2+ fotos
    - Selo de preço promocional em Rosa/Dourado
    - Tipografia de revista de moda + Botão CTA 'LINK NO 1º COMENTÁRIO'
    """
    try:
        W, H = 1080, 1920
        valid_imgs = [p for p in (image_paths or []) if p and os.path.exists(p)]
        if not valid_imgs:
            return None

        # 1. Garantir 100% foto real do produto (escolhendo o ângulo mais nítido/estúdio da galeria oficial do anúncio)
        main_img_path = valid_imgs[1] if len(valid_imgs) >= 2 else valid_imgs[0]
        sec_img_path = valid_imgs[0] if len(valid_imgs) >= 2 else None

        base_img = Image.open(main_img_path).convert("RGB")
        iw, ih = base_img.size
        target_ratio = W / H
        img_ratio = iw / ih

        if img_ratio > target_ratio:
            new_h = H
            new_w = int(H * img_ratio)
        else:
            new_w = W
            new_h = int(W / img_ratio)

        # Foto real do produto enquadrada com tratamento de estúdio de revista
        bg_blur = base_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - W) // 2
        top = (new_h - H) // 2
        canvas = bg_blur.crop((left, top, left + W, top + H))
        canvas = ImageEnhance.Contrast(canvas).enhance(1.10)
        canvas = ImageEnhance.Color(canvas).enhance(1.14)
        canvas = ImageEnhance.Sharpness(canvas).enhance(1.40)
        canvas = canvas.convert("RGBA")

        # 2. Aplicar gradiente cinematográfico suave no topo e na base (para leitura perfeita sem tapar a peça)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)

        # Gradiente superior (0 a 260px)
        for y in range(260):
            alpha = int(185 * (1 - (y / 260) ** 1.4))
            ov_draw.line([(0, y), (W, y)], fill=(18, 6, 14, alpha))

        # Gradiente inferior (1180 a 1920px) em tom vinho/preto sofisticado
        for y in range(1180, H):
            progress = (y - 1180) / (H - 1180)
            alpha = int(245 * (progress ** 1.15))
            ov_draw.line([(0, y), (W, y)], fill=(16, 5, 12, min(alpha, 242)))

        canvas = Image.alpha_composite(canvas, overlay)
        draw = ImageDraw.Draw(canvas)

        # 3. Topo: Badge Oficial "ALANA CRUZ • ACHADINHO VIRAL"
        font_badge = _load_font(32, "bold")
        badge_text = "★ ALANA CRUZ • ACHADINHO VIRAL ★"
        tb = draw.textbbox((0, 0), badge_text, font=font_badge)
        tw = tb[2] - tb[0]
        th = tb[3] - tb[1]
        bw = tw + 84
        bh = 74
        bx = (W - bw) // 2
        by = 58
        draw.rounded_rectangle([bx + 4, by + 6, bx + bw + 4, by + bh + 6], radius=37, fill=(0, 0, 0, 140))
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=37, fill=(24, 10, 20, 235), outline=(244, 114, 182, 255), width=3)
        draw.text((bx + (bw - tw) // 2, by + (bh - th) // 2 - 4), badge_text, font=font_badge, fill=(253, 224, 71, 255))

        # 4. Janela VIP com o 2º ângulo REAL do mesmo produto
        if sec_img_path and os.path.exists(sec_img_path):
            try:
                sec_img = Image.open(sec_img_path).convert("RGBA")
                thumb_w, thumb_h = 290, 370
                sw, sh = sec_img.size
                s_ratio = sw / sh
                t_ratio = thumb_w / thumb_h
                if s_ratio > t_ratio:
                    nh = thumb_h
                    nw = int(thumb_h * s_ratio)
                else:
                    nw = thumb_w
                    nh = int(thumb_w / s_ratio)
                sec_crop = sec_img.resize((nw, nh), Image.Resampling.LANCZOS).crop(((nw - thumb_w) // 2, (nh - thumb_h) // 2, (nw - thumb_w) // 2 + thumb_w, (nh - thumb_h) // 2 + thumb_h))

                mask = Image.new("L", (thumb_w, thumb_h), 0)
                m_draw = ImageDraw.Draw(mask)
                m_draw.rounded_rectangle([0, 0, thumb_w, thumb_h], radius=36, fill=255)

                ix, iy = W - thumb_w - 42, 175
                draw.rounded_rectangle([ix - 2, iy + 6, ix + thumb_w + 10, iy + thumb_h + 12], radius=40, fill=(0, 0, 0, 150))
                draw.rounded_rectangle([ix - 6, iy - 6, ix + thumb_w + 6, iy + thumb_h + 6], radius=40, fill=(250, 204, 21, 255))
                canvas.paste(sec_crop, (ix, iy), mask)
                draw = ImageDraw.Draw(canvas)
            except Exception as e_sec:
                logger.warning(f"Erro ao inserir 2ª foto na capa: {e_sec}")

        # 5. Selo de Preço Promocional em DÓLAR Universal (US$)
        preco_limpo = re.sub(r"(USD|US\$|BRL|R\$|EUR)", "", preco or "", flags=re.IGNORECASE).strip()
        if preco_limpo:
            try:
                val_f = float(preco_limpo.replace(",", "."))
                preco_fmt = f"US$ {val_f:,.2f}"
            except Exception:
                preco_fmt = f"US$ {preco_limpo}"
        else:
            preco_fmt = "OFERTA VIP"

        px, py = 46, 1205
        pw, ph = 430, 134
        draw.rounded_rectangle([px + 6, py + 8, px + pw + 6, py + ph + 8], radius=26, fill=(0, 0, 0, 175))
        draw.rounded_rectangle([px, py, px + pw, py + ph], radius=26, fill=(219, 39, 119, 255), outline=(253, 224, 71, 255), width=4)
        font_tag_top = _load_font(25, "bold")
        font_tag_price = _load_font(56, "bold")
        draw.text((px + 28, py + 14), "SUPER DESCONTO HOJE", font=font_tag_top, fill=(254, 240, 138, 255))
        draw.text((px + 28, py + 48), preco_fmt, font=font_tag_price, fill=(255, 255, 255, 255))

        # 6. Título Principal Editorial (Grande, limpo e magnético)
        font_title = _load_font(72, "bold")
        clean_headline = re.sub(r"\b(sexy|mulheres|feminino)\b", "", titulo_curto, flags=re.IGNORECASE).strip()
        clean_headline = re.sub(r"\s+", " ", clean_headline).upper()
        lines = _wrap_text(clean_headline, font_title, W - 96, draw)

        y_cursor = 1368
        for idx_l, line in enumerate(lines[:2]):
            color_line = (255, 255, 255, 255) if idx_l == 0 else (253, 224, 71, 255)
            _draw_text_with_shadow(draw, (48, y_cursor), line, font_title, fill=color_line, shadow_offset=5, stroke_width=3)
            y_cursor += 86

        # 7. Subtítulo de Benefício
        font_sub = _load_font(36, "bold")
        clean_sub = re.sub(r"[^\w\s•\-★]", "", subtitulo_ia).strip().upper()
        draw.text((50, y_cursor + 12), f"★ {clean_sub}", font=font_sub, fill=(249, 168, 212, 255))

        # 8. Botão CTA Inferior de Alta Conversão (100% Centralizado)
        btn_x, btn_y = 48, 1720
        btn_w, btn_h = W - 96, 114
        draw.rounded_rectangle([btn_x + 4, btn_y + 8, btn_x + btn_w + 4, btn_y + btn_h + 8], radius=57, fill=(0, 0, 0, 170))
        draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h], radius=57, fill=(250, 204, 21, 255), outline=(255, 255, 255, 255), width=4)
        font_cta = _load_font(38, "bold")
        cta_txt = "LINK COM DESCONTO NO 1º COMENTÁRIO"
        ctb = draw.textbbox((0, 0), cta_txt, font=font_cta)
        ctw = ctb[2] - ctb[0]
        cth = ctb[3] - ctb[1]
        ctx = btn_x + (btn_w - ctw) // 2
        cty = btn_y + (btn_h - cth) // 2 - 6
        draw.text((ctx, cty), cta_txt, font=font_cta, fill=(15, 23, 42, 255))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        canvas.convert("RGB").save(output_path, "JPEG", quality=95)
        logger.success(f"Capa Promocional IA (Alana Cruz) gerada com sucesso: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Erro ao gerar capa promocional moda: {e}")
        return None


def gerar_capa_futebol_profissional(
    output_path: str,
    frame_image_path: str,
    titulo: str,
    is_doc: bool = False,
    subtitulo: str = "BASTIDORES & INVESTIGAÇÃO",
) -> Optional[str]:
    """
    Gera capa ULTRA-VIRAL de Futebol Invisível (padrão compor_capas_virais_futebol.py):
    - Pesquisa as capas dos vídeos mais clicados e com maior CTR no YouTube para usar como benchmark
    - Tenta primeiro gerar a arte fotográfica 8k de cinema via Gemini Imagen 3.0 orientada pelas referências
    - Contraste dramático de estádio + vinheta dupla (topo e base)
    - Tarja vermelha de urgência no topo + Fonte IMPACT gigante com contorno preto grosso (stroke 12px) em Branco/Amarelo Ouro/Vermelho
    """
    try:
        W, H = (1280, 720) if is_doc else (1080, 1920)
        base = None

        # 0) Pesquisar capas de concorrentes que mais atraíram cliques no YouTube
        referencias_concorrentes = []
        try:
            from app.services.spy_thumbnails import pesquisar_capas_referencia_virais
            referencias_concorrentes = pesquisar_capas_referencia_virais(titulo, max_referencias=2)
            if referencias_concorrentes:
                logger.info(f"Capas concorrentes de referência com alto CTR obtidas: {[r['title'] for r in referencias_concorrentes]}")
        except Exception as e_ref:
            logger.warning(f"Não foi possível obter referências de capas concorrentes: {e_ref}")

        # 1) Tentar gerar arte cinematográfica 8k com Gemini Imagen orientada pelo benchmark
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY") or ""
            if not api_key:
                try:
                    from app.config import config as app_cfg
                    api_key = app_cfg.app.get("gemini_api_key") or ""
                except Exception:
                    pass
            if api_key and ("clean_frame" in str(frame_image_path) or not os.path.exists(str(frame_image_path))):
                from google import genai
                import io
                client = genai.Client(api_key=api_key)
                
                # Incorporar padrão de alto clique dos concorrentes no prompt
                benchmarks_txt = ""
                if referencias_concorrentes:
                    benchmarks_txt = f" Inspired by viral YouTube thumbnails: dramatic facial expressions, high contrast, intense sports rivalry."
                
                aspect_str = "16:9" if is_doc else "9:16"
                prompt_ia = (
                    f"A hyper-realistic, dramatic 8k sports photojournalism thumbnail for YouTube about: {titulo}. "
                    "Close-up emotional portrait of the football star wearing current official club jersey, looking intense or stressed, "
                    "in modern illuminated stadium at night with stadium floodlights, lens flare, rain drops, atmospheric smoke and sparks. "
                    f"{benchmarks_txt} Cinematic color grading, 85mm portrait lens, shallow depth of field, leave clean negative space on the left and top for typography. "
                    "NO text, NO letters, NO watermark on the image."
                )
                # Modelos oficiais de geração de imagens do Google Gemini / Imagen 3.0
                for model_name in ["imagen-3.0-generate-002", "imagen-3.0-fast-generate-001", "gemini-2.5-flash-image", "gemini-2.0-flash-exp"]:
                    try:
                        if "imagen" in model_name:
                            asp_ratio = "16:9" if is_doc else "9:16"
                            result = client.models.generate_images(
                                model=model_name,
                                prompt=prompt_ia,
                                config=dict(
                                    number_of_images=1,
                                    aspect_ratio=asp_ratio,
                                    output_mime_type="image/jpeg",
                                    person_generation="ALLOW_ADULT"
                                )
                            )
                            if result.generated_images:
                                img_bytes = result.generated_images[0].image.image_bytes
                                base = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                        else:
                            resp_c = client.models.generate_content(
                                model=model_name,
                                contents=prompt_ia + (" Vertical 9:16 portrait aspect ratio." if not is_doc else " Horizontal 16:9 widescreen aspect ratio."),
                                config=dict(response_modalities=["IMAGE"]),
                            )
                            for part in resp_c.candidates[0].content.parts:
                                if getattr(part, "inline_data", None) and part.inline_data.data:
                                    base = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                                    break
                        if base is not None:
                            logger.success(f"Arte 8k de Futebol gerada via {model_name}!")
                            break
                    except Exception:
                        continue
        except Exception as e_ia:
            logger.info(f"Fallback para imagem base/frame na capa de futebol: {e_ia}")

        if base is None:
            if not os.path.exists(frame_image_path):
                return None
            base = Image.open(frame_image_path).convert("RGB")

        iw, ih = base.size
        target_ratio = W / H
        img_ratio = iw / ih
        if img_ratio > target_ratio:
            nh = H
            nw = int(H * img_ratio)
        else:
            nw = W
            nh = int(W / img_ratio)

        canvas = base.resize((nw, nh), Image.Resampling.LANCZOS).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        canvas = ImageEnhance.Contrast(canvas).enhance(1.20)
        canvas = ImageEnhance.Color(canvas).enhance(1.22)

        # Fontes IMPACT oficiais do Windows (como em compor_capas_virais_futebol.py)
        impact_path = r"C:\Windows\Fonts\impact.ttf"
        if not os.path.exists(impact_path):
            impact_path = FONT_BOLD

        def draw_impact_outline(draw_obj, pos, text, font, fill_color, outline_color=(0, 0, 0), stroke_w=10):
            x, y = pos
            for dx in range(-stroke_w, stroke_w + 1):
                for dy in range(-stroke_w, stroke_w + 1):
                    if dx * dx + dy * dy <= stroke_w * stroke_w:
                        draw_obj.text((x + dx, y + dy), text, font=font, fill=outline_color)
            draw_obj.text((x, y), text, font=font, fill=fill_color)

        # Extrair manchetes curtas e explosivas do título sem cortar palavras a meio
        palavras = [p for p in re.sub(r"[^A-ZÀ-Ú0-9\s?!$]", "", titulo.upper()).split() if p not in {"DE", "DO", "DA", "NO", "NA", "O", "A", "OS", "AS", "E", "QUE", "POR", "COM", "PARA", "UM", "UMA"}]
        if len(palavras) >= 4:
            topo_l1 = " ".join(palavras[:2])
            if len(topo_l1) > 15:
                topo_l1 = palavras[0]
                topo_l2 = (palavras[1] + (" " + palavras[2] if len(palavras[1]) + len(palavras[2]) <= 13 else "")) + "!"
                rodape_l1 = " ".join(palavras[3:6])[:24]
            else:
                topo_l2 = " ".join(palavras[2:4])
                if len(topo_l2) > 14:
                    topo_l2 = palavras[2] + "!"
                    rodape_l1 = " ".join(palavras[3:6])[:24]
                else:
                    topo_l2 = topo_l2 + "!"
                    rodape_l1 = " ".join(palavras[4:7])[:24] if len(palavras) > 4 else "BASTIDORES SECRETOS"
        else:
            topo_l1 = (palavras[0] if palavras else "BOMBA")
            topo_l2 = (palavras[1] + "!" if len(palavras) > 1 else "HISTÓRICO!")
            rodape_l1 = "A VERDADE DOS BASTIDORES"

        if is_doc:
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ov_draw = ImageDraw.Draw(overlay)
            for x in range(680):
                alpha = int(225 * (1 - (x / 680)))
                ov_draw.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
            canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(canvas)

            font_xl = ImageFont.truetype(impact_path, 115)
            font_lg = ImageFont.truetype(impact_path, 80)
            font_sm = ImageFont.truetype(impact_path, 42)

            draw.rectangle([40, 35, 560, 100], fill=(220, 20, 60))
            draw.text((60, 45), "URGENTE: DOSSIE EXCLUSIVO", font=font_sm, fill=(255, 255, 255))
            draw_impact_outline(draw, (40, 130), topo_l1, font_xl, fill_color=(255, 255, 0), stroke_w=10)
            draw_impact_outline(draw, (40, 260), topo_l2, font_xl, fill_color=(255, 40, 40), stroke_w=10)
            draw_impact_outline(draw, (40, 430), rodape_l1, font_lg, fill_color=(255, 255, 255), stroke_w=8)
        else:
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ov_draw = ImageDraw.Draw(overlay)
            for y in range(460):
                alpha = int(215 * (1 - y / 460))
                ov_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
            for y in range(1430, H):
                alpha = int(230 * ((y - 1430) / (H - 1430)))
                ov_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
            canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(canvas)

            font_xl = ImageFont.truetype(impact_path, 120)
            font_lg = ImageFont.truetype(impact_path, 88)
            font_md = ImageFont.truetype(impact_path, 66)
            font_sm = ImageFont.truetype(impact_path, 46)

            draw.rectangle([60, 60, 1020, 150], fill=(220, 20, 60))
            draw.text((95, 76), "BOMBA NOS BASTIDORES DO FUTEBOL!", font=font_sm, fill=(255, 255, 255))

            draw_impact_outline(draw, (70, 175), topo_l1, font_xl, fill_color=(255, 255, 255), stroke_w=12)
            draw_impact_outline(draw, (70, 305), topo_l2, font_xl, fill_color=(255, 215, 0), stroke_w=12)

            draw_impact_outline(draw, (70, 1515), rodape_l1, font_md, fill_color=(255, 255, 255), stroke_w=8)
            draw_impact_outline(draw, (70, 1610), subtitulo[:22].upper(), font_lg, fill_color=(255, 215, 0), stroke_w=10)

            draw.rectangle([70, 1755, 580, 1835], fill=(0, 0, 0))
            draw.text((95, 1770), "FUTEBOL INVISIVEL", font=font_sm, fill=(255, 255, 255))

        canvas.save(output_path, "JPEG", quality=95)
        return output_path
    except Exception as e:
        logger.error(f"Erro ao gerar capa de futebol: {e}")
        return None
