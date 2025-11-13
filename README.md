# Projeto de Ciência de Dados

Projeto estruturado para análise de dados, desenvolvimento de modelos e geração de insights.

## 📋 Estrutura do Projeto

```
projeto_ciencia_dados/
│
├── 📁 data/
│   ├── raw/              # Dados brutos (nunca altere)
│   ├── interim/          # Dados parcialmente tratados
│   └── processed/        # Datasets prontos para análise/modelagem
│
├── 📁 notebooks/
│   ├── 01_exploracao.ipynb      # Análise exploratória
│   ├── 02_limpeza.ipynb         # Limpeza e tratamento
│   ├── 03_modelagem.ipynb       # Desenvolvimento de modelos
│   └── 04_visualizacao.ipynb    # Visualizações e relatórios
│
├── 📁 src/
│   ├── __init__.py
│   ├── data_utils.py     # Funções de limpeza / ingestão
│   ├── sql_utils.py      # Conexões e queries SQL
│   ├── stats_utils.py    # Análises estatísticas
│   ├── viz_utils.py      # Gráficos padronizados
│   └── api_utils.py      # Requisições externas (requests/httpx)
│
├── 📁 reports/
│   ├── figures/          # Gráficos exportados
│   └── summaries/        # Relatórios em HTML/PDF
│
├── 📁 config/
│   ├── .env              # Variáveis de ambiente (credenciais)
│   └── settings.yaml     # Configurações gerais
│
├── 📁 tests/             # Scripts de validação e testes
│
├── requirements.txt      # Dependências do projeto
├── README.md            # Este arquivo
└── .gitignore           # Arquivos ignorados pelo Git
```

## 🚀 Começando

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd projeto_ciencia_dados
```

2. Crie um ambiente virtual:
```bash
python -m venv venv

# No Windows
venv\Scripts\activate

# No Linux/Mac
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp config/.env.example config/.env
# Edite config/.env com suas credenciais
```

## 📊 Uso

### 1. Análise Exploratória
Comece pelo notebook `01_exploracao.ipynb` para entender seus dados:
```bash
jupyter notebook notebooks/01_exploracao.ipynb
```

### 2. Limpeza de Dados
Use o notebook `02_limpeza.ipynb` para tratar e preparar os dados:
- Remoção de duplicatas
- Tratamento de valores ausentes
- Detecção de outliers
- Transformações necessárias

### 3. Modelagem
Desenvolva e avalie modelos no notebook `03_modelagem.ipynb`:
- Split treino/teste
- Treinamento de modelos
- Validação cruzada
- Métricas de performance

### 4. Visualização
Crie visualizações e relatórios no notebook `04_visualizacao.ipynb`:
- Gráficos estáticos e interativos
- Dashboards
- Exportação de relatórios

## 🔌 Integrações com APIs

### API Hotmart

```python
from src.hotmart_utils import Hotmart
from dotenv import load_dotenv

load_dotenv()

# Inicializar cliente
hotmart = Hotmart()

# Buscar vendas
vendas = hotmart.get_sales_history(
    transaction_status='APPROVED',
    max_results=50
)

# Buscar alunos
alunos = hotmart.get_students(status='ACTIVE')
```

📖 **Documentação completa**: `examples/README_HOTMART.md`

### API TMB Educação

```python
from src.tmb_utils import TMB
from dotenv import load_dotenv

load_dotenv()

# Inicializar cliente
tmb = TMB()

# Listar produtos
produtos = tmb.get_produtos()

# Consultar pedidos
pedidos = tmb.get_pedidos(
    data_inicio='2025-01-01',
    data_final='2025-01-31'
)

