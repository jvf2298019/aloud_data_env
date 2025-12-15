# 📊 Análise do Schema GraphQL - Switchy API

> **Documentação Oficial:** https://developers.switchy.io/docs/overview/index  
> **Endpoint:** https://graphql.switchy.io/v1/graphql  
> **Tipo de API:** GraphQL (queries) + REST (algumas mutations)

---

## 🎯 Objetivos do Projeto

1. **Consultar links** - Buscar e filtrar links
2. **Alterar apontamento** - Modificar URL de destino dos links
3. **Configurar links** - Setar `linkExpiration`, `extraOptionsLinkRotator`, etc.

---

## 📋 Visão Geral do Schema

### Tipos Principais
- **91 tipos** no total
- **17 queries** disponíveis
- **2 mutations** disponíveis
- Tipos principais: `links`, `domains`, `folders`, `workspaces`, `pixels`, `UTMTemplates`

### Estrutura Hasura/GraphQL
O Switchy usa **Hasura**, que gera automaticamente:
- Queries com filtros avançados (`_bool_exp`)
- Paginação (`limit`, `offset`)
- Ordenação (`order_by`)
- Campos relacionados (relationships)

---

## 🔗 Tipo Principal: `links`

### Campos Importantes

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | String! | ID único do link |
| `domain` | String! | Domínio usado |
| `uniq` | Int! | Código único do link |
| `url` | String | **URL de destino** (onde o link aponta) |
| `name` | String | Nome/título do link |
| `description` | String | Descrição |
| `caseSensitive` | Boolean | Se diferencia maiúsculas/minúsculas |
| `clicks` | Int | Total de cliques |
| `createdDate` | timestamptz | Data de criação |
| `folderId` | Int | ID da pasta |
| `tags` | jsonb | Tags do link |
| `linkExpiration` | jsonb | **Configuração de expiração** |
| `extraOptionsLinkRotator` | jsonb | **Configuração de rotação de links** |
| `extraOptionsGeolocations` | jsonb | Redirecionamento por geolocalização |
| `extraOptionsDeviceRotations` | jsonb | Redirecionamento por dispositivo |
| `extraOptionsOSRotations` | jsonb | Redirecionamento por sistema operacional |
| `clicksLimit` | jsonb | Limite de cliques |
| `passwordProtect` | jsonb | Proteção por senha |
| `pixels` | jsonb | Pixels de tracking |
| `linkScripts` | jsonb | Scripts customizados |
| `masking` | Boolean! | Se usa mascaramento de URL |
| `deepLinkingEnable` | Boolean | Deep linking habilitado |
| `showGDPR` | Boolean | Mostra aviso GDPR |

---

## 📊 QUERIES DISPONÍVEIS

### 1. Listar Links

**Query básica:**
```graphql
query ListarLinks {
  links(limit: 10, order_by: {createdDate: desc}) {
    id
    domain
    uniq
    name
    url
    clicks
    createdDate
    tags
  }
}
```

**Resposta esperada:**
```json
{
  "data": {
    "links": [
      {
        "id": "abc123",
        "domain": "sw.page",
        "uniq": 12345,
        "name": "Link Exemplo",
        "url": "https://destino.com",
        "clicks": 150,
        "createdDate": "2024-12-01T10:00:00",
        "tags": ["bf25", "promo"]
      }
    ]
  }
}
```

### 2. Buscar Link por ID

```graphql
query BuscarLinkPorId {
  links_by_pk(domain: "sw.page", id: "abc123") {
    id
    domain
    uniq
    name
    url
    linkExpiration
    extraOptionsLinkRotator
    clicks
  }
}
```

### 3. Filtrar Links (com condições)

```graphql
query FiltrarLinks {
  links(
    where: {
      _and: [
        {tags: {_contains: ["bf25"]}},
        {clicks: {_gt: 100}},
        {url: {_ilike: "%destino%"}}
      ]
    },
    limit: 20,
    order_by: {clicks: desc}
  ) {
    id
    name
    url
    clicks
    tags
  }
}
```

**Operadores de filtro disponíveis:**
- `_eq` - igual
- `_neq` - diferente
- `_gt` - maior que
- `_gte` - maior ou igual
- `_lt` - menor que
- `_lte` - menor ou igual
- `_like` - like (case sensitive)
- `_ilike` - like (case insensitive)
- `_is_null` - é nulo
- `_contains` - contém (para jsonb/arrays)
- `_and`, `_or`, `_not` - operadores lógicos

