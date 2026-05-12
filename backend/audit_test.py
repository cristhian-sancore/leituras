import json, sys, pathlib

# adicionar caminho do backend ao PYTHONPATH
root = pathlib.Path(r'I:\\BKP DO NOTEBOOK DO ESCRITORIO\\coisa\\SAEMI\\saemi-saas\\backend')
sys.path.append(str(root))

from app.services.calculadora import calcular_consumo, validar_consumo, calcular_conta
from app.services.parser_rem import parse_rem
from app.services.gerador_ret import gerar_arquivo_ret

# ---------------------------------------------------
# 1. Test parser_rem com conteúdo mínimo
rem_content = """A04 01 01 0000010.00 0001\nA05 0001 DESCRICAO 01 00010 S\nA11 0000000000012345          00000123 1                00000100 00000100 0\n"""
try:
    parsed = parse_rem(rem_content)
    print('Parser OK, keys:', parsed.keys())
except Exception as e:
    print('Parser ERROR:', e)

# ---------------------------------------------------
# 2. Calcular consumo simples
try:
    consumo = calcular_consumo(leitura_atual=120, leitura_anterior=100, ocorrencia={'desconsidera_leitura': False, 'tipo_acao': ''})
    print('Consumo:', consumo)
    alert = validar_consumo(consumo, consumo_medio=30)
    print('Validar consumo:', alert)
except Exception as e:
    print('Calculo consumo ERROR:', e)

# ---------------------------------------------------
# 3. Calcular conta
faixas_agua = [{"valor_minimo": 10.0, "limite_metros": 10, "preco_metro": 2.0}, {"valor_minimo": None, "limite_metros": 20, "preco_metro": 3.0}]
faixas_lixo = [{"valor_minimo": 5.0, "limite_metros": 0, "preco_metro": None}]
try:
    conta = calcular_conta(consumo=25, tarifas_agua=faixas_agua, tarifas_lixo=faixas_lixo, tem_esgoto=True, tem_lixo=True)
    print('Conta:', conta)
except Exception as e:
    print('Conta ERROR:', e)

# ---------------------------------------------------
# 4. Gerar .RET (usando cliente e leitura fictícios)
cliente = {
    'codigo_full': '000000000001234',
    'zona': '001',
    'rota': '01',
    'sequencia': '000001',
    'mes_ano_ref': '082023',
    'num_fatura': '123456',
    'data_vencimento': '30/08/2023'
}
leitura = {
    'leitura_atual': 120,
    'consumo': 20,
    'valor_agua': 30.0,
    'valor_esgoto': 21.0,
    'valor_total': 51.0,
    'ocorrencia_codigo': '0000'
}
try:
    ret = gerar_arquivo_ret([{'cliente': cliente, 'leitura': leitura}])
    print('RET generated, lines:', len(ret.split('\r\n')))
except Exception as e:
    print('RET ERROR:', e)
