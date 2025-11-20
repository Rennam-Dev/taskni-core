"""
Rotas para agentes.

Endpoints para listar, invocar e fazer stream de agentes.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from langgraph.graph.state import CompiledStateGraph
from slowapi import Limiter
from slowapi.util import get_remote_address

from taskni_core.agents.base import BaseAgent
from taskni_core.agents.registry import agent_registry
from taskni_core.schema.agent_io import (
    AgentInvokeRequest,
    AgentInvokeResponse,
    AgentListItem,
)
from taskni_core.utils.error_handler import safe_str_exception

logger = logging.getLogger(__name__)

router = APIRouter()

# Inicializa limiter (será injetado pelo app)
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=list[AgentListItem])
@limiter.limit("60/minute")  # 60 requests por minuto - menos crítico
async def list_agents(request: Request):
    """
    Lista todos os agentes disponíveis.

    Rate limit: 60 requests/minuto por IP

    Returns:
        Lista de agentes com seus metadados
    """
    agents = agent_registry.list_agents(include_disabled=False)
    return [AgentListItem(**agent) for agent in agents]


@router.post("/invoke", response_model=AgentInvokeResponse)
@limiter.limit("10/minute")  # 10 requests por minuto - CRÍTICO
async def invoke_agent(request: Request, payload: AgentInvokeRequest):
    """
    Invoca um agente com uma mensagem.

    Args:
        payload: Dados da requisição (agent_id, message, etc)

    Returns:
        Resposta do agente

    Raises:
        HTTPException: Se o agente não existe ou erro na execução
    """
    try:
        agent = agent_registry.get(payload.agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Prepara o contexto
    # Converte metadata tipado para dicionário (compatibilidade com agentes)
    context = {
        "user_id": payload.user_id,
        "session_id": payload.session_id,
        "thread_id": payload.thread_id,
        "metadata": payload.metadata.model_dump(exclude_none=True),
    }

    try:
        # Executa o agente baseado no tipo
        if isinstance(agent, BaseAgent):
            # Agente simples
            reply = await agent.run(
                message=payload.message,
                context=context,
            )
        else:
            # Agente LangGraph
            reply = await _invoke_langgraph_agent(
                agent=agent,
                message=payload.message,
                context=context,
            )

        # Cria resposta com metadata vazio (pode ser populado depois)
        from taskni_core.schema.metadata_schemas import ResponseMetadata

        return AgentInvokeResponse(
            agent_id=payload.agent_id,
            reply=reply,
            session_id=payload.session_id,
            thread_id=payload.thread_id,
            metadata=ResponseMetadata(),
        )

    except Exception as e:
        # Loga detalhes internos NO SERVIDOR (não expõe ao cliente)
        logger.error(
            f"Erro ao executar agente {payload.agent_id}: {safe_str_exception(e)}",
            extra={
                "agent_id": payload.agent_id,
                "user_id": payload.user_id,
                "error_type": e.__class__.__name__,
            },
        )
        # Retorna mensagem genérica ao cliente (sem detalhes internos)
        raise HTTPException(
            status_code=500,
            detail="Erro ao executar agente. Nossa equipe foi notificada.",
        )


async def _invoke_langgraph_agent(
    agent: CompiledStateGraph,
    message: str,
    context: Dict[str, Any],
) -> str:
    """
    Invoca um agente LangGraph.

    Args:
        agent: Agente compilado do LangGraph
        message: Mensagem do usuário
        context: Contexto adicional

    Returns:
        Resposta do agente
    """
    # Prepara o input para o LangGraph
    # TODO: Adaptar conforme a estrutura do state do seu grafo
    input_state = {
        "messages": [{"role": "user", "content": message}],
        **context,
    }

    # Invoca o grafo
    result = await agent.ainvoke(input_state)

    # Extrai a resposta
    # TODO: Adaptar conforme a estrutura do output do seu grafo
    if isinstance(result, dict) and "messages" in result:
        last_message = result["messages"][-1]
        if hasattr(last_message, "content"):
            return last_message.content
        return str(last_message)

    return str(result)


@router.post("/stream")
@limiter.limit("5/minute")  # 5 requests por minuto - streaming é custoso
async def stream_agent(request: Request, payload: AgentInvokeRequest):
    """
    Stream de resposta do agente.

    Rate limit: 5 requests/minuto por IP

    TODO: Implementar streaming com Server-Sent Events (SSE)
    """
    raise HTTPException(
        status_code=501,
        detail="Stream não implementado ainda. Use /invoke por enquanto.",
    )
