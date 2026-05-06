import os
import re
import json
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
import time
from typing import Optional, List, Dict, Any, Union
from urllib.parse import unquote

import pandas as pd
from pytz import timezone as pytz_timezone

# Configurar logging
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES
# =============================================================================

# Timezone padrão para dados Hotmart (Brasil)
HOTMART_TIMEZONE = pytz_timezone('America/Sao_Paulo')

# Caminho do arquivo de cache local para mapeamento de ofertas
# Prioridade: 1. Arquivo JSON local, 2. Banco de dados, 3. Hardcoded
OFFER_CAMPAIGN_MAP_FILE = Path(__file__).parent.parent / 'data' / 'interim' / 'offer_campaign_map.json'

# Mapeamento de códigos de oferta para campanhas (FALLBACK HARDCODED)
# Usado apenas quando arquivo JSON e banco de dados não estão disponíveis
OFFER_TO_CAMPAIGN_MAP_FALLBACK: Dict[str, str] = {
    "4srczreh": "BF24",
    "dvc4f94d": "BF24",
    "x508omy3": "BF24",
    "oakb6qyh": "BF24",
    "k5htrkdt": "BF24",
    "uqa1cqwe": "BF24",
    "2g60wha1": "BF24",
    "e7i0za0r": "BF24_ANT",
    "pqyd6avt": "BF24",
    "bglr3mgf": "BF24",
    "pdaw9dd0": "BF24",
    "ankqn20w": "BF24A",
}


# =============================================================================
# FUNÇÕES DE MAPEAMENTO DE OFERTAS
# =============================================================================

