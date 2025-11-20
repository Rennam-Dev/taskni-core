#!/usr/bin/env python
"""
Teste de validação Pydantic nos inputs dos agentes.

Valida que:
1. Inputs válidos são aceitos
2. Inputs inválidos geram erros claros
3. Validações específicas funcionam
"""

import sys

sys.path.insert(0, "/home/user/taskni-core/src")

from pydantic import ValidationError

from taskni_core.schema.agent_inputs import FollowupInput, IntakeInput, RagQueryInput

print("=" * 80)
print("🧪 TESTE DE VALIDAÇÃO PYDANTIC")
print("=" * 80)


def test_followup_input_valid():
    """Testa input válido do FollowupAgent."""
    print("\n" + "=" * 80)
    print("📋 TESTE 1: FollowupInput Válido")
    print("=" * 80)

    # Input válido
    data = {
        "patient_name": "João Silva",
        "days_inactive": 45,
        "last_message": "Obrigado!",
        "context": {"is_patient": True},
    }

    try:
        input_obj = FollowupInput(**data)
        print("\n✅ Input válido aceito:")
        print(f"   - Nome: {input_obj.patient_name}")
        print(f"   - Dias: {input_obj.days_inactive}")
        print(f"   - Mensagem: {input_obj.last_message}")
        return True
    except ValidationError as e:
        print(f"\n❌ Erro inesperado: {e}")
        return False


def test_followup_input_invalid_days():
    """Testa days_inactive negativo."""
    print("\n" + "=" * 80)
    print("📋 TESTE 2: FollowupInput - Days Negativo")
    print("=" * 80)

    data = {
        "patient_name": "João Silva",
        "days_inactive": -5,  # Inválido!
        "last_message": "Obrigado!",
    }

    try:
        FollowupInput(**data)
        print("\n❌ Input inválido aceito (deveria rejeitar)")
        return False
    except ValidationError as e:
        print("\n✅ Input inválido rejeitado corretamente:")
        print(f"   Erro: {e.errors()[0]['msg']}")
        return True


def test_followup_input_empty_name():
    """Testa nome vazio."""
    print("\n" + "=" * 80)
    print("📋 TESTE 3: FollowupInput - Nome Vazio")
    print("=" * 80)

    data = {
        "patient_name": "   ",  # Apenas espaços
        "days_inactive": 10,
    }

    try:
        FollowupInput(**data)
        print("\n❌ Nome vazio aceito (deveria rejeitar)")
        return False
    except ValidationError as e:
        print("\n✅ Nome vazio rejeitado corretamente:")
        print(f"   Erro: {e.errors()[0]['msg']}")
        return True


def test_followup_input_missing_required():
    """Testa campos obrigatórios faltando."""
    print("\n" + "=" * 80)
    print("📋 TESTE 4: FollowupInput - Campos Obrigatórios")
    print("=" * 80)

    data = {
        "patient_name": "João Silva",
        # Falta days_inactive!
    }

    try:
        FollowupInput(**data)
        print("\n❌ Campo obrigatório faltando aceito (deveria rejeitar)")
        return False
    except ValidationError as e:
        print("\n✅ Campo obrigatório faltando rejeitado:")
        print(f"   Erro: {e.errors()[0]['msg']}")
        return True


def test_rag_query_input_valid():
    """Testa input válido do RagQueryInput."""
    print("\n" + "=" * 80)
    print("📋 TESTE 5: RagQueryInput Válido")
    print("=" * 80)

    data = {"question": "Qual o horário de funcionamento?", "k_documents": 4}

    try:
        input_obj = RagQueryInput(**data)
        print("\n✅ Input válido aceito:")
        print(f"   - Pergunta: {input_obj.question}")
        print(f"   - K docs: {input_obj.k_documents}")
        return True
    except ValidationError as e:
        print(f"\n❌ Erro inesperado: {e}")
        return False


def test_rag_query_input_k_out_of_range():
    """Testa k_documents fora do range."""
    print("\n" + "=" * 80)
    print("📋 TESTE 6: RagQueryInput - K Fora do Range")
    print("=" * 80)

    data = {
        "question": "Pergunta válida",
        "k_documents": 50,  # Máximo é 10
    }

    try:
        RagQueryInput(**data)
        print("\n❌ K fora do range aceito (deveria rejeitar)")
        return False
    except ValidationError as e:
        print("\n✅ K fora do range rejeitado:")
        print(f"   Erro: {e.errors()[0]['msg']}")
        return True


def test_intake_input_valid():
    """Testa input válido do IntakeInput."""
    print("\n" + "=" * 80)
    print("📋 TESTE 7: IntakeInput Válido")
    print("=" * 80)

    data = {
        "message": "Gostaria de agendar uma consulta",
        "user_id": "patient_001",
        "metadata": {"phone": "+5511987654321"},
    }

    try:
        input_obj = IntakeInput(**data)
        print("\n✅ Input válido aceito:")
        print(f"   - Mensagem: {input_obj.message}")
        print(f"   - User ID: {input_obj.user_id}")
        return True
    except ValidationError as e:
        print(f"\n❌ Erro inesperado: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("\n🚀 Iniciando testes de validação...\n")

    results = {
        "followup_valid": test_followup_input_valid(),
        "followup_invalid_days": test_followup_input_invalid_days(),
        "followup_empty_name": test_followup_input_empty_name(),
        "followup_missing": test_followup_input_missing_required(),
        "rag_valid": test_rag_query_input_valid(),
        "rag_k_range": test_rag_query_input_k_out_of_range(),
        "intake_valid": test_intake_input_valid(),
    }

    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"\n✅ Testes passaram: {passed}/{total}")

    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {name}")

    if passed == total:
        print("\n🎉 TODOS OS TESTES DE VALIDAÇÃO PASSARAM!")
        print("\n✅ Sistema de validação Pydantic funcionando:")
        print("   - Inputs válidos são aceitos")
        print("   - Inputs inválidos são rejeitados")
        print("   - Mensagens de erro claras")
    else:
        print("\n⚠️  Alguns testes falharam")

    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback

        traceback.print_exc()
