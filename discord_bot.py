import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import glob
from services.file_handler_service import FileHandlerService
from asyncio import Lock
from core.file_utils import get_latest_file
from core.file_handler import FileHandler
import threading
import time
import asyncio
from fuzzywuzzy import fuzz
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
CANAL_PRODUTO_ID = int(os.getenv('CANAL_PRODUTO_ID', '0'))
CANAL_COMERCIAL_ID = int(os.getenv('CANAL_COMERCIAL_ID', '0'))
CANAL_SUPORTE_ID = int(os.getenv('CANAL_SUPORTE_ID', '0'))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Agora pode ser ativado pois a intent foi liberada no portal

bot = commands.Bot(command_prefix="!", intents=intents)
file_handler_service = FileHandlerService()

# Lock global para evitar execução duplicada
leiapdf_lock = Lock()
# Set para armazenar IDs de mensagens já processadas
mensagens_processadas = set()

async def processar_release_automaticamente(arquivo):
    print(f"[DEBUG] Iniciando processamento automático do arquivo: {arquivo}")
    canais = {
        'comercial': bot.get_channel(CANAL_COMERCIAL_ID),
        'suporte': bot.get_channel(CANAL_SUPORTE_ID),
        'produto': bot.get_channel(CANAL_PRODUTO_ID)
    }
    canais_ids = {k: (v.id if v else None) for k, v in canais.items()}
    print(f"[DEBUG] Canais encontrados: {canais_ids}")
    if not arquivo:
        print("[DEBUG] Nenhum arquivo recebido para processamento.")
        return
    resumo = file_handler_service.get_pdf_preview(arquivo)
    print(f"[DEBUG] Resumo gerado: {repr(resumo)[:200]}")
    if not resumo or resumo.startswith("[AVISO]") or resumo.startswith("[ERRO]"):
        print("[DEBUG] Resumo inválido ou erro ao processar arquivo.")
        return
    if 'Resumo IA (pt-BR):' in resumo:
        texto_tecnico = resumo.split('Resumo IA (pt-BR):', 1)[-1].strip()
    else:
        texto_tecnico = resumo.strip()
    enviados = set()
    for publico in ['comercial', 'suporte', 'produto']:
        print(f"[DEBUG] Adaptando para público: {publico}")
        adaptacao = await file_handler_service.get_audience_adaptation(texto_tecnico, publico)
        print(f"[DEBUG] Adaptação para {publico}: {repr(adaptacao)[:200]}")
        titulo = publico.capitalize()
        canal = canais[publico]
        if canal and adaptacao.strip() and not adaptacao.strip().startswith('Você é') and not adaptacao.strip().startswith('Texto técnico:') and canal.id not in enviados:
            enviados.add(canal.id)
            for i in range(0, len(adaptacao), 2000):
                prefixo = f"**{titulo}:**\n" if i == 0 else ""
                print(f"[DEBUG] Enviando mensagem para canal {canal.id} ({titulo})")
                await canal.send(prefixo + adaptacao[i:i+2000])
        else:
            print(f"[DEBUG] Canal não encontrado ou adaptação vazia para {publico}. Canal: {canal}")

def notificar_novos_releases():
    pasta = "outputs"
    arquivos_anteriores = set(os.listdir(pasta))
    while True:
        time.sleep(10)  # Checa a cada 10 segundos
        arquivos_atuais = set(os.listdir(pasta))
        novos = arquivos_atuais - arquivos_anteriores
        if novos:
            canal = bot.get_channel(CHANNEL_ID)
            for arquivo in novos:
                caminho_arquivo = os.path.join(pasta, arquivo)
                if canal:
                    asyncio.run_coroutine_threadsafe(
                        canal.send(f"Novo release detectado: `{arquivo}`. Processando automaticamente..."), bot.loop
                    )
                # Integra ao fluxo do leiapdf de forma assíncrona
                asyncio.run_coroutine_threadsafe(processar_release_automaticamente(caminho_arquivo), bot.loop)
        arquivos_anteriores = arquivos_atuais

