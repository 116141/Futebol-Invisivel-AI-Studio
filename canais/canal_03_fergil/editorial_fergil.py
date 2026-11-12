"""
Módulo Editorial do Canal FERGIL — Arquitetura de Alta Retenção & High-CPM
Fórmula Editorial dos 5 Pilares de Negócios, Poder, Dinheiro & IA:
1. Psicologia do Dinheiro & Construção de Riqueza
2. Bastidores de Grandes Impérios & Decisões Críticas
3. Modelos Mentais de Alta Performance & Foco
4. Inteligência Artificial, Inovação & Oportunidades do Futuro
5. Estratégias Executivas, Finanças & Podcasts de Elite

Estrutura de Roteiro Retentivo:
- Gancho Provocativo (0 - 4s): Abre com um número, quebra de paradigma ou perda chocante.
- Tensão Narrativa (4 - 18s): Contexto dos bastidores que 99% das pessoas desconhecem.
- O Princípio Invisível (18 - 35s): A lição prática que separa amadores de operadores de elite.
- Conclusão & CTA (35 - 45s): Chamada para ação que instiga o comentário e a inscrição no canal.
"""

from typing import Dict, List, Optional
import random

# ACERVO EDITORIAL EXPANDIDO FERGIL (25 PAUTAS DE ALTO RETORNO E RETENÇÃO)
PAUTAS_FERGIL_MULTIDIMENSIONAIS = [
    # PILAR 1: PSICOLOGIA DO DINHEIRO & RIQUEZA
    {
        "titulo": "A Diferença Crucial Entre Parecer Rico e Ter Liberdade Real",
        "tipo": "short",
        "pilar": "Psicologia Financeira",
        "gancho": "Gastar dinheiro para mostrar aos outros quanto dinheiro você tem é a forma mais rápida de ter menos dinheiro.",
        "palavras_chave": "Psicologia do Dinheiro, Riqueza, Morgan Housel, Mentalidade Financeira, FERGIL"
    },
    {
        "titulo": "A Armadilha do Estilo de Vida: Por Que Salários Altos Ainda Deixam Pessoas Pobres",
        "tipo": "doc",
        "pilar": "Psicologia Financeira",
        "gancho": "Ganhar 100 mil por mês e gastar 100 mil é apenas uma versão sofisticada de viver de salário em salário.",
        "palavras_chave": "Inflação de Estilo de Vida, Finanças Pessoais, Liberdade Financeira, FERGIL"
    },
    {
        "titulo": "O Paradoxo da Riqueza: O Dinheiro Compra Opções, Não Felicidade",
        "tipo": "short",
        "pilar": "Psicologia Financeira",
        "gancho": "O maior dividendo que o dinheiro paga não são carros ou relógios: é a capacidade de controlar o seu próprio tempo.",
        "palavras_chave": "Liberdade, Controle do Tempo, Sucesso Real, FERGIL"
    },
    {
        "titulo": "Por Que os Mais Ricos do Mundo Mantêm Rotinas Extremamente Simples",
        "tipo": "short",
        "pilar": "Psicologia Financeira",
        "gancho": "Warren Buffett mora na mesma casa desde 1958. A ostentação é a taxa que os inseguros pagam pela aprovação alheia.",
        "palavras_chave": "Warren Buffett, Simplicidade, Poder Silencioso, FERGIL"
    },
    {
        "titulo": "O Segredo dos Juros Compostos Silenciosos que Ninguém Tem Paciência Para Praticar",
        "tipo": "doc",
        "pilar": "Psicologia Financeira",
        "gancho": "Mais de 99% da fortuna de Warren Buffett foi acumulada depois dos seus 50 anos de idade.",
        "palavras_chave": "Juros Compostos, Investimentos, Paciência Estratégica, FERGIL"
    },

    # PILAR 2: BASTIDORES DE GRANDES IMPÉRIOS & DRAMAS CORPORATIVOS
    {
        "titulo": "A Demissão de Steve Jobs em 1985: A Lição Oculta Por Trás da Maior Queda da Apple",
        "tipo": "doc",
        "pilar": "Grandes Impérios",
        "gancho": "Steve Jobs foi expulso da empresa que ele mesmo criou na garagem de casa. O motivo real nunca foi incompetência.",
        "palavras_chave": "Steve Jobs, Apple, Liderança, Resiliência, Negócios, FERGIL"
    },
    {
        "titulo": "A Quase Falência da Nvidia: Como Jensen Huang Apostou Tudo e Criou um Monstro de 3 Trilhões",
        "tipo": "doc",
        "pilar": "Grandes Impérios",
        "gancho": "Em 1995, a Nvidia estava a 30 dias de declarar falência absoluta. Hoje, é a dona da espinha dorsal da IA mundial.",
        "palavras_chave": "Jensen Huang, Nvidia, Semicondutores, Risco Calculado, FERGIL"
    },
    {
        "titulo": "O Dia em que Jeff Bezos Quase Perdeu a Amazon no Estouro da Bolha Dotcom",
        "tipo": "doc",
        "pilar": "Grandes Impérios",
        "gancho": "Em 2000, as ações da Amazon despencaram mais de 90%. Wall Street chamava a empresa de 'Amazon.bomb'.",
        "palavras_chave": "Jeff Bezos, Amazon, Visão de Longo Prazo, FERGIL"
    },
    {
        "titulo": "Por Que a Netflix Destruiu a Blockbuster: A Decisão Arrogante de 50 Milhões",
        "tipo": "short",
        "pilar": "Grandes Impérios",
        "gancho": "No ano 2000, o CEO da Blockbuster riu na cara dos fundadores da Netflix quando eles ofereceram a empresa por 50 milhões.",
        "palavras_chave": "Blockbuster, Netflix, Inovação Disruptiva, Negócios, FERGIL"
    },
    {
        "titulo": "A Regra de Ferro dos Bastidores da Formula 1: Como Toto Wolff Transformou a Mercedes em Máquina de Bilhões",
        "tipo": "short",
        "pilar": "Grandes Impérios",
        "gancho": "No automobilismo de elite, não vence quem tem o melhor motor: vence quem gerencia a psicologia do erro sem apontar culpados.",
        "palavras_chave": "Formula 1, Toto Wolff, Gestão de Elite, Cultura Organizacional, FERGIL"
    },

    # PILAR 3: MODELOS MENTAIS & ALTA PERFORMANCE
    {
        "titulo": "A Regra de Warren Buffett Para Dizer 'Não' a 99% das Oportunidades",
        "tipo": "short",
        "pilar": "Modelos Mentais",
        "gancho": "A diferença entre pessoas bem-sucedidas e pessoas verdadeiramente extraordinárias é que as extraordinárias dizem NÃO para quase tudo.",
        "palavras_chave": "Foco Implacável, Warren Buffett, Produtividade, Decisões, FERGIL"
    },
    {
        "titulo": "A Regra dos 5 Segundos de Elon Musk Para Decisões Sob Extrema Pressão",
        "tipo": "short",
        "pilar": "Modelos Mentais",
        "gancho": "Quando o cérebro humano hesita por mais de 5 segundos, o instinto de preservação mata a oportunidade.",
        "palavras_chave": "Elon Musk, Ação Imediata, Coragem Executiva, FERGIL"
    },
    {
        "titulo": "O Princípio 80/20 Aplicado ao Dinheiro: Onde Focar Suas Horas de Maior Alavancagem",
        "tipo": "short",
        "pilar": "Modelos Mentais",
        "gancho": "80% da sua renda e dos seus resultados derivam de apenas 20% das decisões que você toma na semana.",
        "palavras_chave": "Princípio de Pareto, Alavancagem, Gestão de Tempo, FERGIL"
    },
    {
        "titulo": "A Filosofia dos Primeiros Princípios: Como Pensar de Forma Original e Criar Vantagem Injusta",
        "tipo": "doc",
        "pilar": "Modelos Mentais",
        "gancho": "A maioria das pessoas raciocina por analogia: copia o que já existe. Os inovadores decompõem a realidade nas verdades fundamentais.",
        "palavras_chave": "Primeiros Princípios, Raciocínio Crítico, Inovação, FERGIL"
    },
    {
        "titulo": "A Sabedoria Estóica de Charlie Munger: Como Evitar a Estupidez em Vez de Tentar Ser Brilhante",
        "tipo": "short",
        "pilar": "Modelos Mentais",
        "gancho": "É impressionante quanta vantagem a longo prazo pessoas comuns conseguem simplesmente evitando ser idiotas de forma consistente.",
        "palavras_chave": "Charlie Munger, Sabedoria Prática, Modelos Mentais, FERGIL"
    },

    # PILAR 4: INTELIGÊNCIA ARTIFICIAL & O FUTURO DA RENDA
    {
        "titulo": "A Revolução Silenciosa da IA: Quem Não Aprender a Alavancar Será Substituído por Quem Sabe",
        "tipo": "doc",
        "pilar": "Inteligência Artificial",
        "gancho": "A Inteligência Artificial não vai tirar o seu emprego. O profissional que dominar ferramentas de IA é quem vai.",
        "palavras_chave": "Inteligência Artificial, Futuro do Trabalho, Produtividade, ChatGPT, FERGIL"
    },
    {
        "titulo": "Como Sam Altman Vê o Fim do Trabalho Tradicional e a Ascensão dos Negócios de 1 Pessoa",
        "tipo": "short",
        "pilar": "Inteligência Artificial",
        "gancho": "Estamos prestes a ver a primeira empresa de 1 bilhão de dólares operada por apenas uma única pessoa usando agentes autônomos.",
        "palavras_chave": "Sam Altman, Solopreneur, Agentes Autônomos, OpenAI, FERGIL"
    },
    {
        "titulo": "A Nova Moeda Global: Por Que a Atenção e o Algoritmo Valem Mais que Petróleo",
        "tipo": "short",
        "pilar": "Inteligência Artificial",
        "gancho": "No século 20, o império pertencia a quem controlava terras e petróleo. No século 21, pertence a quem comanda a retenção humana.",
        "palavras_chave": "Economia da Atenção, Algoritmos, Plataformas Digitais, FERGIL"
    },
    {
        "titulo": "O Lado Oculto dos Data Centers de IA: A Batalha Geopolítica Pela Energia do Futuro",
        "tipo": "doc",
        "pilar": "Inteligência Artificial",
        "gancho": "Os chips mais avançados do planeta não funcionam sem energia massiva. As big techs estão reativando usinas nucleares secretas.",
        "palavras_chave": "Energia Nuclear, Big Tech, Data Centers, IA, Geopolítica, FERGIL"
    },
    {
        "titulo": "Deepfakes e Fraudes Financeiras com IA: Como Proteger o Seu Patrimônio na Era Digital",
        "tipo": "short",
        "pilar": "Inteligência Artificial",
        "gancho": "Voz clonada e vídeo sintético já causaram golpes milionários em multinacionais. A regra de segurança agora mudou.",
        "palavras_chave": "Cibersegurança, Deepfake, Proteção Patrimonial, FERGIL"
    },

    # PILAR 5: FINANÇAS & ESTRATÉGIAS DE ELITE
    {
        "titulo": "A Estratégia dos Donos do Mundo: O Que os Family Offices Fazem que o Cidadão Comum Ignora",
        "tipo": "doc",
        "pilar": "Estratégias de Elite",
        "gancho": "As famílias mais ricas da Europa preservam fortunas há séculos por uma única razão: proteção de capital acima de ganhos rápidos.",
        "palavras_chave": "Family Offices, Preservação de Riqueza, Herança, Estratégia Financeira, FERGIL"
    },
    {
        "titulo": "A Diferença Entre Ativos que Colocam Dinheiro no Seu Bolso e Passivos que Drenam Sua Energia",
        "tipo": "short",
        "pilar": "Estratégias de Elite",
        "gancho": "Se você precisa continuar trabalhando para pagar algo que comprou, aquilo não é patrimônio: é uma algema disfarçada.",
        "palavras_chave": "Pai Rico Pai Pobre, Ativos e Passivos, Fluxo de Caixa, FERGIL"
    },
    {
        "titulo": "Como Larry Fink e a BlackRock Construíram a Maior Gestora de Ativos da História Humana",
        "tipo": "doc",
        "pilar": "Estratégias de Elite",
        "gancho": "Com mais de 10 trilhões de dólares sob custódia, o sistema Aladdin da BlackRock monitora as engrenagens da economia do planeta.",
        "palavras_chave": "BlackRock, Larry Fink, Aladdin, Finanças Globais, FERGIL"
    },
    {
        "titulo": "A Regra de Ouro da Negociação de Alto Nível: Quem Fala Primeiro Perde o Controle",
        "tipo": "short",
        "pilar": "Estratégias de Elite",
        "gancho": "Em reuniões bilionárias, o silêncio desconfortável é a ferramenta psicológica mais destrutiva que você pode usar.",
        "palavras_chave": "Negociação, Chris Voss, Persuasão, Comunicação de Alto Nível, FERGIL"
    },
    {
        "titulo": "A Lição Oculta de Ray Dalio Sobre os Grandes Ciclos Econômicos e Quedas de Impérios",
        "tipo": "doc",
        "pilar": "Estratégias de Elite",
        "gancho": "A história não se repete, mas ela rima. Todo império que acumulou dívidas impagáveis colapsou da mesma maneira.",
        "palavras_chave": "Ray Dalio, Ciclos Econômicos, Dívida Soberana, Macroeconomia, FERGIL"
    },

    # --- EXPANSÃO EDITORIAL 2026: INTELIGÊNCIA ARTIFICIAL APLICADA, GRANDES EMPRESAS E ENSINAMENTOS PRÁTICOS ---

    # PILAR 4 (EXPANSÃO): INTELIGÊNCIA ARTIFICIAL, AGENTES & O FUTURO DO DINHEIRO
    {
        "titulo": "Como Criar um Negócio Lucrativo Usando Agentes de IA Sem Saber Programar",
        "tipo": "doc",
        "pilar": "Inteligência Artificial",
        "gancho": "O jogo mudou: em 2026, quem comanda um time de agentes autônomos tem a força de produção de uma agência de 50 pessoas.",
        "palavras_chave": "Agentes Autônomos, Inteligência Artificial, Negócios de IA, Solopreneur, Renda com IA, FERGIL"
    },
    {
        "titulo": "O Prompt Secreto de 3 Etapas que os Executivos Mais Pagos Usam no ChatGPT e Claude",
        "tipo": "short",
        "pilar": "Inteligência Artificial",
        "gancho": "Se você ainda usa a IA apenas fazendo perguntas simples, você está jogando fora 90% do poder cognitivo dela.",
        "palavras_chave": "Engenharia de Prompt, ChatGPT, Claude, Produtividade Executiva, FERGIL"
    },
    {
        "titulo": "A Guerra Silenciosa Entre OpenAI, Anthropic e Google: Quem Vai Controlar a Sua Vida em 5 Anos",
        "tipo": "doc",
        "pilar": "Inteligência Artificial",
        "gancho": "Não é apenas tecnologia: é a disputa pelo controle da infraestrutura de pensamento de toda a civilização humana.",
        "palavras_chave": "OpenAI, Sam Altman, Anthropic, Gemini, Big Tech IA, FERGIL"
    },
    {
        "titulo": "As 3 Habilidades Humanas que Nenhuma Inteligência Artificial Jamais Conseguirá Copiar",
        "tipo": "short",
        "pilar": "Inteligência Artificial",
        "gancho": "Quanto mais a IA se torna perfeita na técnica, mais caro e raro se torna o julgamento intuitivo humano.",
        "palavras_chave": "Futuro das Profissões, Habilidades Humanas, Liderança, Julgamento Crítico, FERGIL"
    },
    {
        "titulo": "Como a IA Está Destruindo as Agências Tradicionais e Criando Micro-Monopólios",
        "tipo": "doc",
        "pilar": "Inteligência Artificial",
        "gancho": "Empresas que cobravam 30 mil reais por mês estão sendo substituídas por fluxos automatizados de IA em menos de 10 minutos.",
        "palavras_chave": "Disrupção de Mercado, Agências Digitais, Automação, IA nos Negócios, FERGIL"
    },
    {
        "titulo": "A Diferença Brutal Entre Usar IA Como Brinquedo e Usar IA Como Alavanca de Riqueza",
        "tipo": "short",
        "pilar": "Inteligência Artificial",
        "gancho": "O amador pede para a IA escrever um poema; o profissional cria sistemas de IA para gerar caixa 24 horas por dia.",
        "palavras_chave": "Alavancagem Financeira, Mentalidade IA, Automação de Renda, FERGIL"
    },

    # PILAR 2 (EXPANSÃO): BASTIDORES DE GRANDES IMPÉRIOS & CASES DE SUCESSO
    {
        "titulo": "O Segredo da Ferrari: Por Que Eles Preferem Recusar Clientes a Aumentar a Produção",
        "tipo": "doc",
        "pilar": "Grandes Impérios",
        "gancho": "Enzo Ferrari criou uma das marcas mais lucrativas do mundo com um mandamento: sempre entregue um carro a menos do que o mercado pede.",
        "palavras_chave": "Ferrari, Escassez Extrema, Branding de Luxo, Estratégia de Negócios, FERGIL"
    },
    {
        "titulo": "Como a Spotify Derrotou a Pirataria Fazendo as Pessoas Pagarem Por Música Grátis",
        "tipo": "short",
        "pilar": "Grandes Impérios",
        "gancho": "Daniel Ek percebeu o que as gravadoras não viram: a conveniência vence qualquer arquivo pirata gratuito.",
        "palavras_chave": "Spotify, Daniel Ek, Modelo de Assinatura, Inovação, FERGIL"
    },
    {
        "titulo": "O Império Invisível de Bernard Arnault: A Máquina de Fazer Bilhões da LVMH",
        "tipo": "doc",
        "pilar": "Grandes Impérios",
        "gancho": "Como um homem discreto comprou Louis Vuitton, Dior e Tiffany e se transformou no imperador absoluto do luxo mundial.",
        "palavras_chave": "Bernard Arnault, LVMH, Mercado de Luxo, Aquisições Bilionárias, FERGIL"
    },
    {
        "titulo": "A Estratégia Secreta da Amazon Flywheel: Como Jeff Bezos Esmaga Concorrentes no Preço",
        "tipo": "doc",
        "pilar": "Grandes Impérios",
        "gancho": "O desenho que Jeff Bezos fez num guardanapo em 2001 explica por que é quase impossível competir contra a Amazon.",
        "palavras_chave": "Amazon Flywheel, Jeff Bezos, Efeito de Rede, Estratégia Corporativa, FERGIL"
    },
    {
        "titulo": "Por Que a Rolex Nunca Dá Desconto: A Psicologia do Relógio que Vale Mais Usado que Novo",
        "tipo": "short",
        "pilar": "Grandes Impérios",
        "gancho": "Se você entrar hoje numa boutique da Rolex com uma mala de dinheiro, você não sai com um relógio. Entenda a genialidade dessa barreira.",
        "palavras_chave": "Rolex, Reserva de Valor, Escassez Planejada, Luxo Real, FERGIL"
    },

    # PILAR 1 & 5 (EXPANSÃO): ENSINAMENTOS PRÁTICOS, FINANÇAS & PODER PESSOAL
    {
        "titulo": "A Regra das 5 Pessoas: Por Que o Seu Círculo Social Está Ditando a Sua Conta Bancária",
        "tipo": "short",
        "pilar": "Psicologia Financeira",
        "gancho": "Você não ganha o que merece: você ganha a média exata das cinco conversas que você mais tem durante a semana.",
        "palavras_chave": "Networking de Alto Nível, Ambiente de Sucesso, Mentalidade, FERGIL"
    },
    {
        "titulo": "Como Construir Múltiplas Fontes de Renda Sem Ficar Maluco de Exaustão",
        "tipo": "doc",
        "pilar": "Finanças & Estratégias",
        "gancho": "Ter 5 empregos não é ter 5 fontes de renda, é escravidão moderna. A chave é alavancagem de sistemas, não de horas.",
        "palavras_chave": "Renda Passiva Real, Alavancagem de Negócios, Gestão Financeira, FERGIL"
    },
    {
        "titulo": "O Segredo de Warren Buffett Para Avaliar Pessoas em 10 Minutos de Conversa",
        "tipo": "short",
        "pilar": "Modelos Mentais",
        "gancho": "Integridade, inteligência e energia. Mas se a pessoa não tiver a primeira, as outras duas vão destruir você.",
        "palavras_chave": "Warren Buffett, Caráter, Contratação de Líderes, Inteligência Emocional, FERGIL"
    },
    {
        "titulo": "A Arte da Guerra nos Negócios: 3 Estratégias de Sun Tzu Para Vencer Concorrentes Maiores",
        "tipo": "doc",
        "pilar": "Estratégias de Elite",
        "gancho": "A melhor vitória é aquela que você conquista sem disparar uma única flecha. Como empresas pequenas derrubam gigantes consolidados.",
        "palavras_chave": "Sun Tzu, Arte da Guerra, Estratégia Empresarial, Posicionamento, FERGIL"
    }
]

