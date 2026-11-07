# Regras de Ouro Permanentes — Estúdio Alana Cruz & Futebol Invisível

Estas regras fazem parte do núcleo permanente do sistema e devem ser cumpridas automaticamente em **100% das gerações de vídeos, capas e kits de postagem**, sem que o utilizador precise de repetir:

## 1. Preço Universal em Dólar (`US$`) — Alana Cruz
- Todos os preços de produtos (na capa promocional, na locução/roteiro, na descrição do vídeo e no painel web) devem ser sempre exibidos em **Dólar Americano (`US$ X.XX`)** para alcance universal.
- Na consulta à API do AliExpress (`app/services/aliexpress_affiliate.py`), manter `target_language="PT"` para busca em português e converter/formatar automaticamente o valor final para `US$`.

## 2. Capa Promocional 100% Fiel ao Produto Real — Alana Cruz
- A capa promocional (`app/services/promo_cover.py` -> `gerar_capa_promocional_moda`) deve utilizar **exclusivamente as fotos reais oficiais do produto** vindas do anúncio do AliExpress (`product_small_image_urls` / `product_main_image_url`).
- **Proibido** usar fotos genéricas ou modelos gerados por IA que não vistam exatamente a mesma peça do link de afiliado.
- Usar o ângulo de estúdio mais limpo do produto como imagem principal (1080x1920) e o segundo ângulo/cor real do anúncio na moldura VIP superior direita, acompanhado do selo de preço em `US$` e botão CTA.

## 3. Tags de SEO do YouTube Obrigatórias (Ambos os Canais)
- Todo vídeo gerado (`app_render_studio.py` e arquivo `_POSTAGEM.txt`) deve incluir obrigatoriamente:
  1. **📌 Título Viral do Short / Vídeo** (sem prefixos técnicos como `AFILIADO MODA` ou `SHORT`).
  2. **📝 Descrição + Comentário Fixado** com o preço em `US$` (Alana Cruz) ou chamada de debate (Futebol Invisível).
  3. **🏷️ Tags do YouTube (separadas por vírgula)** prontas para copiar e colar diretamente no campo de Tags do YouTube Studio.

## 4. Proibição Absoluta de Youtubers / Reacts / Podcasts nos Vídeos de Futebol (`@FutebolInvisivelOficial`)
- **NUNCA** baixar vídeos de youtubers falando no microfone, cortes de podcast, lives, reacts ou programas de estúdio para ilustrar vídeos do Futebol Invisível.
- A busca de vídeos (`app_render_studio.py`) deve sempre limpar palavras de opinião (*zoeira, polêmica, crise, contrato, verdade, segredo, treta*) e buscar **exclusivamente imagens reais do jogador e do clube em campo (`goals skills highlights HD -react -podcast -live -cortes`)**, filtrando qualquer resultado com essas palavras proibidas.

## 5. Táticas Oficiais do YouTube Studio Analytics — Futebol Invisível (`@FutebolInvisivelOficial`)
Baseado nos dados reais de retenção e público do YouTube Studio (**43.291 views / 131,9h watch time / 15,1 mil público mensal / 4.222 views a cada 48h**):
- **Fórmula dos 99,4% de Retenção (30 a 37 segundos):** Roteiros investigativos de **30 a 35 segundos (68 a 82 palavras)** com **cifra exata nos primeiros 3 segundos** (sem a palavra técnica `auto` no início).
- **Conversão de Novos Visitantes (98,7% são novos visitantes e 99,2% não subscritos):** Inserir no meio da tensão (**entre os segundos 12 e 16**) uma micro-chamada natural (*"Segue o Futebol Invisível pra não perder os bastidores!"*).
- **Cruzamento Futebol Brasileiro + Europeu:** Priorizar os temas que o público assiste em massa (**Corinthians, Flamengo, Palmeiras, Santos, Fluminense, Messi na Argentina, Momentos Injustos no Futebol, Vini Jr, Manchester City/Haaland e Lamine Yamal**) com `#futebol #futebolbrasileiro #shorts` no título.

## 6. Padrão Obrigatório de Capa Viral de Futebol (`@FutebolInvisivelOficial`)
- **PROIBIDO** usar frames borrados/distantes do vídeo com texto pequeno nas capas do Futebol Invisível.
- Toda capa do Futebol Invisível (`app/services/promo_cover.py` -> `gerar_capa_futebol_profissional`) deve:
  1. Gerar automaticamente um **retrato cinematográfico 8K de estádio à noite com iluminação dramática e faíscas douradas** usando os modelos de imagem nativos da API Gemini (`gemini-3.1-flash-image` / `gemini-2.5-flash-image` / `gemini-3-pro-image`) ou o subagente `image-generator`.
  2. Aplicar **Tarja Vermelha de Urgência** no topo + **Tipografia `IMPACT` gigante com contorno preto grosso (`stroke 12px`)** em Branco e Amarelo Ouro (`255, 215, 0`) + rodapé com pergunta polarizadora e assinatura `FUTEBOL INVISIVEL`, idêntico ao padrão `compor_capas_virais_futebol.py`.

## 7. Proibição de Vídeos com Marcas d'Água / Textos Queimados / Faixas Pretas (`@FutebolInvisivelOficial`)
- **PROIBIDO** baixar vídeos curtos (< 75 segundos), Shorts de terceiros, vídeos do TikTok ou edits que já possuam legendas ou URLs queimadas na imagem (ex: `www.Youtube.com/...`).
- O buscador (`app_render_studio.py`) exige obrigatoriamente vídeos horizontais de transmissão (`75s <= dur <= 900s`) e aplica o filtro de recorte com margem de segurança `crop=ih*0.88*9/16:ih*0.88:(iw-ih*0.88*9/16)/2:ih*0.04,scale=1080:1920,fps=30` para preencher 100% da tela vertical sem faixas pretas e sem marcas d'água de borda.

