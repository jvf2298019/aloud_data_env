"""
Utilitários para conexões e queries SQL
"""

import pandas as pd
from sqlalchemy import create_engine, text
from typing import Optional, Dict, Any
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Carrega variáveis de ambiente de forma robusta
# Tenta diferentes caminhos possíveis para o .env
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent  # Sobe dois níveis (src -> raiz)
_env_paths = [
    _project_root / 'config' / '.env',  # Caminho absoluto a partir deste arquivo
    Path('config/.env'),  # Caminho relativo da raiz do projeto
    Path('../config/.env'),  # Caminho relativo de src/
    Path('.env'),  # .env na raiz do projeto
]

# Tenta carregar de cada caminho possível
_env_loaded = False
_env_file_used = None
for _env_path in _env_paths:
    if _env_path.exists():
        load_dotenv(_env_path)
        _env_loaded = True
        _env_file_used = str(_env_path.resolve())
        break


def load_query_from_file(
    query_name: str,
    queries_dir: Optional[str] = None
) -> str:
    """
    Carrega uma query SQL de um arquivo .sql na pasta queries
    
    Args:
        query_name: Nome do arquivo da query (com ou sem extensão .sql)
        queries_dir: Diretório onde estão os arquivos de queries (opcional)
                    Se não especificado, busca automaticamente em:
                    1. ./queries (se executar da raiz do projeto)
                    2. ../queries (se executar de dentro de src/ ou notebooks/)
        
    Returns:
        String contendo o conteúdo da query SQL
        
    Raises:
        FileNotFoundError: Se o arquivo não for encontrado
        ValueError: Se o arquivo estiver vazio
        
    Example:
        >>> # Para usar com execute_query
        >>> db = DatabaseConnection()
        >>> query = load_query_from_file('buscar_usuarios')
        >>> df = db.execute_query(query, {"idade": 18})
        
        >>> # Para usar com execute_update
        >>> query = load_query_from_file('atualizar_status.sql')
        >>> linhas = db.execute_update(query, {"status": "ativo", "id": 123})
    """
    # Remove .sql se o usuário passou
    if query_name.endswith('.sql'):
        query_name = query_name[:-4]
    
    # Se não especificou o diretório, tenta encontrar automaticamente
    if queries_dir is None:
        # Tenta diferentes caminhos relativos
        possible_paths = [
            Path("queries"),      # Se executar da raiz do projeto
            Path("../queries"),   # Se executar de src/ ou notebooks/
            Path(__file__).parent.parent / "queries"  # Caminho absoluto a partir deste arquivo
        ]
        
        queries_path = None
        for path in possible_paths:
            if path.exists() and path.is_dir():
                queries_path = path
                break
        
        if queries_path is None:
            raise FileNotFoundError(
                f"Pasta 'queries' não encontrada. Procurei em: {[str(p) for p in possible_paths]}"
            )
    else:
        queries_path = Path(queries_dir)
    
    # Constrói o caminho do arquivo
    query_file = queries_path / f"{query_name}.sql"
    
    # Verifica se o arquivo existe
    if not query_file.exists():
        # Lista arquivos disponíveis para ajudar o usuário
        available_queries = list(queries_path.glob("*.sql"))
        if available_queries:
            available_names = [q.stem for q in available_queries]
            raise FileNotFoundError(
                f"Query '{query_name}.sql' não encontrada em '{queries_dir}'.\n"
                f"Queries disponíveis: {', '.join(available_names)}"
            )
        else:
            raise FileNotFoundError(
                f"Query '{query_name}.sql' não encontrada em '{queries_dir}'.\n"
                f"A pasta queries está vazia."
            )
    
    # Lê e retorna o conteúdo do arquivo
    with open(query_file, 'r', encoding='utf-8') as f:
        query = f.read().strip()
    
    if not query:
        raise ValueError(f"O arquivo '{query_name}.sql' está vazio")
    
    return query


