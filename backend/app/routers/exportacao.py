from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Cliente, Leitura, Importacao, Exportacao, Usuario, AuditLog
from app.schemas import ExportacaoOut
from app.auth.deps import get_current_user, require_role
from app.services.gerador_ret import gerar_arquivo_ret
from datetime import datetime

router = APIRouter(prefix="/exportacao", tags=["Exportação"])


@router.post("/{imp_id}/ret")
async def gerar_ret(
    imp_id: int,
    current_user: Usuario = Depends(require_role("admin", "supervisor")),
    db: AsyncSession = Depends(get_db),
):
    """Gerar e retornar arquivo .RET para download."""
    # Verificar importação
    result = await db.execute(
        select(Importacao).where(
            Importacao.id == imp_id,
            Importacao.empresa_id == current_user.empresa_id,
        )
    )
    imp = result.scalar_one_or_none()
    if not imp:
        raise HTTPException(status_code=404, detail="Importação não encontrada")

    # Buscar clientes com leituras
    result = await db.execute(
        select(Cliente).where(
            Cliente.importacao_id == imp_id,
            Cliente.empresa_id == current_user.empresa_id,
        )
    )
    clientes = result.scalars().all()

    result = await db.execute(
        select(Leitura).where(
            Leitura.importacao_id == imp_id,
            Leitura.empresa_id == current_user.empresa_id,
            # Incluir: leituras com valor numérico OU com ocorrência especial (≠ 0000)
            # Ocorrência especial = leiturista registrou impedimento sem poder ler o hidrômetro
            (
                Leitura.leitura_atual.isnot(None) |
                (
                    Leitura.ocorrencia_codigo.isnot(None) &
                    (Leitura.ocorrencia_codigo != '0000')
                )
            ),
        )
    )
    leituras = result.scalars().all()
    leituras_map = {l.cliente_id: l for l in leituras}

    if not leituras:
        raise HTTPException(status_code=400, detail="Nenhuma leitura realizada")

    # Montar dados para gerar arquivo
    clientes_leituras = []
    for c in clientes:
        leitura = leituras_map.get(c.id)
        if leitura:
            clientes_leituras.append({
                'cliente': {
                    'codigo_full': c.codigo_full,
                    'zona': c.zona,
                    'rota': c.rota,
                    'sequencia': c.sequencia,
                    'mes_ano_ref': c.mes_ano_ref,
                    'num_fatura': c.num_fatura,
                    'data_vencimento': c.data_vencimento,
                },
                'leitura': {
                    'leitura_atual': leitura.leitura_atual,
                    'consumo': leitura.consumo,
                    'valor_agua': float(leitura.valor_agua or 0),
                    'valor_esgoto': float(leitura.valor_esgoto or 0),
                    'valor_total': float(leitura.valor_total or 0),
                    'ocorrencia_codigo': leitura.ocorrencia_codigo,
                },
            })

    conteudo = gerar_arquivo_ret(clientes_leituras)

    # Registrar exportação
    agora = datetime.now()
    nome_arquivo = f"RETORNO_{agora.strftime('%d%m%Y_%H%M%S')}.RET"

    exportacao = Exportacao(
        importacao_id=imp_id,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        nome_arquivo=nome_arquivo,
        total_registros=len(clientes_leituras),
    )
    db.add(exportacao)

    # Audit
    db.add(AuditLog(
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        acao="exportar_ret",
        detalhes={"arquivo": nome_arquivo, "registros": len(clientes_leituras)},
    ))

    return PlainTextResponse(
        content=conteudo,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{nome_arquivo}"',
        },
    )


@router.get("/historico", response_model=List[ExportacaoOut])
async def historico_exportacoes(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Histórico de exportações da empresa."""
    result = await db.execute(
        select(Exportacao)
        .where(Exportacao.empresa_id == current_user.empresa_id)
        .order_by(Exportacao.data_exportacao.desc())
    )
    return [ExportacaoOut.model_validate(e) for e in result.scalars().all()]
