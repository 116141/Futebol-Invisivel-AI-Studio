const form = document.getElementById('createForm');
        const progressCard = document.getElementById('progressCard');
        const statusText = document.getElementById('statusText');
        const spinner = document.getElementById('spinner');
        const roteiroBox = document.getElementById('roteiroBox');
        const downloadBox = document.getElementById('downloadBox');
        const btnDownload = document.getElementById('btnDownload');
        const btnSubmit = document.getElementById('btnSubmit');
        const btnGerarGanchos = document.getElementById('btnGerarGanchos');
        const listaTarefas = document.getElementById('listaTarefas');
        const ganchosContainer = document.getElementById('ganchosContainer');
        const listaGanchos = document.getElementById('listaGanchos');
        const ganchoEscolhidoInput = document.getElementById('ganchoEscolhidoInput');
        let ultimoProdutosAli = [];

        function setAliBusca(termo) {
            document.getElementById('aliKeywords').value = termo;
            buscarProdutosAli();
        }

        let aliPaginaAtual = 1;

        function mudarPaginaAli(delta) {
            const novaPag = Math.max(1, aliPaginaAtual + delta);
            if (novaPag !== aliPaginaAtual) {
                buscarProdutosAli(novaPag);
            }
        }

        async function buscarProdutosAli(pagina = 1) {
            aliPaginaAtual = pagina;
            const spanPag = document.getElementById('aliPaginaAtualSpan');
            if (spanPag) spanPag.innerText = `Pág ${aliPaginaAtual}`;

            const kwEl = document.getElementById('aliKeywords');
            const kw = (kwEl ? kwEl.value.trim() : '') || 'vestido feminino elegante';
            const onlyVidEl = document.getElementById('aliOnlyVideo');
            const onlyVid = onlyVidEl ? onlyVidEl.checked : true;
            const sortEl = document.getElementById('aliSortOrder');
            const sortOrder = sortEl ? sortEl.value : 'LAST_VOLUME_DESC';
            const btn = document.getElementById('btnBuscarAli');
            const box = document.getElementById('aliResultados');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Buscando...';
            box.innerHTML = '<div class="col-12 text-center text-secondary py-3">Consultando API Oficial AliExpress Afiliados (Pág ' + aliPaginaAtual + ')...</div>';
            try {
                const res = await fetch(`/api/aliexpress/buscar?keywords=${encodeURIComponent(kw)}&only_video=${onlyVid}&page=${aliPaginaAtual}&sort=${sortOrder}`);
                const data = await res.json();
                ultimoProdutosAli = data.produtos || [];
                if (ultimoProdutosAli.length === 0) {
                    box.innerHTML = '<div class="col-12 text-warning small">Nenhum produto novo nesta página. Tente outra categoria ou desmarque o filtro de vídeo!</div>';
                    return;
                }
                let html = '';
                ultimoProdutosAli.forEach((p, idx) => {
                    const vidBadge = p.has_video 
                        ? '<span class="badge bg-success">🎬 VÍDEO .MP4 OFICIAL</span>' 
                        : '<span class="badge bg-secondary">📸 FOTOS HD</span>';
                    html += `
                        <div class="col-md-4">
                            <div class="card bg-dark border-secondary h-100 p-2 text-light">
                                <img src="${p.main_image}" class="rounded mb-2" style="height: 170px; object-fit: cover; width: 100%;">
                                <div class="d-flex justify-content-between align-items-center mb-1">
                                    ${vidBadge}
                                    <span class="badge bg-warning text-dark">Comissão ${p.commission_rate}</span>
                                </div>
                                <div class="fw-bold small mb-1">${p.short_title}</div>
                                <div class="text-info small mb-2">💰 ${p.sale_price} | 🔥 ${p.orders_volume} vendidos</div>
                                <div class="mt-auto d-grid gap-1">
                                    <button type="button" class="btn btn-pink btn-sm" onclick="criarShortAliExpress(${idx})">⚡ Gerar Short Alana (1-Clique)</button>
                                    <a href="${p.short_link}" target="_blank" class="btn btn-outline-secondary btn-sm" style="font-size:11px;">🔗 Testar Meu Link s.click</a>
                                </div>
                            </div>
                        </div>
                    `;
                });
                box.innerHTML = html;
            } catch (e) {
                box.innerHTML = `<div class="col-12 text-danger small">Erro ao consultar API: ${e}</div>`;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '🔍 Buscar Campeões';
            }
        }

        async function criarShortAliExpress(idx) {
            const prod = ultimoProdutosAli[idx];
            if (!prod) return;
            progressCard.classList.remove('d-none');
            spinner.classList.remove('d-none');
            downloadBox.classList.add('d-none');
            statusText.innerText = `Baixando vídeo/fotos do AliExpress e gerando Short para "${prod.short_title}"...`;
            const res = await fetch('/api/aliexpress/criar_auto', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(prod)
            });
            const data = await res.json();
            acompanharTask(data.task_id);
        }

        async function sincronizarBrain() {
            const btn = document.getElementById('btnSyncBrain');
            const box = document.getElementById('brainBox');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Lendo YouTube & AliExpress...';
            try {
                const res = await fetch('/api/brain/sincronizar', { method: 'POST' });
                const data = await res.json();
                const moda = data.estrategias?.moda || {};
                const fut = data.estrategias?.futebol || {};
                box.innerHTML = `
                    <div class="p-2 bg-dark rounded border border-secondary text-light mt-2">
                        <div class="mb-2"><strong style="color:#f472b6;">🛍️ @AlanaCruzOficial:</strong> ${moda.regras_prompt_ativas || ''}</div>
                        <div><strong class="text-warning">⚽ @FutebolInvisivelOficial:</strong> ${fut.regras_prompt_ativas || ''}</div>
                    </div>
                `;
            } catch (e) {
                box.innerHTML = '<span class="text-danger">Erro ao sincronizar métricas.</span>';
            } finally {
                btn.disabled = false;
                btn.innerHTML = '📊 Sincronizar Métricas & Aprender';
            }
        }

        async function agendarVideosTodosCanais() {
            if (!confirm('📅 Deseja analisar a esteira e AGENDAR os vídeos prontos de TODOS os canais (Futebol, Fergil e Moda) nos horários de pico (hoje e próximos dias)?')) return;
            const btn = document.getElementById('btnAgendarTodos');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Agendando...';
            }
            try {
                const res = await fetch('/api/agendador/executar_todos', { method: 'POST' });
                const data = await res.json();
                alert('📅 ' + (data.mensagem || 'Agendamento em lote disparado com sucesso!'));
            } catch (e) {
                alert('Erro ao agendar vídeos: ' + e.message);
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-calendar-check-fill me-1"></i>📅 Agendar Vídeos (Todos Canais)';
                }
            }
        }

        async function executarAutopilotAgora() {
            if (!confirm('Deseja DISPARAR a produção de 1 ciclo autônomo agora mesmo (Futebol + Moda + Postagem Unlisted)?')) return;
            const btn = document.getElementById('btnExecutarAgoraAutopilot');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Produzindo...';
            }
            try {
                const res = await fetch('/api/autopilot/executar_agora', { method: 'POST' });
                const data = await res.json();
                alert('⚡ Ciclo autônomo disparado em segundo plano! Acompanhe o progresso no painel.');
            } catch (e) {
                alert('Erro ao disparar ciclo: ' + e.message);
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '⚡ Rodar Ciclo Agora';
                }
            }
        }

        async function alternarAutopiloto() {
            const btn = document.getElementById('btnToggleAutopilot');
            const label = document.getElementById('labelAutopilot');
            btn.disabled = true;

            try {
                const statusRes = await fetch('/api/autopilot/status');
                const statusData = await statusRes.json();
                const acao = statusData.ativo ? "parar" : "iniciar";

                if (acao === "iniciar") {
                    if (!confirm("Deseja ATIVAR o Piloto Automático 100% Autônomo?\n\n• O sistema analisará tendências das últimas 24h e o público do canal.\n• Gerará Shorts e Documentários Investigativos.\n• Postará SEMPRE como 'NÃO LISTADO' (unlisted) para sua segurança.\n• Auto-fixará o 1º comentário e responderá inscritos periodicamente.")) {
                        btn.disabled = false;
                        return;
                    }
                }

                const res = await fetch(`/api/autopilot/alternar?acao=${acao}`, { method: 'POST' });
                const data = await res.json();

                if (acao === "iniciar") {
                    label.innerText = "🛑 Desativar Piloto Automático";
                    btn.className = "btn btn-danger btn-sm btn-studio-action fw-bold";
                    alert("🚀 PILOTO AUTOMÁTICO ATIVADO COM SUCESSO!\n\nO sistema agora monitora tendências, gera conteúdos (Shorts e Documentários) e posta como Não Listado automaticamente!");
                } else {
                    label.innerText = "🚀 Ativar Piloto Automático";
                    btn.className = "btn btn-outline-warning btn-sm btn-studio-action fw-bold";
                    alert("🛑 Piloto Automático pausado.");
                }
            } catch (e) {
                alert("Erro ao alternar Piloto Automático: " + e.message);
            } finally {
                btn.disabled = false;
            }
        }

        async function dispararBotRespostas() {
            const op = prompt("Qual canal você deseja que o Bot responda comentários agora?\n\nDigite o número ou nome:\n1 ou futebol = Futebol Invisível\n2 ou fergil = FERGIL (Negócios)\n3 ou moda = Alana Cruz (Moda)\ntodos = Responder em TODOS os canais", "todos");
            if (!op) return;
            const opL = op.trim().toLowerCase();
            let listaCanais = [];
            if (opL === "1" || opL === "futebol") listaCanais = ["futebol"];
            else if (opL === "2" || opL === "fergil") listaCanais = ["fergil"];
            else if (opL === "3" || opL === "moda") listaCanais = ["moda"];
            else if (opL === "todos" || opL === "all") listaCanais = ["futebol", "fergil", "moda"];
            else listaCanais = [opL];

            const btn = document.getElementById('btnBotRespostas');
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Respondendo...';

            try {
                let msgGeral = "💬 RESUMO BOT DE RESPOSTAS:\n\n";
                let totalRespondidosGeral = 0;

                for (const canal of listaCanais) {
                    try {
                        const res = await fetch(`/api/youtube/responder_comentarios?canal=${canal}&max_respostas=10`, { method: 'POST' });
                        const data = await res.json();
                        if (res.ok && !data.erro) {
                            totalRespondidosGeral += (data.comentarios_respondidos || 0);
                            msgGeral += `• ${canal.toUpperCase()}: ${data.comentarios_respondidos || 0} respondidos.\n`;
                        } else {
                            msgGeral += `• ${canal.toUpperCase()}: Erro (${data.detail || data.erro})\n`;
                        }
                    } catch (eC) {
                        msgGeral += `• ${canal.toUpperCase()}: Falha na requisição.\n`;
                    }
                }
                msgGeral += `\n✅ Total geral de inscritos respondidos: ${totalRespondidosGeral}`;
                alert(msgGeral);
            } catch (err) {
                alert("Erro ao acionar bot de respostas: " + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }

        async function varrerECorrigirCanais() {
    if (!confirm('🧹 Deseja acionar o Robô Guardião para varrer o YouTube agora e higienizar/corrigir as descrições de TODOS os canais (Futebol, Fergil, Moda)?\n\nEle removerá minutagens falsas, links duplicados e tags técnicas automaticamente.')) return;
    const btn = document.getElementById('btnVarrerCorrigirCanais');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Varrendo & Corrigindo...';
    }
    try {
        const res = await fetch('/api/canais/varrer_e_corrigir', { method: 'POST' });
        const data = await res.json();
        alert('🧹 ' + (data.mensagem || 'Robô de higienização acionado com sucesso!'));
    } catch (e) {
        alert('Erro ao acionar robô: ' + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-shield-fill-check me-1"></i>🧹 Varrer & Corrigir Descrições (Todos Canais)';
        }
    }
}

async function auditarEAutoFixarComentarios() {
            const op = prompt("Deseja auditar e auto-fixar comentários em qual canal?\n\nDigite o número ou nome:\n1 ou futebol = Futebol Invisível\n2 ou fergil = FERGIL (Negócios)\n3 ou moda = Alana Cruz (Moda)\ntodos = Fixar comentários em TODOS os canais", "todos");
            if (!op) return;
            const opL = op.trim().toLowerCase();
            let listaCanais = [];
            if (opL === "1" || opL === "futebol") listaCanais = ["futebol"];
            else if (opL === "2" || opL === "fergil") listaCanais = ["fergil"];
            else if (opL === "3" || opL === "moda") listaCanais = ["moda"];
            else if (opL === "todos" || opL === "all") listaCanais = ["futebol", "fergil", "moda"];
            else listaCanais = [opL];

            const btn = document.getElementById('btnAuditarComentarios');
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Auditando vídeos...';

            try {
                let msgGeral = "🎯 RESUMO DA FIXAÇÃO DE COMENTÁRIOS:\n\n";
                let totalCriados = 0;

                for (const canal of listaCanais) {
                    try {
                        const res = await fetch(`/api/youtube/auditar_comentarios?canal=${canal}&max_videos=15`, { method: 'POST' });
                        const data = await res.json();
                        if (res.ok && !data.erro) {
                            totalCriados += (data.comentarios_criados || 0);
                            msgGeral += `• ${canal.toUpperCase()}: ${data.videos_analisados} analisados | ${data.comentarios_criados} novos comentários fixados.\n`;
                        } else {
                            msgGeral += `• ${canal.toUpperCase()}: Erro (${data.detail || data.erro})\n`;
                        }
                    } catch (eC) {
                        msgGeral += `• ${canal.toUpperCase()}: Falha na requisição.\n`;
                    }
                }
                msgGeral += `\n💬 Total de novos comentários fixados: ${totalCriados}`;
                alert(msgGeral);
            } catch (err) {
                alert("Erro ao auditar/fixar comentários: " + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }

        async function buscarNoticiasFutebol() {
            const btn = document.getElementById('btnNoticiasFut');
            const box = document.getElementById('noticiasBox');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Buscando...';
            try {
                const res = await fetch('/api/noticias_futebol');
                const data = await res.json();
                let html = '<div class="list-group mt-2">';
                (data.noticias || []).forEach(n => {
                    const safeTit = (n.titulo || '').replace(/'/g, "\\'");
                    html += `
                        <div class="list-group-item bg-dark border-secondary text-light d-flex justify-content-between align-items-center gap-2 py-2">
                            <div class="small">
                                <span class="badge bg-warning text-dark me-1">${n.fonte}</span>
                                <strong>${n.titulo}</strong>
                            </div>
                            <button class="btn btn-gold btn-sm text-nowrap" onclick="usarNoticia('${safeTit}')">⚡ Criar Short</button>
                        </div>
                    `;
                });
                html += '</div>';
                box.innerHTML = html;
                box.classList.remove('d-none');
            } catch (e) {
                console.error(e);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '📰 Notícias Futebol Hoje';
            }
        }

        function usarNoticia(titulo) {
            document.getElementById('tituloInput').value = titulo;
            document.getElementById('tipoShort').checked = true;
            window.scrollTo({ top: document.getElementById('createForm').offsetTop - 40, behavior: 'smooth' });
        }

        async function abrirRadarOutliers() {
            const box = document.getElementById('radarOutliersBox');
            const lista = document.getElementById('listaOutliers');
            const statusMsg = document.getElementById('radarStatusMsg');
            const btn = document.getElementById('btnRadarOutliers');

            box.classList.remove('d-none');
            lista.innerHTML = '';
            statusMsg.classList.remove('d-none');
            statusMsg.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Espionando canais de futebol (@BIDOFC, @ominuto93, @goalfut, @IkeFutebol) e calculando vídeos virais fora da curva...';

            try {
                const res = await fetch('/api/radar/outliers');
                const data = await res.json();
                statusMsg.classList.add('d-none');

                if (!data.outliers || data.outliers.length === 0) {
                    lista.innerHTML = '<div class="text-secondary small">Nenhum outlier fora da curva detectado no momento ou canais inacessíveis.</div>';
                    return;
                }

                let html = '';
                data.outliers.slice(0, 10).forEach(o => {
                    const mult = o.multiplicador_mediana || 1.0;
                    const views = (o.views || 0).toLocaleString('pt-BR');
                    const safeTit = (o.titulo || '').replace(/'/g, "\\'");
                    const safeUrl = (o.url || '').replace(/'/g, "\\'");
                    const safeCanal = (o.canal || '').replace(/'/g, "\\'");

                    html += `
                        <div class="card bg-secondary bg-opacity-25 border-warning p-2 text-light">
                            <div class="d-flex justify-content-between align-items-start gap-2">
                                <div style="max-width: 72%;">
                                    <span class="badge bg-warning text-dark fw-bold me-1">${mult}x Mediana</span>
                                    <span class="badge bg-info text-dark">${o.canal}</span>
                                    <span class="badge bg-dark text-secondary">${views} views</span>
                                    <div class="fw-bold mt-1 small">${o.titulo}</div>
                                </div>
                                <button class="btn btn-warning btn-sm text-dark fw-bold text-nowrap" 
                                        onclick="processarAngleFlip('${safeTit}', '${safeUrl}', '${safeCanal}')">
                                    🔄 Girar Ângulo
                                </button>
                            </div>
                        </div>
                    `;
                });
                lista.innerHTML = html;
            } catch (err) {
                statusMsg.classList.remove('d-none');
                statusMsg.innerHTML = `<span class="text-danger">Erro ao carregar radar de outliers: ${err}</span>`;
            }
        }

        function fecharRadarOutliers() {
            document.getElementById('radarOutliersBox').classList.add('d-none');
        }

        async function processarAngleFlip(titulo, url, canal) {
            const box = document.getElementById('radarOutliersBox');
            const statusMsg = document.getElementById('radarStatusMsg');
            statusMsg.classList.remove('d-none');
            statusMsg.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Transcrevendo áudio do concorrente e criando ângulo invisível com fatos para "${titulo}"...`;

            try {
                const formData = new FormData();
                formData.append('titulo', titulo);
                formData.append('url', url);
                formData.append('canal', canal);

                const res = await fetch('/api/radar/processar_angulo', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                statusMsg.classList.add('d-none');

                if (data.sucesso) {
                    // Preenche o formulário com o novo título sugerido
                    document.getElementById('tituloInput').value = data.titulo_sugerido;
                    document.getElementById('tipoShort').checked = true;

                    // Exibe a mensagem de sucesso e abre a mesa de revisão humana
                    alert(`✅ Ângulo Exclusivo Descoberto!\n\nNovo Ângulo: ${data.novo_angulo}\n\nO dossiê factual já foi criado com ${data.total_fatos} fatos verificados. Abrindo a Mesa de Revisão...`);

                    // Preenche os dados da revisão editorial humana
                    abrirMesaComTarefaPronta(data);
                } else {
                    alert(`Erro ao processar ângulo: ${data.erro || 'Falha desconhecida'}`);
                }
            } catch (e) {
                alert(`Erro de comunicação com o servidor: ${e}`);
                statusMsg.classList.add('d-none');
            }
        }

        function abrirMesaComTarefaPronta(data) {
            tarefaEditorialAtual = {
                task_id: data.task_id,
                titulo: data.titulo_sugerido,
                roteiro: data.roteiro,
                palavras_narradas: data.palavras_narradas,
                json_path: data.json_factual_path,
                versao_minuta: 1,
                hash_minuta: "-",
                afirmacoes_factuais: (data.afirmacoes || []).map(f => ({
                    id: f.id,
                    frase: f.frase,
                    estado: "verificado_original",
                    fontes: [{ nome: f.fonte || "Imprensa Esportiva Oficial" }]
                })),
                bloqueio_motivo: ""
            };
            renderizarPainelRevisao(tarefaEditorialAtual);
            window.scrollTo({ top: document.getElementById('painelRevisaoEditorial').offsetTop - 30, behavior: 'smooth' });
        }

        async function buscarGanchos() {
            const titulo = document.getElementById('tituloInput').value.trim();
            if (!titulo) {
                alert("Por favor, digite o tema ou título antes de gerar os ganchos!");
                return;
            }
            btnGerarGanchos.disabled = true;
            btnGerarGanchos.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Criando 3 Ganchos...';
            try {
                const formData = new FormData();
                formData.append('titulo', titulo);
                const res = await fetch('/api/ganchos', { method: 'POST', body: formData });
                const data = await res.json();
                if (data.ganchos && data.ganchos.length > 0) {
                    let html = '';
                    data.ganchos.forEach((g, idx) => {
                        html += `
                            <div class="card bg-black border-secondary p-3 text-light" style="cursor: pointer; transition: 0.2s;" 
                                 onclick="selecionarGancho('${g.texto.replace(/'/g, "\\'")}', this)">
                                <div class="d-flex justify-content-between align-items-center mb-1">
                                    <span class="badge bg-warning text-dark fw-bold">${g.tipo}</span>
                                    <small class="text-secondary">Opção ${idx + 1}</small>
                                </div>
                                <div class="fs-6 fw-bold">"${g.texto}"</div>
                            </div>
                        `;
                    });
                    listaGanchos.innerHTML = html;
                    ganchosContainer.classList.remove('d-none');
                }
            } catch (err) {
                alert("Não foi possível gerar os ganchos automáticos. Você pode gerar o vídeo direto!");
            } finally {
                btnGerarGanchos.disabled = false;
                btnGerarGanchos.innerHTML = '🎯 ANALISAR & GERAR 3 GANCHOS';
            }
        }

        function selecionarGancho(texto, el) {
            ganchoEscolhidoInput.value = texto;
            document.querySelectorAll('#listaGanchos .card').forEach(c => {
                c.classList.remove('border-warning');
                c.classList.add('border-secondary');
            });
            el.classList.remove('border-secondary');
            el.classList.add('border-warning');
            btnSubmit.innerHTML = '⚡ GERAR VÍDEO COM GANCHO ESCOLHIDO';
            btnSubmit.classList.add('glow');
        }

        function cancelarGanchos() {
            ganchosContainer.classList.add('d-none');
            ganchoEscolhidoInput.value = '';
            btnSubmit.innerHTML = '⚡ GERAR VÍDEO COMPLETO DIRETO';
            btnSubmit.classList.remove('glow');
        }

        let paginaAtualHistorico = 1;
        const itensPorPaginaHistorico = 4;
        let todasTarefasHistorico = [];

        async function carregarTarefas() {
            try {
                const res = await fetch('/api/tarefas');
                const tarefas = await res.json();
                const keys = Object.keys(tarefas);
                if (keys.length === 0) {
                    listaTarefas.innerHTML = '<div class="text-secondary small p-3 text-center">Nenhum vídeo gerado ainda.</div>';
                    document.getElementById('historicoPaginacaoInfo').innerText = 'Página 1 de 1';
                    document.getElementById('btnPaginaAnt').disabled = true;
                    document.getElementById('btnPaginaProx').disabled = true;
                    return;
                }

                // Inverte para exibir os mais recentes primeiro
                todasTarefasHistorico = keys.reverse().map(id => ({ id, ...tarefas[id] }));
                renderizarPaginaHistorico();
            } catch (e) {
                console.error(e);
            }
        }

        function renderizarPaginaHistorico() {
            const totalItens = todasTarefasHistorico.length;
            const totalPaginas = Math.max(1, Math.ceil(totalItens / itensPorPaginaHistorico));
            if (paginaAtualHistorico > totalPaginas) paginaAtualHistorico = totalPaginas;
            if (paginaAtualHistorico < 1) paginaAtualHistorico = 1;

            const inicio = (paginaAtualHistorico - 1) * itensPorPaginaHistorico;
            const fim = inicio + itensPorPaginaHistorico;
            const itensPagina = todasTarefasHistorico.slice(inicio, fim);

            document.getElementById('historicoPaginacaoInfo').innerText = `Página ${paginaAtualHistorico} de ${totalPaginas} (${totalItens} vídeos)`;
            document.getElementById('btnPaginaAnt').disabled = (paginaAtualHistorico <= 1);
            document.getElementById('btnPaginaProx').disabled = (paginaAtualHistorico >= totalPaginas);

            let html = '';
            itensPagina.forEach(t => {
                const id = t.id;
                const isPronto = t.status === "CONCLUÍDO";
                const isErro = (t.status || "").startsWith("Erro");
                const badgeClass = isPronto ? "bg-success" : (isErro ? "bg-danger" : "bg-warning text-dark");
                let icon = "📱 SHORT";
                if (t.tipo === "doc") icon = "🎬 DOC";
                if (t.tipo === "afiliado_moda") icon = "🛍️ MODA";
                const linkInfo = t.link_afiliado ? `<br><small class="text-info">🔗 ${t.link_afiliado}</small>` : '';

                // Trunca texto longo de erro ou detalhes para não estourar a tela
                let statusExibicao = t.status || '';
                if (statusExibicao.length > 110) {
                    statusExibicao = statusExibicao.substring(0, 107) + '...';
                }

                html += `
                    <div class="list-group-item bg-dark border-secondary text-light p-3 mb-2 rounded d-flex justify-content-between align-items-center flex-wrap gap-2">
                        <div style="max-width: 80%;">
                            <span class="badge bg-secondary me-2">${icon}</span>
                            <strong class="fs-6">${t.titulo}</strong>
                            ${linkInfo}<br>
                            <span class="badge ${badgeClass} mt-1 text-wrap text-start" title="${t.status}">${statusExibicao}</span>
                        </div>
                        <div class="d-flex gap-2 flex-wrap">
                            ${!isPronto ? `<button type="button" class="btn btn-warning btn-sm fw-bold px-2" title="Continuar ou refazer este vídeo" onclick="retentarProducaoHistorico('${id}')"><i class="bi bi-arrow-repeat me-1"></i>Continuar / Refazer</button>` : ''}
                            ${isPronto ? `<button type="button" class="btn btn-primary btn-sm fw-bold px-2" title="Assistir vídeo antes de postar" onclick="abrirPlayerHistorico('${id}', '${(t.titulo || '').replace(/'/g, "\\'")}', '${t.tipo}')"><i class="bi bi-play-fill me-1"></i>Assistir</button>` : ''}
                            ${isPronto ? `<a href="/api/download/${id}" class="btn btn-success btn-sm fw-bold px-2" title="Baixar MP4">📥 MP4</a>` : ''}
                            ${isPronto && t.txt_path ? `<a href="/api/download_txt/${id}" class="btn btn-outline-warning btn-sm fw-bold px-2">📄 TXT</a>` : ''}
                            ${isPronto ? `<button type="button" class="btn btn-danger btn-sm fw-bold px-2" title="Postar diretamente no canal" onclick="postarTaskYouTube('${id}')"><i class="bi bi-youtube me-1"></i>Postar</button>` : ''}
                            ${isPronto ? `<button type="button" class="btn btn-outline-secondary btn-sm px-2" title="Refazer este vídeo do zero" onclick="retentarProducaoHistorico('${id}')"><i class="bi bi-arrow-clockwise"></i></button>` : ''}
                        </div>
                    </div>
                `;
            });
            listaTarefas.innerHTML = html;
        }

                async function retentarProducaoHistorico(taskId) {
            if (!confirm("Deseja continuar ou renderizar este vídeo novamente do histórico?")) return;
            try {
                const res = await fetch('/api/tarefas/retentar/' + encodeURIComponent(taskId), { method: 'POST' });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Erro ao reiniciar");
                
                // Abre o card de progresso para acompanhar visualmente
                progressCard.classList.remove('d-none');
                spinner.classList.remove('d-none');
                statusText.innerText = "Reiniciando e continuando renderização...";
                acompanharTask(taskId);
                window.scrollTo({ top: progressCard.offsetTop - 40, behavior: 'smooth' });
            } catch (err) {
                alert("Erro ao retentar produção: " + err.message);
            }
        }

        function mudarPaginaHistorico(delta) {
            paginaAtualHistorico += delta;
            renderizarPaginaHistorico();
        }

                        function abrirPlayerHistorico(id, titulo, tipo) {
            const modalEl = document.getElementById('modalPlayerHistorico');
            const videoEl = document.getElementById('playerModalVideo');
            const infoEl = document.getElementById('modalVideoTituloInfo');
            if (!videoEl) return;
            videoEl.src = `/api/download/${id}`;
            if (tipo === 'doc') {
                videoEl.style.aspectRatio = '16/9';
                videoEl.style.maxHeight = '420px';
            } else {
                videoEl.style.aspectRatio = '9/16';
                videoEl.style.maxHeight = '520px';
            }
            if (infoEl) infoEl.innerText = titulo;
            videoEl.load();
            videoEl.play();
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        }

        function fecharPlayerHistorico() {
            const videoEl = document.getElementById('playerModalVideo');
            if (videoEl) {
                videoEl.pause();
                videoEl.currentTime = 0;
            }
        }

        let taskIdAtualUpload = null;

        async function postarTaskYouTube(id, privacy = 'unlisted') {
            if (!confirm(`Deseja fazer o upload deste vídeo diretamente para o YouTube Studio como "${privacy === 'unlisted' ? 'NÃO LISTADO' : 'PÚBLICO'}"?`)) return;
            const btn = event?.target;
            const originalText = btn ? btn.innerHTML : '';
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Enviando...';
            }
            try {
                const res = await fetch(`/api/youtube/upload/${id}?privacy=${privacy}`, { method: 'POST' });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Erro ao enviar vídeo');
                alert(`🎉 Vídeo postado com sucesso no YouTube!\n\nLink: ${data.video_url}`);
                window.open(data.video_url, '_blank');
                await carregarTarefas();
            } catch (err) {
                alert('Erro no upload: ' + err.message);
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                }
            }
        }

        async function uploadDiretoYouTube() {
            if (!ultimaTaskId) {
                alert('Nenhum vídeo recente selecionado para envio.');
                return;
            }
            const privacy = confirm('Postar como PUBLICO imediatamente?\n\nOK = PUBLICO\nCancelar = NAO LISTADO (recomendado para processar HD)') ? 'public' : 'unlisted';
            const btn = document.getElementById('btnUploadYT');
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Enviando para o YouTube...';
            try {
                const res = await fetch("/api/youtube/upload/" + encodeURIComponent(ultimaTaskId) + "?privacy=" + encodeURIComponent(privacy), { method: "POST" });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Erro ao enviar');
                alert('Video postado com sucesso no seu canal do YouTube!\n\nLink: ' + data.video_url);
                window.open(data.video_url, '_blank');
            } catch (err) {
                alert('Erro ao enviar vídeo para o YouTube: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }

        async function limparHistoricoProducao() {
            if (!confirm('Deseja realmente limpar todo o histórico de tarefas do painel?')) return;
            try {
                const res = await fetch('/api/tarefas/limpar', { method: 'POST' });
                const data = await res.json();
                todasTarefasHistorico = [];
                paginaAtualHistorico = 1;
                await carregarTarefas();
            } catch (err) {
                console.error('Erro ao limpar histórico:', err);
                alert('Erro ao limpar histórico.');
            }
        }

        setInterval(carregarTarefas, 3000);
        carregarTarefas();

        function copiarTexto(elementId) {
            const el = document.getElementById(elementId);
            el.select();
            document.execCommand('copy');
            alert('Copiado para a área de transferência! Pronto para colar no YouTube/TikTok!');
        }

        
        let idTarefaEmAndamento = null;

        async function cancelarProducaoAtiva() {
            if (!idTarefaEmAndamento) {
                alert("Nenhuma produção ativa para cancelar.");
                return;
            }
            if (!confirm("Deseja realmente cancelar a produção do vídeo em andamento?")) {
                return;
            }
            try {
                const btn = document.getElementById('btnCancelarProducao');
                if (btn) {
                    btn.disabled = true;
                    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Cancelando...';
                }
                const res = await fetch('/api/tarefas/cancelar/' + idTarefaEmAndamento, { method: 'POST' });
                const data = await res.json();
                statusText.innerText = "🛑 PRODUÇÃO CANCELADA PELO USUÁRIO";
                spinner.classList.add('d-none');
                btnSubmit.disabled = false;
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-x-circle me-1"></i>Cancelar Produção';
                }
                carregarTarefas();
            } catch (err) {
                console.error("Erro ao cancelar:", err);
                alert("Erro ao cancelar produção: " + err.message);
            }
        }

        function acompanharTask(taskId) {
            idTarefaEmAndamento = taskId;
            const postKitBox = document.getElementById('postKitBox');
            carregarTarefas();
            const interval = setInterval(async () => {
                const check = await fetch(`/api/status/${taskId}`);
                const task = await check.json();
                statusText.innerText = task.status;

                if (task.roteiro) {
                    roteiroBox.innerText = "Roteiro: " + task.roteiro;
                    roteiroBox.classList.remove('d-none');
                }

                if (task.status === "CONCLUÍDO") {
                    clearInterval(interval);
                    spinner.classList.add('d-none');
                    statusText.innerText = "✅ VÍDEO + CAPA PROMOCIONAL 100% PRONTOS!";
                    btnDownload.href = `/api/download/${taskId}`;
                    const btnDownloadThumb = document.getElementById('btnDownloadThumb');
                    if (btnDownloadThumb) btnDownloadThumb.href = `/api/download_thumb/${taskId}`;
                    const btnDownloadTxt = document.getElementById('btnDownloadTxt');
                    if (btnDownloadTxt) btnDownloadTxt.href = `/api/download_txt/${taskId}`;
                    downloadBox.classList.remove('d-none');

                    // Carrega e ativa o Player de Vídeo Embutido
                    const playerBox = document.getElementById('videoPlayerBox');
                    const videoPlayer = document.getElementById('studioVideoPlayer');
                    const playerInfo = document.getElementById('playerFormatoInfo');
                    if (playerBox && videoPlayer) {
                        videoPlayer.src = `/api/download/${taskId}`;
                        videoPlayer.load();
                        if (task.tipo === 'doc') {
                            videoPlayer.style.maxHeight = '380px';
                            videoPlayer.style.aspectRatio = '16/9';
                            if (playerInfo) playerInfo.innerText = 'Documentário 16:9 (Horizontal)';
                        } else {
                            videoPlayer.style.maxHeight = '480px';
                            videoPlayer.style.aspectRatio = '9/16';
                            if (playerInfo) playerInfo.innerText = 'Short Vertical 9:16';
                        }
                        playerBox.classList.remove('d-none');
                    }

                    if (task.post_titulo) {
                        document.getElementById('kitTitulo').value = task.post_titulo;
                        document.getElementById('kitDescricao').value = task.post_descricao;
                        if (document.getElementById('kitTags')) {
                            document.getElementById('kitTags').value = task.post_tags || '';
                        }
                        document.getElementById('kitComentario').value = task.post_comentario;
                        postKitBox.classList.remove('d-none');
                    }

                    btnSubmit.disabled = false;
                    carregarTarefas();
                } else if ((task.status || "").startsWith("Erro") || (task.status || "").includes("CANCELADO")) {
                    clearInterval(interval);
                    spinner.classList.add('d-none');
                    btnSubmit.disabled = false;
                    carregarTarefas();
                }
            }, 3000);
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const titulo = document.getElementById('tituloInput').value;
            const tipo = document.querySelector('input[name="tipoVideo"]:checked').value;
            const promo = document.getElementById('promoInput') ? document.getElementById('promoInput').value : '';
            const fotosInput = document.getElementById('fotosInput');
            const ganchoEscolhido = ganchoEscolhidoInput.value;

            progressCard.classList.remove('d-none');
            spinner.classList.remove('d-none');
            statusText.innerText = `Enviando "${titulo}" para a fila de produção...`;

            const formData = new FormData();
            formData.append('titulo', titulo);
            formData.append('tipo', tipo);
            formData.append('promo', promo);
            formData.append('gancho_escolhido', ganchoEscolhido);
            if (fotosInput.files) {
                for (let i = 0; i < fotosInput.files.length; i++) {
                    formData.append('fotos', fotosInput.files[i]);
                }
            }

            const res = await fetch('/api/criar', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            acompanharTask(data.task_id);
        });

        // ========================================================
        // FUNÇÕES DO FLUXO EDITORIAL HUMAN-IN-THE-LOOP (FASE K)
        // ========================================================
        let tarefaEditorialAtual = null;

        async function iniciarRevisaoEditorial() {
            const titulo = document.getElementById('tituloInput').value.trim();
            const gancho = ganchoEscolhidoInput.value.trim();
            if (!titulo) {
                alert("Por favor, digite o título ou tema do vídeo antes de gerar a minuta!");
                return;
            }

            const btn = document.getElementById('btnRevisarEditorial');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Gerando Minuta & Fatos...';

            try {
                const formData = new FormData();
                formData.append('titulo', titulo);
                formData.append('gancho_escolhido', gancho);
                formData.append('tema_factual', titulo);

                const res = await fetch('/api/editorial/revisar', {
                    method: 'POST',
                    body: formData
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Erro ao gerar minuta");
                }
                const data = await res.json();
                tarefaEditorialAtual = data;
                renderizarPainelRevisao(data);
            } catch (e) {
                alert("Erro ao preparar minuta editorial: " + e.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '📝 GERAR MINUTA & REVISAR (FUTEBOL)';
            }
        }

        function renderizarPainelRevisao(data) {
            const painel = document.getElementById('painelRevisaoEditorial');
            painel.classList.remove('d-none');
            document.getElementById('editorialTaskId').innerText = data.task_id;
            document.getElementById('editorialVersao').innerText = data.versao_minuta || 1;
            document.getElementById('editorialHashMinuta').innerText = data.hash_minuta || '-';
            document.getElementById('editorialRoteiroTexto').value = data.roteiro || '';
            document.getElementById('editorialJsonPath').innerText = data.json_path || '(Nenhum vinculado)';
            document.getElementById('badgeStatusRevisao').innerText = data.status || 'PENDENTE DE REVISÃO';
            document.getElementById('badgeStatusRevisao').className = 'badge bg-warning text-dark px-3 py-2 fw-bold';

            recalcularPalavrasMinuta();

            // Renderizar Lista de Fatos
            const listaFatosEl = document.getElementById('editorialListaFatos');
            const fatos = data.afirmacoes_factuais || [];
            if (fatos.length === 0) {
                listaFatosEl.innerHTML = '<div class="text-danger small p-2">⚠️ Nenhuma evidência factual encontrada no arquivo associado.</div>';
            } else {
                let html = '<table class="table table-dark table-sm table-striped mb-0 small"><thead><tr><th>ID</th><th>Afirmação</th><th>Estado</th><th>Fontes</th></tr></thead><tbody>';
                fatos.forEach(f => {
                    const stBadge = (f.estado === "verificado_copia" || f.estado === "verificado_original")
                        ? '<span class="badge bg-success">Verificado</span>'
                        : '<span class="badge bg-danger">Pendente</span>';
                    const fontesNomes = (f.fontes || []).map(ft => ft.nome).join(', ') || 'Sem fonte';
                    html += `<tr><td><strong>${f.id}</strong></td><td>${f.frase}</td><td>${stBadge}</td><td><span class="text-secondary">${fontesNomes}</span></td></tr>`;
                });
                html += '</tbody></table>';
                listaFatosEl.innerHTML = html;
            }

            const alerta = document.getElementById('editorialAlertaFontes');
            if (data.bloqueio_motivo) {
                alerta.innerText = '⚠️ Atenção: ' + data.bloqueio_motivo;
                alerta.classList.remove('d-none');
                document.getElementById('btnAprovarEditorial').disabled = true;
            } else {
                alerta.classList.add('d-none');
                document.getElementById('btnAprovarEditorial').disabled = false;
            }

            document.getElementById('btnRenderizarEditorial').classList.add('d-none');
            window.scrollTo({ top: painel.offsetTop - 30, behavior: 'smooth' });
        }

        function recalcularPalavrasMinuta() {
            const txt = document.getElementById('editorialRoteiroTexto').value;
            const limpo = txt.replace(/\[.*?\]|\(.*?\)/g, ' ').replace(/[#*_~`]/g, ' ');
            const palavras = limpo.match(/[\wÀ-ÿ]+/g) || [];
            const qtd = palavras.length;
            document.getElementById('editorialQtdPalavras').innerText = qtd;

            const badge = document.getElementById('editorialStatusEstrutural');
            if (qtd >= 65 && qtd <= 85) {
                badge.className = 'badge bg-success';
                badge.innerText = 'Extensão Ideal (30-33s)';
            } else if (qtd < 65) {
                badge.className = 'badge bg-warning text-dark';
                badge.innerText = 'Curto (mínimo 65 palavras)';
            } else {
                badge.className = 'badge bg-danger';
                badge.innerText = 'Longo (máximo 85 palavras)';
            }

            // Qualquer edição invalida visualmente a aprovação prévia
            if (tarefaEditorialAtual && tarefaEditorialAtual.status === "APROVADO PARA RENDERIZAÇÃO") {
                document.getElementById('badgeStatusRevisao').innerText = 'ALTERADO (RE-APROVAÇÃO NECESSÁRIA)';
                document.getElementById('badgeStatusRevisao').className = 'badge bg-danger text-light px-3 py-2 fw-bold';
                document.getElementById('btnRenderizarEditorial').classList.add('d-none');
                document.getElementById('btnAprovarEditorial').disabled = false;
            }
        }

        async function executarAprovacaoEditorial() {
            if (!tarefaEditorialAtual || !tarefaEditorialAtual.task_id) return;
            const taskId = tarefaEditorialAtual.task_id;
            const roteiro = document.getElementById('editorialRoteiroTexto').value;
            let apiKey = document.getElementById('editorialApiKey')?.value?.trim();
            if (!apiKey) apiKey = 'futebol_invisivel_editorial_master_2026';
            const editorNome = document.getElementById('editorialNomeEditor').value;

            const btn = document.getElementById('btnAprovarEditorial');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Validando & Assinando...';

            try {
                const res = await fetch('/api/editorial/aprovar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        task_id: taskId,
                        roteiro_texto: roteiro,
                        editor_nome: editorNome,
                        api_key: apiKey
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || "Erro ao aprovar");
                }

                tarefaEditorialAtual.status = "APROVADO PARA RENDERIZAÇÃO";
                tarefaEditorialAtual.hash_guiao_aprovado = data.hash_guiao_aprovado;
                tarefaEditorialAtual.hash_json_aprovado = data.hash_json_aprovado;

                document.getElementById('badgeStatusRevisao').innerText = "✅ APROVADO PARA RENDERIZAÇÃO";
                document.getElementById('badgeStatusRevisao').className = "badge bg-success text-light px-3 py-2 fw-bold";
                document.getElementById('editorialHashMinuta').innerText = data.hash_guiao_aprovado;
                document.getElementById('btnRenderizarEditorial').classList.remove('d-none');
                alert(`Sucesso! Minuta aprovada formalmente por ${data.aprovado_por}. Hashes SHA-256 vinculados.`);
                carregarTarefas();
            } catch (e) {
                alert("Bloqueio de Aprovação: " + e.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '🛡️ APROVAR VERSÃO EXATA';
            }
        }

        async function executarRenderizacaoEditorial() {
            if (!tarefaEditorialAtual || !tarefaEditorialAtual.task_id) return;
            const taskId = tarefaEditorialAtual.task_id;
            let apiKey = document.getElementById('editorialApiKey')?.value?.trim();
            if (!apiKey) apiKey = 'futebol_invisivel_editorial_master_2026';
            const editorNome = document.getElementById('editorialNomeEditor')?.value?.trim() || 'Editor-Chefe';
            const roteiro = document.getElementById('editorialRoteiroTexto')?.value || '';

            const btn = document.getElementById('btnRenderizarEditorial');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Disparando Renderizador...';

            try {
                // Auto-aprova primeiro caso o usuário clique diretamente em Renderizar
                if (!tarefaEditorialAtual.hash_guiao_aprovado) {
                    const resAprov = await fetch('/api/editorial/aprovar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            task_id: taskId,
                            roteiro_texto: roteiro,
                            editor_nome: editorNome,
                            api_key: apiKey
                        })
                    });
                    if (!resAprov.ok) {
                        const errData = await resAprov.json();
                        throw new Error(errData.detail || 'Falha ao validar minuta antes de renderizar');
                    }
                    const dataAprov = await resAprov.json();
                    tarefaEditorialAtual.hash_guiao_aprovado = dataAprov.hash_guiao_aprovado;
                }

                const res = await fetch('/api/editorial/renderizar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        task_id: taskId,
                        api_key: apiKey
                    })
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || "Erro ao iniciar renderização");
                }

                document.getElementById('painelRevisaoEditorial').classList.add('d-none');
                progressCard.classList.remove('d-none');
                spinner.classList.remove('d-none');
                statusText.innerText = "Produção do vídeo aprovado em andamento...";
                acompanharTask(taskId);
            } catch (e) {
                alert("Erro ao disparar renderização: " + e.message);
                btn.disabled = false;
                btn.innerHTML = '🎬 RENDERIZAR VÍDEO APROVADO';
            }
        }

        function fecharPainelEditorial() {
            document.getElementById('painelRevisaoEditorial').classList.add('d-none');
        }

async function enviarRelatorioTelegram() {
    const btn = document.getElementById("btnRelatorioTelegram");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Enviando...';
    }
    try {
        const res = await fetch("/api/telegram/enviar_relatorio", { method: "POST" });
        const data = await res.json();
        if (res.ok) {
            alert("📱 " + (data.mensagem || "Relatório enviado com sucesso para o Telegram!"));
        } else {
            alert("Erro: " + (data.detail || "Falha ao enviar"));
        }
    } catch (e) {
        alert("Erro na requisição: " + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-telegram me-1 text-info"></i>📱 Relatório Telegram';
        }
    }
}
