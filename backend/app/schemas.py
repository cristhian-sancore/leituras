from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================
# AUTH
# ============================================

class EmpresaRegister(BaseModel):
    nome: str = Field(..., min_length=2, max_length=200)
    cnpj: Optional[str] = None
    admin_nome: str = Field(..., min_length=2, max_length=100)
    admin_email: str = Field(..., min_length=5, max_length=200)
    admin_senha: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    email: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UsuarioOut"


class RefreshRequest(BaseModel):
    refresh_token: str


# ============================================
# EMPRESA
# ============================================

class EmpresaOut(BaseModel):
    id: int
    nome: str
    cnpj: Optional[str] = None
    slug: str
    ativa: bool
    plano: str
    max_leituristas: int
    created_at: datetime

    class Config:
        from_attributes = True


class EmpresaUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None


# ============================================
# USUARIO
# ============================================

class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=200)
    senha: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="leiturista", pattern="^(admin|supervisor|leiturista)$")


class UsuarioOut(BaseModel):
    id: int
    empresa_id: int
    nome: str
    email: str
    role: str
    ativo: bool
    ultimo_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    ativo: Optional[bool] = None


# ============================================
# IMPORTAÇÃO
# ============================================

class ImportacaoOut(BaseModel):
    id: int
    nome_arquivo: str
    data_importacao: datetime
    total_clientes: int
    status: str
    mes_referencia: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# LEITURA
# ============================================

class ClienteComLeitura(BaseModel):
    id: int
    matricula: str
    nome: str
    categoria: str
    leitura_anterior: int
    consumo_medio: int
    rua: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    zona: Optional[str] = None
    rota: Optional[str] = None
    sequencia: Optional[str] = None
    # Dados da leitura (se existir)
    leitura_atual: Optional[int] = None
    ocorrencia_codigo: Optional[str] = None
    consumo: int = 0
    valor_total: float = 0.0

    class Config:
        from_attributes = True


class LeituraUpdate(BaseModel):
    leitura_atual: Optional[int] = None
    ocorrencia_codigo: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LeituraBatch(BaseModel):
    leituras: List[LeituraUpdate]
    cliente_ids: List[int]


class StatsOut(BaseModel):
    total_clientes: int = 0
    leituras_realizadas: int = 0
    leituras_pendentes: int = 0
    consumo_total: int = 0
    valor_total: float = 0.0


# ============================================
# OCORRENCIA
# ============================================

class OcorrenciaOut(BaseModel):
    codigo: str
    descricao: str
    tipo_acao: Optional[str] = None
    consumo_fixo: int = 0
    desconsidera_leitura: bool = False

    class Config:
        from_attributes = True


# ============================================
# TARIFA
# ============================================

class TarifaOut(BaseModel):
    categoria: str
    servico: str
    faixa: int
    valor_minimo: Optional[float] = None
    limite_metros: Optional[float] = None
    preco_metro: Optional[float] = None

    class Config:
        from_attributes = True


# ============================================
# DASHBOARD
# ============================================

class DashboardResumo(BaseModel):
    total_importacoes: int = 0
    importacao_ativa: Optional[ImportacaoOut] = None
    total_usuarios: int = 0
    stats: Optional[StatsOut] = None


class ProgressoRota(BaseModel):
    rota: str
    total: int
    realizadas: int
    pendentes: int
    percentual: float


# ============================================
# EXPORTAÇÃO
# ============================================

class ExportacaoOut(BaseModel):
    id: int
    nome_arquivo: str
    total_registros: int
    data_exportacao: datetime

    class Config:
        from_attributes = True


# Resolve forward reference
TokenResponse.model_rebuild()
