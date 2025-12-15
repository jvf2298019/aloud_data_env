"""
Utilitários para integração com a API do Tally.

Este módulo fornece uma classe para interagir com a API do Tally,
gerenciando autenticação, rate limiting e paginação automática.

Documentação da API: https://developers.tally.so/api-reference/introduction
"""

import os
import sys
import requests
import logging
import time
from typing import Optional, List, Dict, Any

# Configurar logging
logger = logging.getLogger(__name__)


class TallyAPIError(Exception):
    """Exceção customizada para erros da API Tally"""


class Tally:
    """
    Cliente para interação com a API Tally.
    
    Gerencia autenticação, rate limiting e paginação automática.
    Requer a variável de ambiente TALLY_API_KEY com a chave de API.
    
    Base URL: https://api.tally.so
    Rate Limit: 100 requisições por minuto
    
    Exemplo de uso:
        >>> tally = Tally()
        >>> formularios = tally.get_forms()
        >>> submissoes = tally.get_form_submissions('form_id_aqui')
    """
    
    BASE_URL = 'https://api.tally.so'
    RATE_LIMIT = 100  # requisições por minuto
    
    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Inicializa o cliente Tally.
        
        Args:
            api_key: Chave de API do Tally. Se None, busca em TALLY_API_KEY
            
        Raises:
            ValueError: Se a chave de API não for fornecida
        """
        self.api_key: Optional[str] = api_key or os.getenv('TALLY_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Chave de API do Tally não encontrada. "
                "Forneça como parâmetro ou configure a variável TALLY_API_KEY"
            )
        
        # Controle de rate limiting
        self.rate_remaining: int = self.RATE_LIMIT
        self.rate_reset_time: Optional[float] = None
        self.request_times: List[float] = []
    
    def _get_headers(self, version: Optional[str] = None) -> Dict[str, str]:
        """
        Retorna os headers para requisições à API.
        
        Args:
            version: Versão da API (formato: YYYY-MM-DD). Se None, usa versão padrão
            
        Returns:
            Dicionário com headers de autenticação
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        if version:
            headers['tally-version'] = version
        
        return headers
    
    def _check_rate_limit(self) -> None:
        """
        Verifica e gerencia rate limiting (100 req/minuto).
        Aguarda se necessário para não exceder o limite.
        """
        now = time.time()
        one_minute_ago = now - 60
        
        # Remove requisições antigas (mais de 1 minuto)
        self.request_times = [t for t in self.request_times if t > one_minute_ago]
        
        # Verifica se atingiu o limite
        if len(self.request_times) >= self.RATE_LIMIT:
            oldest_request = self.request_times[0]
            wait_time = 60 - (now - oldest_request) + 1  # +1 segundo de margem
            
            if wait_time > 0:
                logger.warning(
                    "Rate limit de %d req/min atingido. Aguardando %.1fs...",
                    self.RATE_LIMIT, wait_time
                )
                time.sleep(wait_time)
                # Limpa histórico após esperar
                self.request_times = []
        
        # Registra esta requisição
        self.request_times.append(now)
    
    def _update_rate_limit(self, headers: Dict[str, str]) -> None:
        """
        Atualiza informações de rate limiting a partir dos headers de resposta.
        
        Args:
            headers: Headers da resposta HTTP
        """
        try:
            if 'X-RateLimit-Remaining' in headers:
                self.rate_remaining = int(headers['X-RateLimit-Remaining'])
            
            if 'X-RateLimit-Reset' in headers:
                self.rate_reset_time = float(headers['X-RateLimit-Reset'])
                
        except (ValueError, TypeError) as e:
            logger.warning("Erro ao atualizar rate limit: %s", e)
    
    def make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        max_retries: int = 3,
        version: Optional[str] = None
    ) -> requests.Response:
        """
        Faz requisição HTTP para a API do Tally com retry logic.
        
        Args:
            endpoint: Endpoint da API (ex: '/forms', '/forms/{id}')
            method: Método HTTP (GET, POST, PUT, DELETE)
            params: Parâmetros da query string
            json_data: Dados JSON para enviar no body
            timeout: Timeout em segundos
            max_retries: Número máximo de tentativas em caso de erro
            version: Versão da API (formato: YYYY-MM-DD)
            
        Returns:
            Response object
            
        Raises:
            TallyAPIError: Em caso de erro na requisição
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers(version=version)
        
        # Implementar retry logic
        for attempt in range(max_retries):
            try:
                # Verificar rate limiting antes da requisição
                self._check_rate_limit()
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=timeout
                )
                
                # Atualizar rate limit
                self._update_rate_limit(response.headers)
                
                # Tratar rate limit da API
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 60  # Aguardar 1 minuto
                        logger.warning(
                            "Rate limit (429). Tentativa %d/%d. Aguardando %ds...",
                            attempt + 1, max_retries, wait_time
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise TallyAPIError(
                            "Rate limit excedido após múltiplas tentativas"
                        )
                
                # Verificar sucesso
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                logger.warning("Timeout na requisição. Tentativa %d/%d", attempt + 1, max_retries)
                if attempt == max_retries - 1:
                    raise TallyAPIError(f"Timeout após {max_retries} tentativas")
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.RequestException as e:
                logger.error("Erro na requisição: %s", e)
                if attempt == max_retries - 1:
                    raise TallyAPIError(f"Erro na requisição: {e}") from e
                time.sleep(2 ** attempt)
        
        raise TallyAPIError("Falha após todas as tentativas")
    
    # ==================== MÉTODOS DE FORMULÁRIOS ====================
    
    def get_forms(self) -> List[Dict[str, Any]]:
        """
        Obtém lista de todos os formulários.
        
        Returns:
            Lista com todos os formulários
            
        Example:
            >>> tally = Tally()
            >>> forms = tally.get_forms()
            >>> print(f"Total de formulários: {len(forms)}")
        """
        try:
            logger.info("Obtendo lista de formulários...")
            response = self.make_request('/forms', method='GET')
            data = response.json()
            
            # A API retorna um objeto com 'data' contendo array de formulários
            forms = data.get('data', []) if isinstance(data, dict) else data
            logger.info("✓ %d formulário(s) obtido(s)", len(forms))
            
            return forms
            
        except TallyAPIError as e:
            logger.error("Erro ao obter formulários: %s", e)
            raise
    
    def get_form(self, form_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um formulário específico.
        
        Args:
            form_id: ID do formulário
            
        Returns:
            Dicionário com detalhes do formulário
            
        Example:
            >>> tally = Tally()
            >>> form = tally.get_form('abc123')
            >>> print(form['name'])
        """
        try:
            logger.info("Obtendo formulário %s...", form_id)
            response = self.make_request(f'/forms/{form_id}', method='GET')
            data = response.json()
            
            logger.info("✓ Formulário '%s' obtido", data.get('name', form_id))
            return data
            
        except TallyAPIError as e:
            logger.error("Erro ao obter formulário %s: %s", form_id, e)
            raise
    
    def get_form_submissions(
        self,
        form_id: str,
        since: Optional[str] = None,
        until: Optional[str] = None,
        status: Optional[str] = None,
        fields: Optional[List[str]] = None,
        sort: str = 'desc',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtém submissões de um formulário com paginação automática.
        
        Args:
            form_id: ID do formulário
            since: Data inicial (ISO 8601 ou timestamp Unix)
            until: Data final (ISO 8601 ou timestamp Unix)
            status: Filtrar por status (ex: 'COMPLETED', 'IN_PROGRESS')
            fields: Lista de campos específicos para retornar
            sort: Ordenação ('asc' ou 'desc', padrão: 'desc')
            limit: Número de resultados por página (max: 100)
            
        Returns:
            Lista com todas as submissões do formulário
            
        Example:
            >>> tally = Tally()
            >>> submissoes = tally.get_form_submissions(
            ...     'abc123',
            ...     since='2024-01-01',
            ...     status='COMPLETED'
            ... )
            >>> print(f"Total de submissões: {len(submissoes)}")
        """
        all_submissions: List[Dict[str, Any]] = []
        page = 1
        after = None  # Cursor para paginação
        
        try:
            while True:
                # Preparar parâmetros
                params: Dict[str, Any] = {
                    'limit': min(limit, 100),  # Máximo 100 por página
                    'sort': sort
                }
                
                if since:
                    params['since'] = since
                if until:
                    params['until'] = until
                if status:
                    params['status'] = status
                if fields:
                    params['fields'] = ','.join(fields)
                if after:
                    params['after'] = after
                
                # Mostrar progresso
                sys.stdout.write(
                    f"\rProcessando página {page} de submissões... "
                    f"(Total: {len(all_submissions)})"
                )
                sys.stdout.flush()
                
                # Fazer requisição
                response = self.make_request(
                    f'/forms/{form_id}/submissions',
                    method='GET',
                    params=params
                )
                data = response.json()
                
                # Extrair submissões
                if isinstance(data, dict):
                    submissions = data.get('data', [])
                    pagination = data.get('pagination', {})
                    after = pagination.get('after')
                else:
                    submissions = data if isinstance(data, list) else []
                    after = None
                
                all_submissions.extend(submissions)
                logger.info(
                    "Página %d: %d submissões. Total: %d",
                    page, len(submissions), len(all_submissions)
                )
                
                # Verificar se há mais páginas
                if not after or not submissions:
                    sys.stdout.write(
                        f"\r✓ Concluído: {page} página(s) processada(s). "
                        f"Total de {len(all_submissions)} submissões obtidas.\n"
                    )
                    sys.stdout.flush()
                    break
                
                page += 1
                
        except TallyAPIError as e:
            sys.stdout.write("\n")
            sys.stdout.flush()
            logger.error("Erro ao obter submissões do formulário %s: %s", form_id, e)
            
        return all_submissions
    
    def create_form(
        self,
        form_data: Dict[str, Any],
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um novo formulário.
        
        Args:
            form_data: Dados do formulário (estrutura conforme API)
            version: Versão da API (formato: YYYY-MM-DD)
            
        Returns:
            Dicionário com dados do formulário criado
            
        Example:
            >>> tally = Tally()
            >>> form_data = {
            ...     "status": "PUBLISHED",
            ...     "blocks": [
            ...         {
            ...             "type": "FORM_TITLE",
            ...             "payload": {
            ...                 "title": "Meu Formulário",
            ...                 "html": "Meu Formulário"
            ...             }
            ...         }
            ...     ]
            ... }
            >>> form = tally.create_form(form_data)
            >>> print(f"Formulário criado: {form['id']}")
        """
        try:
            logger.info("Criando novo formulário...")
            response = self.make_request(
                '/forms',
                method='POST',
                json_data=form_data,
                version=version
            )
            data = response.json()
            
            form_id = data.get('id', 'unknown')
            logger.info("✓ Formulário criado com ID: %s", form_id)
            
            return data
            
        except TallyAPIError as e:
            logger.error("Erro ao criar formulário: %s", e)
            raise
    
    def update_form(
        self,
        form_id: str,
        form_data: Dict[str, Any],
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Atualiza um formulário existente.
        
        Args:
            form_id: ID do formulário
            form_data: Dados para atualizar
            version: Versão da API (formato: YYYY-MM-DD)
            
        Returns:
            Dicionário com dados do formulário atualizado
            
        Example:
            >>> tally = Tally()
            >>> updates = {"status": "CLOSED"}
            >>> form = tally.update_form('abc123', updates)
        """
        try:
            logger.info("Atualizando formulário %s...", form_id)
            response = self.make_request(
                f'/forms/{form_id}',
                method='PUT',
                json_data=form_data,
                version=version
            )
            data = response.json()
            
            logger.info("✓ Formulário %s atualizado", form_id)
            return data
            
        except TallyAPIError as e:
            logger.error("Erro ao atualizar formulário %s: %s", form_id, e)
            raise
    
    def delete_form(self, form_id: str) -> bool:
        """
        Deleta um formulário.
        
        Args:
            form_id: ID do formulário
            
        Returns:
            True se deletado com sucesso
            
        Example:
            >>> tally = Tally()
            >>> success = tally.delete_form('abc123')
        """
        try:
            logger.info("Deletando formulário %s...", form_id)
            self.make_request(f'/forms/{form_id}', method='DELETE')
            
            logger.info("✓ Formulário %s deletado", form_id)
            return True
            
        except TallyAPIError as e:
            logger.error("Erro ao deletar formulário %s: %s", form_id, e)
            raise
    
    # ==================== MÉTODOS DE WEBHOOKS ====================
    
    def create_webhook(
        self,
        form_id: str,
        url: str,
        event_types: Optional[List[str]] = None,
        signing_secret: Optional[str] = None,
        http_headers: Optional[List[Dict[str, str]]] = None,
        external_subscriber: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um novo webhook para um formulário.
        
        Args:
            form_id: ID do formulário
            url: URL do endpoint que receberá os eventos
            event_types: Tipos de eventos (padrão: ['FORM_RESPONSE'])
                Opções: 'FORM_RESPONSE', 'FORM_UPDATED', etc.
            signing_secret: Segredo para validação de assinatura
            http_headers: Headers customizados para enviar no webhook
                Formato: [{"name": "X-Custom", "value": "valor"}]
            external_subscriber: Identificador externo do subscriber
            
        Returns:
            Dicionário com dados do webhook criado
            
        Example:
            >>> tally = Tally()
            >>> webhook = tally.create_webhook(
            ...     form_id='abc123',
            ...     url='https://meusite.com/webhook',
            ...     event_types=['FORM_RESPONSE'],
            ...     signing_secret='meu_segredo_123'
            ... )
            >>> print(f"Webhook ID: {webhook['id']}")
        """
        try:
            logger.info("Criando webhook para formulário %s...", form_id)
            
            # Preparar payload
            payload: Dict[str, Any] = {
                'formId': form_id,
                'url': url,
                'eventTypes': event_types or ['FORM_RESPONSE']
            }
            
            if signing_secret:
                payload['signingSecret'] = signing_secret
            if http_headers:
                payload['httpHeaders'] = http_headers
            if external_subscriber:
                payload['externalSubscriber'] = external_subscriber
            
            response = self.make_request(
                '/webhooks',
                method='POST',
                json_data=payload
            )
            data = response.json()
            
            webhook_id = data.get('id', 'unknown')
            logger.info("✓ Webhook criado com ID: %s", webhook_id)
            
            return data
            
        except TallyAPIError as e:
            logger.error("Erro ao criar webhook: %s", e)
            raise
    
    def list_webhooks(
        self,
        page: int = 1,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        Lista todos os webhooks configurados.
        
        Args:
            page: Número da página (padrão: 1)
            limit: Itens por página (padrão: 25, máximo: 100)
            
        Returns:
            Dicionário com lista de webhooks e informações de paginação
            
        Example:
            >>> tally = Tally()
            >>> webhooks = tally.list_webhooks(page=1, limit=50)
            >>> for webhook in webhooks['data']:
            ...     print(f"{webhook['id']}: {webhook['url']}")
        """
        try:
            logger.info("Listando webhooks...")
            
            params = {
                'page': page,
                'limit': min(limit, 100)  # Máximo 100
            }
            
            response = self.make_request(
                '/webhooks',
                method='GET',
                params=params
            )
            data = response.json()
            
            webhooks = data.get('data', []) if isinstance(data, dict) else []
            logger.info("✓ %d webhook(s) encontrado(s)", len(webhooks))
            
            return data
            
        except TallyAPIError as e:
            logger.error("Erro ao listar webhooks: %s", e)
            raise
    
    def get_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um webhook específico.
        
        Args:
            webhook_id: ID do webhook
            
        Returns:
            Dicionário com dados do webhook
            
        Example:
            >>> tally = Tally()
            >>> webhook = tally.get_webhook('webhook_abc123')
            >>> print(f"URL: {webhook['url']}")
        """
        try:
            logger.info("Obtendo webhook %s...", webhook_id)
            response = self.make_request(f'/webhooks/{webhook_id}', method='GET')
            data = response.json()
            
            logger.info("✓ Webhook obtido: %s", data.get('url', 'N/A'))
            return data
            
        except TallyAPIError as e:
            logger.error("Erro ao obter webhook %s: %s", webhook_id, e)
            raise
    
    def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        signing_secret: Optional[str] = None,
        http_headers: Optional[List[Dict[str, str]]] = None,
        external_subscriber: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Atualiza um webhook existente.
        
        Args:
            webhook_id: ID do webhook
            url: Nova URL do endpoint
            event_types: Novos tipos de eventos
            signing_secret: Novo segredo de assinatura
            http_headers: Novos headers customizados
            external_subscriber: Novo identificador externo
            enabled: Ativar/desativar webhook
            
        Returns:
            Dicionário com dados do webhook atualizado
            
        Example:
            >>> tally = Tally()
            >>> webhook = tally.update_webhook(
            ...     webhook_id='webhook_abc123',
            ...     url='https://novosite.com/webhook',
            ...     enabled=True
            ... )
        """
        try:
            logger.info("Atualizando webhook %s...", webhook_id)
            
            # Preparar payload apenas com campos fornecidos
            payload: Dict[str, Any] = {}
            
            if url is not None:
                payload['url'] = url
            if event_types is not None:
                payload['eventTypes'] = event_types
            if signing_secret is not None:
                payload['signingSecret'] = signing_secret
            if http_headers is not None:
                payload['httpHeaders'] = http_headers
            if external_subscriber is not None:
                payload['externalSubscriber'] = external_subscriber
            if enabled is not None:
                payload['enabled'] = enabled
            
            response = self.make_request(
                f'/webhooks/{webhook_id}',
                method='PUT',
                json_data=payload
            )
            data = response.json()
            
            logger.info("✓ Webhook %s atualizado", webhook_id)
            return data
            
        except TallyAPIError as e:
            logger.error("Erro ao atualizar webhook %s: %s", webhook_id, e)
            raise
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """
        Deleta um webhook.
        
        Args:
            webhook_id: ID do webhook
            
        Returns:
            True se deletado com sucesso
            
        Example:
            >>> tally = Tally()
            >>> success = tally.delete_webhook('webhook_abc123')
            >>> print(f"Deletado: {success}")
        """
        try:
            logger.info("Deletando webhook %s...", webhook_id)
            self.make_request(f'/webhooks/{webhook_id}', method='DELETE')
            
            logger.info("✓ Webhook %s deletado", webhook_id)
            return True
            
        except TallyAPIError as e:
            logger.error("Erro ao deletar webhook %s: %s", webhook_id, e)
            raise
    
    def list_webhook_events(
        self,
        webhook_id: str,
        page: int = 1,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        Lista eventos de um webhook específico.
        
        Args:
            webhook_id: ID do webhook
            page: Número da página (padrão: 1)
            limit: Itens por página (padrão: 25, máximo: 100)
            
        Returns:
            Dicionário com lista de eventos e informações de paginação
            
        Example:
            >>> tally = Tally()
            >>> events = tally.list_webhook_events('webhook_abc123')
            >>> for event in events['data']:
            ...     print(f"Evento {event['id']}: {event['status']}")
        """
        try:
            logger.info("Listando eventos do webhook %s...", webhook_id)
            
            params = {
                'page': page,
                'limit': min(limit, 100)
            }
            
            response = self.make_request(
                f'/webhooks/{webhook_id}/events',
                method='GET',
                params=params
            )
            data = response.json()
            
            events = data.get('data', []) if isinstance(data, dict) else []
            logger.info("✓ %d evento(s) encontrado(s)", len(events))
            
            return data
            
        except TallyAPIError as e:
            logger.error("Erro ao listar eventos do webhook %s: %s", webhook_id, e)
            raise
    
    def retry_webhook_event(
        self,
        webhook_id: str,
        event_id: str
    ) -> Dict[str, Any]:
        """
        Reenvia um evento de webhook que falhou.
        
        Args:
            webhook_id: ID do webhook
            event_id: ID do evento para reenviar
            
        Returns:
            Dicionário com resultado do reenvio
            
        Example:
            >>> tally = Tally()
            >>> result = tally.retry_webhook_event(
            ...     webhook_id='webhook_abc123',
            ...     event_id='event_xyz789'
            ... )
            >>> print(f"Status: {result['status']}")
        """
        try:
            logger.info("Reenviando evento %s do webhook %s...", event_id, webhook_id)
            
            response = self.make_request(
                f'/webhooks/{webhook_id}/events/{event_id}',
                method='POST'
            )
            
            # Pode retornar vazio em caso de sucesso
            try:
                data = response.json()
            except Exception:
                data = {'status': 'success'}
            
            logger.info("✓ Evento %s reenviado", event_id)
            return data
            
        except TallyAPIError as e:
            logger.error("Erro ao reenviar evento %s: %s", event_id, e)
            raise
    
    def validate_webhook_signature(
        self,
        payload: str,
        signature: str,
        signing_secret: str
    ) -> bool:
        """
        Valida a assinatura de um webhook recebido.
        
        Args:
            payload: Corpo da requisição (string JSON)
            signature: Assinatura recebida no header X-Tally-Signature
            signing_secret: Segredo configurado no webhook
            
        Returns:
            True se a assinatura for válida
            
        Example:
            >>> tally = Tally()
            >>> # Em seu endpoint de webhook:
            >>> payload = request.body.decode('utf-8')
            >>> signature = request.headers.get('X-Tally-Signature')
            >>> if tally.validate_webhook_signature(payload, signature, 'seu_segredo'):
            ...     print("Webhook válido!")
            ... else:
            ...     print("Webhook inválido!")
        """
        import hmac
        import hashlib
        
        try:
            # Calcular HMAC-SHA256
            expected_signature = hmac.new(
                signing_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Comparação segura contra timing attacks
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if is_valid:
                logger.info("✓ Assinatura do webhook válida")
            else:
                logger.warning("⚠ Assinatura do webhook inválida!")
            
            return is_valid
            
        except (TypeError, AttributeError, ValueError) as e:
            logger.error("Erro ao validar assinatura: %s", e)
            return False


def get_tally_client() -> Tally:
    """
    Helper function para obter uma instância do cliente Tally.
    
    Returns:
        Instância configurada do cliente Tally
        
    Example:
        >>> tally = get_tally_client()
        >>> forms = tally.get_forms()
    """
    return Tally()
