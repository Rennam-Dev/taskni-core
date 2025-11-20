"""
Schemas para CRM - Pacientes, Tickets, Agendamentos.

Define modelos de dados para gestão de clientes/pacientes.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class PatientStatus(str, Enum):
    """Status do paciente no sistema."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ARCHIVED = "archived"


class AppointmentStatus(str, Enum):
    """Status de agendamento."""

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class TicketStatus(str, Enum):
    """Status de ticket de atendimento."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Prioridade do ticket."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Patient(BaseModel):
    """
    Modelo de paciente/cliente.
    """

    id: Optional[str] = Field(None, description="ID único do paciente")
    name: str = Field(..., description="Nome completo")
    phone: str = Field(..., description="Telefone (WhatsApp)")
    email: Optional[EmailStr] = Field(None, description="Email")
    cpf: Optional[str] = Field(None, description="CPF")
    birth_date: Optional[datetime] = Field(None, description="Data de nascimento")

    # Endereço
    address: Optional[str] = Field(None, description="Endereço completo")
    city: Optional[str] = Field(None, description="Cidade")
    state: Optional[str] = Field(None, description="Estado")
    zip_code: Optional[str] = Field(None, description="CEP")

    # Status e metadados
    status: PatientStatus = Field(
        default=PatientStatus.ACTIVE,
        description="Status do paciente",
    )
    notes: Optional[str] = Field(None, description="Observações internas")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Data de cadastro",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Última atualização",
    )

    # Integrações
    chatwoot_contact_id: Optional[int] = Field(None, description="ID no Chatwoot")
    evolution_remote_jid: Optional[str] = Field(None, description="JID do WhatsApp (Evolution API)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "pt_123456",
                "name": "João Silva",
                "phone": "+5511999999999",
                "email": "joao@example.com",
                "status": "active",
                "created_at": "2025-01-15T10:00:00",
            }
        }
    }


class Appointment(BaseModel):
    """
    Modelo de agendamento.
    """

    id: Optional[str] = Field(None, description="ID único do agendamento")
    patient_id: str = Field(..., description="ID do paciente")
    scheduled_at: datetime = Field(..., description="Data/hora agendada")
    duration_minutes: int = Field(30, description="Duração em minutos")

    # Detalhes
    service_type: Optional[str] = Field(None, description="Tipo de serviço/consulta")
    doctor_name: Optional[str] = Field(None, description="Nome do profissional")
    notes: Optional[str] = Field(None, description="Observações")

    # Status e controle
    status: AppointmentStatus = Field(
        default=AppointmentStatus.SCHEDULED,
        description="Status do agendamento",
    )
    confirmed_at: Optional[datetime] = Field(None, description="Quando foi confirmado")
    completed_at: Optional[datetime] = Field(None, description="Quando foi concluído")

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Data de criação",
    )

    # Integrações
    calendar_event_id: Optional[str] = Field(None, description="ID no Cal.com ou Google Calendar")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "apt_789",
                "patient_id": "pt_123456",
                "scheduled_at": "2025-01-20T14:00:00",
                "duration_minutes": 30,
                "service_type": "Consulta inicial",
                "status": "scheduled",
            }
        }
    }


class Ticket(BaseModel):
    """
    Modelo de ticket de atendimento.
    """

    id: Optional[str] = Field(None, description="ID único do ticket")
    patient_id: str = Field(..., description="ID do paciente")
    subject: str = Field(..., description="Assunto do ticket")
    description: Optional[str] = Field(None, description="Descrição detalhada")

    # Classificação
    status: TicketStatus = Field(
        default=TicketStatus.OPEN,
        description="Status do ticket",
    )
    priority: TicketPriority = Field(
        default=TicketPriority.MEDIUM,
        description="Prioridade",
    )
    category: Optional[str] = Field(None, description="Categoria (dúvida, reclamação, etc)")

    # Controle
    assigned_to: Optional[str] = Field(None, description="Atribuído a (usuário/agente)")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Data de abertura",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Última atualização",
    )
    resolved_at: Optional[datetime] = Field(None, description="Data de resolução")

    # Integrações
    chatwoot_conversation_id: Optional[int] = Field(None, description="ID da conversa no Chatwoot")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "tkt_456",
                "patient_id": "pt_123456",
                "subject": "Dúvida sobre exame",
                "status": "open",
                "priority": "medium",
                "created_at": "2025-01-15T11:00:00",
            }
        }
    }
