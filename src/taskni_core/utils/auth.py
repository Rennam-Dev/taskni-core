"""
Authentication utilities para proteger endpoints da API.

Implementa autenticação via Bearer token simples mas segura.
"""

import logging
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# Security scheme para FastAPI docs (Swagger)
security_scheme = HTTPBearer(
    scheme_name="Bearer Token",
    description="Token de autenticação (formato: Bearer <token>)",
    bearerFormat="Bearer",
    auto_error=False,  # Não falha automaticamente, vamos tratar manualmente
)


class AuthManager:
    """
    Gerenciador de autenticação via Bearer token.

    Suporta:
    - Token único (API_TOKEN no .env)
    - Múltiplos tokens (API_TOKENS no .env, separados por vírgula)
    - Desabilitação (se nenhum token configurado)
    """

    def __init__(self, api_token: str | None = None, api_tokens: str | None = None):
        """
        Inicializa o gerenciador de autenticação.

        Args:
            api_token: Token único (API_TOKEN)
            api_tokens: Múltiplos tokens separados por vírgula (API_TOKENS)
        """
        self.valid_tokens: set[str] = set()

        # Adiciona token único
        if api_token:
            self.valid_tokens.add(api_token.strip())

        # Adiciona múltiplos tokens
        if api_tokens:
            tokens = [t.strip() for t in api_tokens.split(",") if t.strip()]
            self.valid_tokens.update(tokens)

        self.enabled = len(self.valid_tokens) > 0

        if self.enabled:
            logger.info(f"✅ Autenticação habilitada ({len(self.valid_tokens)} token(s))")
        else:
            logger.warning(
                "⚠️  Autenticação DESABILITADA! Configure API_TOKEN no .env para produção."
            )

    def verify_token(self, token: str) -> bool:
        """
        Verifica se um token é válido.

        Usa secrets.compare_digest() para prevenir timing attacks.

        Args:
            token: Token a ser verificado

        Returns:
            True se válido, False caso contrário
        """
        if not self.enabled:
            return True  # Sem autenticação, sempre passa

        # Compara com cada token válido usando timing-safe comparison
        for valid_token in self.valid_tokens:
            if secrets.compare_digest(token, valid_token):
                return True

        return False

    def require_auth(
        self, credentials: HTTPAuthorizationCredentials | None = Security(security_scheme)
    ) -> None:
        """
        Dependency do FastAPI que requer autenticação.

        Uso:
            @router.get("/protected", dependencies=[Depends(auth.require_auth)])
            async def protected_endpoint():
                return {"message": "Autenticado!"}

        Args:
            credentials: Credenciais do header Authorization

        Raises:
            HTTPException: 401 se não autenticado, 403 se token inválido
        """
        # Se autenticação desabilitada, permite acesso
        if not self.enabled:
            return

        # Verifica se header Authorization foi enviado
        if credentials is None:
            logger.warning("❌ Tentativa de acesso sem token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticação necessária. Forneça um Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verifica se token é válido
        token = credentials.credentials
        if not self.verify_token(token):
            logger.warning(f"❌ Token inválido tentado: {token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token inválido ou expirado.",
            )

        # Token válido - permite acesso
        logger.debug(f"✅ Acesso autorizado com token: {token[:10]}...")

    async def require_auth_async(
        self, credentials: HTTPAuthorizationCredentials | None = Security(security_scheme)
    ) -> None:
        """Versão async do require_auth (mesma lógica)."""
        self.require_auth(credentials)


# ============================================================================
# Helper Functions
# ============================================================================


def generate_secure_token(length: int = 32) -> str:
    """
    Gera um token seguro aleatório.

    Útil para gerar novos tokens de API.

    Args:
        length: Tamanho do token em bytes (padrão: 32 = 64 caracteres hex)

    Returns:
        Token hexadecimal seguro

    Example:
        >>> token = generate_secure_token()
        >>> print(f"API_TOKEN={token}")
        API_TOKEN=a1b2c3d4e5f6...
    """
    return secrets.token_hex(length)


def validate_token_format(token: str) -> bool:
    """
    Valida formato básico de um token.

    Args:
        token: Token a ser validado

    Returns:
        True se formato válido, False caso contrário
    """
    # Token deve ter pelo menos 16 caracteres
    if len(token) < 16:
        return False

    # Token não deve conter espaços
    if " " in token:
        return False

    # Token deve ser alfanumérico (ou hex)
    if not all(c.isalnum() or c in "-_" for c in token):
        return False

    return True


# ============================================================================
# Token Generation Script
# ============================================================================

if __name__ == "__main__":
    """
    Script para gerar tokens de API.

    Uso:
        python -m taskni_core.utils.auth
    """
    print("\n🔐 GERADOR DE TOKENS DE API\n")
    print("=" * 60)

    # Gera 3 tokens de exemplo
    for i in range(1, 4):
        token = generate_secure_token()
        print(f"\nToken {i}:")
        print(f"  API_TOKEN={token}")

    print("\n" + "=" * 60)
    print("\n💡 Dicas:")
    print("  1. Copie um dos tokens acima")
    print("  2. Adicione ao arquivo .env:")
    print("     API_TOKEN=<token_aqui>")
    print("  3. Para múltiplos tokens, use:")
    print("     API_TOKENS=token1,token2,token3")
    print("  4. Reinicie o servidor para aplicar")
    print("\n⚠️  IMPORTANTE: Nunca compartilhe seus tokens!")
    print("   Guarde-os em local seguro (ex: gerenciador de senhas)")
    print()
