"""
Pipeline de ingestão de documentos para RAG.

Suporta:
- PDFs
- Arquivos de texto (.txt, .md)
- Chunking inteligente
- Embeddings com múltiplos provedores
- Armazenamento em ChromaDB
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import FakeEmbeddings, OllamaEmbeddings

from core.settings import settings
from taskni_core.core.settings import taskni_settings
from taskni_core.utils.security import sanitize_rag_filter

# Para detecção de firewall
try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class DocumentIngestion:
    """
    Pipeline de ingestão de documentos.

    Processa documentos (PDFs, textos), faz chunking,
    cria embeddings e armazena no ChromaDB.
    """

    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = "taskni_docs",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Inicializa o pipeline de ingestão.

        Args:
            persist_directory: Diretório para persistir ChromaDB
            collection_name: Nome da coleção no ChromaDB
            chunk_size: Tamanho dos chunks de texto
            chunk_overlap: Sobreposição entre chunks
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Cria diretório se não existir
        os.makedirs(persist_directory, exist_ok=True)

        # Inicializa text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

        # Inicializa embeddings
        self.embeddings = self._get_embeddings()

        # Inicializa vector store
        self.vectorstore = self._get_vectorstore()

    def _is_ollama_available(self) -> bool:
        """
        Detecta se o Ollama está disponível e acessível.

        Returns:
            True se Ollama está acessível, False caso contrário
        """
        if not taskni_settings.OLLAMA_BASE_URL:
            return False

        if not HTTPX_AVAILABLE:
            return False

        try:
            # Tenta acessar o endpoint /api/tags do Ollama
            base_url = taskni_settings.OLLAMA_BASE_URL.rstrip("/")
            with httpx.Client(
                timeout=3.0, verify=False
            ) as client:  # verify=False para HTTPS auto-assinado
                response = client.get(f"{base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            print(f"⚠️  Ollama não acessível: {e}")
            return False

    def _is_firewalled(self) -> bool:
        """
        Detecta se o ambiente está atrás de firewall/proxy.

        Tenta acessar a API da OpenAI para verificar conectividade.

        Returns:
            True se está bloqueado, False se tem acesso
        """
        if not HTTPX_AVAILABLE:
            # Se httpx não está disponível, assume que está bloqueado
            return True

        try:
            # Tenta acessar endpoint da OpenAI com timeout curto
            with httpx.Client(timeout=2.0) as client:
                response = client.get("https://api.openai.com/v1/models")
                # Se chegou aqui, não está bloqueado
                return False
        except Exception:
            # Qualquer erro (timeout, connection, SSL, etc) = bloqueado
            return True

    def _get_embeddings(self):
        """
        Retorna embeddings configurados com detecção automática.

        Prioridade:
        1. Ollama (se configurado e acessível) - RECOMENDADO para produção
        2. OpenAI (se chave existe E ambiente não está bloqueado)
        3. FakeEmbeddings (desenvolvimento ou quando há restrições)

        Returns:
            Instância de embeddings configurada
        """
        # 1. PRIORIDADE: Ollama (embeddings locais/self-hosted)
        if taskni_settings.OLLAMA_BASE_URL:
            if self._is_ollama_available():
                try:
                    print(f"✅ Usando Ollama Embeddings ({taskni_settings.OLLAMA_EMBED_MODEL})")
                    print(f"   Endpoint: {taskni_settings.OLLAMA_BASE_URL}")
                    return OllamaEmbeddings(
                        base_url=taskni_settings.OLLAMA_BASE_URL,
                        model=taskni_settings.OLLAMA_EMBED_MODEL,
                    )
                except Exception as e:
                    print(f"⚠️  Ollama Embeddings falhou: {e}")
                    print("📝 Tentando fallback...")
            else:
                print(f"⚠️  Ollama não está acessível em {taskni_settings.OLLAMA_BASE_URL}")
                print("📝 Tentando fallback...")

        # 2. FALLBACK 1: OpenAI (se chave existe)
        if settings.OPENAI_API_KEY:
            # Detecta se ambiente está bloqueado
            is_blocked = self._is_firewalled()

            if not is_blocked:
                # Ambiente OK - usa OpenAI
                try:
                    print("✅ Usando OpenAI Embeddings (text-embedding-3-small)")
                    return OpenAIEmbeddings(
                        api_key=settings.OPENAI_API_KEY.get_secret_value(),
                        model="text-embedding-3-small",  # Mais barato
                    )
                except Exception as e:
                    print(f"⚠️  OpenAI Embeddings falhou: {e}")
                    print("📝 Fallback para FakeEmbeddings")
                    return FakeEmbeddings(size=768)  # nomic-embed-text usa 768 dims
            else:
                # Ambiente bloqueado
                print("⚠️  Firewall/proxy detectado - acesso à OpenAI bloqueado")
                print("📝 Usando FakeEmbeddings (desenvolvimento)")
                return FakeEmbeddings(size=768)

        # 3. FALLBACK FINAL: FakeEmbeddings
        print("⚠️  Nenhum provedor de embeddings disponível")
        print("📝 Usando FakeEmbeddings (desenvolvimento)")
        return FakeEmbeddings(size=768)

    def _get_vectorstore(self) -> Chroma:
        """Inicializa ou carrega o vector store ChromaDB."""
        return Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def load_pdf(self, file_path: str) -> List[Document]:
        """
        Carrega e processa um arquivo PDF.

        Args:
            file_path: Caminho para o arquivo PDF

        Returns:
            Lista de documentos (chunks)
        """
        print(f"📄 Carregando PDF: {file_path}")

        loader = PyPDFLoader(file_path)
        documents = loader.load()

        print(f"   ✅ {len(documents)} páginas carregadas")

        # Chunking
        chunks = self.text_splitter.split_documents(documents)

        print(f"   ✅ {len(chunks)} chunks criados")

        return chunks

    def load_text(self, file_path: str) -> List[Document]:
        """
        Carrega e processa um arquivo de texto.

        Args:
            file_path: Caminho para o arquivo de texto

        Returns:
            Lista de documentos (chunks)
        """
        print(f"📝 Carregando texto: {file_path}")

        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()

        print(f"   ✅ Documento carregado")

        # Chunking
        chunks = self.text_splitter.split_documents(documents)

        print(f"   ✅ {len(chunks)} chunks criados")

        return chunks

    def ingest_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Ingere um arquivo (PDF ou texto) no vector store.

        Args:
            file_path: Caminho para o arquivo
            metadata: Metadata adicional para os documentos

        Returns:
            Número de chunks ingeridos
        """
        file_extension = Path(file_path).suffix.lower()

        # Carrega documento baseado na extensão
        if file_extension == ".pdf":
            chunks = self.load_pdf(file_path)
        elif file_extension in [".txt", ".md"]:
            chunks = self.load_text(file_path)
        else:
            raise ValueError(f"Formato não suportado: {file_extension}")

        # Adiciona metadata customizada
        if metadata:
            for chunk in chunks:
                chunk.metadata.update(metadata)

        # Adiciona metadata padrão
        for chunk in chunks:
            chunk.metadata["ingested_at"] = datetime.now().isoformat()
            chunk.metadata["source_file"] = os.path.basename(file_path)

        # Adiciona ao vector store
        print(f"💾 Adicionando {len(chunks)} chunks ao ChromaDB...")
        self.vectorstore.add_documents(chunks)

        print(f"✅ Ingestão completa: {len(chunks)} chunks")

        return len(chunks)

    def ingest_text_direct(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Ingere texto diretamente (sem arquivo).

        Args:
            text: Texto a ser ingerido
            metadata: Metadata para o documento

        Returns:
            Número de chunks ingeridos
        """
        print(f"📝 Ingerindo texto direto ({len(text)} caracteres)")

        # Cria documento
        doc = Document(page_content=text, metadata=metadata or {})

        # Chunking
        chunks = self.text_splitter.split_documents([doc])

        # Adiciona metadata padrão
        for chunk in chunks:
            chunk.metadata["ingested_at"] = datetime.now().isoformat()
            chunk.metadata["source"] = "direct_text"

        # Adiciona ao vector store
        print(f"💾 Adicionando {len(chunks)} chunks ao ChromaDB...")
        self.vectorstore.add_documents(chunks)

        print(f"✅ Ingestão completa: {len(chunks)} chunks")

        return len(chunks)

    def search(
        self, query: str, k: int = 4, filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Busca documentos similares com sanitização de filtros.

        Args:
            query: Texto de busca
            k: Número de documentos a retornar
            filter: Filtros de metadata (será sanitizado)

        Returns:
            Lista de documentos mais relevantes
        """
        # SANITIZA FILTROS PARA PREVENIR SQL/NoSQL INJECTION
        if filter is not None:
            filter = sanitize_rag_filter(filter)

        results = self.vectorstore.similarity_search(query, k=k, filter=filter)

        return results

    def get_retriever(self, k: int = 4):
        """
        Retorna um retriever configurado.

        Args:
            k: Número de documentos a retornar

        Returns:
            Retriever do LangChain
        """
        return self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": k})

    def list_collections(self) -> List[str]:
        """Lista todas as coleções no ChromaDB."""
        # ChromaDB pode ter múltiplas coleções
        # Retorna a coleção atual por enquanto
        return [self.collection_name]

    def get_collection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da coleção."""
        collection = self.vectorstore._collection

        return {
            "name": self.collection_name,
            "count": collection.count(),
            "persist_directory": self.persist_directory,
        }

    def delete_collection(self):
        """Deleta a coleção atual (cuidado!)."""
        print(f"🗑️  Deletando coleção: {self.collection_name}")
        self.vectorstore.delete_collection()
        print(f"✅ Coleção deletada")


# Instância global para uso no app
_ingestion_pipeline: Optional[DocumentIngestion] = None


def get_ingestion_pipeline() -> DocumentIngestion:
    """Retorna instância singleton do pipeline de ingestão."""
    global _ingestion_pipeline

    if _ingestion_pipeline is None:
        _ingestion_pipeline = DocumentIngestion()

    return _ingestion_pipeline
