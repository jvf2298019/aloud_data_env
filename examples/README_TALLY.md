# Tally Utils - Guia de Uso

Este guia demonstra como usar o módulo `tally_utils.py` para interagir com a API do Tally.

## 📋 Índice

- [Configuração](#configuração)
- [Instalação](#instalação)
- [Uso Básico](#uso-básico)
- [Exemplos](#exemplos)
- [Referência da API](#referência-da-api)
- [Tratamento de Erros](#tratamento-de-erros)
- [Rate Limiting](#rate-limiting)

## 🔧 Configuração

### 1. Obter API Key do Tally

1. Acesse sua conta no [Tally](https://tally.so)
2. Vá em **Settings** (Configurações)
3. Clique em **API keys**
4. Crie uma nova chave de API
5. **Importante**: Copie e salve a chave imediatamente (ela não será exibida novamente)

### 2. Configurar Variável de Ambiente

**Método 1: Linha de comando (temporário)**
```bash
export TALLY_API_KEY='sua_chave_aqui'
```

**Método 2: Arquivo .env (recomendado)**
```bash
# Adicione no arquivo .env na raiz do projeto
TALLY_API_KEY=sua_chave_aqui
```

**Método 3: Python direto**
```python
import os
os.environ['TALLY_API_KEY'] = 'sua_chave_aqui'
```

## 📦 Instalação

Não há dependências adicionais além das já presentes no projeto. O módulo usa apenas:
- `requests` - para requisições HTTP
- `pandas` - para manipulação de dados (opcional)

```bash
# Ativar ambiente virtual
source venv/bin/activate

# As dependências já devem estar instaladas
pip install -r requirements.txt
```

## 🚀 Uso Básico

### Inicializar Cliente

```python
from src.tally_utils import Tally, TallyAPIError

# Método 1: Usar variável de ambiente TALLY_API_KEY
tally = Tally()

# Método 2: Passar API key diretamente
tally = Tally(api_key='sua_chave_aqui')
```

### Listar Formulários

```python
try:
    forms = tally.get_forms()
    print(f"Total de formulários: {len(forms)}")
    
    for form in forms:
        print(f"- {form['name']} (ID: {form['id']})")
        
except TallyAPIError as e:
    print(f"Erro: {e}")
```

### Obter Detalhes de um Formulário

```python
form_id = 'abc123'  # ID do seu formulário

try:
    form = tally.get_form(form_id)
    print(f"Nome: {form['name']}")
    print(f"Status: {form['status']}")
    print(f"Criado em: {form['createdAt']}")
    
except TallyAPIError as e:
    print(f"Erro: {e}")
```

### Obter Submissões de um Formulário

```python
form_id = 'abc123'

try:
    # Obter todas as submissões
    submissions = tally.get_form_submissions(form_id)
    print(f"Total de submissões: {len(submissions)}")
    
    # Com filtros
    submissions = tally.get_form_submissions(
        form_id=form_id,
        since='2024-01-01',           # Data inicial
        until='2024-12-31',            # Data final
        status='COMPLETED',            # Apenas completas
        sort='desc',                   # Mais recentes primeiro
        limit=100                      # Máximo por página
    )
    
except TallyAPIError as e:
    print(f"Erro: {e}")
```

## 📝 Exemplos

### Exemplo 1: Exportar Submissões para CSV

```python
import pandas as pd
from src.tally_utils import Tally

tally = Tally()
form_id = 'seu_form_id'

# Obter submissões
submissions = tally.get_form_submissions(form_id)

# Converter para DataFrame
df = pd.DataFrame(submissions)

# Salvar em CSV
df.to_csv('data/processed/tally_submissions.csv', index=False)
print(f"✓ {len(df)} submissões exportadas")
```

### Exemplo 2: Analisar Submissões dos Últimos 7 Dias

```python
from datetime import datetime, timedelta
from src.tally_utils import Tally
import pandas as pd

tally = Tally()
form_id = 'seu_form_id'

# Calcular data inicial
data_inicial = (datetime.now() - timedelta(days=7)).isoformat()

# Obter submissões
submissions = tally.get_form_submissions(
    form_id=form_id,
    since=data_inicial,
    status='COMPLETED'
)

# Análise
df = pd.DataFrame(submissions)
print(f"Total de submissões (últimos 7 dias): {len(df)}")
print(f"Submissões por dia:")
df['date'] = pd.to_datetime(df['respondedAt']).dt.date
print(df.groupby('date').size())
```

### Exemplo 3: Processar Campos das Submissões

```python
from src.tally_utils import Tally

tally = Tally()
form_id = 'seu_form_id'

submissions = tally.get_form_submissions(form_id, limit=10)

for i, sub in enumerate(submissions, 1):
    print(f"\n=== Submissão {i} ===")
    print(f"ID: {sub.get('submissionId')}")
    print(f"Data: {sub.get('respondedAt')}")
    
    # Processar campos
    fields = sub.get('fields', [])
    for field in fields:
        label = field.get('label', 'Sem label')
        value = field.get('value', 'Sem valor')
        print(f"  {label}: {value}")
```

### Exemplo 4: Criar Novo Formulário

```python
from src.tally_utils import Tally

tally = Tally()

form_data = {
    "status": "DRAFT",  # DRAFT ou PUBLISHED
    "blocks": [
        {
            "type": "FORM_TITLE",
            "payload": {
                "title": "Pesquisa de Satisfação",
                "html": "<h1>Pesquisa de Satisfação</h1>"
            }
        },
        {
            "type": "INPUT_TEXT",
            "payload": {
                "label": "Nome",
                "required": True
            }
        },
        {
            "type": "INPUT_EMAIL",
            "payload": {
                "label": "Email",
                "required": True
            }
        },
        {
            "type": "TEXTAREA",
            "payload": {
                "label": "Comentários",
                "required": False
            }
        }
    ]
}

try:
    form = tally.create_form(form_data)
    print(f"✓ Formulário criado: {form['id']}")
    
except TallyAPIError as e:
    print(f"Erro: {e}")
```

### Exemplo 5: Gerenciar Webhooks

```python
from src.tally_utils import Tally

tally = Tally()
form_id = 'seu_form_id'

# Criar webhook
webhook = tally.create_webhook(
    form_id=form_id,
    url='https://seusite.com/webhook',
    event_types=['FORM_RESPONSE'],
    signing_secret='seu_segredo_unico',
    http_headers=[
        {'name': 'Authorization', 'value': 'Bearer token123'}
    ]
)
print(f"Webhook criado: {webhook['id']}")

# Listar webhooks
webhooks = tally.list_webhooks()
for wh in webhooks['data']:
    print(f"- {wh['url']} ({'Ativo' if wh['enabled'] else 'Inativo'})")

# Atualizar webhook
tally.update_webhook(
    webhook_id=webhook['id'],
    enabled=True,
    url='https://novosite.com/webhook'
)

# Listar eventos do webhook
events = tally.list_webhook_events(webhook['id'])
for event in events['data']:
    status = '✓' if event['status'] == 'success' else '✗'
    print(f"{status} {event['eventType']} - {event['createdAt']}")

# Reenviar evento falhado
failed_events = [e for e in events['data'] if e['status'] == 'failed']
for event in failed_events:
    tally.retry_webhook_event(webhook['id'], event['id'])

# Deletar webhook
tally.delete_webhook(webhook['id'])
```

### Exemplo 6: Receber e Validar Webhooks (Flask)

```python
from flask import Flask, request, jsonify
from src.tally_utils import Tally

app = Flask(__name__)
tally = Tally()

SIGNING_SECRET = 'seu_segredo_configurado_no_webhook'

@app.route('/webhook/tally', methods=['POST'])
def tally_webhook():
    # Obter dados da requisição
    payload = request.data.decode('utf-8')
    signature = request.headers.get('X-Tally-Signature', '')
    
    # Validar assinatura
    if not tally.validate_webhook_signature(
        payload=payload,
        signature=signature,
        signing_secret=SIGNING_SECRET
    ):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Processar evento
    data = request.json
    event_type = data.get('eventType')
    
    if event_type == 'FORM_RESPONSE':
        # Processar submissão do formulário
        response_data = data.get('data', {})
        form_id = response_data.get('formId')
        fields = response_data.get('fields', [])
        
        print(f"Nova submissão no formulário {form_id}")
        for field in fields:
            print(f"  {field['label']}: {field['value']}")
        
        # Salvar no banco de dados, enviar email, etc.
        save_to_database(response_data)
    
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(port=5000)
```

### Exemplo 7: Integração com MongoDB (disparos)

```python
from src.tally_utils import Tally
from src.mongo_utils import get_mongo_client
from datetime import datetime

# Obter submissões do Tally
tally = Tally()
submissions = tally.get_form_submissions('seu_form_id')

# Conectar ao MongoDB
mongo = get_mongo_client()
collection = mongo['aloud']['leads_tally']

# Processar e salvar
for sub in submissions:
    lead = {
        'nome': next((f['value'] for f in sub['fields'] if f['label'] == 'Nome'), None),
        'email': next((f['value'] for f in sub['fields'] if f['label'] == 'Email'), None),
        'telefone': next((f['value'] for f in sub['fields'] if f['label'] == 'Telefone'), None),
        'origem': 'tally',
        'form_id': sub.get('formId'),
        'submission_id': sub.get('submissionId'),
        'data_submissao': sub.get('respondedAt'),
        'data_importacao': datetime.now(),
        'processado': False
    }
    
    # Inserir (evitar duplicatas)
    collection.update_one(
        {'submission_id': lead['submission_id']},
        {'$set': lead},
        upsert=True
    )

print(f"✓ {len(submissions)} leads importados")
```

## 📚 Referência da API

### Classe `Tally`

#### `__init__(api_key: Optional[str] = None)`
Inicializa o cliente Tally.

**Parâmetros:**
- `api_key`: Chave de API (opcional se TALLY_API_KEY estiver configurada)

---

### 📋 Métodos de Formulários

#### `get_forms() -> List[Dict[str, Any]]`
Lista todos os formulários da conta.

**Retorna:** Lista de formulários

#### `get_form(form_id: str) -> Dict[str, Any]`
Obtém detalhes de um formulário específico.

**Parâmetros:**
- `form_id`: ID do formulário

**Retorna:** Dicionário com dados do formulário

#### `get_form_submissions(form_id, since=None, until=None, status=None, fields=None, sort='desc', limit=100)`
Obtém submissões de um formulário com paginação automática.

**Parâmetros:**
- `form_id`: ID do formulário
- `since`: Data inicial (ISO 8601 ou timestamp Unix)
- `until`: Data final (ISO 8601 ou timestamp Unix)
- `status`: Filtrar por status ('COMPLETED', 'IN_PROGRESS')
- `fields`: Lista de campos específicos para retornar
- `sort`: Ordenação ('asc' ou 'desc')
- `limit`: Máximo de resultados por página (max: 100)

**Retorna:** Lista de submissões

#### `create_form(form_data: Dict[str, Any], version: Optional[str] = None) -> Dict[str, Any]`
Cria um novo formulário.

**Parâmetros:**
- `form_data`: Estrutura do formulário
- `version`: Versão da API (formato: YYYY-MM-DD)

**Retorna:** Dicionário com dados do formulário criado

#### `update_form(form_id: str, form_data: Dict[str, Any], version: Optional[str] = None) -> Dict[str, Any]`
Atualiza um formulário existente.

#### `delete_form(form_id: str) -> bool`
Deleta um formulário.

---

### 🔔 Métodos de Webhooks

#### `create_webhook(form_id, url, event_types=None, signing_secret=None, http_headers=None, external_subscriber=None)`
Cria um novo webhook para um formulário.

**Parâmetros:**
- `form_id`: ID do formulário
- `url`: URL do endpoint que receberá os eventos
- `event_types`: Tipos de eventos (padrão: ['FORM_RESPONSE'])
- `signing_secret`: Segredo para validação de assinatura
- `http_headers`: Headers customizados (formato: [{"name": "X-Header", "value": "valor"}])
- `external_subscriber`: Identificador externo do subscriber

**Retorna:** Dicionário com dados do webhook criado

#### `list_webhooks(page=1, limit=25) -> Dict[str, Any]`
Lista todos os webhooks configurados.

**Parâmetros:**
- `page`: Número da página
- `limit`: Itens por página (máximo: 100)

**Retorna:** Dicionário com lista de webhooks e paginação

#### `get_webhook(webhook_id: str) -> Dict[str, Any]`
Obtém detalhes de um webhook específico.

**Parâmetros:**
- `webhook_id`: ID do webhook

**Retorna:** Dicionário com dados do webhook

#### `update_webhook(webhook_id, url=None, event_types=None, signing_secret=None, http_headers=None, external_subscriber=None, enabled=None)`
Atualiza um webhook existente.

**Parâmetros:**
- `webhook_id`: ID do webhook
- `url`: Nova URL (opcional)
- `event_types`: Novos tipos de eventos (opcional)
- `signing_secret`: Novo segredo (opcional)
- `http_headers`: Novos headers (opcional)
- `external_subscriber`: Novo identificador (opcional)
- `enabled`: Ativar/desativar (opcional)

**Retorna:** Dicionário com dados do webhook atualizado

#### `delete_webhook(webhook_id: str) -> bool`
Deleta um webhook.

**Parâmetros:**
- `webhook_id`: ID do webhook

**Retorna:** True se deletado com sucesso

#### `list_webhook_events(webhook_id, page=1, limit=25) -> Dict[str, Any]`
Lista eventos de um webhook específico.

**Parâmetros:**
- `webhook_id`: ID do webhook
- `page`: Número da página
- `limit`: Itens por página (máximo: 100)

**Retorna:** Dicionário com lista de eventos e paginação

#### `retry_webhook_event(webhook_id: str, event_id: str) -> Dict[str, Any]`
Reenvia um evento de webhook que falhou.

**Parâmetros:**
- `webhook_id`: ID do webhook
- `event_id`: ID do evento

**Retorna:** Dicionário com resultado do reenvio

#### `validate_webhook_signature(payload: str, signature: str, signing_secret: str) -> bool`
Valida a assinatura HMAC-SHA256 de um webhook recebido.

**Parâmetros:**
- `payload`: Corpo da requisição (string JSON)
- `signature`: Assinatura recebida no header X-Tally-Signature
- `signing_secret`: Segredo configurado no webhook

**Retorna:** True se a assinatura for válida

### Exceções

#### `TallyAPIError`
Exceção customizada para erros da API Tally.

```python
try:
    tally.get_form('invalid_id')
except TallyAPIError as e:
    print(f"Erro: {e}")
```

## ⚠️ Tratamento de Erros

O módulo implementa tratamento robusto de erros:

```python
from src.tally_utils import Tally, TallyAPIError
import logging

# Configurar logging para ver detalhes
logging.basicConfig(level=logging.INFO)

tally = Tally()

try:
    forms = tally.get_forms()
    
except TallyAPIError as e:
    # Erros específicos da API Tally
    print(f"Erro na API: {e}")
    
except ValueError as e:
    # Erro de configuração (API key faltando)
    print(f"Erro de configuração: {e}")
    
except Exception as e:
    # Outros erros
    print(f"Erro inesperado: {e}")
```

## 🚦 Rate Limiting

A API do Tally permite **100 requisições por minuto**.

O módulo gerencia automaticamente:
- ✅ Controle local de requisições
- ✅ Espera automática quando limite é atingido
- ✅ Retry automático em caso de erro 429
- ✅ Exponential backoff para timeouts

```python
# O módulo gerencia automaticamente!
tally = Tally()

# Mesmo fazendo muitas requisições, o módulo aguarda se necessário
for form in tally.get_forms():
    submissions = tally.get_form_submissions(form['id'])
    # Sem necessidade de sleep manual
```

### Dicas para evitar rate limiting:

1. **Use webhooks** em vez de polling frequente
2. **Processe em lotes** quando possível
3. **Cache resultados** que não mudam frequentemente
4. **Use filtros** para reduzir volume de dados

## 🔗 Recursos Úteis

- [Documentação oficial da API Tally](https://developers.tally.so/api-reference/introduction)
- [Tally API Keys](https://developers.tally.so/api-reference/api-keys)
- [Webhooks do Tally](https://tally.so/help/webhooks)
- [Changelog da API](https://developers.tally.so/api-reference/changelog)

## 📞 Executar Exemplos

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Configurar API key
export TALLY_API_KEY='sua_chave_aqui'

# Executar exemplos
python examples/exemplo_tally.py
```

## ⚙️ Configurações Avançadas

### Usar versão específica da API

```python
tally = Tally()

# Especificar versão ao fazer requisição
form = tally.create_form(form_data, version='2025-02-01')
```

### Customizar timeout e retries

```python
tally = Tally()

# Fazer requisição customizada
response = tally.make_request(
    endpoint='/forms',
    method='GET',
    timeout=60,        # 60 segundos
    max_retries=5      # 5 tentativas
)
```

### Logging detalhado

```python
import logging

# Ativar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agora verá todos os detalhes das requisições
tally = Tally()
forms = tally.get_forms()
```

## 🔔 Webhooks - Guia Completo

### O que são Webhooks?

Webhooks permitem que o Tally envie dados automaticamente para seu sistema quando um formulário é submetido, em vez de você precisar fazer polling (consultas periódicas).

**Vantagens:**
- ⚡ **Instantâneo**: Receba dados em tempo real
- 🚀 **Eficiente**: Não conta para o rate limit da API
- 💰 **Econômico**: Menos requisições = menos custo
- 🔄 **Automático**: Sem necessidade de cron jobs

### Configurar Webhook

#### 1. Criar Webhook

```python
from src.tally_utils import Tally

tally = Tally()

webhook = tally.create_webhook(
    form_id='seu_form_id',
    url='https://seusite.com/webhook',
    event_types=['FORM_RESPONSE'],
    signing_secret='segredo_aleatorio_gerado',  # Para validação
    http_headers=[
        {'name': 'Authorization', 'value': 'Bearer seu_token'}
    ]
)

print(f"Webhook ID: {webhook['id']}")
```

#### 2. Criar Endpoint para Receber Webhooks

```python
from flask import Flask, request, jsonify
from src.tally_utils import Tally

app = Flask(__name__)
tally = Tally()

@app.route('/webhook/tally', methods=['POST'])
def receive_webhook():
    # 1. Obter dados
    payload = request.data.decode('utf-8')
    signature = request.headers.get('X-Tally-Signature')
    
    # 2. Validar assinatura (IMPORTANTE!)
    if not tally.validate_webhook_signature(
        payload=payload,
        signature=signature,
        signing_secret='seu_segredo'
    ):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # 3. Processar dados
    data = request.json
    print(f"Evento: {data['eventType']}")
    print(f"Form ID: {data['data']['formId']}")
    
    # 4. Sua lógica aqui
    # - Salvar no banco
    # - Enviar email
    # - Adicionar à fila de disparos
    
    return jsonify({'status': 'success'}), 200
```

#### 3. Gerenciar Webhooks

```python
# Listar todos webhooks
webhooks = tally.list_webhooks()

# Obter detalhes de um webhook
webhook = tally.get_webhook('webhook_id')

# Atualizar webhook (ex: nova URL)
tally.update_webhook(
    webhook_id='webhook_id',
    url='https://nova-url.com/webhook',
    enabled=True
)

# Desativar webhook temporariamente
tally.update_webhook(webhook_id='webhook_id', enabled=False)

# Deletar webhook
tally.delete_webhook('webhook_id')
```

#### 4. Monitorar e Reenviar Eventos

```python
# Listar eventos de um webhook
events = tally.list_webhook_events('webhook_id')

# Encontrar eventos falhados
failed_events = [
    e for e in events['data'] 
    if e['status'] == 'failed'
]

# Reenviar eventos falhados
for event in failed_events:
    tally.retry_webhook_event('webhook_id', event['id'])
    print(f"Reenviado: {event['id']}")
```

### Tipos de Eventos

- `FORM_RESPONSE` - Nova submissão do formulário (mais comum)
- `FORM_UPDATED` - Formulário foi atualizado
- Outros eventos conforme documentação do Tally

### Estrutura de Dados do Webhook

Quando uma submissão é feita, você receberá:

```json
{
  "eventId": "evt_abc123",
  "eventType": "FORM_RESPONSE",
  "createdAt": "2024-11-24T10:30:00Z",
  "data": {
    "responseId": "resp_xyz789",
    "formId": "form_123",
    "formName": "Cadastro de Leads",
    "respondedAt": "2024-11-24T10:30:00Z",
    "fields": [
      {
        "key": "field_name",
        "label": "Nome",
        "type": "INPUT_TEXT",
        "value": "João Silva"
      },
      {
        "key": "field_email",
        "label": "Email",
        "type": "INPUT_EMAIL",
        "value": "joao@example.com"
      }
    ]
  }
}
```

### Segurança com Signing Secret

**SEMPRE valide a assinatura** para garantir que o webhook veio realmente do Tally:

```python
# O Tally envia no header: X-Tally-Signature
signature = request.headers.get('X-Tally-Signature')

# Validar
is_valid = tally.validate_webhook_signature(
    payload=request.data.decode('utf-8'),
    signature=signature,
    signing_secret='seu_segredo'
)

if not is_valid:
    return {'error': 'Invalid signature'}, 401
```

### Deploy de Webhook

Para receber webhooks em produção, você precisa:

1. **URL Pública HTTPS** (obrigatório)
   - Use serviços como: Heroku, Railway, Render, DigitalOcean
   - Configure SSL/TLS (Let's Encrypt gratuito)

2. **Endpoint sempre disponível**
   - Use serviços serverless (AWS Lambda, Google Cloud Functions)
   - Ou servidor tradicional com boa disponibilidade

3. **Para testes locais:**
   - Use [ngrok](https://ngrok.com) para expor localhost
   - Ou use [webhook.site](https://webhook.site) para ver payloads

```bash
# Expor localhost com ngrok
ngrok http 5000
# Use a URL gerada: https://abc123.ngrok.io/webhook/tally
```

### Exemplo Completo: Sistema de Disparos

```python
from flask import Flask, request, jsonify
from src.tally_utils import Tally
from src.mongo_utils import get_mongo_client
from datetime import datetime

app = Flask(__name__)
tally = Tally()
mongo = get_mongo_client()

SIGNING_SECRET = 'seu_segredo'

@app.route('/webhook/tally', methods=['POST'])
def tally_webhook():
    # Validar assinatura
    if not tally.validate_webhook_signature(
        payload=request.data.decode('utf-8'),
        signature=request.headers.get('X-Tally-Signature', ''),
        signing_secret=SIGNING_SECRET
    ):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Processar dados
    data = request.json
    response_data = data.get('data', {})
    fields = {f['label']: f['value'] for f in response_data.get('fields', [])}
    
    # Criar lead
    lead = {
        'nome': fields.get('Nome'),
        'email': fields.get('Email'),
        'telefone': fields.get('Telefone'),
        'origem': 'tally_webhook',
        'form_id': response_data.get('formId'),
        'submission_id': response_data.get('responseId'),
        'data_submissao': response_data.get('respondedAt'),
        'data_processamento': datetime.now(),
        'processado': False,
        'dados_completos': fields
    }
    
    # Salvar no MongoDB
    mongo['aloud']['leads'].insert_one(lead)
    
    # Adicionar à fila de disparos (exemplo)
    mongo['aloud']['fila_disparos'].insert_one({
        'lead_id': lead['_id'],
        'tipo': 'whatsapp',
        'status': 'pendente',
        'criado_em': datetime.now()
    })
    
    return jsonify({'status': 'success', 'lead_id': str(lead['_id'])}), 200
```

## 🎯 Casos de Uso Comuns

### 1. Sistema de Disparo de Email/SMS
Usar webhooks para receber leads em tempo real e adicionar à fila de disparos

### 2. Dashboard de Métricas
Analisar submissões e criar dashboards com pandas/plotly

### 3. Integração CRM
Sincronizar submissões do Tally com CRM (Hotmart, RD Station, etc) via webhooks

### 4. Backup Automático
Exportar submissões periodicamente para backup

### 5. Validação de Dados
Processar e validar campos das submissões em tempo real

### 6. Automação de Marketing
Disparar sequências de email marketing quando novo lead entra

---

**Desenvolvido para:** Projeto Aloud - Data Environment  
**Versão:** 1.0  
**Data:** Novembro 2024

