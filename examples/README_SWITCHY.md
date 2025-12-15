# 🔗 Switchy API - Guia de Integração

## 📚 Índice de Documentação

Este diretório contém toda a documentação e exemplos para trabalhar com a API Switchy.

### Documentos Principais

1. **[SWITCHY_SCHEMA_ANALYSIS.md](../SWITCHY_SCHEMA_ANALYSIS.md)**
   - 📊 Análise completa do schema GraphQL
   - Tipos de dados disponíveis
   - Queries e mutations
   - Estrutura de campos importantes
   - Exemplos de payloads
   - Tratamento de erros
   - **Leia este documento primeiro!**

2. **[SWITCHY_EXAMPLES.md](../SWITCHY_EXAMPLES.md)**
   - 🧪 Exemplos práticos executáveis
   - Scripts de teste prontos para usar
   - Casos de uso comuns
   - Atualização de links
   - Configuração de expiração
   - Link rotator
   - **Use este documento para testar!**

3. **[src/switchy_utils.py](../src/switchy_utils.py)** *(em desenvolvimento)*
   - 🛠️ Biblioteca Python utilitária
   - Funções prontas para usar
   - Integração simplificada
   - **Use este módulo em seus projetos!**

---

## 🚀 Quick Start

### 1. Credenciais

```python
ENDPOINT = 'https://graphql.switchy.io/v1/graphql'
API_KEY = '735c8051-ef80-4287-bd17-06d7176ad956'

HEADERS = {
    'Api-Authorization': API_KEY,
    'Content-Type': 'application/json'
}
```

### 2. Teste de Conexão

```python
import requests

query = '''
query {
  links(limit: 1) {
    id
    name
  }
}
'''

response = requests.post(
    'https://graphql.switchy.io/v1/graphql',
    json={'query': query},
    headers={
        'Api-Authorization': '735c8051-ef80-4287-bd17-06d7176ad956',
        'Content-Type': 'application/json'
    }
)

print(response.json())
```

---

## 🎯 Objetivos do Projeto

### 1. Consultar Links
- Listar todos os links
- Buscar link específico por ID
- Filtrar por tags, cliques, data, etc.
- Obter estatísticas

### 2. Alterar Apontamento
- Atualizar URL de destino
- Modificar múltiplos links de uma vez
- Atualização condicional por filtros

### 3. Configurar Links
- **Link Expiration**: Definir data de expiração
- **Link Rotator**: Rotacionar entre múltiplas URLs
- **Geolocation Routing**: Redirecionar por país
- **Device Routing**: Redirecionar por tipo de dispositivo
- **Click Limits**: Limitar número de cliques

---

## 🔑 Principais Operações

### Listar Links
```graphql
query {
  links(limit: 10, order_by: {createdDate: desc}) {
    id
    name
    url
    clicks
  }
}
```

### Atualizar URL
```graphql
mutation {
  update_links(
    where: {id: {_eq: "abc123"}},
    _set: {url: "https://nova-url.com"}
  ) {
    affected_rows
  }
}
```

### Configurar Expiração
```graphql
mutation {
  update_links(
    where: {id: {_eq: "abc123"}},
    _set: {
      linkExpiration: {
        enabled: true,
        type: "date",
        date: "2025-12-31T23:59:59Z",
        redirectUrl: "https://expirado.com"
      }
    }
  ) {
    affected_rows
  }
}
```

### Configurar Link Rotator
```graphql
mutation {
  update_links(
    where: {id: {_eq: "abc123"}},
    _set: {
      extraOptionsLinkRotator: {
        enabled: true,
        type: "weighted",
        urls: [
          {url: "https://url1.com", weight: 70},
          {url: "https://url2.com", weight: 30}
        ]
      }
    }
  ) {
    affected_rows
  }
}
```

---

## 🏗️ Estrutura de Tipos Importantes

### Link (tipo principal)
```json
{
  "id": "string",
  "domain": "string",
  "uniq": "number",
  "name": "string",
  "url": "string",
  "clicks": "number",
  "tags": ["array"],
  "linkExpiration": "jsonb",
  "extraOptionsLinkRotator": "jsonb",
  "extraOptionsGeolocations": "jsonb",
  "clicksLimit": "jsonb",
  "passwordProtect": "jsonb"
}
```

### Link Expiration
```json
{
  "enabled": true,
  "type": "date" | "clicks",
  "date": "2025-12-31T23:59:59Z",
  "clicks": 1000,
  "redirectUrl": "https://expired.com"
}
```

### Link Rotator
```json
{
  "enabled": true,
  "type": "random" | "sequential" | "weighted",
  "urls": [
    {
      "url": "https://url1.com",
      "weight": 50
    }
  ]
}
```

---

## 📖 Recursos

### Documentação Oficial
- [Documentação Switchy](https://developers.switchy.io/docs/overview/index)
- [GraphQL Spec](https://spec.graphql.org/)
- [Hasura Docs](https://hasura.io/docs/)

### Ferramentas Úteis
- [GraphiQL Online](https://graphiql-online.com/) - Playground GraphQL
- [Apollo Studio](https://studio.apollographql.com/) - Cliente GraphQL
- [Insomnia](https://insomnia.rest/) - Cliente API

---

## 🔍 Como Usar Este Guia

1. **Iniciante?**
   - Comece com o [SWITCHY_SCHEMA_ANALYSIS.md](../SWITCHY_SCHEMA_ANALYSIS.md)
   - Execute os exemplos do [SWITCHY_EXAMPLES.md](../SWITCHY_EXAMPLES.md)
   - Use as funções do `switchy_utils.py`

2. **Desenvolvedor?**
   - Consulte o schema para entender os tipos
   - Adapte os exemplos para seu caso de uso
   - Contribua com novos exemplos

3. **Integração em Produção?**
   - Use o `switchy_utils.py` para abstração
   - Implemente retry logic e tratamento de erros
   - Configure rate limiting apropriado

---

## ⚠️ Avisos Importantes

1. **Rate Limiting**: A API tem limites de requisições
2. **Autenticação**: Mantenha sua API key segura
3. **Testes**: Use links de teste antes de modificar produção
4. **Backup**: Documente valores originais antes de alterações
5. **Validação**: Sempre verifique `affected_rows` em mutations

---

## 🤝 Contribuindo

Encontrou algo útil? Adicione aos documentos!

1. Exemplos práticos → `SWITCHY_EXAMPLES.md`
2. Análise de schema → `SWITCHY_SCHEMA_ANALYSIS.md`
3. Funções utilitárias → `src/switchy_utils.py`

---

## 📊 Status do Projeto

- ✅ Análise do schema completa
- ✅ Documentação detalhada criada
- ✅ Exemplos práticos desenvolvidos
- 🚧 Biblioteca `switchy_utils.py` em desenvolvimento
- 🚧 Testes automatizados pendentes
- 🚧 Integração com pipeline de dados pendente

---

## 📞 Suporte

- **Live Chat**: Disponível no site e app do Switchy
- **Documentação**: https://developers.switchy.io/
- **Email**: Contactar via chat primeiro

---

**Última atualização:** 01/12/2024  
**Versão:** 1.0  
**Autor:** Análise via introspection query
















