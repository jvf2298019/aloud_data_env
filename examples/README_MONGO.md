# MongoDB Utils - Guia de Uso

## Configuração Inicial

### 1. Instalar dependências

```bash
pip install pymongo python-dotenv
```

Ou instalar todas as dependências do projeto:

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com suas credenciais:

```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DATABASE=disparos-api
```

Para MongoDB Atlas ou outras conexões remotas:

```env
MONGO_URI=mongodb+srv://usuario:senha@cluster.mongodb.net/
MONGO_DATABASE=disparos-api
```

## Uso Básico

### Importar o módulo

```python
from src.mongo_utils import MongoDBConnection
import pandas as pd
```

### Exemplo 1: Conectar e listar coleções

```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    # Listar todas as coleções que contêm "lcto-bf25"
    collections = mongo.get_collection_names(filter_text="lcto-bf25")
    print(collections)
```

### Exemplo 2: Buscar documentos de coleções filtradas

```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    # Buscar todos os documentos de coleções que contêm "lcto-bf25"
    # Retorna DataFrame consolidado automaticamente
    df = mongo.get_documents_from_filtered_collections(
        collection_filter="lcto-bf25"
    )
    
    # DataFrame já vem consolidado com coluna 'collection_name'
    print(f"Total de registros: {len(df)}")
    print(f"Coleções: {df['collection_name'].unique()}")
    print(df.head())
```

### Exemplo 3: Filtrar documentos por campo

```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    # Buscar apenas documentos com status EXECUTED
    results = mongo.get_documents_from_filtered_collections(
        collection_filter="lcto-bf25",
        document_filter={"status": "EXECUTED"}
    )
```

### Exemplo 4: Selecionar apenas campos específicos

```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    # Buscar apenas email, phone e status
    results = mongo.get_documents_from_filtered_collections(
        collection_filter="lcto-bf25",
        projection={"email": 1, "phone": 1, "status": 1}
    )
```

### Exemplo 5: Limitar quantidade de documentos

```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    # Limitar a 100 documentos por coleção
    results = mongo.get_documents_from_filtered_collections(
        collection_filter="lcto-bf25",
        limit_per_collection=100
    )
```

### Exemplo 6: Exportar para CSV

```python
with MongoDBConnection(database_name="disparos-api") as mongo:
    # Exportar uma coleção específica
    mongo.export_collection_to_csv(
        collection_name="minha_colecao",
        output_path="data/raw/minha_colecao.csv",
        filter_query={"status": "EXECUTED"},
        limit=1000
    )
    
    # Ou exportar múltiplas coleções filtradas (consolidado)
    mongo.export_filtered_collections_to_csv(
        collection_filter="lcto-bf25",
        output_dir="data/processed",
        consolidated=True
    )
```

## Métodos Disponíveis

### `MongoDBConnection`
Classe para gerenciar conexão com MongoDB usando context manager.

**Inicialização:**
```python
mongo = MongoDBConnection(
    connection_string="mongodb://localhost:27017/",  # opcional, usa MONGO_URI do .env
    database_name="disparos-api"
)
```

### `mongo.connect()`
Estabelece conexão com o MongoDB.

**Retorna:** Database object

### `mongo.disconnect()`
Fecha a conexão com o MongoDB.

### `mongo.get_collection_names(filter_text=None)`
Lista coleções da database, opcionalmente filtrando por nome.

**Parâmetros:**
- `filter_text`: Texto para filtrar (case insensitive)

**Retorna:** Lista de nomes de coleções

### `mongo.get_documents_from_collection(collection_name, filter_query=None, limit=None, projection=None)`
Busca documentos de uma coleção específica.

**Parâmetros:**
- `collection_name`: Nome da coleção
- `filter_query`: Filtro MongoDB (ex: `{"status": "EXECUTED"}`)
- `limit`: Número máximo de documentos
- `projection`: Campos a incluir/excluir

**Retorna:** Lista de documentos

### `mongo.get_documents_from_filtered_collections(collection_filter, document_filter=None, limit_per_collection=None, projection=None, normalize_id=True)`
Busca documentos de múltiplas coleções filtradas por nome e retorna DataFrame consolidado.

**Parâmetros:**
- `collection_filter`: Texto para filtrar nomes de coleções
- `document_filter`: Filtro MongoDB para documentos (ex: `{"status": "EXECUTED"}`)
- `limit_per_collection`: Limite de documentos por coleção
- `projection`: Campos a incluir/excluir (ex: `{"email": 1, "phone": 1}`)
- `normalize_id`: Se True, converte `_id.$oid` para `_id`

**Retorna:** DataFrame pandas consolidado com todos os documentos e coluna obrigatória `collection_name`

### `mongo.documents_to_dataframe(documents, normalize_id=True)` (método estático)
Converte lista de documentos para DataFrame pandas.

**Parâmetros:**
- `documents`: Lista de documentos MongoDB
- `normalize_id`: Se True, converte `_id.$oid` para `_id`

**Retorna:** DataFrame pandas

### `mongo.get_collection_stats(collection_name)`
Obtém estatísticas de uma coleção.

**Parâmetros:**
- `collection_name`: Nome da coleção

**Retorna:** Dicionário com estatísticas (count, indexes, campos de exemplo)

### `mongo.export_collection_to_csv(collection_name, output_path, filter_query=None, limit=None)`
Exporta uma coleção para arquivo CSV.

**Parâmetros:**
- `collection_name`: Nome da coleção
- `output_path`: Caminho do arquivo de saída
- `filter_query`: Filtro de busca
- `limit`: Limite de documentos

**Retorna:** Caminho do arquivo criado

### `mongo.export_filtered_collections_to_csv(collection_filter, output_dir, document_filter=None, limit_per_collection=None, consolidated=False)`
Exporta múltiplas coleções filtradas para CSV.

**Parâmetros:**
- `collection_filter`: Filtro de nome de coleções
- `output_dir`: Diretório de saída
- `document_filter`: Filtro de documentos
- `limit_per_collection`: Limite por coleção
- `consolidated`: Se True, cria um arquivo consolidado com todas as coleções

**Retorna:** Lista de caminhos dos arquivos criados

## Exemplos Práticos

Veja o arquivo `examples/exemplo_mongo_disparos.py` para exemplos completos de uso incluindo:

- Listagem de coleções
- Busca de documentos
- Filtros por status
- Exportação para CSV
- Análise consolidada de múltiplas coleções

Para executar os exemplos:

```bash
cd examples
python exemplo_mongo_disparos.py
```

## Filtros MongoDB

Exemplos de filtros que você pode usar:

```python
# Status específico
{"status": "EXECUTED"}

# Múltiplos valores
{"status": {"$in": ["EXECUTED", "PENDING"]}}

# Campos não nulos
{"email": {"$ne": None}, "phone": {"$ne": None}}

# Regex
{"campaign_id": {"$regex": "bf.*25", "$options": "i"}}

# Combinação de filtros
{"status": "EXECUTED", "campaign_id": "lcto-bf-nov/25"}
```

## Troubleshooting

### Erro de conexão
- Verifique se o MongoDB está rodando
- Verifique a string de conexão no `.env`
- Teste a conexão: `mongosh "sua_connection_string"`

### Database não encontrada
- Verifique se o nome da database está correto
- Liste todas as databases: `show dbs` no mongosh

### Coleções não encontradas
- Liste todas as coleções: `show collections` no mongosh
- Verifique se o filtro está correto (case insensitive)

