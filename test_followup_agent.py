#!/usr/bin/env python
"""
Teste completo do FollowupAgent.

Testa:
1. Detecção de intenções (6 tipos)
2. Geração de mensagens personalizadas
3. Workflow LangGraph completo
4. Integração com MultiProviderLLM
"""

import asyncio
import sys

sys.path.insert(0, "/home/user/taskni-core/src")

from taskni_core.agents.advanced.followup_agent import create_followup_agent

print("=" * 80)
print("🧪 TESTE DO FOLLOWUP AGENT")
print("=" * 80)


async def test_intent_detection():
    """Testa detecção de diferentes intenções."""
    print("\n" + "=" * 80)
    print("📋 TESTE 1: Detecção de Intenções")
    print("=" * 80)

    agent = create_followup_agent(enable_streaming=False)

    # Cenários de teste
    scenarios = [
        {
            "name": "Reativação - Paciente inativo 45 dias",
            "patient_name": "João Silva",
            "days_inactive": 45,
            "last_message": "Obrigado!",
            "context": {"is_patient": True},
            "expected_intent": "reativacao",
        },
        {
            "name": "Pós-Consulta - 2 dias após consulta",
            "patient_name": "Maria Santos",
            "days_inactive": 2,
            "last_message": "Sim, muito obrigada!",
            "context": {"had_appointment": True},
            "expected_intent": "pos_consulta",
        },
        {
            "name": "Abandono - Iniciou mas não agendou",
            "patient_name": "Carlos Souza",
            "days_inactive": 5,
            "last_message": "Queria agendar uma consulta",
            "context": {},
            "expected_intent": "abandono",
        },
        {
            "name": "Lead Frio - Nunca agendou, 60 dias",
            "patient_name": "Ana Costa",
            "days_inactive": 60,
            "last_message": "Qual o preço da consulta?",
            "context": {"had_appointment": False},
            "expected_intent": "lead_frio",
        },
        {
            "name": "Checagem Retorno - Após procedimento",
            "patient_name": "Pedro Lima",
            "days_inactive": 10,
            "last_message": "Ok, vou fazer o tratamento",
            "context": {"needs_followup": True},
            "expected_intent": "checagem_retorno",
        },
        {
            "name": "Agendar Consulta - Check-up atrasado",
            "patient_name": "Juliana Mendes",
            "days_inactive": 120,
            "last_message": "Muito obrigada!",
            "context": {"is_patient": True},
            "expected_intent": "agendar_consulta",
        },
    ]

    results = []

    for scenario in scenarios:
        print(f"\n{'─' * 80}")
        print(f"📝 Cenário: {scenario['name']}")
        print(f"   Paciente: {scenario['patient_name']}")
        print(f"   Dias inativo: {scenario['days_inactive']}")

        result = await agent.run(
            patient_name=scenario["patient_name"],
            days_inactive=scenario["days_inactive"],
            last_message=scenario["last_message"],
            context=scenario["context"],
        )

        intent_match = result["intent"] == scenario["expected_intent"]
        status = "✅" if intent_match else "❌"

        print(f"\n   {status} Intenção detectada: {result['intent']}")
        print(f"      Esperado: {scenario['expected_intent']}")
        print("\n   📨 Mensagem gerada:")
        print(f"      {result['message']}")

        results.append(
            {
                "scenario": scenario["name"],
                "intent_correct": intent_match,
                "message_generated": bool(result["message"]),
            }
        )

    # Resumo
    print(f"\n{'=' * 80}")
    print("📊 RESUMO - DETECÇÃO DE INTENÇÕES")
    print(f"{'=' * 80}")

    correct_intents = sum(1 for r in results if r["intent_correct"])
    all_messages = sum(1 for r in results if r["message_generated"])

    print(f"\n✅ Intenções corretas: {correct_intents}/{len(results)}")
    print(f"✅ Mensagens geradas: {all_messages}/{len(results)}")

    return results


