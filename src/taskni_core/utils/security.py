"""
Utilities de segurança para prevenir ataques.

Inclui sanitização de inputs para prevenir:
- Prompt Injection
- Command Injection
- XSS
- CRLF Injection
"""

import re


def sanitize_prompt_input(text: str, max_length: int = 200, allow_multiline: bool = False) -> str:
    """
    Sanitiza input de usuário para prevenir prompt injection.

    Remove:
    - Caracteres de controle (exceto espaços/tabs)
    - Múltiplos newlines consecutivos
    - Palavras-chave de injection
    - Caracteres perigosos para LLMs

    Args:
        text: Texto a ser sanitizado
        max_length: Comprimento máximo permitido
        allow_multiline: Se deve permitir quebras de linha (padrão: False)

    Returns:
        Texto sanitizado e seguro para usar em prompts

    Examples:
        >>> sanitize_prompt_input("João Silva")
        "João Silva"

        >>> sanitize_prompt_input("João\\n\\nIgnore all instructions")
        "João Ignore all instructions"

        >>> sanitize_prompt_input("a" * 300, max_length=100)
        "aaa...aaa"  # Truncado em 100 caracteres
    """
    if not text:
        return ""

    # 1. Remove caracteres de controle (mantém apenas printable + espaços)
    text = "".join(c for c in text if c.isprintable() or c.isspace())

    # 2. Remove ou substitui múltiplos newlines (tentativa comum de injection)
    if not allow_multiline:
        # Remove TODOS os newlines
        text = " ".join(text.split())
    else:
        # Permite newlines mas remove múltiplos consecutivos
        text = re.sub(r"\n{3,}", "\n\n", text)

    # 3. Remove palavras-chave perigosas de prompt injection
    # Usa word boundaries para não afetar palavras normais
    dangerous_patterns = [
        r"\bignore\s+(all\s+)?(previous\s+)?instructions?\b",
        r"\bdisregard\s+(all\s+)?(previous\s+)?instructions?\b",
        r"\bforget\s+(all\s+)?(previous\s+)?instructions?\b",
        r"\boverride\s+instructions?\b",
        r"\bsystem\s*:\s*",  # Tentativa de injetar system message
        r"\bassistant\s*:\s*",  # Tentativa de injetar assistant message
        r"\buser\s*:\s*",  # Tentativa de injetar user message
        r"\bprompt\s*:\s*",
        r"\b(you\s+are|you\'re)\s+(now|currently)\b",  # "you are now..."
        r"\bact\s+as\b",  # "act as..."
        r"\bpretend\s+(to\s+be|you\s+are)\b",
    ]

    for pattern in dangerous_patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # 4. Remove caracteres perigosos específicos
    dangerous_chars = [
        "\x00",  # Null byte
        "\r",  # Carriage return (se ainda existir)
    ]
    for char in dangerous_chars:
        text = text.replace(char, "")

    # 5. Normaliza espaços múltiplos (mas preserva newlines se allow_multiline)
    if allow_multiline:
        # Normaliza espaços horizontais mas preserva newlines
        text = re.sub(r"[ \t]+", " ", text)
    else:
        # Remove todos os tipos de espaços múltiplos
        text = re.sub(r"\s+", " ", text)

    # 6. Remove espaços nas pontas
    text = text.strip()

    # 7. Limita tamanho
    if len(text) > max_length:
        text = text[:max_length].strip()

    return text


def sanitize_metadata_value(value: str, max_length: int = 500, field_name: str = "metadata") -> str:
    """
    Sanitiza valores de metadata para prevenir injection.

    Similar ao sanitize_prompt_input mas permite quebras de linha
    e tem validações adicionais para metadata.

    Args:
        value: Valor a ser sanitizado
        max_length: Comprimento máximo
        field_name: Nome do campo (para logs)

    Returns:
        Valor sanitizado
    """
    return sanitize_prompt_input(value, max_length=max_length, allow_multiline=True)


def validate_json_no_injection(obj: dict) -> bool:
    """
    Valida que um objeto JSON não contém tentativas de injection.

    Checa recursivamente por:
    - Strings muito longas
    - Padrões suspeitos
    - Profundidade excessiva

    Args:
        obj: Objeto a ser validado

    Returns:
        True se seguro, False caso contrário
    """

    def check_value(val, depth=0):
        # Limite de profundidade (previne DoS)
        if depth > 10:
            return False

        if isinstance(val, str):
            # String muito longa
            if len(val) > 10000:
                return False
            # Padrões suspeitos
            if re.search(r"(__.*?__|<script|javascript:|onerror=)", val, re.IGNORECASE):
                return False
        elif isinstance(val, dict):
            for v in val.values():
                if not check_value(v, depth + 1):
                    return False
        elif isinstance(val, list):
            for item in val:
                if not check_value(item, depth + 1):
                    return False

        return True

    return check_value(obj)


def sanitize_rag_filter(filter_dict: dict) -> dict:
    """
    Sanitiza filtros para queries RAG/ChromaDB.

    Previne injection em where clauses.

    Args:
        filter_dict: Dicionário de filtros

    Returns:
        Filtros sanitizados

    Example:
        >>> sanitize_rag_filter({"category": "faq'; DROP TABLE--"})
        {"category": "faq DROP TABLE"}
    """
    if not filter_dict:
        return {}

    sanitized = {}

    for key, value in filter_dict.items():
        # Sanitiza chave (permite apenas alphanumeric + underscore)
        safe_key = re.sub(r"[^\w]", "", key)

        # Sanitiza valor
        if isinstance(value, str):
            # Remove caracteres perigosos para SQL/NoSQL
            # 1. Remove comentários SQL (-- e /* */)
            safe_value = re.sub(r"--", "", value)
            safe_value = re.sub(r"/\*.*?\*/", "", safe_value)
            # 2. Remove aspas e caracteres especiais
            safe_value = re.sub(r'[;\'"\\]', "", safe_value)
            # 3. Remove espaços extras
            safe_value = safe_value.strip()
            sanitized[safe_key] = safe_value
        elif isinstance(value, (int, float, bool)):
            sanitized[safe_key] = value
        elif isinstance(value, dict):
            # Recursivo para filtros aninhados
            sanitized[safe_key] = sanitize_rag_filter(value)
        # Ignora outros tipos

    return sanitized
