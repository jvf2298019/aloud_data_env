"""
Utilitários para limpeza e ingestão de dados
"""

import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, List, Optional, Dict, Any

import phonenumbers
from phonenumbers import NumberParseException, carrier, geocoder, timezone


def load_raw_data(filename: str, data_dir: str = "../data/raw", sep: str = ',') -> pd.DataFrame:
    """
    Carrega dados brutos de um arquivo
    
    Args:
        filename: Nome do arquivo a ser carregado
        data_dir: Diretório contendo os dados brutos
        
    Returns:
        DataFrame com os dados carregados
    """
    filepath = Path(data_dir) / filename
    
    if filepath.suffix == '.csv':
        return pd.read_csv(filepath, sep=sep)
    elif filepath.suffix in ['.xlsx', '.xls']:
        return pd.read_excel(filepath)
    elif filepath.suffix == '.parquet':
        return pd.read_parquet(filepath)
    elif filepath.suffix == '.json':
        return pd.read_json(filepath)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {filepath.suffix}")


def save_processed_data(df: pd.DataFrame, filename: str, data_dir: str = "../data/processed") -> None:
    """
    Salva dados processados
    
    Args:
        df: DataFrame a ser salvo
        filename: Nome do arquivo de saída
        data_dir: Diretório de destino
    """
    filepath = Path(data_dir)
    filepath.mkdir(parents=True, exist_ok=True)
    
    output_path = filepath / filename
    
    if output_path.suffix == '.csv':
        df.to_csv(output_path, index=False)
    elif output_path.suffix == '.parquet':
        df.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {output_path.suffix}")


def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Remove linhas duplicadas do DataFrame
    
    Args:
        df: DataFrame de entrada
        subset: Colunas a considerar para identificar duplicatas
        
    Returns:
        DataFrame sem duplicatas
    """
    return df.drop_duplicates(subset=subset, keep='first')


def handle_missing_values(df: pd.DataFrame, strategy: str = 'drop', fill_value=None) -> pd.DataFrame:
    """
    Trata valores ausentes no DataFrame
    
    Args:
        df: DataFrame de entrada
        strategy: Estratégia ('drop', 'mean', 'median', 'mode', 'fill')
        fill_value: Valor para preencher se strategy='fill'
        
    Returns:
        DataFrame com valores ausentes tratados
    """
    df_copy = df.copy()
    
    if strategy == 'drop':
        return df_copy.dropna()
    elif strategy == 'mean':
        return df_copy.fillna(df_copy.mean(numeric_only=True))
    elif strategy == 'median':
        return df_copy.fillna(df_copy.median(numeric_only=True))
    elif strategy == 'mode':
        return df_copy.fillna(df_copy.mode().iloc[0])
    elif strategy == 'fill':
        return df_copy.fillna(fill_value)
    else:
        raise ValueError(f"Estratégia inválida: {strategy}")


def detect_outliers(df: pd.DataFrame, column: str, method: str = 'iqr', threshold: float = 1.5) -> pd.Series:
    """
    Detecta outliers em uma coluna
    
    Args:
        df: DataFrame de entrada
        column: Nome da coluna a analisar
        method: Método de detecção ('iqr' ou 'zscore')
        threshold: Limite para considerar outlier
        
    Returns:
        Series booleana indicando outliers
    """
    if method == 'iqr':
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        return (df[column] < lower_bound) | (df[column] > upper_bound)
    
    elif method == 'zscore':
        from scipy import stats
        z_scores = np.abs(stats.zscore(df[column].dropna()))
        return z_scores > threshold
    
    else:
        raise ValueError(f"Método inválido: {method}")


def normalize_column(df: pd.DataFrame, column: str, method: str = 'minmax') -> pd.Series:
    """
    Normaliza uma coluna numérica
    
    Args:
        df: DataFrame de entrada
        column: Nome da coluna a normalizar
        method: Método de normalização ('minmax' ou 'zscore')
        
    Returns:
        Series com valores normalizados
    """
    if method == 'minmax':
        min_val = df[column].min()
        max_val = df[column].max()
        return (df[column] - min_val) / (max_val - min_val)
    
    elif method == 'zscore':
        mean = df[column].mean()
        std = df[column].std()
        return (df[column] - mean) / std
    
    else:
        raise ValueError(f"Método inválido: {method}")


def process_phone_string(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Processa números de telefone

    Args:
        df: DataFrame de entrada
        column: Nome da coluna a processar

    Returns:
        Series com números de telefone processados
    """
    def clean_phone(val):
        # Trate NA, None e strings vazias de forma segura
        if pd.isna(val):
            return pd.NA
        s = str(val)
        if s == "" or s.upper() == "NA" or s.upper() == "NAN":
            return pd.NA
        s = s.replace('.0', '') if s.endswith('.0') else s
        s = ''.join(filter(str.isdigit, s))
        s = s.strip()
        # 's' pode ser pd.NA, nesse caso str(s) é 'NA', trate de modo seguro
        if s == "" or s.upper() == "NA":
            return pd.NA
        return s

    # dtype='string' do pandas lida melhor com pd.NA
    return df[column].apply(clean_phone).astype('string')

