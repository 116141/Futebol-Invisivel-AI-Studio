# MANUAL DE PRODUÇÃO: O DNA DO SISTEMA - FUTEBOL INVISÍVEL
**Canal Oficial:** `@FutebolInvisivelOficial`  
**Gênero:** Documentário Investigativo Esportivo / True-Crime do Futebol  
**Padrão de Qualidade:** Netflix / HBO Crime Docs / ESPN 30 for 30  

---

## 1. PRINCÍPIOS EDITORIAIS E RIGOR FACTUAL
1. **Credibilidade Factual Inegociável (Zero Invenção):**
   - 100% dos fatos narrados devem ser ancorados em provas documentais, autos judiciais, denúncias formais de federações (FA, UEFA, FIFA, CBF, RFEF), auditorias internacionais (Hacienda espanhola, Sportradar, IBIA) e depoimentos oficiais.
   - Proibido qualquer boato infundado ou acusação sem lastro formal.
   - Em disputas de bastidores, narrar a cronologia forense com precisão cirúrgica (datas, valores exatos, nomes de empresas de fachada e artigos de regulamento).
2. **Estrutura de 3 Micro-Missões com Retenção Máxima:**
   - **Micro-Missão 1 (0:00 - 3:30):** O Choque Inicial e a Quebra da Realidade (O valor astronômico em jogo, o alerta confidencial, a ameaça de punição máxima).
   - **Micro-Missão 2 (3:30 - 7:30):** A Investigação Forense e os Bastidores (Os contratos secretos, as faturas, mensagens e manobras políticas).
   - **Micro-Missão 3 (7:30 - Final):** O Impacto Sistêmico, o Julgamento e o Veredito (Precedentes históricos, consequências e o gancho explosivo para comentários).

---

## 2. REGRAS DE OURO VISUAIS (FIM DOS SLIDES / VÍDEO REAL EM MOVIMENTO)
1. **PROIBIDO SLIDES OU FOTOS ESTÁTICAS COMO BASE DO VÍDEO:**
   - O espectador do YouTube rejeita apresentações que pareçam slides de PowerPoint.
   - Todo documentário deve ser construído com **100% de vídeo real em movimento contínuo** (cortes a cada 3,2s a 3,8s).
   - Documentos de arquivo (contratos, telegramas, fac-símiles) entram apenas pontualmente (máximo 1 a cada 5 cortes) com movimento rápido pericial de câmera.
2. **Acervo de Movimento Diversificado:**
   - Alternar entre: (1) Imagens de coletivas de imprensa tensas, (2) Discussões e confrontos com arbitragem, (3) Lances de jogo intensos blindados, (4) Imagens aéreas de drone dos estádios e (5) Caminhada dos jogadores no túnel de acesso.

---

## 3. ENGENHARIA DE ÁUDIO ININTERRUPTO (ZERO CORTES / ZERO ENGASGOS)
1. **Regra do Áudio Mestre Linear:**
   - **O áudio NUNCA deve ser fatiado junto com os takes de vídeo.** Fatiar áudio com vídeo introduz descontinuidade de pacotes AAC e micro-travamentos a cada corte de cena.
   - A narração dos 10 capítulos deve ser unificada em um arquivo mestre contínuo (`narracao_master_ininterrupta.wav`) do segundo zero ao final.
   - Os takes de vídeo são renderizados mudos (`-an`) e o fluxo de áudio mestre é adicionado de forma limpa na multiplexação final.
2. **Mixagem de Trilha Sonora (BGM):**
   - Trilha de suspense investigativo contínua calibrada exatamente a **-20 dB** em relação à voz.
   - Voz do locutor (`pt-BR-AntonioNeural`) límpida, com volume 1.0 (loudness profissional de transmissão).

---

## 4. PROTOCOLO OBRIGATÓRIO DE BLINDAGEM ANTI-COPYRIGHT / CONTENT ID
Transmissões oficiais de TV (LaLiga, Premier League, UEFA) possuem bots automáticos de reconhecimento de imagem. Para garantir monetização verde e zero reivindicações:

1. **Proibição de Grafismos de TV:**
   - Nunca usar vídeos brutos de TV contendo placares, relógios da partida, vinhetas da liga (ex: `LIGA BBVA`) ou marca d'água de emissoras.
2. **Quádrupla Blindagem Anti-Content ID em Todos os Takes de Jogo:**
   - **`hflip` (Espelhamento Horizontal):** Inverte o eixo visual para quebrar a correspondência vetorial do robô.
   - **`crop=in_w*0.82:in_h*0.82` (Zoom Perimetral de 18%):** Elimina completamente as extremidades da tela onde ficam os logotipos e caracteres de transmissão.
   - **`eq=contrast=1.14:saturation=1.18` (Curva de Cores):** Altera o histograma digital de luminância e crominância.
   - **Padronização de Codec:** `fps=30`, `g=30` (GOP fixo), `pix_fmt=yuv420p`.