def run_discord_bot():
    bot.run(TOKEN)

@bot.event
async def on_ready():
    import os
    print(f'Logged in as {bot.user} | PID: {os.getpid()}')
    threading.Thread(target=notificar_novos_releases, daemon=True).start()

@bot.command(name="leiatxt")
async def leiatxt(ctx, *, nome_arquivo: str):
    response = file_handler_service.get_txt_preview(nome_arquivo)
    await ctx.send(response)

@bot.command(name="leiaarquivo")
async def leiaarquivo(ctx, *, nome_arquivo: str):
    response = file_handler_service.read_any_file(nome_arquivo)
    await ctx.send(response)

@bot.command(name="leiapdf")
async def leiapdf(ctx, *, nome_arquivo: str):
    print(f"[DIAG] Executando leiapdf | msg_id={ctx.message.id} | canal_id={ctx.channel.id} | autor={ctx.author}")
    # Proteção: só processa se a mensagem ainda não foi processada
    if ctx.message.id in mensagens_processadas:
        print(f"[DIAG] Ignorado (já processado): msg_id={ctx.message.id}")
        return
    mensagens_processadas.add(ctx.message.id)
    async with leiapdf_lock:
        await ctx.send(f"Recebido o arquivo '{nome_arquivo}'. O processamento para os públicos Comercial, Suporte e Produto foi iniciado. Aguarde...")
        resumo = file_handler_service.get_pdf_preview(nome_arquivo)
        # Só continue se for um resumo válido
        if not resumo or resumo.startswith("[AVISO]") or resumo.startswith("[ERRO]"):
            await ctx.send(resumo)
            return
        if 'Resumo IA (pt-BR):' in resumo:
            texto_tecnico = resumo.split('Resumo IA (pt-BR):', 1)[-1].strip()
        else:
            texto_tecnico = resumo.strip()
        canais = {
            'comercial': bot.get_channel(CANAL_COMERCIAL_ID),
            'suporte': bot.get_channel(CANAL_SUPORTE_ID),
            'produto': bot.get_channel(CANAL_PRODUTO_ID)
        }
        enviados = set()
        for publico in ['comercial', 'suporte', 'produto']:
            adaptacao = await file_handler_service.get_audience_adaptation(texto_tecnico, publico)
            titulo = publico.capitalize()
            canal = canais[publico]
            # Só envia se o canal de destino for diferente do canal de origem, não for None, não for vazio e não for igual ao prompt
            if canal and canal.id != ctx.channel.id and canal.id not in enviados and adaptacao.strip() and not adaptacao.strip().startswith('Você é') and not adaptacao.strip().startswith('Texto técnico:'):
                enviados.add(canal.id)
                for i in range(0, len(adaptacao), 2000):
                    prefixo = f"**{titulo}:**\n" if i == 0 else ""
                    await canal.send(prefixo + adaptacao[i:i+2000])
            elif canal is None:
                await ctx.send(f"[ERRO] Canal para '{publico}' não encontrado ou não configurado.")

@bot.command(name="ultimaversao")
async def ultimaversao(ctx):
    pasta = "outputs"
    arquivo = get_latest_file(pasta)
    if not arquivo:
        await ctx.send("Nenhum arquivo de release encontrado na pasta outputs.")
        return
    handler = FileHandler()
    if arquivo.lower().endswith(".pdf"):
        conteudo = handler.read_pdf_file(arquivo)
    else:
        conteudo = handler.read_any_file(arquivo)
    if not conteudo or len(conteudo.strip()) < 10:
        await ctx.send("Não foi possível ler o conteúdo da última versão.")
        return
    # Opcional: sumarizar com IA
    resumo = file_handler_service.summarizer.summarize(conteudo, min_length=100, max_length=2048)
    resposta = f"Última versão encontrada: `{os.path.basename(arquivo)}`\nResumo:\n{resumo if resumo else conteudo[:2000]}"
    await ctx.send(resposta)

