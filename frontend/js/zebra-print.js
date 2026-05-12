/**
 * SAEMI - Módulo de Impressão Zebra ZQ521e
 * Comunicação via Zebra Browser Print (agent local na porta 9090)
 * Papel: 80mm (2.36") | 203dpi | largura útil ~560 dots
 */

const ZebraPrint = (() => {

    const BROWSER_PRINT_URL = 'http://localhost:9090';
    let selectedDevice = null;

    // ──────────────────────────────────────────
    // DESCOBERTA DE IMPRESSORAS
    // ──────────────────────────────────────────
    async function getDevices() {
        try {
            const resp = await fetch(`${BROWSER_PRINT_URL}/available`, {
                method: 'GET',
                headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
            });
            if (!resp.ok) throw new Error('Browser Print nao respondeu');
            const data = await resp.json();
            return data.printer || [];
        } catch (e) {
            throw new Error(
                'Zebra Browser Print nao encontrado. Instale o agente em: https://www.zebra.com/us/en/support-downloads/printer-software/browser-print.html'
            );
        }
    }

    async function getDefaultDevice() {
        try {
            const resp = await fetch(`${BROWSER_PRINT_URL}/default?type=printer`);
            if (!resp.ok) throw new Error('Sem impressora padrao');
            return await resp.json();
        } catch (e) {
            return null;
        }
    }

    // ──────────────────────────────────────────
    // ENVIAR ZPL PARA A IMPRESSORA
    // ──────────────────────────────────────────
    async function sendZPL(zpl, device) {
        const dev = device || selectedDevice;
        if (!dev) throw new Error('Nenhuma impressora selecionada');

        const resp = await fetch(`${BROWSER_PRINT_URL}/write`, {
            method: 'POST',
            headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
            body: JSON.stringify({ device: dev, data: zpl }),
        });

        if (!resp.ok) throw new Error('Falha ao enviar para impressora');
        return true;
    }

    // ──────────────────────────────────────────
    // TEMPLATE ZPL — CONTA DE ÁGUA (80mm)
    // ZQ521e 203dpi — largura: 560 dots
    // ──────────────────────────────────────────
    function gerarZPL(dados) {
        const {
            empresa_nome = 'SAEMI',
            empresa_cnpj = '',
            mes_ref = '',
            data_leitura = '',
            vencimento = '',
            matricula = '',
            nome = '',
            endereco = '',
            bairro = '',
            rota = '',
            setor = '',
            leit_anterior = 0,
            leit_atual = 0,
            consumo = 0,
            ocorrencia = '',
            valor_agua = 0,
            valor_esgoto = 0,
            valor_lixo = 0,
            valor_total = 0,
            categoria = '',
            leiturista = '',
        } = dados;

        const fmtR$ = (v) => 'R$ ' + parseFloat(v || 0).toFixed(2).replace('.', ',');
        const truncate = (s, n) => String(s || '').substring(0, n);
        const pad = (s, n) => String(s || '').padEnd(n).substring(0, n);

        return `
^XA
^CI28
^PW560
^LL0
^LH0,0

^FO10,10^A0N,28,28^FB540,1,,C^FD${truncate(empresa_nome, 30)}^FS
^FO10,42^A0N,18,18^FB540,1,,C^FD${empresa_cnpj ? 'CNPJ: ' + empresa_cnpj : ''}^FS
^FO10,65^A0N,22,22^FB540,1,,C^FDCONTA DE AGUA - REF: ${truncate(mes_ref, 10)}^FS

^FO10,95^GB540,2,2^FS

^FO10,105^A0N,20,20^FDMatricula:^FS ^FO160,105^A0N,20,20^FD${truncate(matricula, 15)}^FS
^FO10,130^A0N,18,18^FDCliente:^FS ^FO110,130^A0N,18,18^FD${truncate(nome, 28)}^FS
^FO10,153^A0N,16,16^FDEndereco:^FS ^FO120,153^A0N,16,16^FD${truncate(endereco, 32)}^FS
^FO10,173^A0N,16,16^FD${truncate(bairro, 30)}^FS
^FO10,193^A0N,16,16^FDRota:^FS ^FO70,193^A0N,16,16^FD${truncate(rota, 8)}^FS ^FO200,193^A0N,16,16^FDSetor:^FS ^FO270,193^A0N,16,16^FD${truncate(setor, 10)}^FS
^FO10,213^A0N,16,16^FDCategoria:^FS ^FO130,213^A0N,16,16^FD${truncate(categoria, 20)}^FS

^FO10,235^GB540,2,2^FS

^FO10,245^A0N,18,18^FDLEITURAS^FS
^FO10,268^A0N,16,16^FDAnterior:^FS ^FO130,268^A0N,20,20^FD${leit_anterior}^FS
^FO300,268^A0N,16,16^FDData Ant.:^FS ^FO430,268^A0N,16,16^FD${truncate(data_leitura, 10)}^FS
^FO10,292^A0N,16,16^FDAtual:^FS ^FO130,292^A0N,20,20^FD${leit_atual}^FS
^FO300,292^A0N,16,16^FDData Atu.:^FS ^FO430,292^A0N,16,16^FD${truncate(data_leitura, 10)}^FS
^FO10,316^A0N,16,16^FDConsumo:^FS ^FO130,316^A0N,24,24^FD${consumo} m3^FS
${ocorrencia ? `^FO300,316^A0N,14,14^FDOcorr: ${truncate(ocorrencia, 12)}^FS` : ''}

^FO10,345^GB540,2,2^FS

^FO10,355^A0N,18,18^FDVALORES^FS
^FO10,378^A0N,16,16^FDAgua:^FS ^FO400,378^A0N,16,16^FB140,1,,R^FD${fmtR$(valor_agua)}^FS
^FO10,400^A0N,16,16^FDEsgoto:^FS ^FO400,400^A0N,16,16^FB140,1,,R^FD${fmtR$(valor_esgoto)}^FS
${valor_lixo > 0 ? `^FO10,422^A0N,16,16^FDLixo:^FS ^FO400,422^A0N,16,16^FB140,1,,R^FD${fmtR$(valor_lixo)}^FS` : ''}

^FO10,${valor_lixo > 0 ? 448 : 428}^GB540,3,3^FS
^FO10,${valor_lixo > 0 ? 455 : 435}^A0N,26,26^FDTOTAL A PAGAR:^FS
^FO300,${valor_lixo > 0 ? 452 : 432}^A0N,28,28^FB240,1,,R^FD${fmtR$(valor_total)}^FS

^FO10,${valor_lixo > 0 ? 490 : 470}^GB540,2,2^FS

${vencimento ? `^FO10,${valor_lixo > 0 ? 500 : 480}^A0N,18,18^FDVencimento:^FS ^FO155,${valor_lixo > 0 ? 500 : 480}^A0N,20,20^FD${truncate(vencimento, 12)}^FS` : ''}

^FO10,${valor_lixo > 0 ? 530 : 510}^A0N,14,14^FB540,1,,C^FDLeiturista: ${truncate(leiturista, 25)}^FS
^FO10,${valor_lixo > 0 ? 548 : 528}^A0N,14,14^FB540,1,,C^FDSistema SAEMI - Leitura Digital^FS

^FO10,${valor_lixo > 0 ? 565 : 545}^GB540,2,2^FS

^BY2,3,60
^FO10,${valor_lixo > 0 ? 575 : 555}^BCN,60,Y,N,N^FD${truncate(matricula, 20)}^FS

^XZ`.trim();
    }

    // ──────────────────────────────────────────
    // IMPRIMIR UMA CONTA
    // ──────────────────────────────────────────
    async function imprimirConta(dados, device) {
        const zpl = gerarZPL(dados);
        await sendZPL(zpl, device);
        return zpl;
    }

    // ──────────────────────────────────────────
    // INICIALIZAR — buscar impressora padrão
    // ──────────────────────────────────────────
    async function init() {
        const dev = await getDefaultDevice();
        if (dev) selectedDevice = dev;
        return dev;
    }

    return { init, getDevices, sendZPL, imprimirConta, gerarZPL };

})();
