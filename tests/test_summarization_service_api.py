import unittest
from unittest.mock import patch, MagicMock
from services.summarization_service import SummarizationService
import requests

class TestSummarizationServiceAPI(unittest.TestCase):
    def setUp(self):
        self.service = SummarizationService()

    @patch('requests.post')
    def test_summarize_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"summary_text": "Resumo gerado pela IA."}]
        mock_post.return_value = mock_response
        result = self.service.summarize("Texto de teste.")
        self.assertIn("Resumo gerado pela IA.", result)

    @patch('requests.post')
    def test_summarize_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("Erro 500")
        mock_post.return_value = mock_response
        result = self.service.summarize("Texto de teste.")
        self.assertIn("Erro ao resumir", result)

    @patch('requests.post')
    def test_translate_to_ptbr_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"translation_text": "Texto traduzido."}]
        mock_post.return_value = mock_response
        result = self.service.translate_to_ptbr("Test text.")
        self.assertIn("Texto traduzido.", result)

    @patch('requests.post')
    def test_translate_to_ptbr_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("Erro 404")
        mock_post.return_value = mock_response
        result = self.service.translate_to_ptbr("Test text.")
        self.assertIn("Test text.", result)  # fallback retorna o texto original

    def test_token_not_configured(self):
        service = SummarizationService()
        service.api_token = None
        result = service.summarize('texto')
        self.assertIn('Token da API Hugging Face não configurado', result)

    @patch('requests.post', side_effect=Exception('timeout'))
    def test_summarize_exception(self, mock_post):
        service = SummarizationService()
        service.api_token = 'fake'
        result = service.summarize('texto')
        self.assertIn('Erro ao resumir', result)

    @patch('requests.post', side_effect=Exception('timeout'))
    def test_translate_to_ptbr_exception(self, mock_post):
        service = SummarizationService()
        service.api_token = 'fake'
        result = service.translate_to_ptbr('texto')
        self.assertEqual(result, 'texto')

    @patch('requests.post')
    def test_summarize_unexpected_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"foo": "bar"}]
        mock_post.return_value = mock_response
        service = SummarizationService()
        service.api_token = 'fake'
        result = service.summarize('texto')
        self.assertIn('foo', result)

    @patch('requests.post')
    def test_translate_to_ptbr_token_not_configured(self, mock_post):
        service = SummarizationService()
        service.api_token = None
        result = service.translate_to_ptbr('texto')
        self.assertEqual(result, 'texto')

if __name__ == '__main__':
    unittest.main()
    # python -m unittest discover tests -v

