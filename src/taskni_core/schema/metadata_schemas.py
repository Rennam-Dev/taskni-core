"""
Schemas tipados para metadata.

Substitui Dict[str, Any] genéricos por schemas Pydantic validados.
Previne injection e garante consistência de dados.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Request Metadata
# ============================================================================


class RequestMetadata(BaseModel):
    """
    Metadata de requisições de agentes (input).

    Campos comuns vindos de integrações externas (WhatsApp, Chatwoot, etc).
    """

    # Origem da mensagem
    source: Literal["whatsapp", "chatwoot", "web", "api", "telegram", "instagram"] | None = Field(
        None, description="Canal de origem da mensagem"
    )

    # Contato
    phone: str | None = Field(
        None, description="Telefone do usuário (formato: +5511999999999)", max_length=20
    )
    email: str | None = Field(None, description="Email do usuário", max_length=255)

    # IDs externos
    chatwoot_conversation_id: str | None = Field(
        None, description="ID da conversa no Chatwoot", max_length=100
    )
    evolution_instance_id: str | None = Field(
        None, description="ID da instância Evolution API", max_length=100
    )
    external_user_id: str | None = Field(
        None, description="ID do usuário em sistema externo", max_length=100
    )

    # Contexto adicional
    language: Literal["pt-BR", "en-US", "es-ES"] | None = Field(
        "pt-BR", description="Idioma da conversa"
    )
    timezone: str | None = Field(
        "America/Sao_Paulo", description="Timezone do usuário", max_length=50
    )

    # Campos customizados (limitados para segurança)
    custom: dict[str, str | int | bool] | None = Field(
        default_factory=dict,
        description="Campos customizados (apenas tipos básicos)",
        max_length=10,  # Máximo 10 campos customizados
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Valida formato de telefone."""
        if v is None:
            return v
        # Remove caracteres não-numéricos
        clean = "".join(c for c in v if c.isdigit() or c == "+")
        if clean and not clean.startswith("+"):
            raise ValueError("Telefone deve começar com +")
        if len(clean) < 10 or len(clean) > 15:
            raise ValueError("Telefone deve ter entre 10 e 15 dígitos")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validação básica de email."""
        if v is None:
            return v
        if "@" not in v or "." not in v.split("@")[1]:
            raise ValueError("Email inválido")
        return v.lower()

    @field_validator("custom")
    @classmethod
    def validate_custom(cls, v: dict | None) -> dict:
        """Valida campos customizados."""
        if v is None:
            return {}
        # Limita número de campos
        if len(v) > 10:
            raise ValueError("Máximo de 10 campos customizados")
        # Valida que valores são apenas tipos básicos
        for key, value in v.items():
            if not isinstance(value, (str, int, bool, type(None))):
                raise ValueError(f"Valor '{key}' deve ser string, int, bool ou None")
            # Limita tamanho de strings
            if isinstance(value, str) and len(value) > 500:
                raise ValueError(f"Valor '{key}' muito longo (máx 500 caracteres)")
        return v


# ============================================================================
# Response Metadata
# ============================================================================


class ResponseMetadata(BaseModel):
    """
    Metadata de respostas de agentes (output).

    Informações sobre processamento, uso de recursos, etc.
    """

    # Modelo LLM usado
    model_used: str | None = Field(
        None, description="Modelo LLM usado (ex: gpt-4o-mini, groq-llama3)", max_length=50
    )

    # Métricas de uso
    tokens: int | None = Field(
        None,
        description="Total de tokens usados",
        ge=0,  # Maior ou igual a 0
        le=1000000,  # Limite de 1M tokens
    )
    input_tokens: int | None = Field(None, description="Tokens de input", ge=0)
    output_tokens: int | None = Field(None, description="Tokens de output", ge=0)

    # Métricas de performance
    processing_time_ms: int | None = Field(
        None,
        description="Tempo de processamento em milissegundos",
        ge=0,
        le=300000,  # Máx 5 minutos
    )
    llm_latency_ms: int | None = Field(None, description="Latência do LLM em milissegundos", ge=0)

    # Informações do agente
    agent_version: str | None = Field(None, description="Versão do agente", max_length=20)
    workflow_steps: int | None = Field(
        None, description="Número de steps do workflow executados", ge=0, le=100
    )

    # RAG metadata (se aplicável)
    rag_used: bool | None = Field(None, description="Se RAG foi usado na resposta")
    documents_retrieved: int | None = Field(
        None, description="Número de documentos recuperados do RAG", ge=0, le=100
    )
    cache_hit: bool | None = Field(None, description="Se resposta veio do cache")

    # Flags de qualidade
    confidence_score: float | None = Field(
        None, description="Score de confiança da resposta (0-1)", ge=0.0, le=1.0
    )
    needs_human_review: bool | None = Field(
        None, description="Se resposta precisa de revisão humana"
    )

    @field_validator("tokens", "input_tokens", "output_tokens")
    @classmethod
    def validate_tokens_consistency(cls, v, info):
        """Valida consistência entre tokens."""
        # Se todos estiverem presentes, valida que input + output = total
        values = info.data
        if all(k in values for k in ["tokens", "input_tokens", "output_tokens"]):
            total = values.get("tokens", 0)
            inp = values.get("input_tokens", 0)
            out = values.get("output_tokens", 0)
            if inp + out != total:
                raise ValueError(f"Tokens inconsistentes: {inp} + {out} ≠ {total}")
        return v


# ============================================================================
# RAG Metadata
# ============================================================================


class DocumentMetadata(BaseModel):
    """
    Metadata de documentos ingeridos no RAG.

    Usado em POST /rag/upload e POST /rag/ingest/text
    """

    # Informações da fonte
    source_file: str | None = Field(None, description="Nome do arquivo original", max_length=255)
    source_url: str | None = Field(None, description="URL original do documento", max_length=500)
    source_type: Literal["manual", "crawl", "api", "upload"] | None = Field(
        "upload", description="Como o documento foi obtido"
    )

    # Categorização
    category: Literal["faq", "policy", "procedure", "manual", "other"] | None = Field(
        None, description="Categoria do documento"
    )
    tags: list[str] | None = Field(
        default_factory=list,
        description="Tags do documento",
        max_length=20,  # Máx 20 tags
    )

    # Controle de versão
    version: str | None = Field(None, description="Versão do documento", max_length=20)
    author: str | None = Field(None, description="Autor do documento", max_length=100)

    # Controle de acesso
    visibility: Literal["public", "internal", "restricted"] | None = Field(
        "internal", description="Nível de visibilidade"
    )
    department: str | None = Field(None, description="Departamento responsável", max_length=100)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str]:
        """Valida tags."""
        if v is None:
            return []
        # Limita número de tags
        if len(v) > 20:
            raise ValueError("Máximo de 20 tags")
        # Valida tamanho de cada tag
        for tag in v:
            if len(tag) > 50:
                raise ValueError("Cada tag deve ter no máximo 50 caracteres")
            if not tag.strip():
                raise ValueError("Tags não podem estar vazias")
        return [tag.strip().lower() for tag in v]

    @field_validator("source_url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """Validação básica de URL."""
        if v is None:
            return v
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        return v


# ============================================================================
# Helper Functions
# ============================================================================


def validate_metadata(metadata: dict, metadata_type: type[BaseModel]) -> BaseModel:
    """
    Valida e converte metadata Dict[str, Any] para schema tipado.

    Args:
        metadata: Dicionário com metadata
        metadata_type: Tipo do schema (RequestMetadata, ResponseMetadata, etc)

    Returns:
        Instância validada do schema

    Raises:
        ValidationError: Se metadata for inválida

    Example:
        >>> meta = {"source": "whatsapp", "phone": "+5511999999999"}
        >>> validated = validate_metadata(meta, RequestMetadata)
        >>> print(validated.source)
        "whatsapp"
    """
    return metadata_type(**metadata)