# Aliases de compatibilidade
TEMAS_PILOTO_FERGIL = PAUTAS_FERGIL_MULTIDIMENSIONAIS


def selecionar_proxima_pauta_fergil(is_doc: bool = False, pautas_ja_usadas: Optional[List[str]] = None) -> Dict:
    """
    Seleciona de forma inteligente a próxima pauta do canal FERGIL:
    - Alterna dinamicamente entre os 5 pilares temáticos.
    - Evita repetição de figuras ou tópicos recentes.
    - Prioriza o formato desejado (doc ou short).
    """
    ja_usadas = set(pautas_ja_usadas or [])
    
    candidatos = [p for p in PAUTAS_FERGIL_MULTIDIMENSIONAIS if p["titulo"] not in ja_usadas]
    if not candidatos:
        candidatos = PAUTAS_FERGIL_MULTIDIMENSIONAIS

    # Filtra por tipo preferido se houver correspondência
    tipo_alvo = "doc" if is_doc else "short"
    compativeis = [p for p in candidatos if p.get("tipo") == tipo_alvo]
    if not compativeis:
        compativeis = candidatos

    # Escolhe de forma variada evitando vícios
    escolhido = random.choice(compativeis)
    return escolhido


def formatar_roteiro_editorial_fergil(tema: str, resumo_insight: str) -> Dict[str, str]:
    """Gera a estrutura de roteiro com camada editorial transformativa anti-reused content."""
    return {
        "tema": tema,
        "hook": f"A maioria das pessoas passa a vida inteira sem entender esta regra sobre {tema.lower()}...",
        "insight": resumo_insight,
        "conclusao": "Se você quer dominar a sua mentalidade e os seus negócios, inscreva-se na FERGIL e comente a sua visão abaixo."
    }
