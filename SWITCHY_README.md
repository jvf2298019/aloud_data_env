# 🔗 Switchy API - Guia Completo

Utilitário para integração com a API GraphQL do Switchy.

**Endpoint:** https://graphql.switchy.io/v1/graphql  
**Documentação oficial:** https://developers.switchy.io/docs/overview/index

---

## 🚀 Quick Start

### 1. Configure a API Key

```bash
export SWITCHY_API_KEY="735c8051-ef80-4287-bd17-06d7176ad956"
```

### 2. Use em Python

```python
from src.switchy_utils import SwitchyAPI

# Inicializar
api = SwitchyAPI()

# Listar links
links = api.get_links(limit=10)

# Atualizar URL
result = api.update_link_url('link_id', 'https://nova-url.com')

# Configurar rotator
result = api.update_link_rotator('link_id', [
    'https://url1.com',
    'https://url2.com'
])
```

### 3. Testar Exemplos Interativos

```bash
python examples/exemplo_switchy.py
```

---

## 📦 Arquivos do Projeto

```
src/
  └── switchy_utils.py           ⭐ Biblioteca principal

examples/
  └── exemplo_switchy.py         ⭐ Script interativo com exemplos

SWITCHY_README.md                📖 Este arquivo
```

---

## 🎯 Funcionalidades

### ✅ Consultar Links

```python
api = SwitchyAPI()

# Listar todos
links = api.get_links(limit=50)

# Buscar por ID
link = api.get_link_by_id('abc123', 'sw.page')

# Buscar por tag
links = api.get_links_by_tag('bf25')
links = api.get_links_by_tag(['bf25', 'promo'])

# Buscar por texto
links = api.search_links('black friday')

# Top links mais clicados
top = api.get_top_links(limit=10, min_clicks=100)

# Filtros avançados
links = api.get_links(
    filters={'clicks': {'_gt': 100}},
    order_by={'createdDate': 'desc'}
)
```

### ✅ Alterar Apontamento

```python
# Atualizar URL individual
result = api.update_link_url('link_id', 'https://nova-url.com')

# Com deep linking
result = api.update_link_url(
    'link_id',
    'https://nova-url.com',
    deep_linking_enable=True
)

# Atualização em massa
result = api.update_links_bulk(
    filters={'tags': {'_contains': ['test']}},
    updates={'url': 'https://nova-url-geral.com'}
)
```

### ✅ Configurar Link Rotator

```python
# Rotator com distribuição automática
# Ex: 2 extras = 33% cada, principal 34%
result = api.update_link_rotator('link_id', [
    'https://url1.com',
    'https://url2.com'
])

# Rotator com pesos customizados
result = api.set_link_rotator_custom('link_id', [
    {'url': 'https://url1.com', 'value': 70},
    {'url': 'https://url2.com', 'value': 30}
])

# Remover rotator
result = api.clear_link_rotator('link_id')
```

### ✅ Configurar Expiração

```python
from datetime import datetime, timedelta

# Expiração por data
expiry = datetime.now() + timedelta(days=30)
result = api.set_link_expiration_by_date(
    'link_id',
    expiry,
    redirect_url='https://expirado.com'  # opcional
)

# Expiração por cliques
result = api.set_link_expiration_by_clicks(
    'link_id',
    max_clicks=1000,
    redirect_url='https://limite.com'  # opcional
)

# Remover expiração
result = api.clear_link_expiration('link_id')
```

### ✅ Outros Recursos

```python
# Estatísticas
stats = api.get_statistics()
# Retorna: total_links, total_clicks, average_clicks, etc.

# Domínios
domains = api.get_domains()

# Pastas
folders = api.get_folders()
```

---

## 📚 API Reference

### Classe `SwitchyAPI`

#### Inicialização

```python
api = SwitchyAPI()  # Usa SWITCHY_API_KEY do ambiente
api = SwitchyAPI(api_key="sua-key")  # Passa diretamente
```

#### Métodos de Consulta

| Método | Descrição |
|--------|-----------|
| `get_links(fields, limit, offset, order_by, filters)` | Lista links com filtros |
| `get_link_by_id(link_id, domain, fields)` | Busca link específico |
| `search_links(search_text, search_in, limit)` | Busca por texto |
| `get_links_by_tag(tags, limit)` | Busca por tag(s) |
| `get_top_links(limit, min_clicks)` | Links mais clicados |

#### Métodos de Atualização

| Método | Descrição |
|--------|-----------|
| `update_link_url(link_id, new_url, deep_linking_enable)` | Atualiza URL |
| `update_links_bulk(filters, updates)` | Atualização em massa |

