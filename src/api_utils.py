"""
Utilitários para requisições a APIs externas
"""

import requests
import httpx
import pandas as pd
from typing import Dict, Any, Optional, List
import time
from functools import wraps


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator para tentar novamente em caso de falha
    
    Args:
        max_retries: Número máximo de tentativas
        delay: Tempo de espera entre tentativas (segundos)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                    continue
            raise last_exception
        return wrapper
    return decorator


@retry_on_failure(max_retries=3)
def make_request(
    url: str,
    method: str = 'GET',
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> requests.Response:
    """
    Faz uma requisição HTTP
    
    Args:
        url: URL da API
        method: Método HTTP ('GET', 'POST', 'PUT', 'DELETE')
        params: Parâmetros da query string
        headers: Cabeçalhos HTTP
        data: Dados do corpo (form data)
        json: Dados do corpo (JSON)
        timeout: Timeout em segundos
        
    Returns:
        Objeto Response
    """
    response = requests.request(
        method=method,
        url=url,
        params=params,
        headers=headers,
        data=data,
        json=json,
        timeout=timeout
    )
    response.raise_for_status()
    return response


def get_json(url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """
    Faz uma requisição GET e retorna JSON
    
    Args:
        url: URL da API
        params: Parâmetros da query string
        **kwargs: Argumentos adicionais para requests
        
    Returns:
        Dicionário com resposta JSON
    """
    response = make_request(url, method='GET', params=params, **kwargs)
    return response.json()


def post_json(
    url: str,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Faz uma requisição POST e retorna JSON
    
    Args:
        url: URL da API
        data: Dados do corpo (form data)
        json: Dados do corpo (JSON)
        **kwargs: Argumentos adicionais para requests
        
    Returns:
        Dicionário com resposta JSON
    """
    response = make_request(url, method='POST', data=data, json=json, **kwargs)
    return response.json()


async def async_make_request(
    url: str,
    method: str = 'GET',
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> httpx.Response:
    """
    Faz uma requisição HTTP assíncrona usando httpx
    
    Args:
        url: URL da API
        method: Método HTTP
        params: Parâmetros da query string
        headers: Cabeçalhos HTTP
        json: Dados JSON
        timeout: Timeout em segundos
        
    Returns:
        Objeto Response do httpx
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            json=json
        )
        response.raise_for_status()
        return response


async def fetch_multiple_urls(urls: List[str], **kwargs) -> List[Dict[str, Any]]:
    """
    Faz múltiplas requisições assíncronas
    
    Args:
        urls: Lista de URLs
        **kwargs: Argumentos adicionais para as requisições
        
    Returns:
        Lista com respostas JSON
    """
    import asyncio
    
    async def fetch_one(url):
        response = await async_make_request(url, **kwargs)
        return response.json()
    
    tasks = [fetch_one(url) for url in urls]
    return await asyncio.gather(*tasks)


def paginated_request(
    url: str,
    page_param: str = 'page',
    per_page_param: str = 'per_page',
    per_page: int = 100,
    max_pages: Optional[int] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Faz requisições paginadas e retorna todos os resultados
    
    Args:
        url: URL base da API
        page_param: Nome do parâmetro de página
        per_page_param: Nome do parâmetro de itens por página
        per_page: Número de itens por página
        max_pages: Número máximo de páginas (None para todas)
        **kwargs: Argumentos adicionais para requests
        
    Returns:
        Lista com todos os resultados
    """
    all_results = []
    page = 1
    
    while True:
        if max_pages and page > max_pages:
            break
        
        params = kwargs.get('params', {})
        params[page_param] = page
        params[per_page_param] = per_page
        kwargs['params'] = params
        
        response = get_json(url, **kwargs)
        
        # Adapte esta lógica conforme a estrutura da API
        if isinstance(response, list):
            results = response
        elif isinstance(response, dict) and 'results' in response:
            results = response['results']
        elif isinstance(response, dict) and 'data' in response:
            results = response['data']
        else:
            results = [response]
        
        if not results:
            break
        
        all_results.extend(results)
        page += 1
    
    return all_results


def response_to_dataframe(response: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Converte resposta JSON para DataFrame
    
    Args:
        response: Lista de dicionários da resposta da API
        
    Returns:
        DataFrame com os dados
    """
    return pd.DataFrame(response)