def load_offer_campaign_map(
    cache_file: Optional[Path] = None,
    db: Optional[Any] = None,
    query_name: str = 'select_all_offers',
    use_db_fallback: bool = True,
    use_hardcoded_fallback: bool = True
) -> Dict[str, str]:
    """
    Carrega o mapeamento offer_id -> campaign_id.
    
    Ordem de prioridade:
    1. Arquivo JSON local (data/interim/offer_campaign_map.json)
    2. Banco de dados (se use_db_fallback=True)
    3. Fallback hardcoded (se use_hardcoded_fallback=True)
    
    Args:
        cache_file: Caminho do arquivo JSON de cache. Se None, usa OFFER_CAMPAIGN_MAP_FILE
        db: Instância de DatabaseConnection (sql_utils) para fallback ao banco
        query_name: Nome do arquivo SQL na pasta queries (default: 'select_all_offers')
        use_db_fallback: Se True, tenta carregar do banco se arquivo não existir
        use_hardcoded_fallback: Se True, usa OFFER_TO_CAMPAIGN_MAP_FALLBACK como último recurso
    
    Returns:
        Dict[str, str]: Mapeamento offer_id -> campaign_id
    
    Raises:
        FileNotFoundError: Se nenhuma fonte de dados estiver disponível e fallbacks desabilitados
    
    Example:
        >>> # Uso padrão: lê do arquivo JSON local
        >>> offer_map = load_offer_campaign_map()
        >>> print(offer_map)
        {'4srczreh': 'BF24', 'dvc4f94d': 'BF24', ...}
        
        >>> # Forçar uso do banco de dados (ignora arquivo local)
        >>> from sql_utils import DatabaseConnection
        >>> db = DatabaseConnection()
        >>> offer_map = load_offer_campaign_map(cache_file=Path('/dev/null'), db=db)
    """
    if cache_file is None:
        cache_file = OFFER_CAMPAIGN_MAP_FILE
    
    # === 1. Tenta arquivo JSON local ===
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                offer_map = json.load(f)
            
            if offer_map:
                logger.info("Carregados %d mapeamentos do arquivo %s", len(offer_map), cache_file)
                return offer_map
            else:
                logger.warning("Arquivo %s está vazio", cache_file)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Erro ao ler arquivo %s: %s", cache_file, e)
    else:
        logger.debug("Arquivo de cache não encontrado: %s", cache_file)
    
    # === 2. Tenta banco de dados ===
    if use_db_fallback:
        try:
            if db is None:
                from sql_utils import DatabaseConnection
                db = DatabaseConnection()
            
            df = db.execute_query_from_file(query_name)
            
            if not df.empty:
                # Valida colunas
                required_cols = {'offer_id', 'campaign_id'}
                missing_cols = required_cols - set(df.columns)
                if missing_cols:
                    raise ValueError(
                        f"Colunas obrigatórias não encontradas: {missing_cols}. "
                        f"Colunas disponíveis: {df.columns.tolist()}"
                    )
                
                # Converte DataFrame para dict
                offer_map: Dict[str, str] = {}
                for _, row in df.iterrows():
                    offer_id = row['offer_id']
                    campaign_id = row['campaign_id']
                    
                    if pd.notna(offer_id) and pd.notna(campaign_id):
                        offer_map[str(offer_id)] = str(campaign_id)
                
                if offer_map:
                    logger.info("Carregados %d mapeamentos do banco de dados", len(offer_map))
                    return offer_map
                else:
                    logger.warning("Query %s retornou resultado vazio", query_name)
            else:
                logger.warning("Query %s retornou DataFrame vazio", query_name)
                
        except Exception as e:
            logger.warning("Erro ao carregar do banco de dados: %s", e)
    
    # === 3. Usa fallback hardcoded ===
    if use_hardcoded_fallback:
        logger.info("Usando mapeamento hardcoded como fallback")
        return OFFER_TO_CAMPAIGN_MAP_FALLBACK.copy()
    
    raise FileNotFoundError(
        f"Nenhuma fonte de mapeamento disponível. "
        f"Arquivo: {cache_file}, Banco: {'desabilitado' if not use_db_fallback else 'erro'}"
    )


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def extract_utm_parameters(origem_de_checkout: Optional[str]) -> Dict[str, Any]:
    """
    Extrai parâmetros UTM de uma string de origem de checkout.
    
    Suporta três formatos de encoding:
    - 'legacy': us:valor|um:valor|uc:valor...
    - 'query': utm_source=valor&utm_medium=valor...
    - 'mixed': combinação de ambos (query tem precedência)
    
    Args:
        origem_de_checkout: String com origem do checkout (pode ser URL, 
                           formato legacy ou misto)
    
    Returns:
        Dict com parâmetros extraídos e metadados:
        - has_correct_utm_pattern: bool indicando se algum parâmetro foi encontrado
        - encoding_type: 'legacy', 'query', 'mixed' ou 'unknown'
        - utm_source, utm_medium, utm_campaign, utm_content, utm_term
        - lead_id, active_id, seller, campaign_id
        - extras: dict com parâmetros não reconhecidos (opcional)
    
    Example:
        >>> extract_utm_parameters("us:google|um:cpc|uc:bf24")
        {'has_correct_utm_pattern': True, 'encoding_type': 'legacy', 
         'utm_source': 'google', 'utm_medium': 'cpc', 'utm_campaign': 'bf24', ...}
        
        >>> extract_utm_parameters("utm_source=facebook&utm_medium=social")
        {'has_correct_utm_pattern': True, 'encoding_type': 'query',
         'utm_source': 'facebook', 'utm_medium': 'social', ...}
    """
    empty: Dict[str, Any] = {
        'has_correct_utm_pattern': False,
        'encoding_type': 'unknown',
        'utm_source': None,
        'utm_medium': None,
        'utm_campaign': None,
        'utm_content': None,
        'utm_term': None,
        'lead_id': None,
        'active_id': None,
        'seller': None,
        'campaign_id': None,
    }

    if not origem_de_checkout or not isinstance(origem_de_checkout, str):
        return empty

    raw = origem_de_checkout.strip()
    if not raw:
        return empty

    # --- Mapeamento legacy (abreviações) ---
    legacy_map = {
        'us': 'utm_source',
        'um': 'utm_medium',
        'uc': 'utm_campaign',
        'uo': 'utm_content',
        'ut': 'utm_term',
        'li': 'lead_id',
        'ai': 'active_id',
        'v': 'seller',
        's': 'seller',
        'ci': 'campaign_id',
    }

    known_query_keys = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
        'lead_id', 'active_id', 'seller', 'campaign_id'
    }

    def clean_val(v: Optional[str]) -> Optional[str]:
        """Remove colchetes, espaços e decodifica URL encoding."""
        if v is None:
            return None
        s = str(v).strip()
        s = re.sub(r'^\[+|\]+$', '', s).strip()
        try:
            s = unquote(s)
        except Exception:
            pass
        return s if s else None

    # Detecção de formato
    looks_like_legacy = bool(
        re.search(r'\b(?:us|um|uc|uo|ut|li|ai|v|s|ci):', raw, re.IGNORECASE) 
        or '|' in raw
    )
    # Suporta & e &amp; (HTML-encoded) como separadores
    looks_like_query = bool(
        '=' in raw and ('&' in raw or '&amp;' in raw or raw.startswith('utm_'))
    )

    # Objeto de saída
    out: Dict[str, Any] = {**empty}

    def parse_legacy(s: str) -> None:
        """Parseia formato legacy: us:valor|um:valor|..."""
        chunks = [chunk.strip() for chunk in s.split('|') if chunk.strip()]
        for chunk in chunks:
            idx = chunk.find(':')
            if idx <= 0:
                continue
            k = chunk[:idx].strip().lower()
            v = clean_val(chunk[idx + 1:])
            mapped = legacy_map.get(k)
            if mapped and v:
                if out.get(mapped) is None or out.get(mapped) == '':
                    out[mapped] = v

    def parse_query(s: str) -> None:
        """Parseia formato query string: key=valor&key2=valor2..."""
        # Normaliza separadores: &amp; (HTML-encoded) e espaços para &
        normalized = s.replace('&amp;', '&')
        normalized = re.sub(r'\s+', '&', normalized)
        pairs = [p for p in normalized.split('&') if p]

        for pair in pairs:
            parts = pair.split('=', 1)
            if not parts:
                continue
            
            key = parts[0].strip()
            val = clean_val(parts[1]) if len(parts) > 1 else None
            
            if not key:
                continue

            if key in known_query_keys and val:
                out[key] = val
            elif val:
                if 'extras' not in out:
                    out['extras'] = {}
                out['extras'][key] = val

    # Aplica parsers conforme o tipo detectado
    if looks_like_legacy and looks_like_query:
        out['encoding_type'] = 'mixed'
        parse_legacy(raw)
        parse_query(raw)  # Query tem precedência
    elif looks_like_legacy:
        out['encoding_type'] = 'legacy'
        parse_legacy(raw)
    elif looks_like_query:
        out['encoding_type'] = 'query'
        parse_query(raw)

    # Sucesso se pelo menos um campo conhecido apareceu
    out['has_correct_utm_pattern'] = any(
        out.get(k) is not None and out.get(k) != ''
        for k in known_query_keys
    )

    return out