@bot.command(name="duvida")
async def duvida(ctx, *, pergunta: str):
    pasta = "outputs"
    arquivo = get_latest_file(pasta)
    if not arquivo:
        await ctx.send("Nenhum arquivo de release encontrado na pasta outputs.")
        return
    handler = FileHandler()
    if arquivo.lower().endswith(".pdf"):
        conteudo = handler.read_pdf_file(arquivo)
    else:
        conteudo = handler.read_any_file(arquivo)
    if not conteudo or len(conteudo.strip()) < 10:
        await ctx.send("Não foi possível ler o conteúdo da última versão.")
        return
    resposta = file_handler_service.summarizer.question_answer(pergunta, conteudo[:2000])
    print(f"[DEBUG] Resposta QA: {repr(resposta)}")
    # Fallbacks para resposta vazia, erro ou resposta irrelevante
    if not resposta or resposta.strip() == "" or resposta.lower() in ["n/a", "none", "", "status 404"] or len(resposta.strip()) < 5:
        print("[DEBUG] Executando fallback para sumarização...")
        prompt = (
            f"Você é um assistente especialista em releases de software.\n"
            f"Leia o texto abaixo e responda à pergunta em português do Brasil, de forma clara e objetiva.\n"
            f"Release:\n{conteudo[:1000]}\n\n"
            f"Pergunta: {pergunta}"
        )
        resposta = file_handler_service.summarizer.summarize(prompt, min_length=100, max_length=1024)
        print(f"[DEBUG] Resposta sumarização: {repr(resposta)}")
        if not resposta or resposta.strip() == "" or resposta.lower() in ["n/a", "none", "", "status 404"] or len(resposta.strip()) < 5:
            resposta = "Não foi possível obter uma resposta relevante da IA para sua dúvida."
            print("[DEBUG] Fallback final: resposta padrão enviada.")
    await ctx.send(resposta)

@bot.command(name="versao")
async def versao(ctx, *, termo: str):
    pasta = "outputs"
    arquivos = [f for f in os.listdir(pasta) if termo.lower() in f.lower()]
    if not arquivos:
        await ctx.send(f"Nenhum arquivo de release encontrado contendo '{termo}'.")
        return
    arquivo = os.path.join(pasta, sorted(arquivos)[-1])  # Pega o mais recente se houver mais de um
    handler = FileHandler()
    if arquivo.lower().endswith(".pdf"):
        conteudo = handler.read_pdf_file(arquivo)
    else:
        conteudo = handler.read_any_file(arquivo)
    if not conteudo or len(conteudo.strip()) < 10:
        await ctx.send("Não foi possível ler o conteúdo da versão encontrada.")
        return
    resumo = file_handler_service.summarizer.summarize(conteudo, min_length=100, max_length=1024)
    resposta = f"Versão encontrada: `{os.path.basename(arquivo)}`\nResumo:\n{resumo if resumo else conteudo[:2000]}"
    await ctx.send(resposta)

