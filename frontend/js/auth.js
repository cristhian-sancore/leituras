/**
 * SAEMI SaaS - Auth Module
 * Gerencia login, registro e estado de autenticação
 */

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const senha = document.getElementById('login-senha').value;
    const btn = document.getElementById('login-btn');
    const errEl = document.getElementById('login-error');

    btn.disabled = true;
    btn.textContent = 'Entrando...';
    errEl.classList.add('hidden');

    try {
        const data = await api.login(email, senha);
        api.setTokens(data.access_token, data.refresh_token);
        api.setUser(data.user);
        window.location.href = '/app.html';
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Entrar';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById('register-btn');
    const errEl = document.getElementById('register-error');

    btn.disabled = true;
    btn.textContent = 'Cadastrando...';
    errEl.classList.add('hidden');

    const data = {
        nome: document.getElementById('reg-empresa').value,
        cnpj: document.getElementById('reg-cnpj').value || null,
        admin_nome: document.getElementById('reg-nome').value,
        admin_email: document.getElementById('reg-email').value,
        admin_senha: document.getElementById('reg-senha').value,
    };

    // Validar senha
    const senhaConf = document.getElementById('reg-senha-conf').value;
    if (data.admin_senha !== senhaConf) {
        errEl.textContent = 'As senhas não coincidem';
        errEl.classList.remove('hidden');
        btn.disabled = false;
        btn.textContent = 'Cadastrar Empresa';
        return;
    }

    try {
        const resp = await api.register(data);
        api.setTokens(resp.access_token, resp.refresh_token);
        api.setUser(resp.user);
        window.location.href = '/app.html';
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Cadastrar Empresa';
    }
}

function logout() {
    api.clearTokens();
    window.location.href = '/';
}

function checkAuth() {
    if (!api.isLoggedIn()) {
        window.location.href = '/';
        return false;
    }
    return true;
}
