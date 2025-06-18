from .adaptation_strategy import AdaptationStrategy
from prompts.prompt_loader import load_prompt
from services.summarization_service import SummarizationService
import asyncio

class SuporteStrategy(AdaptationStrategy):
    def __init__(self):
        self.prompt_template = load_prompt('suporte')
        self.summarizer = SummarizationService()

    async def adapt(self, texto: str) -> str:
        prompt = self.prompt_template.replace('{texto}', texto[:1000])
        adaptacao_en = await asyncio.to_thread(self.summarizer.summarize, prompt, min_length=200, max_length=600)
        adaptacao = await asyncio.to_thread(self.summarizer.translate_to_ptbr, adaptacao_en)
        for trecho in [self.prompt_template, prompt, 'Texto técnico:', texto]:
            if trecho and isinstance(adaptacao, str):
                adaptacao = adaptacao.replace(trecho, '').strip()
        return adaptacao
