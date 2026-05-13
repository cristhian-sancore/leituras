/**
 * SAEMI - Módulo de Impressão Zebra ZQ520/ZQ521 via Web Bluetooth (CPCL)
 */

const ZebraPrint = (() => {
  let device = null;
  let server = null;
  let printCharacteristic = null;
  let customLayout = null; 

  // UUIDs comuns da Zebra para impressão Bluetooth LE
  const ZEBRA_SERVICE = '38eb4a80-c570-11e3-9507-0002a5d5c51b';
  const ZEBRA_WRITE = '38eb4a82-c570-11e3-9507-0002a5d5c51b';

  async function connect() {
    if (!navigator.bluetooth) {
      throw new Error("Web Bluetooth não é suportado neste navegador. Use o Chrome no Android.");
    }

    try {
      device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: [ZEBRA_SERVICE, '000018f0-0000-1000-8000-00805f9b34fb']
      });

      server = await device.gatt.connect();
      
      try {
          const service = await server.getPrimaryService(ZEBRA_SERVICE);
          printCharacteristic = await service.getCharacteristic(ZEBRA_WRITE);
      } catch(e) {
          const service = await server.getPrimaryService('000018f0-0000-1000-8000-00805f9b34fb');
          printCharacteristic = await service.getCharacteristic('00002af1-0000-1000-8000-00805f9b34fb');
      }

      device.addEventListener('gattserverdisconnected', onDisconnected);
      return true;
    } catch (e) {
      console.error(e);
      throw new Error("Falha ao conectar: " + e.message);
    }
  }

  function onDisconnected() {
    device = null;
    server = null;
    printCharacteristic = null;
    const statusEl = document.getElementById('printer-status');
    if (statusEl) {
        statusEl.className = 'status-err';
        statusEl.textContent = '? Desconectado';
    }
  }

  function isConnected() {
    return printCharacteristic !== null;
  }

  async function sendData(dataStr) {
    if (!isConnected()) throw new Error("Impressora não conectada");
    
    const encoder = new TextEncoder();
    let data = encoder.encode(dataStr);
    
    // Escrever em chunks de 512 bytes (limite do BLE)
    const CHUNK_SIZE = 512;
    for (let i = 0; i < data.length; i += CHUNK_SIZE) {
        const chunk = data.slice(i, i + CHUNK_SIZE);
        await printCharacteristic.writeValue(chunk);
    }
    return true;
  }

  async function fetchLayout() {
      const token = localStorage.getItem('saemi_token');
      if (!token) return;
      try {
          const res = await fetch('/api/v1/empresa/layout', {
              headers: { 'Authorization': `Bearer ${token}` }
          });
          if (res.ok) {
              const data = await res.json();
              customLayout = data.conteudo_cpcl;
              console.log("Layout customizado carregado!");
          }
      } catch(e) {
          console.error("Erro ao buscar layout customizado", e);
      }
  }

  function gerarCPCL(dados) {
      let cpcl = customLayout;
      
      // Se não houver layout customizado, usa um layout genérico
      if (!cpcl) {
          cpcl = `! 0 200 200 800 1\r\nIN-MILLIMETERS\r\nCOUNTRY LATIN9\r\n` +
                 `T 7 0 10 20 SAEMI\r\n` +
                 `T 5 0 10 50 MATRICULA: {LIGACAO}\r\n` +
                 `T 5 0 10 80 NOME: {NOME_COMPROMISSARIO}\r\n` +
                 `T 5 0 10 110 TOTAL: R$ {VALOR_PAGAR}\r\n` +
                 `FORM\r\nPRINT\r\n`;
      }

      // Substituição de variáveis
      const map = {
          '{NOME_COMPROMISSARIO}': dados.nome || '',
          '{ENDERECO_INSTALACAO}': dados.endereco || '',
          '{CEP}': '',
          '{ROTA}': dados.rota || '',
          '{ENDERECO_ENTREGA}': dados.endereco || '',
          '{SEQUENCIA}': '',
          '{LIGACAO}': dados.matricula || '',
          '{REFERENCIA}': dados.mes_ref || '',
          '{NR_GUIA}': '',
          '{CATEGORIA}': dados.categoria || '',
          '{LANCAMENTO_DESC_1}': 'Agua',
          '{LANCAMENTO_VAL_1}': parseFloat(dados.valor_agua || 0).toFixed(2),
          '{LANCAMENTO_DESC_2}': 'Esgoto',
          '{LANCAMENTO_VAL_2}': parseFloat(dados.valor_esgoto || 0).toFixed(2),
          '{DATA_LEITURA_ANT}': dados.data_leitura || '',
          '{DATA_LEITURA_ATU}': dados.data_leitura || '',
          '{DATA_VENCIMENTO}': dados.vencimento || '',
          '{VALOR_PAGAR}': parseFloat(dados.valor_total || 0).toFixed(2),
          '{LEIT_ANT}': dados.leit_anterior || '',
          '{LEIT_ATUAL}': dados.leit_atual || '',
          '{CONS_REAL}': dados.consumo || '',
          '{CONS_FATURADO}': dados.consumo || '',
          '{MEDIA}': Math.round(parseFloat(dados.consumo || 0)/6),
          '{NR_HIDROMETRO}': '',
          '{VAZAO}': '',
          '{DIAMETRO}': '',
          '{DATA_INSTALACAO}': '',
          '{OCORRENCIA}': dados.ocorrencia || '',
          '{CODIGO_BARRAS}': dados.matricula || '000000',
          '{DATA_EMISSAO}': new Date().toLocaleDateString('pt-BR')
      };

      for (const [key, value] of Object.entries(map)) {
          cpcl = cpcl.split(key).join(value);
      }

      return cpcl;
  }

  async function imprimirConta(dados) {
      const cpcl = gerarCPCL(dados);
      await sendData(cpcl);
      return cpcl;
  }

  return { connect, isConnected, sendData, imprimirConta, fetchLayout };
})();
