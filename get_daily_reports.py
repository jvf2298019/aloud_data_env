import pandas as pd
import os
from pathlib import Path
from aloud_database.aloud_database import Database


MAIN_FOLDER_PATH = Path("~/Documentos/trf_daliy_reports").expanduser()
QUERYS_FOLDER = Path("/Users/jv/Library/Containers/at.eggerapps.Postico/Data/Library/Application Support/Postico/Local Library/aloud_database/Queries/Otimização Tráfego")


def clear_folder(folder_path: Path) -> None:
    """Esvazia a pasta removendo todos os arquivos dentro dela."""
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Pasta criada: {folder_path}")
        return
    
    for item in folder_path.iterdir():
        if item.is_file():
            item.unlink()
            print(f"Arquivo removido: {item.name}")
    print(f"Pasta {folder_path} esvaziada.")


def read_sql_file(file_path: Path) -> str:
    """Lê o conteúdo de um arquivo SQL."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def execute_query_and_save(query_file: Path, output_folder: Path, db: Database) -> None:
    """Executa uma query de um arquivo SQL e salva o resultado em CSV."""
    print(f"\nProcessando: {query_file.name}")
    
    # Lê a query do arquivo
    query = read_sql_file(query_file)
    
    # Executa a query
    try:
        df = db.execute_query(query=query)
        
        if df.empty:
            print(f"  ⚠️  Query não retornou resultados: {query_file.name}")
        else:
            # Define o nome do arquivo de saída (mesmo nome do arquivo .sql, mas com extensão .csv)
            output_filename = query_file.stem + '.csv'
            output_path = output_folder / output_filename
            
            # Salva o DataFrame como CSV
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"  ✓ Salvo: {output_filename} ({len(df)} linhas)")
    
    except Exception as e:
        print(f"  ✗ Erro ao executar query {query_file.name}: {e}")


def main():
    """Função principal que executa o processo completo."""
    print("=" * 60)
    print("INICIANDO GERAÇÃO DE RELATÓRIOS DIÁRIOS")
    print("=" * 60)
    
    # 1. Esvaziar a pasta MAIN_FOLDER_PATH
    print(f"\n[1/3] Esvaziando pasta: {MAIN_FOLDER_PATH}")
    clear_folder(MAIN_FOLDER_PATH)
    
    # 2. Buscar todos os arquivos .sql na pasta QUERYS_FOLDER
    print(f"\n[2/3] Buscando arquivos SQL em: {QUERYS_FOLDER}")
    sql_files = list(QUERYS_FOLDER.glob('*.sql'))
    
    if not sql_files:
        print(f"  ⚠️  Nenhum arquivo .sql encontrado em {QUERYS_FOLDER}")
        return
    
    print(f"  Encontrados {len(sql_files)} arquivo(s) SQL")
    
    # 3. Executar as queries e salvar os resultados
    print(f"\n[3/3] Executando queries e salvando resultados...")
    db = Database()
    
    for sql_file in sql_files:
        execute_query_and_save(sql_file, MAIN_FOLDER_PATH, db)
    
    # Fecha a conexão com o banco
    db.close_connection()
    
    print("\n" + "=" * 60)
    print("PROCESSO CONCLUÍDO!")
    print("=" * 60)
    print(f"Resultados salvos em: {MAIN_FOLDER_PATH}")


if __name__ == "__main__":
    main()