### 4. Listar Links com Paginação

```graphql
query ListarLinksPaginado($offset: Int!, $limit: Int!) {
  links(
    offset: $offset,
    limit: $limit,
    order_by: {createdDate: desc}
  ) {
    id
    name
    url
    clicks
  }
}
```

**Variables:**
```json
{
  "offset": 0,
  "limit": 50
}
```

---

## ✏️ MUTATIONS DISPONÍVEIS

### 1. Atualizar Links (update_links)

**Atualizar URL de destino:**
```graphql
mutation AtualizarURL {
  update_links(
    where: {id: {_eq: "abc123"}},
    _set: {
      url: "https://novo-destino.com"
    }
  ) {
    affected_rows
    returning {
      id
      name
      url
    }
  }
}
```

### 2. Configurar Link Expiration

```graphql
mutation ConfigurarExpiracao {
  update_links(
    where: {id: {_eq: "abc123"}},
    _set: {
      linkExpiration: {
        enabled: true,
        type: "date",
        date: "2025-12-31T23:59:59Z",
        redirectUrl: "https://link-expirado.com"
      }
    }
  ) {
    affected_rows
    returning {
      id
      linkExpiration
    }
  }
}
```

**Estrutura do `linkExpiration`:**
```json
{
  "enabled": true,
  "type": "date" | "clicks",
  "date": "2025-12-31T23:59:59Z",  // se type = "date"
  "clicks": 1000,                   // se type = "clicks"
  "redirectUrl": "https://expired.com"
}
```

### 3. Configurar Link Rotator

```graphql
mutation ConfigurarRotator {
  update_links(
    where: {id: {_eq: "abc123"}},
    _set: {
      extraOptionsLinkRotator: {
        enabled: true,
        type: "sequential",
        urls: [
          {
            url: "https://destino1.com",
            weight: 50
          },
          {
            url: "https://destino2.com",
            weight: 50
          }
        ]
      }
    }
  ) {
    affected_rows
    returning {
      id
      extraOptionsLinkRotator
    }
  }
}
```

**Estrutura do `extraOptionsLinkRotator`:**
```json
{
  "enabled": true,
  "type": "random" | "sequential" | "weighted",
  "urls": [
    {
      "url": "https://url1.com",
      "weight": 50  // para tipo "weighted"
    },
    {
      "url": "https://url2.com",
      "weight": 50
    }
  ]
}
```

### 4. Atualizar Múltiplos Campos

```graphql
mutation AtualizarMultiplosCampos {
  update_links(
    where: {domain: {_eq: "sw.page"}, tags: {_contains: ["bf25"]}},
    _set: {
      url: "https://nova-oferta.com",
      name: "Nova Oferta BF25",
      description: "Link atualizado para campanha",
      linkExpiration: {
        enabled: true,
        type: "date",
        date: "2025-12-31T23:59:59Z"
      }
    }
  ) {
    affected_rows
    returning {
      id
      name
      url
      linkExpiration
    }
  }
}
```

### 5. Deletar Links

```graphql
mutation DeletarLinks {
  delete_links(
    where: {id: {_eq: "abc123"}}
  ) {
    affected_rows
    returning {
      id
      name
    }
  }
}
```

---

## 🔧 Exemplos Práticos Python

### Exemplo 1: Consultar Links

```python
import requests

endpoint = 'https://graphql.switchy.io/v1/graphql'
headers = {
    'Api-Authorization': 'sua-api-key-aqui',
    'Content-Type': 'application/json'
}

query = '''
query {
  links(limit: 10, order_by: {createdDate: desc}) {
    id
    domain
    name
    url
    clicks
  }
}
'''

response = requests.post(endpoint, json={'query': query}, headers=headers)
data = response.json()

for link in data['data']['links']:
    print(f"{link['name']}: {link['url']} ({link['clicks']} clicks)")
```

### Exemplo 2: Atualizar URL

