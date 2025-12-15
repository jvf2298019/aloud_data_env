"""
Utilitários para trabalhar com MongoDB
"""

import os
from typing import List, Dict, Any, Optional
import pandas as pd
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


class MongoDBConnection:
    """
    Classe para gerenciar conexões com MongoDB e realizar operações
    """
    
    def __init__(self, connection_string: Optional[str] = None, database_name: str = "disparos-api"):
        """
        Inicializa a conexão com MongoDB
        
        Args:
            connection_string: String de conexão MongoDB (usa MONGO_URI do .env se não fornecido)
            database_name: Nome da database a conectar
        """
        self.connection_string = connection_string or os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
    
    def connect(self) -> Database:
        """
        Estabelece conexão com o MongoDB
        
        Returns:
            Database object
        """
        if self.client is None:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            print(f"✅ Conectado ao MongoDB - Database: {self.database_name}")
        return self.db
    
    def disconnect(self):
        """
        Fecha a conexão com o MongoDB
        """
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            print("🔌 Desconectado do MongoDB")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def get_collection_names(self, filter_text: Optional[str] = None) -> List[str]:
        """
        Lista todas as coleções da database, opcionalmente filtrando por nome
        
        Args:
            filter_text: Texto para filtrar nomes de coleções (case insensitive)
        
        Returns:
            Lista com nomes das coleções
        """
        if self.db is None:
            raise RuntimeError("Database não conectada. Use connect() primeiro.")
        
        all_collections = self.db.list_collection_names()
        
        if filter_text:
            filtered_collections = [
                col for col in all_collections 
                if filter_text.lower() in col.lower()
            ]
            print(f"📋 Encontradas {len(filtered_collections)} coleções contendo '{filter_text}'")
            return filtered_collections
        
        print(f"📋 Total de {len(all_collections)} coleções na database")
        return all_collections
    
    def get_documents_from_collection(
        self, 
        collection_name: str,
        filter_query: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        projection: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos de uma coleção
        
        Args:
            collection_name: Nome da coleção
            filter_query: Filtro de busca (MongoDB query format)
            limit: Número máximo de documentos a retornar
            projection: Campos a incluir/excluir na resposta
        
        Returns:
            Lista de documentos
        """
        if self.db is None:
            raise RuntimeError("Database não conectada. Use connect() primeiro.")
        
        collection = self.db[collection_name]
        filter_query = filter_query or {}
        cursor = collection.find(filter_query, projection)
        
        if limit:
            cursor = cursor.limit(limit)
        
        documents = list(cursor)
        print(f"📄 {len(documents)} documentos encontrados na coleção '{collection_name}'")
        return documents
    
    def get_documents_from_filtered_collections(
        self,
        collection_filter: str,
        document_filter: Optional[Dict[str, Any]] = None,
        limit_per_collection: Optional[int] = None,
        projection: Optional[Dict[str, int]] = None,
        normalize_id: bool = True
    ) -> pd.DataFrame:
        """
        Busca documentos de múltiplas coleções filtradas por nome e retorna DataFrame consolidado
        
        Args:
            collection_filter: Texto para filtrar nomes de coleções
            document_filter: Filtro de busca para os documentos
            limit_per_collection: Limite de documentos por coleção
            projection: Campos a incluir/excluir
            normalize_id: Se True, converte _id.$oid para _id
        
        Returns:
            DataFrame pandas consolidado com todos os documentos e coluna 'collection_name'
        """
        collection_names = self.get_collection_names(collection_filter)
        
        all_dfs = []
        total_documents = 0
        
        print(f"\n🔍 Buscando documentos em {len(collection_names)} coleções...\n")
        
        for col_name in collection_names:
            docs = self.get_documents_from_collection(
                col_name, 
                document_filter, 
                limit_per_collection,
                projection
            )
            
            if docs:
                df = self.documents_to_dataframe(docs, normalize_id=normalize_id)
                df['collection_name'] = col_name
                all_dfs.append(df)
                total_documents += len(docs)
        
        if all_dfs:
            df_consolidated = pd.concat(all_dfs, ignore_index=True)
            print(f"\n✨ Total: {total_documents} documentos em {len(collection_names)} coleções")
            print(f"📊 DataFrame shape: {df_consolidated.shape}")
            return df_consolidated
        else:
            print("\n⚠️ Nenhum documento encontrado")
            return pd.DataFrame(columns=['collection_name'])
    
    @staticmethod
    def documents_to_dataframe(
        documents: List[Dict[str, Any]], 
        normalize_id: bool = True
    ) -> pd.DataFrame:
        """
        Converte lista de documentos MongoDB para DataFrame pandas
        
        Args:
            documents: Lista de documentos
            normalize_id: Se True, converte _id.$oid para _id
        
        Returns:
            DataFrame pandas
        """
        if not documents:
            return pd.DataFrame()
        
        df = pd.DataFrame(documents)
        
        # Normaliza o campo _id se necessário
        if normalize_id and '_id' in df.columns:
            if isinstance(df['_id'].iloc[0], dict) and '$oid' in df['_id'].iloc[0]:
                df['_id'] = df['_id'].apply(lambda x: x.get('$oid', x) if isinstance(x, dict) else x)
        
        return df
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Obtém estatísticas de uma coleção
        
        Args:
            collection_name: Nome da coleção
        
        Returns:
            Dicionário com estatísticas
        """
        if self.db is None:
            raise RuntimeError("Database não conectada. Use connect() primeiro.")
        
        collection = self.db[collection_name]
        stats = {
            'name': collection_name,
            'count': collection.count_documents({}),
            'indexes': list(collection.list_indexes()),
        }
        
        # Tenta obter amostra de um documento
        sample_doc = collection.find_one()
        if sample_doc:
            stats['sample_keys'] = list(sample_doc.keys())
        
        return stats
    
    def export_collection_to_csv(
        self,
        collection_name: str,
        output_path: str,
        filter_query: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> str:
        """
        Exporta uma coleção para arquivo CSV
        
        Args:
            collection_name: Nome da coleção
            output_path: Caminho do arquivo de saída
            filter_query: Filtro de busca
            limit: Limite de documentos
        
        Returns:
            Caminho do arquivo criado
        """
        documents = self.get_documents_from_collection(
            collection_name, 
            filter_query, 
            limit
        )
        df = self.documents_to_dataframe(documents)
        
        df.to_csv(output_path, index=False)
        print(f"💾 Dados exportados para: {output_path}")
        
        return output_path
    
    def export_filtered_collections_to_csv(
        self,
        collection_filter: str,
        output_dir: str,
        document_filter: Optional[Dict[str, Any]] = None,
        limit_per_collection: Optional[int] = None,
        consolidated: bool = True,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Exporta múltiplas coleções filtradas para CSV
        
        Args:
            collection_filter: Filtro de nome de coleções
            output_dir: Diretório de saída
            document_filter: Filtro de documentos
            limit_per_collection: Limite por coleção
            consolidated: Se True (padrão), cria um arquivo consolidado. Se False, cria um arquivo por coleção
            output_filename: Nome do arquivo de saída (sem extensão). Se None, usa collection_filter
        
        Returns:
            Caminho do arquivo criado (ou lista de caminhos se consolidated=False)
        """
        df_result = self.get_documents_from_filtered_collections(
            collection_filter,
            document_filter,
            limit_per_collection
        )
        
        if df_result.empty:
            print("⚠️ Nenhum dado para exportar")
            return ""
        
        if consolidated:
            # Criar arquivo consolidado
            filename = output_filename or f"{collection_filter}_consolidado"
            output_path = os.path.join(output_dir, f"{filename}.csv")
            df_result.to_csv(output_path, index=False)
            print(f"\n💾 Arquivo consolidado exportado: {output_path}")
            print(f"   Registros: {len(df_result)}")
            print(f"   Colunas: {list(df_result.columns)}")
            return output_path
        else:
            # Criar um arquivo por coleção
            output_files = []
            for col_name in df_result['collection_name'].unique():
                df_col = df_result[df_result['collection_name'] == col_name].copy()
                df_col = df_col.drop(columns=['collection_name'])
                output_path = os.path.join(output_dir, f"{col_name}.csv")
                df_col.to_csv(output_path, index=False)
                output_files.append(output_path)
                print(f"💾 Exportado: {output_path} ({len(df_col)} registros)")
            
            print(f"\n✅ Total de {len(output_files)} arquivos exportados")
            return output_files


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo 1: Conectar e listar coleções filtradas
    with MongoDBConnection(database_name="disparos-api") as mongo:
        
        # Filtrar coleções que contêm "lcto-bf25"
        collections = mongo.get_collection_names(filter_text="lcto-bf25")
        print(f"\nColeções encontradas: {collections}")
        
        # Buscar documentos das coleções filtradas (retorna DataFrame consolidado)
        df = mongo.get_documents_from_filtered_collections(
            collection_filter="lcto-bf25",
            limit_per_collection=10  # Limitar a 10 documentos por coleção para exemplo
        )
        
        if not df.empty:
            print("\n📊 DataFrame Consolidado:")
            print(f"   Shape: {df.shape}")
            print(f"   Colunas: {list(df.columns)}")
            print(f"   Coleções: {df['collection_name'].unique()}")
            print(f"\n{df.head()}")
            
            # Análise por coleção
            print("\n📋 Distribuição por coleção:")
            print(df['collection_name'].value_counts())
        
        # Exemplo 2: Exportar para CSV consolidado
        print("\n" + "="*70)
        print("Exportando dados consolidados...")
        mongo.export_filtered_collections_to_csv(
            collection_filter="lcto-bf25",
            output_dir="../data/processed",
            consolidated=True
        )

