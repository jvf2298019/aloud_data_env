"""
Módulo para importação assíncrona de dados para o backend.

Permite enviar múltiplos dataframes em paralelo com controle de workers concorrentes,
persistência de progresso e retry automático.
"""

import asyncio
import aiohttp
import json
import os
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ImportConfig:
    """Configuração para importação assíncrona."""
    base_url: str
    import_control_key_path: str
    persistence_file: str = "imported_leads.json"
    max_workers: int = 5
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    headers: Dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json"})


class AsyncDataImporter:
    """
    Importador assíncrono de dados com suporte a múltiplos dataframes.
    
    Features:
    - Processamento paralelo com limite de workers
    - Persistência de progresso para resumir importações
    - Retry automático com backoff exponencial
    - Suporte a múltiplos dataframes
    - Callbacks para progresso e erros
    """
    
    def __init__(self, config: ImportConfig):
        self.config = config
        self.imported_keys: set = set()
        self.responses: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self._load_persistence()
        
    def _load_persistence(self):
        """Carrega registros já importados do arquivo de persistência."""
        if os.path.exists(self.config.persistence_file):
            try:
                with open(self.config.persistence_file, "r", encoding="utf-8") as f:
                    self.imported_keys = set(json.load(f))
                logger.info(f"Carregados {len(self.imported_keys)} registros já importados")
            except Exception as e:
                logger.warning(f"Erro ao carregar persistência: {e}")
                self.imported_keys = set()
    
    def _save_persistence(self):
        """Salva registros importados no arquivo de persistência."""
        try:
            with open(self.config.persistence_file, "w", encoding="utf-8") as f:
                json.dump(sorted(list(self.imported_keys)), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar persistência: {e}")
    
    @staticmethod
    def get_deep_key(d: Dict, key_path: str, default: Any = "") -> Any:
        """
        Busca valor em dicionário pelo key_path em formato dot.
        
        Exemplo: 'conversion_data.conversion_raw_info.transaction'
        """
        try:
            for key in key_path.split("."):
                d = d[key]
            return d
        except (KeyError, TypeError):
            return default
    
    async def _send_single_request(
        self,
        session: aiohttp.ClientSession,
        item: Dict[str, Any],
        idx: int,
        total: int,
        semaphore: asyncio.Semaphore,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Envia uma única requisição com retry automático."""
        
        import_key = str(self.get_deep_key(item, self.config.import_control_key_path, "")).strip()
        
        if not import_key:
            result = {
                "status": "skipped",
                "reason": "chave de controle ausente ou inválida",
                "idx": idx
            }
            logger.warning(f"[{idx}/{total}] Registro ignorado: chave de controle ausente")
            return result
        
        if import_key in self.imported_keys:
            result = {
                "status": "skipped",
                "reason": "já importado anteriormente",
                "key": import_key,
                "idx": idx
            }
            logger.debug(f"[{idx}/{total}] Registro já importado: {import_key}")
            return result
        
        async with semaphore:
            for attempt in range(1, self.config.max_retries + 1):
                try:
                    timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                    async with session.post(
                        self.config.base_url,
                        json=item,
                        headers=self.config.headers,
                        timeout=timeout
                    ) as response:
                        try:
                            resp_json = await response.json()
                        except Exception:
                            resp_json = await response.text()
                        
                        result = {
                            "status": "success" if response.status == 200 else "error",
                            "status_code": response.status,
                            "response": resp_json,
                            "key": import_key,
                            "idx": idx
                        }
                        
                        if response.status == 200:
                            self.imported_keys.add(import_key)
                            self._save_persistence()
                            logger.info(f"[{idx}/{total}] ✓ Importado: {import_key}")
                            
                            if progress_callback:
                                progress_callback(idx, total, import_key, "success")
                        else:
                            logger.warning(f"[{idx}/{total}] ✗ Erro HTTP {response.status}: {import_key}")
                        
                        return result
                        
                except asyncio.TimeoutError:
                    logger.warning(f"[{idx}/{total}] Timeout (tentativa {attempt}/{self.config.max_retries}): {import_key}")
                    if attempt < self.config.max_retries:
                        await asyncio.sleep(self.config.retry_delay * (2 ** (attempt - 1)))
                        
                except Exception as e:
                    logger.error(f"[{idx}/{total}] Erro (tentativa {attempt}/{self.config.max_retries}): {e}")
                    if attempt < self.config.max_retries:
                        await asyncio.sleep(self.config.retry_delay * (2 ** (attempt - 1)))
            
            # Todas as tentativas falharam
            result = {
                "status": "failed",
                "reason": "max retries exceeded",
                "key": import_key,
                "idx": idx
            }
            self.errors.append(result)
            return result
    
    async def import_dataframe(
        self,
        items: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Importa uma lista de items (dataframe convertido) de forma assíncrona.
        
        Args:
            items: Lista de dicionários para enviar ao backend
            progress_callback: Função opcional para reportar progresso
            
        Returns:
            Dicionário com estatísticas da importação
        """
        total = len(items)
        logger.info(f"Iniciando importação de {total} registros com {self.config.max_workers} workers")
        
        semaphore = asyncio.Semaphore(self.config.max_workers)
        start_time = datetime.now()
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._send_single_request(session, item, idx, total, semaphore, progress_callback)
                for idx, item in enumerate(items, start=1)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Compilar estatísticas
        stats = {
            "total": total,
            "success": sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success"),
            "skipped": sum(1 for r in results if isinstance(r, dict) and r.get("status") == "skipped"),
            "failed": sum(1 for r in results if isinstance(r, dict) and r.get("status") == "failed"),
            "errors": sum(1 for r in results if isinstance(r, Exception)),
            "elapsed_seconds": round(elapsed, 2),
            "records_per_second": round(total / elapsed, 2) if elapsed > 0 else 0
        }
        
        logger.info(f"Importação concluída em {stats['elapsed_seconds']}s")
        logger.info(f"Sucesso: {stats['success']} | Ignorados: {stats['skipped']} | Falhas: {stats['failed']}")
        
        return {
            "stats": stats,
            "results": results
        }
    
    async def import_multiple_dataframes(
        self,
        dataframes: Dict[str, List[Dict[str, Any]]],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Importa múltiplos dataframes em sequência.
        
        Args:
            dataframes: Dicionário {nome_do_dataframe: lista_de_items}
            progress_callback: Função opcional para reportar progresso
            
        Returns:
            Dicionário com resultados de cada dataframe
        """
        all_results = {}
        
        for name, items in dataframes.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"Processando dataframe: {name}")
            logger.info(f"{'='*50}")
            
            result = await self.import_dataframe(items, progress_callback)
            all_results[name] = result
        
        return all_results
    
    def run_import(
        self,
        items: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Wrapper síncrono para executar importação.
        
        Útil para uso em notebooks Jupyter.
        """
        return asyncio.run(self.import_dataframe(items, progress_callback))
    
    def run_import_multiple(
        self,
        dataframes: Dict[str, List[Dict[str, Any]]],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Wrapper síncrono para executar importação de múltiplos dataframes.
        
        Útil para uso em notebooks Jupyter.
        """
        return asyncio.run(self.import_multiple_dataframes(dataframes, progress_callback))


# Função de conveniência para uso rápido
def quick_import(
    items: List[Dict[str, Any]],
    base_url: str,
    import_control_key_path: str,
    max_workers: int = 5,
    persistence_file: str = "imported_leads.json"
) -> Dict[str, Any]:
    """
    Função de conveniência para importação rápida.
    
    Exemplo de uso:
    ```python
    from async_import_utils import quick_import
    
    result = quick_import(
        items=my_dataframe_list,
        base_url="https://api.example.com/endpoint",
        import_control_key_path="data.id",
        max_workers=5
    )
    print(result['stats'])
    ```
    """
    config = ImportConfig(
        base_url=base_url,
        import_control_key_path=import_control_key_path,
        max_workers=max_workers,
        persistence_file=persistence_file
    )
    
    importer = AsyncDataImporter(config)
    return importer.run_import(items)


def quick_import_multiple(
    dataframes: Dict[str, List[Dict[str, Any]]],
    base_url: str,
    import_control_key_path: str,
    max_workers: int = 5,
    persistence_file: str = "imported_leads.json"
) -> Dict[str, Dict[str, Any]]:
    """
    Função de conveniência para importação rápida de múltiplos dataframes.
    
    Exemplo de uso:
    ```python
    from async_import_utils import quick_import_multiple
    
    result = quick_import_multiple(
        dataframes={
            "hotmart": df_hotmart_conversions,
            "tmb": df_tmb_conversions
        },
        base_url="https://api.example.com/endpoint",
        import_control_key_path="conversion_data.conversion_raw_info.transaction",
        max_workers=5
    )
    
    for name, data in result.items():
        print(f"{name}: {data['stats']}")
    ```
    """
    config = ImportConfig(
        base_url=base_url,
        import_control_key_path=import_control_key_path,
        max_workers=max_workers,
        persistence_file=persistence_file
    )
    
    importer = AsyncDataImporter(config)
    return importer.run_import_multiple(dataframes)
