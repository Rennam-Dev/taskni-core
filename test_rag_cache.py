#!/usr/bin/env python
"""
Teste do sistema de cache do FaqRagAgent.

Valida que:
1. Cache hit funciona
2. Cache miss funciona
3. FIFO funciona (descarte do mais antigo)
4. Normalização de perguntas funciona
"""

import sys
import asyncio

sys.path.insert(0, "/home/user/taskni-core/src")

from taskni_core.agents.advanced.rag_agent import create_faq_rag_agent

print("=" * 80)
print("🧪 TESTE DO CACHE RAG")
print("=" * 80)


async def test_cache_miss_and_hit():
    """Testa cache miss e hit."""
    print("\n" + "=" * 80)
    print("📋 TESTE 1: Cache Miss → Hit")
    print("=" * 80)

    agent = create_faq_rag_agent(k_documents=2, enable_streaming=False)

    # Primeira query (cache miss)
    print("\n📝 Primeira consulta (deve ser cache MISS):")
    result1 = await agent.run("Qual o horário de funcionamento?")

    print(f"\nResultado 1:")
    print(f"  - Cached: {result1.get('cached', False)}")
    print(f"  - Resposta: {result1['answer'][:50]}...")

    # Segunda query igual (cache hit)
    print("\n📝 Segunda consulta (mesma pergunta - deve ser cache HIT):")
    result2 = await agent.run("Qual o horário de funcionamento?")

    print(f"\nResultado 2:")
    print(f"  - Cached: {result2.get('cached', False)}")
    print(f"  - Resposta: {result2['answer'][:50]}...")

    # Validação
    is_first_miss = not result1.get("cached", True)
    is_second_hit = result2.get("cached", False)
    same_answer = result1["answer"] == result2["answer"]

    print(f"\n{'✅' if is_first_miss else '❌'} Primeira foi cache miss")
    print(f"{'✅' if is_second_hit else '❌'} Segunda foi cache hit")
    print(f"{'✅' if same_answer else '❌'} Mesma resposta em ambas")

    return is_first_miss and is_second_hit and same_answer


async def test_cache_normalization():
    """Testa normalização de perguntas."""
    print("\n" + "=" * 80)
    print("📋 TESTE 2: Normalização de Perguntas")
    print("=" * 80)

    agent = create_faq_rag_agent(k_documents=2, enable_streaming=False)

    # Queries variantes da mesma pergunta
    queries = [
        "Qual o horário?",
        "QUAL O HORÁRIO?",  # Uppercase
        "  qual o horário?  ",  # Com espaços
    ]

    print("\n📝 Testando variações da mesma pergunta:")
    results = []

    for i, query in enumerate(queries, 1):
        print(f"\n  {i}. '{query}'")
        result = await agent.run(query)
        results.append(result)
        print(f"     Cached: {result.get('cached', False)}")

    # Validação: primeira deve ser miss, demais hit
    first_miss = not results[0].get("cached", True)
    others_hit = all(r.get("cached", False) for r in results[1:])
    all_same = len(set(r["answer"] for r in results)) == 1

    print(f"\n{'✅' if first_miss else '❌'} Primeira foi cache miss")
    print(f"{'✅' if others_hit else '❌'} Demais foram cache hit")
    print(f"{'✅' if all_same else '❌'} Todas retornaram a mesma resposta")

    return first_miss and others_hit and all_same


async def test_cache_fifo():
    """Testa descarte FIFO quando cache enche."""
    print("\n" + "=" * 80)
    print("📋 TESTE 3: FIFO (First In First Out)")
    print("=" * 80)

    # Cria agente com cache pequeno (3 entradas)
    agent = create_faq_rag_agent(k_documents=2, enable_streaming=False)
    agent.cache_size = 3

    print(f"\n📝 Cache size: {agent.cache_size}")

    # Preenche cache
    queries = [
        "Pergunta 1?",
        "Pergunta 2?",
        "Pergunta 3?",
        "Pergunta 4?",  # Deve expulsar "Pergunta 1?"
    ]

    print(f"\n📝 Adicionando {len(queries)} perguntas ao cache:")
    for query in queries:
        await agent.run(query)
        stats = agent.get_cache_stats()
        print(f"  - '{query}' → Cache: {stats['size']}/{stats['capacity']}")

    # Testa se primeira foi expulsa
    print(f"\n📝 Testando se 'Pergunta 1?' foi expulsa:")
    result1 = await agent.run("Pergunta 1?")
    is_miss = not result1.get("cached", True)

    # Testa se segunda ainda está
    print(f"📝 Testando se 'Pergunta 2?' ainda está:")
    result2 = await agent.run("Pergunta 2?")
    is_hit = result2.get("cached", False)

    print(f"\n{'✅' if is_miss else '❌'} 'Pergunta 1?' foi expulsa (cache miss)")
    print(f"{'✅' if is_hit else '❌'} 'Pergunta 2?' ainda está (cache hit)")

    return is_miss and is_hit


async def test_cache_stats():
    """Testa estatísticas do cache."""
    print("\n" + "=" * 80)
    print("📋 TESTE 4: Estatísticas do Cache")
    print("=" * 80)

    agent = create_faq_rag_agent(k_documents=2, enable_streaming=False)

    # Cache vazio
    stats = agent.get_cache_stats()
    print(f"\n📊 Cache inicial:")
    print(f"  - Size: {stats['size']}")
    print(f"  - Capacity: {stats['capacity']}")

    # Adiciona algumas queries
    await agent.run("Pergunta 1?")
    await agent.run("Pergunta 2?")
    await agent.run("Pergunta 1?")  # Repetida

    stats = agent.get_cache_stats()
    print(f"\n📊 Após 3 queries (2 únicas):")
    print(f"  - Size: {stats['size']}")
    print(f"  - Capacity: {stats['capacity']}")

    # Limpa cache
    agent.clear_cache()
    stats = agent.get_cache_stats()

    print(f"\n📊 Após clear_cache():")
    print(f"  - Size: {stats['size']}")

    is_valid = stats["size"] == 0 and stats["capacity"] == 50

    print(f"\n{'✅' if is_valid else '❌'} Cache limpo corretamente")

    return is_valid


async def main():
    """Executa todos os testes."""
    print("\n🚀 Iniciando testes de cache...\n")

    results = {
        "miss_hit": await test_cache_miss_and_hit(),
        "normalization": await test_cache_normalization(),
        "fifo": await test_cache_fifo(),
        "stats": await test_cache_stats(),
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
        print(f"\n🎉 TODOS OS TESTES DE CACHE PASSARAM!")
        print(f"\n✅ Sistema de cache funcionando:")
        print(f"   - Cache hit/miss detectado corretamente")
        print(f"   - Normalização de perguntas funcionando")
        print(f"   - FIFO descartando entradas antigas")
        print(f"   - Estatísticas precisas")
    else:
        print(f"\n⚠️  Alguns testes falharam")

    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback

        traceback.print_exc()
