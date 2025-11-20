"""
Settings específicos do Taskni Core.

Usa composição ao invés de herança para evitar problemas de import.
O TaskniSettings tem suas próprias configurações e acessa as do toolkit
via `core_settings` quando necessário.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TaskniSettings(BaseSettings):
    """
    Configurações do Taskni Core.

    Específicas para clínicas e pequenos negócios.
    Para acessar configurações do toolkit (LLMs, database), use `core_settings`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        validate_default=False,
    )

    # ==========================================
    # Server Configuration
    # ==========================================
    MODE: str | None = None
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    LOG_LEVEL: str = "INFO"

    # ==========================================
    # Authentication (Bearer Token)
    # ==========================================
    # Token único de autenticação (recomendado para produção)
    API_TOKEN: SecretStr | None = None
    # Múltiplos tokens separados por vírgula (para múltiplos clientes)
    API_TOKENS: SecretStr | None = None

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

    # ==========================================
    # Ollama (embeddings apenas)
    # ==========================================
    # Ollama é usado apenas para EMBEDDINGS
    # LLM de geração usa Groq → OpenAI → FakeModel
    OLLAMA_BASE_URL: str | None = None
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    def is_dev(self) -> bool:
        """Check if running in development mode."""
        return self.MODE == "dev"


# Singleton do Taskni
taskni_settings = TaskniSettings()

# Helper para acessar settings do toolkit de forma lazy (evita import circular)
_core_settings = None


def get_core_settings():
    """
    Retorna o settings do toolkit de forma lazy.

    Isso evita import circular e problemas de inicialização.
    """
    global _core_settings
    if _core_settings is None:
        from core.settings import settings as core_settings

        _core_settings = core_settings
    return _core_settings
