# 🆓 Configuração de LLMs Gratuitas para o Taskni Core

Este guia mostra como configurar APIs de LLM gratuitas como backup para o Groq.

## 📋 Opções Recomendadas (em ordem de prioridade)

### 1. Google AI Studio (Gemini) ⭐ MELHOR OPÇÃO

**Por quê:**
- ✅ Completamente gratuito
- ✅ 15 requests/minuto (muito generoso)
- ✅ Modelos excelentes (Gemini 2.0 Flash)
- ✅ Sem necessidade de cartão de crédito
- ✅ Português nativo

**Como obter a API key:**

1. Acesse: https://aistudio.google.com/apikey
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie a chave gerada

**Configuração no .env:**

```bash
# Google AI Studio (Gemini) - GRATUITO
GOOGLE_API_KEY=sua_chave_aqui
DEFAULT_MODEL=gemini-2.0-flash

# Alternativa: Gemini 1.5 Pro (mais poderoso, mesmo tier gratuito)
# DEFAULT_MODEL=gemini-1.5-pro
```

**Modelos disponíveis:**
- `gemini-2.0-flash` - Rápido, eficiente (recomendado)
- `gemini-2.0-flash-lite` - Ultra rápido, mais leve
- `gemini-1.5-pro` - Mais poderoso, context window maior

**Limites (tier gratuito):**
- 15 requests/minuto
- 1 milhão de tokens/mês
- 1500 requests/dia

---

### 2. Ollama (Local) ⭐ SEM LIMITES

**Por quê:**
- ✅ 100% gratuito e privado
- ✅ SEM limites de uso
- ✅ Roda offline
- ✅ Vários modelos disponíveis
- ⚠️  Precisa de recursos locais (RAM/CPU/GPU)

**Instalação:**

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Baixe de https://ollama.com/download
```

**Baixar modelos:**

```bash
# Modelos recomendados para produção
ollama pull llama3.2              # Rápido, bom (3B)
ollama pull llama3.1:8b           # Balanceado (8B)
ollama pull mistral               # Excelente qualidade (7B)

# Modelos menores (para hardware limitado)
ollama pull phi3                  # Muito rápido (3.8B)
ollama pull gemma2:2b             # Ultra leve (2B)
```

**Configuração no .env:**

```bash
# Ollama (Local)
OLLAMA_MODEL=llama3.2
DEFAULT_MODEL=ollama

# Se rodar Ollama em outro servidor
# OLLAMA_BASE_URL=http://seu-servidor:11434
```

**Iniciar Ollama:**

```bash
# Inicia o servidor Ollama
ollama serve

# Em outro terminal, teste
ollama run llama3.2 "Olá em português"
```

---

### 3. OpenRouter ⭐ FALLBACK

**Por quê:**
- ✅ Acesso a vários modelos gratuitos
- ✅ Fallback automático entre modelos
- ✅ API unificada
- ⚠️  Limites por modelo

**Como obter a API key:**

1. Acesse: https://openrouter.ai/keys
2. Crie uma conta (gratuita)
3. Gere uma API key

**Configuração no .env:**

```bash
# OpenRouter
OPENROUTER_API_KEY=sua_chave_aqui
DEFAULT_MODEL=google/gemini-2.5-flash

# Outros modelos gratuitos disponíveis:
# DEFAULT_MODEL=meta-llama/llama-3.2-3b-instruct:free
# DEFAULT_MODEL=google/gemini-flash-1.5:free
```

**Modelos gratuitos:**
- `google/gemini-2.5-flash` - Google Gemini (gratuito)
- `meta-llama/llama-3.2-3b-instruct:free` - Meta Llama
- `microsoft/phi-3-mini-128k-instruct:free` - Microsoft Phi-3

---

### 4. Hugging Face Inference API

**Por quê:**
- ✅ Gratuito
- ✅ Muitos modelos
- ⚠️  Rate limits baixos
- ⚠️  Pode ter cold start (lento)

**Como obter a API key:**

1. Acesse: https://huggingface.co/settings/tokens
2. Crie uma conta
3. Gere um Access Token

**Configuração:**

```bash
# Hugging Face
HUGGINGFACE_API_KEY=hf_...
DEFAULT_MODEL=meta-llama/Llama-3.2-3B-Instruct
```

---

## 🔄 Sistema de Fallback Automático

Para máxima disponibilidade, você pode configurar múltiplas APIs:

```bash
# .env com fallback automático

# Opção 1: Groq (quando voltar)
GROQ_API_KEY=gsk_...

# Opção 2: Google Gemini (fallback principal)
GOOGLE_API_KEY=AI...

# Opção 3: Ollama (fallback local)
OLLAMA_MODEL=llama3.2

# Opção 4: OpenRouter (fallback final)
OPENROUTER_API_KEY=sk-or-...

# Prioridade de uso
DEFAULT_MODEL=llama-3.1-8b  # Tenta Groq primeiro
# Se Groq falhar, sistema tenta automaticamente Gemini, depois Ollama
```

---

## 💰 Comparação de Custos

| Provider | Custo | Limite Gratuito | Velocidade | Qualidade |
|----------|-------|-----------------|------------|-----------|
| **Gemini** | Grátis | 1M tokens/mês | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| **Ollama** | Grátis | Ilimitado* | ⚡⚡ | ⭐⭐⭐ |
| **Groq** | Grátis | Variável | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ |
| **OpenRouter** | Grátis/Pago | Limitado | ⚡⚡⚡ | ⭐⭐⭐ |
| **HuggingFace** | Grátis | Muito limitado | ⚡ | ⭐⭐⭐ |

*Ilimitado mas depende do seu hardware

---

## 🎯 Recomendação Final

**Para produção imediata (agora):**
```bash
GOOGLE_API_KEY=sua_chave_gemini
DEFAULT_MODEL=gemini-2.0-flash
```

**Para desenvolvimento (sem limites):**
```bash
OLLAMA_MODEL=llama3.2
DEFAULT_MODEL=ollama
```

**Para máxima disponibilidade (quando Groq voltar):**
```bash
# Tenta Groq primeiro, fallback para Gemini
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AI...
DEFAULT_MODEL=llama-3.1-8b  # Groq
# Sistema automaticamente usa Gemini se Groq falhar
```

---

## 🚀 Próximos Passos

1. **Escolha uma opção acima**
2. **Obtenha a API key**
3. **Configure o .env**
4. **Reinicie o servidor**
5. **Teste com:** `python test_intake_scenarios.py`

---

## 📞 Suporte

- Gemini: https://ai.google.dev/docs
- Ollama: https://ollama.com/docs
- OpenRouter: https://openrouter.ai/docs
- Groq: https://console.groq.com/docs
