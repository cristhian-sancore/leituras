"""
Router de Atribuição de Leituristas por Rota.
Permite ao Supervisor distribuir rotas específicas para cada leiturista.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc, update, distinct, or_
from pydantic import BaseModel
from app.database import get_db
from app.models import Cliente, Leitura, Usuario, Importacao
from app.auth.deps import get_current_user, require_role

router = APIRouter(prefix="/atribuicoes", tags=["Atribuições"])


# ============================================
# SCHEMAS LOCAIS
# ============================================

class AtribuicaoRota(BaseModel):
    """Uma rota atribuída a um leiturista."""
    rota: str
    leiturista_id: Optional[int] = None  # None = sem atribuição (limpar)


class AtribuicoesBatch(BaseModel):
    """Lote de atribuições para salvar de uma vez."""
    atribuicoes: List[AtribuicaoRota]


class RotaInfo(BaseModel):
    """Info de uma rota com progresso."""
    rota: str
    total_clientes: int
    leituras_feitas: int
    percentual: float
    leiturista_id: Optional[int] = None
    leiturista_nome: Optional[str] = None


class LeitureistaProgresso(BaseModel):
    """Progresso de um leiturista na importação."""
    leiturista_id: int
    nome: str
    email: str
    rotas: List[str]
    total_clientes: int
    leituras_feitas: int
    percentual: float


# ============================================
# ENDPOINTS
# ============================================

@router.get("/{imp_id}/rotas", response_model=List[RotaInfo])
async def listar_rotas(
    imp_id: int,
    current_user: Usuario = Depends(require_role("supervisor", "admin", "superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas as rotas da importação com progresso e atribuição atual."""
    # Verificar acesso
    result = await db.execute(
        select(Importacao).where(
            Importacao.id == imp_id,
            Importacao.empresa_id == current_user.empresa_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Importação não encontrada")

    # Rotas distintas com total de clientes e leiturista atribuído
    rotas_result = await db.execute(
        select(
            Cliente.rota,
            sqlfunc.count(Cliente.id).label("total"),
            sqlfunc.max(Cliente.leiturista_atribuido_id).label("leiturista_id"),
        )
        .where(
            Cliente.importacao_id == imp_id,
            Cliente.empresa_id == current_user.empresa_id,
        )
        .group_by(Cliente.rota)
        .order_by(Cliente.rota)
    )
    rotas_raw = rotas_result.all()

    # Leituras feitas por rota
    leit_result = await db.execute(
        select(Cliente.rota, sqlfunc.count(Leitura.id))
        .join(Leitura, Leitura.cliente_id == Cliente.id)
        .where(
            Cliente.importacao_id == imp_id,
            Cliente.empresa_id == current_user.empresa_id,
            (
                Leitura.leitura_atual.isnot(None) |
                (Leitura.ocorrencia_codigo.isnot(None) & (Leitura.ocorrencia_codigo != '0000'))
            ),
        )
        .group_by(Cliente.rota)
    )
    leit_por_rota = {row[0]: row[1] for row in leit_result.all()}

    # Buscar nomes dos leituristas
    leiturista_ids = [r.leiturista_id for r in rotas_raw if r.leiturista_id]
    leituristas_map = {}
    if leiturista_ids:
        leit_q = await db.execute(
            select(Usuario).where(Usuario.id.in_(leiturista_ids))
        )
        for u in leit_q.scalars().all():
            leituristas_map[u.id] = u.nome

    itens = []
    for row in rotas_raw:
        rota_label = (row.rota or "").strip() or "S/Rota"
        feitas = leit_por_rota.get(row.rota, 0)
        total = row.total or 0
        perc = round((feitas / total * 100) if total > 0 else 0, 1)
        itens.append(RotaInfo(
            rota=rota_label,
            total_clientes=total,
            leituras_feitas=feitas,
            percentual=perc,
            leiturista_id=row.leiturista_id,
            leiturista_nome=leituristas_map.get(row.leiturista_id) if row.leiturista_id else None,
        ))

    return itens


@router.post("/{imp_id}/atribuir")
async def salvar_atribuicoes(
    imp_id: int,
    data: AtribuicoesBatch,
    current_user: Usuario = Depends(require_role("supervisor", "admin", "superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Atribui leituristas por rota.
    Atualiza em massa o campo leiturista_atribuido_id em todos os clientes da rota.
    leiturista_id = None limpa a atribuição (sem atribuição).
    """
    # Verificar acesso
    result = await db.execute(
        select(Importacao).where(
            Importacao.id == imp_id,
            Importacao.empresa_id == current_user.empresa_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Importação não encontrada")

    total_atualizados = 0
    for atrib in data.atribuicoes:
        # Validar leiturista pertence à empresa (se informado)
        if atrib.leiturista_id is not None:
            user_check = await db.execute(
                select(Usuario).where(
                    Usuario.id == atrib.leiturista_id,
                    Usuario.empresa_id == current_user.empresa_id,
                    Usuario.ativo == True,
                )
            )
            if not user_check.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Leiturista ID {atrib.leiturista_id} não encontrado ou inativo"
                )

        # Atualizar todos os clientes da rota (normalizado — corrige espaços)
        rota_val = atrib.rota.strip() if atrib.rota else ""
        if rota_val == "S/Rota" or rota_val == "":
            # Rota vazia ou None
            stmt = (
                update(Cliente)
                .where(
                    Cliente.importacao_id == imp_id,
                    Cliente.empresa_id == current_user.empresa_id,
                    or_(Cliente.rota.is_(None), sqlfunc.trim(Cliente.rota) == ""),
                )
                .values(leiturista_atribuido_id=atrib.leiturista_id)
            )
        else:
            stmt = (
                update(Cliente)
                .where(
                    Cliente.importacao_id == imp_id,
                    Cliente.empresa_id == current_user.empresa_id,
                    sqlfunc.trim(Cliente.rota) == rota_val,
                )
                .values(leiturista_atribuido_id=atrib.leiturista_id)
            )
        result = await db.execute(stmt)
        total_atualizados += result.rowcount

    await db.commit()
    return {
        "detail": "Atribuições salvas com sucesso",
        "clientes_atualizados": total_atualizados
    }


@router.get("/{imp_id}/leituristas", response_model=List[LeitureistaProgresso])
async def progresso_por_leiturista(
    imp_id: int,
    current_user: Usuario = Depends(require_role("supervisor", "admin", "superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Progresso de cada leiturista: quantas leituras fez vs total atribuído."""
    # Verificar acesso
    result = await db.execute(
        select(Importacao).where(
            Importacao.id == imp_id,
            Importacao.empresa_id == current_user.empresa_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Importação não encontrada")

    # Total de clientes por leiturista atribuído
    total_result = await db.execute(
        select(Cliente.leiturista_atribuido_id, sqlfunc.count(Cliente.id))
        .where(
            Cliente.importacao_id == imp_id,
            Cliente.empresa_id == current_user.empresa_id,
            Cliente.leiturista_atribuido_id.isnot(None),
        )
        .group_by(Cliente.leiturista_atribuido_id)
    )
    totais = {row[0]: row[1] for row in total_result.all()}

    # Leituras feitas por leiturista
    feitas_result = await db.execute(
        select(Cliente.leiturista_atribuido_id, sqlfunc.count(Leitura.id))
        .join(Leitura, Leitura.cliente_id == Cliente.id)
        .where(
            Cliente.importacao_id == imp_id,
            Cliente.empresa_id == current_user.empresa_id,
            Cliente.leiturista_atribuido_id.isnot(None),
            (
                Leitura.leitura_atual.isnot(None) |
                (Leitura.ocorrencia_codigo.isnot(None) & (Leitura.ocorrencia_codigo != '0000'))
            ),
        )
        .group_by(Cliente.leiturista_atribuido_id)
    )
    feitas = {row[0]: row[1] for row in feitas_result.all()}

    # Rotas por leiturista
    rotas_result = await db.execute(
        select(Cliente.leiturista_atribuido_id, Cliente.rota)
        .where(
            Cliente.importacao_id == imp_id,
            Cliente.empresa_id == current_user.empresa_id,
            Cliente.leiturista_atribuido_id.isnot(None),
        )
        .distinct()
    )
    rotas_por_leit: dict = {}
    for row in rotas_result.all():
        lid = row[0]
        if lid not in rotas_por_leit:
            rotas_por_leit[lid] = []
        if row[1] and row[1] not in rotas_por_leit[lid]:
            rotas_por_leit[lid].append((row[1] or "S/Rota").strip())

    # Buscar dados dos leituristas
    if not totais:
        return []

    users_result = await db.execute(
        select(Usuario).where(
            Usuario.id.in_(list(totais.keys())),
            Usuario.empresa_id == current_user.empresa_id,
        )
    )

    itens = []
    for u in users_result.scalars().all():
        total = totais.get(u.id, 0)
        done = feitas.get(u.id, 0)
        perc = round((done / total * 100) if total > 0 else 0, 1)
        itens.append(LeitureistaProgresso(
            leiturista_id=u.id,
            nome=u.nome,
            email=u.email,
            rotas=sorted(rotas_por_leit.get(u.id, [])),
            total_clientes=total,
            leituras_feitas=done,
            percentual=perc,
        ))

    return sorted(itens, key=lambda x: x.nome)


@router.delete("/{imp_id}/limpar")
async def limpar_atribuicoes(
    imp_id: int,
    current_user: Usuario = Depends(require_role("supervisor", "admin", "superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Remove todas as atribuições da importação (volta ao modo 'todos veem tudo')."""
    result = await db.execute(
        select(Importacao).where(
            Importacao.id == imp_id,
            Importacao.empresa_id == current_user.empresa_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Importação não encontrada")

    stmt = (
        update(Cliente)
        .where(
            Cliente.importacao_id == imp_id,
            Cliente.empresa_id == current_user.empresa_id,
        )
        .values(leiturista_atribuido_id=None)
    )
    r = await db.execute(stmt)
    return {"detail": "Atribuições removidas", "clientes_atualizados": r.rowcount}
