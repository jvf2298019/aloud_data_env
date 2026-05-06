## Tally Utils - Guia Completo

Guia de uso do módulo `tally_utils.py` para interagir com a API do Tally.

## 📋 Índice

- [Configuração](#configuração)
- [Uso Básico](#uso-básico)
- [Formulários](#formulários)
- [Submissões](#submissões)
- [Webhooks](#webhooks)
- [Referência da API](#referência-da-api)
- [Exemplos Práticos](#exemplos-práticos)

## 🔧 Configuração

### 1. Obter API Key do Tally

1. Acesse [Tally](https://tally.so)
2. Vá em **Settings** → **API keys**
3. Crie uma nova chave de API
4. **Importante**: Copie imediatamente (não será exibida novamente)

### 2. Configurar Variável de Ambiente

```bash
export TALLY_API_KEY='sua_chave_aqui'
```

Ou no arquivo `.env`:
```
TALLY_API_KEY=sua_chave_aqui
```

## 🚀 Uso Básico

### Inicializar Cliente

```python
from src.tally_utils import Tally, TallyAPIError

# Usar variável de ambiente
tally = Tally()

# Ou passar chave diretamente
tally = Tally(api_key='sua_chave')
```

## 📋 Formulários

### Listar Formulários

```python
forms = tally.get_forms()
print(f"Total: {len(forms)}")

for form in forms:
    print(f"- {form['name']} (ID: {form['id']})")
```

### Obter Detalhes

```python
form = tally.get_form('form_id')
print(f"Nome: {form['name']}")
print(f"Status: {form['status']}")
```

### Criar Formulário

```python
form_data = {
    "status": "DRAFT",
    "blocks": [
        {
            "type": "FORM_TITLE",
            "payload": {
                "title": "Meu Formulário",
                "html": "<h1>Meu Formulário</h1>"
            }
        },
        {
            "type": "INPUT_TEXT",
            "payload": {
                "label": "Nome",
                "required": True
            }
        }
    ]
}

form = tally.create_form(form_data)
print(f"Criado: {form['id']}")
```

## 📝 Submissões

### Obter Submissões

```python
# Todas as submissões
submissions = tally.get_form_submissions('form_id')

# Com filtros
submissions = tally.get_form_submissions(
    form_id='form_id',
    since='2024-01-01',
    until='2024-12-31',
    status='COMPLETED',
    sort='desc',
    limit=100
)

print(f"Total: {len(submissions)}")
```

### Processar Submissões

```python
for sub in submissions:
    print(f"\nSubmissão: {sub['submissionId']}")
    print(f"Data: {sub['respondedAt']}")
    
    for field in sub.get('fields', []):
        print(f"  {field['label']}: {field['value']}")
```

### Exportar para CSV

```python
import pandas as pd

submissions = tally.get_form_submissions('form_id')
df = pd.DataFrame(submissions)
df.to_csv('submissoes.csv', index=False)
```

## 🔔 Webhooks

### Por que usar Webhooks?

- ⚡ **Instantâneo**: Dados em tempo real
- 🚀 **Eficiente**: Não conta para rate limit
- 💰 **Econômico**: Menos requisições
- 🔄 **Automático**: Sem polling

### Criar Webhook

```python
webhook = tally.create_webhook(
    form_id='form_id',
    url='https://seusite.com/webhook',
    event_types=['FORM_RESPONSE'],
    signing_secret='segredo_unico',
    http_headers=[
        {'name': 'Authorization', 'value': 'Bearer token'}
    ]
)

print(f"Webhook ID: {webhook['id']}")
```

### Listar Webhooks

```python
result = tally.list_webhooks()
webhooks = result['data']

for wh in webhooks:
    status = '🟢' if wh['enabled'] else '🔴'
    print(f"{status} {wh['url']}")
```

### Atualizar Webhook

```python
tally.update_webhook(
    webhook_id='webhook_id',
    url='https://nova-url.com/webhook',
    is_enabled=True
)
```

### Gerenciar Eventos

```python
# Listar eventos
events = tally.list_webhook_events('webhook_id')

# Reenviar eventos falhados
for event in events['data']:
    if event['status'] == 'failed':
        tally.retry_webhook_event('webhook_id', event['id'])
```

### Deletar Webhook

```python
tally.delete_webhook('webhook_id')
```

## 🔒 Validar Webhook

### Em seu Endpoint (Flask)

```python
from flask import Flask, request, jsonify
from src.tally_utils import Tally

app = Flask(__name__)
tally = Tally()

SIGNING_SECRET = 'seu_segredo_do_webhook'

@app.route('/webhook/tally', methods=['POST'])
def tally_webhook():
    # Obter dados
    payload = request.data.decode('utf-8')
    signature = request.headers.get('X-Tally-Signature', '')
    
    # Validar assinatura (IMPORTANTE!)
    if not tally.validate_webhook_signature(
        payload=payload,
        signature=signature,
        signing_secret=SIGNING_SECRET
    ):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Processar webhook
    data = request.json
    event_type = data.get('eventType')
    
    if event_type == 'FORM_RESPONSE':
        response_data = data['data']
        form_id = response_data['formId']
        fields = response_data['fields']
        
        print(f"Nova submissão: {form_id}")
        for field in fields:
            print(f"  {field['label']}: {field['value']}")
        
        # Salvar no banco, enviar email, etc.
    
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(port=5000)
```

### Estrutura do Webhook

```json
{
  "eventId": "evt_abc123",
  "eventType": "FORM_RESPONSE",
  "createdAt": "2024-11-24T10:30:00Z",
  "data": {
    "responseId": "resp_xyz789",
    "formId": "form_123",
    "formName": "Cadastro",
    "respondedAt": "2024-11-24T10:30:00Z",
    "fields": [
      {
        "label": "Nome",
        "type": "INPUT_TEXT",
        "value": "João Silva"
      },
      {
        "label": "Email",
        "type": "INPUT_EMAIL",
        "value": "joao@example.com"
      }
    ]
  }
}
```

## 📚 Referência da API

### Classe `Tally`

#### Formulários

| Método | Descrição |
|--------|-----------|
| `get_forms()` | Lista todos os formulários |
| `get_form(form_id)` | Obtém detalhes de um formulário |
| `create_form(form_data)` | Cria novo formulário |
| `update_form(form_id, data)` | Atualiza formulário |
| `delete_form(form_id)` | Deleta formulário |

#### Submissões

| Método | Descrição |
|--------|-----------|
| `get_form_submissions(form_id, ...)` | Obtém submissões (paginação automática) |

**Parâmetros:**
- `since`: Data inicial (ISO 8601)
- `until`: Data final
- `status`: 'COMPLETED', 'IN_PROGRESS'
- `sort`: 'asc' ou 'desc'
- `limit`: Max por página (100)

#### Webhooks

| Método | Descrição |
|--------|-----------|
| `create_webhook(form_id, url, ...)` | Cria webhook |
| `list_webhooks(page, limit)` | Lista webhooks |
| `get_webhook(webhook_id)` | Obtém detalhes |
| `update_webhook(webhook_id, ...)` | Atualiza webhook |
| `delete_webhook(webhook_id)` | Deleta webhook |
| `list_webhook_events(webhook_id)` | Lista eventos |
| `retry_webhook_event(webhook_id, event_id)` | Reenvia evento |
| `validate_webhook_signature(...)` | Valida assinatura |

## 💡 Exemplos Práticos

### Sistema de Leads

```python
from src.tally_utils import Tally
from src.mongo_utils import get_mongo_client
from datetime import datetime

tally = Tally()
mongo = get_mongo_client()

# Obter submissões
submissions = tally.get_form_submissions('form_id')

# Salvar no MongoDB
for sub in submissions:
    fields = {f['label']: f['value'] for f in sub['fields']}
    
    lead = {
        'nome': fields.get('Nome'),
        'email': fields.get('Email'),
        'telefone': fields.get('Telefone'),
        'origem': 'tally',
        'form_id': sub['formId'],
        'submission_id': sub['submissionId'],
        'data_submissao': sub['respondedAt'],
        'data_importacao': datetime.now()
    }
    
    mongo['aloud']['leads'].update_one(
        {'submission_id': lead['submission_id']},
        {'$set': lead},
        upsert=True
    )
```

### Dashboard com Pandas

```python
import pandas as pd
from src.tally_utils import Tally

tally = Tally()
submissions = tally.get_form_submissions('form_id')

df = pd.DataFrame(submissions)
df['date'] = pd.to_datetime(df['respondedAt']).dt.date

# Análise
print("Submissões por dia:")
print(df.groupby('date').size())

print("\nEstatísticas:")
print(df.describe())
```

### Webhook com MongoDB

```python
from flask import Flask, request, jsonify
from src.tally_utils import Tally
from src.mongo_utils import get_mongo_client
from datetime import datetime

app = Flask(__name__)
tally = Tally()
mongo = get_mongo_client()

@app.route('/webhook/tally', methods=['POST'])
def webhook():
    # Validar
    if not tally.validate_webhook_signature(
        payload=request.data.decode('utf-8'),
        signature=request.headers.get('X-Tally-Signature', ''),
        signing_secret='seu_segredo'
    ):
        return jsonify({'error': 'Invalid'}), 401
    
    # Processar
    data = request.json
    response_data = data['data']
    fields = {f['label']: f['value'] for f in response_data['fields']}
    
    # Salvar
    lead = {
        'nome': fields.get('Nome'),
        'email': fields.get('Email'),
        'origem': 'tally_webhook',
        'data': datetime.now()
    }
    
    mongo['aloud']['leads'].insert_one(lead)
    
    return jsonify({'status': 'success'}), 200
```

## 🚦 Rate Limiting

A API do Tally permite **100 requisições por minuto**.

O módulo gerencia automaticamente:
- ✅ Controle local de requisições
- ✅ Espera automática quando limite atingido
- ✅ Retry automático em caso de 429
- ✅ Exponential backoff

**Dica**: Use webhooks em vez de polling!

## ⚠️ Tratamento de Erros

```python
from src.tally_utils import Tally, TallyAPIError

tally = Tally()

try:
    forms = tally.get_forms()
    
except TallyAPIError as e:
    print(f"Erro na API: {e}")
    
except ValueError as e:
    print(f"Erro de configuração: {e}")
```

## 🚀 Deploy de Webhooks

### Para Testes Locais

```bash
# Use ngrok para expor localhost
ngrok http 5000

# Use a URL gerada:
# https://abc123.ngrok.io/webhook/tally
```

### Para Produção

1. **URL HTTPS obrigatória**
2. **Configure signing_secret único**
3. **SEMPRE valide assinatura**
4. **Monitore eventos falhados**

Serviços recomendados:
- Heroku
- Railway
- Render
- DigitalOcean
- AWS Lambda

## 📞 Executar Exemplos

```bash
# Ativar ambiente
source venv/bin/activate

# Configurar API key
export TALLY_API_KEY='sua_chave'

# Executar
python examples/exemplo_tally.py
python examples/exemplo_tally_webhooks.py
```

## 🔗 Recursos

- [Documentação API Tally](https://developers.tally.so/api-reference/introduction)
- [API Keys](https://developers.tally.so/api-reference/api-keys)
- [Webhooks](https://tally.so/help/webhooks)
- [Changelog](https://developers.tally.so/api-reference/changelog)

---

**Desenvolvido para:** Projeto Aloud - Data Environment  
**Versão:** 1.0  
**Data:** Dezembro 2024

