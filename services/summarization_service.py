from dotenv import load_dotenv
load_dotenv()
import os
import requests

class SummarizationService:
    def __init__(self):
        self.api_token = os.getenv("HF_API_TOKEN")
        self.api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

    def summarize(self, text: str, min_length=100, max_length=300, model: str = None) -> str:
        print(f"[HUGGINGFACE] Chamando summarize com texto de {len(text)} caracteres")
        if not self.api_token:
            print("[HUGGINGFACE] Token não configurado.")
            return "Token da API Hugging Face não configurado. Adicione HF_API_TOKEN ao .env."
        headers = {"Authorization": f"Bearer {self.api_token}"}
        api_url = self.api_url if not model else f"https://api-inference.huggingface.co/models/{model}"
        payload = {
            "inputs": text[:2000],
            "parameters": {"min_length": min_length, "max_length": max_length}
        }
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            print(f"[HUGGINGFACE] Status: {response.status_code}, Response: {response.text}")
            response.raise_for_status()
            summary = response.json()
            if isinstance(summary, list) and summary and 'summary_text' in summary[0]:
                print(f"[HUGGINGFACE] Resumo retornado: {summary[0]['summary_text']}")
                return summary[0]['summary_text']
            if isinstance(summary, list) and summary and 'generated_text' in summary[0]:
                return summary[0]['generated_text']
            print(f"[HUGGINGFACE] Resposta inesperada: {summary}")
            return str(summary)
        except Exception as e:
            print(f"[HUGGINGFACE] Erro: {e}")
            return f"Erro ao resumir: {e}"

    def translate_to_ptbr(self, text: str) -> str:
        """
        Traduz o texto para português do Brasil usando o modelo Helsinki-NLP/opus-mt-en-pt da Hugging Face.
        """
        api_url = "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-en-pt"
        if not self.api_token:
            print("[HUGGINGFACE] Token não configurado para tradução.")
            return text
        headers = {"Authorization": f"Bearer {self.api_token}"}
        payload = {"inputs": text[:2000]}
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            print(f"[HUGGINGFACE] Tradução Status: {response.status_code}, Response: {response.text}")
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list) and result and 'translation_text' in result[0]:
                return result[0]['translation_text']
            return str(result)
        except Exception as e:
            print(f"[HUGGINGFACE] Erro na tradução: {e}")
            return text  # fallback: retorna o texto original
