"""
Followup Agent - Agente de acompanhamento e reativação.

Usa LangGraph para implementar um workflow de:
1. detect_intent: Detecta a intenção baseado no contexto
2. generate_message: Gera mensagem personalizada usando LLM
3. schedule_send: Prepara para envio (simulado por enquanto)

Este é um agente AVANÇADO (usa LangGraph completo).
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, TypedDict

from langgraph.graph import END, StateGraph

from taskni_core.core.llm_provider import MultiProviderLLM
from taskni_core.core.settings import taskni_settings
from taskni_core.utils.security import sanitize_prompt_input

if TYPE_CHECKING:
    from taskni_core.schema.agent_inputs import FollowupInput

# ============================================================================
# State Definition
# ============================================================================


class FollowupState(TypedDict):
    """
    Estado do agente de followup.

    Campos:
    - patient_name: Nome do paciente
    - days_inactive: Dias desde último contato
    - last_message: Última mensagem do paciente
    - context: Contexto adicional (clinic_type, service, tone)
    - intent: Intenção detectada
    - message: Mensagem gerada
    - ready_for_delivery: Se está pronto para envio
    - send_at: Quando enviar (now, scheduled)
    """

    patient_name: str
    days_inactive: int
    last_message: str
    context: dict
    intent: str
    message: str
    ready_for_delivery: bool
    send_at: str


# ============================================================================
# Agent Nodes
# ============================================================================


class FollowupAgent:
    """
    Agente de acompanhamento e reativação usando LangGraph.

    Workflow:
    1. detect_intent: Analisa contexto e detecta intenção
    2. generate_message: Gera mensagem personalizada
    3. schedule_send: Prepara para envio
    """

    # Metadata do agente (para o registry)
    id = "followup-agent"
    name = "Agente de Acompanhamento"
    description = (
        "Reativa pacientes inativos, faz acompanhamento pós-consulta e "
        "envia lembretes personalizados baseado no contexto do paciente."
    )

    def __init__(self, enable_streaming: bool = False):
        """
        Inicializa o agente de followup.

        Args:
            enable_streaming: Habilitar streaming nas respostas
        """
        self.enable_streaming = enable_streaming

        # Inicializa LLM multi-provider
        self.llm = MultiProviderLLM(enable_streaming=enable_streaming)

        # Constrói o grafo LangGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Constrói o grafo LangGraph do agente."""
        # Cria workflow
        workflow = StateGraph(FollowupState)

        # Adiciona nodes
        workflow.add_node("detect_intent", self._detect_intent)
        workflow.add_node("generate_message", self._generate_message)
        workflow.add_node("schedule_send", self._schedule_send)

        # Define edges
        workflow.set_entry_point("detect_intent")
        workflow.add_edge("detect_intent", "generate_message")
        workflow.add_edge("generate_message", "schedule_send")
        workflow.add_edge("schedule_send", END)

        # Compila o grafo
        return workflow.compile()

    def _detect_intent(self, state: FollowupState) -> FollowupState:
        """
        Node 1: Detecta a intenção baseado no contexto.

        Intenções possíveis:
        - reativacao: Paciente inativo há muito tempo
        - pos_consulta: Acompanhamento após consulta
        - abandono: Paciente iniciou mas não completou agendamento
        - lead_frio: Lead que nunca agendou
        - checagem_retorno: Verificar se precisa retornar
        - agendar_consulta: Lembrete para agendar

        Args:
            state: Estado atual

        Returns:
            Estado atualizado com intent detectado
        """
        days_inactive = state["days_inactive"]
        last_message = state.get("last_message", "").lower()
        context = state.get("context", {})

        print("🔍 Detectando intenção...")
        print(f"   - Dias inativo: {days_inactive}")
        print(f"   - Última mensagem: '{last_message[:50]}...'")

        # Lógica de detecção de intenção
        intent = "reativacao"  # Default

        # Pós-consulta (1-3 dias após consulta)
        if 1 <= days_inactive <= 3 and context.get("had_appointment"):
            intent = "pos_consulta"

        # Abandono (iniciou mas não completou)
        elif 3 <= days_inactive <= 7 and any(
            keyword in last_message
            for keyword in ["agendar", "consulta", "horário", "disponibilidade"]
        ):
            intent = "abandono"

        # Lead frio (nunca agendou, muito tempo)
        elif days_inactive > 30 and not context.get("had_appointment"):
            intent = "lead_frio"

        # Checagem de retorno (após procedimento)
        elif 7 <= days_inactive <= 15 and context.get("needs_followup"):
            intent = "checagem_retorno"

        # Lembrete para agendar consulta de rotina
        elif days_inactive > 90 and context.get("is_patient"):
            intent = "agendar_consulta"

        # Reativação geral (inativo mas já foi paciente)
        elif days_inactive > 30:
            intent = "reativacao"

        print(f"   ✅ Intenção detectada: {intent}")

        return {
            **state,
            "intent": intent,
        }

    def _generate_message(self, state: FollowupState) -> FollowupState:
        """
        Node 2: Gera mensagem personalizada usando LLM.

        Args:
            state: Estado atual

        Returns:
            Estado atualizado com mensagem gerada
        """
        patient_name = state["patient_name"]
        intent = state["intent"]
        days_inactive = state["days_inactive"]
        context = state.get("context", {})

        print("🤖 Gerando mensagem de followup...")
        print(f"   - Intenção: {intent}")
        print(f"   - Paciente: {patient_name}")

        # Constrói prompt baseado na intenção
        system_prompt = self._get_system_prompt(intent)
        user_prompt = self._get_user_prompt(
            patient_name=patient_name,
            intent=intent,
            days_inactive=days_inactive,
            context=context,
        )

        # Mensagens para o LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Gera mensagem
        message = self.llm.invoke_sync(messages)

        print(f"   ✅ Mensagem gerada ({len(message)} caracteres)")

        return {
            **state,
            "message": message.strip(),
        }

    def _adjust_to_business_hours(self, dt: datetime) -> datetime:
        """
        Ajusta data/hora para horário comercial (8h-20h).

        Args:
            dt: Data/hora desejada

        Returns:
            Data/hora ajustada para horário comercial
        """
        # Se for fim de semana, move para segunda-feira
        if dt.weekday() == 5:  # Sábado
            dt = dt + timedelta(days=2)
        elif dt.weekday() == 6:  # Domingo
            dt = dt + timedelta(days=1)

        # Ajusta horário
        if dt.hour < 8:
            # Antes das 8h → move para 8h
            dt = dt.replace(hour=8, minute=0, second=0, microsecond=0)
        elif dt.hour >= 20:
            # Depois das 20h → move para próximo dia às 8h
            dt = (dt + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)

        return dt

    def _schedule_send(self, state: FollowupState) -> FollowupState:
        """
        Node 3: Prepara para envio com horários comerciais inteligentes.

        Regras de agendamento:
        - pos_consulta: Próxima manhã às 10h
        - abandono: Daqui 2 horas
        - lead_frio: Amanhã às 16h
        - checagem_retorno: Amanhã às 10h
        - agendar_consulta: Hoje às 18h
        - reativacao: Hoje às 18h

        Todas ajustadas para horário comercial (8h-20h, seg-sex).

        Args:
            state: Estado atual

        Returns:
            Estado atualizado com informações de agendamento
        """
        intent = state["intent"]
        now = datetime.now()

        print("📅 Preparando agendamento de envio...")

        # Define horário base por intenção
        if intent == "pos_consulta":
            # Próxima manhã às 10h
            send_at = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

        elif intent == "abandono":
            # Daqui 2 horas
            send_at = now + timedelta(hours=2)

        elif intent == "lead_frio":
            # Amanhã às 16h
            send_at = (now + timedelta(days=1)).replace(hour=16, minute=0, second=0, microsecond=0)

        elif intent == "checagem_retorno":
            # Amanhã às 10h
            send_at = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

        elif intent == "agendar_consulta":
            # Hoje às 18h
            send_at = now.replace(hour=18, minute=0, second=0, microsecond=0)
            # Se já passou das 18h, move para amanhã
            if now.hour >= 18:
                send_at = send_at + timedelta(days=1)

        else:  # reativacao e outros
            # Hoje às 18h
            send_at = now.replace(hour=18, minute=0, second=0, microsecond=0)
            # Se já passou das 18h, move para amanhã
            if now.hour >= 18:
                send_at = send_at + timedelta(days=1)

        # Ajusta para horário comercial
        send_at = self._adjust_to_business_hours(send_at)

        # Verifica se é envio imediato ou agendado
        is_scheduled = send_at > now
        send_at_str = send_at.isoformat() if is_scheduled else "now"

        print(f"   ✅ Envio agendado: {send_at_str}")
        if is_scheduled:
            print(f"      Agendado para: {send_at.strftime('%d/%m/%Y %H:%M')}")

        return {
            **state,
            "ready_for_delivery": True,
            "send_at": send_at_str,
        }

    def _get_system_prompt(self, intent: str) -> str:
        """
        Retorna o prompt de sistema baseado na intenção.

        Args:
            intent: Intenção detectada

        Returns:
            Prompt de sistema
        """
        business_name = taskni_settings.BUSINESS_NAME
        language = taskni_settings.DEFAULT_LANGUAGE

        base_prompt = f"""Você é um assistente da {business_name} especializado em mensagens de acompanhamento.

Sua missão é criar mensagens CURTAS, NATURAIS e AMIGÁVEIS para reconectar com pacientes.

REGRAS IMPORTANTES:
1. Mensagem deve ter NO MÁXIMO 2-3 linhas (como um WhatsApp real)
2. Seja amigável mas profissional
3. Evite ser muito formal ou "marketeiro"
4. Use emojis com moderação (máximo 1-2)
5. Sempre termine com uma call-to-action suave
6. Idioma: {language}

NUNCA:
- Seja insistente ou agressivo
- Faça promessas que não pode cumprir
- Use linguagem muito comercial
"""

        # Instruções específicas por intenção
        intent_instructions = {
            "reativacao": """
CONTEXTO: Paciente está inativo há algum tempo.
OBJETIVO: Reativar de forma suave e amigável.
TOM: Saudoso mas não insistente.
EXEMPLO: "Oi [nome]! Sentimos sua falta por aqui 😊 Que tal agendar um check-up? Estamos à disposição!"
""",
            "pos_consulta": """
CONTEXTO: Acompanhamento após consulta recente.
OBJETIVO: Verificar como está e oferecer suporte.
TOM: Cuidadoso e atencioso.
EXEMPLO: "Olá [nome]! Como você está se sentindo após a consulta? Qualquer dúvida, estamos aqui! 🩺"
""",
            "abandono": """
CONTEXTO: Paciente iniciou agendamento mas não completou.
OBJETIVO: Ajudar a concluir o agendamento.
TOM: Prestativo e facilitador.
EXEMPLO: "Oi [nome]! Vi que você teve interesse em agendar. Posso ajudar a encontrar um horário? 😊"
""",
            "lead_frio": """
CONTEXTO: Lead antigo que nunca agendou.
OBJETIVO: Reativar com oferta de valor.
TOM: Acolhedor e informativo.
EXEMPLO: "Oi [nome]! Ainda podemos ajudar com seu atendimento. Temos horários disponíveis esta semana!"
""",
            "checagem_retorno": """
CONTEXTO: Paciente precisa de retorno após procedimento.
OBJETIVO: Lembrar da importância do retorno.
TOM: Profissional e cuidadoso.
EXEMPLO: "Olá [nome]! Está na hora de agendar seu retorno. É importante para acompanharmos sua evolução! 🩺"
""",
            "agendar_consulta": """
CONTEXTO: Consulta de rotina está atrasada.
OBJETIVO: Incentivar check-up preventivo.
TOM: Amigável e preventivo.
EXEMPLO: "Oi [nome]! Que tal um check-up? Cuidar da saúde preventivamente é sempre melhor! 😊"
""",
        }

        specific_instruction = intent_instructions.get(
            intent,
            intent_instructions["reativacao"],  # Default
        )

        return base_prompt + "\n" + specific_instruction

    def _get_user_prompt(
        self, patient_name: str, intent: str, days_inactive: int, context: dict
    ) -> str:
        """
        Constrói o prompt do usuário com sanitização de inputs.

        Args:
            patient_name: Nome do paciente
            intent: Intenção
            days_inactive: Dias inativo
            context: Contexto adicional

        Returns:
            Prompt formatado e sanitizado
        """
        # SANITIZA TODOS OS INPUTS PARA PREVENIR PROMPT INJECTION
        patient_name = sanitize_prompt_input(patient_name, max_length=200)
        intent = sanitize_prompt_input(intent, max_length=50)
        clinic_type = sanitize_prompt_input(context.get("clinic_type", "clínica"), max_length=100)
        service = sanitize_prompt_input(context.get("service", "atendimento"), max_length=100)
        tone = sanitize_prompt_input(context.get("tone", "amigável"), max_length=50)

        prompt = f"""Crie uma mensagem de followup para:

Nome do paciente: {patient_name}
Dias sem contato: {days_inactive}
Tipo de estabelecimento: {clinic_type}
Serviço principal: {service}
Tom desejado: {tone}
Intenção: {intent}

Lembre-se: mensagem CURTA (2-3 linhas máximo), natural como WhatsApp, e com call-to-action suave.

Mensagem:"""

        return prompt

    async def run(
        self,
        patient_name: str = None,
        days_inactive: int = None,
        last_message: str = "",
        context: dict = None,
        input_data: "FollowupInput" = None,
    ) -> dict:
        """
        Executa o agente de followup.

        Args:
            patient_name: Nome do paciente (ou use input_data)
            days_inactive: Dias desde último contato (ou use input_data)
            last_message: Última mensagem do paciente
            context: Contexto adicional
            input_data: FollowupInput validado (alternativa aos args individuais)

        Returns:
            Dict com intent, message, ready_for_delivery, send_at
        """
        # Suporta tanto input direto quanto FollowupInput
        if input_data is not None:
            from taskni_core.schema.agent_inputs import FollowupInput

            # Valida se é instância de FollowupInput
            if not isinstance(input_data, FollowupInput):
                input_data = FollowupInput(**input_data)

            patient_name = input_data.patient_name
            days_inactive = input_data.days_inactive
            last_message = input_data.last_message
            context = input_data.context
        else:
            # Validação básica para compatibilidade com código antigo
            if patient_name is None or days_inactive is None:
                raise ValueError("patient_name and days_inactive are required")

        print(f"\n{'=' * 80}")
        print("🤖 FollowupAgent: Processando followup")
        print(f"{'=' * 80}")

        # Estado inicial
        initial_state = {
            "patient_name": patient_name,
            "days_inactive": days_inactive,
            "last_message": last_message or "",
            "context": context or {},
            "intent": "",
            "message": "",
            "ready_for_delivery": False,
            "send_at": "",
        }

        # Executa o grafo
        final_state = await self.graph.ainvoke(initial_state)

        print(f"{'=' * 80}\n")

        # Retorna resultado
        return {
            "intent": final_state["intent"],
            "message": final_state["message"],
            "ready_for_delivery": final_state["ready_for_delivery"],
            "send_at": final_state["send_at"],
        }

    def invoke_sync(
        self,
        patient_name: str,
        days_inactive: int,
        last_message: str = "",
        context: dict = None,
    ) -> dict:
        """Versão síncrona do run() para compatibilidade."""
        import asyncio

        return asyncio.run(self.run(patient_name, days_inactive, last_message, context))


# ============================================================================
# Factory Function
# ============================================================================


def create_followup_agent(enable_streaming: bool = False) -> FollowupAgent:
    """
    Factory para criar instância do FollowupAgent.

    Args:
        enable_streaming: Habilitar streaming

    Returns:
        Instância do FollowupAgent (já compilado)
    """
    return FollowupAgent(enable_streaming=enable_streaming)
