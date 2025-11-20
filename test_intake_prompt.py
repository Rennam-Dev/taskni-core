#!/usr/bin/env python
"""
Teste do prompt do IntakeAgent - Verifica o prompt enviado ao LLM.

Mostra como o agente constrói os prompts de sistema e usuário.
"""

import sys

sys.path.insert(0, "/home/user/taskni-core/src")

from taskni_core.agents.intake_agent import IntakeAgent
from taskni_core.core.settings import taskni_settings

print("=" * 70)
print("🔍 VERIFICAÇÃO DO PROMPT DO INTAKEAGENT")
print("=" * 70)

agent = IntakeAgent()

print("\n📋 Configurações do Agente:")
print(f"   ID: {agent.id}")
print(f"   Nome: {agent.name}")
print(f"   Negócio: {taskni_settings.BUSINESS_NAME}")
print(f"   Idioma: {taskni_settings.DEFAULT_LANGUAGE}")

# Teste 1: Construção do prompt de sistema
print(f"\n{'=' * 70}")
print("1️⃣  PROMPT DE SISTEMA")
print(f"{'=' * 70}")
system_prompt = agent._build_system_prompt()
print(system_prompt)

# Teste 2: Construção do prompt de usuário (sem histórico)
print(f"\n{'=' * 70}")
print("2️⃣  PROMPT DE USUÁRIO - Sem histórico")
print(f"{'=' * 70}")
user_prompt_1 = agent._build_user_prompt(
    message="Olá, gostaria de agendar uma consulta",
    context={
        "user_id": "patient_001",
        "metadata": {"source": "whatsapp", "phone": "+5511987654321"},
    },
)
print(user_prompt_1)

# Teste 3: Construção do prompt de usuário (com histórico)
print(f"\n{'=' * 70}")
print("3️⃣  PROMPT DE USUÁRIO - Com histórico")
print(f"{'=' * 70}")
user_prompt_2 = agent._build_user_prompt(
    message="Pode ser na quinta-feira?",
    context={
        "user_id": "patient_001",
        "metadata": {"source": "whatsapp", "phone": "+5511987654321"},
        "history": [
            {"role": "user", "content": "Olá, gostaria de agendar uma consulta"},
            {
                "role": "assistant",
                "content": "Olá! Claro, posso ajudar. Qual especialidade você precisa?",
            },
            {"role": "user", "content": "Cardiologista"},
            {
                "role": "assistant",
                "content": "Perfeito! Temos disponibilidade esta semana. Qual dia prefere?",
            },
        ],
    },
)
print(user_prompt_2)

print(f"\n{'=' * 70}")
print("✅ Verificação concluída!")
print(f"{'=' * 70}")
print("\n💡 Observações:")
print("   - O prompt de sistema define o papel do agente")
print("   - O prompt de usuário contextualiza a mensagem")
print("   - Histórico é mantido para continuidade da conversa")
print("   - Metadata (phone, source) é incluída no contexto")
