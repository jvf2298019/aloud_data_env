# 📦 MongoDB Utils - Configuração e Uso

## ✅ Arquivos Criados

### 1. **src/mongo_utils.py**
Módulo principal com classe `MongoDBConnection` e métodos:
- `connect()` / `disconnect()`: Gerenciar conexão
- `get_collection_names()`: Listar coleções filtradas
- `get_documents_from_collection()`: Buscar documentos de uma coleção
- `get_documents_from_filtered_collections()`: **Buscar de múltiplas coleções e retorna DataFrame consolidado**
- `documents_to_dataframe()`: Converter lista de documentos para pandas DataFrame
- `get_collection_stats()`: Estatísticas das coleções
- `export_collection_to_csv()`: Exportar coleção para CSV
- `export_filtered_collections_to_csv()`: Exportar múltiplas coleções consolidadas

### 2. **examples/exemplo_mongo_disparos.py**
Script completo com 6 exemplos de uso:
- Listar coleções
- Buscar documentos
- Filtrar por status
- Exportar para CSV
- Estatísticas
- Análise completa

### 3. **examples/README_MONGO.md**
Documentação completa com todos os detalhes de uso, exemplos e troubleshooting.

---

## 🚀 Como Usar (Quick Start)

### 1. Instalar dependência
```bash
pip install pymongo
```

Ou instalar todas as dependências:
```bash
pip install -r requirements.txt
```

### 2. Configurar conexão
Criar arquivo `.env` na raiz do projeto:
```env
MONGO_URI=mongodb://localhost:27017/
```

Para MongoDB Atlas ou conexão remota:
```env
MONGO_URI=mongodb+srv://usuario:senha@cluster.mongodb.net/
```

### 3. Usar no código

```python
from src.mongo_utils import MongoDBConnection

# Conectar e buscar dados
with MongoDBConnection(database_name="disparos-api") as mongo:
    # Buscar documentos de coleções que contêm "lcto-bf25"
    # Retorna DataFrame consolidado automaticamente
    df = mongo.get_documents_from_filtered_collections(
        collection_filter="lcto-bf25"
    )
    
    # DataFrame já vem com coluna 'collection_name'
    print(f"Total de registros: {len(df)}")
    print(f"Coleções: {df['collection_name'].unique()}")
    print(df.head())
```

---

## 📝 Exemplos de Filtros

### Filtrar por status
```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    df = mongo.get_documents_from_filtered_collections(
        collection_filter="lcto-bf25",
        document_filter={"status": "EXECUTED"}
    )
    print(f"Documentos EXECUTED: {len(df)}")
```

### Selecionar apenas campos específicos
```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    df = mongo.get_documents_from_filtered_collections(
        collection_filter="lcto-bf25",
        projection={"email": 1, "phone": 1, "status": 1}
    )
    print(df.head())
```

### Limitar quantidade
```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    df = mongo.get_documents_from_filtered_collections(
        collection_filter="lcto-bf25",
        limit_per_collection=100
    )
```

### Múltiplos filtros
```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    df = mongo.get_documents_from_filtered_collections(
        collection_filter="lcto-bf25",
        document_filter={
            "status": "EXECUTED",
            "campaign_id": "lcto-bf-nov/25"
        }
    )
```

### Análise por coleção
```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    df = mongo.get_documents_from_filtered_collections(
        collection_filter="lcto-bf25"
    )
    
    # Contar documentos por coleção
    print(df['collection_name'].value_counts())
    
    # Filtrar apenas uma coleção específica
    df_col1 = df[df['collection_name'] == 'nome_da_colecao']
```

### Exportar consolidado
```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    mongo.export_filtered_collections_to_csv(
        collection_filter="lcto-bf25",
        output_dir="data/processed",
        consolidated=True
    )
```

---

## 🧪 Testar a conexão

Execute o script de exemplo:
```bash
cd examples
python exemplo_mongo_disparos.py
```

Ou teste diretamente:
```bash
cd src
python mongo_utils.py
```

---

## 🔧 Troubleshooting

### ❌ Erro: "Connection refused"
- Verifique se o MongoDB está rodando
- Teste: `mongosh "sua_connection_string"`

### ❌ Erro: "Authentication failed"
- Verifique usuário e senha no MONGO_URI
- Formato: `mongodb://usuario:senha@host:port/`

### ❌ Erro: "Database not found"
- Verifique se o nome da database está correto
- Liste databases: `show dbs` no mongosh

### ❌ Erro: "No module named 'pymongo'"
- Instale: `pip install pymongo`

---

## 📚 Documentação Completa

Para documentação completa e mais exemplos, veja:
- `examples/README_MONGO.md` - Documentação detalhada com todos os métodos
- `examples/exemplo_mongo_disparos.py` - 6 exemplos completos de uso
- `src/mongo_utils.py` - Código fonte com exemplos no final

---

## 💡 Dicas

1. **Use context manager**: Sempre que possível use `with MongoDBConnection()` para garantir que a conexão seja fechada.

2. **Filtros MongoDB**: Use a sintaxe de query do MongoDB nos filtros:
   - `{"status": "EXECUTED"}` - Igualdade
   - `{"status": {"$in": ["EXECUTED", "PENDING"]}}` - IN
   - `{"email": {"$ne": None}}` - Diferente de null
   - `{"campaign_id": {"$regex": "bf.*25"}}` - Regex

3. **Projection**: Use para selecionar apenas os campos necessários e economizar memória:
   - `{"email": 1, "phone": 1}` - Apenas esses campos
   - `{"_id": 0, "email": 1}` - Excluir _id, incluir email

4. **Limit**: Use limit quando estiver explorando ou testando para não carregar muitos dados de uma vez.

---

## 📊 Estrutura de Documento

Os documentos na database têm o seguinte formato:

```json
{
  "_id": {
    "$oid": "68f2f636fa76d87f1267b6de"
  },
  "lead_id": null,
  "campaign_id": "lcto-bf-nov/25",
  "email": "",
  "first_name": "Adejaime",
  "name": "Adejaime Junior",
  "phone": "5592981255539",
  "status": "EXECUTED",
  "updatedAt": 1760753204658,
  "chave": ""
}
```

O campo `_id` é automaticamente normalizado para string quando você usa `documents_to_dataframe()`.

