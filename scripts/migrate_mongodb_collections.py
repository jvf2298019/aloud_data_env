#!/usr/bin/env python3
"""
Script para migrar collections de um banco MongoDB para outro.

Connection strings: definidas no .env na raiz do projeto:
    MONGO_SOURCE_URI=mongodb://user:pass@host-origem:27017
    MONGO_DEST_URI=mongodb://user:pass@host-destino:27017

Uso:
    python scripts/migrate_mongodb_collections.py --db meu_banco

    # Apenas algumas collections
    python scripts/migrate_mongodb_collections.py --db meu_banco --collections users events

    # Apagar collection no destino antes de inserir
    python scripts/migrate_mongodb_collections.py --db meu_banco --drop
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Carrega .env (raiz do projeto e/ou config/.env)
_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")
load_dotenv(_root / "config" / ".env")

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
except ImportError:
    print("Erro: instale pymongo com: pip install pymongo", file=sys.stderr)
    sys.exit(1)

# ============================================================================
# CONFIGURAÇÃO DE LOG
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES PADRÃO
# ============================================================================

DEFAULT_BATCH_SIZE = 1000
ENV_SOURCE_URI = "MONGO_SOURCE_URI"
ENV_DEST_URI = "MONGO_DEST_URI"


def get_client(uri: str, timeout_ms: int = 30000) -> MongoClient:
    """Cria cliente MongoDB com timeout razoável."""
    return MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)


def list_collections(client: MongoClient, db_name: str) -> List[str]:
    """Lista nomes de collections do database (exclui system)."""
    db = client[db_name]
    names = db.list_collection_names()
    return [n for n in names if not n.startswith("system.")]


def migrate_collection(
    source_client: MongoClient,
    dest_client: MongoClient,
    source_db: str,
    dest_db: str,
    collection_name: str,
    *,
    drop_before: bool = False,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> int:
    """
    Copia todos os documentos da collection de origem para o destino.
    Retorna o número de documentos inseridos.
    """
    source_coll = source_client[source_db][collection_name]
    dest_coll = dest_client[dest_db][collection_name]

    if drop_before:
        dest_coll.drop()
        logger.info("  Collection '%s' no destino foi dropada.", collection_name)

    total = 0
    cursor = source_coll.find()
    batch = []

    for doc in cursor:
        # Remove _id para deixar o destino gerar novos (evita conflito entre clusters)
        doc_copy = {k: v for k, v in doc.items()}
        batch.append(doc_copy)

        if len(batch) >= batch_size:
            if batch:
                dest_coll.insert_many(batch)
                total += len(batch)
                logger.info("  %s: +%d documentos (total: %d)", collection_name, len(batch), total)
            batch = []

    if batch:
        dest_coll.insert_many(batch)
        total += len(batch)
        logger.info("  %s: +%d documentos (total: %d)", collection_name, len(batch), total)

    return total


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migra collections de um MongoDB (origem) para outro (destino).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source",
        default=os.environ.get(ENV_SOURCE_URI),
        help=f"URI MongoDB de origem (default: {ENV_SOURCE_URI} no .env)",
    )
    parser.add_argument(
        "--dest",
        default=os.environ.get(ENV_DEST_URI),
        help=f"URI MongoDB de destino (default: {ENV_DEST_URI} no .env)",
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Nome do database a migrar",
    )
    parser.add_argument(
        "--dest-db",
        required=False,
        help="Nome do database de destino (se omitido, usa o mesmo nome de --db)",
    )
    parser.add_argument(
        "--collections",
        nargs="*",
        default=None,
        help="Lista de collections a migrar (omitir = todas)",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Apagar a collection no destino antes de inserir",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Documentos por lote na inserção (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas listar collections que seriam migradas, sem copiar",
    )
    args = parser.parse_args()

    if not args.source or not args.dest:
        logger.error(
            "Defina %s e %s no arquivo .env (na raiz do projeto) ou use --source e --dest.",
            ENV_SOURCE_URI,
            ENV_DEST_URI,
        )
        sys.exit(1)

    logger.info("Conectando à origem: %s", args.source.split("@")[-1] if "@" in args.source else args.source)
    logger.info("Conectando ao destino: %s", args.dest.split("@")[-1] if "@" in args.dest else args.dest)

    try:
        source_client = get_client(args.source)
        dest_client = get_client(args.dest)
        source_client.admin.command("ping")
        dest_client.admin.command("ping")
    except PyMongoError as e:
        logger.error("Falha ao conectar: %s", e)
        sys.exit(1)

    src_db = args.db
    dest_db = args.dest_db or args.db

    if args.collections:
        to_migrate = list(args.collections)
        # Verifica se existem na origem
        existing = set(list_collections(source_client, src_db))
        missing = [c for c in to_migrate if c not in existing]
        if missing:
            logger.warning("Collections não encontradas na origem: %s", missing)
            to_migrate = [c for c in to_migrate if c in existing]
    else:
        to_migrate = list_collections(source_client, src_db)
        if not to_migrate:
            logger.warning("Nenhuma collection encontrada no database '%s'.", src_db)
            sys.exit(0)

    logger.info("Source DB: %s | Dest DB: %s | Collections a migrar: %s", src_db, dest_db, to_migrate)

    if args.dry_run:
        for name in to_migrate:
            count = source_client[src_db][name].estimated_document_count()
            logger.info("  [dry-run] %s.%s -> %s.%s : ~%d documentos", src_db, name, dest_db, name, count)
        logger.info("Dry-run concluído. Execute sem --dry-run para migrar.")
        return

    total_docs = 0
    for coll_name in to_migrate:
        logger.info("Migrando collection: %s ( %s.%s -> %s.%s )", coll_name, src_db, coll_name, dest_db, coll_name)
        try:
            n = migrate_collection(
                source_client,
                dest_client,
                src_db,
                dest_db,
                coll_name,
                drop_before=args.drop,
                batch_size=args.batch_size,
            )
            total_docs += n
        except PyMongoError as e:
            logger.error("Erro ao migrar '%s': %s", coll_name, e)
            sys.exit(1)

    logger.info("Migração concluída. Total de documentos inseridos: %d", total_docs)


if __name__ == "__main__":
    main()
