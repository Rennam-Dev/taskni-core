#!/usr/bin/env python
"""Teste de conectividade com Groq API - Diagnóstico detalhado."""
import sys
import os
from groq import Groq

# Carrega .env
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

print("="*70)
print("🔍 DIAGNÓSTICO DA GROQ API")
print("="*70)

print(f"\n1. API Key configurada: {api_key[:20]}..." if api_key else "❌ Sem API key")

if not api_key:
    print("❌ GROQ_API_KEY não encontrada no .env")
    sys.exit(1)

# Tenta criar o cliente
print(f"\n2. Criando cliente Groq...")
try:
    client = Groq(api_key=api_key)
    print("   ✅ Cliente criado com sucesso")
except Exception as e:
    print(f"   ❌ Erro ao criar cliente: {e}")
    sys.exit(1)

# Testa modelos disponíveis
print(f"\n3. Testando modelos disponíveis:")

models_to_test = [
    "llama-3.1-8b",
    "llama-3.3-70b",
    "mixtral-8x7b-32768",
]

for model_name in models_to_test:
    print(f"\n   Testando: {model_name}")
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "Diga olá em português"}
            ],
            max_tokens=50,
            temperature=0.5
        )
        print(f"   ✅ {model_name}: {response.choices[0].message.content}")
        break  # Se um funcionar, para aqui
    except Exception as e:
        error_msg = str(e)
        if "Access denied" in error_msg:
            print(f"   ❌ {model_name}: Access denied (sem permissão)")
        elif "not found" in error_msg or "does not exist" in error_msg:
            print(f"   ⚠️  {model_name}: Modelo não encontrado")
        elif "rate limit" in error_msg.lower():
            print(f"   ⚠️  {model_name}: Rate limit excedido")
        elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
            print(f"   💰 {model_name}: Problema de quota/billing")
        else:
            print(f"   ❌ {model_name}: {error_msg}")

print(f"\n{'='*70}")
print("📝 CONCLUSÃO:")
print("="*70)
print("""
Se todos os modelos deram "Access denied":
  - A chave pode estar expirada
  - A conta pode estar sem créditos
  - Pode haver restrições de billing

Verifique em: https://console.groq.com/keys
""")
