import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import discord_bot

class TestDiscordBot(unittest.TestCase):
    @patch('discord_bot.file_handler_service')
    def test_leiatxt_command(self, mock_service):
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()
        mock_service.get_txt_preview.return_value = 'preview'
        # Simula chamada do comando async
        coro = discord_bot.leiatxt(mock_ctx, nome_arquivo='arquivo.txt')
        # Executa a coroutine
        import asyncio
        asyncio.run(coro)
        mock_service.get_txt_preview.assert_called_with('arquivo.txt')
        mock_ctx.send.assert_called_with('preview')

    @patch('discord_bot.file_handler_service')
    def test_leiaarquivo_command(self, mock_service):
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()
        mock_service.read_any_file.return_value = 'conteudo'
        coro = discord_bot.leiaarquivo(mock_ctx, nome_arquivo='arquivo.txt')
        import asyncio
        asyncio.run(coro)
        mock_service.read_any_file.assert_called_with('arquivo.txt')
        mock_ctx.send.assert_called_with('conteudo')

    @patch('discord_bot.file_handler_service')
    def test_leiapdf_command(self, mock_service):
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()
        mock_service.get_pdf_preview.return_value = 'Resumo IA (pt-BR): texto'
        mock_service.get_audience_adaptation.return_value = 'adaptacao'
        coro = discord_bot.leiapdf(mock_ctx, nome_arquivo='arquivo.pdf')
        import asyncio
        asyncio.run(coro)
        mock_service.get_pdf_preview.assert_called_with('arquivo.pdf')
        mock_service.get_audience_adaptation.assert_any_call('texto', 'comercial')
        mock_ctx.send.assert_any_call("Recebido o arquivo 'arquivo.pdf'. O processamento para os públicos Comercial, Suporte e PM foi iniciado. Aguarde...")

    @patch('discord_bot.bot.run')
    def test_run_discord_bot(self, mock_run):
        discord_bot.run_discord_bot()
        mock_run.assert_called()

if __name__ == '__main__':
    unittest.main()