class DatabaseConnection:
    """
    Classe para gerenciar conexões e operações com banco de dados
    """
    
    def __init__(
        self,
        db_type: str = 'postgresql',
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Inicializa a conexão com o banco de dados
        
        Args:
            db_type: Tipo do banco ('postgresql', 'mysql', 'sqlite')
            host: Endereço do servidor
            port: Porta de conexão
            database: Nome do banco de dados
            username: Nome de usuário
            password: Senha (caracteres especiais como @, :, / são automaticamente escapados)
            
        Note:
            - Caracteres especiais na senha (@, :, /, etc) são tratados automaticamente via URL encoding
            - Não é necessário escapar manualmente a senha
            
        Example:
            >>> db = DatabaseConnection(
            ...     db_type='postgresql',
            ...     host='localhost',
            ...     port=5432,
            ...     database='meu_banco',
            ...     username='usuario',
            ...     password='senha@123'  # @ na senha é tratado automaticamente
            ... )
        """
        # Tenta pegar credenciais do ambiente se não foram fornecidas
        self.db_type = db_type
        raw_host = host or os.getenv('DB_HOST')
        raw_port = port or os.getenv('DB_PORT')
        self.database = database or os.getenv('DB_NAME')
        raw_username = username or os.getenv('DB_USER')
        self.password = password or os.getenv('DB_PASSWORD')
        
        # Trata caso onde o host contém username (formato: user@host)
        # Isso corrige erros comuns de configuração onde o host vem como "user@ip"
        if raw_host and '@' in str(raw_host):
            # Separa username e host
            parts = str(raw_host).split('@', 1)
            if len(parts) == 2:
                extracted_username = parts[0]
                extracted_host = parts[1]
                
                # DEBUG: mostra o que foi detectado
                import warnings
                warnings.warn(
                    f"\n⚠️  ATENÇÃO: DB_HOST contém username (ou senha com @)!\n"
                    f"   DB_HOST original: {raw_host}\n"
                    f"   Username extraído: {extracted_username}\n"
                    f"   Host extraído: {extracted_host}\n"
                    f"   DB_USER: {raw_username}\n"
                    f"   DICA: Se a senha tiver caracteres especiais (@,:,/), isso é normal.\n"
                    f"         O código já faz URL encoding automaticamente.\n"
                    f"   Se for erro de configuração, corrija o .env:\n"
                    f"   DB_HOST={extracted_host}\n"
                    f"   DB_USER={extracted_username}\n",
                    UserWarning
                )
                
                # Usa os valores extraídos
                self.host = extracted_host
                # Se não tem username definido, usa o extraído
                self.username = raw_username or extracted_username
            else:
                self.host = raw_host
                self.username = raw_username
        else:
            self.host = raw_host or 'localhost'
            self.username = raw_username
        
        # Converte port para int se necessário
        if raw_port:
            self.port = int(raw_port) if not isinstance(raw_port, int) else raw_port
        else:
            self.port = None
        
        # Validação para bancos não-sqlite
        if self.db_type != 'sqlite':
            missing_vars = []
            if not self.host:
                missing_vars.append('DB_HOST ou host')
            if not self.port:
                missing_vars.append('DB_PORT ou port')
            if not self.database:
                missing_vars.append('DB_NAME ou database')
            if not self.username:
                missing_vars.append('DB_USER ou username')
            if not self.password:
                missing_vars.append('DB_PASSWORD ou password')
            
            if missing_vars:
                raise ValueError(
                    f"Credenciais de banco de dados faltando: {', '.join(missing_vars)}.\n"
                    f"Configure as variáveis de ambiente no arquivo config/.env ou "
                    f"passe os parâmetros diretamente no construtor."
                )
        
        # Cria a connection string
        if self.db_type == 'sqlite':
            self.connection_string = f'sqlite:///{self.database}'
            self.engine = create_engine(self.connection_string)
        else:
            # URL-encode username e password para lidar com caracteres especiais (@, :, /, etc)
            # Isso é ESSENCIAL quando a senha contém caracteres especiais como @
            encoded_username = quote_plus(str(self.username)) if self.username else ''
            encoded_password = quote_plus(str(self.password)) if self.password else ''
            
            # Constrói a connection string com credenciais escapadas
            self.connection_string = (
                f'{self.db_type}://{encoded_username}:{encoded_password}'
                f'@{self.host}:{self.port}/{self.database}'
            )
            
            # Cria o engine
            self.engine = create_engine(self.connection_string)
    
    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Executa uma query SQL e retorna os resultados como DataFrame
        
        Args:
            query: Query SQL a ser executada (SELECT)
            params: Parâmetros para a query (opcional)
            
        Returns:
            DataFrame com os resultados da query
            
        Example:
            >>> db = DatabaseConnection()
            >>> df = db.execute_query("SELECT * FROM usuarios WHERE idade > :idade", {"idade": 18})
            >>> print(df.head())
        """
        try:
            with self.engine.connect() as conn:
                if params:
                    result = pd.read_sql(text(query), conn, params=params)
                else:
                    result = pd.read_sql(text(query), conn)
                return result
        except Exception as e:
            raise Exception(f"Erro ao executar query: {str(e)}") from e
    
    def execute_update(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Executa uma query de UPDATE, INSERT ou DELETE
        
        Args:
            query: Query SQL a ser executada (UPDATE, INSERT, DELETE)
            params: Parâmetros para a query (opcional)
            
        Returns:
            Número de linhas afetadas
            
        Example:
            >>> db = DatabaseConnection()
            >>> linhas = db.execute_update(
            ...     "UPDATE usuarios SET status = :status WHERE id = :id",
            ...     {"status": "ativo", "id": 123}
            ... )
            >>> print(f"Linhas afetadas: {linhas}")
        """
        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                conn.commit()
                return result.rowcount
        except Exception as e:
            raise Exception(f"Erro ao executar update: {str(e)}") from e
    
    def execute_batch_update(
        self,
        query: str,
        params_list: list[Dict[str, Any]],
        batch_size: int = 1000,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Executa múltiplos updates em lote de forma eficiente
        
        Esta função é muito mais eficiente que executar updates individuais em loop,
        pois usa uma única transação e conexão para processar múltiplos registros.
        
        Args:
            query: Query SQL parametrizada (UPDATE, INSERT, DELETE)
            params_list: Lista de dicionários com parâmetros para cada update
            batch_size: Tamanho do lote para processamento (padrão: 1000)
            show_progress: Se True, mostra progresso da operação
            
        Returns:
            Dicionário com estatísticas da operação:
            - total_records: Total de registros processados
            - total_affected: Total de linhas afetadas no banco
            - batches: Número de lotes processados
            - success: Número de registros com sucesso
            - failed: Número de registros que falharam
            - errors: Lista de erros (se houver)
            
        Example:
            >>> db = DatabaseConnection()
            >>> updates = [
            ...     {"id": 1, "status": "ativo"},
            ...     {"id": 2, "status": "inativo"},
            ...     {"id": 3, "status": "ativo"}
            ... ]
            >>> resultado = db.execute_batch_update(
            ...     "UPDATE usuarios SET status = :status WHERE id = :id",
            ...     updates,
            ...     batch_size=1000
            ... )
            >>> print(f"Processados: {resultado['success']}, Falhas: {resultado['failed']}")
        """
        import time
        from datetime import datetime
        
        total_records = len(params_list)
        if total_records == 0:
            return {
                'total_records': 0,
                'total_affected': 0,
                'batches': 0,
                'success': 0,
                'failed': 0,
                'errors': []
            }
        
        total_affected = 0
        success_count = 0
        failed_count = 0
        errors = []
        batches_count = 0
        
        start_time = time.time()
        
        if show_progress:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando batch update...")
            print(f"Total de registros: {total_records}")
            print(f"Tamanho do lote: {batch_size}")
        
        try:
            with self.engine.begin() as conn:  # Usa begin() para transação automática
                # Processa em lotes
                for i in range(0, total_records, batch_size):
                    batch = params_list[i:i + batch_size]
                    batch_num = i // batch_size + 1
                    total_batches = (total_records + batch_size - 1) // batch_size
                    
                    try:
                        # ExecuteMany - processa todos os registros do lote de uma vez
                        result = conn.execute(text(query), batch)
                        affected = result.rowcount
                        
                        total_affected += affected
                        success_count += len(batch)
                        batches_count += 1
                        
                        if show_progress:
                            progress = min(i + batch_size, total_records)
                            percent = (progress / total_records) * 100
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                                  f"Lote {batch_num}/{total_batches} - "
                                  f"Processados: {progress}/{total_records} ({percent:.1f}%) - "
                                  f"Linhas afetadas neste lote: {affected}")
                    
                    except Exception as e:
                        failed_count += len(batch)
                        error_msg = f"Erro no lote {batch_num}: {str(e)}"
                        errors.append(error_msg)
                        if show_progress:
                            print(f"⚠️  {error_msg}")
                        # Continua processando os próximos lotes
                        continue
                
                # Commit automático ao sair do bloco 'with'
        
        except Exception as e:
            raise Exception(f"Erro crítico ao executar batch update: {str(e)}") from e
        
        elapsed_time = time.time() - start_time
        
        if show_progress:
            print(f"\n{'='*60}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Batch update concluído!")
            print(f"Tempo total: {elapsed_time:.2f}s")
            print(f"Registros processados: {success_count}/{total_records}")
            print(f"Linhas afetadas no banco: {total_affected}")
            print(f"Taxa: {total_records/elapsed_time:.1f} registros/segundo")
            if failed_count > 0:
                print(f"⚠️  Falhas: {failed_count}")
            print(f"{'='*60}\n")
        
        return {
            'total_records': total_records,
            'total_affected': total_affected,
            'batches': batches_count,
            'success': success_count,
            'failed': failed_count,
            'errors': errors,
            'elapsed_time': elapsed_time
        }
    
    def update_from_dataframe(
        self,
        df: pd.DataFrame,
        query: str,
        column_mapping: Dict[str, str],
        filter_column: Optional[str] = None,
        batch_size: int = 1000,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Executa updates em lote a partir de um DataFrame
        
        Função otimizada para atualizar registros no banco usando dados de um DataFrame.
        Converte automaticamente o DataFrame em uma lista de parâmetros e executa
        os updates em lotes eficientes.
        
        Args:
            df: DataFrame com os dados para atualizar
            query: Query SQL parametrizada (use :nome_coluna para parâmetros)
            column_mapping: Mapeamento de colunas do DataFrame para parâmetros da query
                           Exemplo: {"id_df": "conversion_id", "dados": "new_conversion_raw_info"}
            filter_column: Nome da coluna para filtrar apenas registros não-nulos (opcional)
            batch_size: Tamanho do lote para processamento (padrão: 1000)
            show_progress: Se True, mostra progresso da operação
            
        Returns:
            Dicionário com estatísticas da operação (mesmo formato de execute_batch_update)
            
        Example:
            >>> db = DatabaseConnection()
            >>> df = pd.DataFrame({
            ...     'user_id': [1, 2, 3],
            ...     'new_status': ['ativo', 'inativo', 'ativo']
            ... })
            >>> resultado = db.update_from_dataframe(
            ...     df=df,
            ...     query="UPDATE usuarios SET status = :status WHERE id = :id",
            ...     column_mapping={"user_id": "id", "new_status": "status"}
            ... )
            
            >>> # Exemplo com JSON (como seu caso)
            >>> import json
            >>> df_updates = df_t2[df_t2['new_conversion_raw_info'].notnull()]
            >>> resultado = db.update_from_dataframe(
            ...     df=df_updates,
            ...     query=load_query_from_file('update_conversion_t2_raw_info'),
            ...     column_mapping={
            ...         "id": "conversion_id",
            ...         "new_conversion_raw_info": "new_conversion_raw_info"
            ...     },
            ...     json_columns=["new_conversion_raw_info"]
            ... )
        """
        import json
        
        # Filtra o DataFrame se especificado
        if filter_column:
            df_filtered = df[df[filter_column].notnull()].copy()
            if show_progress:
                print(f"Filtrando por coluna '{filter_column}': "
                      f"{len(df_filtered)}/{len(df)} registros")
        else:
            df_filtered = df.copy()
        
        if len(df_filtered) == 0:
            if show_progress:
                print("Nenhum registro para atualizar após filtro.")
            return {
                'total_records': 0,
                'total_affected': 0,
                'batches': 0,
                'success': 0,
                'failed': 0,
                'errors': []
            }
        
        # Converte DataFrame em lista de parâmetros
        params_list = []
        for _, row in df_filtered.iterrows():
            params = {}
            for df_col, query_param in column_mapping.items():
                value = row.get(df_col)
                
                # Serializa automaticamente dicts/lists para JSON
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                
                params[query_param] = value
            
            params_list.append(params)
        
        # Executa batch update
        return self.execute_batch_update(
            query=query,
            params_list=params_list,
            batch_size=batch_size,
            show_progress=show_progress
        )
    
    def save_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = 'replace'
    ) -> None:
        """
        Salva um DataFrame em uma tabela do banco de dados
        
        Args:
            df: DataFrame a ser salvo
            table_name: Nome da tabela de destino
            if_exists: Ação se a tabela existir ('fail', 'replace', 'append')
            
        Example:
            >>> db = DatabaseConnection()
            >>> df = pd.DataFrame({'nome': ['João', 'Maria'], 'idade': [25, 30]})
            >>> db.save_dataframe(df, 'usuarios', if_exists='append')
        """
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
        except Exception as e:
            raise Exception(f"Erro ao salvar DataFrame: {str(e)}") from e
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """
        Obtém informações sobre as colunas de uma tabela
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            DataFrame com informações das colunas
            
        Example:
            >>> db = DatabaseConnection()
            >>> info = db.get_table_info('usuarios')
            >>> print(info)
        """
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = :table_name
        """
        return self.execute_query(query, {"table_name": table_name})
    
    def list_tables(self) -> list:
        """
        Lista todas as tabelas do banco de dados
        
        Returns:
            Lista com nomes das tabelas
            
        Example:
            >>> db = DatabaseConnection()
            >>> tabelas = db.list_tables()
            >>> print(tabelas)
        """
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def execute_query_from_file(
        self,
        query_name: str,
        params: Optional[Dict[str, Any]] = None,
        queries_dir: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Carrega uma query SQL de um arquivo e a executa, retornando os resultados como DataFrame
        
        Este método combina load_query_from_file() e execute_query() em uma única chamada,
        facilitando a execução de queries armazenadas em arquivos .sql.
        
        Args:
            query_name: Nome do arquivo da query (com ou sem extensão .sql)
            params: Parâmetros para a query (opcional)
            queries_dir: Diretório onde estão os arquivos de queries (opcional)
                        Se não especificado, busca automaticamente em:
                        1. ./queries (se executar da raiz do projeto)
                        2. ../queries (se executar de dentro de src/ ou notebooks/)
            
        Returns:
            DataFrame com os resultados da query
            
        Raises:
            FileNotFoundError: Se o arquivo da query não for encontrado
            ValueError: Se o arquivo estiver vazio
            Exception: Se houver erro na execução da query
            
        Example:
            >>> db = DatabaseConnection()
            >>> # Executa query do arquivo 'buscar_usuarios.sql'
            >>> df = db.execute_query_from_file('buscar_usuarios', {"idade": 18})
            >>> print(df.head())
            
            >>> # Especificando diretório customizado
            >>> df = db.execute_query_from_file(
            ...     'relatorio_vendas',
            ...     params={"ano": 2024},
            ...     queries_dir='/path/to/custom/queries'
            ... )
        """
        # Carrega a query do arquivo
        query = load_query_from_file(query_name, queries_dir)
        
        # Executa a query e retorna o resultado
        return self.execute_query(query, params)
    
    def close(self):
        """
        Fecha a conexão com o banco de dados
        """
        self.engine.dispose()
    
    def __enter__(self):
        """Suporte para context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fecha a conexão ao sair do context manager"""
        self.close()
    
    def __repr__(self):
        return f"DatabaseConnection(db_type='{self.db_type}', host='{self.host}', database='{self.database}')"

