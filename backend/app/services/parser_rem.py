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

    # -----------------------------------------------------------
    # Descricoes dinamicas
    # -----------------------------------------------------------
    desc_agua = 'AGUA'
    desc_esgoto = 'ESGOTO'
    desc_lixo = 'TAXA DE LIXO'

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
    analises_agua = []
    mensagens_por_mat = {}
    historico_por_mat = {}

    # -----------------------------------------------------------
    # PRE-PROCESSAMENTO: coletar A12 (taxas extras) por matricula
    # A12 indica cobrancas extras como TAXA DE LIXO por cliente.
    # Formato: A12 + matricula[3:18] + ... + descricao[20:70]
    # -----------------------------------------------------------
    matriculas_com_lixo = set()
    for line in lines:
        clean = line.strip()
        # Captura descricoes do A01
        if clean.startswith('A01'):
            if len(line) >= 58:
                desc_agua = line[18:58].strip()
            if len(line) >= 98:
                desc_esgoto = line[58:98].strip()

        if clean.startswith('A12') and len(clean) > 25:
            mat_a12 = clean[3:18].strip()
            descricao_a12 = clean[20:70].upper()
            if 'LIXO' in descricao_a12:
                matriculas_com_lixo.add(mat_a12)
                if desc_lixo == 'TAXA DE LIXO': # Pega o primeiro como padrao
                    raw_desc = clean[20:70].strip()
                    # Remove prefixo numerico (ex: "005TAXA DE LIXO*" -> "TAXA DE LIXO")
                    import re
                    raw_desc = re.sub(r'^\d+', '', raw_desc).strip().rstrip('*').strip()
                    if raw_desc:
                        desc_lixo = raw_desc

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
        # A07 - Analise de Agua
        # ============================================
        if clean.startswith('A07'):
            param = clean[9:34].strip()
            unid = clean[34:49].strip()
            vmp = clean[49:69].strip()
            # valor esta no final
            val = clean[89:104].strip() if len(clean) > 100 else clean[89:].strip()
            analises_agua.append({
                'parametro': param,
                'unidade': unid,
                'vmp': vmp,
                'valor': val
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
                hidrometro = line[64:76].strip() if len(line) > 76 else ''
                cep = line[314:324].strip() if len(line) > 324 else ''
                vazao = line[523:533].strip() if len(line) > 533 else ''
                diametro = line[533:543].strip() if len(line) > 543 else ''
                data_instalacao = line[553:563].strip() if len(line) > 563 else ''
                endereco_entrega = line[1052:1102].strip() if len(line) > 1102 else ''
                # Codigo de barras: posicao padrao 436-480 (44 digitos)
                codigo_barras = line[436:480].strip() if len(line) > 480 else ''
                # Limpa caracteres nao-numericos (espaco, letras, etc)
                codigo_barras = ''.join(c for c in codigo_barras if c.isdigit())
                # Se veio vazio na posicao padrao, tenta posicao alternativa (480-524)
                if not codigo_barras and len(line) > 524:
                    alt_barras = line[480:524].strip()
                    alt_barras = ''.join(c for c in alt_barras if c.isdigit())
                    if len(alt_barras) >= 20:
                        codigo_barras = alt_barras

                # -------------------------------------------------------
                # FLAGS DE SERVICO por cliente
                # Posicoes 75-107 contem status + descricao do tipo servico:
                #   "SO AGUA"        => apenas agua, SEM esgoto
                #   "AGUA E ESGOTO"  => agua E esgoto
                #   "SO ESGOTO"      => apenas esgoto, SEM agua
                #   "ESGOTO"         => tem esgoto
                # -------------------------------------------------------
                descricao_servico = line[75:107].upper() if len(line) > 107 else ''
                tem_esgoto = 'ESGOTO' in descricao_servico
                # Agua: presente se descricao contém 'AGUA', ou se nao tem descricao (padrao)
                if descricao_servico.strip():
                    tem_agua = 'AGUA' in descricao_servico
                else:
                    tem_agua = True  # padrao: tem agua

                # Lixo: indicado por A12 com 'LIXO' para esta matricula
                tem_lixo = matricula in matriculas_com_lixo

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
                'tem_esgoto': tem_esgoto,
                'tem_lixo': tem_lixo,
                'tem_agua': tem_agua,
                'hidrometro': hidrometro,
                'cep': cep,
                'vazao': vazao,
                'diametro': diametro,
                'data_instalacao': data_instalacao,
                'endereco_entrega': endereco_entrega,
                'codigo_barras': codigo_barras,
            })

        # ============================================
        # A13 - Mensagens da Fatura
        # ============================================
        if clean.startswith('A13'):
            mat = line[3:18].strip()
            msg = line[22:].strip()
            if msg:
                if mat not in mensagens_por_mat:
                    mensagens_por_mat[mat] = []
                mensagens_por_mat[mat].append(msg)

        # ============================================
        # A14 - Historico de Consumo
        # ============================================
        if clean.startswith('A14'):
            mat = line[3:18].strip()
            mes_ano = line[20:27].strip()
            try:
                consumo = int(line[40:49])
            except ValueError:
                consumo = 0
            if mat not in historico_por_mat:
                historico_por_mat[mat] = []
            historico_por_mat[mat].append({'mes_ano': mes_ano, 'consumo': consumo})

    # Anexar mensagens e historico aos clientes
    for c in clientes:
        mat = c['matricula']
        c['mensagens_fatura'] = mensagens_por_mat.get(mat, [])
        c['historico_consumo'] = historico_por_mat.get(mat, [])

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
        'desc_agua': desc_agua,
        'desc_esgoto': desc_esgoto,
        'desc_lixo': desc_lixo,
        'tarifas': tarifas_list,
        'ocorrencias': ocorrencias,
        'clientes': clientes,
        'analises_agua': analises_agua,
    }
