/**
 * SAEMI - Módulo de Impressão Zebra ZQ520/ZQ521 via Web Bluetooth (CPCL)
 */

const ZebraPrint = (() => {
  let device = null;
  let server = null;
  let printCharacteristic = null;
  let customLayout = null;
  let customLayoutNotif = null;

  // UUIDs Zebra BLE (SPP Serial Port Profile fallback)
  const ZEBRA_SERVICE = '38eb4a80-c570-11e3-9507-0002a5d5c51b';
  const ZEBRA_WRITE   = '38eb4a82-c570-11e3-9507-0002a5d5c51b';
  const SPP_SERVICE   = '000018f0-0000-1000-8000-00805f9b34fb';
  const SPP_WRITE     = '00002af1-0000-1000-8000-00805f9b34fb';

  // ── Conexão Bluetooth ──────────────────────────────────
  async function connect() {
    if (!navigator.bluetooth) {
      throw new Error('Web Bluetooth nao e suportado. Use Chrome no Android.');
    }
    try {
      device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: [ZEBRA_SERVICE, SPP_SERVICE]
      });

      server = await device.gatt.connect();

      // Tenta serviço Zebra nativo primeiro, cai para SPP
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
    device = null;
    server = null;
    printCharacteristic = null;
    const statusEl = document.getElementById('printer-status');
    if (statusEl) {
      statusEl.className = 'status-err';
      statusEl.textContent = 'Desconectado';
    }
    const btnImpr = document.getElementById('btn-imprimir');
    if (btnImpr) btnImpr.disabled = true;
  }

  function isConnected() {
    return printCharacteristic !== null;
  }

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

  // ── Busca layout customizado da API ───────────────────
  async function fetchLayout() {
    const token = localStorage.getItem('saemi_token');
    if (!token) return; // sem token, usa layout generico
    try {
      const res = await fetch('/api/v1/empresa/layout', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      if (res.ok) {
        const data = await res.json();
        customLayout = data.conteudo_cpcl || null;
        customLayoutNotif = data.conteudo_cpcl_notificacao || null;
        console.log('[ZebraPrint] Layout carregado:', !!customLayout, '| Notif:', !!customLayoutNotif);
      }
    } catch (e) {
      console.warn('[ZebraPrint] Falha ao buscar layout, usando generico.', e);
    }
  }

  // ── Tabela de substituição de variáveis ───────────────
  function buildMap(dados) {
    return {
      '{NOME_COMPROMISSARIO}': dados.nome || '',
      '{ENDERECO_INSTALACAO}': dados.endereco || '',
      '{ENDERECO_ENTREGA}':    dados.endereco || '',
      '{CEP}':                 '',
      '{ROTA}':                dados.rota || '',
      '{SEQUENCIA}':           '',
      '{LIGACAO}':             dados.matricula || '',
      '{REFERENCIA}':          dados.mes_ref || '',
      '{NR_GUIA}':             '',
      '{CATEGORIA}':           dados.categoria || '',
      '{LANCAMENTO_DESC_1}':   'Agua',
      '{LANCAMENTO_VAL_1}':    parseFloat(dados.valor_agua  || 0).toFixed(2),
      '{LANCAMENTO_DESC_2}':   'Esgoto',
      '{LANCAMENTO_VAL_2}':    parseFloat(dados.valor_esgoto || 0).toFixed(2),
      '{LANCAMENTO_DESC_3}':   'Taxa Lixo',
      '{LANCAMENTO_VAL_3}':    parseFloat(dados.valor_lixo  || 0).toFixed(2),
      '{DATA_LEITURA_ANT}':    dados.data_leitura || '',
      '{DATA_LEITURA_ATU}':    dados.data_leitura || '',
      '{DATA_VENCIMENTO}':     dados.vencimento || '',
      '{VALOR_PAGAR}':         parseFloat(dados.valor_total || 0).toFixed(2),
      '{LEIT_ANT}':            String(dados.leit_anterior || 0),
      '{LEIT_ATUAL}':          String(dados.leit_atual || 0),
      '{CONS_REAL}':           String(dados.consumo || 0),
      '{CONS_FATURADO}':       String(dados.consumo || 0),
      '{MEDIA}':               String(Math.round(parseFloat(dados.consumo || 0) / 6)),
      '{NR_HIDROMETRO}':       '',
      '{VAZAO}':               '',
      '{DIAMETRO}':            '',
      '{DATA_INSTALACAO}':     '',
      '{OCORRENCIA}':          dados.ocorrencia || '',
      '{CODIGO_BARRAS}':       dados.matricula || '000000',
      '{DATA_EMISSAO}':        new Date().toLocaleDateString('pt-BR'),
    };
  }

  function aplicarVariaveis(cpcl, map) {
    for (const [key, val] of Object.entries(map)) {
      cpcl = cpcl.split(key).join(val);
    }
    return cpcl;
  }

  // ── Layout genérico (fallback sem customização) ────────
  function layoutGenerico(dados) {
    const v = (n) => parseFloat(n || 0).toFixed(2);
    return [
      '! 0 200 200 800 1',
      'IN-MILLIMETERS',
      'COUNTRY LATIN9',
      'T 7 0 10 10 ' + (dados.empresa_nome || 'SAEMI'),
      'LINE 5 18 99 18 1',
      'T 5 0 5 22 MATRICULA: ' + (dados.matricula || ''),
      'T 5 0 5 30 NOME: ' + (dados.nome || ''),
      'T 5 0 5 38 REFERENCIA: ' + (dados.mes_ref || ''),
      'T 5 0 5 46 VENCIMENTO: ' + (dados.vencimento || ''),
      'LINE 5 52 99 52 1',
      'T 5 0 5 56 LEITURA ANTERIOR: ' + (dados.leit_anterior || 0),
      'T 5 0 5 63 LEITURA ATUAL: ' + (dados.leit_atual || 0),
      'T 7 0 5 71 CONSUMO: ' + (dados.consumo || 0) + ' m3',
      'LINE 5 78 99 78 1',
      'T 5 0 5 82 AGUA: R$ ' + v(dados.valor_agua),
      'T 5 0 5 89 ESGOTO: R$ ' + v(dados.valor_esgoto),
      (parseFloat(dados.valor_lixo || 0) > 0 ? 'T 5 0 5 96 TAXA LIXO: R$ ' + v(dados.valor_lixo) : ''),
      'LINE 5 104 99 104 1',
      'T 7 0 5 109 TOTAL A PAGAR: R$ ' + v(dados.valor_total),
      'LINE 5 118 99 118 1',
      'T 5 0 5 122 OCORRENCIA: ' + (dados.ocorrencia || ''),
      'T 5 0 5 130 LEITURISTA: ' + (dados.leiturista || ''),
      'LINE 5 137 99 137 1',
      'B QR 2 1 5 145 ' + (dados.matricula || '000'),
      'FORM',
      'PRINT',
    ].filter(Boolean).join('\r\n');
  }

  // ── Gerar CPCL da fatura ───────────────────────────────
  function gerarCPCL(dados) {
    const raw = customLayout || layoutGenerico(dados);
    return aplicarVariaveis(raw, buildMap(dados));
  }

  // ── Gerar CPCL da notificação ─────────────────────────
  function gerarCPCLNotificacao(dados) {
    if (!customLayoutNotif) return null;
    const map = {
      '{NOME_COMPROMISSARIO}': dados.nome || '',
      '{ENDERECO_INSTALACAO}': dados.endereco || '',
      '{LIGACAO}':             dados.matricula || '',
      '{MENSAGEM_DEBITO}':     dados.mensagem_notificacao || 'CONSTAM DEBITOS EM ABERTO. SUJEITO A CORTE.',
      '{MENSAGEM_CONTAS_ABERTO}': dados.mensagem_notificacao || 'CONSTAM DEBITOS EM ABERTO. SUJEITO A CORTE.',
      '{DATA_EMISSAO}':        new Date().toLocaleDateString('pt-BR'),
    };
    return aplicarVariaveis(customLayoutNotif, map);
  }

  // ── Imprimir conta (fatura + notificação se houver) ───
  async function imprimirConta(dados) {
    const cpclFatura = gerarCPCL(dados);
    await sendData(cpclFatura);

    const cpclNotif = gerarCPCLNotificacao(dados);
    if (cpclNotif && dados.tem_notificacao) {
      await new Promise(r => setTimeout(r, 1200)); // aguarda buffer BLE
      await sendData(cpclNotif);
    }
    return cpclFatura;
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
