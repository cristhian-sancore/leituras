import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Empresa, Usuario, LayoutImpressao
from app.schemas import EmpresaOut, EmpresaUpdate, EmpresaConfigUpdate
from app.auth.deps import get_current_user, require_role
from app.config import get_settings
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/empresa", tags=["Empresa"])
settings = get_settings()


class EmpresaPublicOut(BaseModel):
    nome: str
    slug: str
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/public/{slug}", response_model=EmpresaPublicOut)
async def get_empresa_publica(slug: str, db: AsyncSession = Depends(get_db)):
    """Endpoint publico - retorna nome e logo da empresa pelo slug (sem autenticacao)."""
    result = await db.execute(select(Empresa).where(Empresa.slug == slug, Empresa.ativa == True))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")
    return EmpresaPublicOut(nome=empresa.nome, slug=empresa.slug, logo_url=empresa.logo_url)


@router.get("/", response_model=EmpresaOut)
async def get_empresa(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna dados da empresa do usuario logado."""
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")
    return EmpresaOut.model_validate(empresa)


@router.get("/layout")
async def get_empresa_layout(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna o conteúdo CPCL e tipo da impressora do layout configurado para a empresa logada. Caso não tenha, retorna erro 404."""
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa or not empresa.layout_impressao_id:
        raise HTTPException(status_code=404, detail="Nenhum layout customizado")
        
    res_layout = await db.execute(select(LayoutImpressao).where(LayoutImpressao.id == empresa.layout_impressao_id))
    layout = res_layout.scalar_one_or_none()
    
    if not layout:
        raise HTTPException(status_code=404, detail="Layout não encontrado")
        
    return {
        "conteudo_cpcl": layout.conteudo_cpcl,
        "tipo_impressora": layout.tipo_impressora
    }


@router.put("/", response_model=EmpresaOut)
async def update_empresa(
    data: EmpresaUpdate,
    current_user: Usuario = Depends(require_role("supervisor", "superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Atualizar dados da empresa do usuário logado (supervisor) ou 404 para superadmin sem empresa."""
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada. Superadmin deve usar /superadmin/empresas/{id}/config")
    if data.nome is not None:
        empresa.nome = data.nome
    if data.cnpj is not None:
        empresa.cnpj = data.cnpj
    return EmpresaOut.model_validate(empresa)


@router.put("/config", response_model=EmpresaOut)
async def update_empresa_config(
    data: EmpresaConfigUpdate,
    current_user: Usuario = Depends(require_role("supervisor", "superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Atualizar configuracoes da empresa (supervisor)."""
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")
    
    if data.percentual_esgoto is not None:
        empresa.percentual_esgoto = data.percentual_esgoto
    if data.consumo_minimo_m3 is not None:
        empresa.consumo_minimo_m3 = data.consumo_minimo_m3
        
    return EmpresaOut.model_validate(empresa)


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(require_role("supervisor", "superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Upload de logo da empresa (PNG/JPG, max 2MB)."""
    # Validar tipo
    if file.content_type not in ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/svg+xml"):
        raise HTTPException(status_code=400, detail="Formato invalido. Use PNG, JPG, WEBP ou SVG.")

    # Validar tamanho (2MB)
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Maximo 2MB.")

    # Salvar no volume de uploads
    ext = file.filename.split(".")[-1].lower()
    filename = f"logo_{current_user.empresa_id}_{uuid.uuid4().hex[:8]}.{ext}"
    upload_path = os.path.join(settings.UPLOAD_DIR, "logos")
    os.makedirs(upload_path, exist_ok=True)
    filepath = os.path.join(upload_path, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    # Atualizar empresa
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada. Superadmin deve usar /superadmin/empresas/{id}/config")
    empresa.logo_url = f"/uploads/logos/{filename}"

    return {"logo_url": empresa.logo_url, "detail": "Logo atualizada com sucesso!"}


@router.put("/logo-url")
async def set_logo_url(
    logo_url: str,
    current_user: Usuario = Depends(require_role("supervisor", "superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Definir logo da empresa por URL externa."""
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")
    empresa.logo_url = logo_url
    return {"logo_url": logo_url, "detail": "Logo atualizada!"}