def remove_empty_objects(obj: Any) -> Any:
    """
    Remove valores None, strings vazias e listas vazias de dicts recursivamente.
    
    Args:
        obj: Objeto a ser limpo (dict, list ou valor primitivo)
    
    Returns:
        Objeto limpo sem valores vazios
    
    Example:
        >>> remove_empty_objects({'a': 1, 'b': None, 'c': ''})
        {'a': 1}
        >>> remove_empty_objects({'nested': {'a': None, 'b': 2}})
        {'nested': {'b': 2}}
    """
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            cleaned_v = remove_empty_objects(v)
            # Mantém apenas valores não vazios
            if cleaned_v is not None and cleaned_v != '' and cleaned_v != [] and cleaned_v != {}:
                cleaned[k] = cleaned_v
        return cleaned
    if isinstance(obj, list):
        return [remove_empty_objects(i) for i in obj if i is not None]
    return obj


# =============================================================================
# FUNÇÕES DE LEITURA E CONVERSÃO DE CSV
# =============================================================================

def read_hotmart_csv(
    file_name: str,
    data_dir: str = '../data/raw',
    sep: str = ';'
) -> pd.DataFrame:
    """
    Lê CSV exportado da Hotmart e aplica transformações padrão.
    
    Transformações aplicadas:
    - Converte colunas de data para datetime com timezone America/Sao_Paulo
    - Formata números de telefone usando process_phone_number
    - Calcula valor final considerando moeda de recebimento
    
    Args:
        file_name: Nome do arquivo (com ou sem extensão .csv)
        data_dir: Diretório contendo o arquivo
        sep: Separador do CSV (padrão: ';' para exports Hotmart)
    
    Returns:
        DataFrame com dados processados
    
    Example:
        >>> df = read_hotmart_csv('vendas_janeiro', data_dir='data/raw')
        >>> df.columns.tolist()
        ['Nome', 'Email', 'Data de Venda', ..., 'formatted_phone', 'valor_final']
    """
    # Import local para evitar dependência circular
    from data_utils import load_raw_data, process_phone_number
    
    # Adiciona extensão se não presente
    if not file_name.endswith('.csv'):
        file_name = f'{file_name}.csv'
    
    df = load_raw_data(file_name, data_dir=data_dir, sep=sep)
    
    # === Conversão de datas com timezone ===
    date_columns = ['Data de Venda', 'Data de Confirmação']
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(
                    df[col], 
                    dayfirst=True, 
                    errors='coerce'
                ).dt.tz_localize(HOTMART_TIMEZONE)
            except Exception as e:
                logger.warning("Erro ao converter coluna %s: %s", col, e)
    
    # === Processamento de telefone ===
    if 'DDD' in df.columns and 'Telefone' in df.columns:
        # Converte para string e limpa
        df['DDD'] = df['DDD'].astype('string')
        df['Telefone'] = df['Telefone'].astype('string')
        
        # Remove .0 de DDDs que vieram como float
        df['DDD'] = df['DDD'].apply(
            lambda x: x.replace('.0', '') if pd.notna(x) and '.0' in str(x) else x
        )

        df['Telefone'] = df['Telefone'].apply(
            lambda x: x.replace('.0', '') if pd.notna(x) and '.0' in str(x) else x
        )
        
        # Concatena DDD + Telefone
        df['phone_raw'] = df.apply(
            lambda x: f"{x['DDD']}{x['Telefone']}" if pd.notna(x['DDD']) else x['Telefone'],
            axis=1
        )
        
        # Aplica processamento de telefone
        df['phone_info'] = df['phone_raw'].apply(
            lambda x: process_phone_number(str(x)) if pd.notna(x) else {}
        )

        df['formatted_phone'] = df['phone_info'].apply(
            lambda x: x.get('formatted_phone', '') if isinstance(x, dict) else ''
        )
    
    # === Cálculo de valor final ===
    if 'Moeda de recebimento' in df.columns and 'Faturamento líquido' in df.columns:
        df['valor_final'] = df.apply(
            lambda x: x['Faturamento líquido'] 
                if x.get('Moeda de recebimento') == 'BRL' 
                else x.get('Valor que você recebeu convertido', x['Faturamento líquido']),
            axis=1
        )
    
    logger.info("CSV Hotmart carregado: %s linhas, %s colunas", len(df), len(df.columns))
    return df


