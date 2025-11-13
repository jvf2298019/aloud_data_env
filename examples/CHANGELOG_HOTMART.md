# 📋 Changelog - Cliente Hotmart

## 🎉 Nova Funcionalidade: Formato de Data Simplificado

### Data: 13 de Novembro de 2025

### O Que Mudou?

Todos os métodos que aceitam `start_date` e `end_date` agora suportam **formato de data simplificado** em string `YYYY-MM-DD`!

### Métodos Afetados

- ✅ `get_sales_history()`
- ✅ `get_sales_participants()`
- ✅ `get_sales_commissions()`

### Como Era Antes ❌

```python
from datetime import datetime

# Era necessário calcular timestamp Unix em milissegundos
end_date = datetime.now()
start_date = datetime(2025, 1, 1)

start_ts = int(start_date.timestamp() * 1000)  # 1704067200000
end_ts = int(end_date.timestamp() * 1000)

vendas = hotmart.get_sales_history(
    start_date=start_ts,  # Difícil de ler e manter
    end_date=end_ts
)
```

### Como É Agora ✅

```python
# Formato simples e intuitivo!
vendas = hotmart.get_sales_history(
    start_date='2025-01-01',  # ✨ Muito mais fácil!
    end_date='2025-01-31'
)
```

### Retrocompatibilidade ✅

**O formato antigo (timestamp) ainda funciona!** Você pode migrar gradualmente seu código.

```python
# ✅ Formato novo
vendas = hotmart.get_sales_history(
    start_date='2025-01-01',
    end_date='2025-01-31'
)

# ✅ Formato antigo (ainda funciona)
vendas = hotmart.get_sales_history(
    start_date=1704067200000,
    end_date=1706745599000
)

# ✅ Misturar formatos também funciona!
vendas = hotmart.get_sales_history(
    start_date='2025-01-01',      # String
    end_date=1706745599000        # Timestamp
)
```

### Validação de Erros

O cliente agora valida o formato da data e fornece mensagens de erro claras:

```python
try:
    vendas = hotmart.get_sales_history(
        start_date='2025/01/01',  # ❌ Formato errado
        end_date='2025-01-31'
    )
except ValueError as e:
    print(e)
    # "Formato de data inválido: '2025/01/01'. 
    #  Use YYYY-MM-DD (ex: '2025-01-15') ou timestamp Unix em ms"
```

### Implementação Técnica

Foi adicionado um método privado `_convert_date_to_timestamp()` que:

1. Aceita `Union[int, str, None]`
2. Se receber string: converte de `YYYY-MM-DD` para timestamp Unix em ms
3. Se receber int: retorna como está (já é timestamp)
4. Se receber None: retorna None
5. Valida formato e tipo, lançando exceções descritivas

```python
def _convert_date_to_timestamp(self, date: Union[int, str, None]) -> Optional[int]:
    """Converte data para timestamp Unix em milissegundos."""
    if date is None:
        return None
    
    if isinstance(date, int):
        return date
    
    if isinstance(date, str):
        dt = datetime.strptime(date, '%Y-%m-%d')
        return int(dt.timestamp() * 1000)
    
    raise TypeError(...)
```

### Type Hints Atualizados

```python
# Antes
def get_sales_history(
    self,
    start_date: Optional[int] = None,  # Apenas int
    end_date: Optional[int] = None,
    ...
)

# Agora
def get_sales_history(
    self,
    start_date: Union[int, str, None] = None,  # int OU str!
    end_date: Union[int, str, None] = None,
    ...
)
```

### Exemplos de Uso

#### Exemplo 1: Período Específico

```python
# Vendas de janeiro de 2025
vendas = hotmart.get_sales_history(
    start_date='2025-01-01',
    end_date='2025-01-31',
    transaction_status='APPROVED'
)
```

#### Exemplo 2: Black Friday

