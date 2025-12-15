"""
Exemplo de uso dos métodos de webhooks do tally_utils.py

Este script demonstra como gerenciar webhooks do Tally.

Pré-requisitos:
    - Configurar a variável de ambiente TALLY_API_KEY
    - Ter um formulário criado no Tally
    - Ter um endpoint público para receber webhooks

Uso:
    python examples/exemplo_tally_webhooks.py
"""

import os
import sys
import json
from datetime import datetime

# Adicionar pasta src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tally_utils import Tally, TallyAPIError


def exemplo_criar_webhook(form_id: str, webhook_url: str):
    """Exemplo 1: Criar um novo webhook"""
    print("\n" + "="*60)
    print("EXEMPLO 1: Criar webhook")
    print("="*60)
    
    try:
        tally = Tally()
        
        webhook = tally.create_webhook(
            form_id=form_id,
            url=webhook_url,
            event_types=['FORM_RESPONSE'],
            signing_secret='meu_segredo_super_secreto_123',
            http_headers=[
                {'name': 'X-Custom-Header', 'value': 'MeuValor'},
                {'name': 'Authorization', 'value': 'Bearer token123'}
            ]
        )
        
        print(f"\n✓ Webhook criado com sucesso!")
        print(f"  ID: {webhook.get('id')}")
        print(f"  URL: {webhook.get('url')}")
        print(f"  Form ID: {webhook.get('formId')}")
        
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
        
        print(f"\n✓ Total de webhooks: {len(webhooks)}")
        
        if webhooks:
            print("\nWebhooks configurados:")
            for i, webhook in enumerate(webhooks, 1):
                status = "🟢 Ativo" if webhook.get('enabled') else "🔴 Inativo"
                print(f"\n  {i}. {status}")
                print(f"     ID: {webhook.get('id')}")
                print(f"     URL: {webhook.get('url')}")
        
        return webhooks
        
    except TallyAPIError as e:
        print(f"❌ Erro: {e}")
        return []


def exemplo_validar_webhook():
    """Exemplo 3: Validar assinatura de webhook"""
    print("\n" + "="*60)
    print("EXEMPLO 3: Validar assinatura de webhook")
    print("="*60)
    
    signing_secret = 'meu_segredo_super_secreto_123'
    
    payload = json.dumps({
        'eventId': 'evt_abc123',
        'eventType': 'FORM_RESPONSE',
        'createdAt': datetime.now().isoformat(),
        'data': {
            'responseId': 'resp_xyz789',
            'formId': 'form_123'
        }
    })
    
    import hmac
    import hashlib
    
    valid_signature = hmac.new(
        signing_secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    try:
        tally = Tally()
        
        print("\n📝 Teste 1: Assinatura válida")
        is_valid = tally.validate_webhook_signature(
            payload=payload,
            signature=valid_signature,
            signing_secret=signing_secret
        )
        print(f"  Resultado: {'✓ Válida' if is_valid else '✗ Inválida'}")
        
        print("\n💡 Exemplo de uso em Flask:")
        print("""
        @app.route('/webhook/tally', methods=['POST'])
        def tally_webhook():
            payload = request.data.decode('utf-8')
            signature = request.headers.get('X-Tally-Signature')
            
            if not tally.validate_webhook_signature(payload, signature, 'seu_segredo'):
                return {'error': 'Invalid signature'}, 401
            
            data = request.json
            # Processar webhook...
            return {'status': 'success'}, 200
        """)
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("EXEMPLOS DE USO: Webhooks do Tally")
    print("="*60)
    
    if not os.getenv('TALLY_API_KEY'):
        print("\n❌ ERRO: Variável de ambiente TALLY_API_KEY não encontrada!")
        print("\nPara configurar:")
        print("  export TALLY_API_KEY='sua_chave_aqui'")
        return
    
    print("\n✓ API Key configurada")
    
    # Exemplo sempre executado
    exemplo_validar_webhook()
    
    # Para executar outros exemplos, descomente e configure:
    # FORM_ID = 'seu_form_id_aqui'
    # WEBHOOK_URL = 'https://webhook.site/unique-url'
    # webhook = exemplo_criar_webhook(FORM_ID, WEBHOOK_URL)
    # exemplo_listar_webhooks()
    
    print("\n" + "="*60)
    print("✓ Exemplos concluídos!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()

