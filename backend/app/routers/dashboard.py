from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from app.database import get_db
from app.models import Importacao, Cliente, Leitura, Usuario
from app.schemas import DashboardResumo, StatsOut, ImportacaoOut, ProgressoRota
from app.auth.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/resumo", response_model=DashboardResumo)
async def get_resumo(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resumo geral do dashboard."""
    empresa_id = current_user.empresa_id

    # Guard: superadmin não tem empresa_id — dashboard normal não se aplica
    if empresa_id is None:
        return DashboardResumo(
            total_importacoes=0,
            importacao_ativa=None,
            total_usuarios=0,
            stats=None,
        )

    total_imp = await db.execute(
        select(sqlfunc.count(Importacao.id)).where(Importacao.empresa_id == empresa_id)
    )

    # Total usuários
    total_users = await db.execute(
        select(sqlfunc.count(Usuario.id)).where(Usuario.empresa_id == empresa_id)
    )

    # Importação ativa mais recente
    imp_result = await db.execute(
        select(Importacao)
        .where(Importacao.empresa_id == empresa_id, Importacao.status == "ativo")
        .order_by(Importacao.data_importacao.desc())
        .limit(1)
    )
    imp_ativa = imp_result.scalar_one_or_none()

    stats = None
    if imp_ativa:
        # Stats da importação ativa
        total_clientes = await db.execute(
            select(sqlfunc.count(Cliente.id)).where(Cliente.importacao_id == imp_ativa.id)
        )
        leit_result = await db.execute(
            select(
                sqlfunc.count(Leitura.id),
                sqlfunc.coalesce(sqlfunc.sum(Leitura.consumo), 0),
                sqlfunc.coalesce(sqlfunc.sum(Leitura.valor_total), 0),
            ).where(Leitura.importacao_id == imp_ativa.id)
        )
        row = leit_result.one()
        tc = total_clientes.scalar() or 0
        realizadas = row[0] or 0

        stats = StatsOut(
            total_clientes=tc,
            leituras_realizadas=realizadas,
            leituras_pendentes=tc - realizadas,
            consumo_total=int(row[1] or 0),
            valor_total=float(row[2] or 0),
        )

    return DashboardResumo(
        total_importacoes=total_imp.scalar() or 0,
        importacao_ativa=ImportacaoOut.model_validate(imp_ativa) if imp_ativa else None,
        total_usuarios=total_users.scalar() or 0,
        stats=stats,
    )


@router.get("/por-rota", response_model=List[ProgressoRota])
async def progresso_por_rota(
    imp_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Progresso de leituras agrupado por rota."""
    empresa_id = current_user.empresa_id

    # Total por rota
    total_result = await db.execute(
        select(Cliente.rota, sqlfunc.count(Cliente.id))
        .where(Cliente.importacao_id == imp_id, Cliente.empresa_id == empresa_id)
        .group_by(Cliente.rota)
    )
    totais = {row[0]: row[1] for row in total_result.all()}

    # Realizadas por rota
    real_result = await db.execute(
        select(Cliente.rota, sqlfunc.count(Leitura.id))
        .join(Leitura, Leitura.cliente_id == Cliente.id)
        .where(
            Cliente.importacao_id == imp_id,
            Cliente.empresa_id == empresa_id,
            Leitura.leitura_atual.isnot(None),
        )
        .group_by(Cliente.rota)
    )
    realizadas = {row[0]: row[1] for row in real_result.all()}

    items = []
    for rota, total in sorted(totais.items(), key=lambda x: x[0] or ''):
        real = realizadas.get(rota, 0)
        items.append(ProgressoRota(
            rota=(rota or '').strip() or 'S/R',
            total=total,
            realizadas=real,
            pendentes=total - real,
            percentual=round((real / total * 100) if total > 0 else 0, 1),
        ))

    return items
