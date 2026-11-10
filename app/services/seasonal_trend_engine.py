"""
app/services/seasonal_trend_engine.py

Motor Autônomo de Inteligência Sazonal & Climatização Comercial:
Calcula automaticamente a estação do ano, datas comemorativas e tendências
climáticas para alternar dinamicamente os parâmetros de busca de produtos virais
e os ângulos de persuasão da Dupla IA, sem necessitar de intervenção manual.
"""

from datetime import datetime
from typing import Dict, List
from loguru import logger

def detectar_contexto_sazonal(mes: int = None, dia: int = None) -> Dict:
    """
    Identifica dinamicamente a estação, eventos de pico e clima comercial.
    Considera o calendário global de e-commerce e público-alvo (PT / Europa / BR).
    """
    now = datetime.now()
    m = mes if mes is not None else now.month
    d = dia if dia is not None else now.day

    # 1. Eventos Comerciais de Pico Imediato
    evento_especial = None
    if m == 11:
        if d >= 15:
            evento_especial = "Black Friday / Cyber Monday (Foco em Super Descontos & Presentes de Luxo)"
        else:
            evento_especial = "Esquenta Black Friday / Lançamentos de Inverno"
    elif m == 12:
        if d <= 22:
            evento_especial = "Natal & Presentes de Luxo Fim de Ano"
        else:
            evento_especial = "Réveillon / Look Ano Novo (Branco, Dourado, Prata)"
    elif m == 1:
        evento_especial = "Liquidação de Inverno / Renovação de Guarda-Roupa"
    elif m == 5 and d <= 12:
        evento_especial = "Dia das Mães (Presentes Emocionais, Joias, Bolsas)"

    # 2. Definição da Estação e Climatização
    # Novembro a Março: Inverno / Frio Intenso (Hemisfério Norte / Europa / Portugal / Natal)
    # Abril a Maio: Primavera (Cores suaves, meia-estação)
    # Junho a Agosto: Verão Alto (Tecidos frescos, vestidos fluidos, praia)
    # Setembro a Outubro: Outono (Tons terrosos, camadas leves)
    
    if m in (11, 12, 1, 2):
        estacao = "inverno"
        rotulo_clima = "❄️ Temporada Outono/Inverno (Frio, Aconchego & Alto Ticket)"
        termos_principais = [
            # Peças quentes e virais de frio
            "meia calca termica feminina translucida forrada",
            "casaco sobretudo feminino la batida elegante",
            "trench coat feminino classico elegante",
            "sueter feminino gola alta cashmere trico",
            "cardigan feminino tricot longo luxo",
            "bota feminina cano curto couro salto grosso",
            "bota feminina montaria cano longo confortavel",
            "jaqueta feminina forrada couro sintetico",
            "cachecol pashmina feminina luxo macia",
            "vestido trico midi manga longa outono inverno",
            # Acessórios de luxo de inverno
            "bolsa feminina couro luxo ombro",
            "bolsa tote feminina elegante trabalho",
            "relogio feminino luxo dourado quartzo",
            "colar feminino banhado ouro 18k elegante",
            "blazer alfaiataria feminino elegante slim",
            "secador escova alisadora modeladora 5 em 1"
        ]
        diretriz_ia = (
            "TEMPORADA ATUAL: OUTONO / INVERNO. "
            "Enfatize aconchego, aquecimento sem perder o corte elegante, tecidos encorpados, "
            "proteção contra o vento/frio e sofisticação discreta (looks com casacos, botas e meia térmica)."
        )

    elif m in (3, 4, 5):
        estacao = "primavera"
        rotulo_clima = "🌸 Temporada de Primavera / Meia-Estação"
        termos_principais = [
            "blazer alfaiataria feminino elegante slim",
            "conjunto linho feminino elegante alfaiataria",
            "vestido midi floral elegante soltinho",
            "camisa feminina seda social elegante",
            "calca pantalona alfaiataria feminina luxo",
            "cardigan feminino leve meia estacao",
            "bolsa feminina couro luxo ombro",
            "sapato feminino scarpin bico fino elegante",
            "mule feminina elegante confortavel couro",
            "brinco perola feminino luxo sofisticado",
            "organizador maquiagem acrilico giratorio"
        ]
        diretriz_ia = (
            "TEMPORADA ATUAL: PRIMAVERA. "
            "Enfatize renovação, frescor, cores alegres e sofisticadas, tecidos leves com caimento fluido "
            "e peças versáteis de transição para o dia a dia e trabalho."
        )

    elif m in (6, 7, 8):
        estacao = "verão"
        rotulo_clima = "☀️ Temporada de Verão (Frescor, Linho & Praia Chique)"
        termos_principais = [
            "vestido midi linho elegante soltinho",
            "vestido chemise feminino elegante verao",
            "conjunto linho feminino cropped calca",
            "sandalia feminina salto bloco confortavel",
            "oculos escuros feminino luxo polarizado",
            "bolsa feminina palha praia luxo",
            "vestido longo estampado floral fresco",
            "saida de praia feminina luxo elegante",
            "relogio feminino luxo dourado quartzo",
            "organizador maquiagem acrilico giratorio"
        ]
        diretriz_ia = (
            "TEMPORADA ATUAL: ALTO VERÃO. "
            "Enfatize frescor máximo, respirabilidade dos tecidos (linho e algodão puro), "
            "conforto sem colar na pele, leveza em dias quentes e elegância em passeios, viagens e eventos."
        )

    else: # 9, 10
        estacao = "outono"
        rotulo_clima = "🍂 Temporada de Outono (Tons Terrosos & Alfaiataria)"
        termos_principais = [
            "trench coat feminino classico elegante",
            "blazer alfaiataria feminino elegante slim",
            "calca pantalona alfaiataria feminina luxo",
            "vestido midi manga longa elegante",
            "sueter feminino tricot gola v elegante",
            "bota feminina cano curto couro salto grosso",
            "bolsa feminina couro luxo ombro",
            "colar feminino banhado ouro 18k elegante",
            "pashmina feminina xale macio elegante"
        ]
        diretriz_ia = (
            "TEMPORADA ATUAL: OUTONO. "
            "Enfatize elegância de sobreposição (camadas leves), tons quentes e terrosos, "
            "modelagem impecável de alfaiataria e conforto térmico para o início do frio."
        )

    return {
        "mes": m,
        "estacao": estacao,
        "rotulo_clima": rotulo_clima,
        "evento_especial": evento_especial,
        "termos_busca": termos_principais,
        "diretriz_ia": diretriz_ia
    }

def obter_termo_busca_inteligente() -> str:
    """Retorna um termo de busca calibrado dinamicamente para o momento e estação atual."""
    import random
    contexto = detectar_contexto_sazonal()
    termo = random.choice(contexto["termos_busca"])
    logger.info(f"🌾 [CLIMATIZAÇÃO COMERCIAL] Estação: {contexto['estacao'].upper()} | Termo selecionado: '{termo}'")
    return termo
