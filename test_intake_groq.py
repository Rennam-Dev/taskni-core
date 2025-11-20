#!/usr/bin/env python
"""Teste standalone do IntakeAgent com Groq."""

import asyncio
import sys

sys.path.insert(0, "/home/user/taskni-core/src")

from taskni_core.agents.intake_agent import IntakeAgent
from taskni_core.core.settings import taskni_settings

print("=" * 60)
print("🧪 Teste do IntakeAgent com Groq (llama-3.1-8b)")
print("=" * 60)

print("\n📋 Configurações:")
print(f"   BUSINESS_NAME: {taskni_settings.BUSINESS_NAME}")
print(f"   DEFAULT_LANGUAGE: {taskni_settings.DEFAULT_LANGUAGE}")

print("\n🤖 Criando IntakeAgent...")
agent = IntakeAgent()
print(f"   ID: {agent.id}")
print(f"   Name: {agent.name}")


async def test_agent():
    print("\n💬 Teste 1: Primeira mensagem do paciente")
    print("   Entrada: 'Olá, bom dia! Gostaria de agendar uma consulta'")

    reply = await agent.run(
        message="Olá, bom dia! Gostaria de agendar uma consulta",
        context={
            "user_id": "patient_001",
            "metadata": {"source": "whatsapp", "phone": "+5511987654321"},
        },
    )

    print("\n   Resposta do agente:")
    print(f"   {'-' * 56}")
    print(f"   {reply}")
    print(f"   {'-' * 56}")

    print("\n✅ Teste concluído com sucesso!")
    return reply


print("\n🚀 Executando teste assíncrono...")
result = asyncio.run(test_agent())

print(f"\n{'=' * 60}")
print("✨ Teste finalizado!")
print(f"{'=' * 60}")
