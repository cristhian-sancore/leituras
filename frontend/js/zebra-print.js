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
      '! 0 200 200 600 1',
      'JOURNAL',
      'IN-MILLIMETERS',
      'COUNTRY LATIN9',

      // Borda Externa (X = 2 a 100)
      'LINE 2 4 100 4 0.2',
      'LINE 2 4 2 220 0.2',
      'LINE 100 4 100 220 0.2',

      // --- Bloco 1 (Cabeçalho Esquerda) ---
      'T 7 0 3 6 {NOME_COMPROMISSARIO}',
      'T 5 0 3 10 {ENDERECO_LOGRADOURO}',
      'T 5 0 3 13 {CEP}, {ENDERECO_BAIRRO}',
      'T 5 0 3 16 ROTA: {ROTA}-{SEQUENCIA}',
      'T 5 0 3 20 LIGACAO:{LIGACAO}    SEU CODIGO:{COD_LIGACAO}',

      // --- Bloco 1 (Caixa Direita) ---
      'LINE 62 4 62 23 0.2',
      'LINE 62 8 100 8 0.2',
      'LINE 62 15 100 15 0.2',
      'T 5 0 63 5 MES/ANO:{REFERENCIA}',
      'T 5 0 63 9 NR. GUIA',
      'T 5 0 63 12 {NR_GUIA}',
      'T 5 0 63 16 CATEGORIA/QTDE',
      'T 5 0 63 19 1-{CATEGORIA}',

      // --- Tabela Tarifária x Discriminação ---
      'LINE 2 23 100 23 0.2',
      'LINE 2 27 100 27 0.2',
      'LINE 48 23 48 100 0.2',
      'T 5 0 10 24 TABELA TARIFARIA (M3)',
      'T 5 0 52 24 DISCRIMINACAO DO FATURAMENTO',
      
      'LINE 2 31 100 31 0.2',
      'T 0 0 3 28 FAIXA DE CONSUMO    R$ AGUA',
      'T 0 0 52 28 TARIFAS E SERVICOS  R$ VALOR',

      'T 5 0 3 33 CATEGORIA: {CATEGORIA}',
      'T 5 0 3 36 00 a 10              9,7300',
      'T 5 0 3 39 11 a 9999           10,5400',

      'T 5 0 50 33 AGUA               {LANCAMENTO_VAL_1}',
      'T 5 0 50 36 TAXA DE LIXO*      {LANCAMENTO_VAL_3}',
      'T 5 0 50 39 ESGOTO             {LANCAMENTO_VAL_2}',

      // --- Bloco 3: Leituras ---
      'LINE 2 100 100 100 0.2',
      'LINE 2 105 100 105 0.2',
      'LINE 24 100 24 112 0.2',
      'LINE 50 100 50 112 0.2',
      'LINE 75 100 75 112 0.2',

      'T 0 0 3 102 DATA LEITURA ANTERIOR',
      'T 7 0 4 107 {DATA_LEITURA_ANT}',
      'T 0 0 26 102 DATA LEITURA ATUAL',
      'T 7 0 28 107 {DATA_LEITURA_ATU}',
      'T 7 0 52 102 VENCIMENTO',
      'T 7 0 54 107 {DATA_VENCIMENTO}',
      'T 7 0 76 102 VALOR A PAGAR',
      'T 7 0 76 107 R$ {VALOR_PAGAR}',

      'LINE 2 112 100 112 0.2',
      'LINE 18 112 18 119 0.2',
      'LINE 35 112 35 119 0.2',
      'LINE 55 112 55 119 0.2',
      'LINE 75 112 75 119 0.2',

      'T 0 0 3 113 LEIT. ANT.',
      'T 7 0 5 116 {LEIT_ANT}',
      'T 0 0 20 113 LEIT. ATUAL',
      'T 7 0 22 116 {LEIT_ATUAL}',
      'T 0 0 37 113 CONS. REAL',
      'T 7 0 39 116 {CONS_REAL}',
      'T 0 0 57 113 MEDIA',
      'T 7 0 62 116 {MEDIA}',

      // --- Hidrometro / Ocorrencia ---
      'LINE 2 119 100 119 0.2',
      'LINE 45 119 45 125 0.2',
      'LINE 2 125 100 125 0.2',
      'T 0 0 3 120 NR. HIDROMETRO',
      'T 7 0 3 122 {NR_HIDROMETRO}',
      'T 0 0 46 120 DIAS DE CONSUMO: 30',
      'T 7 0 3 126 OCORRENCIA: {OCORRENCIA}',

      // --- Ultimos 6 Meses ---
      'LINE 2 130 100 130 0.2',
      'LINE 45 130 45 155 0.2',
      'T 0 0 3 131 DADOS DOS ULTIMOS 6 MESES',
      'T 0 0 46 131 MENSAGEM',
      'T 7 0 3 134 MES     CONS',

      // --- Qualidade / Emissao ---
      'LINE 2 155 100 155 0.2',
      'T 0 0 3 156 PERIODO DA ANALISE: 24/08/2021 a',
      'LINE 2 160 100 160 0.2',
      'T 0 0 3 161 PARAMETRO         VMP         VALOR MEDIO DETECTADO',
      'T 0 0 5 164 CLORO        0,2 e 2,0           1,3',
      'T 0 0 5 167 COR             15               6,1',
      'T 0 0 5 170 FLUOR          1,5               1,5',
      'T 0 0 5 173 PH           6,0 e 9,5           7,89',

      'LINE 2 177 100 177 0.2',
      'LINE 2 181 100 181 0.2',
      'T 0 0 3 178 FAVOR AUTENTICAR NO VERSO - DEVOLVER AO USUARIO',
      'T 0 0 55 178 EMISSAO: {DATA_EMISSAO} {HORA_EMISSAO}',

      // --- CANHOTO ---
      'T 7 0 3 184 {NOME_COMPROMISSARIO}',
      'T 7 0 3 188 {ENDERECO_LOGRADOURO}',
      'T 7 0 3 191 {CEP}, {ENDERECO_BAIRRO}',
      'T 7 0 3 194 ROTA: {ROTA}-{SEQUENCIA}',
      'T 7 0 3 198 LIGACAO:{LIGACAO}       ID.ELETRO.:000',

      'LINE 62 181 62 202 0.2',
      'LINE 62 188 100 188 0.2',
      'LINE 62 195 100 195 0.2',
      'LINE 2 202 100 202 0.2',
      'LINE 40 202 40 210 0.2',
      'LINE 2 210 100 210 0.2',

      'T 7 0 63 183 MES/ANO:{REFERENCIA}',
      'T 7 0 63 190 NR. GUIA',
      'T 7 0 63 192 {NR_GUIA}',
      'T 7 0 63 197 CATEGORIA/QTDE 1-{CATEGORIA}',

      'T 7 0 8 204 VENCIMENTO',
      'T 7 0 10 207 {DATA_VENCIMENTO}',
      'T 7 0 55 204 VALOR A PAGAR',
      'T 7 0 58 207 R$ {VALOR_PAGAR}',

      'B I2OF5 0.245 25 8 0 212 {CODIGO_BARRAS}',
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