@bot.command(name="gerarpdf")
async def gerarpdf(ctx, publico: str):
    """
    Gera e envia um PDF customizado com o resumo adaptado para o público informado (comercial, suporte ou produto).
    Uso: !gerarpdf <público>
    """
    publico = publico.lower().strip()
    if publico not in ["comercial", "suporte", "produto"]:
        await ctx.send("Público inválido. Use: comercial, suporte ou produto.")
        return
    pasta = "outputs"
    pdf_pasta = "pdfs_customizados"
    os.makedirs(pdf_pasta, exist_ok=True)
    arquivo = get_latest_file(pasta)
    if not arquivo:
        await ctx.send("Nenhum arquivo de release encontrado na pasta outputs.")
        return
    resumo = file_handler_service.get_pdf_preview(arquivo)
    if not resumo or resumo.startswith("[AVISO]") or resumo.startswith("[ERRO]"):
        await ctx.send(resumo)
        return
    if 'Resumo IA (pt-BR):' in resumo:
        texto_tecnico = resumo.split('Resumo IA (pt-BR):', 1)[-1].strip()
    else:
        texto_tecnico = resumo.strip()
    adaptacao = await file_handler_service.get_audience_adaptation(texto_tecnico, publico)
    if not adaptacao or len(adaptacao.strip()) < 10:
        await ctx.send("Não foi possível gerar a adaptação para o público informado.")
        return
    # Gerar PDF temporário em pasta separada
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    titulo = f"Resumo Adaptado - {publico.capitalize()}"
    pdf.cell(0, 10, titulo, ln=True, align='C')
    for linha in adaptacao.split('\n'):
        pdf.multi_cell(0, 10, linha)
    nome_pdf = f"release_{publico}_{os.path.basename(arquivo).replace('.pdf','').replace('.txt','')}.pdf"
    caminho_pdf = os.path.join(pdf_pasta, nome_pdf)
    pdf.output(caminho_pdf)
    # Enviar PDF no canal
    with open(caminho_pdf, "rb") as f:
        await ctx.send(file=discord.File(f, filename=nome_pdf))
    await ctx.send(f"PDF customizado para '{publico}' gerado com sucesso na pasta '{pdf_pasta}'!")

STOPWORDS = set([
    'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas',
    'por', 'para', 'com', 'e', 'ou', 'que', 'se', 'é', 'da', 'ao', 'à', 'às', 'aos', 'na', 'no', 'nas', 'nos', 'como', 'um', 'uma', 'ser', 'foi', 'são', 'está', 'estão', 'estava', 'estavam', 'fui', 'vai', 'vou', 'vão', 'vai', 'já', 'mas', 'também', 'pode', 'poder', 'pode', 'poder', 'quando', 'onde', 'qual', 'quais', 'quem', 'que', 'por', 'para', 'com', 'sem', 'sobre', 'após', 'antes', 'depois', 'entre', 'até', 'desde', 'durante', 'contra', 'per', 'sob', 'trás', 'diante', 'mediante', 'exceto', 'salvo', 'menos', 'além', 'acima', 'abaixo', 'perante', 'segundo', 'conforme', 'consoante', 'mal', 'bem', 'muito', 'pouco', 'mais', 'menos', 'todo', 'toda', 'todos', 'todas', 'algum', 'alguma', 'alguns', 'algumas', 'nenhum', 'nenhuma', 'nenhuns', 'nenhumas', 'outro', 'outra', 'outros', 'outras', 'mesmo', 'mesma', 'mesmos', 'mesmas', 'tal', 'tais', 'qualquer', 'quaisquer', 'cada', 'certo', 'certa', 'certos', 'certas', 'vários', 'várias', 'tanto', 'tanta', 'tantos', 'tantas', 'quanto', 'quanta', 'quantos', 'quantas', 'um', 'uma', 'uns', 'umas', 'primeiro', 'primeira', 'primeiros', 'primeiras', 'segundo', 'segunda', 'segundos', 'segundas', 'terceiro', 'terceira', 'terceiros', 'terceiras', 'último', 'última', 'últimos', 'últimas', 'próximo', 'próxima', 'próximos', 'próximas', 'anterior', 'anterior', 'anteriores', 'novo', 'nova', 'novos', 'novas', 'velho', 'velha', 'velhos', 'velhas', 'grande', 'grandes', 'pequeno', 'pequena', 'pequenos', 'pequenas', 'bom', 'boa', 'bons', 'boas', 'ruim', 'ruins', 'melhor', 'melhores', 'pior', 'piores', 'maior', 'maiores', 'menor', 'menores', 'primeiro', 'primeira', 'primeiros', 'primeiras', 'último', 'última', 'últimos', 'últimas', 'próximo', 'próxima', 'próximos', 'próximas', 'anterior', 'anteriores', 'novo', 'nova', 'novos', 'novas', 'velho', 'velha', 'velhos', 'velhas', 'grande', 'grandes', 'pequeno', 'pequena', 'pequenos', 'pequenas', 'bom', 'boa', 'bons', 'boas', 'ruim', 'ruins', 'melhor', 'melhores', 'pior', 'piores', 'maior', 'maiores', 'menor', 'menores', 'primeiro', 'primeira', 'primeiros', 'primeiras', 'último', 'última', 'últimos', 'últimas', 'próximo', 'próxima', 'próximos', 'próximas', 'anterior', 'anteriores', 'novo', 'nova', 'novos', 'novas', 'velho', 'velha', 'velhos', 'velhas', 'grande', 'grandes', 'pequeno', 'pequena', 'pequenos', 'pequenas', 'bom', 'boa', 'bons', 'boas', 'ruim', 'ruins', 'melhor', 'melhores', 'pior', 'piores', 'maior', 'maiores', 'menor', 'menores'
])

