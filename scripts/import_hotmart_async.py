#!/usr/bin/env python3
"""
Script para importação assíncrona de dados da Hotmart para o backend.

Uso:
    python scripts/import_hotmart_async.py

Configuração:
    - Edite as constantes no início do arquivo para ajustar os arquivos CSV
    - O script processa múltiplos arquivos em sequência com 5 workers paralelos
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Adiciona src ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

# Diretório de dados raw (caminho absoluto)
RAW_DATA_DIR = str(ROOT_DIR / "data" / "raw")

from hotmart_utils import read_hotmart_csv, format_hotmart_conversions
from sql_utils import DatabaseConnection

# ============================================================================
# CONFIGURAÇÕES - EDITE AQUI
# ============================================================================

# Arquivos CSV para importar (relativos à pasta data/raw/)
CSV_FILES = [
    {"file": "hotmart.csv", "sep": ";"},
]

# URL do backend
BASE_URL = "https://southamerica-east1-aloud-etl.cloudfunctions.net/identity-resolution-http"

# Chave para controle de duplicatas (evita reimportar registros)
IMPORT_CONTROL_KEY_PATH = "conversion_data.conversion_raw_info.transaction"

# Arquivo de persistência (salva progresso para poder resumir)
PERSISTENCE_FILE = ROOT_DIR / "data" / "interim" / "imported_leads_async.json"

# Verificação no banco de dados (camada adicional de deduplicação)
CHECK_DATABASE = True  # Habilita consulta ao banco para verificar transações já importadas
DB_QUERY = "SELECT transaction FROM views.vw_conversions_type_8"

# Número de workers paralelos
MAX_WORKERS = 5

# Configurações de retry
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # segundos (com backoff exponencial)
TIMEOUT = 30.0  # segundos por requisição

# ============================================================================
# CÓDIGO - NÃO EDITE ABAIXO (a menos que saiba o que está fazendo)
# ============================================================================

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """Estatísticas da importação."""
    total: int = 0
    success: int = 0
    skipped: int = 0
    failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def elapsed_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def records_per_second(self) -> float:
        if self.elapsed_seconds > 0:
            return self.total / self.elapsed_seconds
        return 0.0


class AsyncHotmartImporter:
    """Importador assíncrono de dados da Hotmart."""
    
    def __init__(
        self,
        base_url: str,
        import_control_key_path: str,
        persistence_file: Path,
        max_workers: int = 5,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        db_imported_keys: Optional[set] = None
    ):
        self.base_url = base_url
        self.import_control_key_path = import_control_key_path
        self.persistence_file = persistence_file
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        self.imported_keys: set = set()
        self.db_imported_keys: set = db_imported_keys or set()
        self.stats = ImportStats()
        self._load_persistence()
    
    def _load_persistence(self):
        """Carrega registros já importados do arquivo de persistência."""
        if self.persistence_file.exists():
            try:
                with open(self.persistence_file, "r", encoding="utf-8") as f:
                    self.imported_keys = set(json.load(f))
                logger.info(f"[Persistência] {len(self.imported_keys)} registros no arquivo local")
            except Exception as e:
                logger.warning(f"Erro ao carregar persistência: {e}")
                self.imported_keys = set()
        
        if self.db_imported_keys:
            logger.info(f"[Banco de Dados] {len(self.db_imported_keys)} transações já importadas")
    
    def _save_persistence(self):
        """Salva registros importados."""
        try:
            self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persistence_file, "w", encoding="utf-8") as f:
                json.dump(sorted(list(self.imported_keys)), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar persistência: {e}")
    
    @staticmethod
    def get_deep_key(d: Dict, key_path: str, default: Any = "") -> Any:
        """Busca valor em dicionário pelo key_path (ex: 'a.b.c')."""
        try:
            for key in key_path.split("."):
                d = d[key]
            return d
        except (KeyError, TypeError):
            return default
    
    async def _send_request(
        self,
        session: aiohttp.ClientSession,
        item: Dict[str, Any],
        idx: int,
        total: int,
        semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """Envia uma única requisição com retry."""
        
        import_key = str(self.get_deep_key(item, self.import_control_key_path, "")).strip()
        
        # Validar chave
        if not import_key:
            self.stats.skipped += 1
            return {"status": "skipped", "reason": "chave ausente", "idx": idx}
        
        # Verificar se já foi importado (arquivo de persistência local)
        if import_key in self.imported_keys:
            self.stats.skipped += 1
            return {"status": "skipped", "reason": "já importado (local)", "key": import_key, "idx": idx}
        
        # Verificar se já existe no banco de dados
        if import_key in self.db_imported_keys:
            self.stats.skipped += 1
            # Adiciona ao arquivo local para evitar consulta futura
            self.imported_keys.add(import_key)
            return {"status": "skipped", "reason": "já importado (banco)", "key": import_key, "idx": idx}
        
        async with semaphore:
            for attempt in range(1, self.max_retries + 1):
                try:
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    async with session.post(
                        self.base_url,
                        json=item,
                        headers={"Content-Type": "application/json"},
                        timeout=timeout
                    ) as response:
                        
                        if response.status == 200:
                            self.imported_keys.add(import_key)
                            self._save_persistence()
                            self.stats.success += 1
                            
                            # Progresso inline
                            progress = (idx / total) * 100
                            print(f"\r[{progress:5.1f}%] {self.stats.success} importados | {self.stats.skipped} ignorados | {self.stats.failed} falhas | Atual: {import_key}", end="", flush=True)
                            
                            return {"status": "success", "key": import_key, "idx": idx}
                        else:
                            resp_text = await response.text()
                            logger.warning(f"\nHTTP {response.status} para {import_key}: {resp_text[:100]}")
                            
                except asyncio.TimeoutError:
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * (2 ** (attempt - 1)))
                    continue
                    
                except Exception as e:
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * (2 ** (attempt - 1)))
                    continue
            
            # Todas as tentativas falharam
            self.stats.failed += 1
            logger.error(f"\nFalha após {self.max_retries} tentativas: {import_key}")
            return {"status": "failed", "key": import_key, "idx": idx}
    
    async def import_items(self, items: List[Dict[str, Any]], source_name: str = ""):
        """Importa uma lista de items de forma assíncrona."""
        
        total = len(items)
        self.stats = ImportStats(total=total, start_time=datetime.now())
        
        logger.info(f"{'='*60}")
        logger.info(f"Iniciando importação: {source_name or 'dados'}")
        logger.info(f"Total de registros: {total}")
        logger.info(f"Workers paralelos: {self.max_workers}")
        logger.info(f"{'='*60}")
        
        semaphore = asyncio.Semaphore(self.max_workers)
        
        connector = aiohttp.TCPConnector(limit=self.max_workers * 2)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [
                self._send_request(session, item, idx, total, semaphore)
                for idx, item in enumerate(items, start=1)
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.stats.end_time = datetime.now()
        
        # Linha em branco após progresso inline
        print()
        
        # Resumo
        logger.info(f"{'='*60}")
        logger.info(f"RESUMO - {source_name or 'Importação'}")
        logger.info(f"{'='*60}")
        logger.info(f"Total processado: {self.stats.total}")
        logger.info(f"Sucesso:          {self.stats.success}")
        logger.info(f"Ignorados:        {self.stats.skipped}")
        logger.info(f"Falhas:           {self.stats.failed}")
        logger.info(f"Tempo total:      {self.stats.elapsed_seconds:.2f}s")
        logger.info(f"Velocidade:       {self.stats.records_per_second:.2f} registros/segundo")
        logger.info(f"{'='*60}")
        
        return self.stats


def load_and_prepare_data(csv_config: Dict[str, str]) -> List[Dict[str, Any]]:
    """Carrega e prepara dados de um arquivo CSV."""
    
    file_name = csv_config["file"]
    sep = csv_config.get("sep", ";")
    
    logger.info(f"Carregando: {file_name}")
    
    df = read_hotmart_csv(file_name, data_dir=RAW_DATA_DIR, sep=sep)
    logger.info(f"  -> {len(df)} linhas no CSV")
    
    # format_hotmart_conversions retorna lista de dicts
    conversions = format_hotmart_conversions(df)
    logger.info(f"  -> {len(conversions)} registros formatados")
    
    # Retorna a lista de dicionários diretamente (não precisa do flatten_list_to_df)
    return conversions


def load_db_transactions() -> set:
    """Carrega transações já importadas do banco de dados."""
    if not CHECK_DATABASE:
        return set()
    
    try:
        logger.info("Consultando banco de dados para transações já importadas...")
        db = DatabaseConnection()
        df = db.execute_query(query=DB_QUERY)
        
        if df is not None and not df.empty:
            # Extrai valores únicos da coluna 'transaction', removendo nulos
            transactions = set(df['transaction'].dropna().unique())
            logger.info(f"Encontradas {len(transactions)} transações no banco de dados")
            return transactions
        else:
            logger.info("Nenhuma transação encontrada no banco de dados")
            return set()
            
    except Exception as e:
        logger.warning(f"Erro ao consultar banco de dados: {e}")
        logger.warning("Continuando apenas com verificação do arquivo local...")
        return set()


async def main():
    """Função principal."""
    
    logger.info("="*60)
    logger.info("IMPORTAÇÃO ASSÍNCRONA DE DADOS HOTMART")
    logger.info("="*60)
    
    # Processar cada arquivo CSV
    total_stats = {"success": 0, "skipped": 0, "failed": 0, "total": 0}
    
    for csv_config in CSV_FILES:
        try:
            # Carregar transações já importadas do banco de dados (atualizado para cada arquivo)
            db_transactions = load_db_transactions()
            
            # Criar importador com transações atualizadas do banco
            importer = AsyncHotmartImporter(
                base_url=BASE_URL,
                import_control_key_path=IMPORT_CONTROL_KEY_PATH,
                persistence_file=PERSISTENCE_FILE,
                max_workers=MAX_WORKERS,
                max_retries=MAX_RETRIES,
                retry_delay=RETRY_DELAY,
                timeout=TIMEOUT,
                db_imported_keys=db_transactions
            )
            
            # Carregar dados
            items = load_and_prepare_data(csv_config)
            
            if not items:
                logger.warning(f"Nenhum registro para importar de {csv_config['file']}")
                continue
            
            # Importar
            stats = await importer.import_items(items, source_name=csv_config["file"])
            
            # Acumular estatísticas
            total_stats["success"] += stats.success
            total_stats["skipped"] += stats.skipped
            total_stats["failed"] += stats.failed
            total_stats["total"] += stats.total
            
        except Exception as e:
            logger.error(f"Erro ao processar {csv_config['file']}: {e}")
            continue
    
    # Resumo final
    if len(CSV_FILES) > 1:
        logger.info("")
        logger.info("="*60)
        logger.info("RESUMO FINAL - TODOS OS ARQUIVOS")
        logger.info("="*60)
        logger.info(f"Total processado: {total_stats['total']}")
        logger.info(f"Sucesso:          {total_stats['success']}")
        logger.info(f"Ignorados:        {total_stats['skipped']}")
        logger.info(f"Falhas:           {total_stats['failed']}")
        logger.info("="*60)
    
    logger.info("Importação concluída!")


if __name__ == "__main__":
    asyncio.run(main())
