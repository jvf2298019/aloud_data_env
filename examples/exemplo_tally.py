"""
Exemplo de uso do módulo tally_utils.py

Este script demonstra como usar a classe Tally para interagir
com a API do Tally.

Pré-requisitos:
    - Configurar a variável de ambiente TALLY_API_KEY
    - Instalar dependências: requests

Uso:
    python examples/exemplo_tally.py
"""

import os
import sys

# Adicionar pasta src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tally_utils import Tally, TallyAPIError
import pandas as pd
from datetime import datetime, timedelta


def exemplo_listar_formularios():
    """Exemplo 1: Listar todos os formulários"""
    print("\n" + "="*60)
    print("EXEMPLO 1: Listar todos os formulários")
    print("="*60)
    
    try:
        tally = Tally()
        forms = tally.get_forms()
        
        print(f"\n✓ Total de formulários encontrados: {len(forms)}")
        
        if forms:
            print("\nFormulários:")
            for i, form in enumerate(forms[:5], 1):  # Mostrar apenas os 5 primeiros
                print(f"  {i}. {form.get('name', 'Sem nome')} (ID: {form.get('id')})")
            
            if len(forms) > 5:
                print(f"  ... e mais {len(forms) - 5} formulário(s)")
        
        return forms
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return []


def exemplo_obter_formulario(form_id: str):
    """Exemplo 2: Obter detalhes de um formulário específico"""
    print("\n" + "="*60)
    print(f"EXEMPLO 2: Obter detalhes do formulário {form_id}")
    print("="*60)
    
    try:
        tally = Tally()
        form = tally.get_form(form_id)
        
        print(f"\n✓ Formulário obtido:")
        print(f"  Nome: {form.get('name', 'N/A')}")
        print(f"  ID: {form.get('id', 'N/A')}")
        print(f"  Status: {form.get('status', 'N/A')}")
        print(f"  Criado em: {form.get('createdAt', 'N/A')}")
        
        return form
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return None


def exemplo_obter_submissoes(form_id: str):
    """Exemplo 3: Obter submissões de um formulário"""
    print("\n" + "="*60)
    print(f"EXEMPLO 3: Obter submissões do formulário {form_id}")
    print("="*60)
    
    try:
        tally = Tally()
        
        # Obter submissões dos últimos 30 dias
        data_inicial = (datetime.now() - timedelta(days=30)).isoformat()
        
        submissions = tally.get_form_submissions(
            form_id=form_id,
            since=data_inicial,
            status='COMPLETED',
            sort='desc'
        )
        
        print(f"\n✓ Total de submissões (últimos 30 dias): {len(submissions)}")
        
        if submissions:
            print("\nPrimeiras submissões:")
            for i, sub in enumerate(submissions[:3], 1):
                print(f"  {i}. Respondido em: {sub.get('respondedAt', 'N/A')}")
                fields = sub.get('fields', [])
                print(f"     Campos preenchidos: {len(fields)}")
        
        return submissions
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return []


def exemplo_submissoes_para_dataframe(form_id: str):
    """Exemplo 4: Converter submissões para DataFrame do pandas"""
    print("\n" + "="*60)
    print(f"EXEMPLO 4: Converter submissões para DataFrame")
    print("="*60)
    
    try:
        tally = Tally()
        submissions = tally.get_form_submissions(form_id=form_id, limit=50)
        
        if not submissions:
            print("\n⚠ Nenhuma submissão encontrada")
            return None
        
        # Criar DataFrame
        df = pd.DataFrame(submissions)
        
        print(f"\n✓ DataFrame criado com {len(df)} linhas e {len(df.columns)} colunas")
        print("\nColunas disponíveis:")
        for col in df.columns:
            print(f"  - {col}")
        
        print(f"\nPrimeiras linhas:")
        print(df.head())
        
        # Salvar CSV (opcional)
        output_file = 'data/processed/tally_submissions.csv'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"\n✓ Dados salvos em: {output_file}")
        
        return df
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return None


def main():
    """Função principal - executar exemplos"""
    print("\n" + "="*60)
    print("EXEMPLOS DE USO: tally_utils.py")
    print("="*60)
    
    # Verificar se a API key está configurada
    if not os.getenv('TALLY_API_KEY'):
        print("\n❌ ERRO: Variável de ambiente TALLY_API_KEY não encontrada!")
        print("\nPara configurar:")
        print("  export TALLY_API_KEY='sua_chave_aqui'")
        print("\nOu adicione no arquivo .env do projeto")
        return
    
    print("\n✓ API Key configurada")
    
    # Exemplo 1: Listar formulários
    forms = exemplo_listar_formularios()
    
    # Se houver formulários, usar o primeiro para os demais exemplos
    if forms:
        form_id = forms[0].get('id')
        
        # Exemplo 2: Obter detalhes do formulário
        exemplo_obter_formulario(form_id)
        
        # Exemplo 3: Obter submissões
        exemplo_obter_submissoes(form_id)
        
        # Exemplo 4: Converter para DataFrame
        exemplo_submissoes_para_dataframe(form_id)
    else:
        print("\n⚠️  Nenhum formulário encontrado. Crie um formulário no Tally primeiro.")
    
    print("\n" + "="*60)
    print("✓ Exemplos concluídos!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()

