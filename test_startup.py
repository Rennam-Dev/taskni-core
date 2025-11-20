"""Script de teste para verificar se o app inicia corretamente."""

import sys

sys.path.insert(0, "/home/user/taskni-core/src")

print("1. Testando imports...")
from taskni_core.agents.intake_agent import IntakeAgent  # noqa: E402
from taskni_core.agents.registry import agent_registry, register_taskni_agents  # noqa: E402

print("✅ Imports OK")

print("\n2. Criando IntakeAgent...")
agent = IntakeAgent()
print(f"✅ IntakeAgent criado: {agent.id}")

print("\n3. Registrando agentes...")
register_taskni_agents()
agents = agent_registry.list_agents()
print(f"✅ {len(agents)} agente(s) registrado(s)")

print("\n4. Testando run do agente...")
import asyncio  # noqa: E402


async def test_agent():
    result = await agent.run(
        message="Olá, gostaria de agendar uma consulta", context={"user_id": "test_123"}
    )
    print(f"✅ Resposta: {result[:100]}...")
    return result


result = asyncio.run(test_agent())

print("\n✅ TODOS OS TESTES PASSARAM!")