#### Link Rotator

| Método | Descrição |
|--------|-----------|
| `update_link_rotator(link_id, extra_urls)` | Distribui automaticamente |
| `set_link_rotator_custom(link_id, urls_with_weights)` | Pesos customizados |
| `clear_link_rotator(link_id)` | Remove rotator |

#### Link Expiration

| Método | Descrição |
|--------|-----------|
| `set_link_expiration_by_date(link_id, date, redirect_url)` | Expira por data |
| `set_link_expiration_by_clicks(link_id, max_clicks, redirect_url)` | Expira por cliques |
| `clear_link_expiration(link_id)` | Remove expiração |

#### Outros

| Método | Descrição |
|--------|-----------|
| `get_domains()` | Lista domínios |
| `get_folders()` | Lista pastas |
| `get_statistics()` | Estatísticas da conta |

---

## 🔧 Funções Standalone (Compatibilidade)

Para manter compatibilidade com código existente:

```python
from src.switchy_utils import get_links, update_link_url, update_link_rotator

# Mesma interface das suas funções originais
links = get_links()
result = update_link_url('id', 'url', deepLinkingEnable=True)
result = update_link_rotator('id', ['url1', 'url2'])
```

---

## 💡 Exemplos Práticos

### Exemplo 1: Listar e Filtrar

```python
from src.switchy_utils import SwitchyAPI

api = SwitchyAPI()

# Listar últimos 10 links
links = api.get_links(
    limit=10,
    order_by={'createdDate': 'desc'}
)

for link in links:
    print(f"{link['title']}: {link['url']}")
```

### Exemplo 2: Atualizar Campanha

```python
from src.switchy_utils import SwitchyAPI

api = SwitchyAPI()

# Buscar links da campanha
links = api.get_links_by_tag('bf25')

# Atualizar todos de uma vez
result = api.update_links_bulk(
    filters={'tags': {'_contains': ['bf25']}},
    updates={'url': 'https://nova-oferta.com'}
)

print(f"✅ {result['affected_rows']} links atualizados")
```

### Exemplo 3: Rotacionar Ofertas

```python
from src.switchy_utils import SwitchyAPI

api = SwitchyAPI()

# Configurar rotação entre 3 ofertas
# Cada uma receberá ~25%, principal ~25%
api.update_link_rotator('link_id', [
    'https://oferta1.com',
    'https://oferta2.com',
    'https://oferta3.com'
])
```

### Exemplo 4: Expiração em Massa

```python
from src.switchy_utils import SwitchyAPI
from datetime import datetime, timedelta

api = SwitchyAPI()

# Data de expiração
expiry = datetime(2025, 12, 31, 23, 59, 59)

# Buscar links
links = api.get_links_by_tag('bf25')

# Configurar expiração para todos
for link in links:
    api.set_link_expiration_by_date(
        link['id'],
        expiry,
        'https://campanha-encerrada.com'
    )
    print(f"✅ {link['title']}: configurado")
```

### Exemplo 5: Uso em Notebook

```python
# Em um Jupyter Notebook
import sys
sys.path.insert(0, '../src')

from switchy_utils import SwitchyAPI
import pandas as pd

# Buscar dados
api = SwitchyAPI()
links = api.get_links_by_tag('bf25')

# Converter para DataFrame
df = pd.DataFrame(links)
df[['title', 'url', 'clicks']].head()
```

---

## 🔍 Filtros Avançados (Hasura)

A API usa Hasura, que oferece filtros poderosos:

### Operadores Disponíveis

```python
# Igualdade
filters = {'clicks': {'_eq': 100}}

# Comparação
filters = {'clicks': {'_gt': 100}}      # maior que
filters = {'clicks': {'_gte': 100}}     # maior ou igual
filters = {'clicks': {'_lt': 100}}      # menor que
filters = {'clicks': {'_lte': 100}}     # menor ou igual

# Texto
filters = {'name': {'_like': '%promo%'}}      # case sensitive
filters = {'name': {'_ilike': '%promo%'}}     # case insensitive

# Arrays/JSON
filters = {'tags': {'_contains': ['bf25']}}

# Lógica
filters = {
    '_and': [
        {'clicks': {'_gt': 100}},
        {'tags': {'_contains': ['bf25']}}
    ]
}

filters = {
    '_or': [
        {'clicks': {'_gt': 1000}},
        {'tags': {'_contains': ['vip']}}
    ]
}
```

---

## 📊 Schema GraphQL

### Tipo Principal: `links`

