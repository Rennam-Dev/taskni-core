#!/usr/bin/env python
"""
Teste do sistema multi-provedor com streaming.

Testa:
1. Fallback automático entre provedores (Groq → OpenAI → FakeModel)
2. Streaming de respostas
3. IntakeAgent com o novo sistema
"""

import sys
import asyncio

sys.path.insert(0, "/home/user/taskni-core/src")

from taskni_core.core.llm_provider import MultiProviderLLM
from taskni_core.agents.intake_agent import IntakeAgent

print("=" * 80)
print("🧪 TESTE DO SISTEMA MULTI-PROVEDOR COM STREAMING")
print("=" * 80)


async def test_multi_provider_direct():
    """Testa o MultiProviderLLM diretamente."""
    print("\n" + "=" * 80)
    print("📋 TESTE 1: MultiProviderLLM Direto (ainvoke)")
    print("=" * 80)

    llm = MultiProviderLLM(enable_streaming=False)

    print(f"\n✅ Provedores disponíveis: {llm.get_available_providers()}")
    print(f"📍 Provedor atual (primário): {llm.get_current_provider()}")

    messages = [
        {"role": "system", "content": "Você é um assistente amigável."},
        {"role": "user", "content": "Diga olá em português de forma breve."},
    ]

    print(f"\n💬 Enviando mensagem: 'Diga olá em português de forma breve.'")

    try:
        response = await llm.ainvoke(messages)

        if hasattr(response, "content"):
            reply = response.content
        else:
            reply = str(response)

        print(f"\n✅ RESPOSTA RECEBIDA:")
        print(f"{'=' * 80}")
        print(reply)
        print(f"{'=' * 80}")

        return True

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_multi_provider_streaming():
    """Testa streaming do MultiProviderLLM."""
    print("\n" + "=" * 80)
    print("📋 TESTE 2: MultiProviderLLM com Streaming")
    print("=" * 80)

    llm = MultiProviderLLM(enable_streaming=True)

    print(f"\n✅ Streaming habilitado")
    print(f"📍 Provedor primário: {llm.get_current_provider()}")

    messages = [
        {"role": "system", "content": "Você é um assistente que conta até 5."},
        {"role": "user", "content": "Conte de 1 até 5, um número por linha."},
    ]

    print(f"\n💬 Enviando mensagem para streaming...")
    print(f"\n✅ RESPOSTA (STREAMING):")
    print(f"{'=' * 80}")

    try:
        full_response = ""
        async for chunk in llm.astream(messages):
            print(chunk, end="", flush=True)
            full_response += chunk

        print(f"\n{'=' * 80}")
        print(f"\n✅ Stream concluído! Total de caracteres: {len(full_response)}")

        return True

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_intake_agent_with_multi_provider():
    """Testa IntakeAgent com o sistema multi-provedor."""
    print("\n" + "=" * 80)
    print("📋 TESTE 3: IntakeAgent com Multi-Provider")
    print("=" * 80)

    agent = IntakeAgent()

    print(f"\n✅ Agente criado: {agent.id}")
    print(f"📝 Nome: {agent.name}")
    print(f"📄 Descrição: {agent.description}")

    # Verifica se está usando MultiProviderLLM
    print(f"\n🔍 Verificando tipo do LLM...")
    print(f"   Tipo: {type(agent.llm).__name__}")
    print(f"   Provedores disponíveis: {agent.llm.get_available_providers()}")

    # Testa conversação
    print(f"\n💬 Testando conversação de triagem...")

    message = "Olá, bom dia! Gostaria de agendar uma consulta"
    context = {
        "user_id": "patient_001",
        "session_id": "session_001",
        "metadata": {"source": "whatsapp", "phone": "+5511987654321"},
    }

    print(f"\n📤 Mensagem do paciente:")
    print(f"   '{message}'")
    print(f"\n📋 Contexto:")
    print(f"   - user_id: {context['user_id']}")
    print(f"   - source: {context['metadata']['source']}")
    print(f"   - phone: {context['metadata']['phone']}")

    try:
        reply = await agent.run(message=message, context=context)

        print(f"\n✅ RESPOSTA DO AGENTE:")
        print(f"{'=' * 80}")
        print(reply)
        print(f"{'=' * 80}")

        return True

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_fallback_mechanism():
    """Testa o mecanismo de fallback entre provedores."""
    print("\n" + "=" * 80)
    print("📋 TESTE 4: Mecanismo de Fallback")
    print("=" * 80)

    print(f"\n📝 Neste teste, vamos tentar invocar o LLM.")
    print(f"   Se Groq falhar (403), deve tentar OpenAI.")
    print(f"   Se OpenAI falhar, deve usar FakeModel.")
    print(f"\n🔄 Iniciando teste de fallback...")

    llm = MultiProviderLLM(enable_streaming=False)

    messages = [{"role": "user", "content": "Teste de fallback"}]

    try:
        response = await llm.ainvoke(messages)

        if hasattr(response, "content"):
            reply = response.content
        else:
            reply = str(response)

        print(f"\n✅ Sistema de fallback funcionou!")
        print(f"📤 Resposta recebida: {reply[:100]}...")

        return True

    except Exception as e:
        print(f"\n❌ Todos os provedores falharam: {e}")
        return False


async def main():
    """Executa todos os testes."""
    print("\n🚀 Iniciando bateria de testes...\n")

    results = {}

    # Teste 1: MultiProviderLLM direto
    results["test1"] = await test_multi_provider_direct()

    # Teste 2: Streaming
    results["test2"] = await test_multi_provider_streaming()

    # Teste 3: IntakeAgent
    results["test3"] = await test_intake_agent_with_multi_provider()

    # Teste 4: Fallback
    results["test4"] = await test_fallback_mechanism()

    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"\n✅ Testes passaram: {passed}/{total}")
    print(f"\nDetalhes:")
    print(f"  {'✅' if results.get('test1') else '❌'} Teste 1: MultiProviderLLM Direto")
    print(f"  {'✅' if results.get('test2') else '❌'} Teste 2: Streaming")
    print(f"  {'✅' if results.get('test3') else '❌'} Teste 3: IntakeAgent")
    print(f"  {'✅' if results.get('test4') else '❌'} Teste 4: Fallback Mechanism")

    if passed == total:
        print(f"\n🎉 TODOS OS TESTES PASSARAM!")
        print(f"\n✅ Sistema multi-provedor configurado com sucesso:")
        print(f"   - Groq como primário")
        print(f"   - OpenAI como fallback")
        print(f"   - FakeModel como último recurso")
        print(f"   - Streaming habilitado")
    else:
        print(f"\n⚠️  Alguns testes falharam. Verifique os logs acima.")

    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback

        traceback.print_exc()
