#!/usr/bin/env python
"""
Testa todas as APIs de LLM configuradas e mostra quais estão funcionando.

Útil para verificar disponibilidade e escolher o melhor provider.
"""

import os

from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🔍 TESTE DE TODAS AS APIs DE LLM")
print("=" * 70)

results = []

# =============================================================================
# 1. GROQ
# =============================================================================
print("\n1️⃣  Testando GROQ...")
groq_key = os.getenv("GROQ_API_KEY")
if groq_key:
    try:
        from groq import Groq

        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b",
            messages=[{"role": "user", "content": "Diga apenas 'OK' em português"}],
            max_tokens=10,
        )
        reply = response.choices[0].message.content
        print(f"   ✅ GROQ funcionando: {reply}")
        results.append(("Groq", "✅ OK", "llama-3.1-8b"))
    except Exception as e:
        error = str(e)
        if "Access denied" in error:
            print("   ❌ GROQ: Access denied (outage Cloudflare)")
            results.append(("Groq", "❌ Indisponível", "Cloudflare outage"))
        else:
            print(f"   ❌ GROQ: {error[:60]}...")
            results.append(("Groq", "❌ Erro", error[:40]))
else:
    print("   ⚠️  GROQ_API_KEY não configurada")
    results.append(("Groq", "⚠️  Não configurada", "-"))

# =============================================================================
# 2. GOOGLE GEMINI
# =============================================================================
print("\n2️⃣  Testando GOOGLE GEMINI...")
google_key = os.getenv("GOOGLE_API_KEY")
if google_key:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", google_api_key=google_key, temperature=0.5
        )
        response = llm.invoke("Diga apenas 'OK' em português")
        print(f"   ✅ GEMINI funcionando: {response.content}")
        results.append(("Google Gemini", "✅ OK", "gemini-2.0-flash"))
    except Exception as e:
        print(f"   ❌ GEMINI: {str(e)[:60]}...")
        results.append(("Google Gemini", "❌ Erro", str(e)[:40]))
else:
    print("   ⚠️  GOOGLE_API_KEY não configurada")
    results.append(
        ("Google Gemini", "⚠️  Não configurada", "Obtenha em: https://aistudio.google.com/apikey")
    )

# =============================================================================
# 3. OLLAMA (LOCAL)
# =============================================================================
print("\n3️⃣  Testando OLLAMA (local)...")
ollama_model = os.getenv("OLLAMA_MODEL")
if ollama_model:
    try:
        from langchain_ollama import ChatOllama

        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        llm = ChatOllama(model=ollama_model, base_url=ollama_base_url, temperature=0.5)
        response = llm.invoke("Diga apenas 'OK' em português")
        print(f"   ✅ OLLAMA funcionando: {response.content}")
        results.append(("Ollama", "✅ OK", ollama_model))
    except Exception as e:
        error = str(e)
        if "Connection" in error or "connect" in error:
            print("   ❌ OLLAMA: Servidor não está rodando")
            print("      Execute: ollama serve")
            results.append(("Ollama", "❌ Servidor offline", "Execute: ollama serve"))
        else:
            print(f"   ❌ OLLAMA: {error[:60]}...")
            results.append(("Ollama", "❌ Erro", error[:40]))
else:
    print("   ⚠️  OLLAMA_MODEL não configurada")
    results.append(
        ("Ollama", "⚠️  Não configurada", "Instale: curl -fsSL https://ollama.com/install.sh | sh")
    )

# =============================================================================
# 4. OPENROUTER
# =============================================================================
print("\n4️⃣  Testando OPENROUTER...")
openrouter_key = os.getenv("OPENROUTER_API_KEY")
if openrouter_key:
    try:
        import httpx

        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.5-flash",
                "messages": [{"role": "user", "content": "Diga apenas 'OK' em português"}],
            },
            timeout=30.0,
        )
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            print(f"   ✅ OPENROUTER funcionando: {reply}")
            results.append(("OpenRouter", "✅ OK", "google/gemini-2.5-flash"))
        else:
            print(f"   ❌ OPENROUTER: Status {response.status_code}")
            results.append(("OpenRouter", f"❌ HTTP {response.status_code}", "-"))
    except Exception as e:
        print(f"   ❌ OPENROUTER: {str(e)[:60]}...")
        results.append(("OpenRouter", "❌ Erro", str(e)[:40]))
else:
    print("   ⚠️  OPENROUTER_API_KEY não configurada")
    results.append(("OpenRouter", "⚠️  Não configurada", "Obtenha em: https://openrouter.ai/keys"))

# =============================================================================
# 5. FAKE MODEL (sempre funciona)
# =============================================================================
print("\n5️⃣  Testando FAKE MODEL...")
use_fake = os.getenv("USE_FAKE_MODEL", "").lower() == "true"
if use_fake:
    print("   ✅ FAKE MODEL está ativa (desenvolvimento)")
    results.append(("FakeModel", "✅ OK", "Para desenvolvimento"))
else:
    print("   ⚠️  FAKE MODEL desativada")
    results.append(("FakeModel", "⚠️  Desativada", "Use apenas para testes"))

# =============================================================================
# RESUMO
# =============================================================================
print("\n" + "=" * 70)
print("📊 RESUMO DOS TESTES")
print("=" * 70)

print(f"\n{'Provider':<20} {'Status':<20} {'Modelo/Observação':<30}")
print("-" * 70)
for provider, status, model in results:
    print(f"{provider:<20} {status:<20} {model:<30}")

# =============================================================================
# RECOMENDAÇÃO
# =============================================================================
print("\n" + "=" * 70)
print("💡 RECOMENDAÇÃO")
print("=" * 70)

working_providers = [p for p, s, m in results if "✅" in s]

if working_providers:
    print(f"\n✅ Você tem {len(working_providers)} provider(s) funcionando:")
    for p in working_providers:
        print(f"   - {p}")

    # Recomenda o melhor
    if "Google Gemini" in working_providers:
        print("\n🎯 RECOMENDADO: Use Google Gemini (gratuito, rápido, confiável)")
        print("   Configure no .env:")
        print("   DEFAULT_MODEL=gemini-2.0-flash")
    elif "Groq" in working_providers:
        print("\n🎯 RECOMENDADO: Use Groq (muito rápido)")
        print("   Configure no .env:")
        print("   DEFAULT_MODEL=llama-3.1-8b")
    elif "Ollama" in working_providers:
        print("\n🎯 RECOMENDADO: Use Ollama (local, sem limites)")
        print("   Configure no .env:")
        print("   DEFAULT_MODEL=ollama")
    elif "OpenRouter" in working_providers:
        print("\n🎯 RECOMENDADO: Use OpenRouter")
        print("   Configure no .env:")
        print("   DEFAULT_MODEL=google/gemini-2.5-flash")
else:
    print("\n⚠️  Nenhum provider está funcionando!")
    print("\n📝 AÇÕES RECOMENDADAS:")
    print("   1. Configure Google Gemini (mais fácil e gratuito):")
    print("      - Obtenha key em: https://aistudio.google.com/apikey")
    print("      - Adicione no .env: GOOGLE_API_KEY=sua_chave")
    print("   ")
    print("   2. OU instale Ollama (local, sem limites):")
    print("      - curl -fsSL https://ollama.com/install.sh | sh")
    print("      - ollama pull llama3.2")
    print("      - Adicione no .env: OLLAMA_MODEL=llama3.2")

print("\n" + "=" * 70)
print("📚 Veja SETUP_FREE_LLMS.md para mais detalhes")
print("=" * 70)
