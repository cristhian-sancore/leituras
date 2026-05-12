/**
 * SAEMI SaaS - App Principal (pós-login)
 * Gerencia tabs, leituras, importações
 */

let currentImportacao = null;
let ocorrencias = [];
let saveTimers = {};

// ============================================
// SEGURANÇA — Sanitização XSS
// ============================================
/**
 * Escapa HTML para prevenir XSS Stored via dados do arquivo .REM
 * Converte < > " ' & em entidades HTML seguras
 */
function sanitize(str) {
    if (str == null) return '';
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(String(str)));
    return d.innerHTML;
}

// ============================================
// INIT
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
    if (!checkAuth()) return;

    const user = api.getUser();
    if (user) {
        if (user.role === 'superadmin') {
            window.location.href = '/superadmin.html';
            return;
        }

        document.getElementById('user-name').textContent = user.nome;
        document.getElementById('user-role').textContent = user.role;
        document.getElementById('user-avatar').textContent = getInitials(user.nome);

        // Badge no mobile-header
        const mb = document.getElementById('mobile-user-badge');
        if (mb) mb.textContent = getInitials(user.nome);

        // Esconder items de admin se não for supervisor
        if (user.role !== 'supervisor') {
            document.querySelectorAll('.admin-only').forEach(el => el.classList.add('hidden'));
        }
    }

    showTab('tab-dashboard');
    loadDashboard();
});

// ============================================
// SIDEBAR MOBILE
// ============================================
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const btn = document.getElementById('hamburger-btn');
    const isOpen = sidebar.classList.contains('open');
    if (isOpen) {
        closeSidebar();
    } else {
        sidebar.classList.add('open');
        overlay.classList.add('open');
        btn.classList.add('open');
    }
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const btn = document.getElementById('hamburger-btn');
    sidebar.classList.remove('open');
    overlay.classList.remove('open');
    btn.classList.remove('open');
}

// ============================================
// NAVIGATION
// ============================================
function showTab(tabId, navEl) {
    // Fechar sidebar no mobile ao trocar de aba
    closeSidebar();
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
    // Remove active from nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    // Show selected tab
    const tab = document.getElementById(tabId);
    if (tab) tab.classList.remove('hidden');

    // Activate nav
    if (navEl) {
        navEl.classList.add('active');
    } else {
        // Find nav by data-tab
        const nav = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
        if (nav) nav.classList.add('active');
    }

    // Load data for tab
    switch (tabId) {
        case 'tab-dashboard': loadDashboard(); break;
        case 'tab-leitura': loadLeituras(); break;
        case 'tab-precos': loadPrecos(); break;
        case 'tab-historico': loadHistorico(); break;
        case 'tab-usuarios': loadUsuarios(); break;
        case 'tab-distribuicao': loadDistribuicao(); break;
    }
}

// ============================================
// DASHBOARD
// ============================================
async function loadDashboard() {
    try {
        const data = await api.getDashboard();

        document.getElementById('dash-total-imp').textContent = data.total_importacoes;
        document.getElementById('dash-total-users').textContent = data.total_usuarios;

        if (data.importacao_ativa) {
            currentImportacao = data.importacao_ativa;
            document.getElementById('dash-imp-nome').textContent = data.importacao_ativa.nome_arquivo;
            document.getElementById('dash-imp-status').textContent = data.importacao_ativa.status;
            document.getElementById('imp-active-info').classList.remove('hidden');
            document.getElementById('imp-empty-info').classList.add('hidden');
        } else {
            document.getElementById('imp-active-info').classList.add('hidden');
            document.getElementById('imp-empty-info').classList.remove('hidden');
        }

        if (data.stats) {
            document.getElementById('dash-clientes').textContent = fmtNumero(data.stats.total_clientes);
            document.getElementById('dash-realizadas').textContent = fmtNumero(data.stats.leituras_realizadas);
            document.getElementById('dash-pendentes').textContent = fmtNumero(data.stats.leituras_pendentes);
            document.getElementById('dash-consumo').textContent = fmtNumero(data.stats.consumo_total) + ' m³';
            document.getElementById('dash-valor').textContent = fmtMoeda(data.stats.valor_total);

            // Progress
            const pct = data.stats.total_clientes > 0
                ? ((data.stats.leituras_realizadas / data.stats.total_clientes) * 100).toFixed(1)
                : 0;
            document.getElementById('dash-progress-fill').style.width = pct + '%';
            document.getElementById('dash-progress-text').textContent = pct + '%';
        }

        // Progresso por rota
        if (currentImportacao) {
            const rotas = await api.getProgressoRota(currentImportacao.id);
            const rotasEl = document.getElementById('dash-rotas');
            rotasEl.innerHTML = '';
            rotas.forEach(r => {
                rotasEl.innerHTML += `
                    <div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--border-light)">
                        <code style="font-weight:700;width:50px">${r.rota}</code>
                        <div style="flex:1">
                            <div class="progress-bar"><div class="progress-fill" style="width:${r.percentual}%"></div></div>
                        </div>
                        <span style="font-size:0.8rem;color:var(--text-light);width:80px;text-align:right">${r.realizadas}/${r.total}</span>
                        <span style="font-weight:700;font-size:0.8rem;width:50px;text-align:right">${r.percentual}%</span>
                    </div>`;
            });
        }
    } catch (err) {
        console.error('Dashboard error:', err);
    }
}