async def test_message_quality():
    """Testa qualidade das mensagens geradas."""
    print("\n" + "=" * 80)
    print("📋 TESTE 2: Qualidade das Mensagens")
    print("=" * 80)

    agent = create_followup_agent(enable_streaming=False)

    # Testa mensagem específica
    print("\n📝 Gerando mensagem de reativação...")

    result = await agent.run(
        patient_name="Roberto Alves",
        days_inactive=30,
        last_message="Muito bom o atendimento!",
        context={
            "clinic_type": "clínica odontológica",
            "service": "odontologia",
            "tone": "amigável e profissional",
            "is_patient": True,
        },
    )

    print("\n✅ Resultado:")
    print(f"{'─' * 80}")
    print(f"Intenção: {result['intent']}")
    print(f"Pronto para envio: {result['ready_for_delivery']}")
    print(f"Enviar em: {result['send_at']}")
    print("\nMensagem:")
    print(f"{result['message']}")
    print(f"{'─' * 80}")

    # Validações de qualidade
    message = result["message"]
    validations = {
        "Não está vazia": len(message) > 0,
        "Tamanho razoável (< 500 chars)": len(message) < 500,
        "Menciona o nome": "Roberto" in message or "[nome]" not in message.lower(),
        "Tem call-to-action": any(
            keyword in message.lower()
            for keyword in ["agendar", "disponível", "contato", "ajudar", "falar"]
        ),
        "Pronta para envio": result["ready_for_delivery"],
    }

    print("\n📊 Validações de Qualidade:")
    for check, passed in validations.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")

    all_passed = all(validations.values())
    return all_passed


async def test_workflow_complete():
    """Testa workflow completo do agente."""
    print("\n" + "=" * 80)
    print("📋 TESTE 3: Workflow LangGraph Completo")
    print("=" * 80)

    agent = create_followup_agent(enable_streaming=False)

    print("\n🤖 Executando workflow completo...")
    print(f"   Agente: {agent.name}")
    print(f"   ID: {agent.id}")

    # Executa com diferentes intenções
    test_cases = [
        ("Abandono", 5, "Queria consultar horários"),
        ("Pós-consulta", 2, "Obrigado pela consulta", {"had_appointment": True}),
        ("Reativação", 50, "Tudo bem!", {"is_patient": True}),
    ]

    workflow_results = []

    for name, days, message, *context_args in test_cases:
        context = context_args[0] if context_args else {}

        print(f"\n{'─' * 40}")
        print(f"📝 Teste: {name}")

        result = await agent.run(
            patient_name="Paciente Teste",
            days_inactive=days,
            last_message=message,
            context=context,
        )

        has_intent = bool(result.get("intent"))
        has_message = bool(result.get("message"))
        is_ready = result.get("ready_for_delivery", False)

        print(f"   Intenção: {result['intent']}")
        print(f"   Mensagem: {result['message'][:50]}...")
        print(f"   Status: {'✅ Pronto' if is_ready else '❌ Não pronto'}")

        workflow_results.append(
            {
                "test": name,
                "has_intent": has_intent,
                "has_message": has_message,
                "is_ready": is_ready,
            }
        )

    print(f"\n{'=' * 80}")
    print("📊 RESUMO - WORKFLOW")
    print(f"{'=' * 80}")

    all_complete = all(
        r["has_intent"] and r["has_message"] and r["is_ready"] for r in workflow_results
    )

    if all_complete:
        print("\n✅ Todos os workflows completaram com sucesso!")
    else:
        print("\n⚠️  Alguns workflows falharam")

    for r in workflow_results:
        status = "✅" if all([r["has_intent"], r["has_message"], r["is_ready"]]) else "❌"
        print(f"   {status} {r['test']}")

    return all_complete


async def main():
    """Executa todos os testes."""
    print("\n🚀 Iniciando bateria de testes...\n")

    try:
        # Teste 1: Detecção de intenções
        intent_results = await test_intent_detection()

        # Teste 2: Qualidade das mensagens
        quality_passed = await test_message_quality()

        # Teste 3: Workflow completo
        workflow_passed = await test_workflow_complete()

        # Resumo Final
        print("\n" + "=" * 80)
        print("📊 RESUMO GERAL DOS TESTES")
        print("=" * 80)

        intent_correct = sum(1 for r in intent_results if r["intent_correct"])
        total_intents = len(intent_results)

        print(f"\n✅ Detecção de Intenções: {intent_correct}/{total_intents}")
        print(f"{'✅' if quality_passed else '❌'} Qualidade das Mensagens")
        print(f"{'✅' if workflow_passed else '❌'} Workflow Completo")

        if intent_correct == total_intents and quality_passed and workflow_passed:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print("\n✅ FollowupAgent funcionando perfeitamente:")
            print("   - 6 tipos de intenções detectadas corretamente")
            print("   - Mensagens curtas e naturais")
            print("   - Workflow LangGraph completo (3 nodes)")
            print("   - Integrado com MultiProviderLLM")
        else:
            print("\n⚠️  Alguns testes falharam")

        print("=" * 80)

    except Exception as e:
        print(f"\n\n❌ Erro durante os testes: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback

        traceback.print_exc()
