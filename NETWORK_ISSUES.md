# 🌐 Problemas de Rede Identificados

## Situação Atual

O ambiente de desenvolvimento está atrás de um **proxy/firewall** que bloqueia requisições HTTPS para APIs externas de LLM.

## 🔍 Evidências

### 1. Google Gemini
```
Erro: HTTP 403 Forbidden
IP resolvido: 21.0.0.13 (IP de proxy, não Google)
SSL Error: CERTIFICATE_VERIFY_FAILED (self signed certificate)
```

### 2. Groq
```
Erro: HTTP 403 "Access denied"
Causa: Problema de billing/quota (não é rede)
Pode funcionar após resolver no console
```

## 🎯 Soluções Possíveis

### Opção 1: FakeModel (ATUAL) ✅
```bash
USE_FAKE_MODEL=true
DEFAULT_MODEL=fake
```
**Vantagens:**
- ✅ Funciona sem restrições
- ✅ Valida toda a lógica
- ✅ Sem dependência de rede

**Limitações:**
- ⚠️  Respostas sempre iguais
- ⚠️  Não testa modelo real

---

### Opção 2: Ollama (LOCAL) ⭐ RECOMENDADO
```bash
# Instalar Ollama localmente
curl -fsSL https://ollama.com/install.sh | sh

# Baixar modelo
ollama pull llama3.2

# Iniciar servidor
ollama serve

# Configurar .env
OLLAMA_MODEL=llama3.2
DEFAULT_MODEL=ollama
```

**Vantagens:**
- ✅ Roda 100% local (sem internet)
- ✅ Sem limites de uso
- ✅ Sem bloqueios de firewall
- ✅ Modelos reais (llama3, mistral, etc)
- ✅ Respostas variadas e inteligentes

**Requisitos:**
- RAM: 8GB+ recomendado
- CPU: Qualquer (GPU opcional)
- Espaço: ~4-8GB por modelo

---

### Opção 3: Resolver Proxy/Firewall

Se você tem acesso administrativo ao ambiente:

```bash
# Configurar proxy bypass
export NO_PROXY="localhost,127.0.0.1,*.googleapis.com,*.groq.com"

# OU desabilitar verificação SSL (não recomendado em produção)
export CURL_CA_BUNDLE=""
export REQUESTS_CA_BUNDLE=""
```

⚠️ **Não recomendado:** Desabilitar verificação SSL é um risco de segurança.

---

### Opção 4: Usar VPN/Tunnel

Se permitido pela política da organização:

```bash
# SSH Tunnel
ssh -D 8080 usuario@servidor-externo

# Configurar proxy SOCKS
export ALL_PROXY=socks5://localhost:8080
```

---

## 💡 Recomendação para Produção

### Para Desenvolvimento (Agora):
```bash
# Use Ollama - funciona localmente
OLLAMA_MODEL=llama3.2
DEFAULT_MODEL=ollama
```

### Para Produção (Quando deploy):
```bash
# Use Groq (após resolver billing) ou Gemini
# Em servidor de produção sem proxy
GROQ_API_KEY=gsk_...
DEFAULT_MODEL=llama-3.1-8b
```

---

## 🧪 Como Testar

### Teste de conectividade:
```bash
# Testa se consegue acessar APIs
curl -I https://generativelanguage.googleapis.com
curl -I https://api.groq.com

# Se der erro SSL ou proxy, está bloqueado
```

### Teste com Ollama:
```bash
# Instala e testa
ollama pull llama3.2
ollama run llama3.2 "Diga olá em português"

# Se funcionar, configure no .env
```

---

## 📊 Comparação de Opções

| Opção | Funciona? | Custo | Qualidade | Setup |
|-------|-----------|-------|-----------|-------|
| FakeModel | ✅ Sim | Grátis | ⭐ | 0min |
| **Ollama** | ✅ Sim | Grátis | ⭐⭐⭐⭐ | 5min |
| Gemini | ❌ Bloqueado | Grátis | ⭐⭐⭐⭐⭐ | - |
| Groq | ❌ Billing | Grátis | ⭐⭐⭐⭐ | - |

---

## 🚀 Próximos Passos

1. **Continue desenvolvimento com FakeModel**
   - Valida toda a lógica
   - Implementa features
   - Testes estruturais

2. **Instale Ollama quando quiser testar modelo real**
   - Sem bloqueios
   - Sem custos
   - Respostas reais

3. **Em produção, use Groq ou Gemini**
   - Após resolver problemas de rede/billing
   - APIs externas funcionarão normalmente
