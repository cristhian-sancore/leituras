from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer,
    Numeric, String, Text, func, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class LayoutImpressao(Base):
    __tablename__ = "layout_impressao"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nome = Column(Text, nullable=False, unique=True)
    conteudo_cpcl = Column(Text, nullable=False) # JSON gerado pelo canvas ou string CPCL raw
    tipo_impressora = Column(Text, nullable=False, default="ZQ520")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nome = Column(Text, nullable=False)
    cnpj = Column(Text, unique=True, nullable=True)
    slug = Column(Text, unique=True, nullable=False)
    logo_url = Column(Text, nullable=True)
    ativa = Column(Boolean, nullable=False, default=True)
    plano = Column(Text, nullable=False, default="basico")
    max_leituristas = Column(Integer, nullable=False, default=5)
    percentual_esgoto = Column(Numeric(5, 2), nullable=False, default=70.00)
    consumo_minimo_m3 = Column(Integer, nullable=False, default=10)
    layout_impressao_id = Column(BigInteger, ForeignKey("layout_impressao.id", ondelete="SET NULL"), nullable=True)
    layout_notificacao_id = Column(BigInteger, ForeignKey("layout_impressao.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    importacoes = relationship("Importacao", back_populates="empresa", cascade="all, delete-orphan")
    layout_impressao = relationship("LayoutImpressao", foreign_keys=[layout_impressao_id])
    layout_notificacao = relationship("LayoutImpressao", foreign_keys=[layout_notificacao_id])


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id", ondelete="CASCADE"), nullable=True)  # null = superadmin
    nome = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    senha_hash = Column(Text, nullable=False)
    role = Column(Text, nullable=False, default="leiturista")
    ativo = Column(Boolean, nullable=False, default=True)
    ultimo_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_usuario_empresa", "empresa_id"),
    )

    empresa = relationship("Empresa", back_populates="usuarios")


class Importacao(Base):
    __tablename__ = "importacoes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(BigInteger, ForeignKey("usuarios.id"), nullable=False)
    nome_arquivo = Column(Text, nullable=False)
    data_importacao = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    total_clientes = Column(Integer, nullable=False, default=0)
    status = Column(Text, nullable=False, default="ativo")
    mes_referencia = Column(Text, nullable=True)
    desc_agua = Column(Text, nullable=True, default="FORNECIMENTO DE AGUA")
    desc_esgoto = Column(Text, nullable=True, default="ESGOTO")
    desc_lixo = Column(Text, nullable=True, default="TAXA DE LIXO")

    __table_args__ = (
        Index("ix_importacao_empresa_status", "empresa_id", "status"),
    )

    empresa = relationship("Empresa", back_populates="importacoes")
    usuario = relationship("Usuario")
    tarifas = relationship("Tarifa", back_populates="importacao", cascade="all, delete-orphan")
    ocorrencias = relationship("Ocorrencia", back_populates="importacao", cascade="all, delete-orphan")
    clientes = relationship("Cliente", back_populates="importacao", cascade="all, delete-orphan")
    leituras = relationship("Leitura", back_populates="importacao", cascade="all, delete-orphan")


class Tarifa(Base):
    __tablename__ = "tarifas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    importacao_id = Column(BigInteger, ForeignKey("importacoes.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False)
    categoria = Column(Text, nullable=False)
    servico = Column(Text, nullable=False)
    faixa = Column(Integer, nullable=False)
    valor_minimo = Column(Numeric(12, 2), nullable=True)
    limite_metros = Column(Numeric(10, 2), nullable=True)
    preco_metro = Column(Numeric(10, 5), nullable=True)

    __table_args__ = (
        Index("ix_tarifa_importacao", "importacao_id"),
    )

    importacao = relationship("Importacao", back_populates="tarifas")