## 8. Método das 3 Fases (Outliers + Regra dos 10 Títulos + Roteiro Multi-Missões com Open Loop)
Baseado na transcrição e análise do vídeo de referência (`https://youtu.be/xPwlbvnntGU`):
1. **Fase 1 (O Pacote — Outliers + Dupla Título/Thumbnail):**
   - Usar `autoviral_brain.espionar_canais_concorrentes()` para encontrar vídeos nos canais do nicho que fizeram **2x a 50x mais views que a média do próprio canal** (sinal de que a ideia é mais forte que o canal) e abordar um ângulo inédito.
   - Gerar internamente 10 variações de títulos e escolher apenas do 6º ao 10º (combinando **Curiosidade Aberta + Benefício + Tensão/Perda**).
   - **A Thumbnail nunca repete o Título:** O Título promete, a Thumbnail provoca (eles funcionam em dupla complementar).
2. **Fase 2 (O Roteiro — Jogo de Multi-Missões e Transição Open Loop):**
   - **Proibido roteiro de missão única** (que promete no início e enrola até o final).
   - Dividir o roteiro em micro-missões (Missão 1: Confirmar o clique imediatamente nos primeiros 3s; Missão 2: O primeiro sinal/pista ignorada; Missão 3: A reviravolta/prova oculta).
   - **Técnica de Transição Open Loop:** Antes de fechar uma missão, abrir imediatamente a próxima (*"E foi assim que descobriram a primeira pista, mas o que ninguém esperava estava escondido no lugar mais óbvio..."*), para que o espectador nunca pense *"já entendi, posso sair"*.
3. **Fase 3 (A Produção — Olho Nunca Parado):**
   - Mudar o estímulo visual a cada 2,5 a 3,5 segundos (cortes dinâmicos, zoom, destaque na legenda, ritmo da locução) para manter a retenção até o último segundo.

## 10. PROTOCOLO DE DNA ANTI-ERRO PARA SHORTS 100% PROFISSIONAIS (INEGOCIÁVEL)
Estabelecido após auditoria do lote oficial de Shorts:
1. **PROIBIDO VÍDEO COM IMAGEM ESTÁTICA OU DESCONEXA DO TEMA:**
   - Todo Short deve conter no mínimo de 5 a 8 takes/cenas dinâmicas, com troca de corte a cada 3 a 4 segundos, ou transições fluidas de Ken Burns (zoom-in progressivo 1.0 -> 1.15, zoom-out e pan lateral) em 30 fps contínuos. Jamais renderizar vídeo de imagem congelada.
   - **FIDELIDADE EDITORIAL TOTAL AO ROTEIRO (REGRA DE OURO):** É terminantemente proibido utilizar imagens que não representem exatamente a entidade, jogador, troféu ou evento citado naquela cena do áudio. O sistema DEVE usar termos nominais exatos (ex: "Vinicius Junior Real Madrid", "Ballon d'Or trophy", "Florentino Perez") e priorizar fotos oficiais e autênticas via `coletor_fotos_reais.py` (Wikimedia Commons / Acervo Oficial) antes de qualquer fallback.
2. **PROIBIDO VÍDEO SEM LEGENDA QUEIMADA (HARDCODED):**
   - É obrigatório queimar as legendas dinâmicas diretamente no arquivo de vídeo MP4 via HyperFrames / ASS.
   - Padrão visual das legendas: Tipografia Impact / Montserrat / Arial Black, cor Amarelo Ouro (`#FFDE00` / `#FACC15`), borda preta sólida com sombra suave, centralizada no terço inferior (margem de segurança acima dos botões da interface do feed de Shorts do YouTube).
   - Formatação: Linha única com 3 a 5 palavras por frase, sincronizadas milimetricamente com a locução neural (`pt-BR-AntonioNeural`), trocando rapidamente para manter o estímulo de leitura contínuo.
3. **PROIBIDO BANCOS DE IMAGENS COM MARCAS D'ÁGUA COMERCIAIS (ALAMY, GETTY, SHUTTERSTOCK):**
   - É expressamente proibido usar recortes ou fotos que contenham letras, selos de agências ou marcas d'água de bancos comerciais no fundo.
   - Para toda e qualquer ilustração gráfica/visual de jogadores, estádios ou personalidades, o sistema DEVE utilizar o acervo editorial autêntico (`coletor_fotos_reais.py`) ou geração nativa via modelo de imagem Gemini em qualidade cinematográfica 8K limpa.
4. **MARCA D'ÁGUA OFICIAL OBRIGATÓRIA DO CANAL:**
   - Em todo Short gerado, aplicar obrigatoriamente o selo oficial circular do canal (`perfil_futebol_invisivel.jpg` ou PNG com cantos arredondados/alpha) posicionado com elegância no canto superior direito (`x=W-w-35:y=35`) com escala discreta (largura ~100px a 140px) e opacidade/blend ideal, assegurando a assinatura institucional da marca Futebol Invisível.
5. **ALINHAMENTO DE FUSOS HORÁRIOS PARA AGENDAMENTO AUTOMÁTICO:**
   - O utilizador opera a partir de **Cabo Verde (UTC-1)**.
   - Toda programação de lançamento e agendamento deve calcular a conversão matemática exata para o pico de consumo do público-alvo:
     * **Brasil (UTC-3):** Hora de Cabo Verde menos 2 horas (ex: 19:45 CV = 17:45 BR).
     * **Portugal (UTC+1):** Hora de Cabo Verde mais 2 horas (ex: 19:45 CV = 21:45 PT).
