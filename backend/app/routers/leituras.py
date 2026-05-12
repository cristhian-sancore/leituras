from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from app.database import get_db
from app.models import Cliente, Leitura, Tarifa, Ocorrencia, Importacao, Empresa, Usuario, AuditLog
from app.schemas import ClienteComLeitura, LeituraUpdate, StatsOut, OcorrenciaOut, TarifaOut
from app.auth.deps import get_current_user
from app.services.calculadora import calcular_consumo, calcular_conta, validar_consumo

router = APIRouter(prefix="/leituras", tags=["Leituras"])


async def _get_empresa_config(db: AsyncSession, empresa_id: int) -> dict:
    """Busca configurações da empresa (% esgoto, consumo mínimo)."""
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        return {'percentual_esgoto': 70.0, 'consumo_minimo_m3': 10}
    return {
        'percentual_esgoto': float(empresa.percentual_esgoto or 70),
        'consumo_minimo_m3': int(empresa.consumo_minimo_m3 or 10),
    }


async def _get_tarifas_dict(db: AsyncSession, imp_id: int, empresa_id: int) -> dict:
    """Busca tarifas e organiza por categoria."""
    result = await db.execute(
        select(Tarifa).where(
            Tarifa.importacao_id == imp_id,
            Tarifa.empresa_id == empresa_id,
        )
    )
    tarifas = result.scalars().all()
    tarifas_dict = {}
    for t in tarifas:
        key = f"{t.categoria}_{t.servico}"
        if key not in tarifas_dict:
            tarifas_dict[key] = []
        tarifas_dict[key].append({
            'valor_minimo': float(t.valor_minimo) if t.valor_minimo else None,
            'limite_metros': float(t.limite_metros) if t.limite_metros else None,
            'preco_metro': float(t.preco_metro) if t.preco_metro else None,
        })
    return tarifas_dict


async def _get_ocorrencias_dict(db: AsyncSession, imp_id: int, empresa_id: int) -> dict:
    """Busca ocorrências e organiza por código."""
    result = await db.execute(
        select(Ocorrencia).where(
            Ocorrencia.importacao_id == imp_id,
            Ocorrencia.empresa_id == empresa_id,
        )
    )
    ocorrs = result.scalars().all()
    return {o.codigo: {
        'tipo_acao': o.tipo_acao,
        'consumo_fixo': o.consumo_fixo,
        'desconsidera_leitura': o.desconsidera_leitura,
    } for o in ocorrs}