def limpar_texto(texto):
    # Remove pontuação e stopwords
    texto = re.sub(r'[^\w\s]', '', texto.lower())
    return ' '.join([w for w in texto.split() if w not in STOPWORDS])

@bot.command(name="faq")
async def faq(ctx, *, pergunta: str = None):
    """
    Responde perguntas frequentes a partir da base gerada dos chamados.
    - !faq           => lista as perguntas mais frequentes
    - !faq <pergunta> => busca a resposta mais próxima na base (fuzzy + match exato + stopwords + fallback)
    """
    faq_path = os.path.join("prompts", "faq.txt")
    if not os.path.exists(faq_path):
        await ctx.send("Base de FAQ não encontrada. Gere a FAQ a partir dos chamados primeiro.")
        return
    with open(faq_path, encoding="utf-8") as f:
        blocos = f.read().strip().split('\n\n')
    faqs = []
    for bloco in blocos:
        if bloco.strip():
            linhas = bloco.strip().split('\n')
            q = next((l[3:].strip() for l in linhas if l.startswith('Q: ')), None)
            a = next((l[3:].strip() for l in linhas if l.startswith('A: ')), None)
            if q and a:
                faqs.append((q, a))
    if not pergunta:
        perguntas = [f"- {q}" for q, _ in faqs]
        msg = "Perguntas frequentes:\n" + "\n".join(perguntas[:15])
        await ctx.send(msg)
        return
    # Busca exata (case-insensitive)
    for q, a in faqs:
        if pergunta.strip().lower() == q.strip().lower():
            await ctx.send(f"Q: {q}\nA: {a}")
            return
    # Busca fuzzy com limpeza de stopwords (threshold alto)
    pergunta_proc = limpar_texto(pergunta)
    melhor_q, melhor_a, melhor_score = None, None, 0
    for q, a in faqs:
        q_proc = limpar_texto(q)
        score = fuzz.token_set_ratio(pergunta_proc, q_proc)
        if score > melhor_score:
            melhor_q, melhor_a, melhor_score = q, a, score
    if melhor_a and melhor_score >= 80:
        await ctx.send(f"Q: {melhor_q}\nA: {melhor_a}")
        return
    # Fallback: fuzzy com threshold menor
    melhor_q2, melhor_a2, melhor_score2 = None, None, 0
    for q, a in faqs:
        q_proc = limpar_texto(q)
        score = fuzz.token_set_ratio(pergunta_proc, q_proc)
        if score > melhor_score2:
            melhor_q2, melhor_a2, melhor_score2 = q, a, score
    if melhor_a2 and melhor_score2 >= 65:
        await ctx.send(f"Q: {melhor_q2}\nA: {melhor_a2}")
    else:
        await ctx.send("Não encontrei uma resposta relevante na FAQ. Tente reformular sua dúvida ou consulte o suporte humano.")