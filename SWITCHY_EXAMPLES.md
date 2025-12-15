# 🧪 Switchy API - Exemplos Práticos de Teste

Este documento contém exemplos práticos que você pode executar para testar as funcionalidades da API Switchy.

---

## 🔧 Setup Inicial

```python
import requests
import json
from datetime import datetime, timedelta

# Configuração
ENDPOINT = 'https://graphql.switchy.io/v1/graphql'
API_KEY = '735c8051-ef80-4287-bd17-06d7176ad956'

HEADERS = {
    'Api-Authorization': API_KEY,
    'Content-Type': 'application/json'
}

def execute_query(query, variables=None):
    """Executa uma query GraphQL"""
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    
    response = requests.post(ENDPOINT, json=payload, headers=HEADERS)
    result = response.json()
    
    if 'errors' in result:
        print("❌ Erro:", json.dumps(result['errors'], indent=2))
        return None
    
    return result['data']
```

---

## 📊 Teste 1: Listar Todos os Links

### Objetivo
Obter uma lista de todos os links da conta.

### Query
```python
query = '''
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
    linkExpiration
    extraOptionsLinkRotator
  }
}
'''

data = execute_query(query)

if data:
    print(f"✅ Total de links retornados: {len(data['links'])}")
    for link in data['links']:
        print(f"\n📎 {link['name'] or 'Sem nome'}")
        print(f"   ID: {link['id']}")
        print(f"   Domain: {link['domain']}")
        print(f"   Uniq: {link['uniq']}")
        print(f"   URL: {link['url']}")
        print(f"   Clicks: {link['clicks']}")
        print(f"   Tags: {link['tags']}")
```

### Resultado Esperado
```
✅ Total de links retornados: 10
📎 Link Campanha BF25
   ID: abc123
   Domain: sw.page
   Uniq: 12345
   URL: https://destino.com
   Clicks: 150
   Tags: ["bf25", "promo"]
```

---

## 🔍 Teste 2: Buscar Link Específico por ID

### Objetivo
Buscar detalhes completos de um link específico.

### Query
```python
# Primeiro, pegue um ID real dos seus links
query_list = '''
query {
  links(limit: 1) {
    id
    domain
  }
}
'''

result = execute_query(query_list)
if result and result['links']:
    link_id = result['links'][0]['id']
    link_domain = result['links'][0]['domain']
    
    print(f"🔎 Buscando link: ID={link_id}, Domain={link_domain}")
    
    # Agora buscar o link completo
    query_detail = '''
    query BuscarLink($domain: String!, $id: String!) {
      links_by_pk(domain: $domain, id: $id) {
        id
        domain
        uniq
        name
        url
        description
        clicks
        createdDate
        caseSensitive
        folderId
        tags
        linkExpiration
        extraOptionsLinkRotator
        extraOptionsGeolocations
        clicksLimit
        passwordProtect
        pixels
        masking
        deepLinkingEnable
        showGDPR
      }
    }
    '''
    
    variables = {
        "domain": link_domain,
        "id": link_id
    }
    
    detail = execute_query(query_detail, variables)
    if detail:
        print("\n✅ Link encontrado:")
        print(json.dumps(detail['links_by_pk'], indent=2))
```

---

## 🏷️ Teste 3: Filtrar Links por Tags

### Objetivo
Buscar todos os links com uma tag específica.

### Query
```python
query = '''
query FiltrarPorTag($tag: jsonb!) {
  links(
    where: {tags: {_contains: $tag}},
    order_by: {createdDate: desc}
  ) {
    id
    name
    url
    tags
    clicks
  }
}
'''

variables = {
    "tag": ["bf25"]  # Substitua pela tag que você usa
}

data = execute_query(query, variables)

if data:
    print(f"✅ Links com tag 'bf25': {len(data['links'])}")
    for link in data['links']:
        print(f"  • {link['name']}: {link['clicks']} clicks")
```

