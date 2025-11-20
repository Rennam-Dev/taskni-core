"""
Aplicação principal do Taskni Core.

Cria o app FastAPI e integra com o Agent Service Toolkit.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from taskni_core.agents.registry import register_taskni_agents
from taskni_core.api.routes_agents import router as agents_router
from taskni_core.api.routes_health import router as health_router
from taskni_core.api.routes_rag import router as rag_router
from taskni_core.core.settings import taskni_settings
from taskni_core.utils.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from taskni_core.utils.auth import AuthManager

logger = logging.getLogger(__name__)

# Inicializa o rate limiter
# Usa IP do cliente como chave para limitar requests por IP
limiter = Limiter(key_func=get_remote_address)

# Inicializa o gerenciador de autenticação
# Obtém tokens do .env de forma segura
api_token = taskni_settings.API_TOKEN.get_secret_value() if taskni_settings.API_TOKEN else None
api_tokens = taskni_settings.API_TOKENS.get_secret_value() if taskni_settings.API_TOKENS else None
auth_manager = AuthManager(api_token=api_token, api_tokens=api_tokens)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.

    Executa na inicialização e shutdown.
    """
    # Startup
    print("🚀 Iniciando Taskni Core...")

    # Registra os agentes do Taskni
    register_taskni_agents()
    print("✅ Agentes Taskni registrados")

    yield

    # Shutdown
    print("👋 Encerrando Taskni Core...")


def create_app() -> FastAPI:
    """
    Cria e configura a aplicação FastAPI.

    Returns:
        Aplicação FastAPI configurada
    """
    app = FastAPI(
        title="Taskni Core API",
        version="0.1.0",
        description=(
            "Motor de agentes para clínicas e pequenos negócios. "
            "Integra LangGraph, Evolution API, Chatwoot, n8n e mais."
        ),
        lifespan=lifespan,
    )

    # Configura Rate Limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("✅ Rate limiting configurado")

    # Configura Exception Handlers (previne exposição de erros internos)
    # IMPORTANTE: A ordem importa! Handlers mais específicos primeiro.
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)  # Catch-all
    logger.info("✅ Exception handlers configurados (erros internos protegidos)")

    # Configuração CORS segura
    # IMPORTANTE: allow_origins=["*"] com allow_credentials=True é MUITO PERIGOSO!
    # Sempre use uma whitelist específica de origens permitidas.
    import os

    cors_origins_env = os.getenv("CORS_ORIGINS", "")

    if cors_origins_env:
        # Produção: use lista específica do .env
        cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
        logger.info(f"✅ CORS configurado com whitelist: {cors_origins}")
    else:
        # Desenvolvimento: apenas localhost
        cors_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8501",  # Streamlit
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8501",
        ]
        logger.warning(
            "⚠️  CORS usando origens localhost padrão. Configure CORS_ORIGINS no .env para produção!"
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,  # Lista específica, NUNCA ["*"]
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
        max_age=3600,
    )

    # Disponibiliza auth_manager para os routers
    # Pode ser acessado via request.app.state.auth
    app.state.auth = auth_manager

    # Inclui as rotas do Taskni Core
    # /health é público (para health checks de load balancers)
    app.include_router(
        health_router,
        prefix="/health",
        tags=["health"],
    )

    # /agents e /rag são protegidos (requerem Bearer token se configurado)
    from fastapi import Depends

    auth_dependency = [Depends(auth_manager.require_auth)]

    app.include_router(
        agents_router,
        prefix="/agents",
        tags=["agents"],
        dependencies=auth_dependency,  # Protege todos os endpoints
    )

    app.include_router(
        rag_router,
        prefix="/rag",
        tags=["rag"],
        dependencies=auth_dependency,  # Protege todos os endpoints
    )

    # TODO: Adicionar rotas de CRM quando implementar
    # app.include_router(
    #     crm_router,
    #     prefix="/crm",
    #     tags=["crm"],
    # )

    @app.get("/")
    async def root():
        """Endpoint raiz com informações do serviço."""
        return {
            "service": "taskni-core",
            "version": "0.1.0",
            "description": "Motor de agentes para clínicas e negócios",
            "docs": "/docs",
            "health": "/health",
        }

    return app


# Cria a aplicação
app = create_app()


# ===================================================================
# Para compatibilidade com o toolkit original
# ===================================================================
# Se você quiser rodar o Taskni Core junto com as rotas do toolkit,
# pode importar e incluir o service original aqui:
#
# from service.service import create_app as create_toolkit_app
# toolkit_app = create_toolkit_app()
# app.mount("/toolkit", toolkit_app)
#
# Assim você teria:
# - /agents/* - rotas do Taskni Core
# - /toolkit/chatbot/* - rotas do toolkit original
