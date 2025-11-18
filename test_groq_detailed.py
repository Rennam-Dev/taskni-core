#!/usr/bin/env python
"""Teste específico de status da Groq API com detalhes do erro."""
import sys
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

print("="*70)
print("🔍 TESTE DETALHADO DA GROQ API")
print("="*70)

if not api_key:
    print("\n❌ GROQ_API_KEY não encontrada")
    sys.exit(1)

print(f"\n1. API Key: {api_key[:20]}...")

client = Groq(api_key=api_key)
print("2. ✅ Cliente criado")

print("\n3. Tentando requisição real...")
try:
    response = client.chat.completions.create(
        model="llama-3.1-8b",
        messages=[
            {"role": "user", "content": "Diga olá"}
        ],
        max_tokens=10
    )
    print(f"\n✅ SUCESSO! Groq está funcionando!")
    print(f"Resposta: {response.choices[0].message.content}")

except Exception as e:
    print(f"\n❌ ERRO:")
    print(f"   Tipo: {type(e).__name__}")
    print(f"   Mensagem: {str(e)}")

    # Tenta extrair mais informações
    if hasattr(e, 'response'):
        print(f"   Status Code: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
        print(f"   Response: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")

    # Análise do erro
    error_str = str(e).lower()
    print(f"\n📊 ANÁLISE:")
    if "access denied" in error_str:
        print("   🔴 Access Denied - Possíveis causas:")
        print("      1. Chave sem permissão/expirada")
        print("      2. Conta sem créditos/billing")
        print("      3. Ainda afetado pelo outage Cloudflare")
        print("      4. Rate limit excedido")
    elif "not found" in error_str:
        print("   ⚠️  Modelo não encontrado")
    elif "rate limit" in error_str:
        print("   ⏰ Rate limit excedido")
    elif "timeout" in error_str or "connection" in error_str:
        print("   🌐 Problema de conectividade")
    else:
        print("   ❓ Erro desconhecido")

print("\n" + "="*70)
print("💡 PRÓXIMOS PASSOS:")
print("="*70)
print("""
1. Verifique sua conta em: https://console.groq.com/
   - Status da API key
   - Créditos disponíveis
   - Billing configurado

2. Se o problema persistir, use alternativa gratuita:
   - Google Gemini: https://aistudio.google.com/apikey
   - Ollama (local): curl -fsSL https://ollama.com/install.sh | sh

3. Veja SETUP_FREE_LLMS.md para mais opções
""")
