"""
Schemas de input para agentes com validação Pydantic.

Garante que os inputs dos agentes sejam validados antes de processar,
evitando erros em runtime e fornecendo mensagens claras de erro.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class FollowupInput(BaseModel):
    """
    Input do FollowupAgent com validação.

    Valida que os dados estejam no formato correto antes de
    processar o workflow de reativação/acompanhamento.
    """

    patient_name: str = Field(
        ..., min_length=1, max_length=200, description="Nome do paciente (obrigatório)"
    )

    days_inactive: int = Field(..., ge=0, description="Dias desde último contato (deve ser >= 0)")

    last_message: str = Field(
        default="", max_length=1000, description="Última mensagem do paciente"
    )

    context: dict[str, Any] = Field(
        default_factory=dict, description="Contexto adicional (clinic_type, service, etc)"
    )

    @field_validator("days_inactive")
    @classmethod
    def validate_days_inactive(cls, v: int) -> int:
        """Valida que days_inactive seja não-negativo."""
        if v < 0:
            raise ValueError("days_inactive must be >= 0")
        return v

    @field_validator("patient_name")
    @classmethod
    def validate_patient_name(cls, v: str) -> str:
        """Valida que o nome não seja vazio ou apenas espaços."""
        if not v or not v.strip():
            raise ValueError("patient_name cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "patient_name": "João Silva",
                "days_inactive": 45,
                "last_message": "Obrigado pelo atendimento!",
                "context": {
                    "clinic_type": "clínica geral",
                    "service": "consulta",
                    "is_patient": True,
                },
            }
        }


class RagQueryInput(BaseModel):
    """
    Input do FaqRagAgent com validação.

    Valida perguntas para busca RAG.
    """

    question: str = Field(..., min_length=1, max_length=500, description="Pergunta do usuário")

    k_documents: int | None = Field(
        default=4, ge=1, le=10, description="Número de documentos a recuperar (1-10)"
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Valida que a pergunta não seja vazia."""
        if not v or not v.strip():
            raise ValueError("question cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {"question": "Qual o horário de funcionamento?", "k_documents": 4}
        }


class IntakeInput(BaseModel):
    """
    Input do IntakeAgent com validação.

    Valida mensagens para triagem inicial.
    """

    message: str = Field(..., min_length=1, max_length=1000, description="Mensagem do paciente")

    user_id: str | None = Field(default=None, description="ID do usuário (opcional)")

    session_id: str | None = Field(default=None, description="ID da sessão (opcional)")

    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata adicional (phone, source, etc)"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Valida que a mensagem não seja vazia."""
        if not v or not v.strip():
            raise ValueError("message cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Gostaria de agendar uma consulta",
                "user_id": "patient_001",
                "session_id": "session_123",
                "metadata": {"phone": "+5511987654321", "source": "whatsapp"},
            }
        }
