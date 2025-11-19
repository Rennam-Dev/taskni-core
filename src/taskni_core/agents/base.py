"""
Base agent interface para agentes simples do Taskni Core.

Agentes que herdam de BaseAgent são agentes leves que não precisam
da complexidade completa do LangGraph. Eles implementam apenas o método run().

Para agentes mais complexos (com state, tools, memory avançada),
use diretamente LangGraph e registre no registry.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """
    Interface base para agentes simples.

    Attributes:
        id: Identificador único do agente (ex: "intake-agent")
        name: Nome amigável do agente
        description: Descrição do que o agente faz
    """

    id: str
    name: str
    description: str

    @abstractmethod
    async def run(self, message: str, context: Dict[str, Any]) -> str:
        """
        Executa o agente com uma mensagem e contexto.

        Args:
            message: Mensagem do usuário
            context: Contexto adicional (user_id, session_id, metadata, etc)

        Returns:
            Resposta do agente como string
        """
        ...

    def get_info(self) -> Dict[str, str]:
        """Retorna informações sobre o agente."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": "simple",  # vs "langgraph"
        }
