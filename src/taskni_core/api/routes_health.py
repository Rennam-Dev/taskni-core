"""
Rotas de health check.

Endpoint simples para verificar se o serviço está rodando.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Health check endpoint.

    Retorna status ok se o serviço está rodando.
    """
    return {
        "status": "ok",
        "service": "taskni-core",
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Verifica se o serviço está pronto para receber requisições.
    Pode incluir checagens de banco de dados, etc.
    """
    # TODO: Adicionar checagens de dependências (DB, APIs externas, etc)
    return {
        "status": "ready",
        "service": "taskni-core",
    }
