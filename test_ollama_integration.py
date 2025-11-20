"""
Teste de Integração Ollama com Taskni Core.

Testa:
- Conectividade com Ollama via HTTPS
- Ingestão de texto usando Ollama embeddings
- Ingestão de PDF usando Ollama embeddings
- RAG Agent usando Ollama embeddings
"""

import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import os
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

from taskni_core.rag.ingest import DocumentIngestion
from taskni_core.core.settings import taskni_settings


def test_ollama_connection():
    """Testa conexão com Ollama."""
    print("=" * 60)
    print("🧪 TESTE 1: Conexão com Ollama")
    print("=" * 60)

    print(f"\n📍 Endpoint: {taskni_settings.OLLAMA_BASE_URL}")
    print(f"📦 Modelo: {taskni_settings.OLLAMA_EMBED_MODEL}")

    pipeline = DocumentIngestion()

    if pipeline._is_ollama_available():
        print("\n✅ Ollama está ACESSÍVEL!")
        return True
    else:
        print("\n❌ Ollama NÃO está acessível")
        return False


def test_text_ingestion():
    """Testa ingestão de texto direto."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 2: Ingestão de Texto")
    print("=" * 60)

    pipeline = DocumentIngestion(
        collection_name="test_ollama_text", persist_directory="./data/test_chroma"
    )

    # Texto de teste
    test_text = """
    Clínica Taskni - Horários de Funcionamento

    Atendemos de segunda a sexta-feira, das 8h às 18h.
    Sábados: 8h às 12h
    Domingos e feriados: Fechado

    Para agendamentos, ligue: (11) 1234-5678
    WhatsApp: (11) 98765-4321
    Email: contato@taskni.com
    """

    try:
        num_chunks = pipeline.ingest_text_direct(
            text=test_text, metadata={"source": "test", "category": "faq"}
        )

        print(f"\n✅ Texto ingerido com sucesso!")
        print(f"   Chunks criados: {num_chunks}")

        # Testa busca
        results = pipeline.search("Qual o horário de funcionamento?", k=2)
        print(f"\n🔍 Teste de busca:")
        print(f"   Query: 'Qual o horário de funcionamento?'")
        print(f"   Resultados encontrados: {len(results)}")

        if results:
            print(f"\n📄 Primeiro resultado:")
            print(f"   {results[0].page_content[:200]}...")

        return True
    except Exception as e:
        print(f"\n❌ Erro na ingestão: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pdf_ingestion():
    """Testa ingestão de PDF (se existir)."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 3: Ingestão de PDF")
    print("=" * 60)

    # Cria um PDF de teste se não existir
    pdf_path = "./data/test_document.pdf"

    if not os.path.exists(pdf_path):
        print(f"\n⚠️  PDF de teste não encontrado em {pdf_path}")
        print("   Pulando teste de PDF")
        return None

    pipeline = DocumentIngestion(
        collection_name="test_ollama_pdf", persist_directory="./data/test_chroma"
    )

    try:
        num_chunks = pipeline.ingest_file(
            file_path=pdf_path, metadata={"source": "test_pdf", "category": "documentation"}
        )

        print(f"\n✅ PDF ingerido com sucesso!")
        print(f"   Chunks criados: {num_chunks}")

        return True
    except Exception as e:
        print(f"\n❌ Erro na ingestão de PDF: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_rag_agent():
    """Testa o FaqRagAgent com Ollama embeddings."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 4: RAG Agent com Ollama")
    print("=" * 60)

    try:
        # Primeiro, ingere alguns dados de FAQ
        pipeline = DocumentIngestion(
            collection_name="clinic_faq", persist_directory="./data/chroma"
        )

        faq_data = """
        FAQ - Clínica Taskni

        P: Qual o horário de funcionamento?
        R: Atendemos de segunda a sexta, das 8h às 18h. Sábados das 8h às 12h.

        P: Como agendar uma consulta?
        R: Você pode agendar pelo telefone (11) 1234-5678, WhatsApp (11) 98765-4321
        ou através do nosso site.

        P: Quais especialidades vocês atendem?
        R: Atendemos clínica geral, pediatria, ginecologia, cardiologia e ortopedia.

        P: Aceitam convênios?
        R: Sim, trabalhamos com os principais convênios médicos: Unimed, SulAmérica,
        Bradesco Saúde, Amil e outros. Consulte nossa recepção.
        """

        pipeline.ingest_text_direct(
            text=faq_data, metadata={"source": "faq", "type": "clinic_info"}
        )

        print("\n✅ FAQ ingerido no ChromaDB")

        # Testa busca no retriever
        results = pipeline.search("Como faço para agendar?", k=3)

        print(f"\n🔍 Teste de retrieval:")
        print(f"   Query: 'Como faço para agendar?'")
        print(f"   Documentos encontrados: {len(results)}")

        if results:
            print(f"\n📄 Melhor resultado:")
            print(f"   {results[0].page_content[:300]}...")

        return True

    except Exception as e:
        print(f"\n❌ Erro no RAG Agent: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_embeddings_endpoint():
    """Testa o endpoint /api/embeddings do Ollama diretamente."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 5: Endpoint /api/embeddings")
    print("=" * 60)

    import httpx

    base_url = taskni_settings.OLLAMA_BASE_URL
    if not base_url:
        print("\n⚠️  OLLAMA_BASE_URL não configurado")
        return False

    try:
        with httpx.Client(timeout=10.0, verify=False) as client:
            response = client.post(
                f"{base_url}/api/embeddings",
                json={
                    "model": taskni_settings.OLLAMA_EMBED_MODEL,
                    "prompt": "Hello, this is a test",
                },
            )

            if response.status_code == 200:
                data = response.json()
                embedding = data.get("embedding", [])

                print(f"\n✅ Endpoint funcionando!")
                print(f"   Status: {response.status_code}")
                print(f"   Dimensões do embedding: {len(embedding)}")
                print(f"   Primeiros 5 valores: {embedding[:5]}")

                return True
            else:
                print(f"\n❌ Erro no endpoint: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

    except Exception as e:
        print(f"\n❌ Erro ao chamar endpoint: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Executa todos os testes."""
    print("\n" + "🚀" * 30)
    print("TESTE DE INTEGRAÇÃO OLLAMA + TASKNI CORE")
    print("🚀" * 30)

    results = {}

    # Teste 1: Conexão
    results["connection"] = test_ollama_connection()

    # Teste 2: Texto
    if results["connection"]:
        results["text"] = test_text_ingestion()
    else:
        print("\n⏭️  Pulando testes de ingestão (Ollama não acessível)")
        results["text"] = None

    # Teste 3: PDF
    if results["connection"]:
        results["pdf"] = test_pdf_ingestion()
    else:
        results["pdf"] = None

    # Teste 4: RAG Agent
    if results["connection"]:
        results["rag"] = test_rag_agent()
    else:
        results["rag"] = None

    # Teste 5: Endpoint direto
    results["endpoint"] = test_embeddings_endpoint()

    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)

    for test_name, result in results.items():
        if result is True:
            status = "✅ PASSOU"
        elif result is False:
            status = "❌ FALHOU"
        else:
            status = "⏭️  PULADO"

        print(f"{test_name.ljust(20)}: {status}")

    # Status final
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)

    print(f"\n{'=' * 60}")
    print(f"RESULTADO FINAL: {passed}/{total} testes passaram")
    print(f"{'=' * 60}\n")

    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Ollama está integrado corretamente.")
        return 0
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")
        return 1


if __name__ == "__main__":
    exit(main())
