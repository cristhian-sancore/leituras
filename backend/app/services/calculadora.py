"""
Motor de cálculo tarifário SAEMI.
Calcula valores de água, esgoto e lixo por faixas progressivas.
"""
from decimal import Decimal
from typing import List, Dict, Optional


def calcular_por_faixas(consumo: int, faixas: List[dict]) -> float:
    """
    Calcula o valor total por faixas progressivas.
    
    Args:
        consumo: consumo em m³
        faixas: lista de dicts com keys: valor_minimo, limite_metros, preco_metro
                faixa 0 tem valor_minimo (taxa fixa até 10m³)
                faixas seguintes têm limite_metros e preco_metro
    
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

    # Valor base (taxa mínima até 10m³)
    total = float(faixa_min['valor_minimo']) if faixa_min else 0.0

    # Excedente acima de 10m³
    if consumo > 10:
        excedente = consumo - 10
        for i, faixa in enumerate(faixas_exc):
            preco = float(faixa.get('preco_metro', 0) or 0)
            limite_atual = float(faixa.get('limite_metros', 0) or 0)
            # Próximo limite
            if i + 1 < len(faixas_exc):
                prox_limite = float(faixas_exc[i + 1].get('limite_metros', 999999) or 999999)
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
) -> int:
    """
    Calcula o consumo considerando ocorrências especiais.
    
    Args:
        leitura_atual: leitura do hidrômetro atual
        leitura_anterior: leitura anterior
        ocorrencia: dict com tipo_acao, consumo_fixo, desconsidera_leitura
        consumo_medio: média histórica de consumo
    
    Returns:
        Consumo em m³
    """
    consumo = max(0, leitura_atual - leitura_anterior)

    if ocorrencia and ocorrencia.get('desconsidera_leitura'):
        tipo_acao = ocorrencia.get('tipo_acao', '')
        if tipo_acao == '01':
            consumo = consumo_medio          # Calcula pela Média
        elif tipo_acao == '02':
            consumo = 10                     # Tarifa Mínima (10 m³)
        elif tipo_acao == '03':
            consumo = ocorrencia.get('consumo_fixo', 0)  # Consumo Fixo
        # tipo_acao 04 e 05: mantém consumo normal/medido

    return consumo


def calcular_conta(
    consumo: int,
    tarifas_agua: List[dict],
    tarifas_lixo: List[dict],
) -> dict:
    """
    Calcula os valores completos da conta.
    
    Returns:
        Dict com valor_agua, valor_esgoto, valor_lixo, valor_total
    """
    valor_agua = calcular_por_faixas(consumo, tarifas_agua)
    valor_esgoto = round(valor_agua * 0.70, 2)  # Esgoto = 70% da água
    valor_lixo = calcular_por_faixas(consumo, tarifas_lixo)
    valor_total = round(valor_agua + valor_esgoto + valor_lixo, 2)

    return {
        'valor_agua': valor_agua,
        'valor_esgoto': valor_esgoto,
        'valor_lixo': valor_lixo,
        'valor_total': valor_total,
    }
