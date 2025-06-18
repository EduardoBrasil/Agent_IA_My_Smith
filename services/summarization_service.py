from dotenv import load_dotenv
load_dotenv()
import os
from adapters.huggingface_adapter import HuggingFaceAdapter

class SummarizationService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.api_token = os.getenv("HF_API_TOKEN")
        self.api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        self.adapter = HuggingFaceAdapter(self.api_token)

    def summarize(self, text: str, min_length=100, max_length=300, model: str = None) -> str:
        return self.adapter.summarize(text, min_length, max_length, model)

    def translate_to_ptbr(self, text: str) -> str:
        return self.adapter.translate_to_ptbr(text)
