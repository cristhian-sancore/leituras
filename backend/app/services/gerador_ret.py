"""
Gerador de arquivo .RET (retorno) no formato D01.
Compatível com o SIA (Sistema Integrado de Abastecimento).
"""
from datetime import datetime
from typing import List


def fmt92(v: float) -> str:
    """Formato Numérico (9.2) = 12 chars: 000000085.10"""
    parts = f"{v:.2f}".split('.')
    return parts[0].zfill(9) + '.' + parts[1]


def gerar_linha_d01(
    cliente: dict,
    leitura: dict,
    data_coleta: str,
    hora_coleta: str,
    codigo_normal: str = '0000',
) -> str:
    """
    Gera uma linha D01 do arquivo .RET.
    
    Args:
        cliente: dict com dados do cliente (codigo_full, zona, rota, sequencia, etc.)
        leitura: dict com dados da leitura (leitura_atual, consumo, valores, ocorrencia_codigo)
        data_coleta: string DD/MM/YYYY
        hora_coleta: string HH:MM:SS
        codigo_normal: string representando o código da ocorrência normal
    
    Returns:
        String com a linha D01 formatada
    """
    leitura_atual = leitura.get('leitura_atual', 0) or 0
    consumo = leitura.get('consumo', 0) or 0
    valor_agua = leitura.get('valor_agua', 0) or 0
    valor_esgoto = leitura.get('valor_esgoto', 0) or 0
    valor_total = leitura.get('valor_total', 0) or 0
    ocorrencia = leitura.get('ocorrencia_codigo', '') or codigo_normal
    if ocorrencia == '0000':
        ocorrencia = codigo_normal
    consumo_faturado = max(consumo, 10)

    l = ''
    l += 'D01'                                                          # 01: pos 1, tam 3
    l += (cliente.get('codigo_full', '') or '').ljust(15)               # 02: pos 4, tam 15
    l += 'S'                                                            # 03: pos 19, tam 1
    l += str(leitura_atual).zfill(8)                                   # 04: pos 20, tam 8
    l += data_coleta                                                    # 05: pos 28, tam 10
    l += hora_coleta                                                    # 06: pos 38, tam 8
    l += ocorrencia.zfill(4)[:4]                                       # 07: pos 46, tam 4
    l += '0000'                                                         # 08: pos 50, tam 4
    l += '0000'                                                         # 09: pos 54, tam 4
    l += 'N'                                                            # 10: pos 58, tam 1
    l += fmt92(0)                                                       # 11: pos 59, tam 12
    l += fmt92(valor_agua)                                              # 12: pos 71, tam 12
    l += fmt92(0)                                                       # 13: pos 83, tam 12
    l += fmt92(valor_esgoto)                                            # 14: pos 95, tam 12
    l += fmt92(0)                                                       # 15: pos 107, tam 12
    l += fmt92(0)                                                       # 16: pos 119, tam 12
    l += fmt92(valor_total)                                             # 17: pos 131, tam 12
    l += str(consumo).zfill(5)                                         # 18: pos 143, tam 5
    l += str(consumo_faturado).zfill(5)                                # 19: pos 148, tam 5
    l += str(leitura_atual).zfill(8)                                   # 20: pos 153, tam 8
    l += 'NNNN'                                                         # 21-24: pos 161, tam 4
    l += (cliente.get('mes_ano_ref', '') or '').ljust(7)[:7]           # 25: pos 165, tam 7
    l += (cliente.get('num_fatura', '') or '').ljust(20)[:20]          # 26: pos 172, tam 20
    l += ' ' * 30                                                       # 27: pos 192, tam 30
    l += 'N'                                                            # 28: pos 222, tam 1
    l += (cliente.get('data_vencimento', '') or '').ljust(10)[:10]     # 29: pos 223, tam 10
    l += '000000000'                                                    # 30: pos 233, tam 9
    l += '000000000'                                                    # 31: pos 242, tam 9
    l += '02'                                                           # 32: pos 251, tam 2
    l += ' ' * 50                                                       # 33: pos 253, tam 50
    l += 'S'                                                            # 34: pos 303, tam 1
    l += '0002'                                                         # 35: pos 304, tam 4
    l += ' ' * 30                                                       # 36: pos 308, tam 30
    l += 'N'                                                            # 37: pos 338, tam 1
    l += ' ' * 4                                                        # 38: pos 339, tam 4
    l += ' ' * 19                                                       # 39: pos 343, tam 19
    l += (cliente.get('zona', '') or '   ')[:3]                        # 40: pos 362, tam 3
    l += '   '                                                          # 41: pos 365, tam 3
    l += (cliente.get('rota', '') or '    ')[:4]                       # 42: pos 368, tam 4
    l += (cliente.get('sequencia', '') or '000000').zfill(6)[:6]       # 43: pos 372, tam 6
    l += '  '                                                           # 44: pos 378, tam 2
    l += '2         '                                                   # 45: pos 380, tam 10
    l += 'N'                                                            # 46: pos 390, tam 1
    l += 'N'                                                            # 47: pos 391, tam 1

    # Campos 48+ do arquivo de referência
    leit_pad = str(leitura_atual).zfill(8)
    l += 'NNN'                                                          # pos 392-394
    l += '00000000.000000000000000000.00000000000000000000000'          # pos 395-445
    l += ' ' * 50                                                       # pos 446-495
    l += '000000000000'                                                 # pos 496-507
    l += data_coleta                                                    # pos 508-517
    l += leit_pad                                                       # pos 518-525
    l += ' ' * 70                                                       # pos 526-595
    l += '00000N'                                                       # pos 596-601
    l += ' ' * 60                                                       # pos 602-661

    return l


def gerar_arquivo_ret(
    clientes_leituras: List[dict],
    codigo_normal: str = '0000',
) -> str:
    """
    Gera o conteúdo completo do arquivo .RET.
    
    Args:
        clientes_leituras: lista de dicts, cada um com 'cliente' e 'leitura'
        codigo_normal: código correspondente à ocorrência normal da remessa
    
    Returns:
        Conteúdo do arquivo .RET como string
    """
    agora = datetime.now()
    data_coleta = agora.strftime('%d/%m/%Y')
    hora_coleta = agora.strftime('%H:%M:%S')

    lines = []
    for item in clientes_leituras:
        cliente = item['cliente']
        leitura = item['leitura']
        ocorrencia = leitura.get('ocorrencia_codigo', '') or codigo_normal
        if ocorrencia == '0000':
            ocorrencia = codigo_normal
        tem_leitura = leitura.get('leitura_atual') is not None
        tem_ocorrencia_especial = ocorrencia and ocorrencia != codigo_normal

        # Incluir no .RET se:
        # 1. Tem leitura numérica digitada, OU
        # 2. Tem ocorrência especial registrada (impedimento, hidrômetro com problema, etc.)
        if tem_leitura or tem_ocorrencia_especial:
            line = gerar_linha_d01(cliente, leitura, data_coleta, hora_coleta, codigo_normal=codigo_normal)
            lines.append(line)

    return '\r\n'.join(lines)
