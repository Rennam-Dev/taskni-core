"""
Error handling utilities para prevenir exposição de informações sensíveis.

Este módulo previne vazamento de stacktraces e informações internas
em respostas de erro da API.
"""

import logging
import traceback
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class SafeErrorResponse:
    """
    Cria respostas de erro seguras que não expõem detalhes internos.
    """

    # Mensagens genéricas por tipo de erro
    GENERIC_MESSAGES = {
        400: "Requisição inválida. Verifique os dados enviados.",
        401: "Autenticação necessária.",
        403: "Acesso negado.",
        404: "Recurso não encontrado.",
        422: "Dados de entrada inválidos.",
        429: "Muitas requisições. Tente novamente mais tarde.",
        500: "Erro interno do servidor. Nossa equipe foi notificada.",
        502: "Serviço temporariamente indisponível.",
        503: "Serviço em manutenção.",
    }

    @staticmethod
    def create_error_response(
        status_code: int,
        public_message: str | None = None,
        internal_details: str | None = None,
        error_code: str | None = None,
    ) -> dict[str, Any]:
        """
        Cria um dicionário de resposta de erro seguro.

        Args:
            status_code: Código HTTP do erro
            public_message: Mensagem para o cliente (opcional)
            internal_details: Detalhes internos (apenas logados, não retornados)
            error_code: Código de erro customizado (opcional)

        Returns:
            Dict com campos de erro seguros
        """
        # Loga detalhes internos (stacktrace, etc) no servidor
        if internal_details:
            logger.error(
                f"Error {status_code}: {internal_details}",
                extra={"status_code": status_code, "error_code": error_code}
            )

        # Mensagem pública (genérica se não fornecida)
        if not public_message:
            public_message = SafeErrorResponse.GENERIC_MESSAGES.get(
                status_code,
                "Erro ao processar requisição."
            )

        # Resposta para o cliente (SEM detalhes internos)
        response = {
            "error": True,
            "message": public_message,
            "status_code": status_code,
        }

        # Adiciona código de erro se fornecido
        if error_code:
            response["error_code"] = error_code

        return response


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handler para HTTPException do Starlette/FastAPI.

    Args:
        request: Request do FastAPI
        exc: Exceção HTTP

    Returns:
        JSONResponse com erro seguro
    """
    # Loga a exceção com contexto
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        }
    )

    # Para erros 4xx, pode retornar a mensagem original (geralmente segura)
    # Para erros 5xx, usa mensagem genérica
    if exc.status_code < 500:
        public_message = str(exc.detail)
    else:
        public_message = None  # Usa mensagem genérica

    response_data = SafeErrorResponse.create_error_response(
        status_code=exc.status_code,
        public_message=public_message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handler para erros de validação Pydantic.

    Args:
        request: Request do FastAPI
        exc: Exceção de validação

    Returns:
        JSONResponse com detalhes de validação (seguros de expor)
    """
    # Loga erro de validação
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        }
    )

    # Erros de validação são seguros de expor (não contêm lógica interna)
    response_data = {
        "error": True,
        "message": "Dados de entrada inválidos.",
        "status_code": 422,
        "validation_errors": exc.errors(),
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data,
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handler genérico para exceções não tratadas.

    IMPORTANTE: Este é o handler mais crítico para segurança!
    Previne vazamento de stacktraces e detalhes internos.

    Args:
        request: Request do FastAPI
        exc: Exceção genérica

    Returns:
        JSONResponse com erro genérico seguro
    """
    # Captura stacktrace completo
    tb = traceback.format_exc()

    # Loga TUDO internamente (stacktrace completo, variáveis, etc)
    logger.error(
        f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": exc.__class__.__name__,
            "exception_message": str(exc),
        }
    )
    logger.debug(f"Stacktrace:\n{tb}")  # Debug level para stacktrace completo

    # Retorna APENAS mensagem genérica para o cliente
    # NUNCA retorna: stacktrace, nomes de variáveis, paths internos, etc
    response_data = SafeErrorResponse.create_error_response(
        status_code=500,
        public_message=None,  # Usa mensagem genérica
        internal_details=f"{exc.__class__.__name__}: {str(exc)}\n{tb}",
        error_code="INTERNAL_ERROR",
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data,
    )


def safe_str_exception(exc: Exception, max_length: int = 200) -> str:
    """
    Converte exceção para string segura (sem detalhes internos).

    Args:
        exc: Exceção a ser convertida
        max_length: Tamanho máximo da mensagem

    Returns:
        String segura da exceção
    """
    import re

    exc_type = exc.__class__.__name__
    exc_str = str(exc)

    # Remove paths de arquivo (stacktrace format): File "/path/to/file.py"
    exc_str = re.sub(r'File ".*?"', 'File "<internal>"', exc_str)

    # Remove paths absolutos Unix/Linux: /home/user/... ou /usr/local/...
    exc_str = re.sub(r'/[\w\-./]+', '<path>', exc_str)

    # Remove paths absolutos Windows: C:\Users\... ou C:/Users/...
    exc_str = re.sub(r'[A-Za-z]:[/\\][\w\-./\\]+', '<path>', exc_str)

    # Limita tamanho
    if len(exc_str) > max_length:
        exc_str = exc_str[:max_length] + "..."

    return f"{exc_type}: {exc_str}"
