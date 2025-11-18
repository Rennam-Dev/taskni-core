"""
Settings específicos do Taskni Core.

Herda do Settings base do Agent Service Toolkit e adiciona
configurações específicas para integrações de clínicas/negócios.
"""

from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict

# Importa o Settings base do toolkit
from core.settings import Settings as BaseSettings


class TaskniSettings(BaseSettings):
    """
    Configurações do Taskni Core.

    Herda todas as configurações do Agent Service Toolkit (LLMs, database, etc)
    e adiciona as específicas para clínicas e pequenos negócios.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        validate_default=False,
    )

    # ==========================================
    # Integrações específicas do Taskni
    # ==========================================

    # Evolution API (WhatsApp)
    EVOLUTION_API_URL: str | None = None
    EVOLUTION_API_KEY: SecretStr | None = None
    EVOLUTION_INSTANCE_NAME: str | None = None

    # Chatwoot (CRM/Atendimento)
    CHATWOOT_API_URL: str | None = None
    CHATWOOT_API_TOKEN: SecretStr | None = None
    CHATWOOT_ACCOUNT_ID: int | None = None
    CHATWOOT_INBOX_ID: int | None = None

    # n8n (Automações)
    N8N_WEBHOOK_URL: str | None = None
    N8N_API_KEY: SecretStr | None = None

    # Supabase (Auth + Database adicional)
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: SecretStr | None = None
    SUPABASE_SERVICE_KEY: SecretStr | None = None

    # Cal.com ou similar (Agendamento)
    CALENDAR_API_URL: str | None = None
    CALENDAR_API_KEY: SecretStr | None = None

    # Stripe/Payment Gateway (Cobrança)
    STRIPE_API_KEY: SecretStr | None = None
    STRIPE_WEBHOOK_SECRET: SecretStr | None = None

    # ==========================================
    # Configurações específicas de clínica
    # ==========================================

    # Nome da clínica/negócio (usado pelos agentes)
    BUSINESS_NAME: str = "Taskni Clinic"
    BUSINESS_PHONE: str | None = None
    BUSINESS_EMAIL: str | None = None

    # Idioma padrão dos agentes
    DEFAULT_LANGUAGE: str = "pt-BR"

    # Habilitar/desabilitar agentes específicos
    ENABLE_INTAKE_AGENT: bool = True
    ENABLE_FAQ_AGENT: bool = True
    ENABLE_FOLLOWUP_AGENT: bool = True
    ENABLE_BILLING_AGENT: bool = False  # Desabilitado por padrão

    # ==========================================
    # RAG/Vector Store para FAQ
    # ==========================================
    # (Pode usar ChromaDB do toolkit ou outro)
    FAQ_VECTOR_STORE_PATH: str | None = None
    FAQ_COLLECTION_NAME: str = "clinic_faq"


# Singleton
taskni_settings = TaskniSettings()
