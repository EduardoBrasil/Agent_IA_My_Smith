import unittest
from unittest.mock import patch, MagicMock
from services.file_handler_service import FileHandlerService

class TestFileHandlerService(unittest.TestCase):
    def setUp(self):
        self.service = FileHandlerService()

    @patch('services.file_handler_service.FileHandler')
    @patch('services.file_handler_service.SummarizationService')
    def test_get_txt_preview(self, MockSummarizer, MockFileHandler):
        mock_handler = MockFileHandler.return_value
        mock_handler.read_any_file.return_value = 'Conteúdo do arquivo: Texto de teste.'
        mock_summarizer = MockSummarizer.return_value
        mock_summarizer.summarize.return_value = 'Resumo.'
        service = FileHandlerService()
        service.handler = mock_handler
        service.summarizer = mock_summarizer
        result = service.get_txt_preview('arquivo.txt')
        self.assertIn('Resumo.', result)

    @patch('services.file_handler_service.FileHandler')
    def test_read_any_file_not_found(self, MockFileHandler):
        mock_handler = MockFileHandler.return_value
        mock_handler.read_any_file.return_value = "Arquivo 'inexistente.pdf' não encontrado no workspace ou caminho absoluto não existe."
        result = self.service.read_any_file('inexistente.pdf')
        self.assertIn('não encontrado', result)

    @patch('services.file_handler_service.FileHandler')
    def test_read_pdf_file_not_found(self, MockFileHandler):
        mock_handler = MockFileHandler.return_value
        mock_handler.read_pdf_file.return_value = "PDF 'inexistente.pdf' não encontrado no workspace ou caminho absoluto não existe."
        result = self.service.read_pdf_file('inexistente.pdf')
        self.assertIn('não encontrado', result)

    @patch('services.file_handler_service.SummarizationService')
    @patch('services.file_handler_service.FileHandler')
    def test_get_audience_adaptation(self, MockFileHandler, MockSummarizer):
        mock_handler = MockFileHandler.return_value
        mock_summarizer = MockSummarizer.return_value
        mock_summarizer.summarize.return_value = 'Texto adaptado.'
        service = FileHandlerService()
        service.handler = mock_handler
        service.summarizer = mock_summarizer
        result = service.get_audience_adaptation('Texto técnico', 'comercial')
        self.assertIn('Texto adaptado.', result)

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

    @patch('services.file_handler_service.load_prompt', side_effect=[
        'Prompt Comercial: {texto}',
        'Prompt Suporte: {texto}',
        'Prompt PM: {texto}'
    ])
    @patch('services.file_handler_service.FileHandler', return_value=MagicMock())
    @patch('services.file_handler_service.SummarizationService')
    def test_get_audience_adaptations_success(self, MockSummarizer, MockFileHandler, mock_load_prompt):
        mock_handler = MockFileHandler.return_value
        mock_summarizer = MockSummarizer.return_value
        mock_summarizer.translate_to_ptbr.side_effect = lambda x: x + ' PTBR'
        mock_summarizer.summarize.side_effect = lambda prompt, **kwargs: f"Resumo de {prompt[:20]}"
        mock_summarizer.translate_to_ptbr.side_effect = lambda x: x + ' PTBR'
        service = FileHandlerService()
        service.handler = mock_handler
        service.summarizer = mock_summarizer
        result = service.get_audience_adaptations('Texto técnico')
        self.assertIn('comercial', result)
        self.assertIn('suporte', result)
        self.assertIn('pm', result)
        for v in result.values():
            self.assertIn('Resumo de', v)

    @patch('services.file_handler_service.FileHandler')
    @patch('services.file_handler_service.SummarizationService')
    def test_get_txt_preview_empty(self, MockSummarizer, MockFileHandler):
        mock_handler = MockFileHandler.return_value
        mock_handler.read_any_file.return_value = ''
        mock_summarizer = MockSummarizer.return_value
        mock_summarizer.summarize.return_value = ''
        service = FileHandlerService()
        service.handler = mock_handler
        service.summarizer = mock_summarizer
        result = service.get_txt_preview('arquivo.txt')
        self.assertIn('Conteúdo do arquivo resumido', result)

if __name__ == '__main__':
    unittest.main()
