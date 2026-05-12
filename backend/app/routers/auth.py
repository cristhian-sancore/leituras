import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from app.database import get_db
from app.models import Empresa, Usuario, AuditLog
from app.schemas import EmpresaRegister, LoginRequest, TokenResponse, RefreshRequest, UsuarioOut
from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# ============================================
# RATE LIMITING (em memória - simples e eficaz)
# ============================================
_login_attempts = defaultdict(list)  # ip -> [timestamps]
RATE_LIMIT_WINDOW = 900   # 15 minutos (Aumentado para segurança)
RATE_LIMIT_MAX = 5        # máximo 5 tentativas por janela (Reduzido para segurança)


def _check_rate_limit(ip: str):
    """Verifica se o IP excedeu o limite de tentativas de login."""
    now = time.time()
    # Limpar tentativas antigas
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_login_attempts[ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"Muitas tentativas de login. Tente novamente em {RATE_LIMIT_WINDOW // 60} minutos."
        )
    _login_attempts[ip].append(now)


def slugify(text: str) -> str:
    """Gera slug URL-friendly a partir do nome."""
    text = text.lower().strip()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'[\\s]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


@router.post("/register", status_code=403)
async def register_blocked():
    """Registro publico desativado. Empresas sao criadas pelo SuperAdmin."""
    raise HTTPException(
        status_code=403,
        detail="Cadastro publico desativado. Contate o administrador do sistema SAEMI."
    )



@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Login com email e senha (rate limited)."""
    # Rate limiting por IP
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    result = await db.execute(select(Usuario).where(Usuario.email == data.email.lower()))
    usuario = result.scalar_one_or_none()

    if not usuario or not verify_password(data.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário desativado")

    # Verificar se empresa está ativa (superadmin não tem empresa própria)
    if usuario.role != "superadmin":
        result_emp = await db.execute(select(Empresa).where(Empresa.id == usuario.empresa_id))
        empresa = result_emp.scalar_one_or_none()
        if not empresa or not empresa.ativa:
            raise HTTPException(status_code=403, detail="Empresa desativada")

    # Atualizar último login
    usuario.ultimo_login = datetime.now(timezone.utc)

    # Audit (superadmin tem empresa_id=None — registrar mesmo assim)
    db.add(AuditLog(
        empresa_id=usuario.empresa_id,  # None ok — coluna agora nullable
        usuario_id=usuario.id,
        acao="login",
        ip_address=client_ip,
    ))

    token_data = {"sub": str(usuario.id), "empresa_id": usuario.empresa_id, "role": usuario.role}
    access = create_access_token(token_data)
    refresh = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UsuarioOut.model_validate(usuario),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Renovar access token usando refresh token."""
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    user_id = payload.get("sub")
    result = await db.execute(select(Usuario).where(Usuario.id == int(user_id)))
    usuario = result.scalar_one_or_none()

    if not usuario or not usuario.ativo:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    # Verificar se empresa ainda está ativa (exceto superadmin)
    if usuario.role != "superadmin":
        result_emp = await db.execute(select(Empresa).where(Empresa.id == usuario.empresa_id))
        empresa = result_emp.scalar_one_or_none()
        if not empresa or not empresa.ativa:
            raise HTTPException(status_code=403, detail="Empresa desativada")

    token_data = {"sub": str(usuario.id), "empresa_id": usuario.empresa_id, "role": usuario.role}
    access = create_access_token(token_data)
    refresh = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UsuarioOut.model_validate(usuario),
    )


@router.get("/me", response_model=UsuarioOut)
async def me(current_user: Usuario = Depends(get_current_user)):
    """Retorna dados do usuário logado."""
    return UsuarioOut.model_validate(current_user)
