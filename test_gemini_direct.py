#!/usr/bin/env python
"""Teste direto do Google Gemini sem o agente."""
import os
from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("🧪 TESTE DIRETO DO GOOGLE GEMINI")
print("="*70)

api_key = os.getenv("GOOGLE_API_KEY")
print(f"\n1. API Key: {api_key[:20]}..." if api_key else "❌ Sem API key")

print(f"\n2. Testando com langchain_google_genai...")
try:
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0.5
    )
    print(f"   ✅ Modelo criado")

    print(f"\n3. Enviando mensagem de teste...")
    response = llm.invoke("Diga 'Olá' em português de forma amigável")

    print(f"\n✅ SUCESSO!")
    print(f"📤 Resposta do Gemini:")
    print(f"{'='*70}")
    print(response.content)
    print(f"{'='*70}")

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