// ============================================
// UPLOAD .REM
// ============================================
async function handleUpload() {
    const input = document.getElementById('file-rem');
    const file = input.files[0];
    if (!file) {
        showToast('Selecione um arquivo .REM', 'error');
        return;
    }

    showLoading();
    try {
        const imp = await api.uploadREM(file);
        currentImportacao = imp;
        showToast(`Arquivo importado! ${imp.total_clientes} clientes carregados.`);
        input.value = '';
        // Atualiza dashboard em segundo plano
        loadDashboard();
        // Verifica se o usuário é supervisor → vai pra Distribuição
        const user = api.getUser();
        if (user && user.role === 'supervisor') {
            showTab('tab-distribuicao');
            await loadDistribuicao();
        } else {
            showTab('tab-leitura');
        }
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        hideLoading();
    }
}

// ============================================
// LEITURAS
// ============================================
async function loadLeituras() {
    if (!currentImportacao) {
        // Tentar carregar importação ativa
        try {
            const imps = await api.listImportacoes();
            const ativa = imps.find(i => i.status === 'ativo');
            if (ativa) currentImportacao = ativa;
            else return;
        } catch { return; }
    }

    try {
        // Carregar ocorrências
        ocorrencias = await api.getOcorrencias(currentImportacao.id);

        // Carregar stats
        const stats = await api.getStats(currentImportacao.id);
        document.getElementById('stat-total').textContent = stats.total_clientes;
        document.getElementById('stat-pend').textContent = stats.leituras_pendentes;
        document.getElementById('stat-consumo').textContent = fmtNumero(stats.consumo_total) + ' m³';

        // Carregar clientes
        const busca = document.getElementById('search-input')?.value || '';
        const clientes = await api.getClientes(currentImportacao.id, busca);
        renderClientes(clientes);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function renderClientes(clientes) {
    const tbody = document.getElementById('lista-clientes');
    tbody.innerHTML = '';

    if (!clientes.length) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:var(--text-muted);padding:40px">Nenhum cliente encontrado</td></tr>';
        return;
    }

    // Options de ocorrência
    let ocorrOptions = '<option value="">Normal</option>';
    ocorrencias.forEach(o => {
        ocorrOptions += `<option value="${o.codigo}">${o.codigo.padStart(4, '0')} - ${o.descricao}</option>`;
    });

    const catLabels = {
        residencial: 'Residencial', comercial: 'Comercial',
        industrial: 'Industrial', publica: 'Pública', tarifa_social: 'Social'
    };

    clientes.forEach(c => {
        const enderecoRaw = (c.rua || '') + (c.numero ? ', ' + c.numero : '');
        // Sanitizar TODOS os dados do .REM para prevenir XSS Stored
        const sMatricula = sanitize(c.matricula);
        const sNome     = sanitize(c.nome);
        const sEndereco = sanitize(enderecoRaw);
        const sBairro   = sanitize(c.bairro);
        const sZona     = sanitize((c.zona || '').trim());
        const sRota     = sanitize((c.rota || '').trim());
        const catLabel  = sanitize(catLabels[c.categoria] || c.categoria);

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td data-label="Matrícula"><code>${sMatricula}</code></td>
            <td data-label="Cliente">
                <div style="font-weight:600;font-size:0.85rem">${sNome}</div>
                <span class="badge badge-${sanitize(c.categoria)}">${catLabel}</span>
            </td>
            <td data-label="Endereço" class="endereco-cell">
                <div>${sEndereco}</div>
                <div class="info-small">${sBairro}</div>
            </td>
            <td data-label="Zona"><code>${sZona}</code></td>
            <td data-label="Rota"><code>${sRota}</code></td>
            <td data-label="Leit. Ant." style="font-weight:600;color:#475569">${sanitize(c.leitura_anterior)}</td>
            <td data-label="Leit. Atual">
                <input type="number" class="leitura-input" 
                    value="${c.leitura_atual !== null ? c.leitura_atual : ''}" 
                    oninput="onLeituraChange(${c.id}, this.value)"
                    placeholder="0" id="leit-${c.id}">
            </td>
            <td data-label="Ocorrência">
                <select class="ocorrencia-select" onchange="onOcorrenciaChange(${c.id}, this.value)" id="ocorr-${c.id}">
                    ${ocorrOptions}
                </select>
            </td>
            <td data-label="Consumo" class="consumo-cell" id="cons-${c.id}">${sanitize(c.consumo)}</td>
            <td data-label="Total" class="total-cell" id="tot-${c.id}">${fmtMoeda(c.valor_total)}</td>
            <td data-label="Imprimir">
                <button class="btn btn-sm btn-outline" id="btn-print-${c.id}"
                    onclick="abrirImpressao(${c.id})"
                    title="Imprimir conta"
                    ${(c.leitura_atual === null && (!c.ocorrencia_codigo || c.ocorrencia_codigo === '0000')) ? 'disabled style="opacity:0.4"' : ''}>
                    🖨️
                </button>
            </td>
        `;
        tbody.appendChild(tr);

        // Selecionar ocorrência correta
        if (c.ocorrencia_codigo) {
            const sel = document.getElementById(`ocorr-${c.id}`);
            if (sel) sel.value = c.ocorrencia_codigo;
        }
    });
}

function onLeituraChange(clienteId, value) {
    // Debounce: salvar após 500ms de inatividade
    if (saveTimers[clienteId]) clearTimeout(saveTimers[clienteId]);
    saveTimers[clienteId] = setTimeout(() => {
        salvarLeitura(clienteId);
    }, 500);
}

function onOcorrenciaChange(clienteId, value) {
    salvarLeitura(clienteId);
}

async function salvarLeitura(clienteId) {
    const leituraInput = document.getElementById(`leit-${clienteId}`);
    const ocorrSelect = document.getElementById(`ocorr-${clienteId}`);

    if (!leituraInput) return;

    const leituraAtual = leituraInput.value ? parseInt(leituraInput.value) : null;
    const ocorrencia = ocorrSelect ? ocorrSelect.value : '';
    const temOcorrenciaEspecial = ocorrencia && ocorrencia !== '0000';

    // Não salvar se: sem leitura E sem ocorrência especial (nada a salvar)
    if (leituraAtual === null && !temOcorrenciaEspecial) return;

    // Capturar GPS se disponível
    let latitude = null, longitude = null;
    if (navigator.geolocation) {
        try {
            const pos = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 });
            });
            latitude = pos.coords.latitude;
            longitude = pos.coords.longitude;
        } catch { /* GPS não disponível */ }
    }

    try {
        const result = await api.salvarLeitura(clienteId, {
            leitura_atual: leituraAtual,
            ocorrencia_codigo: ocorrencia || null,
            latitude,
            longitude,
        });

        // Atualizar UI — células de consumo e total
        const consCell = document.getElementById(`cons-${clienteId}`);
        const totCell = document.getElementById(`tot-${clienteId}`);
        consCell.textContent = result.consumo;
        totCell.textContent = fmtMoeda(result.valor_total);

        // Habilitar botão de impressão: quando tem leitura OU quando ocorrência especial foi salva
        const btnPrint = document.getElementById(`btn-print-${clienteId}`);
        if (btnPrint) {
            const ocorrAtual = ocorrSelect ? ocorrSelect.value : '';
            const temOcorrEspecial = ocorrAtual && ocorrAtual !== '0000';
            if (leituraAtual !== null || temOcorrEspecial) {
                btnPrint.disabled = false;
                btnPrint.style.opacity = '1';
            } else {
                btnPrint.disabled = true;
                btnPrint.style.opacity = '0.4';
            }
        }

        // Alertas de consumo alto/baixo/zero
        consCell.style.color = '';
        consCell.style.fontWeight = '';
        consCell.title = '';
        if (result.alerta === 'alto') {
            consCell.style.color = '#ef4444';
            consCell.style.fontWeight = '800';
            consCell.title = result.mensagem;
            showToast(result.mensagem, 'error');
        } else if (result.alerta === 'zero') {
            consCell.style.color = '#f59e0b';
            consCell.style.fontWeight = '800';
            consCell.title = result.mensagem;
            showToast(result.mensagem, 'error');
        } else if (result.alerta === 'baixo') {
            consCell.style.color = '#3b82f6';
            consCell.style.fontWeight = '800';
            consCell.title = result.mensagem;
            showToast(result.mensagem, 'error');
        }

        // Atualizar stats (sem bloquear)
        updateStats();
    } catch (err) {
        showToast('Erro ao salvar: ' + err.message, 'error');
    }
}

async function updateStats() {
    if (!currentImportacao) return;
    try {
        const stats = await api.getStats(currentImportacao.id);
        document.getElementById('stat-total').textContent = stats.total_clientes;
        document.getElementById('stat-pend').textContent = stats.leituras_pendentes;
        document.getElementById('stat-consumo').textContent = fmtNumero(stats.consumo_total) + ' m³';
    } catch { /* silent */ }
}

const debouncedSearch = debounce(() => loadLeituras(), 400);
function onSearch(value) {
    debouncedSearch();
}

// ============================================
// EXPORTAR .RET
// ============================================
async function exportarRET() {
    if (!currentImportacao) {
        showToast('Nenhuma importação ativa', 'error');
        return;
    }

    showLoading();
    try {
        const { blob, filename } = await api.exportarRET(currentImportacao.id);
        downloadBlob(blob, filename);
        showToast(`Arquivo ${filename} gerado com sucesso!`);
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        hideLoading();
    }
}

// ============================================
// PREÇOS
// ============================================
async function loadPrecos() {
    if (!currentImportacao) return;
    try {
        const tarifas = await api.getTarifas(currentImportacao.id);
        const container = document.getElementById('precos-content');
        container.innerHTML = '';

        // Agrupar por categoria
        const grouped = {};
        tarifas.forEach(t => {
            if (!grouped[t.categoria]) grouped[t.categoria] = { agua: [], lixo: [] };
            grouped[t.categoria][t.servico].push(t);
        });

        for (const [cat, servicos] of Object.entries(grouped)) {
            const card = document.createElement('div');
            card.className = 'card';
            card.style.display = 'inline-block';
            card.style.marginRight = '12px';
            card.style.marginBottom = '12px';
            card.style.verticalAlign = 'top';
            card.style.minWidth = '220px';

            let html = `<h3 style="margin-bottom:12px"><span class="badge badge-${cat}">${cat.toUpperCase()}</span></h3>`;

            if (servicos.agua.length) {
                const min = servicos.agua.find(f => f.valor_minimo);
                html += `<p style="font-size:0.85rem"><strong>Água Mín:</strong> ${min ? fmtMoeda(min.valor_minimo) : '-'}</p>`;
            }
            if (servicos.lixo.length) {
                const min = servicos.lixo.find(f => f.valor_minimo);
                html += `<p style="font-size:0.85rem"><strong>Lixo Mín:</strong> ${min ? fmtMoeda(min.valor_minimo) : '-'}</p>`;
            }

            card.innerHTML = html;
            container.appendChild(card);
        }

        if (!Object.keys(grouped).length) {
            container.innerHTML = '<p style="color:var(--text-muted)">Nenhuma tarifa carregada.</p>';
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ============================================
// HISTÓRICO
// ============================================
async function loadHistorico() {
    try {
        const imps = await api.listImportacoes();
        const tbody = document.getElementById('historico-body');
        tbody.innerHTML = '';

        imps.forEach(imp => {
            const date = new Date(imp.data_importacao).toLocaleDateString('pt-BR');
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><code>${imp.id}</code></td>
                <td style="font-weight:600">${imp.nome_arquivo}</td>
                <td>${date}</td>
                <td>${imp.total_clientes}</td>
                <td>
                    <span class="status-dot status-${imp.status}"></span>
                    ${imp.status}
                </td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="selectImportacao(${imp.id}, '${imp.nome_arquivo}', ${imp.total_clientes}, '${imp.status}', '${imp.mes_referencia || ''}')">
                        Abrir
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        if (!imps.length) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:30px">Nenhuma importação encontrada</td></tr>';
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function selectImportacao(id, nome, total, status, mesRef) {
    currentImportacao = { id, nome_arquivo: nome, total_clientes: total, status, mes_referencia: mesRef };
    showToast(`Importação "${nome}" selecionada`);
    showTab('tab-leitura');
}

// ============================================
// USUÁRIOS
// ============================================
async function loadUsuarios() {
    try {
        const usuarios = await api.listUsuarios();
        const tbody = document.getElementById('usuarios-body');
        tbody.innerHTML = '';

        if (!usuarios.length) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:30px">Nenhum usuário cadastrado</td></tr>';
            return;
        }

        const currentUser = api.getUser();

        usuarios.forEach(u => {
            const date = new Date(u.created_at).toLocaleDateString('pt-BR');
            const isSelf = currentUser && u.id === currentUser.id;
            const canEdit = u.role === 'leiturista' || u.role === 'supervisor';
            const tr = document.createElement('tr');
            tr.id = `user-row-${u.id}`;
            tr.innerHTML = `
                <td style="font-weight:600">${sanitize(u.nome)}</td>
                <td>${sanitize(u.email)}</td>
                <td><span class="badge badge-${u.role}">${u.role.toUpperCase()}</span></td>
                <td>${u.ativo ? '<span style="color:#22c55e">&#10003; Ativo</span>' : '<span style="color:#ef4444">&#10007; Inativo</span>'}</td>
                <td>${date}</td>
                <td style="display:flex;gap:6px;flex-wrap:wrap">
                    ${canEdit && !isSelf ? `
                        <button class="btn btn-sm btn-outline" onclick="abrirEditarUsuario(${u.id}, '${sanitize(u.nome)}', '${sanitize(u.email)}')" title="Editar usuário">
                            ✏️ Editar
                        </button>
                        <button class="btn btn-sm btn-outline" style="border-color:#f59e0b;color:#f59e0b" onclick="abrirResetSenha(${u.id}, '${sanitize(u.nome)}')" title="Redefinir senha">
                            🔑 Senha
                        </button>
                    ` : ''}
                    ${!isSelf ? `
                        <button class="btn btn-sm ${u.ativo ? 'btn-danger' : 'btn-outline'}" onclick="toggleUsuario(${u.id}, ${u.ativo})">
                            ${u.ativo ? 'Desativar' : 'Ativar'}
                        </button>
                    ` : '<span style="color:var(--text-muted);font-size:.75rem">(você)</span>'}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function abrirEditarUsuario(id, nomeAtual, emailAtual) {
    const novoNome = prompt(`Novo nome (atual: ${nomeAtual}):`, nomeAtual);
    if (novoNome === null) return; // cancelou
    const novoEmail = prompt(`Novo email (atual: ${emailAtual}):`, emailAtual);
    if (novoEmail === null) return;

    if (!novoNome.trim() || !novoEmail.trim()) {
        showToast('Nome e email não podem ser vazios', 'error');
        return;
    }

    api.updateUsuario(id, { nome: novoNome.trim(), email: novoEmail.trim() })
        .then(() => {
            showToast(`Usuário atualizado!`);
            loadUsuarios();
        })
        .catch(err => showToast(err.message, 'error'));
}

function abrirResetSenha(id, nome) {
    const novaSenha = prompt(`Nova senha para ${nome} (mínimo 6 caracteres):`);
    if (novaSenha === null) return; // cancelou
    if (novaSenha.length < 6) {
        showToast('A senha deve ter pelo menos 6 caracteres', 'error');
        return;
    }
    const confirmacao = prompt('Confirme a nova senha:');
    if (confirmacao === null) return;
    if (novaSenha !== confirmacao) {
        showToast('As senhas não conferem', 'error');
        return;
    }

    api._json(`/usuarios/${id}/reset-senha`, {
        method: 'POST',
        body: JSON.stringify({ nova_senha: novaSenha }),
    })
        .then(res => showToast(`🔑 ${res.detail}`))
        .catch(err => showToast(err.message, 'error'));
}

async function toggleUsuario(id, ativoAtual) {
    const acao = ativoAtual ? 'desativar' : 'reativar';
    if (!confirm(`Deseja ${acao} este usuário?`)) return;
    try {
        if (ativoAtual) {
            await api.deleteUsuario(id);  // desativa
        } else {
            await api.updateUsuario(id, { ativo: true });
        }
        showToast(`Usuário ${ativoAtual ? 'desativado' : 'reativado'}!`);
        loadUsuarios();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function criarUsuario(e) {
    e.preventDefault();
    const data = {
        nome: document.getElementById('new-user-nome').value,
        email: document.getElementById('new-user-email').value,
        senha: document.getElementById('new-user-senha').value,
        role: document.getElementById('new-user-role').value,
    };

    try {
        await api.createUsuario(data);
        showToast(`Usuário ${data.nome} criado!`);
        document.getElementById('form-new-user').reset();
        loadUsuarios();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ============================================
// IMPRESSÃO ZEBRA LIS
// ============================================
function abrirImpressao(clienteId) {
    const user = api.getUser();
    const imp = currentImportacao;
    if (!imp) return;

    // Coletar dados do DOM
    const leitAtual = document.getElementById(`leit-${clienteId}`)?.value || '0';
    const consumo = document.getElementById(`cons-${clienteId}`)?.textContent || '0';
    const total = document.getElementById(`tot-${clienteId}`)?.textContent?.replace(/[^0-9,]/g,'').replace(',','.') || '0';
    const ocorr = document.getElementById(`ocorr-${clienteId}`)?.value || '';

    // Montar URL com parâmetros
    const params = new URLSearchParams({
        mat: clienteId,
        mes: imp.mes_referencia || '',
        data: new Date().toLocaleDateString('pt-BR'),
        cons: consumo,
        total: total,
        ocorr: ocorr,
        leit: user?.nome || '',
    });

    window.open(`/print-conta.html?${params}`, '_blank', 'width=900,height=700');
}

async function desativarUsuario(id) {
    if (!confirm('Desativar este usuário?')) return;
    try {
        await api.deleteUsuario(id);
        showToast('Usuário desativado');
        loadUsuarios();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ============================================
// DISTRIBUICAO DE LEITURAS POR LEITURISTA
// ============================================

let _leituristas = [];

/** Mostra a zona de upload e esconde o conteúdo de atribuição */
function _distribModoUpload() {
    document.getElementById('distrib-upload-zone').style.display = '';
    document.getElementById('distrib-imp-info').style.display = 'none';
    document.getElementById('distrib-content').classList.add('hidden');
    document.getElementById('distrib-actions').style.display = 'none';
    document.getElementById('distrib-loading').style.display = 'none';
}

/** Mostra o conteúdo de atribuição após importar */
function _distribModoAtribuicao(imp) {
    document.getElementById('distrib-upload-zone').style.display = 'none';
    // Preenche info do arquivo
    document.getElementById('distrib-imp-nome').textContent = imp.nome_arquivo || imp.nome || 'Arquivo';
    document.getElementById('distrib-imp-detalhe').textContent =
        `${imp.total_clientes} clientes · Ref: ${imp.mes_referencia || '—'} · Status: ${imp.status}`;
    document.getElementById('distrib-imp-info').style.display = '';
    document.getElementById('distrib-content').classList.remove('hidden');
    document.getElementById('distrib-actions').style.display = 'flex';
}

/** Upload do .REM direto na aba Distribuição */
async function handleUploadDistribuicao(file) {
    if (!file) return;
    const loading = document.getElementById('distrib-loading');
    const zone    = document.getElementById('distrib-upload-zone');
    loading.style.display = '';
    zone.style.pointerEvents = 'none';
    try {
        console.log('[SAEMI] Iniciando upload:', file.name, file.size, 'bytes');
        const imp = await api.uploadREM(file);
        console.log('[SAEMI] Upload OK:', imp);
        currentImportacao = imp;
        showToast(`📂 ${imp.total_clientes} clientes carregados!`);
        document.getElementById('file-rem-distrib').value = '';
        _distribModoAtribuicao(imp);
        await _carregarAtribuicoes(imp.id);
        loadDashboard();
    } catch (err) {
        console.error('[SAEMI] Erro no upload/carregamento:', err);
        showToast('Erro ao importar: ' + (err.message || err), 'error');
    } finally {
        loading.style.display = 'none';
        zone.style.pointerEvents = '';
    }
}

/** Drag & drop na zona de upload */
function handleDropDistribuicao(event) {
    const file = event.dataTransfer.files[0];
    if (file) handleUploadDistribuicao(file);
}

/** Volta para a tela de upload (trocar arquivo) */
function resetDistribuicao() {
    currentImportacao = null;
    _distribModoUpload();
}

/** Carrega leituristas + rotas + progresso para uma importação */
async function _carregarAtribuicoes(impId) {
    console.log('[SAEMI] _carregarAtribuicoes impId=', impId);
    try {
        const [usuarios, rotas, progresso] = await Promise.all([
            api._json('/usuarios/').catch(e => { console.warn('usuarios erro:', e.message); return []; }),
            api._json(`/atribuicoes/${impId}/rotas`).catch(e => { console.warn('rotas erro:', e.message); return []; }),
            api._json(`/atribuicoes/${impId}/leituristas`).catch(e => { console.warn('leituristas erro:', e.message); return []; }),
        ]);
        console.log('[SAEMI] usuarios:', usuarios?.length, '| rotas:', rotas?.length, '| progresso:', progresso?.length);
        _leituristas = (usuarios || []).filter(u => u.role === 'leiturista' && u.ativo);
        renderLeitureistaCards(progresso || [], _leituristas);
        renderRotasTable(rotas || [], _leituristas);
        // Popula select do painel "atribuir todos"
        const sel = document.getElementById('atrib-todos-select');
if (sel) {
    sel.innerHTML = '<option value=""></option>' + _leituristas.map(u => `<option value="${u.id}">${sanitize(u.nome)}</option>`).join('');
}
        sel.innerHTML = '<option value="">-- Selecione --</option>' +
            _leituristas.map(u => `<option value="${u.id}">${sanitize(u.nome)}</option>`).join('');
    } catch (err) {
        console.error('[SAEMI] _carregarAtribuicoes erro:', err);
        showToast('Erro ao carregar distribuição: ' + err.message, 'error');
    }
}

/** Carrega a aba de distribuição — chamado ao trocar de aba */
async function loadDistribuicao() {
    // Tenta recuperar importação ativa do servidor
    if (!currentImportacao) {
        try {
            const imps = await api.listImportacoes();
            const ativa = imps.find(i => i.status === 'ativo');
            if (ativa) {
                currentImportacao = ativa;
            } else {
                _distribModoUpload();
                return;
            }
        } catch {
            _distribModoUpload();
            return;
        }
    }
    // Há importação ativa — exibe direto
    _distribModoAtribuicao(currentImportacao);
    await _carregarAtribuicoes(currentImportacao.id);
}

function renderLeitureistaCards(progresso, leituristas) {
    const container = document.getElementById('leituristas-progresso');
    const idsComAtrib = new Set(progresso.map(p => p.leiturista_id));
    const semAtrib = leituristas.filter(u => !idsComAtrib.has(u.id));
    let html = '';
    progresso.forEach(p => {
        const perc = p.percentual;
        const completo = perc >= 100;
        const rotasStr = p.rotas.length ? p.rotas.join(', ') : 'nenhuma';
        html += `<div class="leiturista-card">
            <div class="leiturista-card-nome" title="${sanitize(p.nome)}">${sanitize(p.nome)}</div>
            <div class="leiturista-card-email">${sanitize(p.email)}</div>
            <div class="leiturista-card-rotas">Rotas: ${sanitize(rotasStr)}</div>
            <div class="progress-bar-wrap"><div class="progress-bar-fill ${completo ? 'completo' : ''}" style="width:${perc}%"></div></div>
            <div class="progress-label"><span>${p.leituras_feitas}/${p.total_clientes} leituras</span><span style="font-weight:600;color:${completo ? '#22c55e' : 'var(--primary)'}">${perc}%</span></div>
        </div>`;
    });
    semAtrib.forEach(u => {
        html += `<div class="leiturista-card" style="opacity:0.6">
            <div class="leiturista-card-nome">${sanitize(u.nome)}</div>
            <div class="leiturista-card-email">${sanitize(u.email)}</div>
            <div class="leiturista-card-rotas" style="color:var(--text-muted)">Sem rotas atribuídas</div>
            <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:0%"></div></div>
            <div class="progress-label"><span>0 leituras</span><span>0%</span></div>
        </div>`;
    });
    if (!html) html = '<p style="color:var(--text-muted);grid-column:1/-1">Nenhum leiturista cadastrado. Adicione leituristas na aba <strong>Usuários</strong>.</p>';
    container.innerHTML = html;
}

function renderRotasTable(rotas, leituristas) {
    const tbody = document.getElementById('rotas-tbody');
    if (!rotas || !rotas.length) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:30px">Nenhuma rota encontrada no arquivo.</td></tr>';
        return;
    }
    const opts = leituristas.map(u => `<option value="${u.id}">${sanitize(u.nome)}</option>`).join('');
    tbody.innerHTML = rotas.map(r => {
        const perc = r.percentual;
        const completo = perc >= 100;
        return `<tr>
            <td><strong>${sanitize(r.rota)}</strong></td>
            <td>${r.total_clientes}</td>
            <td>${r.leituras_feitas}</td>
            <td><div style="display:flex;align-items:center;gap:8px">
                <div class="rota-mini-bar"><div class="rota-mini-fill ${completo ? 'completo' : ''}" style="width:${perc}%"></div></div>
                <span style="font-size:.75rem;color:${completo ? '#22c55e' : 'var(--text-muted)'};min-width:36px">${perc}%</span>
            </div></td>
            <td><select class="rota-select" data-rota="${sanitize(r.rota)}">
                <option value="">-- Sem atribuição --</option>${opts}
            </select></td>
        </tr>`;
    }).join('');
    rotas.forEach(r => {
        if (r.leiturista_id) {
            const sel = tbody.querySelector(`select[data-rota="${r.rota}"]`);
            if (sel) sel.value = String(r.leiturista_id);
        }
    });
}

/** Painel rápido para atribuir TODAS as rotas ao mesmo leiturista */
function atribuirTodosParaUm() {
    const panel = document.getElementById('atrib-todos-panel');
    panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
}

function aplicarTodosParaUm() {
    const leitId = document.getElementById('atrib-todos-select').value;
    document.querySelectorAll('#rotas-tbody .rota-select').forEach(sel => {
        sel.value = leitId;
    });
    document.getElementById('atrib-todos-panel').style.display = 'none';
    showToast('Todas as rotas atribuídas! Clique em Salvar Distribuição para confirmar.');
}

async function salvarAtribuicoes() {
    if (!currentImportacao) return showToast('Nenhuma importação ativa', 'error');
    const selects = document.querySelectorAll('#rotas-tbody .rota-select');
    const atribuicoes = [];
    selects.forEach(sel => atribuicoes.push({
        rota: sel.getAttribute('data-rota'),
        leiturista_id: sel.value ? parseInt(sel.value) : null,
    }));
    const btn = document.getElementById('btn-salvar-atrib');
    btn.disabled = true; btn.textContent = '⏳ Salvando…';
    try {
        const res = await api._json(`/atribuicoes/${currentImportacao.id}/atribuir`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ atribuicoes }),
        });
        showToast(`✅ ${res.clientes_atualizados} clientes distribuídos com sucesso!`);
        await _carregarAtribuicoes(currentImportacao.id);
    } catch (err) {
        showToast('Erro ao salvar: ' + err.message, 'error');
    } finally {
        btn.disabled = false; btn.textContent = '💾 Salvar Distribuição';
    }
}

async function limparAtribuicoes() {
    if (!currentImportacao) return;
    if (!confirm('Remover todas as atribuições? Todos os leituristas voltarão a ver todos os clientes.')) return;
    try {
        const res = await api._json(`/atribuicoes/${currentImportacao.id}/limpar`, { method: 'DELETE' });
        showToast(`🗑️ Atribuições removidas (${res.clientes_atualizados} clientes)`);
        await _carregarAtribuicoes(currentImportacao.id);
    } catch (err) {
        showToast('Erro ao limpar: ' + err.message, 'error');
    }
}
