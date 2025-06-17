import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.file_handler import FileHandler
from services.summarization_service import SummarizationService
from prompts.prompt_loader import load_prompt

class FileHandlerService:
    def __init__(self):
        self.handler = FileHandler()
        self.summarizer = SummarizationService()

    def read_any_file(self, nome_arquivo):
        return self.handler.read_any_file(nome_arquivo)

    def read_pdf_file(self, nome_arquivo):
        return self.handler.read_pdf_file(nome_arquivo)

    def get_txt_preview(self, filename: str) -> str:
        print(f"[DEBUG] Chamando get_txt_preview para: {filename}")
        content = self.handler.read_any_file(filename)
        print(f"[DEBUG] Conteúdo lido: {content[:100]}")
        # Chama summarize com parâmetros para resumo aprofundado
        resumo = self.summarizer.summarize(content, min_length=100, max_length=300)
        print(f"[DEBUG] Resumo IA: {resumo}")
        return f"Conteúdo do arquivo resumido:\n{resumo}"

    def get_pdf_preview(self, filename: str) -> str:
        content = self.handler.read_pdf_file(filename)
        if "Conteúdo do PDF" in content:
            texto = content.split(':', 1)[-1].strip()[:2000]  # Limita a 2000 caracteres
            if not texto or len(texto) < 50:
                return f"[AVISO] Não foi possível extrair texto útil do PDF. O arquivo pode estar protegido, ser uma imagem ou ter formatação incompatível.\nPreview extraído:\n{texto}"
            texto_len = len(texto)
            min_length = min(600, max(50, texto_len // 3))
            max_length = min(1200, max(100, int(texto_len * 0.6)))
            if min_length >= max_length:
                min_length = max_length - 50 if max_length > 50 else max_length
            # Carrega prompt customizável
            prompt_template = load_prompt('release_tecnologia')
            prompt = prompt_template.replace('{texto}', texto)
            try:
                resumo = self.summarizer.summarize(prompt, min_length=min_length, max_length=max_length)
            except Exception as e:
                return f"[ERRO] A IA demorou demais para responder ou houve falha: {e}"
            return f"Resumo IA (pt-BR):\n{resumo}"
        return content

    def get_any_file_preview(self, filename: str) -> str:
        content = self.handler.read_any_file(filename)
        if "Conteúdo do arquivo" in content or "Conteúdo do PDF" in content:
            resumo = self.summarizer.summarize(content)
            return f"{content}\n\nResumo IA:\n{resumo}"
        return content

    def get_audience_adaptations(self, texto_tecnico: str) -> dict:
        """
        Recebe um texto técnico e retorna adaptações para Comercial, Suporte e PM usando prompts separados.
        Sumariza com modelo em inglês e traduz o resultado para português.
        """
        texto_ptbr = self.summarizer.translate_to_ptbr(texto_tecnico)
        audiencias = ['comercial', 'suporte', 'pm']
        resultados = {}
        modelo_sum = 'facebook/bart-large-cnn'
        for audiencia in audiencias:
            prompt_template = load_prompt(audiencia)
            prompt = prompt_template.replace('{texto}', texto_ptbr)
            try:
                adaptacao_en = self.summarizer.summarize(prompt, min_length=200, max_length=600, model=modelo_sum)
                adaptacao = self.summarizer.translate_to_ptbr(adaptacao_en)
            except Exception as e:
                adaptacao = f"[ERRO] Falha ao adaptar para {audiencia}: {e}"
            resultados[audiencia] = adaptacao
        return resultados

    def get_audience_adaptation(self, texto_tecnico: str, audiencia: str) -> str:
        """
        Recebe um texto técnico e retorna a adaptação para uma audiência específica (comercial, suporte ou pm).
        Sumariza com modelo em inglês, usando prompt que força resposta em português.
        """
        modelo_sum = 'facebook/bart-large-cnn'
        prompt_template = load_prompt(audiencia)
        prompt = prompt_template.replace('{texto}', texto_tecnico)
        try:
            adaptacao = self.summarizer.summarize(prompt, min_length=200, max_length=600, model=modelo_sum)
        except Exception as e:
            adaptacao = f"[ERRO] Falha ao adaptar para {audiencia}: {e}"
        return adaptacao
