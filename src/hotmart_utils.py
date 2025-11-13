import os
import requests
import logging
from datetime import datetime, timedelta
import time
from typing import Optional, List, Dict, Any, Union

# Configurar logging
logger = logging.getLogger(__name__)


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