#!/usr/bin/env python
"""Teste do Gemini via API REST direta."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🧪 TESTE DO GEMINI VIA API REST")
print("=" * 70)

api_key = os.getenv("GOOGLE_API_KEY")
print(f"\n1. API Key: {api_key[:20]}...")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"

payload = {"contents": [{"parts": [{"text": "Diga 'Olá' em português de forma amigável"}]}]}

print("\n2. Enviando requisição...")
try:
    response = requests.post(url, json=payload, timeout=15, verify=False)

    if response.status_code == 200:
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]

        print("\n✅ SUCESSO!")
        print("📤 Resposta do Gemini:")
        print(f"{'=' * 70}")
        print(text)
        print(f"{'=' * 70}")
    else:
        print(f"\n❌ Erro HTTP {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"\n❌ ERRO: {e}")
