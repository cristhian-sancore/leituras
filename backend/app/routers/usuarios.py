from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from app.database import get_db
from app.models import Usuario, Empresa
from app.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.auth.password import hash_password
from app.auth.deps import require_role

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/", response_model=List[UsuarioOut])
async def list_usuarios(
    current_user: Usuario = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Listar todos os usuarios da empresa."""
    result = await db.execute(
        select(Usuario).where(Usuario.empresa_id == current_user.empresa_id).order_by(Usuario.nome)
    )
    return [UsuarioOut.model_validate(u) for u in result.scalars().all()]


@router.post("/", response_model=UsuarioOut, status_code=201)
async def create_usuario(
    data: UsuarioCreate,
    current_user: Usuario = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Criar novo usuario na empresa (admin only). Verifica limite do plano."""
    # Verificar email duplicado
    existing = await db.execute(select(Usuario).where(Usuario.email == data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email ja cadastrado")

    # Verificar limite de leituristas do plano
    emp_result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = emp_result.scalar_one_or_none()
    if empresa:
        count_result = await db.execute(
            select(sqlfunc.count(Usuario.id)).where(
                Usuario.empresa_id == current_user.empresa_id,
                Usuario.ativo == True,
            )
        )
        total_ativos = count_result.scalar() or 0
        if total_ativos >= empresa.max_leituristas:
            raise HTTPException(
                status_code=403,
                detail=f"Limite do plano atingido ({empresa.max_leituristas} usuarios). Contate o suporte para upgrade."
            )

    usuario = Usuario(
        empresa_id=current_user.empresa_id,
        nome=data.nome,
        email=data.email.lower(),
        senha_hash=hash_password(data.senha),
        role=data.role,
    )
    db.add(usuario)
    await db.flush()
    return UsuarioOut.model_validate(usuario)


@router.put("/{user_id}", response_model=UsuarioOut)
async def update_usuario(
    user_id: int,
    data: UsuarioUpdate,
    current_user: Usuario = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Atualizar um usuario da empresa."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == user_id,
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    if data.nome is not None:
        usuario.nome = data.nome
    if data.email is not None:
        usuario.email = data.email.lower()
    if data.role is not None:
        usuario.role = data.role
    if data.ativo is not None:
        usuario.ativo = data.ativo

    return UsuarioOut.model_validate(usuario)


@router.delete("/{user_id}")
async def delete_usuario(
    user_id: int,
    current_user: Usuario = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Desativar um usuario da empresa."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Nao eh possivel desativar a si mesmo")

    result = await db.execute(
        select(Usuario).where(
            Usuario.id == user_id,
            Usuario.empresa_id == current_user.empresa_id,
        )
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    usuario.ativo = False
    return {"detail": "Usuario desativado"}