```graphql
type links {
  id: String!
  domain: String!
  uniq: Int!
  name: String
  title: String
  url: String                          # URL de destino
  clicks: Int
  tags: jsonb
  createdDate: timestamptz
  
  # Configurações especiais
  linkExpiration: jsonb                # Expiração
  extraOptionsLinkRotator: jsonb       # Rotator
  extraOptionsGeolocations: jsonb      # Geo routing
  extraOptionsDeviceRotations: jsonb   # Device routing
  extraOptionsOSRotations: jsonb       # OS routing
  
  clicksLimit: jsonb
  passwordProtect: jsonb
  pixels: jsonb
  linkScripts: jsonb
  
  caseSensitive: Boolean
  masking: Boolean!
  deepLinkingEnable: Boolean
  showGDPR: Boolean
  
  folderId: Int
  description: String
  note: String
  favicon: String
  image: String
}
```

### Queries Principais

```graphql
# Listar links
query {
  links(limit: 10, where: {clicks: {_gt: 100}}) {
    id
    title
    url
    clicks
  }
}

# Buscar por ID
query {
  links_by_pk(domain: "sw.page", id: "abc123") {
    id
    url
  }
}
```

### Mutations Principais

```graphql
# Atualizar links
mutation {
  update_links(
    where: {id: {_eq: "abc123"}},
    _set: {url: "https://nova-url.com"}
  ) {
    affected_rows
  }
}

# Deletar links
mutation {
  delete_links(where: {id: {_eq: "abc123"}}) {
    affected_rows
  }
}
```

---

## 🎓 Boas Práticas

### 1. Use Variáveis de Ambiente

```python
# ❌ Ruim
api = SwitchyAPI(api_key='chave-exposta-no-codigo')

# ✅ Bom
import os
os.environ['SWITCHY_API_KEY'] = 'sua-key'
api = SwitchyAPI()
```

### 2. Trate Erros

```python
try:
    result = api.update_link_url('link_id', 'nova_url')
    if result['affected_rows'] == 0:
        print("Nenhum link atualizado")
except Exception as e:
    print(f"Erro: {e}")
```

### 3. Valide Operações em Massa

```python
# Antes de atualizar, verifique quantos serão afetados
links = api.get_links_by_tag('test')
print(f"⚠️  {len(links)} links serão atualizados")

confirmacao = input("Confirmar? (sim/não): ")
if confirmacao.lower() == 'sim':
    result = api.update_links_bulk(
        filters={'tags': {'_contains': ['test']}},
        updates={'url': 'nova_url'}
    )
```

### 4. Use Filtros Específicos

```python
# ❌ Ruim: atualizar TODOS os links
api.update_links_bulk({}, {'url': 'nova_url'})

# ✅ Bom: atualizar apenas os necessários
api.update_links_bulk(
    {'tags': {'_contains': ['test']}},
    {'url': 'nova_url'}
)
```

---

## 🐛 Troubleshooting

### Erro: "API key não fornecida"

```bash
export SWITCHY_API_KEY="sua-key-aqui"
```

### Erro: "Module 'switchy_utils' not found"

```python
import sys
sys.path.insert(0, 'src')
from switchy_utils import SwitchyAPI
```

### Erro: "affected_rows: 0"

Verifique:
- ID do link está correto
- Link existe no domínio especificado
- Filtros estão corretos

### Erro: Timeout

```python
# Aumentar timeout (padrão: 30s)
api._execute_query(query, variables, timeout=60)
```

---

## 📖 Recursos Adicionais

### Documentação Oficial
- [Switchy Developers](https://developers.switchy.io/docs/overview/index)
- [GraphQL Spec](https://spec.graphql.org/)
- [Hasura Docs](https://hasura.io/docs/)

### Ferramentas Úteis
- [GraphiQL Online](https://graphiql-online.com/) - Playground GraphQL
- [Insomnia](https://insomnia.rest/) - Cliente API

---

## ✅ Checklist

- [x] Análise do schema GraphQL
- [x] Classe `SwitchyAPI` implementada
- [x] Métodos de consulta
- [x] Métodos de atualização
- [x] Link Rotator
- [x] Link Expiration
- [x] Funções standalone (compatibilidade)
- [x] Script de exemplos interativo
- [x] Documentação completa
- [x] Pronto para produção ✨

---

## 📞 Suporte

- **Documentação Local**: Este arquivo
- **Documentação Oficial**: https://developers.switchy.io/
- **Live Chat**: Disponível no site do Switchy

---

**Status:** ✅ Pronto para Produção  
**Versão:** 1.0.0  
**Última atualização:** 01/12/2024

🎉 **Implementação completa e funcional!**

