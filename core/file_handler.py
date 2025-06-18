import os
import unicodedata

class FileHandler:
    def __init__(self):
        pass

    def _normalize(self, s):
        return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').lower()

    def _find_file(self, nome_arquivo, extensions=None):
        file_path = nome_arquivo.strip().strip('"')
        if os.path.isabs(file_path) and os.path.isfile(file_path):
            return file_path
        matches = []
        file_path_norm = self._normalize(os.path.basename(file_path))
        for root, dirs, files in os.walk(os.getcwd()):
            for f in files:
                if file_path_norm in self._normalize(f):
                    if not extensions or any(f.lower().endswith(ext) for ext in extensions):
                        matches.append(os.path.join(root, f))
        if not matches:
            return None
        if len(matches) > 1:
            return matches
        return matches[0]

    def read_any_file(self, nome_arquivo):
        result = self._find_file(nome_arquivo, extensions=['.txt', '.pdf'])
        if result is None:
            return f"Arquivo '{nome_arquivo}' não encontrado no workspace ou caminho absoluto não existe."
        if isinstance(result, list):
            msg = '\n'.join(result)
            return f"Foram encontrados vários arquivos compatíveis:\n{msg}\nUtilize o caminho completo."
        if result.lower().endswith('.txt'):
            try:
                with open(result, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                if not conteudo.strip():
                    return f"O arquivo '{nome_arquivo}' está vazio."
                preview = conteudo[:1500] + ("..." if len(conteudo) > 1500 else "")
                return f"Conteúdo do arquivo '{nome_arquivo}':\n{preview}"
            except Exception as e:
                return f"Erro ao ler o arquivo '{nome_arquivo}': {e}"
        elif result.lower().endswith('.pdf'):
            return self.read_pdf_file(result)
        else:
            return f"Tipo de arquivo não suportado. Envie um .txt ou .pdf."

    def read_pdf_file(self, nome_arquivo):
        result = self._find_file(nome_arquivo, extensions=['.pdf'])
        if result is None:
            return ""
        if isinstance(result, list):
            return ""
        text = ""
        try:
            import pdfplumber
            with pdfplumber.open(result) as pdf:
                text = "\n".join(page.extract_text() or '' for page in pdf.pages)
        except Exception:
            text = ""
        if not text or len(text.strip()) < 30:
            try:
                import PyPDF2
                with open(result, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception:
                text = ""
        import re
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        text = re.sub(r' +', ' ', text)
        if not text or len(text.strip()) < 30:
            return ""
        return text.strip()
