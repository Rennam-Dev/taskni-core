#!/usr/bin/env python
"""Teste da OpenAI API."""

import sys
import asyncio

sys.path.insert(0, "/home/user/taskni-core/src")

from taskni_core.agents.intake_agent import IntakeAgent

print("=" * 70)
print("🧪 TESTE DO INTAKEAGENT COM OPENAI")
print("=" * 70)

agent = IntakeAgent()
print(f"\n✅ Agente criado: {agent.id}")


async def test():
    print(f"\n💬 Testando com OpenAI (gpt-4o-mini)...")
    print(f"   Mensagem: 'Olá, gostaria de agendar uma consulta'")

    reply = await agent.run(
        message="Olá, bom dia! Gostaria de agendar uma consulta",
        context={
            "user_id": "patient_001",
            "metadata": {"source": "whatsapp", "phone": "+5511987654321"},
        },
    )

    print(f"\n📤 Resposta da OpenAI:")
    print(f"{'=' * 70}")
    print(reply)
    print(f"{'=' * 70}")
    return reply


try:
    result = asyncio.run(test())
    print(f"\n✅ Teste concluído com sucesso!")
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback

    traceback.print_exc()
