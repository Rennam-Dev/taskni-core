# 🏥 Taskni Core

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Sistema de automação inteligente para clínicas, construído com FastAPI, LangGraph e múltiplos provedores de LLM.

## 🎯 Visão Geral

O **Taskni Core** é uma plataforma robusta de agentes de IA especializados para automação de processos em clínicas. O sistema implementa:

- **3 Agentes Especializados** (Intake, FAQ/RAG, Follow-up)
- **Multi-Provider LLM** com fallback automático (Groq → OpenAI → FakeModel)
- **Sistema RAG** completo com ChromaDB e detecção de firewall
- **Workflows LangGraph** com state management
- **API REST** completa com streaming de respostas
- **Validação Pydantic** em todos os inputs
- **Cache inteligente** para redução de custos
- **Agendamento automático** respeitando horários comerciais

---

## 🚀 Melhorias Recentes (v2.0)

### 1. ⏰ Agendamento Inteligente
- **Horários comerciais**: 8h-20h, segunda a sexta
- **Evita finais de semana**: Mensagens movidas automaticamente para segunda-feira
- **Regras por intenção**:
  - `pos_consulta` → Manhã seguinte às 10h
  - `abandono` → 2 horas após detectar
  - `lead_frio` → Amanhã às 16h
  - `checagem_retorno` → Amanhã às 10h
  - `reativacao` → Hoje às 18h
  - `agendar_consulta` → Hoje às 18h

### 2. ✅ Validação Pydantic
- **Inputs validados** para todos os agentes
- **Mensagens de erro claras** em português
- **Type safety** com Pydantic v2
- **Validações customizadas**:
  - `days_inactive >= 0`
  - `patient_name` não pode ser vazio
  - `k_documents` entre 1-10

### 3. 💾 Cache para RAG
- **50 respostas em cache** (FIFO)
- **Normalização de perguntas** (case-insensitive)
- **MD5 hash** para chaves de cache
- **Redução de custos** com OpenAI
- **Resposta instantânea** em cache hits

### 4. 🔒 Detecção de Firewall
- **Detecção automática** de ambiente bloqueado
- **Fallback inteligente** para FakeEmbeddings
- **Timeout rápido** (2 segundos)
- **Sistema continua operacional** mesmo com firewall

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Service                        │
│                    (src/service/service.py)                 │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │  Agent Registry  │
    │  (registry.py)   │
    └────────┬────────┘
             │
    ┌────────┴─────────────────────────────────────┐
    │                                              │
┌───▼────────┐  ┌──────────────┐  ┌──────────────┐
│  Intake    │  │  FAQ RAG     │  │  Follow-up   │
│  Agent     │  │  Agent       │  │  Agent       │
│ (simples)  │  │ (LangGraph)  │  │ (LangGraph)  │
└────────────┘  └───────┬──────┘  └───────┬──────┘
                        │                 │
                ┌───────▼─────┐   ┌───────▼─────────┐
                │ ChromaDB    │   │ 6 Tipos de      │
                │ + Embeddings│   │ Intenções       │
                └─────────────┘   └─────────────────┘
                        │
                ┌───────▼──────────────────────┐
                │   Multi-Provider LLM         │
                │   Groq → OpenAI → FakeModel  │
                └──────────────────────────────┘
```

---

## 🤖 Agentes Disponíveis

### 1. IntakeAgent (Triagem)
**Tipo**: Agente Simples (BaseAgent)
**Endpoint**: `/intake/invoke`

Primeiro contato com pacientes, realiza triagem inicial e coleta informações básicas.

**Input**:
```json
{
  "message": "Gostaria de agendar uma consulta",
  "user_id": "patient_001",
  "metadata": {"phone": "+5511987654321"}
}
```

**Output**:
```json
{
  "response": "Olá! Vou ajudá-lo a agendar. Qual especialidade você precisa?",
  "intent": "agendamento",
  "next_step": "coletar_especialidade"
}
```

---

### 2. FaqRagAgent (Perguntas Frequentes)
**Tipo**: Agente LangGraph (CompiledStateGraph)
**Endpoint**: `/faq/invoke`

Responde perguntas usando RAG (Retrieval-Augmented Generation) com ChromaDB.

**Workflow**:
```
retrieve_docs → generate_answer → END
```

**Input**:
```json
{
  "question": "Qual o horário de funcionamento?",
  "k_documents": 4
}
```

**Output**:
```json
{
  "answer": "Funcionamos de segunda a sexta, das 8h às 18h.",
  "sources": ["FAQ-001", "FAQ-010"],
  "retrieved_docs": [...],
  "cached": false
}
```

**Features**:
- ✅ Cache de 50 respostas (FIFO)
- ✅ Detecção automática de firewall
- ✅ Fallback para FakeEmbeddings
- ✅ Streaming de resposta

---

### 3. FollowupAgent (Reativação)
**Tipo**: Agente LangGraph (CompiledStateGraph)
**Endpoint**: `/followup/invoke`

Gera mensagens de reativação personalizadas baseadas em 6 tipos de intenções.

**Workflow**:
```
detect_intent → generate_message → schedule_send → END
```

**Intenções Detectadas**:
1. **pos_consulta**: Acompanhamento pós-consulta (2-5 dias)
2. **abandono**: Retomar conversas iniciadas (3-7 dias)
3. **lead_frio**: Reativar leads antigos (30+ dias)
4. **checagem_retorno**: Verificar necessidade de retorno (7-15 dias)
5. **reativacao**: Reativar pacientes inativos (15-60 dias)
6. **agendar_consulta**: Lembrar check-ups periódicos (90+ dias)

**Input**:
```json
{
  "patient_name": "João Silva",
  "days_inactive": 45,
  "last_message": "Obrigado!",
  "context": {"is_patient": true}
}
```

**Output**:
```json
{
  "intent": "reativacao",
  "message": "Olá João! Como você está? Faz um tempo que não nos falamos. Tem algo em que posso ajudar?",
  "ready_for_delivery": true,
  "send_at": "2025-01-22T18:00:00-03:00"
}
```

**Features**:
- ✅ 6 tipos de intenções detectadas automaticamente
- ✅ Mensagens curtas e naturais (< 500 chars)
- ✅ Agendamento inteligente com horários comerciais
- ✅ Evita finais de semana
- ✅ Validação Pydantic nos inputs

---

## 📦 Instalação

### Pré-requisitos
- Python 3.11+
- pip ou uv
- API keys (opcional: OpenAI ou Groq)

### Setup Básico

```bash
# Clone o repositório
git clone https://github.com/Rennam-Dev/taskni-core.git
cd taskni-core

