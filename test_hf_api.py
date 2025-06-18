import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("HF_API_TOKEN")
api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": f"Bearer {token}"}
texto = "O Pix é um sistema de pagamentos instantâneos criado pelo Banco Central do Brasil. Ele permite transferências e pagamentos em tempo real, 24 horas por dia, todos os dias."
payload = {
    "inputs": texto,
    "parameters": {"min_length": 50, "max_length": 150}
}

print("Enviando requisição para Hugging Face...")
response = requests.post(api_url, headers=headers, json=payload, timeout=60)
print("Status code:", response.status_code)
print("Resposta bruta:", response.text)
try:
    summary = response.json()
    if isinstance(summary, list) and summary and 'summary_text' in summary[0]:
        print("Resumo:", summary[0]['summary_text'])
    elif isinstance(summary, list) and summary and 'generated_text' in summary[0]:
        print("Resumo:", summary[0]['generated_text'])
    else:
        print("Resposta inesperada:", summary)
except Exception as e:
    print("Erro ao decodificar resposta:", e)
