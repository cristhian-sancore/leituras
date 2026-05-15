from pydantic import BaseModel, Field, field_validator
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
    admin_senha: str = Field(..., min_length=8, max_length=100, description="Mínimo 8 caracteres com letras e números")

    @field_validator("admin_senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos um número")
        return v


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
    layout_impressao_id: Optional[int] = None
    layout_notificacao_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EmpresaUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None

class EmpresaConfigUpdate(BaseModel):
    percentual_esgoto: Optional[float] = None
    consumo_minimo_m3: Optional[int] = None
    layout_impressao_id: Optional[int] = None
    layout_notificacao_id: Optional[int] = None


# ============================================
# LAYOUT DE IMPRESSÃO
# ============================================

class LayoutImpressaoCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    conteudo_cpcl: str = Field(...)
    tipo_impressora: str = Field(default="ZQ520")

class LayoutImpressaoOut(BaseModel):
    id: int
    nome: str
    conteudo_cpcl: str
    tipo_impressora: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# USUARIO
# ============================================

class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=200)
    senha: str = Field(..., min_length=8, max_length=100, description="A senha deve ter no mínimo 8 caracteres, contendo pelo menos uma letra e um número.")
    role: str = Field(default="leiturista", pattern="^(supervisor|leiturista)$")

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos um número")
        return v


class UsuarioOut(BaseModel):
    id: int
    empresa_id: Optional[int] = None  # None para superadmin
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
    ativo: Optional[bool] = None
    # Nota: campo 'role' intencionalmente ausente — alteração de role
    # deve ser feita pelo superadmin via /superadmin/usuarios/{id}


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
    desc_agua: Optional[str] = None
    desc_esgoto: Optional[str] = None
    desc_lixo: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# LEITURA
# ============================================

class HistoricoItem(BaseModel):
    mes: str
    consumo: int
    dias: int = 30
    media: float


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
    cep: Optional[str] = None
    mes_ano_ref: Optional[str] = None
    data_vencimento: Optional[str] = None
    num_fatura: Optional[str] = None
    data_leit_anterior: Optional[str] = None
    ocorr_anterior: Optional[str] = None
    hidrometro: Optional[str] = None
    vazao: Optional[str] = None
    diametro: Optional[str] = None
    data_instalacao: Optional[str] = None
    endereco_entrega: Optional[str] = None
    codigo_barras: Optional[str] = None
    mensagem_1: Optional[str] = None
    mensagem_2: Optional[str] = None
    historico: List[HistoricoItem] = []
    # Dados da leitura (se existir)
    leitura_atual: Optional[int] = None
    ocorrencia_codigo: Optional[str] = None
    consumo: int = 0
    valor_agua: float = 0.0
    valor_esgoto: float = 0.0
    valor_lixo: float = 0.0
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
