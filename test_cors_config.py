"""
Teste para validar configuração CORS no FastAPI.
"""

import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi.testclient import TestClient
from service.service import app


def test_cors_headers():
    """Testa se os headers CORS estão presentes nas respostas."""
    client = TestClient(app)

    # Simula uma requisição OPTIONS (preflight) de outro domínio
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    # Verifica se os headers CORS estão presentes
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers

    print("✅ CORS configurado corretamente!")
    print(f"   Allow-Origin: {response.headers.get('access-control-allow-origin')}")
    print(f"   Allow-Methods: {response.headers.get('access-control-allow-methods')}")
    print(f"   Allow-Headers: {response.headers.get('access-control-allow-headers')}")


def test_cors_on_actual_request():
    """Testa se CORS funciona em requisição real."""
    client = TestClient(app)

    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

    print("✅ Requisição GET com CORS funcionando!")
    print(f"   Status: {response.status_code}")
    print(f"   Allow-Origin: {response.headers.get('access-control-allow-origin')}")


if __name__ == "__main__":
    print("🧪 Testando configuração CORS...\n")
    test_cors_headers()
    print()
    test_cors_on_actual_request()
    print("\n✅ Todos os testes CORS passaram!")