---

## 📈 Teste 4: Links Mais Clicados

### Objetivo
Obter os 10 links com mais cliques.

### Query
```python
query = '''
query TopLinks {
  links(
    limit: 10,
    order_by: {clicks: desc},
    where: {clicks: {_gt: 0}}
  ) {
    id
    name
    url
    clicks
    domain
    uniq
  }
}
'''

data = execute_query(query)

if data:
    print("🏆 Top 10 Links Mais Clicados:\n")
    for i, link in enumerate(data['links'], 1):
        short_url = f"https://{link['domain']}/{link['uniq']}"
        print(f"{i:2d}. {link['name'] or 'Sem nome':40s} | {link['clicks']:5d} clicks | {short_url}")
```

---

## ✏️ Teste 5: Atualizar URL de Destino

### Objetivo
Alterar o apontamento de um link existente.

### Mutation
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
      name
      url
    }
  }
}
'''

# ⚠️ ATENÇÃO: Substitua pelo ID real de um link seu!
variables = {
    "linkId": "SEU_LINK_ID_AQUI",
    "novaUrl": "https://nova-url-de-destino.com"
}

print("⚠️  Você está prestes a atualizar um link!")
print(f"   Link ID: {variables['linkId']}")
print(f"   Nova URL: {variables['novaUrl']}")

confirmacao = input("\nConfirmar? (sim/não): ")

if confirmacao.lower() == 'sim':
    data = execute_query(mutation, variables)
    
    if data and data['update_links']['affected_rows'] > 0:
        print(f"\n✅ Link atualizado com sucesso!")
        print(f"   Linhas afetadas: {data['update_links']['affected_rows']}")
        for link in data['update_links']['returning']:
            print(f"   Nova URL: {link['url']}")
    else:
        print("\n⚠️ Nenhum link foi atualizado. Verifique o ID.")
else:
    print("❌ Operação cancelada.")
```

---

## ⏰ Teste 6: Configurar Expiração de Link

### Objetivo
Configurar um link para expirar em uma data específica.

### Mutation
```python
mutation = '''
mutation ConfigurarExpiracao($linkId: String!, $expiration: jsonb!) {
  update_links(
    where: {id: {_eq: $linkId}},
    _set: {linkExpiration: $expiration}
  ) {
    affected_rows
    returning {
      id
      name
      linkExpiration
    }
  }
}
'''

# Configurar expiração para 30 dias a partir de hoje
expiration_date = (datetime.now() + timedelta(days=30)).isoformat()

variables = {
    "linkId": "SEU_LINK_ID_AQUI",
    "expiration": {
        "enabled": True,
        "type": "date",
        "date": expiration_date,
        "redirectUrl": "https://link-expirado.com"
    }
}

print("⏰ Configurando expiração do link:")
print(f"   Data de expiração: {expiration_date}")
print(f"   URL de redirecionamento: https://link-expirado.com")

confirmacao = input("\nConfirmar? (sim/não): ")

if confirmacao.lower() == 'sim':
    data = execute_query(mutation, variables)
    
    if data and data['update_links']['affected_rows'] > 0:
        print("\n✅ Expiração configurada com sucesso!")
        for link in data['update_links']['returning']:
            print(f"   Link: {link['name']}")
            print(f"   Configuração: {json.dumps(link['linkExpiration'], indent=2)}")
    else:
        print("\n⚠️ Falha ao configurar expiração.")
else:
    print("❌ Operação cancelada.")
```

---

## 🔄 Teste 7: Configurar Link Rotator

### Objetivo
Configurar um link para rotacionar entre múltiplas URLs de destino.

### Mutation
```python
mutation = '''
mutation ConfigurarRotator($linkId: String!, $rotator: jsonb!) {
  update_links(
    where: {id: {_eq: $linkId}},
    _set: {extraOptionsLinkRotator: $rotator}
  ) {
    affected_rows
    returning {
      id
      name
      extraOptionsLinkRotator
    }
  }
}
'''

variables = {
    "linkId": "SEU_LINK_ID_AQUI",
    "rotator": {
        "enabled": True,
        "type": "weighted",  # Pode ser: "random", "sequential", "weighted"
        "urls": [
            {
                "url": "https://destino1.com",
                "weight": 70  # 70% do tráfego
            },
            {
                "url": "https://destino2.com",
                "weight": 30  # 30% do tráfego
            }
        ]
    }
}

print("🔄 Configurando Link Rotator:")
print(f"   Tipo: {variables['rotator']['type']}")
print(f"   URLs:")
for url_config in variables['rotator']['urls']:
    print(f"     - {url_config['url']} (weight: {url_config['weight']})")

confirmacao = input("\nConfirmar? (sim/não): ")

if confirmacao.lower() == 'sim':
    data = execute_query(mutation, variables)
    
    if data and data['update_links']['affected_rows'] > 0:
        print("\n✅ Link Rotator configurado com sucesso!")
        for link in data['update_links']['returning']:
            print(f"   Link: {link['name']}")
            print(f"   Configuração: {json.dumps(link['extraOptionsLinkRotator'], indent=2)}")
    else:
        print("\n⚠️ Falha ao configurar rotator.")
else:
    print("❌ Operação cancelada.")
```

---

## 🔄 Teste 8: Atualização em Massa

### Objetivo
Atualizar múltiplos links de uma só vez (ex: todos com uma tag específica).

### Mutation
```python
mutation = '''
mutation AtualizarEmMassa($tag: jsonb!, $novaUrl: String!) {
  update_links(
    where: {tags: {_contains: $tag}},
    _set: {url: $novaUrl}
  ) {
    affected_rows
    returning {
      id
      name
      url
      tags
    }
  }
}
'''

variables = {
    "tag": ["test"],  # Tag dos links a atualizar
    "novaUrl": "https://nova-oferta-geral.com"
}

print("⚠️  ATENÇÃO: Atualização em massa!")
print(f"   Tag: {variables['tag']}")
print(f"   Nova URL: {variables['novaUrl']}")
print("\n   Isso irá atualizar TODOS os links com essa tag!")

confirmacao = input("\nConfirmar? (SIM em maiúsculas): ")

if confirmacao == 'SIM':
    data = execute_query(mutation, variables)
    
    if data:
        affected = data['update_links']['affected_rows']
        print(f"\n✅ {affected} link(s) atualizado(s)!")
        
        if affected > 0:
            print("\nLinks atualizados:")
            for link in data['update_links']['returning']:
                print(f"  • {link['name']}: {link['url']}")
    else:
        print("\n⚠️ Falha na atualização em massa.")
else:
    print("❌ Operação cancelada.")
```

---

## 📊 Teste 9: Estatísticas Gerais

### Objetivo
Obter estatísticas gerais da conta.

### Query
```python
query = '''
query Estatisticas {
  links {
    clicks
  }
}
'''

data = execute_query(query)

if data:
    total_links = len(data['links'])
    total_clicks = sum(link['clicks'] or 0 for link in data['links'])
    avg_clicks = total_clicks / total_links if total_links > 0 else 0
    
    print("📊 ESTATÍSTICAS DA CONTA")
    print("=" * 50)
    print(f"Total de links: {total_links}")
    print(f"Total de cliques: {total_clicks:,}")
    print(f"Média de cliques por link: {avg_clicks:.2f}")
    
    # Links sem cliques
    zero_clicks = sum(1 for link in data['links'] if link['clicks'] == 0)
    print(f"Links sem cliques: {zero_clicks} ({zero_clicks/total_links*100:.1f}%)")
```

---

## 🗂️ Teste 10: Listar Domínios e Pastas

### Objetivo
Ver todos os domínios e pastas disponíveis na conta.

### Query
```python
query = '''
query DominiosEPastas {
  domains {
    name
    ownerId
  }
  folders {
    id
    name
    description
  }
}
'''

data = execute_query(query)

if data:
    print("🌐 DOMÍNIOS:")
    for domain in data['domains']:
        print(f"  • {domain['name']}")
    
    print("\n📁 PASTAS:")
    for folder in data['folders']:
        desc = f" - {folder['description']}" if folder['description'] else ""
        print(f"  • {folder['name']} (ID: {folder['id']}){desc}")
```

---

## 🧪 Script de Teste Completo

```python
#!/usr/bin/env python3
"""
Script completo de teste da API Switchy
Execute: python test_switchy_api.py
"""

import requests
import json
from datetime import datetime

ENDPOINT = 'https://graphql.switchy.io/v1/graphql'
API_KEY = '735c8051-ef80-4287-bd17-06d7176ad956'

HEADERS = {
    'Api-Authorization': API_KEY,
    'Content-Type': 'application/json'
}

def execute_query(query, variables=None):
    """Executa uma query GraphQL"""
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    
    try:
        response = requests.post(ENDPOINT, json=payload, headers=HEADERS, timeout=30)
        result = response.json()
        
        if 'errors' in result:
            print("❌ Erro:", json.dumps(result['errors'], indent=2))
            return None
        
        return result['data']
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return None

def test_connection():
    """Teste 1: Testar conexão básica"""
    print("\n" + "="*60)
    print("Teste 1: Conexão com API")
    print("="*60)
    
    query = '''
    query {
      links(limit: 1) {
        id
        name
      }
    }
    '''
    
    data = execute_query(query)
    if data:
        print("✅ Conexão OK!")
        return True
    else:
        print("❌ Falha na conexão!")
        return False

def test_list_links():
    """Teste 2: Listar links"""
    print("\n" + "="*60)
    print("Teste 2: Listar Links")
    print("="*60)
    
    query = '''
    query {
      links(limit: 5, order_by: {createdDate: desc}) {
        id
        name
        url
        clicks
        tags
      }
    }
    '''
    
    data = execute_query(query)
    if data:
        print(f"✅ {len(data['links'])} links retornados")
        for link in data['links']:
            print(f"  • {link['name'] or 'Sem nome'}: {link['clicks']} clicks")
        return True
    return False

def test_statistics():
    """Teste 3: Estatísticas"""
    print("\n" + "="*60)
    print("Teste 3: Estatísticas")
    print("="*60)
    
    query = '''
    query {
      links {
        clicks
      }
    }
    '''
    
    data = execute_query(query)
    if data:
        total = len(data['links'])
        clicks = sum(l['clicks'] or 0 for l in data['links'])
        print(f"✅ Total de links: {total}")
        print(f"✅ Total de cliques: {clicks:,}")
        return True
    return False

def main():
    print("\n🧪 INICIANDO TESTES DA API SWITCHY")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        test_connection,
        test_list_links,
        test_statistics
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "="*60)
    print(f"RESULTADO: {passed}/{len(tests)} testes passaram")
    print("="*60)

if __name__ == '__main__':
    main()
```

---

## 🚨 Avisos Importantes

1. **Cuidado com Atualizações em Massa**: Sempre use filtros específicos e verifique antes de executar
2. **Backup**: Anote os valores originais antes de fazer mudanças
3. **Rate Limiting**: A API pode ter limites de requisições. Respeite os limites
4. **Testes**: Use tags específicas como "test" ou "dev" para testar operações
5. **Validação**: Sempre valide se `affected_rows > 0` após mutations

---

## 📝 Próximos Passos

1. Execute os testes básicos para validar conectividade
2. Identifique um link de teste para experimentos
3. Teste cada funcionalidade individualmente
4. Implemente o utilitário `switchy_utils.py` baseado nesses exemplos

---

**Última atualização:** 01/12/2024
