def clean_and_lower_column(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Realiza trim e lower_case em uma coluna de string

    Args:
        df: DataFrame de entrada
        column: Nome da coluna a processar

    Returns:
        Series com valores ajustados
    """
    return df[column].astype(str).str.strip().str.lower()


def process_phone_number(phone: str, default_region: str = 'BR', return_type: str = 'COMPLETE') -> Dict[str, Any]:
    """
    Versão ROBUSTA usando python-phonenumbers (baseada na libphonenumber do Google).
    
    Args:
        phone: Número de telefone em qualquer formato
        default_region: Região padrão se não especificada (BR = Brasil)
    
    Returns:
        Dict com informações detalhadas do telefone
    """
    output = {
        'raw_phone_input': phone,
        'formatted_phone': '',
        'whatsapp_format': '',
        'isValid': False,
        'type': 'Invalid',
        'ddd': None,
        'ddi': None,
        'region': None,
        'carrier': None,
        'location': None,
        'timezone': None,
        'number_type': None
    }
    
    if not phone or not phone.strip():
        return output
    
    try:
        # Pré-processamento: Filtra caracteres não numéricos, exceto o "+"
        cleaned_phone = ''.join(c for c in phone.strip() if c.isdigit() or c == '+')

        if cleaned_phone.startswith('+'):
            cleaned_phone = cleaned_phone
        elif cleaned_phone.startswith('00') and len(cleaned_phone) > 2:
            cleaned_phone = '+' + cleaned_phone[2:]
        elif cleaned_phone.startswith('0') and not cleaned_phone.startswith('+') and len(cleaned_phone) > 10:
            cleaned_phone = '+' + cleaned_phone[1:]
        
        parsed_number = phonenumbers.parse(cleaned_phone, default_region)
        is_valid = phonenumbers.is_valid_number(parsed_number)
        is_possible = phonenumbers.is_possible_number(parsed_number)
        
        output['isValid'] = is_valid
        
        if not is_possible:
            output['type'] = 'Invalid'
            output['formatted_phone'] = phone
            output['whatsapp_format'] = phone
            return output
        
        output['ddi'] = str(parsed_number.country_code)
        output['region'] = phonenumbers.region_code_for_number(parsed_number)
        
        output['formatted_phone'] = phonenumbers.format_number(
            parsed_number, phonenumbers.PhoneNumberFormat.E164
        )
        output['whatsapp_format'] = output['formatted_phone']
        
        number_type = phonenumbers.number_type(parsed_number)
        type_mapping = {
            phonenumbers.PhoneNumberType.MOBILE: 'Mobile',
            phonenumbers.PhoneNumberType.FIXED_LINE: 'Fixed Line',
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: 'Fixed Line or Mobile',
            phonenumbers.PhoneNumberType.TOLL_FREE: 'Toll Free',
            phonenumbers.PhoneNumberType.PREMIUM_RATE: 'Premium Rate',
            phonenumbers.PhoneNumberType.VOIP: 'VoIP',
            phonenumbers.PhoneNumberType.UNKNOWN: 'Unknown'
        }
        output['number_type'] = type_mapping.get(number_type, 'Unknown')
        
        if output['region'] == 'BR':
            output['type'] = 'Nacional'
            national_number = str(parsed_number.national_number)
            if len(national_number) >= 10:
                output['ddd'] = national_number[:2]
                ddd_int = int(output['ddd']) if output['ddd'].isdigit() else 0
                if ddd_int > 28 and len(national_number) == 11 and national_number[2] == '9':
                    whatsapp_number = national_number[:2] + national_number[3:]
                    output['whatsapp_format'] = f"+55{whatsapp_number}"
                else:
                    output['whatsapp_format'] = f"+55{national_number}"
            try:
                output['carrier'] = carrier.name_for_number(parsed_number, 'pt')
                output['location'] = geocoder.description_for_number(parsed_number, 'pt')
                timezones = timezone.time_zones_for_number(parsed_number)
                output['timezone'] = list(timezones) if timezones else None
            except Exception:
                pass
        else:
            output['type'] = 'Internacional'
        
        if output['ddd'] and str(output['ddd']).isdigit():
            output['ddd'] = int(output['ddd'])
        if output['ddi'] and str(output['ddi']).isdigit():
            output['ddi'] = int(output['ddi'])
    except NumberParseException as e:
        output['type'] = 'Invalid'
        output['formatted_phone'] = phone
        output['whatsapp_format'] = phone
        output['error'] = str(e)
    except Exception as e:
        output['type'] = 'Invalid'
        output['formatted_phone'] = phone
        output['whatsapp_format'] = phone
        output['error'] = f"Unexpected error: {str(e)}"

    
    if return_type == 'COMPLETE':
        return output
    elif return_type == 'FORMATTED':
        return output['formatted_phone']
    elif return_type == 'WHATSAPP':
        return output['whatsapp_format']
    else:
        raise ValueError(f"Tipo de retorno inválido: {return_type}")

def to_snake_case(name: str) -> str:
    """
    Converte nomes para snake_case minúsculo.
    
    Args:
        name: String a ser convertida
        
    Returns:
        String no formato snake_case
        
    Examples:
        >>> to_snake_case("firstName")
        'first_name'
        >>> to_snake_case("First Name")
        'first_name'
        >>> to_snake_case("first-name.data")
        'first_name_data'
    """
    if not isinstance(name, str):
        name = str(name)
    
    # Substitui espaços, hífens e pontos por underscore
    name = re.sub(r'[\s\-\.]+', '_', name)
    # Adiciona underscore antes de maiúsculas precedidas por minúsculas/números
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    # Remove underscores múltiplos consecutivos
    name = re.sub(r'_+', '_', name)
    # Remove underscores no início e fim
    name = name.strip('_')
    
    return name.lower()


def flatten_dict(
    d: Dict[str, Any], 
    parent_key: str = '', 
    sep: str = '_',
    max_depth: Optional[int] = None
) -> Dict[str, Any]:
    """
    Achata dicionários aninhados (com suporte a listas) em uma única camada.
    
    Args:
        d: Dicionário a ser achatado
        parent_key: Chave pai para concatenação (usado na recursão)
        sep: Separador para concatenar chaves
        max_depth: Profundidade máxima de achatamento (None = sem limite)
        
    Returns:
        Dicionário achatado com chaves concatenadas
        
    Examples:
        >>> data = {'user': {'name': 'João', 'age': 30}}
        >>> flatten_dict(data)
        {'user_name': 'João', 'user_age': 30}
    """
    if not isinstance(d, dict):
        raise TypeError(f"Esperado dict, recebido {type(d).__name__}")
    
    items = []
    current_depth = parent_key.count(sep) if parent_key else 0
    
    for k, v in d.items():
        k = to_snake_case(str(k))
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        # Verifica se atingiu profundidade máxima
        if max_depth is not None and current_depth >= max_depth:
            items.append((new_key, v))
            continue
        
        if isinstance(v, dict) and v:  # Dicionário não vazio
            items.extend(flatten_dict(v, new_key, sep=sep, max_depth=max_depth).items())
        
        elif isinstance(v, list) and v:  # Lista não vazia
            for i, elem in enumerate(v):
                list_key = f"{new_key}{sep}{i}"
                if isinstance(elem, dict):
                    items.extend(flatten_dict(elem, list_key, sep=sep, max_depth=max_depth).items())
                else:
                    items.append((list_key, elem))
        
        else:
            # Valor simples (string, número, None, lista/dict vazios)
            items.append((new_key, v))
    
    return dict(items)


def flatten_list_to_df(
    data_list: List[Dict[str, Any]], 
    sep: str = '_',
    max_depth: Optional[int] = None
) -> pd.DataFrame:
    """
    Recebe uma lista de dicionários aninhados,
    aplica flatten_dict em todos e retorna um DataFrame pandas.
    
    Args:
        data_list: Lista de dicionários aninhados
        sep: Separador para concatenar chaves
        max_depth: Profundidade máxima de achatamento
        
    Returns:
        DataFrame com dicionários achatados
        
    Raises:
        ValueError: Se data_list estiver vazia ou não for uma lista
        
    Examples:
        >>> data = [{'user': {'name': 'João', 'age': 30}}, 
        ...         {'user': {'name': 'Maria', 'age': 25}}]
        >>> df = flatten_list_to_df(data)
        >>> df.columns.tolist()
        ['user_name', 'user_age']
    """
    if not isinstance(data_list, list):
        raise TypeError(f"Esperado list, recebido {type(data_list).__name__}")
    
    if not data_list:
        raise ValueError("data_list não pode estar vazia")
    
    flattened = [flatten_dict(item, sep=sep, max_depth=max_depth) for item in data_list]
    df = pd.DataFrame(flattened)
    
    return df


def timestamp_ms_to_datetime(df: pd.DataFrame, column: str, errors: str = 'coerce') -> pd.Series:
    """
    Converte uma coluna de timestamps em milissegundos para objetos datetime.
    
    Args:
        df: DataFrame de entrada
        column: Nome da coluna com timestamps em milissegundos
        errors: Como lidar com erros ('raise', 'coerce', 'ignore')
                - 'raise': lança exceção em caso de erro
                - 'coerce': converte valores inválidos para NaT
                - 'ignore': retorna a série original em caso de erro
        
    Returns:
        Series com valores datetime convertidos
        
    Examples:
        >>> df = pd.DataFrame({'timestamp': [1698857976000, 1698857977000, None]})
        >>> df['datetime'] = timestamp_ms_to_datetime(df, 'timestamp')
        >>> df['datetime'].dtype
        dtype('<M8[ns]')
    """
    if column not in df.columns:
        raise ValueError(f"Coluna '{column}' não encontrada no DataFrame")
    
    try:
        # Converte timestamps em milissegundos para datetime
        # pd.to_datetime com unit='ms' espera valores numéricos
        return pd.to_datetime(df[column], unit='ms', errors=errors)
    except Exception as e:
        if errors == 'raise':
            raise ValueError(f"Erro ao converter coluna '{column}': {str(e)}")
        elif errors == 'ignore':
            return df[column]
        else:
            # Para 'coerce' ou qualquer outro valor, tenta novamente com coerce
            return pd.to_datetime(df[column], unit='ms', errors='coerce')


def parse_utm_string(df: pd.DataFrame, column: str, inplace: bool = False) -> pd.DataFrame:
    """
    Extrai informações de UTM de strings em múltiplos formatos.
    
    Suporta três formatos de entrada:
    1. Query string URL-encoded: utm_source=valor%26utm_campaign=valor%26...
    2. Query string padrão: utm_source=valor&utm_campaign=valor&...
    3. Formato customizado com abreviações: us:valor|uc:valor|uo:valor|...
    
    Mapeamento de abreviações (formato 3):
        us: → utm_source
        uc: → utm_campaign
        uo: → utm_content
        um: → utm_medium
        ut: → utm_term
        s:  → seller
    
    Args:
        df: DataFrame de entrada
        column: Nome da coluna contendo as strings de UTM
        inplace: Se True, modifica o DataFrame original. Se False, retorna uma cópia.
        
    Returns:
        DataFrame com as seguintes colunas adicionadas:
        - utm_source
        - utm_campaign
        - utm_content
        - utm_medium
        - utm_term
        - seller
        - campaign_id
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'utm_raw': [
        ...         'utm_source=whatsapp%26utm_campaign=lcto-bf25',
        ...         'utm_source=sales&seller=maria',
        ...         'us:cs|uc:venda|um:whatsapp'
        ...     ]
        ... })
        >>> result = parse_utm_string(df, 'utm_raw')
        >>> result['utm_source'].tolist()
        ['whatsapp', 'sales', 'cs']
    """
    from urllib.parse import unquote
    
    if column not in df.columns:
        raise ValueError(f"Coluna '{column}' não encontrada no DataFrame")
    
    # Trabalha com cópia ou original dependendo do parâmetro inplace
    result_df = df if inplace else df.copy()
    
    # Mapeamento de abreviações para nomes completos
    ABBREVIATION_MAP = {
        'us': 'utm_source',
        'uc': 'utm_campaign',
        'uo': 'utm_content',
        'um': 'utm_medium',
        'ut': 'utm_term',
        's': 'seller'
    }
    
    # Lista de campos a extrair
    UTM_FIELDS = ['utm_source', 'utm_campaign', 'utm_content', 'utm_medium', 'utm_term', 'seller', 'campaign_id']
    
    def _detect_pattern(utm_string: str) -> str:
        """Detecta o padrão da string de UTM."""
        if not utm_string or not isinstance(utm_string, str):
            return 'empty'
        
        # Padrão 1: URL encoded
        if '%26' in utm_string or '%3D' in utm_string.lower():
            return 'url_encoded'
        
        # Normaliza caracteres especiais
        s = s.replace('｜', '|').replace('：', ':').replace('＝', '=').replace('＆', '&')
        
        # Padrão 3: Formato customizado (us:valor ou us:valor|uc:valor)
        # Detecta se tem abreviações conhecidas seguidas de :
        if ':' in utm_string:
            # Verifica se começa com uma abreviação conhecida
            first_part = utm_string.split('|')[0] if '|' in utm_string else utm_string
            if ':' in first_part:
                prefix = first_part.split(':')[0].strip().lower()
                if prefix in ABBREVIATION_MAP:
                    return 'custom'
        
        return 'unknown'
    
    def _parse_query_string(utm_string: str, url_encoded: bool = False) -> Dict[str, str]:
        """Parse de query strings (padrões 1 e 2)."""
        result = {}
        
        return out
    
    # Aplica parse e expande para colunas
    parsed = result_df[column].apply(parse_single)
    parsed_df = pd.DataFrame(parsed.tolist(), index=result_df.index)
    
    # Adiciona colunas ao resultado
    for field in FIELDS:
        result_df[field] = parsed_df[field]
    
    return result_df