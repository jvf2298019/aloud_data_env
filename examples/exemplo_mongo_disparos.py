"""
Exemplo de uso do módulo mongo_utils para buscar dados de disparos
"""

import sys
sys.path.append('../src')

from mongo_utils import MongoDBConnection
import pandas as pd


def exemplo_1_listar_colecoes():
    """Exemplo 1: Listar coleções filtradas"""
    print("=" * 70)
    print("EXEMPLO 1: Listar coleções que contêm 'lcto-bf25'")
    print("=" * 70)
    
    with MongoDBConnection(database_name="disparos-api") as mongo:
        # Listar todas as coleções que contêm "lcto-bf25"
        collections = mongo.get_collection_names(filter_text="lcto-bf25")
        
        print(f"\n📋 Coleções encontradas:")
        for col in collections:
            print(f"   • {col}")


def exemplo_2_buscar_documentos():
    """Exemplo 2: Buscar documentos das coleções filtradas"""
    print("\n" + "=" * 70)
    print("EXEMPLO 2: Buscar documentos das coleções")
    print("=" * 70)
    
    with MongoDBConnection(database_name="disparos-api") as mongo:
        # Buscar todos os documentos das coleções que contêm "lcto-bf25"
        # Agora retorna DataFrame consolidado diretamente
        df = mongo.get_documents_from_filtered_collections(
            collection_filter="lcto-bf25"
        )
        
        # Mostrar resumo
        if not df.empty:
            print(f"\n📊 Resumo dos dados:")
            print(f"   Total de documentos: {len(df)}")
            print(f"   Colunas: {list(df.columns)}")
            print(f"   Coleções encontradas: {df['collection_name'].nunique()}")
            
            if 'status' in df.columns:
                print(f"   Status únicos: {df['status'].unique()}")
            
            # Distribuição por coleção
            print(f"\n📋 Documentos por coleção:")
            print(df['collection_name'].value_counts())
        else:
            print("\n⚠️ Nenhum documento encontrado")


def exemplo_3_filtrar_por_status():
    """Exemplo 3: Filtrar documentos por status"""
    print("\n" + "=" * 70)
    print("EXEMPLO 3: Filtrar documentos com status EXECUTED")
    print("=" * 70)
    
    with MongoDBConnection(database_name="disparos-api") as mongo:
        # Buscar apenas documentos com status EXECUTED
        df = mongo.get_documents_from_filtered_collections(
            collection_filter="lcto-bf25",
            document_filter={"status": "EXECUTED"}
        )
        
        if not df.empty:
            print(f"\n✅ Total de documentos EXECUTED: {len(df)}")
            print(f"📋 Por coleção:")
            print(df['collection_name'].value_counts())
        else:
            print("\n⚠️ Nenhum documento EXECUTED encontrado")


def exemplo_4_exportar_para_csv():
    """Exemplo 4: Exportar dados para CSV"""
    print("\n" + "=" * 70)
    print("EXEMPLO 4: Exportar dados para CSV")
    print("=" * 70)
    
    with MongoDBConnection(database_name="disparos-api") as mongo:
        # Exportar coleções automaticamente (separadas)
        mongo.export_filtered_collections_to_csv(
            collection_filter="lcto-bf25",
            output_dir="../data/raw",
            consolidated=False
        )
        
        # Exportar consolidado
        print("\n📦 Exportando versão consolidada...")
        mongo.export_filtered_collections_to_csv(
            collection_filter="lcto-bf25",
            output_dir="../data/processed",
            consolidated=True
        )


def exemplo_5_estatisticas():
    """Exemplo 5: Obter estatísticas das coleções"""
    print("\n" + "=" * 70)
    print("EXEMPLO 5: Estatísticas das coleções")
    print("=" * 70)
    
    with MongoDBConnection(database_name="disparos-api") as mongo:
        collections = mongo.get_collection_names(filter_text="lcto-bf25")
        
        for col_name in collections:
            stats = mongo.get_collection_stats(col_name)
            print(f"\n📊 Coleção: {stats['name']}")
            print(f"   Total de documentos: {stats['count']}")
            if 'sample_keys' in stats:
                print(f"   Campos: {stats['sample_keys']}")


