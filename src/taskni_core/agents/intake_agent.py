"""
Agente de Triagem (Intake Agent).

Responsável pelo primeiro contato com o paciente/cliente.
Coleta informações básicas e encaminha para o fluxo adequado.

Este é um agente SIMPLES (não usa LangGraph), apenas LLM direto.
Ideal para começar rápido sem complexidade.
"""

from typing import Any, Dict

from taskni_core.agents.base import BaseAgent
from taskni_core.core.settings import taskni_settings


class IntakeAgent(BaseAgent):
    """
    Agente de triagem inicial.

    Faz o primeiro atendimento, coleta dados básicos do paciente
    (nome, telefone, motivo do contato) e encaminha para o fluxo correto.
    """

    id = "intake-agent"
    name = "Agente de Triagem"
    description = (
        "Faz a triagem inicial do paciente/cliente, coleta dados básicos "
        "(nome, telefone, motivo do contato) e encaminha para o fluxo correto."
    )

    def __init__(self):
        # LLM será inicializado lazy no primeiro uso
        self._llm = None

    @property
    def llm(self):
        """Lazy load do LLM."""
        if self._llm is None:
            from core.llm import get_model
            from core.settings import settings as core_settings
            self._llm = get_model(core_settings.DEFAULT_MODEL)
        return self._llm

    async def run(self, message: str, context: Dict[str, Any]) -> str:
        """
        Executa a triagem do paciente.

        Args:
            message: Mensagem do paciente
            context: Contexto (user_id, session_id, metadata, etc)

        Returns:
            Resposta do agente
        """
        # Extrai informações do contexto
        user_id = context.get("user_id")
        session_id = context.get("session_id")
        metadata = context.get("metadata", {})

        # Constrói o prompt de triagem
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(message, context)

        # Chama o LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Invoca o modelo
        response = await self.llm.ainvoke(messages)

        # Extrai o conteúdo da resposta
        if hasattr(response, "content"):
            reply = response.content
        else:
            reply = str(response)

        return reply

    def _build_system_prompt(self) -> str:
        """Constrói o prompt de sistema do agente."""
        business_name = taskni_settings.BUSINESS_NAME
        language = taskni_settings.DEFAULT_LANGUAGE

        return f"""Você é um agente de triagem e atendimento inicial da {business_name}.

Seu papel é:
1. Cumprimentar o paciente/cliente de forma amigável e profissional
2. Coletar informações básicas necessárias:
   - Nome completo
   - Telefone/WhatsApp (se não tiver no contexto)
   - Motivo do contato (agendamento, dúvida, resultado de exame, etc)
3. Fazer perguntas claras e objetivas, uma de cada vez
4. Ser empático e acolhedor
5. Se o paciente já forneceu alguma informação, não perguntar novamente

Estilo de comunicação:
- Amigável mas profissional
- Conciso e objetivo
- Empático com as necessidades do paciente
- Use o idioma: {language}

IMPORTANTE: Não invente informações. Se não souber algo, diga que vai verificar.
"""

    def _build_user_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """Constrói o prompt do usuário com contexto."""
        prompt_parts = []

        # Adiciona informações do contexto se disponíveis
        metadata = context.get("metadata", {})

        if metadata.get("phone"):
            prompt_parts.append(f"Telefone do paciente: {metadata['phone']}")

        if metadata.get("source"):
            prompt_parts.append(f"Canal de atendimento: {metadata['source']}")

        # Adiciona o histórico se houver (simplificado)
        # TODO: Integrar com memória real depois
        history = context.get("history", [])
        if history:
            prompt_parts.append("\nHistórico recente da conversa:")
            for msg in history[-5:]:  # Últimas 5 mensagens
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")

        # Adiciona a mensagem atual
        prompt_parts.append(f"\nMensagem atual do paciente: {message}")

        return "\n".join(prompt_parts)
