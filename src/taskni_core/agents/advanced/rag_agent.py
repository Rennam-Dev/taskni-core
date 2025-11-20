"""
FAQ RAG Agent - Agente de perguntas frequentes com RAG.

Usa LangGraph para implementar um workflow de:
1. Retrieval: Busca documentos relevantes no ChromaDB
2. Generation: Gera resposta usando LLM + contexto recuperado

Este é um agente AVANÇADO (usa LangGraph completo).
"""

import hashlib
from collections import OrderedDict
from collections.abc import Sequence
from operator import add
from typing import Annotated, Any, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from taskni_core.core.llm_provider import MultiProviderLLM
from taskni_core.core.settings import taskni_settings
from taskni_core.rag.ingest import get_ingestion_pipeline
from taskni_core.utils.security import sanitize_prompt_input

# ============================================================================
# State Definition
# ============================================================================


class RagState(TypedDict):
    """
    Estado do agente RAG.

    Campos:
    - question: Pergunta do usuário
    - retrieved_docs: Documentos recuperados do vector store
    - context: Contexto formatado dos documentos
    - answer: Resposta final gerada
    - sources: Fontes dos documentos
    - messages: Histórico de mensagens (para LangGraph)
    """

    question: str
    retrieved_docs: list[Document]
    context: str
    answer: str
    sources: list[str]
    messages: Annotated[Sequence[BaseMessage], add]


# ============================================================================
# Agent Nodes
# ============================================================================


