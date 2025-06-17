import unittest
from unittest.mock import patch, MagicMock
from core.file_handler import FileHandler
import os

class TestFileHandler(unittest.TestCase):
    def setUp(self):
        self.handler = FileHandler()

    @patch('os.path.isfile')
    @patch('os.path.isabs')
    def test_find_file_absolute(self, mock_isabs, mock_isfile):
        mock_isabs.return_value = True
        mock_isfile.return_value = True
        result = self.handler._find_file('/tmp/test.txt')
        self.assertEqual(result, '/tmp/test.txt')

    @patch('os.walk')
    def test_find_file_relative(self, mock_walk):
        mock_walk.return_value = [('.', [], ['arquivo.txt'])]
        result = self.handler._find_file('arquivo.txt', extensions=['.txt'])
        self.assertIn('arquivo.txt', result)

    def test_normalize(self):
        s = 'Café'
        normalized = self.handler._normalize(s)
        self.assertEqual(normalized, 'cafe')

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='conteudo')
    @patch('os.path.isfile')
    @patch('os.path.isabs')
    def test_read_any_file_txt(self, mock_isabs, mock_isfile, mock_open):
        mock_isabs.return_value = True
        mock_isfile.return_value = True
        result = self.handler.read_any_file('/tmp/test.txt')
        self.assertIn('Conteúdo do arquivo', result)

    @patch('core.file_handler.FileHandler.read_pdf_file')
    @patch('core.file_handler.FileHandler._find_file')
    def test_read_any_file_pdf(self, mock_find_file, mock_read_pdf):
        mock_find_file.return_value = 'arquivo.pdf'
        mock_read_pdf.return_value = 'Conteúdo do PDF: ...'
        handler = FileHandler()
        result = handler.read_any_file('arquivo.pdf')
        self.assertIn('Conteúdo do PDF', result)

    @patch('os.walk')
    def test_read_any_file_not_found(self, mock_walk):
        mock_walk.return_value = []
        result = self.handler.read_any_file('inexistente.txt')
        self.assertIn('não encontrado', result)

    @patch('core.file_handler.FileHandler._find_file')
    def test_find_file_multiple(self, mock_walk):
        # Simula múltiplos arquivos encontrados
        mock_walk.return_value = [('.', [], ['a.txt', 'b.txt'])]
        result = self.handler._find_file('a', extensions=['.txt'])
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)

    @patch('core.file_handler.FileHandler._find_file')
    def test_read_any_file_empty(self, mock_find):
        mock_find.return_value = 'arquivo.txt'
        with patch('builtins.open', unittest.mock.mock_open(read_data='')):
            result = self.handler.read_any_file('arquivo.txt')
            self.assertIn('está vazio', result)

    @patch('core.file_handler.FileHandler._find_file')
    def test_read_any_file_exception(self, mock_find):
        mock_find.return_value = 'arquivo.txt'
        with patch('builtins.open', side_effect=Exception('erro')):
            result = self.handler.read_any_file('arquivo.txt')
            self.assertIn('Erro ao ler o arquivo', result)

    @patch('core.file_handler.FileHandler._find_file')
    def test_read_pdf_file_text_insuficiente(self, mock_find):
        mock_find.return_value = 'arquivo.pdf'
        with patch('pdfplumber.open', side_effect=Exception('erro')):
            with patch('PyPDF2.PdfReader', side_effect=Exception('erro')):
                result = self.handler.read_pdf_file('arquivo.pdf')
                self.assertIn('Não foi possível extrair texto útil', result)

    @patch('os.walk')
    def test_find_file_none(self, mock_walk):
        mock_walk.return_value = []
        result = self.handler._find_file('inexistente.txt', extensions=['.txt'])
        self.assertIsNone(result)

    @patch('os.walk')
    def test_find_file_multiple_return_list(self, mock_walk):
        mock_walk.return_value = [('.', [], ['a.txt', 'a1.txt'])]
        # O nome 'a' está em ambos, retorna lista
        result = self.handler._find_file('a', extensions=['.txt'])
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 2)

    @patch('core.file_handler.FileHandler._find_file')
    def test_read_any_file_multiple(self, mock_find):
        mock_find.return_value = ['a.txt', 'b.txt']
        result = self.handler.read_any_file('a')
        self.assertIn('Foram encontrados vários arquivos compatíveis', result)

    @patch('core.file_handler.FileHandler._find_file')
    def test_read_pdf_file_multiple(self, mock_find):
        mock_find.return_value = ['a.pdf', 'b.pdf']
        result = self.handler.read_pdf_file('a')
        self.assertIn('Foram encontrados vários PDFs compatíveis', result)

    @patch('core.file_handler.FileHandler._find_file')
    def test_read_pdf_file_exception(self, mock_find):
        mock_find.return_value = 'arquivo.pdf'
        with patch('pdfplumber.open', side_effect=Exception('erro')):
            with patch('PyPDF2.PdfReader', side_effect=Exception('erro')):
                result = self.handler.read_pdf_file('arquivo.pdf')
                self.assertIn('Não foi possível extrair texto útil', result)

if __name__ == '__main__':
    unittest.main()
