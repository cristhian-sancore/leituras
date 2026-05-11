"""
Parser do arquivo .REM (SAEMI/SIA)
Registros:
  A04 - Tabelas de tarifas por categoria/serviço
  A05 - Ocorrências (tipos de ação na leitura)
  A11 - Clientes/consumidores com dados cadastrais
"""

MAP_CAT = {'01': 'residencial', '02': 'comercial', '03': 'industrial', '04': 'publica', '05': 'tarifa_social'}
MAP_CAT_A11 = {'1': 'residencial', '2': 'comercial', '3': 'industrial', '4': 'publica', '5': 'tarifa_social'}


def parse_rem(content: str) -> dict:
    """
    Parseia o conteúdo de um arquivo .REM e retorna dicionário com:
    - tarifas: lista de dicts por categoria/serviço
    - ocorrencias: lista de dicts
    - clientes: lista de dicts
    - linhas_originais: conteúdo bruto para referência
    """
    lines = content.split('\n')

    tarifas_raw = {
        'residencial': {'agua': [], 'lixo': []},
        'comercial': {'agua': [], 'lixo': []},
        'industrial': {'agua': [], 'lixo': []},
        'publica': {'agua': [], 'lixo': []},
        'tarifa_social': {'agua': [], 'lixo': []},
    }
    ult_lim = {}
    ocorrencias = []
    clientes = []

    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        # ============================================
        # A04 - Tabelas de Tarifas
        # ============================================
        if clean.startswith('A04'):
            cat = MAP_CAT.get(clean[3:5])
            serv_code = clean[8:10]
            serv = 'agua' if serv_code == '01' else ('lixo' if serv_code in ('04', '05') else None)

            try:
                v = float(clean[15:30].strip())
            except (ValueError, IndexError):
                continue

            n_faixa = 0
            try:
                n_faixa = int(clean[10:14])
            except (ValueError, IndexError):
                continue

            if cat and serv and v < 1000000:
                key = cat + serv
                if n_faixa == 1:
                    tarifas_raw[cat][serv].insert(0, {
                        'faixa': 0,
                        'valor_minimo': round(v * 10, 2),
                        'limite_metros': 0,
                        'preco_metro': None,
                    })
                    ult_lim[key] = 10
                else:
                    if v == 0 and clean[10:14].startswith('9'):
                        continue
                    m = ult_lim.get(key, 10)
                    tarifas_raw[cat][serv].append({
                        'faixa': n_faixa,
                        'valor_minimo': None,
                        'limite_metros': m,
                        'preco_metro': v,
                    })
                    ult_lim[key] = n_faixa * 10

        # ============================================
        # A05 - Ocorrências
        # ============================================
        if clean.startswith('A05'):
            codigo = clean[3:7].strip()
            descricao = clean[7:47].strip() if len(clean) > 7 else ''
            tipo_acao = clean[49:51] if len(clean) > 50 else ''
            try:
                consumo_fixo = int(clean[51:56]) if len(clean) > 55 else 0
            except ValueError:
                consumo_fixo = 0
            desconsidera_leitura = clean[56] == 'S' if len(clean) > 56 else False

            ocorrencias.append({
                'codigo': codigo,
                'descricao': descricao,
                'tipo_acao': tipo_acao,
                'consumo_fixo': consumo_fixo,
                'desconsidera_leitura': desconsidera_leitura,
            })

        # ============================================
        # A11 - Clientes/Consumidores
        # ============================================
        if clean.startswith('A11'):
            try:
                matricula = line[3:18].strip()
                codigo_full = line[3:18]
                nome = line[106:146].strip() if len(line) > 146 else ''
                anterior = int(line[359:367]) if len(line) > 367 else 0
                cat_code = line[324] if len(line) > 324 else '1'
                cat = MAP_CAT_A11.get(cat_code, 'residencial')
                ocorr_anterior = line[367:371].strip() if len(line) > 371 else ''
                consumo_medio = int(line[381:386]) if len(line) > 386 else 0
                rua = line[211:251].strip() if len(line) > 251 else ''
                numero = line[251:257].strip() if len(line) > 257 else ''
                bairro = line[272:292].strip() if len(line) > 292 else ''
                zona = line[22:25] if len(line) > 25 else ''
                rota = line[25:29] if len(line) > 29 else ''
                sequencia = line[42:48] if len(line) > 48 else ''
                tipo_servico = line[398:400] if len(line) > 400 else '02'
                num_fatura = line[416:436] if len(line) > 436 else ''
                data_vencimento = line[486:496] if len(line) > 496 else ''
                mes_ano_ref = line[496:503] if len(line) > 503 else ''
                data_leit_anterior = line[503:513] if len(line) > 513 else ''
            except (ValueError, IndexError):
                continue

            clientes.append({
                'matricula': matricula,
                'codigo_full': codigo_full,
                'nome': nome,
                'categoria': cat,
                'leitura_anterior': anterior,
                'consumo_medio': consumo_medio,
                'rua': rua,
                'numero': numero,
                'bairro': bairro,
                'zona': zona,
                'rota': rota,
                'sequencia': sequencia,
                'tipo_servico': tipo_servico,
                'num_fatura': num_fatura,
                'data_vencimento': data_vencimento,
                'mes_ano_ref': mes_ano_ref,
                'data_leit_anterior': data_leit_anterior,
                'ocorr_anterior': ocorr_anterior,
            })

    # Converter tarifas_raw em lista plana
    tarifas_list = []
    for cat_name, servicos in tarifas_raw.items():
        for serv_name, faixas in servicos.items():
            for tarifa in faixas:
                tarifas_list.append({
                    'categoria': cat_name,
                    'servico': serv_name,
                    **tarifa,
                })

    return {
        'tarifas': tarifas_list,
        'ocorrencias': ocorrencias,
        'clientes': clientes,
    }
