from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Empresa, Usuario
from app.schemas import EmpresaOut, EmpresaUpdate
from app.auth.deps import get_current_user, require_role

router = APIRouter(prefix="/empresa", tags=["Empresa"])


@router.get("/", response_model=EmpresaOut)
async def get_empresa(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna dados da empresa do usuário logado."""
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return EmpresaOut.model_validate(empresa)


@router.put("/", response_model=EmpresaOut)
async def update_empresa(
    data: EmpresaUpdate,
    current_user: Usuario = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Atualizar dados da empresa (admin only)."""
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    if data.nome is not None:
        empresa.nome = data.nome
    if data.cnpj is not None:
        empresa.cnpj = data.cnpj

    return EmpresaOut.model_validate(empresa)
