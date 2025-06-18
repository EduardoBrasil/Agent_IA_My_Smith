import os
import requests

class HuggingFaceAdapter:
    def __init__(self, api_token=None):
        self.api_token = api_token or os.getenv("HF_API_TOKEN")

    def summarize(self, text: str, min_length=100, max_length=2048, model: str = None) -> str:
        api_url = f"https://api-inference.huggingface.co/models/{model or 'facebook/bart-large-cnn'}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        payload = {
            "inputs": text[:2000],
            "parameters": {"min_length": min_length, "max_length": max_length}
        }
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            summary = response.json()
            if isinstance(summary, list) and summary and 'summary_text' in summary[0]:
                return summary[0]['summary_text']
            if isinstance(summary, list) and summary and 'generated_text' in summary[0]:
                return summary[0]['generated_text']
            return ""
        except Exception:
            return ""

    def translate_to_ptbr(self, text: str) -> str:
        api_url = "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-en-pt"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        payload = {"inputs": text[:2000]}
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list) and result and 'translation_text' in result[0]:
                return result[0]['translation_text']
            if isinstance(result, list) and result and 'generated_text' in result[0]:
                return result[0]['generated_text']
            return text
        except Exception:
            return text