4. **Regras de Pós-Produção e Blindagem Visual:**
   - **Introdução (Primeiros 20 segundos):** Usar 100% de planos de apoio imersivos em tela cheia (close-ups em dossiês, documentos jurídicos carimbados, fachadas sob chuva e manchetes históricas) antes de qualquer corte para bancada/estúdio.
   - **Exibição de Contratos e Documentos:** Nunca exibir documentos com textos invertidos/espelhados ou planos estáticos longos; aplicar zoom suave (*Ken Burns*) com destaque gráfico limpo nos valores monetários e datas cruciais.

---

## 5. CIÊNCIA DE LEGENDAGEM DINÂMICA (ASS)
1. **Tipografia Oficial:** `Arial Black` ou `Impact`.
2. **Cor:** Amarelo Ouro vibrante (`#FFDE00`) com contorno preto reforçado de 4 a 6px e sombra suave.
3. **Margem Inferior:** `MarginV: 110` (área nobre de leitura da TV e do player de desktop/mobile sem colidir com a barra de progresso do YouTube).
4. **Cadência:** Linha única de **3 a 4 palavras por frase**, sincronizada ao milissegundo com a fala do narrador.

---

## 6. SISTEMA DE TESTE A/B/C DE MINIATURAS E TÍTULOS
Para todo documentário longo, gerar obrigatoriamente:
1. **3 Opções de Capa 16:9 (1920x1080) e 3 Títulos Diferentes:**
   - **Opção 1:** Ângulo Institucional / Ameaça Imediata / Punição Máxima.
   - **Opção 2:** Ângulo Financeiro / Fraude / Provas Materiais / Valores Astronômicos.
   - **Opção 3:** Ângulo da Conspiração Histórica / Golpe Político / Traição de Bastidores.
2. **Regras de Ouro da Capa (yt-package):**
   - O texto da capa **NUNCA** repete o título (promessa complementar).
   - No máximo **3 a 4 palavras de impacto visual**.
   - Alto contraste com vinheta cinematográfica no fundo.
3. **Capa Vertical (9:16 - 1080x1920) do Short de Alto CTR:**
   - **Zona Segura (Safe Zone):** Textos e elementos críticos DEVEM ficar entre `y=1250` e `y=1600` (abaixo da área de corte de celulares altos e acima da barra de canal/áudio/botão inscrever-se que ocupa de `y=1600` a `y=1920`).
   - **Close-up Facial Extremo:** O rosto do personagem principal (expressão de choque, tensão ou desespero) deve ocupar de 50% a 65% da metade superior (`y=0` a `y=1200`).
   - **Tratamento Visual:** Realce de saturação (+45%), contraste (+28%) e nitidez (+50%) com iluminação de recorte (rim light) para destaque no feed escuro.
   - **Tipografia:** Máximo de 2 linhas curtas em `Impact` gigante (100 a 112pt) em amarelo `#FFDE00` com contorno preto de 12px e sombra projetada, acompanhada de sub-tarja neon de contexto.
   - Todo Short conectado deve ter obrigatoriamente a sua thumbnail vertical de alta definição arquivada em `canais/canal_01_futebol_invisivel/videos_prontos/shorts/`.

---

## 7. PROTOCOLO DE UPLOAD E MATURAÇÃO NO YOUTUBE STUDIO
1. **Questionário de Conteúdo Alterado / IA:**
   - Marcar: Sim -> Áudio/voz gerada artificialmente. Justificar: Narração documental neural sobre dados públicos e processos judiciais reais.
2. **Autocertificação de Anúncios:**
   - Classificação zerada para linguagem imprópria, violência e temas sensíveis -> **Garante Selo Verde ($)** imediato.
3. **Cartões Interativos (Cards) & Tela Final:**
   - Cards aos 5 e 9 minutos com teasers curtos (<= 30 caracteres).
   - Tela final nos últimos 25 segundos com vídeo recomendado + botão de inscrição.
4. **Alavancagem de Algoritmo com Enquetes na Aba Comunidade:**
   - **Enquete 1 (1 hora antes do vídeo):** Aquecimento e debate sobre o tema do documentário.
   - **Enquete 2 (final da tarde):** Veredito e repercussão após a audiência assistir ao vídeo completo.
5. **Maturação Não Listada (Unlisted):**
   - Manter o vídeo não listado por **2 horas** antes de liberar para o público para garantir processamento 1080p60 e verificação limpa de direitos autorais.
