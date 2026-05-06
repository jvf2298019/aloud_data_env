"""
Script de importação retroativa de dados de vendas da Hotmart.

Lê o CSV de vendas em data/raw/hotmart.csv, formata os dados no padrão
de conversão e envia para o serviço de identity-resolution no Cloud Run.

Controle de importação:
  - Usa um arquivo JSON local (imported_leads.json) para rastrear transações já enviadas.
  - Registros já importados são ignorados automaticamente em re-execuções.

Uso:
  python scripts/import_hotmart_sales.py
  python scripts/import_hotmart_sales.py --csv data/raw/hotmart.csv --sep ";"
  python scripts/import_hotmart_sales.py --dry-run
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import requests

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from data_utils import flatten_list_to_df
from hotmart_utils import read_hotmart_csv, format_hotmart_conversions
from sql_utils import DatabaseConnection

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Constantes
DEFAULT_CSV = 'hotmart.csv'
DEFAULT_DATA_DIR = str(Path(__file__).resolve().parent.parent / 'data' / 'raw')
DEFAULT_SEP = ';'
CONVERSION_TYPE_ID = '8'
DESTINATION_QUEUE = 'S.NORM.PROD.NEW'
SKIP_ORQUESTRATION = True
SKIP_CONVERSION = False
BASE_URL = 'https://southamerica-east1-aloud-etl.cloudfunctions.net/identity-resolution-http'
PERSISTENCE_FILE = Path(__file__).resolve().parent / 'imported_leads.json'
IMPORT_CONTROL_KEY_PATH = 'conversion_data.conversion_raw_info.transaction'
EXISTING_TRANSACTIONS_QUERY = """
SELECT
    c.conversion_raw_info->>'transaction' as transaction_code
FROM
    lead_tracking_prod.conversions c
WHERE
    c.conversion_type_id = '8'
"""


def fetch_existing_transactions() -> set:
    """Consulta o banco e retorna set de transaction codes já importados."""
    logger.info('Consultando conversões já existentes no banco...')
    db = DatabaseConnection()
    df = db.execute_query(EXISTING_TRANSACTIONS_QUERY)
    existing = set(df['transaction_code'].dropna().astype(str))
    logger.info('Conversões existentes no banco: %d', len(existing))
    return existing


def filter_existing_conversions(records: list, existing: set) -> list:
    """Remove registros cujo transaction já existe no banco."""
    filtered = []
    for item in records:
        tx = str(get_deep_key(item, IMPORT_CONTROL_KEY_PATH, '')).strip()
        if tx not in existing:
            filtered.append(item)

    removed = len(records) - len(filtered)
    logger.info(
        'Filtro do banco: %d removidos, %d restantes (de %d total)',
        removed, len(filtered), len(records),
    )
    return filtered


def get_deep_key(d: dict, key_path: str, default: str = '') -> str:
    """Busca valor em d pelo key_path em formato dot."""
    try:
        for key in key_path.split('.'):
            d = d[key]
        return d
    except (KeyError, TypeError):
        return default


def load_imported_keys(persistence_file: Path) -> set:
    """Carrega chaves de registros já importados."""
    if persistence_file.exists():
        with open(persistence_file, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()


def save_imported_keys(imported_keys: set, persistence_file: Path) -> None:
    """Persiste chaves de registros importados."""
    with open(persistence_file, 'w', encoding='utf-8') as f:
        json.dump(sorted(list(imported_keys)), f, ensure_ascii=False, indent=2)


def prepare_data(csv_file: str, data_dir: str, sep: str) -> list:
    """Lê o CSV e formata os dados de conversão."""
    logger.info('Lendo CSV: %s/%s', data_dir, csv_file)
    df_hotmart = read_hotmart_csv(csv_file, data_dir=data_dir, sep=sep)
    logger.info('Registros lidos do CSV: %d', len(df_hotmart))

    logger.info('Formatando conversões (conversion_type_id=%s)', CONVERSION_TYPE_ID)
    conversions = format_hotmart_conversions(
        df_hotmart,
        conversion_type_id=CONVERSION_TYPE_ID,
        skip_conversion=SKIP_CONVERSION,
        skip_orquestration=SKIP_ORQUESTRATION,
        destination_queue=DESTINATION_QUEUE,
    )
    logger.info('Conversões formatadas: %d', len(conversions))
    return conversions


def import_records(
    records: list,
    imported_keys: set,
    persistence_file: Path,
    dry_run: bool = False,
) -> list:
    """Envia registros para o serviço de identity-resolution."""
    total = len(records)
    responses = []
    sent = 0
    skipped = 0

    for idx, item in enumerate(records, start=1):
        import_key = str(get_deep_key(item, IMPORT_CONTROL_KEY_PATH, '')).strip()

        if not import_key:
            logger.warning('Registro %d/%d ignorado: chave de controle ausente.', idx, total)
            skipped += 1
            continue

        if import_key in imported_keys:
            skipped += 1
            continue

        if dry_run:
            logger.info('[DRY-RUN] Registro %d/%d seria enviado (key: %s)', idx, total, import_key)
            sent += 1
            continue

        logger.info('Importando registro %d/%d (key: %s)', idx, total, import_key)
        try:
            response = requests.post(BASE_URL, json=item, timeout=30)
            response.raise_for_status()
            resp_json = response.json()
        except requests.exceptions.RequestException as e:
            logger.error('Erro ao enviar registro %d (key: %s): %s', idx, import_key, e)
            resp_json = {'error': str(e), 'key': import_key}

        responses.append(resp_json)
        sent += 1

        imported_keys.add(import_key)
        save_imported_keys(imported_keys, persistence_file)

    logger.info(
        'Importação concluída: %d enviados, %d ignorados (já importados ou sem chave), %d total',
        sent, skipped, total,
    )
    return responses


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Importação retroativa de vendas Hotmart para o serviço de identity-resolution.',
    )
    parser.add_argument(
        '--csv', default=DEFAULT_CSV,
        help=f'Nome do arquivo CSV (default: {DEFAULT_CSV})',
    )
    parser.add_argument(
        '--data-dir', default=DEFAULT_DATA_DIR,
        help=f'Diretório do CSV (default: {DEFAULT_DATA_DIR})',
    )
    parser.add_argument(
        '--sep', default=DEFAULT_SEP,
        help=f'Separador do CSV (default: "{DEFAULT_SEP}")',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Simula a importação sem enviar dados.',
    )
    parser.add_argument(
        '--persistence-file', default=str(PERSISTENCE_FILE),
        help=f'Arquivo de controle de importação (default: {PERSISTENCE_FILE})',
    )
    parser.add_argument(
        '--skip-db-check', action='store_true',
        help='Pula a consulta ao banco para verificar conversões existentes.',
    )

    args = parser.parse_args()
    persistence_file = Path(args.persistence_file)

    records = prepare_data(args.csv, args.data_dir, args.sep)

    if not records:
        logger.warning('Nenhum registro para importar.')
        return

    if not args.skip_db_check:
        existing = fetch_existing_transactions()
        records = filter_existing_conversions(records, existing)
        if not records:
            logger.info('Todos os registros já existem no banco. Nada a importar.')
            return

    imported_keys = load_imported_keys(persistence_file)
    logger.info('Registros já importados anteriormente: %d', len(imported_keys))

    responses = import_records(records, imported_keys, persistence_file, dry_run=args.dry_run)

    if args.dry_run:
        logger.info('[DRY-RUN] Nenhum dado foi enviado.')


if __name__ == '__main__':
    main()