def format_hotmart_conversions(
    df: pd.DataFrame,
    conversion_type_id: str = "8",
    campaign_map: Optional[Dict[str, str]] = None,
    default_campaign: str = 'PERP',
    skip_conversion: bool = False,
    skip_orquestration: bool = True,
    destination_queue: str = 'S.NORM.PROD.NEW'
) -> List[Dict[str, Any]]:
    """
    Converte DataFrame de vendas Hotmart para estrutura de conversão.
    
    Gera lista de dicts no formato esperado pelo sistema de normalização,
    com dados do lead e da conversão separados.
    
    Args:
        df: DataFrame com dados de vendas (output de read_hotmart_csv)
        conversion_type_id: ID do tipo de conversão (padrão: 8 = PURCHASE_APPROVED)
        campaign_map: Mapeamento offer_code -> campaign_id. Se None, usa fallback hardcoded.
                      Prefira usar load_offer_campaign_map(db) para carregar do banco.
        default_campaign: Campanha padrão para ofertas não mapeadas
        skip_conversion: Se True, pula a criação de conversão no fluxo (default: False)
        skip_orquestration: Se True, pula orquestração no fluxo (default: True)
        destination_queue: Fila de destino para processamento (default: 'S.NORM.PROD.NEW')
    
    Returns:
        Lista de dicts com estrutura:
        {
            "lead_data": {...},
            "conversion_data": {...},
            "flow_settings": {...},
            "row": int
        }
    
    Example:
        >>> # Usando mapeamento do banco de dados (recomendado)
        >>> from sql_utils import DatabaseConnection
        >>> db = DatabaseConnection()
        >>> offer_map = load_offer_campaign_map(db)
        >>> df = read_hotmart_csv('vendas')
        >>> conversions = format_hotmart_conversions(df, campaign_map=offer_map)
        
        >>> # Usando cache local (lê de data/interim/offer_campaign_map.json)
        >>> conversions = format_hotmart_conversions(df)
    """
    if campaign_map is None:
        # Carrega do arquivo JSON local, com fallback para banco e hardcoded
        campaign_map = load_offer_campaign_map()
    
    # Import para processamento de telefone
    from data_utils import process_phone_number
    
    processed_leads: List[Dict[str, Any]] = []
    
    for index, row in df.iterrows():
        # Extrai UTM da origem de checkout
        origin = row.get('Origem de Checkout', '')
        utm_params = extract_utm_parameters(origin if pd.notna(origin) else '')
        
        # Determina campanha pelo código de oferta
        offer_code = row.get('Código de Oferta', '')
        if pd.isna(offer_code):
            offer_code = ''
        campaign_id = campaign_map.get(str(offer_code), default_campaign)
        
        # Monta raw_conversion_info
        raw_conversion_info: Dict[str, Any] = {
            "event_type": "PURCHASE_APPROVED",
            "product_name": str(row.get('Nome do Produto', '')).strip() if pd.notna(row.get('Nome do Produto')) else '',
            "approved_date": row['Data de Confirmação'].isoformat() if pd.notna(row.get('Data de Confirmação')) else None,
            "order_date": row['Data de Venda'].isoformat() if pd.notna(row.get('Data de Venda')) else None,
            "is_order_bump": False,
            "origin": origin if pd.notna(origin) else None,
            "payment_method": row.get('Tipo de Pagamento') if pd.notna(row.get('Tipo de Pagamento')) else None,
            "installments_number": row.get('Número da Parcela') if pd.notna(row.get('Número da Parcela')) else None,
            "offer_code": offer_code if offer_code else None,
            "price_value": row.get('Preço Total') if pd.notna(row.get('Preço Total')) else None,
            "price_currency": row.get('Moeda') if pd.notna(row.get('Moeda')) else None,
            "checkout_country": row.get('País') if pd.notna(row.get('País')) else None,
            "transaction": row.get('Transação') if pd.notna(row.get('Transação')) else None,
            "recurrence_number": int(row['Recorrência']) if pd.notna(row.get('Recorrência')) else 0,
            "raw_producer_commission_value": row.get('Faturamento líquido') if pd.notna(row.get('Faturamento líquido')) else None,
            "producer_commission_currency": row.get('Moeda de recebimento') if pd.notna(row.get('Moeda de recebimento')) else None,
            "converted_producer_commission_value": row.get('valor_final') if pd.notna(row.get('valor_final')) else None,
            "checkout_platform": "hotmart",
        }
        
        # Taxa de câmbio
        if row.get('Moeda de recebimento') == "BRL":
            raw_conversion_info["considered_conversion_rate"] = 1
        else:
            rate = row.get('Taxa de Câmbio do valor recebido')
            raw_conversion_info["considered_conversion_rate"] = rate if pd.notna(rate) else None
        
        # Adiciona seller do UTM se presente
        if utm_params.get('seller'):
            raw_conversion_info["seller"] = utm_params['seller']
        
        # Processa telefone: DDD + Telefone -> process_phone_number
        phone_data = None
        telefone_raw = row.get('Telefone')
        ddd_raw = row.get('DDD')
        
        # Só processa se Telefone não for nulo
        if pd.notna(telefone_raw) and str(telefone_raw).strip():
            # Remove .0 de DDD e Telefone (vêm como float às vezes)
            def clean_phone_part(val):
                if pd.isna(val):
                    return None
                s = str(val).strip()
                if s.endswith('.0'):
                    s = s[:-2]
                # Remove caracteres não numéricos
                s = ''.join(c for c in s if c.isdigit())
                return s if s else None
            
            ddd_clean = clean_phone_part(ddd_raw)
            telefone_clean = clean_phone_part(telefone_raw)
            
            if telefone_clean:
                # Concatena DDD + Telefone (se DDD existir)
                if ddd_clean:
                    phone_raw = f"{ddd_clean}{telefone_clean}"
                else:
                    # Número internacional (sem DDD brasileiro)
                    phone_raw = telefone_clean
                
                # Processa com process_phone_number
                phone_data = process_phone_number(phone_raw)
                phone_data['success'] = phone_data.get('isValid', False) or phone_data.get('type') != 'Invalid'
        
        # Monta lead_data
        lead_data: Dict[str, Any] = {
            "email": {"value": row.get('Email') if pd.notna(row.get('Email')) else None},
            "country": row.get('País') if pd.notna(row.get('País')) else None,
            "state": row.get('Estado') if pd.notna(row.get('Estado')) else None,
            "city": row.get('Cidade') if pd.notna(row.get('Cidade')) else None,
            "document": row.get('Documento') if pd.notna(row.get('Documento')) else None,
            "name": row.get('Nome') if pd.notna(row.get('Nome')) else None,
        }
        
        # Só adiciona phone se houver dados processados
        if phone_data:
            lead_data["phone"] = phone_data
        
        # Monta estrutura de saída
        lead_output: Dict[str, Any] = {
            "lead_data": lead_data,
            "conversion_data": {
                "conversion_date": row['Data de Venda'].isoformat() if pd.notna(row.get('Data de Venda')) else None,
                "conversion_type_id": conversion_type_id,
                "campaign_id": campaign_id,
                "utm_source": utm_params.get('utm_source'),
                "utm_medium": utm_params.get('utm_medium'),
                "utm_content": utm_params.get('utm_content'),
                "utm_campaign": utm_params.get('utm_campaign'),
                "utm_term": utm_params.get('utm_term'),
                "conversion_raw_info": raw_conversion_info,
            },
            "flow_settings": {
                "skip_conversion": skip_conversion,
                "skip_orquestration": skip_orquestration,
                "destination_queue": destination_queue,
            },
            "row": index + 1,
        }
        
        processed_leads.append(remove_empty_objects(lead_output))
    
    logger.info("Formatados %s leads para conversão", len(processed_leads))
    return processed_leads


