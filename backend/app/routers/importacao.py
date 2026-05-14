from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..database import get_db
from ..models import Importacao, Tarifa, Ocorrencia, Cliente, Usuario, AuditLog
from ..schemas import ImportacaoOut
from ..auth.deps import get_current_user, require_role
from ..services.parser_rem import parse_rem




router = APIRouter(prefix="/importacao", tags=["Importação"])


@router.post("/upload", response_model=ImportacaoOut, status_code=201)
async def upload_rem(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(require_role("admin", "supervisor")),
    db: AsyncSession = Depends(get_db),
):
    """Upload e parse de arquivo .REM."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo não fornecido")

    # Limitar tamanho: 10MB máximo
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read(MAX_SIZE + 1)
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Máximo 10MB.")

    try:
        text = content.decode('latin-1')  # Arquivos .REM usam encoding latin-1
    except Exception:
        text = content.decode('utf-8', errors='ignore')

    # Parsear arquivo
    dados = parse_rem(text)

    if not dados['clientes']:
        raise HTTPException(status_code=400, detail="Nenhum cliente encontrado no arquivo")

    # Detectar mês referência do primeiro cliente
    mes_ref = None
    if dados['clientes']:
        mes_ref = dados['clientes'][0].get('mes_ano_ref', '').strip() or None

    # Criar importação
    importacao = Importacao(
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        nome_arquivo=file.filename,
        total_clientes=len(dados['clientes']),
        status="ativo",
        mes_referencia=mes_ref,
        desc_agua=dados.get('desc_agua', 'FORNECIMENTO DE AGUA'),
        desc_esgoto=dados.get('desc_esgoto', 'ESGOTO'),
        desc_lixo=dados.get('desc_lixo', 'TAXA DE LIXO'),
    )
    db.add(importacao)
    await db.flush()  # garante que importacao.id seja gerado

    # Salvar tarifas
    for t in dados['tarifas']:
        db.add(Tarifa(
            importacao_id=importacao.id,
            empresa_id=current_user.empresa_id,
            **t,
        ))

    # Salvar ocorrências
    for o in dados['ocorrencias']:
        db.add(Ocorrencia(
            importacao_id=importacao.id,
            empresa_id=current_user.empresa_id,
            **o,
        ))

    # Salvar clientes
    for c in dados['clientes']:
        db.add(Cliente(
            importacao_id=importacao.id,
            empresa_id=current_user.empresa_id,
            **c,
        ))

    # Audit
    db.add(AuditLog(
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        acao="upload_rem",
        detalhes={
            "arquivo": file.filename,
            "clientes": len(dados['clientes']),
            "tarifas": len(dados['tarifas']),
            "ocorrencias": len(dados['ocorrencias']),
        },
    ))

    # Commit explícito ANTES de retornar — o frontend faz nova requisição
    # imediatamente após receber a resposta e precisa encontrar os dados no banco.
    await db.commit()
    await db.refresh(importacao)

    return ImportacaoOut.model_validate(importacao)


@router.get("/", response_model=List[ImportacaoOut])
async def list_importacoes(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Listar todas as importações da empresa."""
    result = await db.execute(
        select(Importacao)
        .where(Importacao.empresa_id == current_user.empresa_id)
        .order_by(Importacao.data_importacao.desc())
    )
    return [ImportacaoOut.model_validate(i) for i in result.scalars().all()]


@router.get("/{imp_id}", response_model=ImportacaoOut)
async def get_importacao(
    imp_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Detalhes de uma importação."""
    result = await db.execute(
        select(Importacao).where(
            Importacao.id == imp_id,
            Importacao.empresa_id == current_user.empresa_id,
        )
    )
    imp = result.scalar_one_or_none()
    if not imp:
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    return ImportacaoOut.model_validate(imp)


@router.put("/{imp_id}/status")
async def update_status(
    imp_id: int,
    status: str,
    current_user: Usuario = Depends(require_role("admin", "supervisor")),
    db: AsyncSession = Depends(get_db),
):
    """Mudar status de uma importação."""
    if status not in ('ativo', 'em_andamento', 'finalizado', 'cancelado'):
        raise HTTPException(status_code=400, detail="Status inválido")

    result = await db.execute(
        select(Importacao).where(
            Importacao.id == imp_id,
            Importacao.empresa_id == current_user.empresa_id,
        )
    )
    imp = result.scalar_one_or_none()
    if not imp:
        raise HTTPException(status_code=404, detail="Importação não encontrada")

    imp.status = status
    await db.commit()
    return {"detail": f"Status atualizado para {status}"}