# Criar oferta
oferta = tmb.criar_oferta(
    titulo='Promoção',
    produto_id=123,
    valor_principal=997.00,
    qtd_parcelas='12'
)
```

📖 **Documentação completa**: `examples/README_TMB.md`

### Características dos Clientes API

Ambos os clientes implementam:
- ✅ **Tratamento completo de exceções**
- ✅ **Timeout configurável** (30s padrão)
- ✅ **Retry automático** (até 3 tentativas)
- ✅ **Logging profissional**
- ✅ **Validação de credenciais**
- ✅ **Type hints completos**
- ✅ **Documentação completa**
- ✅ **Zero erros de lint**

## 🛠️ Módulos Utilitários

### data_utils.py
Funções para manipulação de dados:
- `load_raw_data()` - Carrega dados de diversos formatos
- `save_processed_data()` - Salva dados processados
- `remove_duplicates()` - Remove duplicatas
- `handle_missing_values()` - Trata valores ausentes
- `detect_outliers()` - Detecta outliers
- `normalize_column()` - Normaliza colunas numéricas

### sql_utils.py
Utilitários para banco de dados:
- `create_db_connection()` - Cria conexão com BD
- `execute_query()` - Executa queries SQL
- `save_to_database()` - Salva DataFrame no BD
- `list_tables()` - Lista tabelas disponíveis

### stats_utils.py
Funções estatísticas:
- `descriptive_stats()` - Estatísticas descritivas
- `correlation_analysis()` - Análise de correlação
- `hypothesis_test_ttest()` - Teste t de Student
- `hypothesis_test_chi2()` - Teste qui-quadrado
- `normality_test()` - Teste de normalidade
- `anova_test()` - Análise de variância

### viz_utils.py
Visualizações padronizadas:
- `plot_distribution()` - Histograma com densidade
- `plot_boxplot()` - Boxplot para outliers
- `plot_correlation_heatmap()` - Heatmap de correlação
- `plot_scatter()` - Gráfico de dispersão
- `plot_time_series()` - Séries temporais
- `save_figure()` - Salva figuras

### api_utils.py
Requisições a APIs:
- `make_request()` - Requisição HTTP genérica
- `get_json()` - GET retornando JSON
- `post_json()` - POST retornando JSON
- `async_make_request()` - Requisição assíncrona
- `paginated_request()` - Requisições paginadas

### hotmart_utils.py
Cliente completo para API Hotmart:
- `Hotmart()` - Cliente com autenticação OAuth 2.0
- `get_sales_history()` - Histórico de vendas
- `get_sales_participants()` - Participantes de vendas
- `get_sales_commissions()` - Comissões
- `get_students()` - Alunos do Hotmart Club
- Paginação automática, retry logic e rate limiting

### tmb_utils.py
Cliente completo para API TMB Educação:
- `TMB()` - Cliente com autenticação Bearer Token
- `get_pedidos()` - Consultar pedidos com paginação
- `get_pedido_detalhe()` - Detalhes de pedido específico
- `get_produtos()` - Listar produtos cadastrados
- `criar_oferta()` - Criar nova oferta
- `get_ofertas()` - Listar todas as ofertas
- Timeout configurável, retry automático e logging profissional

## 📁 Organização de Dados

- **data/raw/**: Mantenha os dados originais intocados
- **data/interim/**: Dados em estágio intermediário de processamento
- **data/processed/**: Dados finais prontos para análise

> ⚠️ **Importante**: Nunca modifique os dados em `data/raw/`. Sempre crie cópias em `interim/` ou `processed/`.

## 🔐 Configuração

### Variáveis de Ambiente (.env)
```env
# Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=seu_banco
DB_USER=usuario
DB_PASSWORD=senha

# API Hotmart
HOTMART_CLIENT_ID=seu_client_id
HOTMART_CLIENT_SECRET=seu_client_secret
HOTMART_BASIC_AUTH=Basic seu_token_base64
HOTMART_SUBDOMAIN=seu-subdomain

# API TMB Educação
TMB_API_TOKEN=seu_token_tmb

# Outras APIs
API_KEY=sua_chave_api
API_URL=https://api.exemplo.com
```

### Settings (settings.yaml)
```yaml
data:
  raw_path: data/raw
  processed_path: data/processed

models:
  random_seed: 42
  test_size: 0.2

visualization:
  style: seaborn
  figsize: [10, 6]
```

## 🧪 Testes

Execute os testes com:
```bash
pytest tests/
```

Com cobertura:
```bash
pytest --cov=src tests/
```

## 📝 Boas Práticas

1. **Controle de Versão**
   - Commit frequente com mensagens descritivas
   - Não versione dados ou credenciais

2. **Documentação**
   - Documente funções com docstrings
   - Mantenha o README atualizado
   - Comente código complexo

3. **Qualidade de Código**
   - Use formatação consistente (Black)
   - Siga PEP 8
   - Execute linters regularmente

4. **Reprodutibilidade**
   - Fixe random seeds
   - Documente versões de pacotes
   - Registre hiperparâmetros

## 🤝 Contribuindo

1. Crie uma branch para sua feature
2. Faça suas alterações
3. Execute os testes
4. Faça commit das mudanças
5. Abra um Pull Request

## 📄 Licença

[Especifique sua licença aqui]

## 👥 Autores

[Seu nome/equipe]

## 📞 Contato

[Informações de contato]

