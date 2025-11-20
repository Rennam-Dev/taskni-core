"""
Rotas para o sistema RAG (Retrieval-Augmented Generation).

Endpoints:
- POST /rag/upload - Upload de documentos (PDF, texto)
- POST /rag/ingest/text - Ingestão de texto direto
- GET /rag/documents - Informações sobre documentos ingeridos
- DELETE /rag/documents - Deleta coleção (cuidado!)
"""

import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from taskni_core.rag.ingest import get_ingestion_pipeline
from taskni_core.utils.error_handler import safe_str_exception
from taskni_core.schema.metadata_schemas import DocumentMetadata

logger = logging.getLogger(__name__)

# ============================================================================
# Router
# ============================================================================

router = APIRouter(tags=["RAG"])

# Inicializa limiter (será injetado pelo app)
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Schemas
# ============================================================================


class IngestTextRequest(BaseModel):
    """Request para ingestão de texto direto."""

    text: str
    metadata: DocumentMetadata = Field(
        default_factory=DocumentMetadata, description="Metadados validados do documento"
    )


class IngestTextResponse(BaseModel):
    """Response da ingestão de texto."""

    message: str
    chunks_count: int
    metadata: DocumentMetadata


class UploadResponse(BaseModel):
    """Response do upload de documento."""

    message: str
    filename: str
    chunks_count: int
    file_size: int


class DocumentsStatsResponse(BaseModel):
    """Response com estatísticas dos documentos."""

    collection_name: str
    documents_count: int
    persist_directory: str


class DeleteResponse(BaseModel):
    """Response da deleção."""

    message: str
    collection_name: str


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/upload", response_model=UploadResponse)
@limiter.limit("5/minute")  # 5 uploads por minuto - pode encher disco
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    metadata: Optional[str] = None,
):
    """
    Upload e ingestão de documento (PDF ou texto).

    Rate limit: 5 requests/minuto por IP

    Args:
        file: Arquivo a ser ingerido (PDF, TXT, MD)
        metadata: Metadata adicional (JSON string opcional)

    Returns:
        Informações sobre a ingestão
    """
    # Valida extensão
    filename = file.filename or "unknown"
    file_extension = os.path.splitext(filename)[1].lower()

    if file_extension not in [".pdf", ".txt", ".md"]:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado: {file_extension}. Use .pdf, .txt ou .md",
        )

    # Lê conteúdo do arquivo
    content = await file.read()
    file_size = len(content)

    # Salva temporariamente
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension, mode="wb") as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Pipeline de ingestão
        pipeline = get_ingestion_pipeline()

        # Parse metadata se fornecido
        import json

        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Metadata inválida. Use formato JSON.")

        # Ingere arquivo
        chunks_count = pipeline.ingest_file(file_path=tmp_path, metadata=metadata_dict)

        return UploadResponse(
            message=f"Documento '{filename}' ingerido com sucesso",
            filename=filename,
            chunks_count=chunks_count,
            file_size=file_size,
        )

    finally:
        # Remove arquivo temporário
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/ingest/text", response_model=IngestTextResponse)
@limiter.limit("10/minute")  # 10 ingestões de texto por minuto
async def ingest_text(request: Request, payload: IngestTextRequest):
    """
    Ingere texto direto (sem arquivo).

    Rate limit: 10 requests/minuto por IP

    Args:
        payload: Texto e metadata opcional

    Returns:
        Informações sobre a ingestão
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Texto não pode estar vazio")

    # Pipeline de ingestão
    pipeline = get_ingestion_pipeline()

    # Converte metadata tipado para dicionário
    metadata_dict = payload.metadata.model_dump(exclude_none=True)

    # Ingere texto
    chunks_count = pipeline.ingest_text_direct(text=payload.text, metadata=metadata_dict)

    return IngestTextResponse(
        message="Texto ingerido com sucesso",
        chunks_count=chunks_count,
        metadata=payload.metadata,
    )


@router.get("/documents", response_model=DocumentsStatsResponse)
@limiter.limit("30/minute")  # 30 consultas por minuto - menos crítico
async def get_documents_stats(request: Request):
    """
    Retorna estatísticas sobre os documentos ingeridos.

    Rate limit: 30 requests/minuto por IP

    Returns:
        Informações sobre a coleção ChromaDB
    """
    pipeline = get_ingestion_pipeline()
    stats = pipeline.get_collection_stats()

    return DocumentsStatsResponse(
        collection_name=stats["name"],
        documents_count=stats["count"],
        persist_directory=stats["persist_directory"],
    )


@router.delete("/documents", response_model=DeleteResponse)
@limiter.limit("1/hour")  # 1 deleção por hora - SUPER CRÍTICO!
async def delete_all_documents(request: Request):
    """
    Deleta todos os documentos da coleção.

    ⚠️ CUIDADO: Esta operação é irreversível!
    Rate limit: 1 request/hora por IP (operação destrutiva)

    Returns:
        Confirmação da deleção
    """
    pipeline = get_ingestion_pipeline()
    collection_name = pipeline.collection_name

    # Deleta coleção
    pipeline.delete_collection()

    return DeleteResponse(
        message=f"Coleção '{collection_name}' deletada com sucesso",
        collection_name=collection_name,
    )
