"""
Exemplo de uso dos métodos de webhooks do tally_utils.py

Este script demonstra como gerenciar webhooks do Tally:
- Criar webhooks
- Listar webhooks existentes
- Obter detalhes de webhooks
- Atualizar webhooks
- Deletar webhooks
- Listar eventos de webhooks
- Reenviar eventos falhados
- Validar assinaturas de webhooks

Pré-requisitos:
    - Configurar a variável de ambiente TALLY_API_KEY
    - Ter um formulário criado no Tally
    - Ter um endpoint público para receber webhooks (para testes reais)

Uso:
    python examples/exemplo_tally_webhooks.py
"""

import os
import sys

# Adicionar pasta src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tally_utils import Tally, TallyAPIError
import json
from datetime import datetime


def exemplo_criar_webhook(form_id: str, webhook_url: str):
    """Exemplo 1: Criar um novo webhook"""
    print("\n" + "="*60)
    print("EXEMPLO 1: Criar webhook")
    print("="*60)
    
    try:
        tally = Tally()
        
        # Criar webhook com configurações completas
        webhook = tally.create_webhook(
            form_id=form_id,
            url=webhook_url,
            event_types=['FORM_RESPONSE'],  # Evento de resposta do formulário
            signing_secret='meu_segredo_super_secreto_123',
            http_headers=[
                {'name': 'X-Custom-Header', 'value': 'MeuValor'},
                {'name': 'Authorization', 'value': 'Bearer token123'}
            ],
            external_subscriber='sistema_crm_v1'
        )
        
        print(f"\n✓ Webhook criado com sucesso!")
        print(f"  ID: {webhook.get('id')}")
        print(f"  URL: {webhook.get('url')}")
        print(f"  Form ID: {webhook.get('formId')}")
        print(f"  Eventos: {webhook.get('eventTypes')}")
        print(f"  Status: {'Ativo' if webhook.get('enabled') else 'Inativo'}")
        
        return webhook
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return None


def exemplo_listar_webhooks():
    """Exemplo 2: Listar todos os webhooks"""
    print("\n" + "="*60)
    print("EXEMPLO 2: Listar webhooks")
    print("="*60)
    
    try:
        tally = Tally()
        result = tally.list_webhooks(page=1, limit=50)
        
        webhooks = result.get('data', [])
        pagination = result.get('pagination', {})
        
        print(f"\n✓ Total de webhooks: {len(webhooks)}")
        
        if webhooks:
            print("\nWebhooks configurados:")
            for i, webhook in enumerate(webhooks, 1):
                status = "🟢 Ativo" if webhook.get('enabled') else "🔴 Inativo"
                print(f"\n  {i}. {status}")
                print(f"     ID: {webhook.get('id')}")
                print(f"     URL: {webhook.get('url')}")
                print(f"     Form ID: {webhook.get('formId')}")
                print(f"     Eventos: {', '.join(webhook.get('eventTypes', []))}")
                print(f"     Criado em: {webhook.get('createdAt', 'N/A')}")
        
        if pagination:
            print(f"\nPaginação:")
            print(f"  Página atual: {pagination.get('page', 1)}")
            print(f"  Total de páginas: {pagination.get('totalPages', 1)}")
        
        return webhooks
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return []


def exemplo_obter_webhook(webhook_id: str):
    """Exemplo 3: Obter detalhes de um webhook específico"""
    print("\n" + "="*60)
    print(f"EXEMPLO 3: Obter detalhes do webhook {webhook_id}")
    print("="*60)
    
    try:
        tally = Tally()
        webhook = tally.get_webhook(webhook_id)
        
        print(f"\n✓ Webhook encontrado:")
        print(f"  ID: {webhook.get('id')}")
        print(f"  URL: {webhook.get('url')}")
        print(f"  Form ID: {webhook.get('formId')}")
        print(f"  Eventos: {', '.join(webhook.get('eventTypes', []))}")
        print(f"  Status: {'Ativo' if webhook.get('enabled') else 'Inativo'}")
        print(f"  Subscriber: {webhook.get('externalSubscriber', 'N/A')}")
        
        # Headers customizados
        headers = webhook.get('httpHeaders', [])
        if headers:
            print(f"\n  Headers customizados:")
            for header in headers:
                print(f"    - {header.get('name')}: {header.get('value')}")
        
        return webhook
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return None


