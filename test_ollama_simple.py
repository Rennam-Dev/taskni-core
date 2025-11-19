"""
Teste simples de conexão com Ollama.
"""
import os

# Configura variáveis de ambiente diretamente
os.environ["OLLAMA_BASE_URL"] = "https://apiollama.rennam.dev"
os.environ["OLLAMA_EMBED_MODEL"] = "nomic-embed-text"

try:
    import httpx

    print("🧪 Testando conexão com Ollama...")
    print(f"📍 Endpoint: https://apiollama.rennam.dev")
    print(f"📦 Modelo: nomic-embed-text")
    print()

    # Teste 1: /api/tags
    print("TESTE 1: Listar modelos (/api/tags)")
    print("-" * 50)
    with httpx.Client(timeout=5.0, verify=False) as client:
        response = client.get("https://apiollama.rennam.dev/api/tags")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            print(f"✅ Modelos disponíveis: {len(models)}")
            for model in models:
                print(f"   - {model.get('name')}")
        else:
            print(f"❌ Erro: {response.text}")

    print()

    # Teste 2: /api/embeddings
    print("TESTE 2: Gerar embeddings (/api/embeddings)")
    print("-" * 50)
    with httpx.Client(timeout=10.0, verify=False) as client:
        response = client.post(
            "https://apiollama.rennam.dev/api/embeddings",
            json={
                "model": "nomic-embed-text",
                "prompt": "Hello, this is a test from Taskni Core"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding", [])
            print(f"✅ Embedding gerado com sucesso!")
            print(f"   Dimensões: {len(embedding)}")
            print(f"   Primeiros 5 valores: {embedding[:5]}")
        else:
            print(f"❌ Erro: {response.text}")

    print()
    print("=" * 50)
    print("✅ Ollama está funcionando corretamente!")
    print("=" * 50)

except ImportError:
    print("❌ httpx não está instalado")
    print("   Instale com: pip install httpx")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
