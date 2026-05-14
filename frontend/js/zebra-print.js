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
  function removerAcentos(str) {
    if(!str) return '';
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  function formatarValor(val) {
    return parseFloat(val || 0).toFixed(2).replace('.', ',');
  }

  function formatData(data) {
    if (!data) return '';
    if (data.indexOf('-') > 0) {
      let p = data.split('-');
      if (p.length === 3) return p[2] + '/' + p[1] + '/' + p[0];
    }
    return data;
  }

  function layoutGenerico(dados) {
    let sb = '';
    const add = (str) => { sb += str + '\r\n'; };
    
    // Header
    add('! 0 200 200 230 1');
    add('JOURNAL');
    add('IN-MILLIMETERS');
    add('COUNTRY LATIN9');

    // Box 1 lines
    add('LINE 2 15 100 15 0.2');
    add('LINE 2 15 2 174 0.2');
    add('LINE 100 15 100 174 0.2');
    add('LINE 2 174 100 174 0.2');
    
    add('LINE 76 15 76 39 0.2');
    add('LINE 76 22 100 22 0.2');
    add('LINE 76 30 100 30 0.2');
    add('LINE 76 34 100 34 0.2');
    add('LINE 2 39 100 39 0.2');
    add('LINE 2 44 100 44 0.2');

    let nomeCompromissario = removerAcentos(dados.nome || '');
    let enderecoInst = removerAcentos(dados.endereco || '') + ', ' + (dados.numero || '') + ', ' + removerAcentos(dados.bairro || '');
    let cep = dados.cep || ' ';
    let rota = dados.rota || '';
    let enderecoEntrega = removerAcentos(dados.endereco || '') + ', ' + (dados.numero || '') + ', ' + removerAcentos(dados.bairro || '');
    let sequencia = (dados.setor || ' ') + ' - ' + (dados.quadra || ' ') + ' - ' + (dados.lote || '  ');
    let instalacao = dados.matricula || '';

    add('T 7 0 3 16 ' + nomeCompromissario);
    add('T 7 0 3 19 ' + enderecoInst);
    add('T 7 0 3 22 CEP: ' + cep + ', Rota: ' + rota);
    add('T 7 0 3 25 END. ENT: ' + enderecoEntrega);
    add('T 7 0 3 28 Sequencia anterior: ' + sequencia);
    add('T 7 0 3 31 LIGACAO: ' + instalacao);

    add('T 7 2 78 15 MES/ANO: ' + (dados.referencia || ''));
    add('T 7 0 78 23 NR. GUIA ');
    add('T 7 0 78 26 ' + (dados.nosso_numero || ''));
    add('T 7 0 78 31 CATEGORIA/QTDE ');
    add('T 7 0 82 35 ' + (dados.categoria || ''));

    add('T 7 0 30 40 DESCRICAO ');
    add('T 7 0 89 40 VALOR ');

    let y5 = 45;
    if (parseFloat(dados.valor_agua || 0) > 0) {
       add('T 7 0 5 ' + y5 + ' AGUA');
       add('T 7 0 87 ' + y5 + '  ' + formatarValor(dados.valor_agua));
       y5 += 3;
    }
    if (parseFloat(dados.valor_esgoto || 0) > 0) {
       add('T 7 0 5 ' + y5 + ' ESGOTO');
       add('T 7 0 87 ' + y5 + '  ' + formatarValor(dados.valor_esgoto));
       y5 += 3;
    }
    if (parseFloat(dados.valor_lixo || 0) > 0) {
       add('T 7 0 5 ' + y5 + '  TAXA DE LIXO');
       add('T 7 0 87 ' + y5 + '  ' + formatarValor(dados.valor_lixo));
       y5 += 3;
    }

    add('LINE 2 80 100 80 0.2');
    add('LINE 28 80 28 89 0.2');
    add('LINE 50 80 50 89 0.2');
    add('LINE 78 80 78 89 0.2');
    add('LINE 2 89 100 89 0.2');

    add('T 0 2 4 80 DATA LEITURA ANTERIOR ');
    add('T 7 2 5 83 ' + formatData(dados.leitura_anterior_data || dados.data_leitura_ant));
    add('T 0 2 30 80 DATA LEITURA ATUAL ');
    add('T 7 2 30 83 ' + formatData(dados.leitura_atual_data || dados.data_leitura));
    add('T 0 2 60 80 VENCIMENTO ');
    add('T 7 2 56 83 ' + formatData(dados.vencimento));
    add('T 0 2 80 80 VALOR A PAGAR');
    add('T 7 2 82 83 R$ ' + formatarValor(dados.valor_total));

    add('LINE 25 89 25 97 0.2');
    add('LINE 44 89 44 97 0.2');
    add('LINE 60 89 60 97 0.2');
    add('LINE 78 89 78 97 0.2');
    add('LINE 2 97 100 97 0.2');
    add('LINE 2 105 100 105 0.2');

    add('T 0 2 7 89 LEITURA ANTERIOR ');
    add('T 0 2 28 89 LEITURA ATUAL ');
    add('T 0 2 45 89 CONSUMO REAL ');
    add('T 0 2 61 89 CONS. FATURADO ');
    add('T 0 2 86 89 MEDIA ');

    add('T 5 0 9 93 ' + (dados.leit_anterior || ' '));
    add('T 5 0 30 93 ' + (dados.leit_atual || ' '));
    add('T 5 0 50 93 ' + (dados.consumo || ' '));
    add('T 5 0 66 93 ' + (dados.consumo || ' '));
    add('T 5 0 87 93 ' + Math.round(parseFloat(dados.consumo||0)/6));

    add('LINE 44 97 44 105 0.2');
    add('LINE 60 97 60 105 0.2');
    add('LINE 78 97 78 105 0.2');

    add('T 0 2 15 97 NR. DO HIDROMETRO ');
    add('T 0 2 50 97 VAZAO ');
    add('T 0 2 64 97 DIAMETRO ');
    add('T 0 2 80 97 DATA DE INSTALACAO ');

    add('T 5 0 15 101 ' + (dados.hidrometro || ' '));
    add('T 5 0 50 101  ');
    add('T 5 0 66 101  ');
    add('T 5 0 82 101  ');

    add('LINE 2 110 100 110 0.2');
    add('T 7 0 4 107 OCORRENCIA: ' + (dados.ocorrencia || '0000'));

    add('LINE 44 110 44 144 0.2');
    add('T 0 2 4 110 DADOS DOS ULTIMOS 6 MESES ');
    add('LINE 2 114 44 114 0.2');

    add('T 0 2 4 114 MES ');
    add('T 0 2 18 114 CONSUMO ');
    add('T 0 2 31 114 DIAS ');
    add('T 0 2 38 114 MEDIA ');

    let yh = 118;
    if(dados.historico && dados.historico.length > 0) {
      dados.historico.forEach(h => {
        add('T 7 0 4 ' + yh + ' ' + (h.mes||''));
        add('T 7 0 20 ' + yh + ' ' + (h.consumo||''));
        add('T 7 0 31 ' + yh + ' ' + (h.dias||''));
        add('T 7 0 38 ' + yh + '  ' + (h.media||'0'));
        yh += 3;
      });
    }

    add('T 0 2 45 110 MENSAGEM');
    add('LINE 2 144 100 144 0.2');
    add('T 0 2 10 144 DETALHES SOBRE ');
    add('T 0 2 8 147 LEGISLACAO VIDE VERSO');
    add('LINE 35 144 35 151 0.2');

    add('T 0 2 42 145 PERIODO DA ANALISE: 24/08/2021 a ');
    add('LINE 2 151 100 151 0.2');

    add('T 0 2 10 152 PARAMETRO ');
    add('T 0 2 28 152 UNIDADE ');
    add('T 0 2 47 152 VMP ');
    add('T 0 2 60 151 TOTAL DE ANALISES ');
    add('T 0 2 64 154 REALIZADAS ');
    add('T 0 2 87 151 VALOR MEDIO ');
    add('T 0 2 87 154 DETECTADO ');

    add('T 7 0 8 158 Cloro ');
    add('T 7 0 28 158 mg/L ');
    add('T 7 0 40 158 0,2 a 2 ');
    add('T 7 0 65 158 1 ');
    add('T 7 0 85 158 1,3 ');

    add('LINE 2 157 100 157 0.2');

    const dtEmissao = new Date().toLocaleDateString("pt-BR");
    const hrEmissao = new Date().getHours().toString().padStart(2, "0") + ":" + new Date().getMinutes().toString().padStart(2, "0");

    add('T 0 2 3 180 FAVOR AUTENTICAR NO VERSO - DEVOLVER AO USUARIO');
    add('T 0 2 76 180 EMISSAO: ' + dtEmissao + ' ' + hrEmissao);

    // Canhoto
    add('LINE 2 174 100 174 0.2');
    add('LINE 2 174 2 206 0.2');
    add('LINE 100 174 100 206 0.2');
    add('LINE 2 199 100 199 0.2');

    add('T 7 0 3 184 ' + nomeCompromissario);
    add('T 7 0 3 187 ' + enderecoInst);
    add('T 7 0 3 190 CEP: ' + cep + ', Rota: ' + rota);
    add('T 7 0 3 193 END. ENT: ' + enderecoEntrega);
    add('T 7 0 3 196 Sequencia anterior: ' + sequencia);
    add('T 7 0 78 184 MES/ANO: ' + (dados.referencia || ''));

    add('LINE 76 187 100 187 0.2');
    add('T 7 0 78 187.5 NR. GUIA ');
    add('T 7 0 78 190 ' + (dados.nosso_numero || ''));
    add('LINE 76 193 100 193 0.2');
    add('T 7 0 78 193 CATEGORIA/QTDE ');
    add('T 7 0 82 196 ' + (dados.categoria || ''));

    add('T 7 0 12 200 LIGACAO ');
    add('T 7 0 12 203 ' + instalacao);
    add('LINE 35 199 35 206 0.2');
    add('T 7 0 47 200 VENCIMENTO ');
    add('T 7 0 47 203 ' + formatData(dados.vencimento));
    add('T 7 0 80 200 VALOR A PAGAR ');
    add('T 7 0 82 203 R$ ' + formatarValor(dados.valor_total));
    add('LINE 76 174 76 206 0.2');
    add('LINE 2 206 100 206 0.2');

    add('CENTER');
    let codStr = (dados.matricula || "000000").replace(/\D/g, "");
    if (codStr.length % 2 !== 0) codStr = "0" + codStr;
    add('T 5 0 0 208 ' + codStr);
    add('B I2OF5 0.245 25 8 0 212 ' + codStr);
    add('FORM');
    add('PRINT');

    return sb;
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