class Ocorrencia(Base):
    __tablename__ = "ocorrencias"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    importacao_id = Column(BigInteger, ForeignKey("importacoes.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False)
    codigo = Column(Text, nullable=False)
    descricao = Column(Text, nullable=False)
    tipo_acao = Column(Text, nullable=True)
    consumo_fixo = Column(Integer, default=0)
    desconsidera_leitura = Column(Boolean, default=False)

    importacao = relationship("Importacao", back_populates="ocorrencias")


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    importacao_id = Column(BigInteger, ForeignKey("importacoes.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False)
    matricula = Column(Text, nullable=False)
    codigo_full = Column(Text, nullable=False)
    nome = Column(Text, nullable=False)
    categoria = Column(Text, nullable=False)
    leitura_anterior = Column(Integer, default=0)
    consumo_medio = Column(Integer, default=0)
    rua = Column(Text, nullable=True)
    numero = Column(Text, nullable=True)
    bairro = Column(Text, nullable=True)
    zona = Column(Text, nullable=True)
    rota = Column(Text, nullable=True)
    sequencia = Column(Text, nullable=True)
    tipo_servico = Column(Text, default="02")
    num_fatura = Column(Text, nullable=True)
    data_vencimento = Column(Text, nullable=True)
    mes_ano_ref = Column(Text, nullable=True)
    data_leit_anterior = Column(Text, nullable=True)
    ocorr_anterior = Column(Text, nullable=True)
    # Atribuição: qual leiturista vai fazer a leitura deste cliente
    leiturista_atribuido_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    # Flags de servico lidos do arquivo .REM por cliente
    # tem_esgoto=False => instalacao "SO AGUA" (sem cobranca de esgoto)
    # tem_lixo=False   => sem taxa de lixo (sem A12 de lixo para este cliente)
    tem_esgoto = Column(Boolean, default=True, nullable=False, server_default='true')
    tem_lixo   = Column(Boolean, default=True, nullable=False, server_default='true')

    # Novos campos de metadados e impressão
    hidrometro = Column(Text, nullable=True)
    vazao = Column(Text, nullable=True)
    diametro = Column(Text, nullable=True)
    data_instalacao = Column(Text, nullable=True)
    endereco_entrega = Column(Text, nullable=True)
    cep = Column(Text, nullable=True)
    codigo_barras = Column(String(44), nullable=True)

    __table_args__ = (
        Index("ix_cliente_importacao", "importacao_id"),
        Index("ix_cliente_empresa", "empresa_id"),
        Index("ix_cliente_matricula", "matricula"),
        Index("ix_cliente_rota", "rota"),
        Index("ix_cliente_leiturista", "leiturista_atribuido_id"),
    )

    importacao = relationship("Importacao", back_populates="clientes")
    leitura = relationship("Leitura", back_populates="cliente", uselist=False)
    leiturista_atribuido = relationship("Usuario", foreign_keys=[leiturista_atribuido_id])


class Leitura(Base):
    __tablename__ = "leituras"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    importacao_id = Column(BigInteger, ForeignKey("importacoes.id"), nullable=False)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False)
    leiturista_id = Column(BigInteger, ForeignKey("usuarios.id"), nullable=True)
    leitura_atual = Column(Integer, nullable=True)
    ocorrencia_codigo = Column(Text, nullable=True)
    consumo = Column(Integer, default=0)
    valor_agua = Column(Numeric(12, 2), default=0)
    valor_esgoto = Column(Numeric(12, 2), default=0)
    valor_lixo = Column(Numeric(12, 2), default=0)
    valor_total = Column(Numeric(12, 2), default=0)
    data_leitura = Column(DateTime(timezone=True), server_default=func.now())
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)

    __table_args__ = (
        UniqueConstraint("cliente_id", "importacao_id", name="uq_leitura_cliente_importacao"),
        Index("ix_leitura_importacao", "importacao_id"),
        Index("ix_leitura_empresa", "empresa_id"),
    )

    cliente = relationship("Cliente", back_populates="leitura")
    importacao = relationship("Importacao", back_populates="leituras")


class Exportacao(Base):
    __tablename__ = "exportacoes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    importacao_id = Column(BigInteger, ForeignKey("importacoes.id"), nullable=False)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False)
    usuario_id = Column(BigInteger, ForeignKey("usuarios.id"), nullable=False)
    nome_arquivo = Column(Text, nullable=False)
    total_registros = Column(Integer, nullable=False)
    data_exportacao = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=True)  # null = superadmin
    usuario_id = Column(BigInteger, ForeignKey("usuarios.id"), nullable=True)
    acao = Column(Text, nullable=False)
    detalhes = Column(JSONB, nullable=True)
    ip_address = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_audit_empresa", "empresa_id"),
    )