```python
mutation = '''
mutation AtualizarURL($linkId: String!, $novaUrl: String!) {
  update_links(
    where: {id: {_eq: $linkId}},
    _set: {url: $novaUrl}
  ) {
    affected_rows
    returning {
      id
      url
    }
  }
}
'''

variables = {
    "linkId": "abc123",
    "novaUrl": "https://novo-destino.com"
}

response = requests.post(
    endpoint,
    json={'query': mutation, 'variables': variables},
    headers=headers
)
```

### Exemplo 3: Configurar Expiração

```python
mutation = '''
mutation ConfigurarExpiracao($linkId: String!, $expiration: jsonb!) {
  update_links(
    where: {id: {_eq: $linkId}},
    _set: {linkExpiration: $expiration}
  ) {
    affected_rows
  }
}
'''

variables = {
    "linkId": "abc123",
    "expiration": {
        "enabled": True,
        "type": "date",
        "date": "2025-12-31T23:59:59Z",
        "redirectUrl": "https://expirado.com"
    }
}

response = requests.post(
    endpoint,
    json={'query': mutation, 'variables': variables},
    headers=headers
)
```

---

## 🚨 Tratamento de Erros

### Estrutura de Resposta com Erro

```json
{
  "errors": [
    {
      "message": "field 'id' not found in type: 'links_bool_exp'",
      "extensions": {
        "path": "$.selectionSet.update_links.args.where",
        "code": "validation-failed"
      }
    }
  ]
}
```

### Erros Comuns

1. **Autenticação inválida:**
```json
{
  "errors": [{
    "message": "Could not verify JWT: JWTExpired",
    "extensions": {"code": "invalid-jwt"}
  }]
}
```

2. **Campo não existe:**
```json
{
  "errors": [{
    "message": "field 'campo_invalido' not found in type: 'links'",
    "extensions": {"code": "validation-failed"}
  }]
}
```

3. **Permissão negada:**
```json
{
  "errors": [{
    "message": "check constraint of an insert/update permission has failed",
    "extensions": {"code": "permission-error"}
  }]
}
```

---

## 📚 Outros Tipos Úteis

### Domains
```graphql
query ListarDominios {
  domains {
    name
    ownerId
    verified
    active
  }
}
```

### Folders
```graphql
query ListarPastas {
  folders {
    id
    name
    description
  }
}
```

### Workspaces
```graphql
query ListarWorkspaces {
  workspaces {
    id
    name
    uid
  }
}
```

---

## 🎓 Boas Práticas

### 1. Sempre use variáveis para valores dinâmicos
❌ **Ruim:**
```graphql
mutation {
  update_links(where: {id: {_eq: "abc123"}}, _set: {url: "https://novo.com"})
}
```

✅ **Bom:**
```graphql
mutation AtualizarLink($id: String!, $url: String!) {
  update_links(where: {id: {_eq: $id}}, _set: {url: $url})
}
```

### 2. Selecione apenas os campos necessários
❌ **Ruim:**
```graphql
query {
  links {
    id domain uniq name url clicks createdDate tags linkExpiration
    extraOptionsLinkRotator extraOptionsGeolocations ...
  }
}
```

✅ **Bom:**
```graphql
query {
  links {
    id
    name
    url
  }
}
```

### 3. Use paginação para grandes volumes
```graphql
query ListarLinks($limit: Int = 50, $offset: Int = 0) {
  links(limit: $limit, offset: $offset, order_by: {createdDate: desc}) {
    id
    name
    url
  }
}
```

### 4. Verifique `affected_rows` nas mutations
```python
result = response.json()
if result['data']['update_links']['affected_rows'] == 0:
    print("Nenhum link foi atualizado!")
```

---

## 🔄 Próximos Passos

1. ✅ Análise do schema concluída
2. 🚧 Criar `src/switchy_utils.py` com funções utilitárias
3. 🚧 Criar exemplos práticos em `examples/exemplo_switchy.py`
4. 🚧 Criar testes básicos
5. 🚧 Documentar casos de uso específicos

---

## 📖 Referências

- [Documentação Oficial Switchy](https://developers.switchy.io/docs/overview/index)
- [GraphQL Spec](https://spec.graphql.org/)
- [Hasura Queries](https://hasura.io/docs/latest/queries/index/)
- [Hasura Mutations](https://hasura.io/docs/latest/mutations/index/)

---

**Documento gerado automaticamente via introspection query**  
**Data:** 01/12/2024  
**Schema version:** v1
















