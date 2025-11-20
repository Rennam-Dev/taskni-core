"""
Schemas para requisições e respostas dos agentes.

Define os payloads de /invoke, /stream e outras rotas de agentes.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from taskni_core.schema.metadata_schemas import RequestMetadata, ResponseMetadata


class AgentInvokeRequest(BaseModel):
    """
    Requisição para invocar um agente.

    Usado no endpoint POST /agents/invoke
    """

    agent_id: str = Field(..., description="ID do agente a ser invocado")
    message: str = Field(..., description="Mensagem do usuário")
    user_id: Optional[str] = Field(None, description="ID do usuário/paciente")
    session_id: Optional[str] = Field(None, description="ID da sessão/conversa")
    thread_id: Optional[str] = Field(
        None, description="ID do thread (para continuidade de conversas)"
    )
    metadata: RequestMetadata = Field(
        default_factory=RequestMetadata,
        description="Metadados validados (source, phone, email, etc)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "agent_id": "intake-agent",
                "message": "Olá, gostaria de agendar uma consulta",
                "user_id": "user_123",
                "session_id": "session_456",
                "metadata": {
                    "source": "whatsapp",
                    "phone": "+5511999999999",
                },
            }
        }
    }


class AgentInvokeResponse(BaseModel):
    """
    Resposta do agente após invocação.

    Usado como retorno do endpoint POST /agents/invoke
    """

    agent_id: str = Field(..., description="ID do agente que processou")
    reply: str = Field(..., description="Resposta do agente")
    session_id: Optional[str] = Field(None, description="ID da sessão")
    thread_id: Optional[str] = Field(None, description="ID do thread")
    metadata: ResponseMetadata = Field(
        default_factory=ResponseMetadata,
        description="Metadados validados (tokens, tempo, modelo usado, etc)",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp da resposta",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "agent_id": "intake-agent",
                "reply": "Olá! Fico feliz em ajudar com seu agendamento. Para continuar, preciso de algumas informações...",
                "session_id": "session_456",
                "thread_id": "thread_789",
                "metadata": {
                    "model_used": "gpt-4o-mini",
                    "tokens": 150,
                    "processing_time_ms": 320,
                },
                "timestamp": "2025-01-15T10:30:00",
            }
        }
    }


class AgentStreamRequest(BaseModel):
    """
    Requisição para stream de um agente.

    Usado no endpoint POST /agents/stream
    """

    agent_id: str = Field(..., description="ID do agente a ser invocado")
    message: str = Field(..., description="Mensagem do usuário")
    user_id: Optional[str] = Field(None, description="ID do usuário/paciente")
    session_id: Optional[str] = Field(None, description="ID da sessão/conversa")
    thread_id: Optional[str] = Field(None, description="ID do thread")
    metadata: RequestMetadata = Field(
        default_factory=RequestMetadata, description="Metadados validados"
    )


class AgentListItem(BaseModel):
    """
    Item da lista de agentes disponíveis.

    Usado no endpoint GET /agents
    """

    id: str = Field(..., description="ID único do agente")
    name: str = Field(..., description="Nome amigável do agente")
    description: str = Field(..., description="Descrição do que o agente faz")
    type: str = Field(..., description="Tipo: 'simple' ou 'langgraph'")
    enabled: bool = Field(True, description="Se o agente está ativo")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "intake-agent",
                "name": "Agente de Triagem",
                "description": "Faz triagem inicial e coleta dados do paciente",
                "type": "simple",
                "enabled": True,
            }
        }
    }
