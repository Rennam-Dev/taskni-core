"""
Registry de agentes do Taskni Core.

Suporta dois tipos de agentes:
1. Agentes simples: herdam de BaseAgent, implementam apenas run()
2. Agentes LangGraph: são CompiledStateGraph completos do LangGraph

Isso permite começar com agentes simples e evoluir para LangGraph
conforme a complexidade aumenta.
"""

from typing import Any, Dict, Union

from langgraph.graph.state import CompiledStateGraph

from taskni_core.agents.base import BaseAgent
from taskni_core.core.settings import taskni_settings

# Type alias para aceitar ambos os tipos
AgentType = Union[BaseAgent, CompiledStateGraph]


class AgentRegistry:
    """
    Registro centralizado de agentes.

    Permite registrar tanto agentes simples quanto LangGraph,
    e fornece uma interface unificada para acessá-los.
    """

    def __init__(self):
        self._agents: Dict[str, AgentType] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        agent: AgentType,
        agent_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        enabled: bool = True,
    ):
        """
        Registra um agente no registry.

        Args:
            agent: Instância do agente (BaseAgent ou CompiledStateGraph)
            agent_id: ID do agente (se None, tenta pegar do agent.id)
            name: Nome do agente (se None, tenta pegar do agent.name)
            description: Descrição (se None, tenta pegar do agent.description)
            enabled: Se o agente está habilitado
        """
        # Tenta extrair metadados do agente
        if isinstance(agent, BaseAgent):
            agent_id = agent_id or agent.id
            name = name or agent.name
            description = description or agent.description
            agent_type = "simple"
        else:
            # É um CompiledStateGraph do LangGraph
            if not agent_id:
                raise ValueError("agent_id é obrigatório para agentes LangGraph")
            name = name or agent_id
            description = description or "Agente LangGraph"
            agent_type = "langgraph"

        self._agents[agent_id] = agent
        self._metadata[agent_id] = {
            "id": agent_id,
            "name": name,
            "description": description,
            "type": agent_type,
            "enabled": enabled,
        }

    def get(self, agent_id: str) -> AgentType:
        """
        Obtém um agente pelo ID.

        Args:
            agent_id: ID do agente

        Returns:
            O agente (BaseAgent ou CompiledGraph)

        Raises:
            ValueError: Se o agente não existe ou está desabilitado
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agente '{agent_id}' não encontrado")

        metadata = self._metadata[agent_id]
        if not metadata.get("enabled", True):
            raise ValueError(f"Agente '{agent_id}' está desabilitado")

        return self._agents[agent_id]

    def list_agents(self, include_disabled: bool = False) -> list[Dict[str, Any]]:
        """
        Lista todos os agentes registrados.

        Args:
            include_disabled: Se deve incluir agentes desabilitados

        Returns:
            Lista de metadados dos agentes
        """
        agents = []
        for metadata in self._metadata.values():
            if include_disabled or metadata.get("enabled", True):
                agents.append(metadata)
        return agents

    def is_simple_agent(self, agent_id: str) -> bool:
        """Verifica se é um agente simples (BaseAgent)."""
        if agent_id not in self._metadata:
            return False
        return self._metadata[agent_id]["type"] == "simple"

    def is_langgraph_agent(self, agent_id: str) -> bool:
        """Verifica se é um agente LangGraph."""
        if agent_id not in self._metadata:
            return False
        return self._metadata[agent_id]["type"] == "langgraph"


# Singleton global
agent_registry = AgentRegistry()


def get_agent(agent_id: str) -> AgentType:
    """Helper function para obter um agente."""
    return agent_registry.get(agent_id)


def list_agents(include_disabled: bool = False) -> list[Dict[str, Any]]:
    """Helper function para listar agentes."""
    return agent_registry.list_agents(include_disabled)


# ===================================================================
# Auto-registro de agentes com base nas configurações
# ===================================================================


def register_taskni_agents():
    """
    Registra os agentes do Taskni baseado nas configurações.

    Essa função é chamada na inicialização do app para registrar
    os agentes que estão habilitados no settings.
    """
    # Vamos importar os agentes aqui para evitar imports circulares
    # e para que só sejam carregados se estiverem habilitados

    # Intake Agent (Triagem)
    if taskni_settings.ENABLE_INTAKE_AGENT:
        try:
            from taskni_core.agents.intake_agent import IntakeAgent

            agent_registry.register(
                agent=IntakeAgent(),
                enabled=True,
            )
        except ImportError:
            pass  # Agente ainda não implementado

    # FAQ Agent (RAG)
    if taskni_settings.ENABLE_FAQ_AGENT:
        try:
            from taskni_core.agents.advanced.rag_agent import create_faq_rag_agent

            # Cria e registra o agente RAG
            faq_agent = create_faq_rag_agent(k_documents=4, enable_streaming=True)

            agent_registry.register(
                agent=faq_agent,
                agent_id=faq_agent.id,
                name=faq_agent.name,
                description=faq_agent.description,
                enabled=True,
            )
        except ImportError as e:
            print(f"⚠️  Não foi possível carregar FaqRagAgent: {e}")
            pass  # Agente ainda não implementado

    # Follow-up Agent
    if taskni_settings.ENABLE_FOLLOWUP_AGENT:
        try:
            from taskni_core.agents.advanced.followup_agent import create_followup_agent

            # Cria e registra o agente de Followup
            followup_agent = create_followup_agent(enable_streaming=False)

            agent_registry.register(
                agent=followup_agent,
                agent_id=followup_agent.id,
                name=followup_agent.name,
                description=followup_agent.description,
                enabled=True,
            )
        except ImportError as e:
            print(f"⚠️  Não foi possível carregar FollowupAgent: {e}")
            pass  # Agente ainda não implementado

    # Billing Agent
    if taskni_settings.ENABLE_BILLING_AGENT:
        try:
            from taskni_core.agents.billing_agent import BillingAgent

            agent_registry.register(
                agent=BillingAgent(),
                enabled=True,
            )
        except ImportError:
            pass  # Agente ainda não implementado

    # TODO: Adicionar agentes LangGraph existentes do toolkit se necessário
    # Exemplo:
    # from agents.chatbot import chatbot_graph
    # agent_registry.register(
    #     agent=chatbot_graph,
    #     agent_id="chatbot",
    #     name="Chatbot Geral",
    #     description="Chatbot geral usando LangGraph",
    #     enabled=True,
    # )
