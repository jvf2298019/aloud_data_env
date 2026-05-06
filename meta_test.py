import requests
import datetime
import time
import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega o .env do diretório config
env_path = Path(__file__).resolve().parent / "config" / ".env"
load_dotenv(dotenv_path=env_path)

# --- CONFIGURAÇÕES ---
ACCESS_TOKEN = "EAAWZC9OAXbIIBQ1szypZAOD3rsQMKT039Fuj40zZCHA6sG1BlCVfImSbGZA4LKIfaoANZA18OsroWOzspBcihln0vmpguJRZCe9a4BAf3svs2BUpJzfZA21yUPTBybS6kZCP4nq5vYCjS7ikngL0IpwZCAGXpyzt965xoqbf3Iy1ObvUDbNYeQYMYm4cZC6lzmp4ZBOyr2YY1wZAxa9HYdQZBgzsPxeiJTKEB5oov4GUfNwLEF4JKYHHckbOZBHJ0QFIZC263aIJnGgi3O9NNJ1xtlErkYMBwZDZD"

if not ACCESS_TOKEN:
    raise ValueError(
        f"META_ACCESS_TOKEN não encontrado!\n"
        f"Crie um arquivo .env em: {env_path}\n"
        f"Com o conteúdo: META_ACCESS_TOKEN=seu_token_aqui"
    )
WABA_ID = "1587777142592196"
TEMPLATE_IDS = ["1672388187259466"] # ppt_lpm_cdf_autoapproach

# Definir intervalo de datas (Ex: Últimos 7 dias)
today = datetime.datetime.now()
seven_days_ago = today - datetime.timedelta(days=7)

# Converter para UNIX Timestamp (exigência da API)
start_timestamp = int(time.mktime(seven_days_ago.timetuple()))
end_timestamp = int(time.mktime(today.timetuple()))

# --- MONTAGEM DA REQUISIÇÃO ---
url = f"https://graph.facebook.com/v21.0/{WABA_ID}"

# 1. HEADERS: Onde a autenticação deve estar
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 2. PARAMS: Apenas os filtros de dados
# O formato de template_ids precisa ser uma string representando a lista
template_ids_str = ",".join(TEMPLATE_IDS)
params = {
    "fields": f"template_analytics.start({start_timestamp}).end({end_timestamp}).granularity(DAILY).template_ids({template_ids_str})"
}

try:
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status() # Levanta erro se não for 200 OK
    
    data = response.json()
    
    # Processando os dados
    if "template_analytics" in data:
        analytics = data["template_analytics"]
        points = analytics["data"][0]["data_points"]
        print(f"{'DATA':<12} | {'TEMPLATE ID':<15} | {'ENVIADOS':<8} | {'ENTREGUES':<9} | {'LIDOS':<5} | {'CLIQUES':<7}")
        print("-" * 75)
        
        for p in points:
            # Converter timestamp de volta para data legível
            date_str = datetime.datetime.fromtimestamp(p['start']).strftime('%d/%m/%Y')
            print(f"{date_str:<12} | {p.get('template_id', 'N/A'):<15} | {p.get('sent', 0):<8} | {p.get('delivered', 0):<9} | {p.get('read', 0):<5} | {p.get('clicked', 0):<7}")
    else:
        print("Nenhum dado de analíticos encontrado.")

except requests.exceptions.HTTPError as err:
    print(f"Erro na requisição: {err}")
    print(response.text)