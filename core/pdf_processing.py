from .file_processing_template import FileProcessingTemplate
from services.summarization_service import SummarizationService
from strategies.adaptation_factory import AdaptationFactory
from core.file_handler import FileHandler
import asyncio

class PDFProcessing(FileProcessingTemplate):
    def __init__(self):
        self.handler = FileHandler()
        self.summarizer = SummarizationService()

    def read_file(self, filename: str) -> str:
        return self.handler.read_pdf_file(filename)

    def summarize(self, content: str) -> str:
        return self.summarizer.summarize(content)

    def adapt(self, resumo: str, audiencia: str) -> str:
        strategy = AdaptationFactory.get_strategy(audiencia)
        # Adaptation strategies são assíncronas, mas Template Method é síncrono por padrão
        # Para uso real, adapte para async/await conforme necessário
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(strategy.adapt(resumo))
