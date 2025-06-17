import unittest
from unittest.mock import patch, MagicMock
from services.file_handler_service import FileHandlerService

class TestFileHandlerServiceIntegration(unittest.TestCase):
    def setUp(self):
        self.service = FileHandlerService()

    @patch('services.file_handler_service.FileHandler')
    @patch('services.file_handler_service.SummarizationService')
    def test_get_pdf_preview_success(self, MockSummarizer, MockFileHandler):
        mock_handler = MockFileHandler.return_value
        # Retorna texto extraído com mais de 50 caracteres
        mock_handler.read_pdf_file.return_value = 'Conteúdo do PDF: ' + ('Texto extraído. ' * 10)
        mock_summarizer = MockSummarizer.return_value
        mock_summarizer.summarize.return_value = 'Resumo IA.'
        service = FileHandlerService()
        service.handler = mock_handler
        service.summarizer = mock_summarizer
        result = service.get_pdf_preview('arquivo.pdf')
        self.assertIn('Resumo IA', result)

    @patch('services.file_handler_service.FileHandler')
    def test_get_pdf_preview_not_found(self, MockFileHandler):
        mock_handler = MockFileHandler.return_value
        mock_handler.read_pdf_file.return_value = "PDF 'inexistente.pdf' não encontrado no workspace ou caminho absoluto não existe."
        result = self.service.get_pdf_preview('inexistente.pdf')
        self.assertIn('não encontrado', result)

    @patch('services.file_handler_service.FileHandler')
    @patch('services.file_handler_service.SummarizationService')
    def test_get_any_file_preview_success(self, MockSummarizer, MockFileHandler):
        mock_handler = MockFileHandler.return_value
        mock_handler.read_any_file.return_value = 'Conteúdo do arquivo: Texto.'
        mock_summarizer = MockSummarizer.return_value
        mock_summarizer.summarize.return_value = 'Resumo IA.'
        service = FileHandlerService()
        service.handler = mock_handler
        service.summarizer = mock_summarizer
        result = service.get_any_file_preview('arquivo.txt')
        self.assertIn('Resumo IA', result)

    @patch('services.file_handler_service.FileHandler')
    @patch('services.file_handler_service.SummarizationService')
    def test_get_pdf_preview_texto_insuficiente(self, MockSummarizer, MockFileHandler):
        mock_handler = MockFileHandler.return_value
        mock_handler.read_pdf_file.return_value = 'Conteúdo do PDF: curto'
        service = FileHandlerService()
        service.handler = mock_handler
        service.summarizer = MockSummarizer.return_value
        result = service.get_pdf_preview('arquivo.pdf')
        self.assertIn('Não foi possível extrair texto útil', result)

    @patch('services.file_handler_service.FileHandler')
    @patch('services.file_handler_service.SummarizationService')
    def test_get_pdf_preview_erro_summarizer(self, MockSummarizer, MockFileHandler):
        mock_handler = MockFileHandler.return_value
        mock_handler.read_pdf_file.return_value = 'Conteúdo do PDF: ' + ('Texto extraído. ' * 10)
        mock_summarizer = MockSummarizer.return_value
        mock_summarizer.summarize.side_effect = Exception('erro')
        service = FileHandlerService()
        service.handler = mock_handler
        service.summarizer = mock_summarizer
        result = service.get_pdf_preview('arquivo.pdf')
        self.assertIn('A IA demorou demais para responder ou houve falha', result)

    @patch('services.file_handler_service.FileHandler')
    @patch('services.file_handler_service.SummarizationService')
    def test_get_any_file_preview_error(self, MockSummarizer, MockFileHandler):
        mock_handler = MockFileHandler.return_value
        mock_handler.read_any_file.return_value = 'Erro ao ler o arquivo'
        service = FileHandlerService()
        service.handler = mock_handler
        service.summarizer = MockSummarizer.return_value
        result = service.get_any_file_preview('arquivo.txt')
        self.assertIn('Erro ao ler o arquivo', result)

    @patch('services.file_handler_service.load_prompt', return_value='Prompt: {texto}')
    @patch('services.file_handler_service.FileHandler', return_value=MagicMock())
    @patch('services.file_handler_service.SummarizationService')
    def test_get_audience_adaptations_erro(self, MockSummarizer, MockFileHandler, mock_load_prompt):
        mock_handler = MockFileHandler.return_value
        mock_summarizer = MockSummarizer.return_value
        mock_summarizer.summarize.side_effect = Exception('erro')
        mock_summarizer.translate_to_ptbr.return_value = 'Texto técnico'
        service = FileHandlerService()
        service.handler = mock_handler
        service.summarizer = mock_summarizer
        result = service.get_audience_adaptations('Texto técnico')
        for v in result.values():
            self.assertIn('Falha ao adaptar', v)

if __name__ == '__main__':
    unittest.main()
