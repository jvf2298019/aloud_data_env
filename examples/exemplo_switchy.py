#!/usr/bin/env python3
"""
Exemplos práticos de uso do switchy_utils.py

Para executar:
    1. Configure: export SWITCHY_API_KEY="sua-api-key"
    2. Execute: python examples/exemplo_switchy.py
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from switchy_utils import SwitchyAPI


def exemplo_1_listar_links():
    """Exemplo 1: Listar links básico"""
    print("\n" + "="*70)
    print("EXEMPLO 1: Listar Links")
    print("="*70)
    
    api = SwitchyAPI()
    links = api.get_links(limit=5, order_by={'createdDate': 'desc'})
    
    print(f"\n✅ {len(links)} links encontrados:\n")
    for link in links:
        print(f"📎 {link.get('title') or 'Sem nome'}")
        print(f"   ID: {link['id']}")
        print(f"   URL: {link.get('url')}\n")


def exemplo_2_buscar_por_tag():
    """Exemplo 2: Buscar links por tag"""
    print("\n" + "="*70)
    print("EXEMPLO 2: Buscar por Tag")
    print("="*70)
    
    api = SwitchyAPI()
    tag = input("\nDigite a tag para buscar (ex: bf25): ").strip() or 'bf25'
    
    links = api.get_links_by_tag(tag)
    print(f"\n✅ {len(links)} links com a tag '{tag}' encontrados")


def exemplo_3_atualizar_url():
    """Exemplo 3: Atualizar URL de um link"""
    print("\n" + "="*70)
    print("EXEMPLO 3: Atualizar URL")
    print("="*70)
    
    api = SwitchyAPI()
    
    link_id = input("\nDigite o ID do link (ou Enter para pular): ").strip()
    if not link_id:
        print("⏭️  Exemplo pulado")
        return
    
    nova_url = input("Digite a nova URL: ").strip()
    if not nova_url:
        print("❌ URL não fornecida")
        return
    
    confirmacao = input(f"\n⚠️  Atualizar? (sim/não): ")
    
    if confirmacao.lower() == 'sim':
        result = api.update_link_url(link_id, nova_url)
        if result['affected_rows'] > 0:
            print(f"\n✅ Link atualizado! ({result['affected_rows']} linhas)")
        else:
            print("\n⚠️ Nenhum link atualizado")
    else:
        print("❌ Cancelado")


def exemplo_4_configurar_rotator():
    """Exemplo 4: Configurar Link Rotator"""
    print("\n" + "="*70)
    print("EXEMPLO 4: Configurar Link Rotator")
    print("="*70)
    
    api = SwitchyAPI()
    
    link_id = input("\nDigite o ID do link (ou Enter para pular): ").strip()
    if not link_id:
        print("⏭️  Exemplo pulado")
        return
    
    print("\nDigite as URLs extras (linha vazia para finalizar):")
    extra_urls = []
    while True:
        url = input(f"URL {len(extra_urls) + 1}: ").strip()
        if not url:
            break
        extra_urls.append(url)
    
    if not extra_urls:
        print("\n⚠️ Nenhuma URL fornecida")
        return
    
    n = len(extra_urls)
    share = 100 // (n + 1)
    principal = 100 - (share * n)
    
    print(f"\n📊 Distribuição:")
    print(f"   Principal: {principal}%")
    for i, url in enumerate(extra_urls, 1):
        print(f"   URL {i}: {share}% - {url}")
    
    confirmacao = input("\nConfirmar? (sim/não): ")
    
    if confirmacao.lower() == 'sim':
        result = api.update_link_rotator(link_id, extra_urls)
        if result['affected_rows'] > 0:
            print(f"\n✅ Rotator configurado!")
        else:
            print("\n⚠️ Falha ao configurar")
    else:
        print("❌ Cancelado")


def exemplo_5_configurar_expiracao():
    """Exemplo 5: Configurar expiração"""
    print("\n" + "="*70)
    print("EXEMPLO 5: Configurar Expiração")
    print("="*70)
    
    api = SwitchyAPI()
    
    link_id = input("\nDigite o ID do link (ou Enter para pular): ").strip()
    if not link_id:
        print("⏭️  Exemplo pulado")
        return
    
    print("\nTipo de expiração:")
    print("1. Por data")
    print("2. Por cliques")
    tipo = input("Escolha (1 ou 2): ").strip()
    
    if tipo == '1':
        dias = input("Expira em quantos dias? (default: 30): ").strip()
        dias = int(dias) if dias else 30
        
        expiry_date = datetime.now() + timedelta(days=dias)
        redirect_url = input("URL de redirecionamento (opcional): ").strip()
        
        print(f"\n📅 Expira em: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        confirmacao = input("\nConfirmar? (sim/não): ")
        
        if confirmacao.lower() == 'sim':
            result = api.set_link_expiration_by_date(
                link_id,
                expiry_date,
                redirect_url if redirect_url else None
            )
            if result['affected_rows'] > 0:
                print("\n✅ Expiração configurada!")
            else:
                print("\n⚠️ Falha")
        else:
            print("❌ Cancelado")
    
    elif tipo == '2':
        max_clicks = input("Número máximo de cliques: ").strip()
        if not max_clicks or not max_clicks.isdigit():
            print("❌ Número inválido")
            return
        
        max_clicks = int(max_clicks)
        redirect_url = input("URL de redirecionamento (opcional): ").strip()
        
        print(f"\n🔢 Expira após {max_clicks} cliques")
        
        confirmacao = input("\nConfirmar? (sim/não): ")
        
        if confirmacao.lower() == 'sim':
            result = api.set_link_expiration_by_clicks(
                link_id,
                max_clicks,
                redirect_url if redirect_url else None
            )
            if result['affected_rows'] > 0:
                print("\n✅ Expiração configurada!")
            else:
                print("\n⚠️ Falha")
        else:
            print("❌ Cancelado")
    else:
        print("❌ Opção inválida")


def exemplo_6_estatisticas():
    """Exemplo 6: Estatísticas da conta"""
    print("\n" + "="*70)
    print("EXEMPLO 6: Estatísticas")
    print("="*70)
    
    api = SwitchyAPI()
    
    stats = api.get_statistics()
    
    print(f"\n📊 ESTATÍSTICAS")
    print(f"   Total de links: {stats['total_links']:,}")
    print(f"   Total de cliques: {stats['total_clicks']:,}")
    print(f"   Média: {stats['average_clicks']:.2f} cliques/link")
    print(f"   Sem cliques: {stats['links_without_clicks']} ({stats['percentage_without_clicks']:.1f}%)")


def exemplo_7_top_links():
    """Exemplo 7: Links mais clicados"""
    print("\n" + "="*70)
    print("EXEMPLO 7: Top Links")
    print("="*70)
    
    api = SwitchyAPI()
    
    top = api.get_top_links(limit=10)
    
    print(f"\n🏆 Top {len(top)} Links:\n")
    for i, link in enumerate(top, 1):
        name = link.get('title') or link.get('name') or 'Sem nome'
        clicks = link.get('clicks', 0)
        print(f"{i:2d}. {name:40s} | {clicks:5d} clicks")


def menu_interativo():
    """Menu interativo"""
    exemplos = [
        ("Listar Links", exemplo_1_listar_links),
        ("Buscar por Tag", exemplo_2_buscar_por_tag),
        ("Atualizar URL", exemplo_3_atualizar_url),
        ("Configurar Rotator", exemplo_4_configurar_rotator),
        ("Configurar Expiração", exemplo_5_configurar_expiracao),
        ("Estatísticas", exemplo_6_estatisticas),
        ("Top Links", exemplo_7_top_links),
    ]
    
    while True:
        print("\n" + "="*70)
        print("SWITCHY API - EXEMPLOS")
        print("="*70)
        
        print("\nEscolha um exemplo:\n")
        for i, (nome, _) in enumerate(exemplos, 1):
            print(f"  {i}. {nome}")
        print("  0. Sair")
        
        escolha = input("\nOpção: ").strip()
        
        if escolha == '0':
            print("\n👋 Até logo!")
            break
        
        try:
            idx = int(escolha) - 1
            if 0 <= idx < len(exemplos):
                nome, func = exemplos[idx]
                try:
                    func()
                except KeyboardInterrupt:
                    print("\n⚠️  Interrompido")
                except Exception as e:
                    print(f"\n❌ Erro: {e}")
                
                input("\nEnter para continuar...")
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Opção inválida")


def main():
    """Função principal"""
    print("\n🔗 SWITCHY API - EXEMPLOS PRÁTICOS")
    print("="*70)
    
    if not os.getenv("SWITCHY_API_KEY"):
        print("\n⚠️  ATENÇÃO: SWITCHY_API_KEY não encontrada!")
        print("\nDefina antes de executar:")
        print('  export SWITCHY_API_KEY="sua-api-key"')
        return
    
    try:
        api = SwitchyAPI()
        print("\n✅ Conexão estabelecida")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        menu_interativo()
    
    except ValueError as e:
        print(f"\n❌ Erro: {e}")
    except Exception as e:
        print(f"\n❌ Erro: {e}")


if __name__ == '__main__':
    main()

