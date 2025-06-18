import sys
import os
import logging
from typing import Dict
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.file_handler import FileHandler
from services.summarization_service import SummarizationService
from prompts.prompt_loader import load_prompt
from strategies.adaptation_factory import AdaptationFactory

AUDIENCIAS = ['comercial', 'suporte', 'pm']
MODELO_SUM = 'facebook/bart-large-cnn'

logger = logging.getLogger(__name__)

class FileHandlerService:
    def __init__(self):
        self.handler = FileHandler()
        self.summarizer = SummarizationService()

    def read_any_file(self, nome_arquivo: str) -> str:
        """Lê qualquer arquivo suportado (txt, pdf) e retorna seu conteúdo ou mensagem de erro."""
        return self.handler.read_any_file(nome_arquivo)

    def read_pdf_file(self, nome_arquivo: str) -> str:
        """Lê um arquivo PDF e retorna seu conteúdo ou mensagem de erro."""
        return self.handler.read_pdf_file(nome_arquivo)

    def get_txt_preview(self, filename: str) -> str:
        """Gera um resumo IA para um arquivo texto."""
        logger.debug(f"Chamando get_txt_preview para: {filename}")
        content = self.handler.read_any_file(filename)
        logger.debug(f"Conteúdo lido: {content[:100]}")
        try:
            resumo = self.summarizer.summarize(content, min_length=100, max_length=300)
        except Exception as e:
            logger.error(f"Erro ao resumir texto: {e}")
            resumo = f"[ERRO] Falha ao resumir: {e}"
        logger.debug(f"Resumo IA: {resumo}")
        return f"Conteúdo do arquivo resumido:\n{resumo}"

    def get_pdf_preview(self, filename: str) -> str:
        """Gera um resumo IA para um arquivo PDF."""
        content = self.handler.read_pdf_file(filename)
        if "Conteúdo do PDF" in content:
            texto = content.split(':', 1)[-1].strip()[:2000]
            if not texto or len(texto) < 50:
                return f"[AVISO] Não foi possível extrair texto útil do PDF. O arquivo pode estar protegido, ser uma imagem ou ter formatação incompatível.\nPreview extraído:\n{texto}"
            texto_len = len(texto)
            min_length = min(600, max(50, texto_len // 3))
            max_length = min(1200, max(100, int(texto_len * 0.6)))
            if min_length >= max_length:
                min_length = max_length - 50 if max_length > 50 else max_length
            prompt_template = load_prompt('release_tecnologia')
            prompt = prompt_template.replace('{texto}', texto)
            try:
                resumo = self.summarizer.summarize(prompt, min_length=min_length, max_length=max_length)
            except Exception as e:
                logger.error(f"Erro ao resumir PDF: {e}")
                return f"[ERRO] A IA demorou demais para responder ou houve falha: {e}"
            return f"Resumo IA (pt-BR):\n{resumo}"
        return content

    def get_any_file_preview(self, filename: str) -> str:
        """Gera um resumo IA para qualquer arquivo suportado."""
        content = self.handler.read_any_file(filename)
        if "Conteúdo do arquivo" in content or "Conteúdo do PDF" in content:
            try:
                resumo = self.summarizer.summarize(content)
            except Exception as e:
                logger.error(f"Erro ao resumir arquivo: {e}")
                resumo = f"[ERRO] Falha ao resumir: {e}"
            return f"{content}\n\nResumo IA:\n{resumo}"
        return content

    async def _adaptar_para_audiencia(self, texto: str, audiencia: str) -> str:
        strategy = AdaptationFactory.get_strategy(audiencia)
        return await strategy.adapt(texto)

    async def get_audience_adaptation(self, texto_tecnico: str, audiencia: str) -> str:
        """
        Recebe um texto técnico e retorna a adaptação para uma audiência específica (comercial, suporte ou pm).
        Sumariza com modelo em inglês, usando prompt que força resposta em português.
        """
        return await self._adaptar_para_audiencia(texto_tecnico, audiencia)
