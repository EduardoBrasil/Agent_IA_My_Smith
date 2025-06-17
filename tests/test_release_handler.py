import unittest
from unittest.mock import patch, MagicMock
import release_handler

class TestReleaseHandler(unittest.TestCase):
    @patch('release_handler.client')
    @patch('release_handler.read_prompt')
    def test_generate_document(self, mock_read_prompt, mock_client):
        mock_read_prompt.return_value = 'Prompt: {mensagem}'
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='Conteúdo gerado'))]
        mock_client.chat.completions.create.return_value = mock_response
        with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            release_handler.generate_document('Prompt: {mensagem}', 'msg', 'saida.txt')
            mock_open.assert_called_with('saida.txt', 'w', encoding='utf-8')
            mock_open().write.assert_called_with('Conteúdo gerado')

    @patch('release_handler.read_prompt')
    @patch('release_handler.generate_document')
    def test_generate_documents(self, mock_generate_document, mock_read_prompt):
        mock_read_prompt.side_effect = lambda name: f'Prompt: {{{name}}}'
        release_handler.generate_documents('mensagem')
        self.assertEqual(mock_generate_document.call_count, 3)
        mock_generate_document.assert_any_call('Prompt: {cliente}', 'mensagem', release_handler.OUTPUTS_DIR / 'cliente_output.txt')
        mock_generate_document.assert_any_call('Prompt: {comercial}', 'mensagem', release_handler.OUTPUTS_DIR / 'comercial_output.txt')
        mock_generate_document.assert_any_call('Prompt: {suporte}', 'mensagem', release_handler.OUTPUTS_DIR / 'suporte_output.txt')

if __name__ == '__main__':
    unittest.main()