def exemplo_6_campos_especificos():
    """Exemplo 6: Buscar apenas campos específicos"""
    print("\n" + "=" * 70)
    print("EXEMPLO 6: Buscar apenas campos específicos (projection)")
    print("=" * 70)
    
    with MongoDBConnection(database_name="disparos-api") as mongo:
        # Buscar apenas email, phone e status
        df = mongo.get_documents_from_filtered_collections(
            collection_filter="lcto-bf25",
            projection={"email": 1, "phone": 1, "status": 1, "campaign_id": 1},
            limit_per_collection=5
        )
        
        if not df.empty:
            print(f"\n📋 Dados consolidados (primeiras linhas):")
            print(df.head(10))
            print(f"\n   Total de registros: {len(df)}")
            print(f"   Colunas: {list(df.columns)}")
        else:
            print("\n⚠️ Nenhum documento encontrado")


def exemplo_completo():
    """Exemplo completo com análise"""
    print("\n" + "=" * 70)
    print("EXEMPLO COMPLETO: Análise de disparos BF25")
    print("=" * 70)
    
    with MongoDBConnection(database_name="disparos-api") as mongo:
        # Buscar dados (já retorna DataFrame consolidado)
        df_completo = mongo.get_documents_from_filtered_collections(
            collection_filter="lcto-bf25"
        )
        
        if not df_completo.empty:
            print(f"\n📊 ANÁLISE CONSOLIDADA:")
            print(f"   Total de registros: {len(df_completo)}")
            print(f"   Coleções: {df_completo['collection_name'].nunique()}")
            print(f"   Colunas: {list(df_completo.columns)}")
            
            if 'status' in df_completo.columns:
                print(f"\n   Status dos disparos:")
                status_counts = df_completo['status'].value_counts()
                for status, count in status_counts.items():
                    percentage = (count / len(df_completo)) * 100
                    print(f"      {status}: {count} ({percentage:.1f}%)")
            
            if 'campaign_id' in df_completo.columns:
                print(f"\n   Campanhas:")
                for campaign in df_completo['campaign_id'].unique():
                    count = len(df_completo[df_completo['campaign_id'] == campaign])
                    print(f"      {campaign}: {count} registros")
            
            # Distribuição por coleção
            print(f"\n   Documentos por coleção:")
            col_counts = df_completo['collection_name'].value_counts()
            for col_name, count in col_counts.items():
                percentage = (count / len(df_completo)) * 100
                print(f"      {col_name}: {count} ({percentage:.1f}%)")
            
            # Salvar consolidado
            output_path = "../data/processed/disparos_lcto_bf25_consolidado.csv"
            df_completo.to_csv(output_path, index=False)
            print(f"\n💾 Dados consolidados salvos em: {output_path}")
            
            return df_completo
        else:
            print("\n⚠️ Nenhum documento encontrado")
            return pd.DataFrame()


if __name__ == "__main__":
    # Executar exemplos
    try:
        exemplo_1_listar_colecoes()
        exemplo_2_buscar_documentos()
        exemplo_3_filtrar_por_status()
        exemplo_5_estatisticas()
        exemplo_6_campos_especificos()
        
        # Exemplo completo
        df_resultado = exemplo_completo()
        
        print("\n" + "=" * 70)
        print("✅ Todos os exemplos executados com sucesso!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Erro ao executar exemplos: {e}")
        print("\nVerifique se:")
        print("  1. O MongoDB está rodando")
        print("  2. A variável MONGO_URI está configurada no .env")
        print("  3. Você tem acesso à database 'disparos-api'")

