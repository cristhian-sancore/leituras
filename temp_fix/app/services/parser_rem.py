"""
Parser do arquivo .REM (SAEMI/SIA)
Registros:
  A04 - Tabelas de tarifas por categoria/servico
  A05 - Ocorrencias (tipos de acao na leitura)
  A11 - Clientes/consumidores com dados cadastrais
  A12 - Taxas extras por cliente (ex: lixo separado)
"""

MAP_CAT = {'01': 'residencial', '02': 'comercial', '03': 'industrial', '04': 'publica', '05': 'tarifa_social'}
MAP_CAT_A11 = {'1': 'residencial', '2': 'comercial', '3': 'industrial', '4': 'publica', '5': 'tarifa_social'}


def parse_rem(content: str) -> dict:
    """
    Parseia o conteudo de um arquivo .REM e retorna dicionario com:
    - tarifas: lista de dicts por categoria/servico
    - ocorrencias: lista de dicts
    - clientes: lista de dicts (inclui tem_esgoto e tem_lixo)
    """
    lines = content.split('\n')

    tarifas_raw = {
        'residencial': {'agua': [], 'esgoto': [], 'lixo': []},
        'comercial': {'agua': [], 'esgoto': [], 'lixo': []},
        'industrial': {'agua': [], 'esgoto': [], 'lixo': []},
        'publica': {'agua': [], 'esgoto': [], 'lixo': []},
        'tarifa_social': {'agua': [], 'esgoto': [], 'lixo': []},
    }
    ult_lim = {}
    ocorrencias = []
    clientes = []

    # -----------------------------------------------------------
    # PRE-PROCESSAMENTO: coletar A12 (taxas extras) por matricula
    # A12 indica cobrancas extras como TAXA DE LIXO por cliente.
    # Formato: A12 + matricula[3:18] + ... + descricao[20:70]
    # -----------------------------------------------------------
    matriculas_com_lixo = set()
    for line in lines:
        clean = line.strip()
        if clean.startswith('A12') and len(clean) > 25:
            mat_a12 = clean[3:18].strip()
            descricao_a12 = clean[20:70].upper()
            if 'LIXO' in descricao_a12:
                matriculas_com_lixo.add(mat_a12)

    for line in lines:
        clean = line.strip()
        if not clean:
            continue

        # ============================================
        # A04 - Tabelas de Tarifas
        # ============================================
        if clean.startswith('A04'):
            cat_code = clean[3:5].strip()
            cat = MAP_CAT.get(cat_code)
            serv_code = clean[8:10].strip()
            serv = 'agua' if serv_code == '01' else ('esgoto' if serv_code == '02' else ('lixo' if serv_code in ('04', '05') else None))

            # Debug logs no console do container
            print(f"DEBUG A04: cat_code={cat_code} ({cat}), serv_code={serv_code} ({serv})")

            try:
                v_str = clean[15:30].strip()
                v = float(v_str) if v_str else 0.0
            except (ValueError, IndexError):
                continue

            n_faixa = 0
            try:
                nf_str = clean[10:15].strip()
                n_faixa = int(nf_str) if nf_str else 0
            except (ValueError, IndexError):
                continue

            if cat and serv and v < 1000000:
                key = cat + serv
                if len(tarifas_raw[cat][serv]) == 0:
                    # O valor na primeira faixa (A04) do .REM já é o valor fixo cheio.
                    valor_fixo = round(v, 2)
                    tarifas_raw[cat][serv].insert(0, {
                        'faixa': 0,
                        'valor_minimo': valor_fixo,
                        'limite_metros': 0,
                        'preco_metro': None,
                    })
                    ult_lim[key] = n_faixa
                else:
                    if v == 0 and clean[10:15].startswith('9'):
                        continue
                    m = ult_lim.get(key, 10)
                    tarifas_raw[cat][serv].append({
                        'faixa': n_faixa,
                        'valor_minimo': None,
                        'limite_metros': m,
                        'preco_metro': v,
                    })
                    ult_lim[key] = n_faixa

        # ============================================
        # A05 - Ocorrencias
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
                # Ajuste de offsets de endereço conforme padrão Fiorilli e amostra RO0526S6R11
        if line.startswith('A11'):
            try:
                matricula = line[4:13].strip()
                codigo_full = line[4:31].strip()
                nome = line[13:53].strip()
                
                leitura_anterior = int(line[53:60].strip() or "0")
                consumo_medio = int(line[60:68].strip().replace('.', '') or "0")
                
                # Offsets A11 (ajustados para amostra real)
                rua = line[213:253].strip()
                numero = line[253:259].strip()
                bairro = line[266:286].strip()
                cidade = line[286:306].strip()
                uf = line[306:308].strip()
                cep = line[314:323].strip()
                
                mes_ano_ref = line[110:116].strip()
                data_leit_anterior = line[143:151].strip()
                ocorr_anterior = line[151:155].strip()

                # Categoria
                cat_code = line[11:13].strip()
                categoria = MAP_CAT.get(cat_code, "residencial")

                # Extração de campos técnicos para impressão
                economias = int(line[100:104].strip() or "1") if len(line) > 104 else 1
                num_hidrometro = line[116:126].strip() if len(line) > 126 else ''
                rota_cag = line[104:108].strip() if len(line) > 108 else ''
                sequencia_cag = line[108:110].strip() if len(line) > 110 else ''

                # FLAGS DE SERVICO
                descricao_servico = line[75:107].upper() if len(line) > 107 else ''
                tem_agua = 'SO ESGOTO' not in descricao_servico
                tem_esgoto = 'SO AGUA' not in descricao_servico
                tem_lixo = matricula in matriculas_com_lixo

                clientes.append({
                    'matricula': matricula,
                    'codigo_full': codigo_full,
                    'nome': nome,
                    'categoria': categoria,
                    'rua': rua,
                    'numero': numero,
                    'bairro': bairro,
                    'cep': cep,
                    'cidade': cidade,
                    'uf': uf,
                    'rota': rota_cag,
                    'sequencia': sequencia_cag,
                    'num_hidrometro': num_hidrometro,
                    'economias': economias,
                    'leitura_anterior': leitura_anterior,
                    'consumo_medio': consumo_medio,
                    'mes_ano_ref': mes_ano_ref,
                    'data_leit_anterior': data_leit_anterior,
                    'ocorr_anterior': ocorr_anterior,
                    'tem_agua': tem_agua,
                    'tem_esgoto': tem_esgoto,
                    'tem_lixo': tem_lixo,
                })
            except (ValueError, IndexError):
                continue

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
