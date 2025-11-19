"""
Aplicação principal do Taskni Core.

Cria o app FastAPI e integra com o Agent Service Toolkit.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from taskni_core.agents.registry import register_taskni_agents
from taskni_core.api.routes_agents import router as agents_router
from taskni_core.api.routes_health import router as health_router
from taskni_core.api.routes_rag import router as rag_router
from taskni_core.core.settings import taskni_settings


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

    # CORS (ajuste conforme necessário)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, especifique os domínios
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inclui as rotas do Taskni Core
    app.include_router(
        health_router,
        prefix="/health",
        tags=["health"],
    )

    app.include_router(
        agents_router,
        prefix="/agents",
        tags=["agents"],
    )

    app.include_router(
        rag_router,
        prefix="/rag",
        tags=["rag"],
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
