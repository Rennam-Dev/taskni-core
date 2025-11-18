# Taskni Core 🏥

Motor de agentes para clínicas e pequenos negócios usando FastAPI + LangGraph.

## 📁 Estrutura

```
taskni_core/
├── api/                    # Rotas FastAPI
│   ├── routes_health.py   # /health
│   └── routes_agents.py   # /agents (invoke, stream, list)
├── agents/                 # Agentes
│   ├── base.py            # Interface BaseAgent (agentes simples)
│   ├── registry.py        # Registro de agentes
│   └── intake_agent.py    # Agente de triagem (exemplo)
├── core/                   # Configurações
│   └── settings.py        # TaskniSettings (herda do toolkit)
├── schema/                 # Modelos Pydantic
│   ├── agent_io.py        # Request/Response dos agentes
│   └── crm.py             # Patient, Appointment, Ticket
├── memory/                 # Memória (a implementar)
└── main.py                 # App FastAPI
```

## 🎯 Abordagem Híbrida

O Taskni Core suporta **dois tipos de agentes**:

### 1. Agentes Simples (BaseAgent)
- Herdam de `BaseAgent`
- Implementam apenas `async def run(message, context) -> str`
- Ideais para começar rápido
- Exemplo: `IntakeAgent`

```python
from taskni_core.agents.base import BaseAgent

class MyAgent(BaseAgent):
    id = "my-agent"
    name = "Meu Agente"
    description = "Descrição"

    async def run(self, message: str, context: Dict) -> str:
        # Lógica simples aqui
        return "Resposta"
```

### 2. Agentes LangGraph (CompiledStateGraph)
- Grafos completos do LangGraph
- Para fluxos complexos com tools, memory, etc
- Registro via `agent_registry.register(graph, agent_id="...", ...)`

## 🚀 Como Usar

### 1. Rodar o servidor

```bash
# Configure o .env
cp .env.example .env
# Adicione suas chaves de API

# Instale dependências
uv sync --frozen

# Rode o servidor
source .venv/bin/activate
PYTHONPATH=/home/user/taskni-core/src python src/run_taskni.py
```

### 2. Testar a API

```bash
# Health check
curl http://localhost:8080/health/

# Listar agentes
curl http://localhost:8080/agents/

# Invocar agente
curl -X POST http://localhost:8080/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "intake-agent",
    "message": "Olá, gostaria de agendar uma consulta",
    "user_id": "user_123"
  }'
```

## 🔌 Integrações

O Taskni Core está preparado para integrar com:

- **Evolution API**: WhatsApp
- **Chatwoot**: CRM/Atendimento
- **n8n**: Automações
- **Supabase**: Auth + Database
- **Cal.com**: Agendamento
- **Stripe**: Pagamentos

Configure via variáveis de ambiente no `.env`.

## 📝 Próximos Passos

### Prioridade 1: Testar servidor funcionando
- [ ] Corrigir problema com inicialização do FakeModel
- [ ] Validar endpoints `/health`, `/agents`, `/agents/invoke`
- [ ] Testar IntakeAgent com modelo real (OpenAI/Anthropic)

### Prioridade 2: Agentes específicos
- [ ] Implementar `FaqRagAgent` (RAG com ChromaDB)
- [ ] Implementar `FollowupAgent` (pós-consulta)
- [ ] Implementar `BillingAgent` (cobrança)

### Prioridade 3: Integrações
- [ ] Criar cliente Evolution API
- [ ] Criar cliente Chatwoot
- [ ] Webhook para receber mensagens do WhatsApp
- [ ] Sincronizar pacientes com Chatwoot

### Prioridade 4: Memória
- [ ] Implementar memória de curto prazo (threads/sessões)
- [ ] Implementar memória de longo prazo (por paciente)
- [ ] Integrar com Postgres checkpointer

### Prioridade 5: CRM
- [ ] Criar rotas `/crm/patients`
- [ ] Criar rotas `/crm/appointments`
- [ ] Criar rotas `/crm/tickets`
- [ ] Integrar com banco de dados

## 🛠️ Desenvolvimento

### Adicionar novo agente simples

1. Crie um arquivo em `agents/`:

```python
# agents/my_agent.py
from taskni_core.agents.base import BaseAgent

class MyAgent(BaseAgent):
    id = "my-agent"
    name = "Meu Agente"
    description = "Faz X e Y"

    async def run(self, message: str, context: Dict) -> str:
        # Sua lógica aqui
        return "Resposta"
```

2. Registre em `agents/registry.py`:

```python
def register_taskni_agents():
    from taskni_core.agents.my_agent import MyAgent
    agent_registry.register(MyAgent(), enabled=True)
```

3. Adicione variável de controle em `core/settings.py`:

```python
ENABLE_MY_AGENT: bool = True
```

### Adicionar novo agente LangGraph

```python
from langgraph.graph import StateGraph
from taskni_core.agents.registry import agent_registry

# Crie seu grafo
graph = StateGraph(...)
# ... configure nodes, edges, etc
compiled = graph.compile()

# Registre
agent_registry.register(
    agent=compiled,
    agent_id="my-graph-agent",
    name="Meu Agente Avançado",
    description="Usa LangGraph completo",
    enabled=True,
)
```

## 📚 Documentação

- FastAPI docs: `http://localhost:8080/docs`
- Agent Service Toolkit: [README do toolkit](../../README.md)
- LangGraph: https://langchain-ai.github.io/langgraph/

## 🤝 Contribuindo

Este projeto está em desenvolvimento ativo. Qualquer dúvida, abra uma issue ou entre em contato.

## 📄 Licença

MIT
