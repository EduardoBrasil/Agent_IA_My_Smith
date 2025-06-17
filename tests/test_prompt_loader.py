import unittest
from unittest.mock import patch, MagicMock
from prompts import prompt_loader
import os

class TestPromptLoader(unittest.TestCase):
    def test_load_prompt_success(self):
        # Cria um arquivo temporário
        path = os.path.join(os.path.dirname(__file__), '../prompts/teste_prompt.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('conteudo')
        result = prompt_loader.load_prompt('teste_prompt')
        self.assertEqual(result, 'conteudo')
        os.remove(path)

    def test_load_prompt_not_found(self):
        with self.assertRaises(FileNotFoundError):
            prompt_loader.load_prompt('nao_existe')

if __name__ == '__main__':
    unittest.main()