```python
# Vendas da Black Friday 2024
vendas = hotmart.get_sales_history(
    start_date='2024-11-24',
    end_date='2024-11-27',
    max_results=200
)
```

#### Exemplo 3: Comissões do Mês

```python
# Comissões de dezembro
comissoes = hotmart.get_sales_commissions(
    start_date='2024-12-01',
    end_date='2024-12-31',
    commission_as='AFFILIATE'
)
```

#### Exemplo 4: Participantes Últimos 7 Dias

```python
from datetime import datetime, timedelta

# Data de hoje e 7 dias atrás (formato string)
hoje = datetime.now().strftime('%Y-%m-%d')
semana_passada = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

participantes = hotmart.get_sales_participants(
    start_date=semana_passada,
    end_date=hoje
)
```

### Benefícios

1. **✅ Mais Fácil de Ler**: Datas em formato legível
2. **✅ Mais Fácil de Escrever**: Não precisa calcular timestamps
3. **✅ Menos Erros**: Formato intuitivo reduz bugs
4. **✅ Retrocompatível**: Código antigo continua funcionando
5. **✅ Validação Clara**: Mensagens de erro descritivas
6. **✅ Type Safe**: Type hints atualizados para IDE support

### Migração

**Não é necessária migração imediata!** O formato antigo continua funcionando.

Quando quiser migrar:

```python
# De:
start_ts = int(datetime(2025, 1, 1).timestamp() * 1000)
vendas = hotmart.get_sales_history(start_date=start_ts, ...)

# Para:
vendas = hotmart.get_sales_history(start_date='2025-01-01', ...)
```

### Compatibilidade

- ✅ **Python 3.9+**: Compatível
- ✅ **Type Checkers**: mypy, pyright
- ✅ **Código Existente**: Totalmente retrocompatível
- ✅ **Zero Breaking Changes**: Nada quebra!

### Documentação Atualizada

- ✅ Docstrings dos métodos atualizadas
- ✅ README_HOTMART.md atualizado
- ✅ Exemplos práticos adicionados
- ✅ exemplo_hotmart.py com nova função de demonstração

### Testes Recomendados

Se você usa este cliente em produção, teste:

```python
import unittest
from src.hotmart_utils import Hotmart

class TestDateFormats(unittest.TestCase):
    def setUp(self):
        self.hotmart = Hotmart()
    
    def test_string_date_format(self):
        """Testa formato YYYY-MM-DD"""
        vendas = self.hotmart.get_sales_history(
            start_date='2025-01-01',
            end_date='2025-01-31',
            max_results=1
        )
        self.assertIsInstance(vendas, list)
    
    def test_timestamp_format(self):
        """Testa formato timestamp (retrocompatibilidade)"""
        vendas = self.hotmart.get_sales_history(
            start_date=1704067200000,
            end_date=1706745599000,
            max_results=1
        )
        self.assertIsInstance(vendas, list)
    
    def test_invalid_format(self):
        """Testa validação de formato inválido"""
        with self.assertRaises(ValueError):
            self.hotmart.get_sales_history(
                start_date='01/01/2025',  # Formato errado
                end_date='2025-01-31'
            )
```

### Próximos Passos

Considere usar o formato simplificado em:
- Scripts de relatórios
- Dashboards automatizados
- Integrações com outros sistemas
- Análises de período

---

## 📝 Histórico de Versões

### v2.0.0 - 13/11/2025
- ✨ **Nova funcionalidade**: Formato de data simplificado (YYYY-MM-DD)
- ✅ Retrocompatível com formato timestamp
- 📚 Documentação completamente atualizada
- 🎯 Type hints melhorados com Union types

### v1.0.0 - 13/11/2025
- 🎉 Versão inicial do cliente Hotmart
- ✅ Correção de bug crítico (linha 129)
- ✅ Tratamento completo de exceções
- ✅ Logging profissional
- ✅ Retry automático
- ✅ Zero erros de lint

---

**Feedback?** Entre em contato ou abra uma issue!

