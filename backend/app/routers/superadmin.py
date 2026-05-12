from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc, desc
from app.database import get_db
from app.models import Empresa, Usuario, Importacao, Leitura, AuditLog
from app.schemas import EmpresaOut
from app.auth.deps import require_role, get_current_user
from app.auth.password import hash_password
from app.config import get_settings
from pydantic import BaseModel

router = APIRouter(prefix="/superadmin", tags=["SaaS Master Admin"])

settings = get_settings()


class GlobalStats(BaseModel):
    total_empresas: int
    empresas_ativas: int
    total_usuarios: int
    total_leituras: int
    total_faturamento_global: float


class EmpresaDetalhada(EmpresaOut):
    total_usuarios: int = 0
    total_leituras: int = 0
    percentual_esgoto: float = 70.0
    consumo_minimo_m3: int = 10


class NovaEmpresaRequest(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    admin_nome: str
    admin_email: str
    admin_senha: str
    plano: str = "basico"
    max_leituristas: int = 5
    percentual_esgoto: float = 70.0
    consumo_minimo_m3: int = 10
    logo_url: Optional[str] = None


class AtualizarEmpresaRequest(BaseModel):
    plano: Optional[str] = None
    max_leituristas: Optional[int] = None
    percentual_esgoto: Optional[float] = None
    consumo_minimo_m3: Optional[int] = None
    logo_url: Optional[str] = None


class UsuarioSuperOut(BaseModel):
    id: int
    nome: str
    email: str
    role: str
    ativo: bool
    created_at: datetime
    ultimo_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogOut(BaseModel):
    id: int
    empresa_id: int
    acao: str
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


import re


def slugify(text: str) -> str:
    text = text.lower().strip()
    for a, b in [('aáâãä', 'a'), ('eéêë', 'e'), ('iíîï', 'i'), ('oóôõö', 'o'), ('uúûü', 'u'), ('ç', 'c')]:
        for c in a:
            text = text.replace(c, b[-1] if len(b) > 1 else b)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text).strip('-')
    return text


class SetupRequest(BaseModel):
    master_key: str
    email: str = "superadmin@saemi.com"
    senha: str = "saemi@2024"
    nome: str = "Super Admin"


class FirstRunRequest(BaseModel):
    # Dados da empresa
    empresa_nome: str
    empresa_cnpj: Optional[str] = None
    # Dados do administrador (supervisor da empresa)
    nome: str
    email: str
    senha: str


@router.get("/setup-status")
async def setup_status(db: AsyncSession = Depends(get_db)):
    """
    Endpoint PÚBLICO — verifica se o sistema precisa de configuração inicial.
    Retorna needs_setup=true se não houver nenhuma empresa cadastrada.
    """
    existing = await db.execute(select(Empresa).limit(1))
    empresa = existing.scalar_one_or_none()
    return {"needs_setup": empresa is None}


