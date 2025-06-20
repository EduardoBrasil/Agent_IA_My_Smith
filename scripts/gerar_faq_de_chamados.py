import pandas as pd
import os
import sys

def normalizar_colunas(df):
    import unicodedata
    # Remove espaços, acentos e deixa minúsculo
    def norm(s):
        return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').strip().lower().replace('  ', ' ')
    df.columns = [norm(col) for col in df.columns]
    return df

# Lê o arquivo de chamados exportado (CSV, XLS ou XLSX)
def gerar_faq_de_chamados(caminho_entrada, caminho_faq):
    # Detecta extensão e lê CSV ou XLSX
    ext = os.path.splitext(caminho_entrada)[-1].lower()
    if ext == '.csv':
        df = pd.read_csv(caminho_entrada, dtype=str).fillna("")
    elif ext in ['.xls', '.xlsx']:
        df = pd.read_excel(caminho_entrada, dtype=str).fillna("")
    else:
        raise ValueError("Arquivo de chamados deve ser .csv, .xls ou .xlsx")
    df = normalizar_colunas(df)
    # Nomes normalizados
    col_produto = 'produto'
    col_categoria = 'categoria'
    col_pergunta = 'pergunta'
    col_tipo = 'tipo de solicitacao'
    col_proc = 'procedimento'
    col_sol = 'solucao'
    with open(caminho_faq, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            produto = row.get(col_produto, '').strip()
            categoria = row.get(col_categoria, '').strip()
            pergunta = row.get(col_pergunta, '').strip()
            tipo = row.get(col_tipo, '').strip()
            procedimento = row.get(col_proc, '').strip()
            solucao = row.get(col_sol, '').strip()
            f.write(f"Produto: {produto}\n")
            f.write(f"Categoria: {categoria}\n")
            f.write(f"Pergunta: {pergunta}\n")
            f.write(f"Tipo de solicitação: {tipo}\n")
            f.write(f"Procedimento: {procedimento}\n")
            f.write(f"Solução: {solucao}\n")
            f.write("-" * 40 + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Uso: {sys.argv[0]} <caminho_entrada> <caminho_faq>")
        sys.exit(1)

    caminho_entrada = sys.argv[1]
    caminho_faq = sys.argv[2]
    # Gera sempre o arquivo com nome faqSUPORTE.txt
    if not caminho_faq.lower().endswith('faqsuporte.txt'):
        caminho_faq = os.path.join(os.path.dirname(caminho_faq), 'faqSUPORTE.txt')
    gerar_faq_de_chamados(caminho_entrada, caminho_faq)
    print(f"FAQ gerada em {caminho_faq}")
