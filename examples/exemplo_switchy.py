#!/usr/bin/env python3
"""
Exemplos práticos de uso do switchy_utils.py

Para executar:
    1. Configure a variável de ambiente: export SWITCHY_API_KEY="sua-api-key"
    2. Execute: python examples/exemplo_switchy.py

Documentação completa:
    - SWITCHY_SCHEMA_ANALYSIS.md
    - SWITCHY_EXAMPLES.md
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
    
    # Listar primeiros 5 links
    links = api.get_links(limit=5, order_by={'createdDate': 'desc'})
    
    print(f"\n✅ {len(links)} links encontrados:\n")
    for link in links:
        print(f"📎 {link.get('title') or link.get('name') or 'Sem nome'}")
        print(f"   ID: {link['id']}")
        print(f"   URL: {link.get('url')}")
        print(f"   Rotator: {link.get('extraOptionsLinkRotator', 'Não configurado')}\n")


def exemplo_2_buscar_por_tag():
    """Exemplo 2: Buscar links por tag"""
    print("\n" + "="*70)
    print("EXEMPLO 2: Buscar por Tag")
    print("="*70)
    
    api = SwitchyAPI()
    
    # Buscar links com tag 'bf25'
    tag = 'bf25'
    links = api.get_links_by_tag(tag)
    
    print(f"\n✅ {len(links)} links com a tag '{tag}' encontrados")


def exemplo_3_top_links():
    """Exemplo 3: Links mais clicados"""
    print("\n" + "="*70)
    print("EXEMPLO 3: Top 10 Links Mais Clicados")
    print("="*70)
    
    api = SwitchyAPI()
    
    top_links = api.get_top_links(limit=10, min_clicks=0)
    
    print(f"\n🏆 Top {len(top_links)} Links:\n")
    for i, link in enumerate(top_links, 1):
        name = link.get('title') or link.get('name') or 'Sem nome'
        clicks = link.get('clicks', 0)
        domain = link.get('domain', 'sw.page')
        uniq = link.get('uniq', '')
        short_url = f"https://{domain}/{uniq}" if uniq else "N/A"
        
        print(f"{i:2d}. {name:40s} | {clicks:5d} clicks | {short_url}")


def exemplo_4_atualizar_url():
    """Exemplo 4: Atualizar URL de um link"""
    print("\n" + "="*70)
    print("EXEMPLO 4: Atualizar URL")
    print("="*70)
    
    api = SwitchyAPI()
    
    # ⚠️ ATENÇÃO: Substitua pelo ID real de um link seu!
    link_id = input("\nDigite o ID do link a atualizar (ou Enter para pular): ").strip()
    
    if not link_id:
        print("⏭️  Exemplo pulado")
        return
    
    nova_url = input("Digite a nova URL: ").strip()
    
    if not nova_url:
        print("❌ URL não fornecida")
        return
    
    confirmacao = input(f"\n⚠️  Atualizar link {link_id} para {nova_url}? (sim/não): ")
    
    if confirmacao.lower() == 'sim':
        result = api.update_link_url(link_id, nova_url)
        
        if result['affected_rows'] > 0:
            print(f"\n✅ Link atualizado com sucesso!")
            print(f"   Linhas afetadas: {result['affected_rows']}")
            if 'returning' in result:
                for link in result['returning']:
                    print(f"   Nova URL: {link['url']}")
        else:
            print("\n⚠️ Nenhum link foi atualizado. Verifique o ID.")
    else:
        print("❌ Operação cancelada")


def exemplo_5_configurar_rotator():
    """Exemplo 5: Configurar Link Rotator"""
    print("\n" + "="*70)
    print("EXEMPLO 5: Configurar Link Rotator")
    print("="*70)
    
    api = SwitchyAPI()
    
    # ⚠️ ATENÇÃO: Substitua pelo ID real de um link seu!
    link_id = input("\nDigite o ID do link para configurar rotator (ou Enter para pular): ").strip()
    
    if not link_id:
        print("⏭️  Exemplo pulado")
        return
    
    print("\nDigite as URLs extras (uma por linha, linha vazia para finalizar):")
    extra_urls = []
    while True:
        url = input(f"URL {len(extra_urls) + 1}: ").strip()
        if not url:
            break
        extra_urls.append(url)
    
    if not extra_urls:
        print("\n⚠️ Nenhuma URL extra fornecida")
        return
    
    # Calcular distribuição
    n = len(extra_urls)
    share = 100 // (n + 1)
    principal = 100 - (share * n)
    
    print(f"\n📊 Distribuição:")
    print(f"   Link principal: {principal}%")
    for i, url in enumerate(extra_urls, 1):
        print(f"   URL {i}: {share}% - {url}")
    
    confirmacao = input("\nConfirmar? (sim/não): ")
    
    if confirmacao.lower() == 'sim':
        result = api.update_link_rotator(link_id, extra_urls)
        
        if result['affected_rows'] > 0:
            print(f"\n✅ Link Rotator configurado com sucesso!")
            if 'returning' in result:
                for link in result['returning']:
                    print(f"\n   Configuração salva:")
                    import json
                    print(json.dumps(link['extraOptionsLinkRotator'], indent=2))
        else:
            print("\n⚠️ Falha ao configurar rotator")
    else:
        print("❌ Operação cancelada")


def exemplo_6_configurar_expiracao():
    """Exemplo 6: Configurar expiração de link"""
    print("\n" + "="*70)
    print("EXEMPLO 6: Configurar Expiração")
    print("="*70)
    
    api = SwitchyAPI()
    
    # ⚠️ ATENÇÃO: Substitua pelo ID real de um link seu!
    link_id = input("\nDigite o ID do link para configurar expiração (ou Enter para pular): ").strip()
    
    if not link_id:
        print("⏭️  Exemplo pulado")
        return
    
    print("\nTipo de expiração:")
    print("1. Por data")
    print("2. Por número de cliques")
    tipo = input("Escolha (1 ou 2): ").strip()
    
    if tipo == '1':
        dias = input("Expira em quantos dias? (default: 30): ").strip()
        dias = int(dias) if dias else 30
        
        expiry_date = datetime.now() + timedelta(days=dias)
        redirect_url = input("URL de redirecionamento após expiração (opcional): ").strip()
        
        print(f"\n📅 Link expirará em: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
        if redirect_url:
            print(f"   Redirecionará para: {redirect_url}")
        
        confirmacao = input("\nConfirmar? (sim/não): ")
        
        if confirmacao.lower() == 'sim':
            result = api.set_link_expiration_by_date(
                link_id,
                expiry_date,
                redirect_url if redirect_url else None
            )
            
            if result['affected_rows'] > 0:
                print("\n✅ Expiração configurada com sucesso!")
            else:
                print("\n⚠️ Falha ao configurar expiração")
        else:
            print("❌ Operação cancelada")
    
    elif tipo == '2':
        max_clicks = input("Número máximo de cliques: ").strip()
        
        if not max_clicks or not max_clicks.isdigit():
            print("❌ Número inválido")
            return
        
        max_clicks = int(max_clicks)
        redirect_url = input("URL de redirecionamento após limite (opcional): ").strip()
        
        print(f"\n🔢 Link expirará após {max_clicks} cliques")
        if redirect_url:
            print(f"   Redirecionará para: {redirect_url}")
        
        confirmacao = input("\nConfirmar? (sim/não): ")
        
        if confirmacao.lower() == 'sim':
            result = api.set_link_expiration_by_clicks(
                link_id,
                max_clicks,
                redirect_url if redirect_url else None
            )
            
            if result['affected_rows'] > 0:
                print("\n✅ Expiração configurada com sucesso!")
            else:
                print("\n⚠️ Falha ao configurar expiração")
        else:
            print("❌ Operação cancelada")
    else:
        print("❌ Opção inválida")


def exemplo_7_estatisticas():
    """Exemplo 7: Estatísticas da conta"""
    print("\n" + "="*70)
    print("EXEMPLO 7: Estatísticas da Conta")
    print("="*70)
    
    api = SwitchyAPI()
    
    stats = api.get_statistics()
    
    print(f"\n📊 ESTATÍSTICAS")
    print(f"   Total de links: {stats['total_links']:,}")
    print(f"   Total de cliques: {stats['total_clicks']:,}")
    print(f"   Média de cliques por link: {stats['average_clicks']:.2f}")
    print(f"   Links sem cliques: {stats['links_without_clicks']} ({stats['percentage_without_clicks']:.1f}%)")


def exemplo_8_buscar_texto():
    """Exemplo 8: Buscar links por texto"""
    print("\n" + "="*70)
    print("EXEMPLO 8: Buscar por Texto")
    print("="*70)
    
    api = SwitchyAPI()
    
    texto = input("\nDigite o texto para buscar (ou Enter para pular): ").strip()
    
    if not texto:
        print("⏭️  Exemplo pulado")
        return
    
    links = api.search_links(texto, limit=10)
    
    print(f"\n✅ {len(links)} links encontrados com '{texto}':\n")
    for link in links:
        name = link.get('title') or link.get('name') or 'Sem nome'
        url = link.get('url', 'N/A')
        print(f"📎 {name}")
        print(f"   URL: {url}\n")


def exemplo_9_dominios_e_pastas():
    """Exemplo 9: Listar domínios e pastas"""
    print("\n" + "="*70)
    print("EXEMPLO 9: Domínios e Pastas")
    print("="*70)
    
    api = SwitchyAPI()
    
    # Domínios
    domains = api.get_domains()
    print(f"\n🌐 DOMÍNIOS ({len(domains)}):")
    for domain in domains:
        print(f"   • {domain['name']}")
    
    # Pastas
    folders = api.get_folders()
    print(f"\n📁 PASTAS ({len(folders)}):")
    for folder in folders:
        desc = f" - {folder['description']}" if folder.get('description') else ""
        print(f"   • {folder['name']} (ID: {folder['id']}){desc}")


def exemplo_10_uso_funcoes_standalone():
    """Exemplo 10: Usar funções standalone (compatibilidade)"""
    print("\n" + "="*70)
    print("EXEMPLO 10: Funções Standalone (Compatibilidade)")
    print("="*70)
    
    # Importar funções standalone
    from switchy_utils import get_links, update_link_url, update_link_rotator
    
    print("\n📦 Usando funções standalone (compatibilidade com código antigo)")
    
    # get_links()
    links = get_links()
    print(f"\n✅ get_links() retornou {len(links)} links")
    
    print("\nFunções disponíveis:")
    print("  • get_links() - Busca links")
    print("  • update_link_url(id, url, deep_linking) - Atualiza URL")
    print("  • update_link_rotator(id, urls) - Configura rotator")


def menu_interativo():
    """Menu interativo para escolher exemplos"""
    exemplos = [
        ("Listar Links", exemplo_1_listar_links),
        ("Buscar por Tag", exemplo_2_buscar_por_tag),
        ("Top Links Mais Clicados", exemplo_3_top_links),
        ("Atualizar URL", exemplo_4_atualizar_url),
        ("Configurar Link Rotator", exemplo_5_configurar_rotator),
        ("Configurar Expiração", exemplo_6_configurar_expiracao),
        ("Estatísticas da Conta", exemplo_7_estatisticas),
        ("Buscar por Texto", exemplo_8_buscar_texto),
        ("Listar Domínios e Pastas", exemplo_9_dominios_e_pastas),
        ("Funções Standalone", exemplo_10_uso_funcoes_standalone),
    ]
    
    while True:
        print("\n" + "="*70)
        print("SWITCHY API - EXEMPLOS PRÁTICOS")
        print("="*70)
        
        print("\nEscolha um exemplo para executar:\n")
        for i, (nome, _) in enumerate(exemplos, 1):
            print(f"  {i:2d}. {nome}")
        print(f"  {len(exemplos) + 1:2d}. Executar todos")
        print("   0. Sair")
        
        escolha = input("\nOpção: ").strip()
        
        if escolha == '0':
            print("\n👋 Até logo!")
            break
        
        if escolha == str(len(exemplos) + 1):
            # Executar todos
            for nome, func in exemplos:
                try:
                    func()
                except KeyboardInterrupt:
                    print("\n⚠️  Exemplo interrompido")
                    break
                except Exception as e:
                    print(f"\n❌ Erro no exemplo '{nome}': {e}")
            
            input("\nPressione Enter para continuar...")
            continue
        
        try:
            idx = int(escolha) - 1
            if 0 <= idx < len(exemplos):
                nome, func = exemplos[idx]
                try:
                    func()
                except KeyboardInterrupt:
                    print("\n⚠️  Exemplo interrompido")
                except Exception as e:
                    print(f"\n❌ Erro: {e}")
                    import traceback
                    traceback.print_exc()
                
                input("\nPressione Enter para continuar...")
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Opção inválida")


def main():
    """Função principal"""
    print("\n🔗 SWITCHY API - EXEMPLOS PRÁTICOS")
    print("="*70)
    
    # Verificar API key
    if not os.getenv("SWITCHY_API_KEY"):
        print("\n⚠️  ATENÇÃO: Variável de ambiente SWITCHY_API_KEY não encontrada!")
        print("\nDefina antes de executar:")
        print('  export SWITCHY_API_KEY="sua-api-key-aqui"')
        print("\nOu configure em um arquivo .env")
        return
    
    try:
        # Testar conexão
        api = SwitchyAPI()
        print("\n✅ Conexão com API estabelecida")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Menu interativo
        menu_interativo()
    
    except ValueError as e:
        print(f"\n❌ Erro de configuração: {e}")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
