# Instale as dependências
pip install -e .

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas API keys (opcional)

# Execute os testes
pytest

# Inicie o servidor
python src/run_service.py
```

O servidor estará disponível em `http://localhost:8080`

Acesse a documentação em `http://localhost:8080/docs`

---

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```bash
# LLM Providers (opcional - usa FakeModel se não configurado)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

# Configurações dos Agentes
ENABLE_INTAKE_AGENT=true
ENABLE_FAQ_AGENT=true
ENABLE_FOLLOWUP_AGENT=true
ENABLE_BILLING_AGENT=false

# LLM Settings
PRIMARY_LLM_PROVIDER=groq
FALLBACK_LLM_PROVIDER=openai
ENABLE_STREAMING=true

# RAG Settings
CHROMADB_PERSIST_DIR=./data/chroma
FAQ_COLLECTION_NAME=clinic_faq
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Cache Settings (interno ao agente)
RAG_CACHE_SIZE=50  # número de respostas em cache
```

### Settings Python

Todas as configurações estão em `src/taskni_core/core/settings.py` usando Pydantic Settings.

---

## 🔌 API Endpoints

### Health Check
```bash
GET /health
```

### Agent Registry
```bash
GET /agents
```

Retorna lista de agentes registrados:
```json
[
  {
    "id": "intake",
    "name": "IntakeAgent",
    "description": "Triagem inicial de pacientes",
    "type": "simple",
    "enabled": true
  },
  {
    "id": "faq_rag",
    "name": "FaqRagAgent",
    "description": "FAQ com RAG",
    "type": "langgraph",
    "enabled": true
  }
]
```

### Invoke Agent
```bash
POST /{agent_id}/invoke
Content-Type: application/json

{
  "message": "input parameters..."
}
```

### Stream Agent (LangGraph apenas)
```bash
POST /{agent_id}/stream
Content-Type: application/json

{
  "question": "..."
}
```

Retorna SSE (Server-Sent Events) com chunks de resposta.

---

## 📁 Estrutura do Projeto

```
taskni-core/
├── src/
│   └── taskni_core/
│       ├── agents/              # Agentes de IA
│       │   ├── base.py          # BaseAgent
│       │   ├── intake_agent.py  # IntakeAgent
│       │   ├── registry.py      # Registry de agentes
│       │   └── advanced/        # Agentes LangGraph
│       │       ├── followup_agent.py  # FollowupAgent
│       │       └── rag_agent.py       # FaqRagAgent
│       ├── core/                # Configurações
│       │   ├── llm.py           # Multi-provider LLM
│       │   └── settings.py      # Settings Pydantic
│       ├── rag/                 # Sistema RAG
│       │   ├── ingest.py        # Ingestão com detecção de firewall
│       │   └── retrieval.py     # Retrieval
│       ├── schema/              # Schemas Pydantic
│       │   ├── agent_inputs.py  # Validação de inputs
│       │   └── agent_state.py   # Estados LangGraph
│       └── service/             # FastAPI Service
│           └── service.py       # Servidor principal
├── tests/                       # Testes
│   ├── test_agents.py
│   ├── test_llm.py
│   ├── test_rag.py
│   └── test_service.py
├── test_*.py                    # Testes standalone
├── data/                        # Dados persistentes
│   └── chroma/                  # ChromaDB
├── .env                         # Variáveis de ambiente
├── pyproject.toml               # Dependências
├── PROGRESSO.md                 # Histórico de desenvolvimento
└── README.md                    # Este arquivo
```

