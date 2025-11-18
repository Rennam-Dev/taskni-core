"""
Rotas para o sistema RAG (Retrieval-Augmented Generation).

Endpoints:
- POST /rag/upload - Upload de documentos (PDF, texto)
- POST /rag/ingest/text - Ingestão de texto direto
- GET /rag/documents - Informações sobre documentos ingeridos
- DELETE /rag/documents - Deleta coleção (cuidado!)
"""

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from taskni_core.rag.ingest import get_ingestion_pipeline


# ============================================================================
# Router
# ============================================================================

router = APIRouter(tags=["RAG"])


# ============================================================================
# Schemas
# ============================================================================

class IngestTextRequest(BaseModel):
    """Request para ingestão de texto direto."""
    text: str
    metadata: Optional[dict] = None


class IngestTextResponse(BaseModel):
    """Response da ingestão de texto."""
    message: str
    chunks_count: int
    metadata: dict


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
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = None,
):
    """
    Upload e ingestão de documento (PDF ou texto).

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
            detail=f"Formato não suportado: {file_extension}. Use .pdf, .txt ou .md"
        )

    # Lê conteúdo do arquivo
    content = await file.read()
    file_size = len(content)

    # Salva temporariamente
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=file_extension,
        mode="wb"
    ) as tmp_file:
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
                raise HTTPException(
                    status_code=400,
                    detail="Metadata inválida. Use formato JSON."
                )

        # Ingere arquivo
        chunks_count = pipeline.ingest_file(
            file_path=tmp_path,
            metadata=metadata_dict
        )

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
async def ingest_text(payload: IngestTextRequest):
    """
    Ingere texto direto (sem arquivo).

    Args:
        payload: Texto e metadata opcional

    Returns:
        Informações sobre a ingestão
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Texto não pode estar vazio"
        )

    # Pipeline de ingestão
    pipeline = get_ingestion_pipeline()

    # Ingere texto
    chunks_count = pipeline.ingest_text_direct(
        text=payload.text,
        metadata=payload.metadata or {}
    )

    return IngestTextResponse(
        message="Texto ingerido com sucesso",
        chunks_count=chunks_count,
        metadata=payload.metadata or {},
    )


@router.get("/documents", response_model=DocumentsStatsResponse)
async def get_documents_stats():
    """
    Retorna estatísticas sobre os documentos ingeridos.

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
async def delete_all_documents():
    """
    Deleta todos os documentos da coleção.

    ⚠️ CUIDADO: Esta operação é irreversível!

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
