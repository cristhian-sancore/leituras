"""
Motor de cálculo tarifário SAEMI.
Calcula valores de água, esgoto e lixo por faixas progressivas.
"""
from typing import List, Optional


def calcular_por_faixas(consumo: int, faixas: List[dict], consumo_minimo: int = 10) -> float:
    """
    Calcula o valor total por faixas progressivas.

    Args:
        consumo: consumo em m³
        faixas: lista de dicts com keys: valor_minimo, limite_metros, preco_metro
        consumo_minimo: m³ incluídos na taxa mínima (padrão 10, configurável por empresa)

    Returns:
        Valor total em reais
    """
    if not faixas:
        return 0.0

    # Separar faixa mínima das excedentes
    faixa_min = None
    faixas_exc = []
    for f in faixas:
        if f.get('valor_minimo') is not None and f.get('preco_metro') is None:
            faixa_min = f
        else:
            faixas_exc.append(f)

    # Valor base (taxa mínima)
    total = float(faixa_min['valor_minimo']) if faixa_min else 0.0

    # Excedente acima do consumo mínimo
    if consumo > consumo_minimo:
        excedente = consumo - consumo_minimo
        # Garantir ordenação correta por limite_metros (ascendente)
        # para que o cálculo progressivo funcione independente da ordem do banco
        faixas_exc_ord = sorted(faixas_exc, key=lambda f: float(f.get('limite_metros', 0) or 0))
        for i, faixa in enumerate(faixas_exc_ord):
            preco = float(faixa.get('preco_metro', 0) or 0)
            limite_atual = float(faixa.get('limite_metros', 0) or 0)
            if i + 1 < len(faixas_exc_ord):
                prox_limite = float(faixas_exc_ord[i + 1].get('limite_metros', 999999) or 999999)
            else:
                prox_limite = 999999
            tamanho_faixa = prox_limite - limite_atual
            consumo_na_faixa = min(excedente, tamanho_faixa)
            total += consumo_na_faixa * preco
            excedente -= consumo_na_faixa
            if excedente <= 0:
                break

    return round(total, 2)


def calcular_consumo(
    leitura_atual: int,
    leitura_anterior: int,
    ocorrencia: Optional[dict] = None,
    consumo_medio: int = 0,
    consumo_minimo: int = 10,
) -> int:
    """
    Calcula o consumo considerando virada de hidrômetro e ocorrências especiais.

    Args:
        leitura_atual: leitura do hidrômetro atual
        leitura_anterior: leitura anterior
        ocorrencia: dict com tipo_acao, consumo_fixo, desconsidera_leitura
        consumo_medio: média histórica de consumo
        consumo_minimo: m³ mínimo da empresa

    Returns:
        Consumo em m³
    """
    # Detectar virada de hidrômetro (99999 → 00012)
    if leitura_atual < leitura_anterior:
        # Determinar capacidade do hidrômetro (5, 6, 7 ou 8 dígitos)
        digitos = len(str(leitura_anterior))
        capacidade = 10 ** digitos  # ex: 100000 para 5 dígitos
        consumo = (capacidade - leitura_anterior) + leitura_atual
    else:
        consumo = leitura_atual - leitura_anterior

    consumo = max(0, consumo)

    if ocorrencia and ocorrencia.get('desconsidera_leitura'):
        tipo_acao = ocorrencia.get('tipo_acao', '')
        if tipo_acao == '01':
            consumo = consumo_medio          # Calcula pela Média
        elif tipo_acao == '02':
            consumo = consumo_minimo         # Tarifa Mínima
        elif tipo_acao == '03':
            consumo = ocorrencia.get('consumo_fixo', 0)  # Consumo Fixo
        # tipo_acao 04 e 05: mantém consumo normal/medido

    return consumo


def validar_consumo(consumo: int, consumo_medio: int) -> dict:
    """
    Valida o consumo e retorna alertas se necessário.

    Returns:
        Dict com 'alerta' (null, 'alto', 'baixo', 'zero') e 'mensagem'
    """
    if consumo_medio <= 0:
        return {'alerta': None, 'mensagem': None}

    if consumo == 0:
        return {
            'alerta': 'zero',
            'mensagem': f'Consumo ZERO. Média histórica: {consumo_medio} m³. Verificar hidrômetro.'
        }

    ratio = consumo / consumo_medio if consumo_medio > 0 else 1

    if ratio >= 5:
        return {
            'alerta': 'alto',
            'mensagem': f'Consumo {consumo} m³ é {ratio:.1f}x acima da média ({consumo_medio} m³). Possível erro de leitura.'
        }

    if ratio <= 0.2 and consumo_medio >= 5:
        return {
            'alerta': 'baixo',
            'mensagem': f'Consumo {consumo} m³ é muito abaixo da média ({consumo_medio} m³). Verificar vazamento ou leitura.'
        }

    return {'alerta': None, 'mensagem': None}


def calcular_conta(
    consumo: int,
    tarifas_agua: List[dict],
    tarifas_lixo: List[dict],
    percentual_esgoto: float = 70.0,
    consumo_minimo: int = 10,
    tem_agua: bool = True,
    tem_esgoto: bool = True,
    tem_lixo: bool = True,
) -> dict:
    """
    Calcula os valores completos da conta respeitando os servicos da instalacao.

    Args:
        consumo: consumo em m3
        tarifas_agua: faixas de tarifa de agua
        tarifas_lixo: faixas de tarifa de lixo
        percentual_esgoto: % do valor de agua cobrado como esgoto (configuravel)
        consumo_minimo: m3 incluidos na taxa minima
        tem_agua: False = instalacao sem taxa/fornecimento de agua
        tem_esgoto: False = instalacao SO AGUA (sem cobranca de esgoto)
        tem_lixo: False = instalacao sem taxa de lixo

    Returns:
        Dict com valor_agua, valor_esgoto, valor_lixo, valor_total
    """
    valor_agua_teorico = calcular_por_faixas(consumo, tarifas_agua, consumo_minimo)
    valor_agua   = valor_agua_teorico if tem_agua else 0.0
    valor_esgoto = round(valor_agua_teorico * (percentual_esgoto / 100), 2) if tem_esgoto else 0.0
    valor_lixo   = calcular_por_faixas(consumo, tarifas_lixo, consumo_minimo) if tem_lixo else 0.0
    valor_total  = round(valor_agua + valor_esgoto + valor_lixo, 2)

    return {
        'valor_agua': valor_agua,
        'valor_esgoto': valor_esgoto,
        'valor_lixo': valor_lixo,
        'valor_total': valor_total,
    }

