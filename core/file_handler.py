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
            return f"PDF '{nome_arquivo}' não encontrado no workspace ou caminho absoluto não existe."
        if isinstance(result, list):
            msg = '\n'.join(result)
            return f"Foram encontrados vários PDFs compatíveis:\n{msg}\nUtilize o caminho completo."
        text = ""
        # Tenta extrair com pdfplumber primeiro
        try:
            import pdfplumber
            with pdfplumber.open(result) as pdf:
                text = "\n".join(page.extract_text() or '' for page in pdf.pages)
        except Exception as e:
            print(f"[ERRO] Falha ao extrair com pdfplumber: {e}")
            text = ""
        # Se pdfplumber falhar, tenta PyPDF2
        if not text or len(text.strip()) < 30:
            try:
                import PyPDF2
                with open(result, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for i, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                        except Exception as e:
                            page_text = f"[Erro ao extrair texto da página {i+1}: {e}]"
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"[ERRO] Falha ao extrair com PyPDF2: {e}")
                text = ""
        # Limpa quebras de linha artificiais
        import re
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        text = re.sub(r' +', ' ', text)
        if not text or len(text.strip()) < 30:
            return f"[AVISO] Não foi possível extrair texto útil do PDF '{nome_arquivo}'. O arquivo pode estar protegido, ser uma imagem ou ter formatação incompatível."
        preview = text[:1500] + ("..." if len(text) > 1500 else "")
        return f"Conteúdo do PDF '{nome_arquivo}':\n{preview}"
