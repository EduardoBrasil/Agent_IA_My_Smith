from abc import ABC, abstractmethod

class FileProcessingTemplate(ABC):
    def process(self, filename: str, audiencia: str = None):
        content = self.read_file(filename)
        if not content:
            return '[ERRO] Arquivo não encontrado ou vazio.'
        resumo = self.summarize(content)
        if not resumo:
            return '[ERRO] Falha ao resumir o conteúdo.'
        if audiencia:
            adaptacao = self.adapt(resumo, audiencia)
            return adaptacao
        return resumo

    @abstractmethod
    def read_file(self, filename: str) -> str:
        pass

    @abstractmethod
    def summarize(self, content: str) -> str:
        pass

    def adapt(self, resumo: str, audiencia: str) -> str:
        # Implementação padrão pode ser sobrescrita
        return resumo
