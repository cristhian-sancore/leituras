/**
 * SAEMI SaaS - App Principal (pós-login)
 * Gerencia tabs, leituras, importações
 */

let currentImportacao = null;
let ocorrencias = [];
let saveTimers = {};

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
        loadDashboard();
        showTab('tab-leitura');
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
        const endereco = c.rua + (c.numero ? ', ' + c.numero : '');
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td data-label="Matrícula"><code>${c.matricula}</code></td>
            <td data-label="Cliente">
                <div style="font-weight:600;font-size:0.85rem">${c.nome}</div>
                <span class="badge badge-${c.categoria}">${catLabels[c.categoria] || c.categoria}</span>
            </td>
            <td data-label="Endereço" class="endereco-cell">
                <div>${endereco}</div>
                <div class="info-small">${c.bairro || ''}</div>
            </td>
            <td data-label="Zona"><code>${(c.zona || '').trim()}</code></td>
            <td data-label="Rota"><code>${(c.rota || '').trim()}</code></td>
            <td data-label="Leit. Ant." style="font-weight:600;color:#475569">${c.leitura_anterior}</td>
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
            <td data-label="Consumo" class="consumo-cell" id="cons-${c.id}">${c.consumo}</td>
            <td data-label="Total" class="total-cell" id="tot-${c.id}">${fmtMoeda(c.valor_total)}</td>
            <td data-label="Imprimir">
                <button class="btn btn-sm btn-outline" id="btn-print-${c.id}"
                    onclick="abrirImpressao(${c.id})"
                    title="Imprimir conta"
                    ${c.leitura_atual === null ? 'disabled style="opacity:0.4"' : ''}>
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

        // Atualizar UI
        const consCell = document.getElementById(`cons-${clienteId}`);
        const totCell = document.getElementById(`tot-${clienteId}`);
        consCell.textContent = result.consumo;
        totCell.textContent = fmtMoeda(result.valor_total);

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

        usuarios.forEach(u => {
            const date = new Date(u.created_at).toLocaleDateString('pt-BR');
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-weight:600">${u.nome}</td>
                <td>${u.email}</td>
                <td><span class="badge badge-${u.role}">${u.role}</span></td>
                <td>${u.ativo ? '✅ Ativo' : '❌ Inativo'}</td>
                <td>${date}</td>
                <td>
                    ${u.role !== 'admin' ? `<button class="btn btn-sm btn-danger" onclick="desativarUsuario(${u.id})">Desativar</button>` : ''}
                </td>
            `;
            tbody.appendChild(tr);
        });
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
