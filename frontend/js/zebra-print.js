/**
 * SAEMI - Módulo de Impressão Zebra ZQ520/ZQ521 via Web Bluetooth (CPCL)
 */

const ZebraPrint = (() => {
  let device = null;
  let server = null;
  let printCharacteristic = null;
  let customLayout = null;
  let customLayoutNotif = null;

  // UUIDs Zebra BLE
  const ZEBRA_SERVICE = '38eb4a80-c570-11e3-9507-0002a5d5c51b';
  const ZEBRA_WRITE   = '38eb4a82-c570-11e3-9507-0002a5d5c51b';
  const SPP_SERVICE   = '000018f0-0000-1000-8000-00805f9b34fb';
  const SPP_WRITE     = '00002af1-0000-1000-8000-00805f9b34fb';

  // ── Conexao Bluetooth ──────────────────────────────────
  async function connect() {
    if (!navigator.bluetooth) {
      throw new Error('Web Bluetooth nao suportado. Use Chrome no Android.');
    }
    try {
      device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: [ZEBRA_SERVICE, SPP_SERVICE]
      });
      server = await device.gatt.connect();
      try {
        const svc = await server.getPrimaryService(ZEBRA_SERVICE);
        printCharacteristic = await svc.getCharacteristic(ZEBRA_WRITE);
      } catch (_) {
        const svc = await server.getPrimaryService(SPP_SERVICE);
        printCharacteristic = await svc.getCharacteristic(SPP_WRITE);
      }
      device.addEventListener('gattserverdisconnected', onDisconnected);
      return true;
    } catch (e) {
      console.error('BT connect error:', e);
      throw new Error('Falha ao conectar: ' + e.message);
    }
  }

  function onDisconnected() {
    device = null; server = null; printCharacteristic = null;
    const el = document.getElementById('printer-status');
    if (el) { el.className = 'status-err'; el.textContent = 'Desconectado'; }
    const btn = document.getElementById('btn-imprimir');
    if (btn) btn.disabled = true;
  }

  function isConnected() { return printCharacteristic !== null; }

  // ── Envio BLE em chunks ────────────────────────────────
  async function sendData(dataStr) {
    if (!isConnected()) throw new Error('Impressora nao conectada');
    const data = new TextEncoder().encode(dataStr);
    const CHUNK = 512;
    for (let i = 0; i < data.length; i += CHUNK) {
      await printCharacteristic.writeValue(data.slice(i, i + CHUNK));
    }
    return true;
  }

  // ── Busca layouts da API ───────────────────────────────
  async function fetchLayout() {
    const token = localStorage.getItem('saemi_token');
    if (!token) return;
    try {
      const res = await fetch('/api/v1/empresa/layout', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      if (res.ok) {
        const data = await res.json();
        customLayout      = data.conteudo_cpcl || null;
        customLayoutNotif = data.conteudo_cpcl_notificacao || null;
        console.log('[ZebraPrint] Fatura:', !!customLayout, '| Notif:', !!customLayoutNotif);
      }
    } catch (e) {
      console.warn('[ZebraPrint] Sem layout customizado, usando generico.', e);
    }
  }

  // ── Mapa completo de variáveis ─────────────────────────
  function buildMap(dados) {
    const now  = new Date();
    const hora = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    const fv   = (n) => parseFloat(n || 0).toFixed(2);
    
    let codStr = (dados.matricula || '000000').replace(/\D/g, '');
    if (codStr.length % 2 !== 0) codStr = '0' + codStr; // I2OF5 exige numeração par

    return {
      '{NOME_COMPROMISSARIO}':  dados.nome        || '',
      '{ENDERECO_LOGRADOURO}':  dados.endereco    || '',
      '{ENDERECO_BAIRRO}':      dados.bairro      || '',
      '{ENDERECO_INSTALACAO}':  dados.endereco    || '',
      '{ENDERECO_ENTREGA}':     dados.endereco    || '',
      '{CEP}':                  dados.cep         || '',
      '{ROTA}':                 dados.rota        || '',
      '{SEQUENCIA}':            dados.setor       || '',
      '{LOTE}':                 '',
      '{QUADRA}':               '',
      '{COD_BAIXA}':            '',
      '{LIGACAO}':              dados.matricula   || '',
      '{COD_LIGACAO}':          dados.matricula   || '',
      '{REFERENCIA}':           dados.mes_ref     || '',
      '{NR_GUIA}':              dados.matricula   || '',
      '{CATEGORIA}':            dados.categoria   || '',
      // Lançamentos
      '{LANCAMENTO_DESC_1}':    'AGUA',
      '{LANCAMENTO_VAL_1}':     fv(dados.valor_agua),
      '{LANCAMENTO_DESC_2}':    'ESGOTO',
      '{LANCAMENTO_VAL_2}':     fv(dados.valor_esgoto),
      '{LANCAMENTO_DESC_3}':    'TAXA LIXO',
      '{LANCAMENTO_VAL_3}':     fv(dados.valor_lixo),
      // Leituras
      '{DATA_LEITURA_ANT}':     dados.data_leitura || '',
      '{DATA_LEITURA_ATU}':     dados.data_leitura || '',
      '{LEIT_ANT}':             String(dados.leit_anterior || 0),
      '{LEIT_ATUAL}':           String(dados.leit_atual    || 0),
      '{CONS_REAL}':            String(dados.consumo       || 0),
      '{CONS_FATURADO}':        String(dados.consumo       || 0),
      '{MEDIA}':                String(Math.round(parseFloat(dados.consumo || 0) / 6)),
      // Hidrômetro
      '{NR_HIDROMETRO}':        '',
      '{VAZAO}':                '',
      '{DIAMETRO}':             '',
      '{DATA_INSTALACAO}':      '',
      // Valores
      '{DATA_VENCIMENTO}':      dados.vencimento   || '',
      '{VALOR_PAGAR}':          fv(dados.valor_total),
      '{TOTAL_PAGAR}':          fv(dados.valor_total),
      '{DIVIDA}':               'R$ ' + fv(dados.valor_total),
      // Débitos anteriores (notificação)
      '{MES_ANO_1}':            dados.mes_ref     || '',
      '{VENCIMENTO_1}':         dados.vencimento  || '',
      '{VALOR_1}':              fv(dados.valor_total),
      '{MES_ANO_2}':            '',
      '{VENCIMENTO_2}':         '',
      '{VALOR_2}':              '',
      // Outros
      '{OCORRENCIA}':           dados.ocorrencia  || 'LEITURA NORMAL',
      '{CODIGO_BARRAS}':        codStr,
      '{LINHA_DIGITAVEL}':      dados.matricula   || '',
      '{DATA_EMISSAO}':         now.toLocaleDateString('pt-BR'),
      '{HORA_EMISSAO}':         hora,
    };
  }

  function aplicarVariaveis(cpcl, map) {
    for (const [key, val] of Object.entries(map)) {
      cpcl = cpcl.split(key).join(val);
    }
    
    // Forçar a instrução JOURNAL caso falte (evita o problema da impressora puxar papel infinitamente)
    if (!cpcl.includes('JOURNAL')) {
        cpcl = cpcl.replace(/(!\s.*\r?\n)/, '$1JOURNAL\r\n');
    }
    
    return cpcl;
  }

  // ── Layout genérico (fallback sem customização) ────────
  function layoutGenerico(dados) {
    const fv = (n) => parseFloat(n || 0).toFixed(2);
    return [
      '! 0 200 200 240 1',
      'JOURNAL',
      'IN-MILLIMETERS',
      'COUNTRY LATIN9',

      // CAIXA PRINCIPAL SUPERIOR (15 até 174)
      'LINE 2 15 100 15 0.2',
      'LINE 2 15 2 174 0.2',
      'LINE 100 15 100 174 0.2',
      'LINE 2 174 100 174 0.2',

      // DIVISÕES SUPERIORES
      'LINE 76 15 76 39 0.2',
      'LINE 76 22 100 22 0.2',
      'LINE 76 30 100 30 0.2',
      'LINE 76 34 100 34 0.2',
      'LINE 2 39 100 39 0.2',
      'LINE 2 44 100 44 0.2',

      'T 7 0 3 16 {NOME_COMPROMISSARIO}',
      'T 7 0 3 19 {ENDERECO_LOGRADOURO}',
      'T 7 0 3 22 CEP: {CEP}, Rota: {ROTA}',
      'T 7 0 3 25 END. ENT: {ENDERECO_BAIRRO}',
      'T 7 0 3 28 Sequencia anterior: {SEQUENCIA}',
      'T 7 0 3 31 LIGACAO: {LIGACAO}',

      'T 7 2 78 15 MES/ANO: {REFERENCIA}',
      'T 7 0 78 23 NR. GUIA',
      'T 7 0 78 26 {NR_GUIA}',
      'T 7 0 78 31 CATEGORIA/QTDE',
      'T 7 0 82 35 {CATEGORIA}',

      'T 7 0 30 40 DESCRICAO',
      'T 7 0 89 40 VALOR',

      'T 7 0 5 45 {LANCAMENTO_DESC_1}',
      'T 7 0 87 45 {LANCAMENTO_VAL_1}',
      'T 7 0 5 48 {LANCAMENTO_DESC_2}',
      'T 7 0 87 48 {LANCAMENTO_VAL_2}',
      'T 7 0 5 51 TAXA LIXO/OUTROS',
      'T 7 0 87 51 {LANCAMENTO_VAL_3}',

      // TABELA DATA LEITURA
      'LINE 2 80 100 80 0.2',
      'LINE 28 80 28 89 0.2',
      'LINE 50 80 50 89 0.2',
      'LINE 78 80 78 89 0.2',
      'LINE 2 89 100 89 0.2',

      'T 7 0 4 80 DT. LEIT. ANT',
      'T 7 2 5 83 {DATA_LEITURA_ANT}',
      'T 7 0 30 80 DT. LEIT. ATUAL',
      'T 7 2 30 83 {DATA_LEITURA_ATU}',
      'T 7 0 60 80 VENCIMENTO',
      'T 7 2 56 83 {DATA_VENCIMENTO}',
      'T 7 0 80 80 VALOR A PAGAR',
      'T 7 2 82 83 R$ {VALOR_PAGAR}',

      // TABELA CONSUMO
      'LINE 25 89 25 97 0.2',
      'LINE 44 89 44 97 0.2',
      'LINE 60 89 60 97 0.2',
      'LINE 78 89 78 97 0.2',
      'LINE 2 97 100 97 0.2',
      'LINE 2 105 100 105 0.2',

      'T 7 0 7 89 LEITURA ANT.',
      'T 7 0 28 89 LEITURA ATUAL',
      'T 7 0 45 89 CONS. REAL',
      'T 7 0 61 89 CONS. FATUR.',
      'T 7 0 86 89 MEDIA',

      'T 5 0 9 93 {LEIT_ANT}',
      'T 5 0 30 93 {LEIT_ATUAL}',
      'T 5 0 50 93 {CONS_REAL}',
      'T 5 0 66 93 {CONS_FATURADO}',
      'T 5 0 87 93 {MEDIA}',

      // TABELA HIDROMETRO
      'LINE 44 97 44 105 0.2',
      'LINE 60 97 60 105 0.2',
      'LINE 78 97 78 105 0.2',

      'T 7 0 15 97 NR. DO HIDROMETRO',
      'T 7 0 50 97 VAZAO',
      'T 7 0 64 97 DIAMETRO',
      'T 7 0 80 97 DATA INST.',

      'T 5 0 15 101 {NR_HIDROMETRO}',

      'LINE 2 110 100 110 0.2',
      'T 7 0 4 107 OCORRENCIA: {OCORRENCIA}',

      // DADOS HISTORICO / MENSAGEM
      'LINE 44 110 44 144 0.2',
      'T 7 0 4 110 ULTIMOS 6 MESES',
      'LINE 2 114 44 114 0.2',

      'T 7 0 4 114 MES',
      'T 7 0 18 114 CONSUMO',
      'T 7 0 31 114 DIAS',
      'T 7 0 38 114 MEDIA',

      'T 7 0 45 110 MENSAGEM',

      // QUALIDADE E LEGISLACAO
      'LINE 2 144 100 144 0.2',
      'T 7 0 10 144 DETALHES SOBRE',
      'T 7 0 8 147 LEGISLACAO VIDE VERSO',
      'LINE 35 144 35 151 0.2',

      'T 7 0 42 145 PERIODO DA ANALISE:',
      'LINE 2 151 100 151 0.2',

      'T 7 0 10 152 PARAMETRO',
      'T 7 0 28 152 UNIDADE',
      'T 7 0 47 152 VMP',
      'T 7 0 60 151 ANALISES',
      'T 7 0 64 154 REALIZADAS',
      'T 7 0 87 151 V. MEDIO',
      'T 7 0 87 154 DETECTADO',

      'LINE 2 157 100 157 0.2',
      
      'T 7 0 3 176 AUTENTICAR NO VERSO - DEVOLVER AO USUARIO',
      'T 7 0 76 176 EMISSAO: {DATA_EMISSAO} {HORA_EMISSAO}',

      // CAIXA DO CANHOTO (de 182 a 206)
      'LINE 2 182 2 206 0.2',
      'LINE 100 182 100 206 0.2',
      'LINE 2 182 100 182 0.2',
      'LINE 2 199 100 199 0.2',
      'LINE 2 206 100 206 0.2',
      'LINE 76 182 76 206 0.2',

      'T 7 0 3 184 {NOME_COMPROMISSARIO}',
      'T 7 0 3 187 {ENDERECO_LOGRADOURO}',
      'T 7 0 3 190 CEP: {CEP}, Rota: {ROTA}',
      'T 7 0 3 193 END. ENT: {ENDERECO_BAIRRO}',
      'T 7 0 3 196 Sequencia anterior: {SEQUENCIA}',

      'T 7 0 78 184 MES/ANO: {REFERENCIA}',
      'LINE 76 187 100 187 0.2',
      'T 7 0 78 188 NR. GUIA',
      'T 7 0 78 190 {NR_GUIA}',
      'LINE 76 193 100 193 0.2',
      'T 7 0 78 194 CATEGORIA/QTDE',
      'T 7 0 82 197 {CATEGORIA}',

      'T 7 0 12 200 LIGACAO',
      'T 7 0 12 203 {LIGACAO}',
      'LINE 35 199 35 206 0.2',
      'T 7 0 47 200 VENCIMENTO',
      'T 7 0 47 203 {DATA_VENCIMENTO}',
      'T 7 0 80 200 VALOR A PAGAR',
      'T 7 0 82 203 R$ {VALOR_PAGAR}',

      'CENTER',
      'T 5 0 0 208 {LINHA_DIGITAVEL}',
      'B I2OF5 0.245 25 8 0 213 {CODIGO_BARRAS}',
      'FORM',
      'PRINT',
    ].join('\r\n');
  }

  // ── Gerar CPCL da fatura ───────────────────────────────
  function gerarCPCL(dados) {
    const raw = customLayout || layoutGenerico(dados);
    return aplicarVariaveis(raw, buildMap(dados));
  }

  // ── Gerar CPCL da notificacao ─────────────────────────
  function gerarCPCLNotificacao(dados) {
    if (!customLayoutNotif) return null;
    return aplicarVariaveis(customLayoutNotif, buildMap(dados));
  }

  // ── Imprimir conta + notificacao ──────────────────────
  async function imprimirConta(dados) {
    // Pagina 1: Fatura
    await sendData(gerarCPCL(dados));

    // Pagina 2: Notificacao (somente se houver layout e flag)
    const cpclNotif = gerarCPCLNotificacao(dados);
    if (cpclNotif && dados.tem_notificacao) {
      await new Promise(r => setTimeout(r, 1200));
      await sendData(cpclNotif);
    }
    return true;
  }

  return {
    connect,
    isConnected,
    sendData,
    imprimirConta,
    fetchLayout,
    gerarCPCL,
    gerarCPCLNotificacao,
  };

})();
