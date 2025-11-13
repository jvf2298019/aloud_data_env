# Pasta de Queries SQL

Esta pasta contém arquivos `.sql` com queries testadas e reutilizáveis.

## Como Usar

### 1. Criar um arquivo .sql

Crie um arquivo com a extensão `.sql` nesta pasta. Por exemplo: `buscar_usuarios_ativos.sql`

```sql
-- queries/buscar_usuarios_ativos.sql
SELECT 
    id,
    nome,
    email,
    created_at
FROM usuarios
WHERE status = :status
    AND idade >= :idade_minima
ORDER BY created_at DESC
```

### 2. Carregar e Executar a Query

Use a função `load_query_from_file()` para carregar e executar:

```python
from sql_utils import DatabaseConnection, load_query_from_file

# Inicializa conexão
db = DatabaseConnection()

# Carrega e executa query
query = load_query_from_file('buscar_usuarios_ativos')
df = db.execute_query(query, {'status': 'ativo', 'idade_minima': 18})
```

### 3. Forma Compacta

Você pode fazer tudo em uma linha:

```python
df = db.execute_query(
    load_query_from_file('buscar_usuarios_ativos'),
    {'status': 'ativo', 'idade_minima': 18}
)
```

## Tipos de Queries

### SELECT (execute_query)

Para queries que retornam dados (SELECT):

```python
df = db.execute_query(load_query_from_file('nome_da_query'), params)
```

### UPDATE/INSERT/DELETE (execute_update)

Para queries que modificam dados:

```python
linhas = db.execute_update(load_query_from_file('nome_da_query'), params)
```

## Parâmetros

Use `:nome_parametro` para criar placeholders na query:

```sql
SELECT * FROM tabela 
WHERE coluna1 = :valor1 
  AND coluna2 = :valor2
```

E passe os valores ao executar:

```python
params = {'valor1': 'abc', 'valor2': 123}
df = db.execute_query(query, params)
```

## Boas Práticas

1. **Nomenclatura**: Use nomes descritivos para os arquivos
   - ✅ `buscar_clientes_por_periodo.sql`
   - ❌ `query1.sql`

2. **Comentários**: Documente suas queries
   ```sql
   -- Busca clientes ativos do último mês
   -- Parâmetros: :data_inicio, :data_fim, :status
   SELECT ...
   ```

3. **Organização**: Agrupe queries relacionadas por prefixo
   - `usuarios_buscar_ativos.sql`
   - `usuarios_atualizar_status.sql`
   - `pedidos_listar_recentes.sql`

4. **Versionamento**: Mantenha no Git para rastrear mudanças

5. **Testes**: Teste manualmente antes de salvar

## Exemplos

Veja os arquivos de exemplo nesta pasta:
- `exemplo_select.sql` - Exemplo de query SELECT
- `exemplo_update.sql` - Exemplo de query UPDATE

Para exemplos completos de uso, consulte:
- `notebooks/exemplo_uso_queries.ipynb`

