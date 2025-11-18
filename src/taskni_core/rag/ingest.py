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
from langchain_community.embeddings import FakeEmbeddings

from core.settings import settings


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

    def _get_embeddings(self):
        """
        Retorna embeddings configurados.

        Prioridade:
        1. OpenAI (se disponível e ambiente permite)
        2. FakeEmbeddings (desenvolvimento ou quando há restrições de rede)
        """
        # Por enquanto, sempre usa FakeEmbeddings para evitar problemas de rede
        # TODO: Implementar detecção automática de ambiente ou usar variável de ambiente
        print("📝 Usando FakeEmbeddings (desenvolvimento)")
        return FakeEmbeddings(size=1536)

        # Código comentado para quando o ambiente permitir acesso externo:
        # if settings.OPENAI_API_KEY:
        #     try:
        #         return OpenAIEmbeddings(
        #             api_key=settings.OPENAI_API_KEY.get_secret_value(),
        #             model="text-embedding-3-small",  # Mais barato
        #         )
        #     except Exception as e:
        #         print(f"⚠️  OpenAI Embeddings falhou: {e}")
        #
        # # Fallback para FakeEmbeddings
        # print("⚠️  Usando FakeEmbeddings (desenvolvimento)")
        # return FakeEmbeddings(size=1536)

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

    def ingest_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
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

    def ingest_text_direct(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
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
        doc = Document(
            page_content=text,
            metadata=metadata or {}
        )

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
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Busca documentos similares.

        Args:
            query: Texto de busca
            k: Número de documentos a retornar
            filter: Filtros de metadata

        Returns:
            Lista de documentos mais relevantes
        """
        results = self.vectorstore.similarity_search(
            query,
            k=k,
            filter=filter
        )

        return results

    def get_retriever(self, k: int = 4):
        """
        Retorna um retriever configurado.

        Args:
            k: Número de documentos a retornar

        Returns:
            Retriever do LangChain
        """
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )

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