def exemplo_atualizar_webhook(webhook_id: str):
    """Exemplo 4: Atualizar um webhook existente"""
    print("\n" + "="*60)
    print(f"EXEMPLO 4: Atualizar webhook {webhook_id}")
    print("="*60)
    
    try:
        tally = Tally()
        
        # Atualizar apenas campos específicos
        webhook = tally.update_webhook(
            webhook_id=webhook_id,
            url='https://novosite.com/webhook-endpoint',
            enabled=True,  # Ativar webhook
            event_types=['FORM_RESPONSE', 'FORM_UPDATED']  # Adicionar mais eventos
        )
        
        print(f"\n✓ Webhook atualizado com sucesso!")
        print(f"  Nova URL: {webhook.get('url')}")
        print(f"  Status: {'Ativo' if webhook.get('enabled') else 'Inativo'}")
        print(f"  Eventos: {', '.join(webhook.get('eventTypes', []))}")
        
        return webhook
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return None


def exemplo_listar_eventos_webhook(webhook_id: str):
    """Exemplo 5: Listar eventos de um webhook"""
    print("\n" + "="*60)
    print(f"EXEMPLO 5: Listar eventos do webhook {webhook_id}")
    print("="*60)
    
    try:
        tally = Tally()
        result = tally.list_webhook_events(webhook_id, page=1, limit=20)
        
        events = result.get('data', [])
        
        print(f"\n✓ Total de eventos: {len(events)}")
        
        if events:
            print("\nEventos recentes:")
            for i, event in enumerate(events[:10], 1):
                status_icon = "✓" if event.get('status') == 'success' else "✗"
                print(f"\n  {i}. {status_icon} {event.get('eventType', 'N/A')}")
                print(f"     ID: {event.get('id')}")
                print(f"     Status: {event.get('status', 'N/A')}")
                print(f"     Data: {event.get('createdAt', 'N/A')}")
                print(f"     Tentativas: {event.get('attempts', 0)}")
                
                # Detalhes de erro, se houver
                if event.get('error'):
                    print(f"     Erro: {event.get('error')}")
        else:
            print("\n⚠️  Nenhum evento encontrado ainda")
        
        return events
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return []


def exemplo_reenviar_evento(webhook_id: str, event_id: str):
    """Exemplo 6: Reenviar um evento que falhou"""
    print("\n" + "="*60)
    print(f"EXEMPLO 6: Reenviar evento {event_id}")
    print("="*60)
    
    try:
        tally = Tally()
        result = tally.retry_webhook_event(webhook_id, event_id)
        
        print(f"\n✓ Evento reenviado com sucesso!")
        print(f"  Status: {result.get('status', 'success')}")
        
        return result
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return None


