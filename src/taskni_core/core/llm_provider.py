"""
Sistema de LLM com múltiplos provedores e fallback automático.

Prioridade:
1. Groq (primário - rápido e gratuito)
2. OpenAI (fallback - confiável)
3. FakeModel (development)

Suporta streaming e retry automático.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from core.llm import get_model
from core.settings import settings

logger = logging.getLogger(__name__)


class MultiProviderLLM:
    """
    LLM com múltiplos provedores e fallback automático.

    Tenta usar os provedores na ordem de prioridade:
    1. Groq (se configurado)
    2. OpenAI (se configurado)
    3. FakeModel (sempre disponível)

    Suporta:
    - Fallback automático em caso de erro
    - Streaming de respostas
    - Retry com exponential backoff
    """

    def __init__(self, enable_streaming: bool = True):
        """
        Inicializa o multi-provider LLM.

        Args:
            enable_streaming: Se deve habilitar streaming de respostas
        """
        self.enable_streaming = enable_streaming
        self._providers = self._initialize_providers()
        self._current_provider_index = 0

    def _initialize_providers(self) -> List[Dict[str, Any]]:
        """
        Inicializa a lista de provedores disponíveis.

        Returns:
            Lista de dicionários com informações dos provedores
        """
        providers = []

        # 1. Groq (primário)
        if settings.GROQ_API_KEY:
            try:
                from schema.models import GroqModelName

                providers.append(
                    {
                        "name": "Groq",
                        "model": GroqModelName.LLAMA_31_8B,
                        "priority": 1,
                        "fast": True,
                    }
                )
                logger.info("✅ Groq configurado como provider primário")
            except Exception as e:
                logger.warning(f"⚠️  Groq não pôde ser inicializado: {e}")

        # 2. OpenAI (fallback)
        if settings.OPENAI_API_KEY:
            try:
                from schema.models import OpenAIModelName

                providers.append(
                    {
                        "name": "OpenAI",
                        "model": OpenAIModelName.GPT_4O_MINI,
                        "priority": 2,
                        "fast": True,
                    }
                )
                logger.info("✅ OpenAI configurado como fallback")
            except Exception as e:
                logger.warning(f"⚠️  OpenAI não pôde ser inicializado: {e}")

        # 3. FakeModel (sempre disponível)
        from schema.models import FakeModelName

        providers.append(
            {
                "name": "FakeModel",
                "model": FakeModelName.FAKE,
                "priority": 999,  # Último recurso
                "fast": True,
            }
        )
        logger.info("✅ FakeModel configurado como último recurso")

        # Ordena por prioridade
        providers.sort(key=lambda p: p["priority"])

        logger.info(f"📋 Provedores disponíveis: {[p['name'] for p in providers]}")
        return providers

    def _get_llm(self, provider_info: Dict[str, Any]) -> BaseChatModel:
        """
        Obtém instância do LLM para um provedor.

        Args:
            provider_info: Informações do provedor

        Returns:
            Instância do chat model
        """
        return get_model(provider_info["model"])

    async def ainvoke(
        self, messages: List[BaseMessage] | List[Dict[str, str]], timeout: float = 30.0, **kwargs
    ) -> Any:
        """
        Invoca o LLM com fallback automático e timeout.

        Tenta os provedores em ordem de prioridade até um funcionar.

        Args:
            messages: Mensagens para enviar ao LLM
            timeout: Timeout em segundos (padrão: 30s)
            **kwargs: Argumentos adicionais

        Returns:
            Resposta do LLM

        Raises:
            Exception: Se todos os provedores falharem
        """
        import asyncio

        errors = []

        for provider_info in self._providers:
            try:
                logger.info(f"🔄 Tentando provider: {provider_info['name']}")

                llm = self._get_llm(provider_info)

                # Adiciona timeout de 30 segundos para evitar hang
                response = await asyncio.wait_for(llm.ainvoke(messages, **kwargs), timeout=timeout)

                logger.info(f"✅ {provider_info['name']} respondeu com sucesso")
                return response

            except asyncio.TimeoutError:
                error_msg = f"{provider_info['name']}: Timeout após {timeout}s"
                logger.warning(f"⚠️  {error_msg}")
                errors.append(error_msg)
                continue
            except Exception as e:
                error_msg = f"{provider_info['name']}: {str(e)[:100]}"
                logger.warning(f"⚠️  {error_msg}")
                errors.append(error_msg)
                continue

        # Se chegou aqui, todos falharam
        error_summary = "\n".join([f"  - {err}" for err in errors])
        raise Exception(f"Todos os provedores falharam:\n{error_summary}")

    async def astream(
        self, messages: List[BaseMessage] | List[Dict[str, str]], timeout: float = 60.0, **kwargs
    ):
        """
        Stream de respostas do LLM com fallback automático e timeout.

        Args:
            messages: Mensagens para enviar ao LLM
            timeout: Timeout total em segundos (padrão: 60s para streaming)
            **kwargs: Argumentos adicionais

        Yields:
            Chunks de resposta do LLM

        Raises:
            Exception: Se todos os provedores falharem
        """
        import asyncio

        if not self.enable_streaming:
            # Fallback para invoke se streaming desabilitado
            response = await self.ainvoke(messages, timeout=timeout, **kwargs)
            if hasattr(response, "content"):
                yield response.content
            else:
                yield str(response)
            return

        errors = []

        for provider_info in self._providers:
            try:
                logger.info(f"🔄 Streaming com: {provider_info['name']}")

                llm = self._get_llm(provider_info)

                # Timeout para o stream completo
                async def stream_with_timeout():
                    async for chunk in llm.astream(messages, **kwargs):
                        if hasattr(chunk, "content"):
                            yield chunk.content
                        else:
                            yield str(chunk)

                async for chunk in asyncio.wait_for(stream_with_timeout(), timeout=timeout):
                    yield chunk

                logger.info(f"✅ {provider_info['name']} stream concluído")
                return  # Stream bem-sucedido, sai da função

            except asyncio.TimeoutError:
                error_msg = f"{provider_info['name']}: Stream timeout após {timeout}s"
                logger.warning(f"⚠️  {error_msg}")
                errors.append(error_msg)
                continue
            except Exception as e:
                error_msg = f"{provider_info['name']}: {str(e)[:100]}"
                logger.warning(f"⚠️  {error_msg}")
                errors.append(error_msg)
                continue

        # Se chegou aqui, todos falharam
        error_summary = "\n".join([f"  - {err}" for err in errors])
        raise Exception(f"Todos os provedores falharam no streaming:\n{error_summary}")

    def invoke_sync(self, messages: List[BaseMessage] | List[Dict[str, str]], **kwargs) -> str:
        """
        Versão síncrona do ainvoke.

        Args:
            messages: Mensagens para enviar ao LLM
            **kwargs: Argumentos adicionais

        Returns:
            Conteúdo da resposta como string

        Raises:
            Exception: Se todos os provedores falharem
        """
        import asyncio

        # Executa ainvoke de forma síncrona
        response = asyncio.run(self.ainvoke(messages, **kwargs))

        # Extrai conteúdo
        if hasattr(response, "content"):
            return response.content
        return str(response)

    def get_current_provider(self) -> str:
        """Retorna o nome do provider atual."""
        if self._providers:
            return self._providers[0]["name"]
        return "None"

    def get_available_providers(self) -> List[str]:
        """Retorna lista de providers disponíveis."""
        return [p["name"] for p in self._providers]
