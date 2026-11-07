import os
import re
import time
import hmac
import hashlib
import json
import urllib.parse
import urllib.request
from typing import List, Dict, Optional
from loguru import logger


def _load_env(filepath: str = ".env") -> Dict[str, str]:
    env = {}
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_credentials() -> Dict[str, str]:
    env = _load_env(".env")
    return {
        "app_key": env.get("ALIEXPRESS_APP_KEY") or os.environ.get("ALIEXPRESS_APP_KEY", ""),
        "app_secret": env.get("ALIEXPRESS_APP_SECRET") or os.environ.get("ALIEXPRESS_APP_SECRET", ""),
        "tracking_id": env.get("ALIEXPRESS_TRACKING_ID") or os.environ.get("ALIEXPRESS_TRACKING_ID", "default"),
    }


def _sign_request(secret: str, params: Dict[str, str]) -> str:
    sorted_keys = sorted(params.keys())
    query = "".join(f"{k}{params[k]}" for k in sorted_keys if params[k] is not None)
    return hmac.new(secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest().upper()


def call_aliexpress_api(method: str, biz_params: Dict[str, str]) -> Dict:
    creds = get_credentials()
    app_key = creds["app_key"]
    app_secret = creds["app_secret"]
    if not app_key or not app_secret:
        raise ValueError("Credenciais ALIEXPRESS_APP_KEY ou ALIEXPRESS_APP_SECRET ausentes no ficheiro .env")

    url = "https://api-sg.aliexpress.com/sync"
    sys_params = {
        "app_key": app_key,
        "method": method,
        "sign_method": "sha256",
        "timestamp": str(int(time.time() * 1000)),
        "format": "json",
        "v": "2.0",
    }
    all_params = {**sys_params, **{k: str(v) for k, v in biz_params.items() if v is not None}}
    all_params["sign"] = _sign_request(app_secret, all_params)

    data = urllib.parse.urlencode(all_params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_short_affiliate_link(source_url: str, tracking_id: Optional[str] = None) -> str:
    """Converte uma URL de produto do AliExpress num link curto oficial https://s.click.aliexpress.com/e/..."""
    creds = get_credentials()
    tid = tracking_id or creds["tracking_id"] or "default"
    try:
        res = call_aliexpress_api(
            "aliexpress.affiliate.link.generate",
            {
                "promotion_link_type": "0",
                "source_values": source_url,
                "tracking_id": tid,
            },
        )
        links = (
            res.get("aliexpress_affiliate_link_generate_response", {})
            .get("resp_result", {})
            .get("result", {})
            .get("promotion_links", {})
            .get("promotion_link", [])
        )
        if links and links[0].get("promotion_link"):
            return links[0]["promotion_link"]
    except Exception as e:
        logger.warning(f"Falha ao encurtar link AliExpress: {e}")
    return source_url


def limpiar_titulo_moda(raw_title: str) -> str:
    """Transforma títulos longos/literais de SEO do AliExpress num título curto, elegante e natural para Shorts."""
    if not raw_title:
        return "Conjunto Feminino Elegante que Valoriza o Corpo"
    clean = re.sub(r"\b(202[3-7]|hxao|dulzura|traf|za|shein|y2k|dropshipping|atacado|mulheres|feminino|femininos|feminina|para mulher)\b", "", raw_title, flags=re.IGNORECASE)
    substituicoes = [
        (r"\bdeslizamento\b", "Vestido Slip Dress"),
        (r"\bmagro\b", "Modelador"),
        (r"\bsem costas\b", "Costas Abertas"),
        (r"\btopo\b", "Top"),
        (r"\btpos\b", "Tops"),
        (r"\btanque\b", "Elegante"),
        (r"\bsólido\b", "Liso"),
        (r"\bclube rua outfit\b", "Look Noite"),
    ]
    for padrao, novo in substituicoes:
        clean = re.sub(padrao, novo, clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+", " ", clean).strip(" ,.-|/")
    words = clean.split()
    if len(words) > 7:
        clean = " ".join(words[:7])
    # Detect category dynamically from raw_title
    raw_lower = (raw_title or "").lower()
    if any(w in raw_lower for w in ["bolsa", "bag", "handbag", "carteira", "mochila"]):
        prefix = "Bolsa "
    elif any(w in raw_lower for w in ["relogio", "relógio", "watch"]):
        prefix = "Relógio "
    elif any(w in raw_lower for w in ["colar", "brinco", "anel", "pulseira", "semijoia", "joia"]):
        prefix = "Acessório "
    elif any(w in raw_lower for w in ["sapato", "salto", "sandalia", "sandália", "scarpin", "tenis", "tênis"]):
        prefix = "Calçado "
    elif any(w in raw_lower for w in ["oculos", "óculos"]):
        prefix = "Óculos "
    elif any(w in raw_lower for w in ["conjunto", "terno", "blazer", "alfaiataria"]):
        prefix = "Conjunto "
    elif any(w in raw_lower for w in ["maquiagem", "batom", "skincare", "base"]):
        prefix = "Item de Beleza "
    else:
        prefix = "Peça "

    if not any(w in clean.lower() for w in ["vestido", "conjunto", "top", "blusa", "saia", "macacão", "bolsa", "relógio", "relogio", "colar", "sapato", "salto", "óculos", "oculos"]):
        clean = prefix + clean
    return clean[:60].title()


def search_winning_fashion_products(
    keywords: str = "vestido feminino elegante",
    page_size: int = 40,
    page_no: int = 1,
    sort_type: str = "LAST_VOLUME_DESC",
    only_with_video: bool = False,
    target_currency: str = "BRL",
    target_language: str = "PT",
) -> List[Dict]:
    """
    Busca produtos campeões de vendas na API de Afiliados do AliExpress (em PT)
    e retorna os preços sempre em DÓLAR Universal (US$), priorizando produtos com vídeo .mp4.
    """
    creds = get_credentials()
    tracking_id = creds["tracking_id"] or "default"

    res = call_aliexpress_api(
        "aliexpress.affiliate.product.query",
        {
            "keywords": keywords,
            "target_currency": "BRL",
            "target_language": target_language,
            "tracking_id": tracking_id,
            "page_no": str(max(1, page_no)),
            "page_size": str(min(max(page_size, 5), 50)),
            "sort": sort_type,
        },
    )

    raw_products = (
        res.get("aliexpress_affiliate_product_query_response", {})
        .get("resp_result", {})
        .get("result", {})
        .get("products", {})
        .get("product", [])
    )

    parsed_list = []
    for p in raw_products:
        video_url = (p.get("product_video_url") or "").strip()
        if only_with_video and not video_url:
            continue

        small_imgs = p.get("product_small_image_urls", {}).get("string", [])
        main_img = p.get("product_main_image_url", "")
        all_images = []
        if main_img:
            all_images.append(main_img)
        for img in small_imgs:
            if img and img not in all_images:
                all_images.append(img)

        detail_url = p.get("product_detail_url") or p.get("promotion_link") or ""
        short_link = generate_short_affiliate_link(detail_url, tracking_id) if detail_url else p.get("promotion_link", "")

        raw_title = p.get("product_title", "Peça de Moda Feminina")
        short_title = limpiar_titulo_moda(raw_title)

        comm_str = p.get("commission_rate") or p.get("hot_product_commission_rate") or "0%"
        try:
            comm_val = float(comm_str.replace("%", "").strip())
        except Exception:
            comm_val = 0.0

        volume = 0
        try:
            volume = int(p.get("lastest_volume") or 0)
        except Exception:
            volume = 0

        # Extrair preço em USD (Dólar Universal)
        sale_curr = (p.get("sale_price_currency") or "").upper()
        raw_sale = p.get("sale_price") or p.get("target_sale_price") or ""
        raw_orig = p.get("original_price") or p.get("target_original_price") or ""
        try:
            val_sale = float(str(raw_sale).replace(",", "."))
            if sale_curr != "USD" and (p.get("target_sale_price_currency") == "BRL" or sale_curr == "BRL"):
                val_sale = round(val_sale / 5.50, 2)
            usd_sale_str = f"US$ {val_sale:.2f}"
        except Exception:
            usd_sale_str = f"US$ {raw_sale}" if raw_sale else "US$ 9.90"

        try:
            val_orig = float(str(raw_orig).replace(",", "."))
            if sale_curr != "USD" and (p.get("target_original_price_currency") == "BRL" or sale_curr == "BRL"):
                val_orig = round(val_orig / 5.50, 2)
            usd_orig_str = f"US$ {val_orig:.2f}"
        except Exception:
            usd_orig_str = ""

        parsed_list.append({
            "product_id": str(p.get("product_id", "")),
            "raw_title": raw_title,
            "short_title": short_title,
            "sale_price": usd_sale_str,
            "original_price": usd_orig_str,
            "discount": p.get("discount", ""),
            "commission_rate": comm_str,
            "commission_val": comm_val,
            "orders_volume": volume,
            "evaluate_rate": p.get("evaluate_rate", ""),
            "video_url": video_url,
            "has_video": bool(video_url),
            "main_image": main_img,
            "images": all_images[:6],
            "short_link": short_link,
            "detail_url": detail_url,
        })

    # Ordena priorizando: 1) Produtos com vídeo .mp4 oficial, 2) Maior volume de vendas
    parsed_list.sort(key=lambda x: (1 if x["has_video"] else 0, x["orders_volume"], x["commission_val"]), reverse=True)
    return parsed_list


def download_product_assets(product: Dict, dest_dir: str) -> Dict[str, List[str]]:
    """
    Baixa o vídeo .mp4 nativo do AliExpress (se disponível) e as fotos HD do produto
    para a pasta temporária de renderização.
    """
    os.makedirs(dest_dir, exist_ok=True)
    downloaded_videos = []
    downloaded_images = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    video_url = product.get("video_url", "")
    if video_url:
        try:
            vid_path = os.path.join(dest_dir, f"ali_official_{product.get('product_id', 'vid')}.mp4")
            req = urllib.request.Request(video_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp, open(vid_path, "wb") as out:
                out.write(resp.read())
            if os.path.exists(vid_path) and os.path.getsize(vid_path) > 80000:
                downloaded_videos.append(vid_path)
                logger.info(f"Vídeo oficial AliExpress baixado com sucesso: {vid_path}")
        except Exception as e:
            logger.warning(f"Não foi possível baixar vídeo do produto AliExpress ({video_url}): {e}")

    for idx, img_url in enumerate(product.get("images", [])[:5], 1):
        try:
            ext = ".jpg"
            if ".png" in img_url.lower():
                ext = ".png"
            img_path = os.path.join(dest_dir, f"ali_img_{idx:02d}{ext}")
            req = urllib.request.Request(img_url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp, open(img_path, "wb") as out:
                out.write(resp.read())
            if os.path.exists(img_path) and os.path.getsize(img_path) > 5000:
                downloaded_images.append(img_path)
        except Exception as e:
            logger.warning(f"Erro ao baixar imagem {img_url}: {e}")

    return {"videos": downloaded_videos, "images": downloaded_images}


def fetch_affiliate_orders(start_time: str = "2026-10-01 00:00:00", end_time: str = "2026-10-31 23:59:59") -> List[Dict]:
    """
    Consulta automaticamente as vendas e comissões geradas na conta AliExpress Afiliados.
    """
    try:
        res = call_aliexpress_api(
            "aliexpress.affiliate.order.list",
            {
                "start_time": start_time,
                "end_time": end_time,
                "status": "Payment Completed",
                "page_no": "1",
                "page_size": "50",
            },
        )
        orders = (
            res.get("aliexpress_affiliate_order_list_response", {})
            .get("resp_result", {})
            .get("result", {})
            .get("orders", {})
            .get("order", [])
        )
        return orders if isinstance(orders, list) else []
    except Exception as e:
        logger.warning(f"Erro ao consultar pedidos AliExpress: {e}")
        return []