@router.get("/{imp_id}/stats", response_model=StatsOut)
async def get_stats(
    imp_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Estatísticas de uma importação."""
    total_result = await db.execute(
        select(sqlfunc.count(Cliente.id)).where(
            Cliente.importacao_id == imp_id,
            Cliente.empresa_id == current_user.empresa_id,
        )
    )
    total_clientes = total_result.scalar() or 0

    leit_result = await db.execute(
        select(
            sqlfunc.count(Leitura.id),
            sqlfunc.coalesce(sqlfunc.sum(Leitura.consumo), 0),
            sqlfunc.coalesce(sqlfunc.sum(Leitura.valor_total), 0),
        ).where(
            Leitura.importacao_id == imp_id,
            Leitura.empresa_id == current_user.empresa_id,
        )
    )
    row = leit_result.one()
    realizadas = row[0] or 0
    consumo_total = int(row[1] or 0)
    valor_total = float(row[2] or 0)

    return StatsOut(
        total_clientes=total_clientes,
        leituras_realizadas=realizadas,
        leituras_pendentes=total_clientes - realizadas,
        consumo_total=consumo_total,
        valor_total=valor_total,
    )


@router.get("/{imp_id}/ocorrencias", response_model=List[OcorrenciaOut])
async def get_ocorrencias(
    imp_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Listar ocorrências disponíveis para uma importação."""
    result = await db.execute(
        select(Ocorrencia).where(
            Ocorrencia.importacao_id == imp_id,
            Ocorrencia.empresa_id == current_user.empresa_id,
        )
    )
    return [OcorrenciaOut.model_validate(o) for o in result.scalars().all()]


@router.get("/{imp_id}/tarifas", response_model=List[TarifaOut])
async def get_tarifas(
    imp_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Listar tarifas de uma importação."""
    result = await db.execute(
        select(Tarifa).where(
            Tarifa.importacao_id == imp_id,
            Tarifa.empresa_id == current_user.empresa_id,
        )
    )
    return [TarifaOut.model_validate(t) for t in result.scalars().all()]


@router.get("/{imp_id}", response_model=List[ClienteComLeitura])
async def list_clientes_com_leituras(
    imp_id: int,
    busca: Optional[str] = Query(None, description="Buscar por nome, matrícula, endereço, rota ou setor"),
    page: int = Query(1, ge=1, description="Página"),
    limit: int = Query(100, ge=10, le=500, description="Itens por página"),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Listar clientes de uma importação com suas leituras (paginado)."""
    # Verificar acesso
    result = await db.execute(
        select(Importacao).where(
            Importacao.id == imp_id,
            Importacao.empresa_id == current_user.empresa_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Importação não encontrada")

    # Buscar clientes com paginação
    query = select(Cliente).where(
        Cliente.importacao_id == imp_id,
        Cliente.empresa_id == current_user.empresa_id,
    )

    # DISTRIBUIÇÃO: leiturista só vê os clientes atribuídos a ele
    # Se supervisor/admin → vê tudo. Se leiturista → filtrar pelos seus.
    # Mas só filtra se houver alguma atribuição nessa importação (evita travar importações antigas)
    if current_user.role == "leiturista":
        # Verificar se existe alguma atribuição nesta importação
        atrib_check = await db.execute(
            select(sqlfunc.count(Cliente.id)).where(
                Cliente.importacao_id == imp_id,
                Cliente.empresa_id == current_user.empresa_id,
                Cliente.leiturista_atribuido_id.isnot(None),
            )
        )
        total_atribuidos = atrib_check.scalar() or 0
        if total_atribuidos > 0:
            # Importação já tem distribuição → leiturista vê só os seus
            query = query.where(
                Cliente.leiturista_atribuido_id == current_user.id
            )
        # Se total_atribuidos == 0 → sem distribuição → vê tudo (compatibilidade)

    if busca:
        term = f"%{busca}%"
        query = query.where(
            (Cliente.nome.ilike(term)) |
            (Cliente.matricula.ilike(term)) |
            (Cliente.rua.ilike(term)) |
            (Cliente.bairro.ilike(term)) |
            (Cliente.zona.ilike(term)) |
            (Cliente.rota.ilike(term))
        )

    offset = (page - 1) * limit
    query = query.order_by(Cliente.rota, Cliente.sequencia, Cliente.id).offset(offset).limit(limit)
    result = await db.execute(query)
    clientes = result.scalars().all()

    # Buscar leituras existentes para esses clientes
    cliente_ids = [c.id for c in clientes]
    leituras_map = {}
    if cliente_ids:
        leitura_result = await db.execute(
            select(Leitura).where(
                Leitura.importacao_id == imp_id,
                Leitura.cliente_id.in_(cliente_ids),
            )
        )
        leituras_map = {l.cliente_id: l for l in leitura_result.scalars().all()}

    # Montar resposta
    items = []
    for c in clientes:
        leitura = leituras_map.get(c.id)
        items.append(ClienteComLeitura(
            id=c.id,
            matricula=c.matricula,
            nome=c.nome,
            categoria=c.categoria,
            leitura_anterior=c.leitura_anterior,
            consumo_medio=c.consumo_medio,
            rua=c.rua,
            numero=c.numero,
            bairro=c.bairro,
            zona=c.zona,
            rota=c.rota,
            sequencia=c.sequencia,
            leitura_atual=leitura.leitura_atual if leitura else None,
            ocorrencia_codigo=leitura.ocorrencia_codigo if leitura else None,
            consumo=leitura.consumo if leitura else 0,
            valor_total=float(leitura.valor_total) if leitura else 0.0,
        ))

    return items
