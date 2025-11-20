"""
Teste manual de rate limiting.

Para testar:
1. Inicie o servidor: python -m uvicorn taskni_core.main:app --reload
2. Execute este script: python test_rate_limiting.py
"""

import requests
import time

BASE_URL = "http://localhost:8080"


def test_agent_invoke_rate_limit():
    """
    Testa rate limit do endpoint /agents/invoke (10/minuto).
    """
    print("\n" + "=" * 80)
    print("🧪 TESTE: Rate Limit em /agents/invoke (10/minuto)")
    print("=" * 80)

    url = f"{BASE_URL}/agents/invoke"

    # Faz 12 requests rápidos
    print("\n📤 Enviando 12 requests rápidos...")
    success_count = 0
    rate_limited_count = 0

    for i in range(1, 13):
        try:
            response = requests.post(
                url,
                json={"agent_id": "followup-agent", "message": "Teste", "metadata": {}},
                timeout=5,
            )

            if response.status_code == 200:
                success_count += 1
                print(f"   ✅ Request {i}: 200 OK")
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"   ⛔ Request {i}: 429 TOO MANY REQUESTS (rate limited!)")
            else:
                print(f"   ❓ Request {i}: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Request {i}: Erro - {e}")

        time.sleep(0.1)  # Pequeno delay entre requests

    print(f"\n📊 Resultados:")
    print(f"   ✅ Sucessos: {success_count}")
    print(f"   ⛔ Rate Limited (429): {rate_limited_count}")

    if rate_limited_count > 0:
        print("\n✅ RATE LIMITING ESTÁ FUNCIONANDO!")
    else:
        print("\n⚠️  Nenhum request foi bloqueado. Servidor rodando?")


def test_rag_upload_rate_limit():
    """
    Testa rate limit do endpoint /rag/upload (5/minuto).
    """
    print("\n" + "=" * 80)
    print("🧪 TESTE: Rate Limit em /rag/upload (5/minuto)")
    print("=" * 80)

    url = f"{BASE_URL}/rag/upload"

    print("\n📤 Enviando 7 requests de upload...")
    success_count = 0
    rate_limited_count = 0

    for i in range(1, 8):
        try:
            # Cria arquivo temporário
            files = {"file": ("test.txt", "Conteúdo de teste", "text/plain")}

            response = requests.post(url, files=files, timeout=5)

            if response.status_code in [200, 201]:
                success_count += 1
                print(f"   ✅ Request {i}: {response.status_code} OK")
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"   ⛔ Request {i}: 429 TOO MANY REQUESTS (rate limited!)")
            else:
                print(f"   ❓ Request {i}: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Request {i}: Erro - {e}")

        time.sleep(0.1)

    print(f"\n📊 Resultados:")
    print(f"   ✅ Sucessos: {success_count}")
    print(f"   ⛔ Rate Limited (429): {rate_limited_count}")

    if rate_limited_count > 0:
        print("\n✅ RATE LIMITING ESTÁ FUNCIONANDO!")
    else:
        print("\n⚠️  Nenhum request foi bloqueado. Servidor rodando?")


def test_rag_delete_rate_limit():
    """
    Testa rate limit do endpoint /rag/documents DELETE (1/hora).
    """
    print("\n" + "=" * 80)
    print("🧪 TESTE: Rate Limit em /rag/documents DELETE (1/hora)")
    print("=" * 80)

    url = f"{BASE_URL}/rag/documents"

    print("\n📤 Enviando 3 requests DELETE...")
    print("⚠️  ATENÇÃO: Este endpoint DELETA documentos!")

    for i in range(1, 4):
        try:
            response = requests.delete(url, timeout=5)

            if response.status_code in [200, 201]:
                print(f"   ✅ Request {i}: {response.status_code} OK (documentos deletados!)")
            elif response.status_code == 429:
                print(f"   ⛔ Request {i}: 429 TOO MANY REQUESTS (rate limited!)")
            else:
                print(f"   ❓ Request {i}: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Request {i}: Erro - {e}")

        time.sleep(0.5)

    print("\n💡 Apenas o primeiro request deveria passar (limite de 1/hora)")


def check_server():
    """Verifica se o servidor está rodando."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Servidor está rodando!")
            return True
    except:
        pass

    print("❌ Servidor não está rodando!")
    print("   Execute: python -m uvicorn taskni_core.main:app --reload")
    return False


if __name__ == "__main__":
    print("\n" + "🔒 " * 40)
    print("TESTES DE RATE LIMITING")
    print("🔒 " * 40)

    if not check_server():
        exit(1)

    # Teste 1: Agent invoke (10/min)
    test_agent_invoke_rate_limit()

    time.sleep(2)

    # Teste 2: RAG upload (5/min)
    # test_rag_upload_rate_limit()  # Descomentarpara testar upload

    time.sleep(2)

    # Teste 3: RAG delete (1/hora) - CUIDADO!
    # test_rag_delete_rate_limit()  # Descomentar para testar delete

    print("\n" + "=" * 80)
    print("✅ TESTES CONCLUÍDOS")
    print("=" * 80)
    print("\n💡 Dica: Se nenhum request foi bloqueado, verifique se o servidor está")
    print("   rodando com o código atualizado.")
    print()