@router.post("/setup-first-run")
async def setup_first_run(
    data: FirstRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint PÚBLICO — cria a primeira empresa + supervisor na inicialização.
    Estilo Chatwoot: só funciona enquanto não houver nenhuma empresa cadastrada.
    """
    # Segurança: só executa uma vez
    existing = await db.execute(select(Empresa).limit(1))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Sistema já configurado. Use o painel de login."
        )

    # Validações
    if len(data.empresa_nome.strip()) < 2:
        raise HTTPException(status_code=422, detail="Nome da empresa deve ter pelo menos 2 caracteres")
    if len(data.nome.strip()) < 2:
        raise HTTPException(status_code=422, detail="Seu nome deve ter pelo menos 2 caracteres")
    if len(data.senha) < 6:
        raise HTTPException(status_code=422, detail="Senha deve ter pelo menos 6 caracteres")
    if "@" not in data.email or "." not in data.email:
        raise HTTPException(status_code=422, detail="Email inválido")

    # Verificar email duplicado
    dup = await db.execute(select(Usuario).where(Usuario.email == data.email.lower().strip()))
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Este email já está em uso")

    # Gerar slug único para a empresa
    from app.routers.superadmin import slugify
    base_slug = slugify(data.empresa_nome)
    slug = base_slug
    count = 1
    while True:
        existing_slug = await db.execute(select(Empresa).where(Empresa.slug == slug))
        if not existing_slug.scalar_one_or_none():
            break
        slug = f"{base_slug}-{count}"
        count += 1

    # Criar empresa
    nova_empresa = Empresa(
        nome=data.empresa_nome.strip(),
        cnpj=data.empresa_cnpj,
        slug=slug,
        ativa=True,
        plano="basico",
        max_leituristas=5,
        percentual_esgoto=70.00,
        consumo_minimo_m3=10,
    )
    db.add(nova_empresa)
    await db.flush()  # gera o ID

    # Criar supervisor (admin da empresa)
    novo_usuario = Usuario(
        empresa_id=nova_empresa.id,
        nome=data.nome.strip(),
        email=data.email.lower().strip(),
        senha_hash=hash_password(data.senha),
        role="supervisor",
        ativo=True,
    )
    db.add(novo_usuario)
    await db.flush()

    return {
        "detail": f"Empresa '{nova_empresa.nome}' e administrador '{novo_usuario.email}' criados com sucesso!",
        "empresa": nova_empresa.nome,
        "email": novo_usuario.email,
        "role": "supervisor"
    }


@router.post("/setup")
async def initial_setup(
    data: SetupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint legado com master_key para setup manual via API.
    Mantido para recuperação de emergência via curl/Postman.
    """
    if data.master_key != settings.JWT_SECRET:
        raise HTTPException(status_code=403, detail="Chave master invalida")

    existing = await db.execute(select(Usuario).where(Usuario.role == "superadmin"))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Setup ja foi realizado")

    result = await db.execute(select(Usuario).order_by(Usuario.created_at.asc()).limit(1))
    user = result.scalar_one_or_none()

    if user:
        user.role = "superadmin"
        user.ativo = True
        return {"detail": f"Usuario {user.email} agora eh SuperAdmin Master!"}
    else:
        dup = await db.execute(select(Usuario).where(Usuario.email == data.email.lower()))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email ja cadastrado")

        novo = Usuario(
            empresa_id=None,
            nome=data.nome,
            email=data.email.lower(),
            senha_hash=hash_password(data.senha),
            role="superadmin",
            ativo=True,
        )
        db.add(novo)
        await db.flush()
        return {"detail": f"SuperAdmin '{data.email}' criado com sucesso!"}


@router.get("/stats", response_model=GlobalStats)
async def get_global_stats(
    current_user: Usuario = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Estatisticas globais da plataforma SaaS."""
    emp_count = await db.execute(select(sqlfunc.count(Empresa.id)))
    emp_ativas = await db.execute(select(sqlfunc.count(Empresa.id)).where(Empresa.ativa == True))
    user_count = await db.execute(select(sqlfunc.count(Usuario.id)))
    leit_result = await db.execute(
        select(sqlfunc.count(Leitura.id), sqlfunc.coalesce(sqlfunc.sum(Leitura.valor_total), 0))
    )
    row = leit_result.one()
    return {
        "total_empresas": emp_count.scalar() or 0,
        "empresas_ativas": emp_ativas.scalar() or 0,
        "total_usuarios": user_count.scalar() or 0,
        "total_leituras": row[0] or 0,
        "total_faturamento_global": float(row[1] or 0),
    }


@router.get("/empresas", response_model=List[EmpresaDetalhada])
async def list_todas_empresas(
    current_user: Usuario = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas as empresas com detalhes."""
    result = await db.execute(select(Empresa).order_by(Empresa.created_at.desc()))
    empresas = result.scalars().all()
    items = []
    for e in empresas:
        u_count = await db.execute(select(sqlfunc.count(Usuario.id)).where(Usuario.empresa_id == e.id))
        l_count = await db.execute(select(sqlfunc.count(Leitura.id)).where(Leitura.empresa_id == e.id))
        item = EmpresaDetalhada(
            id=e.id, nome=e.nome, cnpj=e.cnpj, slug=e.slug,
            ativa=e.ativa, plano=e.plano, max_leituristas=e.max_leituristas,
            created_at=e.created_at,
            percentual_esgoto=float(e.percentual_esgoto or 70),
            consumo_minimo_m3=int(e.consumo_minimo_m3 or 10),
            total_usuarios=u_count.scalar() or 0,
            total_leituras=l_count.scalar() or 0,
        )
        items.append(item)
    return items


@router.post("/empresas", status_code=201)
async def criar_empresa(
    data: NovaEmpresaRequest,
    current_user: Usuario = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Criar nova empresa diretamente pelo SuperAdmin."""
    existing_email = await db.execute(select(Usuario).where(Usuario.email == data.admin_email.lower()))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email ja cadastrado")

    base_slug = slugify(data.nome)
    slug = base_slug
    counter = 1
    while True:
        ex = await db.execute(select(Empresa).where(Empresa.slug == slug))
        if not ex.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    empresa = Empresa(
        nome=data.nome, cnpj=data.cnpj, slug=slug,
        plano=data.plano, max_leituristas=data.max_leituristas,
        percentual_esgoto=data.percentual_esgoto,
        consumo_minimo_m3=data.consumo_minimo_m3,
        logo_url=data.logo_url,
    )
    db.add(empresa)
    await db.flush()

    admin = Usuario(
        empresa_id=empresa.id, nome=data.admin_nome,
        email=data.admin_email.lower(),
        senha_hash=hash_password(data.admin_senha),
        role="supervisor",  # Corrigido: admin -> supervisor
    )
    db.add(admin)
    return {"detail": f"Empresa '{data.nome}' criada com sucesso!", "empresa_id": empresa.id}


@router.put("/empresas/{emp_id}/status")
async def toggle_empresa_status(
    emp_id: int,
    ativa: bool,
    current_user: Usuario = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Ativar ou desativar uma empresa cliente."""
    result = await db.execute(select(Empresa).where(Empresa.id == emp_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")
    empresa.ativa = ativa
    return {"detail": f"Empresa {'ativada' if ativa else 'bloqueada'} com sucesso"}


@router.put("/empresas/{emp_id}/config")
async def update_empresa_config(
    emp_id: int,
    data: AtualizarEmpresaRequest,
    current_user: Usuario = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Atualizar configuracoes de uma empresa (plano, limites, esgoto, consumo minimo)."""
    result = await db.execute(select(Empresa).where(Empresa.id == emp_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")
    if data.plano is not None:
        empresa.plano = data.plano
    if data.max_leituristas is not None:
        empresa.max_leituristas = data.max_leituristas
    if data.percentual_esgoto is not None:
        empresa.percentual_esgoto = data.percentual_esgoto
    if data.consumo_minimo_m3 is not None:
        empresa.consumo_minimo_m3 = data.consumo_minimo_m3
    if data.logo_url is not None:
        empresa.logo_url = data.logo_url
    return {"detail": "Empresa atualizada com sucesso"}


@router.get("/empresas/{emp_id}/usuarios", response_model=List[UsuarioSuperOut])
async def get_usuarios_empresa(
    emp_id: int,
    current_user: Usuario = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Listar usuarios de uma empresa especifica."""
    result = await db.execute(
        select(Usuario).where(Usuario.empresa_id == emp_id).order_by(Usuario.created_at.desc())
    )
    return [UsuarioSuperOut.model_validate(u) for u in result.scalars().all()]


@router.get("/audit", response_model=List[AuditLogOut])
async def get_audit_global(
    limit: int = Query(50, ge=1, le=200),
    current_user: Usuario = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Ultimas acoes na plataforma (audit log global)."""
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    return [AuditLogOut.model_validate(a) for a in result.scalars().all()]


# ─── RESET DE SENHA ─────────────────────────────────────────────────────────

class ResetSenhaAdmin(BaseModel):
    nova_senha: str


@router.post("/usuarios/{user_id}/reset-senha")
async def superadmin_reset_senha(
    user_id: int,
    data: ResetSenhaAdmin,
    current_user: Usuario = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """SuperAdmin reseta senha de qualquer usuario da plataforma."""
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    if len(data.nova_senha) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 6 caracteres")
    usuario.senha_hash = hash_password(data.nova_senha)
    return {"detail": f"Senha de {usuario.nome} ({usuario.email}) redefinida com sucesso"}


@router.get("/usuarios", response_model=List[UsuarioSuperOut])
async def listar_todos_usuarios(
    empresa_id: Optional[int] = None,
    role: Optional[str] = None,
    current_user: Usuario = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Listar todos os usuarios da plataforma com filtros opcionais."""
    query = select(Usuario).order_by(Usuario.empresa_id, Usuario.nome)
    if empresa_id:
        query = query.where(Usuario.empresa_id == empresa_id)
    if role:
        query = query.where(Usuario.role == role)
    result = await db.execute(query)
    return [UsuarioSuperOut.model_validate(u) for u in result.scalars().all()]


@router.put("/usuarios/{user_id}/toggle")
async def toggle_usuario(
    user_id: int,
    current_user: Usuario = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Ativar ou desativar qualquer usuario da plataforma."""
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    if usuario.role == "superadmin":
        raise HTTPException(status_code=403, detail="Nao e possivel desativar o superadmin")
    usuario.ativo = not usuario.ativo
    status_str = "ativado" if usuario.ativo else "desativado"
    return {"detail": f"Usuario {usuario.nome} {status_str}", "ativo": usuario.ativo}

