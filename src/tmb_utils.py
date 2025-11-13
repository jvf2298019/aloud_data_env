import os
import requests
import logging
from datetime import datetime
import time
from typing import Optional, List, Dict, Any

# Configurar logging
logger = logging.getLogger(__name__)


class TMBAPIError(Exception):
    """Exceção customizada para erros da API TMB"""


class TMB:
    """
    Cliente para interação com a API TMB Educação.
    
    Gerencia autenticação via Bearer Token e fornece métodos para:
    - Consultar pedidos efetivados
    - Obter detalhes de pedidos
    - Listar produtos cadastrados
    - Criar e listar ofertas
    
    Requer a seguinte variável de ambiente:
    - TMB_API_TOKEN
    
    Documentação oficial:
    https://info.tmbeducacao.com.br/portal-do-produtor/central-de-ajuda/produto/integracoes/tmb-api
    """
    
    BASE_URL = "https://api.tmbeducacao.com.br"
    
    def __init__(self) -> None:
        """
        Inicializa o cliente TMB.
        
        Raises:
            ValueError: Se TMB_API_TOKEN não estiver configurado
        """
        self.api_token: Optional[str] = os.getenv('TMB_API_TOKEN')
        
        # Validar token no init
        if not self.api_token:
            raise ValueError(
                "Token TMB não encontrado. "
                "Configure a variável de ambiente TMB_API_TOKEN"
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Retorna os headers padrão para requisições.
        
        Returns:
            Dict com headers incluindo Authorization Bearer Token
        """
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    def make_request(
        self, 
        endpoint: str,
        method: str = 'GET',
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any
    ) -> requests.Response:
        """
        Faz requisição HTTP com tratamento de erros e retry logic.
        
        Args:
            endpoint: Endpoint da API (ex: '/api/pedidos')
            method: Método HTTP (GET, POST, etc)
            timeout: Timeout em segundos
            max_retries: Número máximo de tentativas em caso de erro
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Response object
            
        Raises:
            TMBAPIError: Em caso de erro na requisição
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
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
                
                # Retry em caso de rate limit
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 60  # Aguardar 1 minuto
                        logger.warning("Rate limit (429). Tentativa %s/%s. Aguardando %ss",
                                     attempt + 1, max_retries, wait_time)
                        time.sleep(wait_time)
                        continue
                    else:
                        raise TMBAPIError("Rate limit excedido após múltiplas tentativas")
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout as exc:
                logger.warning("Timeout na requisição. Tentativa %s/%s", attempt + 1, max_retries)
                if attempt == max_retries - 1:
                    raise TMBAPIError(f"Timeout após {max_retries} tentativas") from exc
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.RequestException as e:
                logger.error("Erro na requisição: %s", e)
                if attempt == max_retries - 1:
                    raise TMBAPIError(f"Erro na requisição: {e}") from e
                time.sleep(2 ** attempt)
        
        raise TMBAPIError("Falha após todas as tentativas")
    
    def get_pedidos(
        self,
        produto_id: Optional[int] = None,
        data_inicio: Optional[str] = None,
        data_final: Optional[str] = None,
        page_number: int = 1,
        page_size: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Consulta pedidos efetivados com paginação automática.
        
        Args:
            produto_id: ID do produto para filtrar
            data_inicio: Data inicial do filtro (formato: YYYY-MM-DD)
            data_final: Data final do filtro (formato: YYYY-MM-DD)
            page_number: Número da página inicial (padrão: 1)
            page_size: Tamanho da página (padrão: 7)
            
        Returns:
            Lista com todos os pedidos encontrados
            
        Example:
            >>> tmb = TMB()
            >>> pedidos = tmb.get_pedidos(
            ...     produto_id=123,
            ...     data_inicio='2025-01-01',
            ...     data_final='2025-01-31'
            ... )
        """
        all_pedidos: List[Dict[str, Any]] = []
        current_page = page_number
        
        while True:
            params = {
                'produto_id': produto_id,
                'data_inicio': data_inicio,
                'data_final': data_final,
                'pageNumber': current_page,
                'pageSize': page_size
            }
            
            # Remover parâmetros None
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                response = self.make_request('/api/pedidos', method='GET', params=params)
                data = response.json()
                
                # Verificar se é uma lista ou um dict com itens
                if isinstance(data, list):
                    items = data
                else:
                    items = data.get('data', [])
                
                if not items:
                    break
                
                all_pedidos.extend(items)
                logger.info("Obtidos %s pedidos. Total: %s", len(items), len(all_pedidos))
                
                # Verificar se há mais páginas
                if len(items) < page_size:
                    break
                
                current_page += 1
                
            except TMBAPIError as e:
                logger.error("Erro ao obter pedidos: %s", e)
                break
        
        return all_pedidos
    
    def get_pedido_detalhe(self, pedido_id: int) -> Dict[str, Any]:
        """
        Obtém detalhes completos de um pedido específico.
        
        Args:
            pedido_id: ID do pedido
            
        Returns:
            Dict com detalhes do pedido
            
        Raises:
            TMBAPIError: Se o pedido não for encontrado ou houver erro
            
        Example:
            >>> tmb = TMB()
            >>> pedido = tmb.get_pedido_detalhe(1234)
            >>> print(pedido['cliente'])
        """
        try:
            params = {'pedido_id': pedido_id}
            response = self.make_request(
                '/api/pedidos/DetalhePedidoEfetivado',
                method='GET',
                params=params
            )
            
            data = response.json()
            logger.info("Detalhes do pedido %s obtidos com sucesso", pedido_id)
            return data
            
        except TMBAPIError as e:
            logger.error("Erro ao obter detalhes do pedido %s: %s", pedido_id, e)
            raise
    
    def get_produtos(self) -> List[Dict[str, Any]]:
        """
        Lista todos os produtos cadastrados na plataforma TMB.
        
        Returns:
            Lista com todos os produtos cadastrados
            
        Example:
            >>> tmb = TMB()
            >>> produtos = tmb.get_produtos()
            >>> for produto in produtos:
            ...     print(f"{produto['produto_nome']}: {produto['valor_total']}")
        """
        try:
            response = self.make_request('/api/produtos', method='GET')
            data = response.json()
            
            logger.info("Obtidos %s produtos", len(data))
            return data
            
        except TMBAPIError as e:
            logger.error("Erro ao obter produtos: %s", e)
            return []
    
    def criar_oferta(
        self,
        titulo: str,
        produto_id: int,
        valor_principal: float,
        qtd_parcelas: str,
        valor_boleto_entrada: Optional[float] = None,
        vencimento_boleto_entrada: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cadastra uma nova oferta para um produto.
        
        Args:
            titulo: Título da oferta
            produto_id: ID do produto
            valor_principal: Valor do ticket
            qtd_parcelas: Quantidade de parcelas disponíveis
            valor_boleto_entrada: Valor customizado do boleto de entrada (opcional)
            vencimento_boleto_entrada: Data de vencimento do boleto (formato: YYYY-MM-DD).
                                      Deve ser entre 3 e 60 dias após a data atual (opcional)
                                      
        Returns:
            Dict com status e URL da oferta criada
            
        Raises:
            TMBAPIError: Se houver erro ao criar a oferta
            ValueError: Se o vencimento do boleto não estiver no intervalo válido
            
        Example:
            >>> tmb = TMB()
            >>> resultado = tmb.criar_oferta(
            ...     titulo='Promoção Verão',
            ...     produto_id=123,
            ...     valor_principal=299.99,
            ...     qtd_parcelas='12',
            ...     valor_boleto_entrada=50.00,
            ...     vencimento_boleto_entrada='2025-02-15'
            ... )
            >>> print(resultado['url'])
        """
        # Validar data de vencimento se fornecida
        if vencimento_boleto_entrada:
            try:
                data_vencimento = datetime.strptime(vencimento_boleto_entrada, '%Y-%m-%d')
                hoje = datetime.now()
                dias_diferenca = (data_vencimento - hoje).days
                
                if dias_diferenca < 3:
                    raise ValueError("A data de vencimento deve ser pelo menos 3 dias após hoje")
                if dias_diferenca > 60:
                    raise ValueError("A data de vencimento deve ser no máximo 60 dias após hoje")
                    
            except ValueError as e:
                if "does not match format" in str(e):
                    raise ValueError("Data de vencimento deve estar no formato YYYY-MM-DD") from e
                raise
        
        payload = {
            'titulo': titulo,
            'produto_id': produto_id,
            'valor_principal': valor_principal,
            'qtd_parcelas': qtd_parcelas
        }
        
        # Adicionar parâmetros opcionais se fornecidos
        if valor_boleto_entrada is not None:
            payload['valor_boleto_entrada'] = valor_boleto_entrada
        if vencimento_boleto_entrada:
            payload['vencimento_boleto_entrada'] = vencimento_boleto_entrada
        
        try:
            response = self.make_request('/api/ofertas', method='POST', json=payload)
            data = response.json()
            
            logger.info("Oferta '%s' criada com sucesso: %s", titulo, data.get('url', 'N/A'))
            return data
            
        except TMBAPIError as e:
            logger.error("Erro ao criar oferta: %s", e)
            raise
    
    def get_ofertas(self) -> List[Dict[str, Any]]:
        """
        Lista todas as ofertas cadastradas.
        
        Returns:
            Lista com todas as ofertas (título e URL)
            
        Example:
            >>> tmb = TMB()
            >>> ofertas = tmb.get_ofertas()
            >>> for oferta in ofertas:
            ...     print(f"{oferta['titulo']}: {oferta['url']}")
        """
        try:
            response = self.make_request('/api/ofertas', method='GET')
            data = response.json()
            
            logger.info("Obtidas %s ofertas", len(data))
            return data
            
        except TMBAPIError as e:
            logger.error("Erro ao obter ofertas: %s", e)
            return []
    
    def get_pedidos_por_periodo(
        self,
        data_inicio: str,
        data_final: str,
        produto_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Método auxiliar para buscar pedidos em um período específico.
        
        Args:
            data_inicio: Data inicial (formato: YYYY-MM-DD)
            data_final: Data final (formato: YYYY-MM-DD)
            produto_id: ID do produto (opcional)
            
        Returns:
            Lista com pedidos do período
            
        Example:
            >>> tmb = TMB()
            >>> pedidos = tmb.get_pedidos_por_periodo(
            ...     data_inicio='2025-01-01',
            ...     data_final='2025-01-31'
            ... )
        """
        return self.get_pedidos(
            produto_id=produto_id,
            data_inicio=data_inicio,
            data_final=data_final
        )
    
    def get_pedidos_hoje(self, produto_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Método auxiliar para buscar pedidos de hoje.
        
        Args:
            produto_id: ID do produto (opcional)
            
        Returns:
            Lista com pedidos de hoje
            
        Example:
            >>> tmb = TMB()
            >>> pedidos_hoje = tmb.get_pedidos_hoje()
        """
        hoje = datetime.now().strftime('%Y-%m-%d')
        return self.get_pedidos(
            produto_id=produto_id,
            data_inicio=hoje,
            data_final=hoje
        )