# =============================================================================
# EXCEÇÕES E CLASSES
# =============================================================================

class HotmartAPIError(Exception):
    """Exceção customizada para erros da API Hotmart"""


class Hotmart:
    """
    Cliente para interação com a API Hotmart.
    
    Gerencia autenticação, rate limiting e paginação automática.
    Requer as seguintes variáveis de ambiente:
    - HOTMART_CLIENT_ID
    - HOTMART_CLIENT_SECRET
    - HOTMART_BASIC_AUTH
    - HOTMART_SUBDOMAIN (opcional, para métodos do Club)
    """
    
    def __init__(self) -> None:
        # Carregar credenciais
        self.client_id: Optional[str] = os.getenv('HOTMART_CLIENT_ID')
        self.client_secret: Optional[str] = os.getenv('HOTMART_CLIENT_SECRET')
        self.basic_auth: Optional[str] = os.getenv('HOTMART_BASIC_AUTH')
        
        # Validar credenciais no init
        if not all([self.client_id, self.client_secret, self.basic_auth]):
            raise ValueError(
                "Credenciais Hotmart não encontradas. "
                "Configure HOTMART_CLIENT_ID, HOTMART_CLIENT_SECRET e HOTMART_BASIC_AUTH"
            )
        
        # Tokens e controle
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # Rate limiting
        self.rate_limit: int = 500
        self.rate_remaining: int = 500
        self.rate_reset: Optional[int] = None

    def authenticate(self) -> None:
        """Autentica na API Hotmart e obtém access token"""
        url = (
            f"https://api-sec-vlc.hotmart.com/security/oauth/token"
            f"?grant_type=client_credentials"
            f"&client_id={self.client_id}"
            f"&client_secret={self.client_secret}"
        )
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'{self.basic_auth}'
        }
        
        try:
            response = requests.post(url, headers=headers, timeout=30)
            self._update_rate_limit(response.headers)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            expires_in = data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            logger.info("Autenticação realizada com sucesso")
            
        except requests.exceptions.RequestException as e:
            logger.error("Falha na autenticação: %s", e)
            raise HotmartAPIError(f"Erro ao autenticar: {e}") from e

    def refresh_token(self) -> None:
        """Verifica e renova token se necessário"""
        if self.token_expiry and datetime.now() >= self.token_expiry:
            logger.info("Token expirado. Renovando...")
            self.authenticate()
        else:
            logger.debug("Token ainda válido")

    def _update_rate_limit(self, headers: Dict[str, str]) -> None:
        """Atualiza informações de rate limiting a partir dos headers"""
        try:
            self.rate_limit = int(headers.get('X-RateLimit-Limit-Minute', 500))
            self.rate_remaining = int(headers.get('X-RateLimit-Remaining-Minute', 500))
            reset_value = headers.get('RateLimit-Reset', '60')
            self.rate_reset = int(reset_value) if str(reset_value).isdigit() else 60
        except (ValueError, AttributeError) as e:
            logger.warning("Erro ao atualizar rate limit: %s", e)

    def _ensure_authenticated(self) -> None:
        """Garante que há um token válido antes de fazer requisições"""
        if not self.access_token or (self.token_expiry and datetime.now() >= self.token_expiry):
            logger.info("Token inválido ou expirado. Autenticando...")
            self.authenticate()
    
    def _convert_date_to_timestamp(self, date: Union[int, str, None]) -> Optional[int]:
        """
        Converte data para timestamp Unix em milissegundos.
        
        Args:
            date: Data em formato YYYY-MM-DD (str), timestamp Unix em ms (int), ou None
            
        Returns:
            Timestamp Unix em milissegundos ou None
            
        Raises:
            ValueError: Se o formato da data for inválido
            
        Example:
            >>> _convert_date_to_timestamp('2025-01-15')
            1736899200000
            >>> _convert_date_to_timestamp(1736899200000)
            1736899200000
            >>> _convert_date_to_timestamp(None)
            None
        """
        if date is None:
            return None
        
        # Se já é timestamp (int), retorna como está
        if isinstance(date, int):
            return date
        
        # Se é string, converte de YYYY-MM-DD para timestamp
        if isinstance(date, str):
            try:
                dt = datetime.strptime(date, '%Y-%m-%d')
                # Converter para timestamp Unix em milissegundos
                timestamp_ms = int(dt.timestamp() * 1000)
                return timestamp_ms
            except ValueError as e:
                raise ValueError(
                    f"Formato de data inválido: '{date}'. "
                    f"Use YYYY-MM-DD (ex: '2025-01-15') ou timestamp Unix em ms"
                ) from e
        
        raise TypeError(
            f"Tipo de data inválido: {type(date).__name__}. "
            f"Use string (YYYY-MM-DD), int (timestamp Unix em ms) ou None"
        )

    def make_request(
        self, 
        url: str, 
        method: str = 'GET', 
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any
    ) -> requests.Response:
        """
        Faz requisição HTTP com autenticação, rate limiting e retry logic.
        
        Args:
            url: URL da requisição
            method: Método HTTP (GET, POST, etc)
            timeout: Timeout em segundos
            max_retries: Número máximo de tentativas em caso de erro
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Response object
            
        Raises:
            HotmartAPIError: Em caso de erro na requisição
        """
        self._ensure_authenticated()

        # Rate limiting: aguardar se necessário
        if self.rate_remaining <= 0 and self.rate_reset:
            wait_time = self.rate_reset - int(time.time())
            if wait_time > 0:
                logger.warning("Rate limit atingido. Aguardando %ss", wait_time)
                time.sleep(wait_time)
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Implementar retry logic
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method, 
                    url, 
                    headers=headers, 
                    timeout=timeout,
                    **kwargs
                )
                self._update_rate_limit(response.headers)
                
                # Retry em caso de rate limit
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = self.rate_reset or 60
                        logger.warning("Rate limit (429). Tentativa %s/%s. Aguardando %ss", 
                                     attempt + 1, max_retries, wait_time)
                        time.sleep(wait_time)
                        continue
                    else:
                        raise HotmartAPIError("Rate limit excedido após múltiplas tentativas")
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout as exc:
                logger.warning("Timeout na requisição. Tentativa %s/%s", attempt + 1, max_retries)
                if attempt == max_retries - 1:
                    raise HotmartAPIError(f"Timeout após {max_retries} tentativas") from exc
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.RequestException as e:
                logger.error("Erro na requisição: %s", e)
                if attempt == max_retries - 1:
                    raise HotmartAPIError(f"Erro na requisição: {e}") from e
                time.sleep(2 ** attempt)
        
        raise HotmartAPIError("Falha após todas as tentativas")

    def get_sales_history(
        self, 
        max_results: int = 50, 
        page_token: Optional[str] = None, 
        product_id: Optional[str] = None,
        start_date: Union[int, str, None] = None, 
        end_date: Union[int, str, None] = None,
        sales_source: Optional[str] = None, 
        transaction: Optional[str] = None,
        buyer_name: Optional[str] = None, 
        buyer_email: Optional[str] = None,
        transaction_status: Optional[str] = None, 
        payment_type: Optional[str] = None,
        offer_code: Optional[str] = None, 
        commission_as: Optional[str] = None,
        **filters: Any
    ) -> List[Dict[str, Any]]:
        """
        Obtém histórico de vendas com paginação automática.
        
        Args:
            max_results: Número máximo de resultados por página (1-200)
            page_token: Token para paginação
            product_id: Filtrar por ID do produto
            start_date: Data inicial (YYYY-MM-DD ou timestamp Unix em ms)
            end_date: Data final (YYYY-MM-DD ou timestamp Unix em ms)
            sales_source: Fonte da venda (ex: CHECKOUT, SUBSCRIPTION)
            transaction: ID da transação
            buyer_name: Nome do comprador
            buyer_email: Email do comprador
            transaction_status: Status da transação (APPROVED, CANCELLED, etc)
            payment_type: Tipo de pagamento
            offer_code: Código da oferta
            commission_as: Tipo de comissão (PRODUCER, AFFILIATE, CO_PRODUCER)
            **filters: Filtros adicionais
            
        Returns:
            Lista com todos os itens de vendas
            
        Example:
            >>> hotmart = Hotmart()
            >>> # Usando formato de data string
            >>> vendas = hotmart.get_sales_history(
            ...     start_date='2025-01-01',
            ...     end_date='2025-01-31'
            ... )
            >>> # Ou usando timestamp (ainda suportado)
            >>> vendas = hotmart.get_sales_history(
            ...     start_date=1704067200000,
            ...     end_date=1706745599000
            ... )
        """
        url = 'https://developers.hotmart.com/payments/api/v1/sales/history'
        all_items: List[Dict[str, Any]] = []
        
        # Converter datas para timestamp se necessário
        start_date_ts = self._convert_date_to_timestamp(start_date)
        end_date_ts = self._convert_date_to_timestamp(end_date)

        while True:
            params = {
                'max_results': max_results,
                'page_token': page_token,
                'product_id': product_id,
                'start_date': start_date_ts,
                'end_date': end_date_ts,
                'sales_source': sales_source,
                'transaction': transaction,
                'buyer_name': buyer_name,
                'buyer_email': buyer_email,
                'transaction_status': transaction_status,
                'payment_type': payment_type,
                'offer_code': offer_code,
                'commission_as': commission_as,
                **filters
            }
            
            # Remover parâmetros None
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                response = self.make_request(url, method='GET', params=params)
                data = response.json()
                items = data.get('items', [])
                all_items.extend(items)
                
                logger.info("Obtidos %s itens. Total: %s", len(items), len(all_items))
                
                # Verificar próxima página
                page_info = data.get('page_info', {})
                page_token = page_info.get('next_page_token')
                
                if not page_token:
                    break
                    
            except HotmartAPIError as e:
                logger.error("Erro ao obter histórico de vendas: %s", e)
                break

        return all_items

    def get_sales_participants(
        self, 
        max_results: int = 50, 
        page_token: Optional[str] = None,
        product_id: Optional[str] = None,
        start_date: Union[int, str, None] = None, 
        end_date: Union[int, str, None] = None,
        buyer_email: Optional[str] = None,
        sales_source: Optional[str] = None, 
        transaction: Optional[str] = None,
        buyer_name: Optional[str] = None,
        affiliate_name: Optional[str] = None, 
        commission_as: Optional[str] = None,
        transaction_status: Optional[str] = None,
        **filters: Any
    ) -> List[Dict[str, Any]]:
        """
        Obtém participantes de vendas com paginação automática.
        
        Args:
            max_results: Número máximo de resultados por página
            page_token: Token para paginação
            product_id: Filtrar por ID do produto
            start_date: Data inicial (YYYY-MM-DD ou timestamp Unix em ms)
            end_date: Data final (YYYY-MM-DD ou timestamp Unix em ms)
            buyer_email: Email do comprador
            sales_source: Fonte da venda
            transaction: ID da transação
            buyer_name: Nome do comprador
            affiliate_name: Nome do afiliado
            commission_as: Tipo de comissão
            transaction_status: Status da transação
            **filters: Filtros adicionais
            
        Returns:
            Lista com todos os participantes
        """
        url = 'https://developers.hotmart.com/payments/api/v1/sales/users'
        all_items: List[Dict[str, Any]] = []
        
        # Converter datas para timestamp se necessário
        start_date_ts = self._convert_date_to_timestamp(start_date)
        end_date_ts = self._convert_date_to_timestamp(end_date)

        while True:
            params = {
                'max_results': max_results,
                'page_token': page_token,
                'product_id': product_id,
                'start_date': start_date_ts,
                'end_date': end_date_ts,
                'buyer_email': buyer_email,
                'sales_source': sales_source,
                'transaction': transaction,
                'buyer_name': buyer_name,
                'affiliate_name': affiliate_name,
                'commission_as': commission_as,
                'transaction_status': transaction_status,
                **filters
            }
            
            # Remover parâmetros None
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                response = self.make_request(url, method='GET', params=params)
                data = response.json()
                items = data.get('items', [])
                all_items.extend(items)
                
                logger.info("Obtidos %s participantes. Total: %s", len(items), len(all_items))
                
                # Verificar próxima página
                page_info = data.get('page_info', {})
                page_token = page_info.get('next_page_token')
                
                if not page_token:
                    break
                    
            except HotmartAPIError as e:
                logger.error("Erro ao obter participantes: %s", e)
                break

        return all_items

    def get_sales_commissions(
        self, 
        max_results: int = 50, 
        page_token: Optional[str] = None,
        product_id: Optional[str] = None,
        start_date: Union[int, str, None] = None, 
        end_date: Union[int, str, None] = None,
        transaction: Optional[str] = None,
        commission_as: Optional[str] = None, 
        transaction_status: Optional[str] = None,
        **filters: Any
    ) -> List[Dict[str, Any]]:
        """
        Obtém comissões de vendas com paginação automática.
        
        Args:
            max_results: Número máximo de resultados por página
            page_token: Token para paginação
            product_id: Filtrar por ID do produto
            start_date: Data inicial (YYYY-MM-DD ou timestamp Unix em ms)
            end_date: Data final (YYYY-MM-DD ou timestamp Unix em ms)
            transaction: ID da transação
            commission_as: Tipo de comissão
            transaction_status: Status da transação
            **filters: Filtros adicionais
            
        Returns:
            Lista com todas as comissões
        """
        url = 'https://developers.hotmart.com/payments/api/v1/sales/commissions'
        all_items: List[Dict[str, Any]] = []
        
        # Converter datas para timestamp se necessário
        start_date_ts = self._convert_date_to_timestamp(start_date)
        end_date_ts = self._convert_date_to_timestamp(end_date)

        while True:
            params = {
                'max_results': max_results,
                'page_token': page_token,
                'product_id': product_id,
                'start_date': start_date_ts,
                'end_date': end_date_ts,
                'transaction': transaction,
                'commission_as': commission_as,
                'transaction_status': transaction_status,
                **filters
            }
            
            # Remover parâmetros None
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                response = self.make_request(url, method='GET', params=params)
                data = response.json()
                items = data.get('items', [])
                all_items.extend(items)
                
                logger.info("Obtidas %s comissões. Total: %s", len(items), len(all_items))
                
                # Verificar próxima página
                page_info = data.get('page_info', {})
                page_token = page_info.get('next_page_token')
                
                if not page_token:
                    break
                    
            except HotmartAPIError as e:
                logger.error("Erro ao obter comissões: %s", e)
                break

        return all_items

    def get_students(
        self, 
        subdomain: Optional[str] = None,
        email: Optional[str] = None,
        max_results: int = 50,
        page_token: Optional[str] = None, 
        role: Optional[str] = None,
        plus_access: Optional[str] = None,
        status: Optional[str] = None, 
        student_type: Optional[str] = None,
        **filters: Any
    ) -> List[Dict[str, Any]]:
        """
        Obtém alunos do Hotmart Club com paginação automática.
        
        Args:
            subdomain: Subdomínio do Club. Se None, usa HOTMART_SUBDOMAIN
            email: Filtrar por email específico
            max_results: Número máximo de resultados por página
            page_token: Token para paginação
            role: Papel do usuário (STUDENT, ADMIN, etc)
            plus_access: Filtrar por acesso Plus
            status: Status do aluno (ACTIVE, INACTIVE, etc)
            student_type: Tipo de estudante
            **filters: Filtros adicionais
            
        Returns:
            Lista com todos os alunos
            
        Raises:
            ValueError: Se subdomain não for fornecido e HOTMART_SUBDOMAIN não estiver configurado
        """
        # Obter subdomain de variável de ambiente se não fornecido
        if not subdomain:
            subdomain = os.getenv('HOTMART_SUBDOMAIN')
            if not subdomain:
                raise ValueError(
                    "Subdomain não fornecido. Passe como parâmetro ou "
                    "configure a variável de ambiente HOTMART_SUBDOMAIN"
                )
        
        url = f'https://developers.hotmart.com/club/api/v1/users?subdomain={subdomain}'
        all_items: List[Dict[str, Any]] = []

        while True:
            params = {
                'max_results': max_results,
                'page_token': page_token,
                'email': email,
                'role': role,
                'plus_access': plus_access,
                'status': status,
                'type': student_type,
                **filters
            }
            
            # Remover parâmetros None
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                response = self.make_request(url, method='GET', params=params)
                data = response.json()
                items = data.get('items', [])
                all_items.extend(items)
                
                logger.info("Obtidos %s alunos. Total: %s", len(items), len(all_items))
                
                # Verificar próxima página
                page_info = data.get('page_info', {})
                page_token = page_info.get('next_page_token')
                
                if not page_token:
                    break
                    
            except HotmartAPIError as e:
                logger.error("Erro ao obter alunos: %s", e)
                break

        return all_items