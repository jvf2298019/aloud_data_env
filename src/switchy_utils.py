"""
Switchy API - Utilitários para integração com a API GraphQL do Switchy

Documentação oficial: https://developers.switchy.io/docs/overview/index
API Endpoint: https://graphql.switchy.io/v1/graphql

Requer variável de ambiente:
    SWITCHY_API_KEY: API key para autenticação
"""

import os
import requests
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


class SwitchyAPI:
    """Cliente para interação com a API GraphQL do Switchy"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente Switchy.
        
        Args:
            api_key: API key para autenticação. Se não fornecida, usa SWITCHY_API_KEY do ambiente.
        
        Raises:
            ValueError: Se a API key não for fornecida nem encontrada no ambiente.
        """
        self.endpoint = "https://graphql.switchy.io/v1/graphql"
        self.api_key = api_key or os.getenv("SWITCHY_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "API key não fornecida. Defina SWITCHY_API_KEY no ambiente "
                "ou passe como parâmetro."
            )
        
        self.headers = {
            "Content-Type": "application/json",
            "Api-Authorization": self.api_key
        }
    
    def _execute_query(
        self, 
        query: str, 
        variables: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Executa uma query GraphQL.
        
        Args:
            query: Query ou mutation GraphQL
            variables: Variáveis da query (opcional)
            timeout: Timeout em segundos (padrão: 30)
        
        Returns:
            Dados retornados pela query
        
        Raises:
            Exception: Se houver erro na requisição ou na resposta GraphQL
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code != 200:
                raise Exception(
                    f"Erro na requisição: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            
            if "errors" in data and data["errors"]:
                raise Exception(f"Erro na resposta GraphQL: {data['errors']}")
            
            return data.get("data", {})
        
        except requests.exceptions.Timeout:
            raise Exception(f"Timeout na requisição após {timeout} segundos")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro na requisição: {str(e)}")
    
    # ========================================================================
    # QUERIES - Consultar Links
    # ========================================================================
    
    def get_links(
        self,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
        order_by: Optional[Dict] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca links da conta Switchy.
        
        Args:
            fields: Lista de campos a retornar. Default: ['id', 'title', 'url', 'extraOptionsLinkRotator']
            limit: Número máximo de resultados (opcional)
            offset: Offset para paginação (default: 0)
            order_by: Ordenação, ex: {'createdDate': 'desc'}
            filters: Filtros no formato Hasura, ex: {'tags': {'_contains': ['bf25']}}
        
        Returns:
            Lista de links
        
        Example:
            >>> api = SwitchyAPI()
            >>> links = api.get_links(limit=10, order_by={'clicks': 'desc'})
            >>> links = api.get_links(filters={'tags': {'_contains': ['promo']}})
        """
        if fields is None:
            fields = ['id', 'title', 'url', 'extraOptionsLinkRotator']
        
        fields_str = '\n      '.join(fields)
        
        # Montar argumentos da query dinamicamente
        args = []
        if filters:
            args.append("where: $where")
        if limit is not None:
            args.append(f"limit: {limit}")
        if offset:
            args.append(f"offset: {offset}")
        if order_by:
            order_str = ", ".join([f"{k}: {v}" for k, v in order_by.items()])
            args.append(f"order_by: {{{order_str}}}")
        
        args_str = ", ".join(args)
        
        # Montar a query com sintaxe GraphQL correta
        query_header = "query GetLinks"
        if filters:
            query_header += "($where: links_bool_exp!)"
        
        # Montar links com ou sem parênteses dependendo se há argumentos
        links_line = f"  links({args_str}) {{" if args_str else "  links {"
        
        query_parts = [
            f"{query_header} {{",
            links_line,
            f"      {fields_str}",
            "  }",
            "}"
        ]
        
        query = "\n".join(query_parts)
        
        variables = {"where": filters} if filters else None
        
        result = self._execute_query(query, variables)
        return result.get("links", [])
    
    def get_link_by_id(
        self,
        link_id: str,
        domain: str,
        fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca um link específico por ID e domínio.
        
        Args:
            link_id: ID do link
            domain: Domínio do link (ex: 'sw.page')
            fields: Campos a retornar
        
        Returns:
            Dados do link ou None se não encontrado
        
        Example:
            >>> link = api.get_link_by_id('abc123', 'sw.page')
        """
        if fields is None:
            fields = [
                'id', 'domain', 'uniq', 'name', 'title', 'url', 
                'clicks', 'tags', 'createdDate',
                'linkExpiration', 'extraOptionsLinkRotator'
            ]
        
        fields_str = '\n      '.join(fields)
        
        query = f"""
        query GetLinkById($domain: String!, $id: String!) {{
          links_by_pk(domain: $domain, id: $id) {{
            {fields_str}
          }}
        }}
        """
        
        variables = {"domain": domain, "id": link_id}
        result = self._execute_query(query, variables)
        return result.get("links_by_pk")
    
    def search_links(
        self,
        search_text: str,
        search_in: List[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Busca links por texto (case insensitive).
        
        Args:
            search_text: Texto a buscar
            search_in: Campos onde buscar. Default: ['name', 'title', 'url']
            limit: Número máximo de resultados
        
        Returns:
            Lista de links encontrados
        
        Example:
            >>> links = api.search_links('black friday')
        """
        if search_in is None:
            search_in = ['name', 'title', 'url']
        
        # Montar condições OR para cada campo
        or_conditions = []
        for field in search_in:
            or_conditions.append({field: {"_ilike": f"%{search_text}%"}})
        
        filters = {"_or": or_conditions}
        
        return self.get_links(
            filters=filters,
            limit=limit,
            order_by={'createdDate': 'desc'}
        )
    
    def get_links_by_tag(
        self,
        tags: Union[str, List[str]],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca links por tag(s).
        
        Args:
            tags: Tag ou lista de tags
            limit: Número máximo de resultados
        
        Returns:
            Lista de links com as tags especificadas
        
        Example:
            >>> links = api.get_links_by_tag('bf25')
            >>> links = api.get_links_by_tag(['bf25', 'promo'])
        """
        if isinstance(tags, str):
            tags = [tags]
        
        filters = {"tags": {"_contains": tags}}
        return self.get_links(filters=filters, limit=limit)
    
    def get_top_links(
        self,
        limit: int = 10,
        min_clicks: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Busca os links mais clicados.
        
        Args:
            limit: Número de links a retornar
            min_clicks: Número mínimo de cliques
        
        Returns:
            Lista de links ordenados por cliques
        
        Example:
            >>> top_links = api.get_top_links(limit=10, min_clicks=100)
        """
        filters = None
        if min_clicks > 0:
            filters = {"clicks": {"_gt": min_clicks}}
        
        return self.get_links(
            fields=['id', 'name', 'title', 'url', 'clicks', 'domain', 'uniq'],
            filters=filters,
            limit=limit,
            order_by={'clicks': 'desc'}
        )
    
    # ========================================================================
    # MUTATIONS - Atualizar Links
    # ========================================================================
    
    def update_link_url(
        self,
        link_id: str,
        new_url: str,
        deep_linking_enable: bool = False
    ) -> Dict[str, Any]:
        """
        Atualiza a URL de destino de um link.
        
        Args:
            link_id: ID do link
            new_url: Nova URL de destino
            deep_linking_enable: Habilitar deep linking
        
        Returns:
            Resultado da mutation com affected_rows
        
        Example:
            >>> result = api.update_link_url('abc123', 'https://nova-url.com')
            >>> print(f"Links atualizados: {result['affected_rows']}")
        """
        mutation = """
        mutation UpdateLinkUrl($id: String!, $url: String!, $deepLinking: Boolean!) {
          update_links(
            where: {id: {_eq: $id}},
            _set: {url: $url, deepLinkingEnable: $deepLinking}
          ) {
            affected_rows
            returning {
              id
              url
              deepLinkingEnable
            }
          }
        }
        """
        
        variables = {
            "id": link_id,
            "url": new_url,
            "deepLinking": deep_linking_enable
        }
        
        result = self._execute_query(mutation, variables)
        return result.get("update_links", {})
    
    def update_links_bulk(
        self,
        filters: Dict,
        updates: Dict
    ) -> Dict[str, Any]:
        """
        Atualiza múltiplos links de uma vez.
        
        Args:
            filters: Filtros para selecionar links (formato Hasura)
            updates: Campos a atualizar
        
        Returns:
            Resultado com affected_rows e returning
        
        Example:
            >>> result = api.update_links_bulk(
            ...     filters={'tags': {'_contains': ['test']}},
            ...     updates={'url': 'https://nova-url.com'}
            ... )
        """
        mutation = """
        mutation UpdateLinksBulk($where: links_bool_exp!, $set: links_set_input!) {
          update_links(where: $where, _set: $set) {
            affected_rows
            returning {
              id
              name
              url
            }
          }
        }
        """
        
        variables = {
            "where": filters,
            "set": updates
        }
        
        result = self._execute_query(mutation, variables)
        return result.get("update_links", {})
    
    # ========================================================================
    # LINK ROTATOR
    # ========================================================================
    
    def update_link_rotator(
        self,
        link_id: str,
        extra_urls: List[str]
    ) -> Dict[str, Any]:
        """
        Atualiza o Link Rotator de um link.
        
        O link principal (campo 'url') recebe automaticamente o percentual restante.
        
        Args:
            link_id: ID do link
            extra_urls: Lista de URLs extras para rotacionar
        
        Returns:
            Resultado da mutation
        
        Lógica de distribuição:
            - Com N extras, cada extra recebe floor(100 / (N + 1))
            - O principal (url do link) fica com o restante automaticamente
            - Ex: 2 extras → cada extra 33%, principal 34%
        
        Example:
            >>> result = api.update_link_rotator('abc123', [
            ...     'https://url1.com',
            ...     'https://url2.com'
            ... ])
        """
        n = len(extra_urls)
        
        if n <= 0:
            # Sem extras: zera o rotator (100% vai para URL principal)
            rotator = []
        else:
            share = 100 // (n + 1)  # Cota para cada extra
            
            # Fallback: se share <= 0, distribui 1% para cada
            if share <= 0:
                rotator = [{"url": u, "value": 1} for u in extra_urls]
            else:
                rotator = [{"url": u, "value": share} for u in extra_urls]
        
        mutation = """
        mutation UpdateRotator($id: String!, $rotator: jsonb!) {
          update_links(
            where: {id: {_eq: $id}},
            _set: {extraOptionsLinkRotator: $rotator}
          ) {
            affected_rows
            returning {
              id
              extraOptionsLinkRotator
            }
          }
        }
        """
        
        variables = {
            "id": link_id,
            "rotator": rotator
        }
        
        result = self._execute_query(mutation, variables)
        return result.get("update_links", {})
    
    def set_link_rotator_custom(
        self,
        link_id: str,
        urls_with_weights: List[Dict[str, Union[str, int]]]
    ) -> Dict[str, Any]:
        """
        Configura Link Rotator com pesos customizados.
        
        Args:
            link_id: ID do link
            urls_with_weights: Lista de dicts com 'url' e 'value' (percentual)
        
        Returns:
            Resultado da mutation
        
        Example:
            >>> result = api.set_link_rotator_custom('abc123', [
            ...     {'url': 'https://url1.com', 'value': 70},
            ...     {'url': 'https://url2.com', 'value': 30}
            ... ])
        """
        # Validar que os valores somam <= 100
        total = sum(item.get('value', 0) for item in urls_with_weights)
        if total > 100:
            raise ValueError(
                f"A soma dos valores ({total}) não pode exceder 100%. "
                "O link principal receberá o percentual restante."
            )
        
        mutation = """
        mutation UpdateRotator($id: String!, $rotator: jsonb!) {
          update_links(
            where: {id: {_eq: $id}},
            _set: {extraOptionsLinkRotator: $rotator}
          ) {
            affected_rows
            returning {
              id
              extraOptionsLinkRotator
            }
          }
        }
        """
        
        variables = {
            "id": link_id,
            "rotator": urls_with_weights
        }
        
        result = self._execute_query(mutation, variables)
        return result.get("update_links", {})
    
    def clear_link_rotator(self, link_id: str) -> Dict[str, Any]:
        """
        Remove o Link Rotator (100% vai para URL principal).
        
        Args:
            link_id: ID do link
        
        Returns:
            Resultado da mutation
        """
        return self.update_link_rotator(link_id, [])
    
    # ========================================================================
    # LINK EXPIRATION
    # ========================================================================
    
    def set_link_expiration_by_date(
        self,
        link_id: str,
        expiration_date: Union[str, datetime],
        redirect_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configura expiração do link por data.
        
        Args:
            link_id: ID do link
            expiration_date: Data de expiração (ISO string ou datetime)
            redirect_url: URL para redirecionar após expiração (opcional)
        
        Returns:
            Resultado da mutation
        
        Example:
            >>> from datetime import datetime, timedelta
            >>> expiry = datetime.now() + timedelta(days=30)
            >>> result = api.set_link_expiration_by_date(
            ...     'abc123',
            ...     expiry,
            ...     'https://link-expirado.com'
            ... )
        """
        if isinstance(expiration_date, datetime):
            expiration_date = expiration_date.isoformat()
        
        expiration_config = {
            "enabled": True,
            "type": "date",
            "date": expiration_date
        }
        
        if redirect_url:
            expiration_config["redirectUrl"] = redirect_url
        
        mutation = """
        mutation SetExpiration($id: String!, $expiration: jsonb!) {
          update_links(
            where: {id: {_eq: $id}},
            _set: {linkExpiration: $expiration}
          ) {
            affected_rows
            returning {
              id
              linkExpiration
            }
          }
        }
        """
        
        variables = {
            "id": link_id,
            "expiration": expiration_config
        }
        
        result = self._execute_query(mutation, variables)
        return result.get("update_links", {})
    
    def set_link_expiration_by_clicks(
        self,
        link_id: str,
        max_clicks: int,
        redirect_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configura expiração do link por número de cliques.
        
        Args:
            link_id: ID do link
            max_clicks: Número máximo de cliques
            redirect_url: URL para redirecionar após atingir limite
        
        Returns:
            Resultado da mutation
        
        Example:
            >>> result = api.set_link_expiration_by_clicks(
            ...     'abc123',
            ...     1000,
            ...     'https://limite-atingido.com'
            ... )
        """
        expiration_config = {
            "enabled": True,
            "type": "clicks",
            "clicks": max_clicks
        }
        
        if redirect_url:
            expiration_config["redirectUrl"] = redirect_url
        
        mutation = """
        mutation SetExpiration($id: String!, $expiration: jsonb!) {
          update_links(
            where: {id: {_eq: $id}},
            _set: {linkExpiration: $expiration}
          ) {
            affected_rows
            returning {
              id
              linkExpiration
            }
          }
        }
        """
        
        variables = {
            "id": link_id,
            "expiration": expiration_config
        }
        
        result = self._execute_query(mutation, variables)
        return result.get("update_links", {})
    
    def clear_link_expiration(self, link_id: str) -> Dict[str, Any]:
        """
        Remove a configuração de expiração do link.
        
        Args:
            link_id: ID do link
        
        Returns:
            Resultado da mutation
        """
        expiration_config = {"enabled": False}
        
        mutation = """
        mutation ClearExpiration($id: String!, $expiration: jsonb!) {
          update_links(
            where: {id: {_eq: $id}},
            _set: {linkExpiration: $expiration}
          ) {
            affected_rows
          }
        }
        """
        
        variables = {
            "id": link_id,
            "expiration": expiration_config
        }
        
        result = self._execute_query(mutation, variables)
        return result.get("update_links", {})
    
    # ========================================================================
    # OUTROS RECURSOS
    # ========================================================================
    
    def get_domains(self) -> List[Dict[str, Any]]:
        """
        Lista todos os domínios da conta.
        
        Returns:
            Lista de domínios
        """
        query = """
        query GetDomains {
          domains {
            name
            ownerId
          }
        }
        """
        
        result = self._execute_query(query)
        return result.get("domains", [])
    
    def get_folders(self) -> List[Dict[str, Any]]:
        """
        Lista todas as pastas da conta.
        
        Returns:
            Lista de pastas
        """
        query = """
        query GetFolders {
          folders {
            id
            name
            description
          }
        }
        """
        
        result = self._execute_query(query)
        return result.get("folders", [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas gerais da conta.
        
        Returns:
            Dict com estatísticas (total_links, total_clicks, avg_clicks, etc.)
        """
        query = """
        query GetStats {
          links {
            clicks
          }
        }
        """
        
        result = self._execute_query(query)
        links = result.get("links", [])
        
        total_links = len(links)
        total_clicks = sum(link.get('clicks', 0) or 0 for link in links)
        avg_clicks = total_clicks / total_links if total_links > 0 else 0
        zero_clicks = sum(1 for link in links if (link.get('clicks') or 0) == 0)
        
        return {
            "total_links": total_links,
            "total_clicks": total_clicks,
            "average_clicks": round(avg_clicks, 2),
            "links_without_clicks": zero_clicks,
            "percentage_without_clicks": round(zero_clicks / total_links * 100, 2) if total_links > 0 else 0
        }


# ============================================================================
# FUNÇÕES STANDALONE (Compatibilidade com código existente)
# ============================================================================

def get_links() -> List[Dict[str, Any]]:
    """
    Busca os links via GraphQL na API Switchy.
    Requer a variável de ambiente 'SWITCHY_API_KEY' para autenticação.
    
    Returns:
        Lista de links com campos: title, url, id, extraOptionsLinkRotator
    """
    api = SwitchyAPI()
    return api.get_links(
        fields=['title', 'url', 'id', 'extraOptionsLinkRotator']
    )


def update_link_url(
    link_id: str,
    new_url: str,
    deepLinkingEnable: bool = False
) -> Dict[str, Any]:
    """
    Atualiza a URL de um link específico via GraphQL na API Switchy.
    
    Args:
        link_id: ID do link
        new_url: Nova URL de destino
        deepLinkingEnable: Se o deepLinkingEnable está ativo
    
    Returns:
        Resultado da mutation
    """
    api = SwitchyAPI()
    return api.update_link_url(link_id, new_url, deepLinkingEnable)


def update_link_rotator(link_id: str, extra_urls: List[str]) -> Dict:
    """
    Atualiza o campo extraOptionsLinkRotator de um link na Switchy.
    
    Args:
        link_id: ID do link original (principal já está configurado no próprio link)
        extra_urls: lista com N URLs extras (páginas do rotator)
    
    Regras:
        - Com N extras, cada extra recebe floor(100 / (N + 1))
        - O principal fica automaticamente com o restante (não é enviado no array)
        - Ex.: 2 extras -> cada extra 33; principal 34 (implícito)
    
    Returns:
        Resultado da mutation
    """
    api = SwitchyAPI()
    return api.update_link_rotator(link_id, extra_urls)
