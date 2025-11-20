#!/usr/bin/env python
"""Teste rápido do Google Gemini."""

import sys
import asyncio

sys.path.insert(0, "/home/user/taskni-core/src")

from taskni_core.agents.intake_agent import IntakeAgent

print("=" * 70)
print("🧪 TESTE DO INTAKEAGENT COM GOOGLE GEMINI")
print("=" * 70)

agent = IntakeAgent()
print(f"\n✅ Agente criado: {agent.id}")


async def test():
    print(f"\n💬 Testando com mensagem real...")
    reply = await agent.run(
        message="Olá, bom dia! Gostaria de agendar uma consulta",
        context={
            "user_id": "patient_001",
            "metadata": {"source": "whatsapp", "phone": "+5511987654321"},
        },
    )
    print(f"\n📤 Resposta do Gemini:")
    print(f"{'=' * 70}")
    print(reply)
    print(f"{'=' * 70}")
    return reply


result = asyncio.run(test())
print(f"\n✅ Teste concluído com sucesso!")
