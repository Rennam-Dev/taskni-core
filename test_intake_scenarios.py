#!/usr/bin/env python
"""
Testes do IntakeAgent - Validação de cenários de conversa.

Simula diferentes situações de atendimento inicial.
"""

import json
import requests

BASE_URL = "http://localhost:8080"


def test_agent(test_name: str, message: str, user_id: str, metadata: dict = None):
    """Testa o IntakeAgent com uma mensagem."""
    print(f"\n{'=' * 70}")
    print(f"🧪 {test_name}")
    print(f"{'=' * 70}")
    print(f"📥 Entrada:")
    print(f"   Mensagem: {message}")
    print(f"   User ID: {user_id}")
    if metadata:
        print(f"   Metadata: {json.dumps(metadata, indent=6)}")

    payload = {
        "agent_id": "intake-agent",
        "message": message,
        "user_id": user_id,
        "metadata": metadata or {},
    }

    response = requests.post(
        f"{BASE_URL}/agents/invoke", json=payload, headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\n📤 Resposta do Agente:")
        print(f"   {'-' * 66}")
        print(f"   {data['reply']}")
        print(f"   {'-' * 66}")
        print(f"   Agent ID: {data['agent_id']}")
        print(f"   Timestamp: {data['timestamp']}")
        return data
    else:
        print(f"\n❌ Erro {response.status_code}:")
        print(f"   {response.text}")
        return None


print("=" * 70)
print("🏥 TASKNI CORE - Testes do IntakeAgent")
print("=" * 70)

# Teste 1: Primeiro contato - Agendamento
test_agent(
    test_name="Cenário 1: Primeiro contato - Agendamento",
    message="Olá, bom dia! Gostaria de agendar uma consulta",
    user_id="patient_001",
    metadata={"source": "whatsapp", "phone": "+5511987654321"},
)

# Teste 2: Dúvida sobre procedimento
test_agent(
    test_name="Cenário 2: Dúvida sobre procedimento",
    message="Quanto custa uma consulta de rotina?",
    user_id="patient_002",
    metadata={"source": "whatsapp", "phone": "+5511912345678"},
)

# Teste 3: Urgência
test_agent(
    test_name="Cenário 3: Urgência médica",
    message="Meu filho está com febre alta há 2 dias, preciso de atendimento urgente",
    user_id="patient_003",
    metadata={"source": "whatsapp", "phone": "+5511999887766", "urgency": "high"},
)

# Teste 4: Informação sobre resultados
test_agent(
    test_name="Cenário 4: Consulta de resultados",
    message="Gostaria de saber se meus exames já ficaram prontos",
    user_id="patient_004",
    metadata={"source": "web", "existing_patient": True},
)

# Teste 5: Horário de funcionamento
test_agent(
    test_name="Cenário 5: Informação geral",
    message="Qual o horário de atendimento da clínica?",
    user_id="patient_005",
    metadata={"source": "web"},
)

print("\n" + "=" * 70)
print("✅ Todos os testes executados!")
print("=" * 70)