def exemplo_validar_webhook():
    """Exemplo 7: Validar assinatura de webhook"""
    print("\n" + "="*60)
    print("EXEMPLO 7: Validar assinatura de webhook")
    print("="*60)
    
    # Simular dados recebidos em um webhook
    signing_secret = 'meu_segredo_super_secreto_123'
    
    # Payload simulado (JSON string)
    payload = json.dumps({
        'eventId': 'evt_abc123',
        'eventType': 'FORM_RESPONSE',
        'createdAt': datetime.now().isoformat(),
        'data': {
            'responseId': 'resp_xyz789',
            'formId': 'form_123',
            'fields': [
                {'label': 'Nome', 'value': 'João Silva'},
                {'label': 'Email', 'value': 'joao@example.com'}
            ]
        }
    })
    
    # Gerar assinatura válida
    import hmac
    import hashlib
    
    valid_signature = hmac.new(
        signing_secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Assinatura inválida para teste
    invalid_signature = 'assinatura_invalida_123'
    
    try:
        tally = Tally()
        
        # Teste 1: Validar assinatura válida
        print("\n📝 Teste 1: Assinatura válida")
        is_valid = tally.validate_webhook_signature(
            payload=payload,
            signature=valid_signature,
            signing_secret=signing_secret
        )
        print(f"  Resultado: {'✓ Válida' if is_valid else '✗ Inválida'}")
        
        # Teste 2: Validar assinatura inválida
        print("\n📝 Teste 2: Assinatura inválida")
        is_valid = tally.validate_webhook_signature(
            payload=payload,
            signature=invalid_signature,
            signing_secret=signing_secret
        )
        print(f"  Resultado: {'✓ Válida' if is_valid else '✗ Inválida (esperado)'}")
        
        print("\n💡 Exemplo de uso em seu endpoint:")
        print("""
        from flask import Flask, request
        from src.tally_utils import Tally
        
        app = Flask(__name__)
        tally = Tally()
        
        @app.route('/webhook/tally', methods=['POST'])
        def tally_webhook():
            # Obter dados da requisição
            payload = request.data.decode('utf-8')
            signature = request.headers.get('X-Tally-Signature')
            
            # Validar assinatura
            if not tally.validate_webhook_signature(
                payload=payload,
                signature=signature,
                signing_secret='seu_segredo'
            ):
                return {'error': 'Invalid signature'}, 401
            
            # Processar webhook
            data = request.json
            print(f"Novo formulário recebido: {data['eventId']}")
            
            return {'status': 'success'}, 200
        """)
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def exemplo_deletar_webhook(webhook_id: str):
    """Exemplo 8: Deletar um webhook"""
    print("\n" + "="*60)
    print(f"EXEMPLO 8: Deletar webhook {webhook_id}")
    print("="*60)
    print("\n⚠️  ATENÇÃO: Este exemplo deleta um webhook real!")
    print("Descomente o código para executar.")
    
    # Descomente para deletar
    """
    try:
        tally = Tally()
        success = tally.delete_webhook(webhook_id)
        
        if success:
            print(f"\n✓ Webhook {webhook_id} deletado com sucesso!")
        
        return success
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return False
    """
    
    print("\n⏸️  Exemplo desabilitado por segurança")


def exemplo_fluxo_completo():
    """Exemplo 9: Fluxo completo de gerenciamento de webhook"""
    print("\n" + "="*60)
    print("EXEMPLO 9: Fluxo completo de webhook")
    print("="*60)
    
    print("\n📋 Este exemplo demonstra um fluxo completo:")
    print("  1. Criar webhook")
    print("  2. Verificar webhook criado")
    print("  3. Listar eventos")
    print("  4. Atualizar webhook")
    print("  5. Desativar webhook")
    
    print("\n💡 Para implementar em produção:")
    print("""
    # 1. Criar webhook ao inicializar sistema
    tally = Tally()
    webhook = tally.create_webhook(
        form_id='seu_form_id',
        url='https://seusite.com/webhook',
        event_types=['FORM_RESPONSE'],
        signing_secret='segredo_unico_gerado'
    )
    
    # 2. Salvar webhook_id no banco de dados
    save_to_database({
        'webhook_id': webhook['id'],
        'form_id': webhook['formId'],
        'created_at': webhook['createdAt']
    })
    
    # 3. Monitorar eventos periodicamente
    events = tally.list_webhook_events(webhook['id'])
    failed_events = [e for e in events['data'] if e['status'] == 'failed']
    
    # 4. Reenviar eventos falhados
    for event in failed_events:
        tally.retry_webhook_event(webhook['id'], event['id'])
    
    # 5. Limpar webhooks antigos ao desativar funcionalidade
    tally.delete_webhook(webhook['id'])
    """)


def main():
    """Função principal - executar exemplos"""
    print("\n" + "="*60)
    print("EXEMPLOS DE USO: Webhooks do Tally")
    print("="*60)
    
    # Verificar se a API key está configurada
    if not os.getenv('TALLY_API_KEY'):
        print("\n❌ ERRO: Variável de ambiente TALLY_API_KEY não encontrada!")
        print("\nPara configurar:")
        print("  export TALLY_API_KEY='sua_chave_aqui'")
        return
    
    print("\n✓ API Key configurada")
    
    # Configurações de teste (AJUSTE CONFORME SEU AMBIENTE)
    FORM_ID = 'seu_form_id_aqui'  # Substitua pelo ID do seu formulário
    WEBHOOK_URL = 'https://webhook.site/unique-url'  # Use webhook.site para testes
    
    print("\n⚠️  IMPORTANTE:")
    print(f"  - Certifique-se de ter um formulário (ID: {FORM_ID})")
    print(f"  - Use um endpoint válido (ex: {WEBHOOK_URL})")
    print(f"  - Para testes, recomendamos: https://webhook.site")
    
    # Exemplo 1: Criar webhook (comentado por segurança)
    print("\n" + "="*60)
    print("Para executar os exemplos:")
    print("1. Ajuste FORM_ID e WEBHOOK_URL no código")
    print("2. Descomente os exemplos que deseja testar")
    print("3. Execute o script novamente")
    print("="*60)
    
    # Descomente para executar:
    """
    # Criar webhook
    webhook = exemplo_criar_webhook(FORM_ID, WEBHOOK_URL)
    
    if webhook:
        webhook_id = webhook['id']
        
        # Listar todos webhooks
        exemplo_listar_webhooks()
        
        # Obter detalhes do webhook criado
        exemplo_obter_webhook(webhook_id)
        
        # Atualizar webhook
        exemplo_atualizar_webhook(webhook_id)
        
        # Listar eventos do webhook
        events = exemplo_listar_eventos_webhook(webhook_id)
        
        # Se houver eventos, tentar reenviar o primeiro
        if events:
            exemplo_reenviar_evento(webhook_id, events[0]['id'])
        
        # Deletar webhook (cuidado!)
        # exemplo_deletar_webhook(webhook_id)
    """
    
    # Exemplos que não precisam de webhook real:
    
    # Exemplo 7: Validar assinatura (sempre executado)
    exemplo_validar_webhook()
    
    # Exemplo 9: Fluxo completo (documentação)
    exemplo_fluxo_completo()
    
    print("\n" + "="*60)
    print("✓ Exemplos concluídos!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()

