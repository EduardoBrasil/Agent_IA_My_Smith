import pandas as pd

# Lê o arquivo de chamados exportado (CSV)
def gerar_faq_de_chamados(caminho_csv, caminho_faq_txt):
    df = pd.read_csv(caminho_csv)
    with open(caminho_faq_txt, 'w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            pergunta = str(row['pergunta']).strip()
            resposta = str(row['resposta']).strip()
            if pergunta and resposta:
                f.write(f"Q: {pergunta}\nA: {resposta}\n\n")
    print(f"FAQ gerada em: {caminho_faq_txt}")

if __name__ == "__main__":
    gerar_faq_de_chamados('chamados_exemplo.csv', 'prompts/faq.txt')