class FaqRagAgent:
    """
    Agente RAG para FAQ usando LangGraph.

    Workflow:
    1. retrieve_documents: Busca documentos relevantes
    2. generate_answer: Gera resposta usando LLM + contexto
    """

    # Metadata do agente (para o registry)
    id = "faq-rag-agent"
    name = "Agente RAG de FAQ"
    description = (
        "Responde perguntas frequentes usando RAG (Retrieval-Augmented Generation). "
        "Busca documentos relevantes e gera respostas baseadas no contexto recuperado."
    )

    def __init__(self, k_documents: int = 4, enable_streaming: bool = True, cache_size: int = 50):
        """
        Inicializa o agente RAG.

        Args:
            k_documents: Número de documentos a recuperar
            enable_streaming: Habilitar streaming nas respostas
            cache_size: Tamanho máximo do cache (default: 50)
        """
        self.k_documents = k_documents
        self.enable_streaming = enable_streaming
        self.cache_size = cache_size

        # Inicializa LLM multi-provider
        self.llm = MultiProviderLLM(enable_streaming=enable_streaming)

        # Inicializa pipeline de ingestão/retrieval
        self.ingestion = get_ingestion_pipeline()

        # Cache para respostas (FIFO com OrderedDict)
        # Estrutura: {cache_key: {"answer": str, "sources": List[str]}}
        self.cache: OrderedDict[str, dict[str, Any]] = OrderedDict()

        # Constrói o grafo LangGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Constrói o grafo LangGraph do agente."""
        # Cria workflow
        workflow = StateGraph(RagState)

        # Adiciona nodes
        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("generate", self._generate_answer)

        # Define edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        # Compila o grafo
        return workflow.compile()

    def _retrieve_documents(self, state: RagState) -> RagState:
        """
        Node 1: Recupera documentos relevantes do vector store.

        Args:
            state: Estado atual

        Returns:
            Estado atualizado com documentos recuperados
        """
        question = state["question"]

        print(f"🔍 Buscando documentos para: '{question}'")

        # Busca documentos similares
        docs = self.ingestion.search(query=question, k=self.k_documents)

        print(f"   ✅ {len(docs)} documentos recuperados")

        # Formata contexto
        context_parts = []
        sources = []

        for i, doc in enumerate(docs, 1):
            # Adiciona documento ao contexto
            context_parts.append(f"[Documento {i}]\n{doc.page_content}\n")

            # Adiciona fonte
            source = doc.metadata.get("source_file", f"doc_{i}")
            page = doc.metadata.get("page", "")
            if page:
                sources.append(f"{source} (página {page})")
            else:
                sources.append(source)

        context = "\n".join(context_parts)

        # Atualiza estado
        return {
            **state,
            "retrieved_docs": docs,
            "context": context,
            "sources": sources,
        }

    def _generate_answer(self, state: RagState) -> RagState:
        """
        Node 2: Gera resposta usando LLM + contexto recuperado.

        Args:
            state: Estado atual

        Returns:
            Estado atualizado com resposta gerada
        """
        question = state["question"]
        context = state["context"]

        print("🤖 Gerando resposta...")

        # Template do prompt
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self._get_system_prompt()),
                ("human", self._get_user_prompt_template()),
            ]
        )

        # Formata prompt
        messages = prompt_template.format_messages(
            business_name=taskni_settings.BUSINESS_NAME,
            language=taskni_settings.DEFAULT_LANGUAGE,
            context=context,
            question=question,
        )

        # Converte para formato dict
        messages_dict = [
            {"role": "system", "content": messages[0].content},
            {"role": "user", "content": messages[1].content},
        ]

        # Gera resposta
        response = self.llm.invoke_sync(messages_dict)

        print("   ✅ Resposta gerada")

        # Atualiza estado
        return {
            **state,
            "answer": response,
            "messages": state.get("messages", [])
            + [
                HumanMessage(content=question),
                AIMessage(content=response),
            ],
        }

    def _get_system_prompt(self) -> str:
        """Retorna o prompt de sistema do agente."""
        return """Você é um assistente especializado em responder perguntas frequentes (FAQ).

Seu papel:
1. Analisar cuidadosamente o contexto fornecido (documentos recuperados)
2. Responder a pergunta do usuário baseado EXCLUSIVAMENTE no contexto
3. Se a informação não estiver no contexto, dizer "Não encontrei essa informação na base de conhecimento"
4. Ser claro, objetivo e útil
5. Citar as fontes quando apropriado

IMPORTANTE:
- NÃO invente informações que não estão no contexto
- Se não tiver certeza, seja honesto
- Mantenha um tom profissional e acolhedor
"""

    def _get_user_prompt_template(self) -> str:
        """Retorna o template do prompt do usuário."""
        return """Contexto (documentos recuperados):
{context}

---

Pergunta do usuário: {question}

Por favor, responda a pergunta baseado no contexto acima. Se a informação não estiver no contexto, seja honesto e diga que não encontrou.

Responda em {language}."""

    def _get_cache_key(self, question: str) -> str:
        """
        Gera chave de cache para uma pergunta.

        Args:
            question: Pergunta do usuário

        Returns:
            Hash MD5 da pergunta normalizada
        """
        # Normaliza a pergunta (lowercase, strip)
        normalized = question.lower().strip()
        # Gera hash MD5
        return hashlib.md5(normalized.encode()).hexdigest()

    def _get_from_cache(self, question: str) -> dict[str, Any] | None:
        """
        Busca resposta no cache.

        Args:
            question: Pergunta do usuário

        Returns:
            Dict com answer e sources, ou None se não encontrado
        """
        cache_key = self._get_cache_key(question)

        if cache_key in self.cache:
            # Move para o final (LRU behavior)
            self.cache.move_to_end(cache_key)
            print(f"   💾 Resposta encontrada no cache (key: {cache_key[:8]}...)")
            return self.cache[cache_key]

        return None

    def _save_to_cache(self, question: str, answer: str, sources: list[str]):
        """
        Salva resposta no cache.

        Args:
            question: Pergunta do usuário
            answer: Resposta gerada
            sources: Fontes dos documentos
        """
        cache_key = self._get_cache_key(question)

        # Se cache está cheio, remove o mais antigo (FIFO)
        if len(self.cache) >= self.cache_size:
            # Remove primeiro item (mais antigo)
            oldest_key = next(iter(self.cache))
            self.cache.pop(oldest_key)
            print("   🗑️  Cache cheio: removendo entrada antiga")

        # Adiciona ao cache
        self.cache[cache_key] = {
            "answer": answer,
            "sources": sources,
        }

        print(f"   💾 Resposta salva no cache ({len(self.cache)}/{self.cache_size})")

    def get_cache_stats(self) -> dict[str, int]:
        """
        Retorna estatísticas do cache.

        Returns:
            Dict com size e capacity
        """
        return {
            "size": len(self.cache),
            "capacity": self.cache_size,
        }

    def clear_cache(self):
        """Limpa todo o cache."""
        self.cache.clear()
        print("   🗑️  Cache limpo")

    async def run(self, question: str) -> dict:
        """
        Executa o agente RAG com cache e sanitização de input.

        Args:
            question: Pergunta do usuário

        Returns:
            Dict com answer, sources, retrieved_docs, cached
        """
        print(f"\n{'=' * 80}")
        print("🤖 FaqRagAgent: Processando pergunta")
        print(f"{'=' * 80}")

        # SANITIZA O INPUT PARA PREVENIR PROMPT INJECTION
        # Permite quebras de linha pois perguntas podem ser multilinhas
        question = sanitize_prompt_input(question, max_length=500, allow_multiline=True)

        # Tenta buscar no cache
        cached_result = self._get_from_cache(question)

        if cached_result is not None:
            print(f"{'=' * 80}\n")
            return {
                "answer": cached_result["answer"],
                "sources": cached_result["sources"],
                "retrieved_docs": [],  # Não retorna docs do cache
                "cached": True,
            }

        # Não está no cache - executa workflow normal
        print("   🔄 Cache miss - executando workflow RAG...")

        # Estado inicial
        initial_state = {
            "question": question,
            "retrieved_docs": [],
            "context": "",
            "answer": "",
            "sources": [],
            "messages": [],
        }

        # Executa o grafo
        final_state = await self.graph.ainvoke(initial_state)

        # Salva no cache
        self._save_to_cache(
            question=question, answer=final_state["answer"], sources=final_state["sources"]
        )

        print(f"{'=' * 80}\n")

        # Retorna resultado
        return {
            "answer": final_state["answer"],
            "sources": final_state["sources"],
            "retrieved_docs": final_state["retrieved_docs"],
            "cached": False,
        }

    def invoke_sync(self, question: str) -> dict:
        """Versão síncrona do run() para compatibilidade."""
        import asyncio

        return asyncio.run(self.run(question))


# ============================================================================
# Factory Function
# ============================================================================


def create_faq_rag_agent(k_documents: int = 4, enable_streaming: bool = True) -> FaqRagAgent:
    """
    Factory para criar instância do FaqRagAgent.

    Args:
        k_documents: Número de documentos a recuperar
        enable_streaming: Habilitar streaming

    Returns:
        Instância do FaqRagAgent (já compilado)
    """
    return FaqRagAgent(k_documents=k_documents, enable_streaming=enable_streaming)