---

## 🧪 Testes

### Rodar Todos os Testes
```bash
pytest
```

### Testes Standalone

```bash
# Teste de validação Pydantic
python test_agent_validation.py

# Teste de cache do RAG
python test_rag_cache.py

# Teste de detecção de firewall
python test_firewall_detection.py

# Teste completo do FollowupAgent
python test_followup_agent.py
```

### Cobertura de Testes

| Componente | Testes | Status |
|-----------|--------|--------|
| MultiProviderLLM | 8 | ✅ 100% |
| FaqRagAgent | 7 | ✅ 100% |
| FollowupAgent | 9 | ✅ 100% |
| Validação Pydantic | 7 | ✅ 100% |
| Cache RAG | 4 | ✅ 100% |
| Detecção Firewall | 4 | ✅ 100% |
| **TOTAL** | **39** | **✅ 100%** |

---

## 🛠️ Desenvolvimento

### Adicionar um Novo Agente

1. **Agente Simples** (herda de `BaseAgent`):
```python
# src/taskni_core/agents/my_agent.py
from taskni_core.agents.base import BaseAgent

class MyAgent(BaseAgent):
    id = "my_agent"
    name = "My Agent"
    description = "Descrição do agente"

    async def run(self, **kwargs) -> dict:
        # Sua lógica aqui
        return {"response": "..."}
```

2. **Agente LangGraph** (CompiledStateGraph):
```python
# src/taskni_core/agents/advanced/my_langgraph_agent.py
from langgraph.graph import StateGraph

def create_my_agent():
    workflow = StateGraph(MyState)
    workflow.add_node("node1", node1_func)
    workflow.add_edge("node1", END)
    workflow.set_entry_point("node1")

    graph = workflow.compile()
    graph.id = "my_langgraph"
    graph.name = "My LangGraph Agent"
    return graph
```

3. **Registrar** no `registry.py`:
```python
from taskni_core.agents.my_agent import MyAgent
agent_registry.register(
    agent=MyAgent(),
    enabled=True
)
```

---

## 🗺️ Roadmap

### ✅ Concluído
- [x] Multi-provider LLM com fallback automático
- [x] Sistema RAG completo com ChromaDB
- [x] FollowupAgent com 6 tipos de intenções
- [x] Agendamento inteligente com horários comerciais
- [x] Validação Pydantic em todos os inputs
- [x] Cache para respostas RAG
- [x] Detecção automática de firewall
- [x] 39 testes com 100% de cobertura
- [x] Documentação completa

### 🚧 Em Progresso
- [ ] BillingAgent (cobrança automática)
- [ ] Integração com WhatsApp Business API
- [ ] Dashboard de métricas

### 📋 Planejado
- [ ] Autenticação e autorização (JWT)
- [ ] Multi-tenancy (várias clínicas)
- [ ] Agente de agendamento automático
- [ ] Integração com sistemas de prontuário
- [ ] Webhooks para eventos
- [ ] Monitoramento com Prometheus/Grafana
- [ ] Deploy em Kubernetes

---

## 📊 Tecnologias Utilizadas

- **Framework Backend**: FastAPI 0.115+
- **Orquestração de Agentes**: LangGraph 0.2+
- **LLM Providers**: OpenAI, Groq, FakeModel
- **Vector Database**: ChromaDB
- **Embeddings**: OpenAI text-embedding-3-small
- **Validação**: Pydantic 2.x
- **State Management**: LangGraph StateGraph
- **Cache**: OrderedDict (Python stdlib)
- **HTTP Client**: httpx
- **Testing**: pytest

---

## 📝 Commits Recentes

```bash
0575f3d - feat: add firewall detection for embeddings
7fdac1e - feat: add caching to FaqRagAgent
6f9d5f6 - feat: add Pydantic input validation for agents
cca33b7 - feat: add intelligent scheduling to FollowupAgent
33aca99 - feat: Implementa FollowupAgent com LangGraph
894cde7 - feat: Implementa sistema RAG completo com FaqRagAgent
3750765 - feat: Implementa sistema multi-provedor LLM com streaming
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código
- Use `ruff` para linting
- Use `black` para formatação
- Adicione testes para novas features
- Atualize a documentação conforme necessário

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 👥 Autores

- **Rennam-Dev** - Desenvolvimento e manutenção

---

## 🙏 Agradecimentos

- **LangChain/LangGraph**: Framework de orquestração de agentes
- **FastAPI**: Framework web moderno e rápido
- **Anthropic/OpenAI/Groq**: Provedores de LLM
- **ChromaDB**: Vector database open-source

---

## 📧 Suporte

Para questões ou suporte, abra uma issue no GitHub ou entre em contato através do repositório.

---

**Taskni Core** - Automatizando clínicas com IA 🏥🤖
