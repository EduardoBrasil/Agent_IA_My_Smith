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

# Função utilitária para carregar a base de FAQ
async def carregar_faq():
    faq_path = os.path.join("prompts", "faqSUPORTE.txt")
    with open(faq_path, encoding="utf-8") as f:
        conteudo = f.read()
    blocos = [b.strip() for b in conteudo.split('----------------------------------------') if b.strip()]
    faqs = []
    produto_atual = None
    categoria_atual = None
    for bloco in blocos:
        linhas = [l.strip() for l in bloco.split('\n') if l.strip()]
        dados = {"produto": None, "categoria": None, "pergunta": None, "tipo": None, "procedimento": None, "solucao": None}
        for l in linhas:
            l_lower = l.lower().replace('ç', 'c').replace('ã', 'a').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            if l_lower.replace(' ', '').startswith('produto:'):
                produto_atual = l.split(':',1)[1].strip() or None
                dados["produto"] = produto_atual
            elif l_lower.replace(' ', '').startswith('categoria:'):
                categoria_atual = l.split(':',1)[1].strip() or None
                dados["categoria"] = categoria_atual
            elif l_lower.replace(' ', '').startswith('pergunta:'):
                dados["pergunta"] = l.split(':',1)[1].strip()
            elif l_lower.replace(' ', '').startswith('tipodesolicitacao:'):
                dados["tipo"] = l.split(':',1)[1].strip()
            elif l_lower.replace(' ', '').startswith('procedimento:'):
                dados["procedimento"] = l.split(':',1)[1].strip()
            elif l_lower.replace(' ', '').startswith('solucao:'):
                dados["solucao"] = l.split(':',1)[1].strip()
        if not dados["produto"]:
            dados["produto"] = produto_atual
        if not dados["categoria"]:
            dados["categoria"] = categoria_atual
        if dados["pergunta"] and dados["solucao"]:
            faqs.append(dados)
    return faqs

@bot.command(name="faq")
async def faq(ctx, *, pergunta: str = None):
    """
    Responde perguntas frequentes a partir da base gerada dos chamados.
    - !faq           => inicia menu navegável por produto/categoria/pergunta
    - !faq <pergunta> => busca a resposta mais próxima na base (fuzzy + match exato + stopwords + fallback)
    """
    # Restrição: só permite uso no canal de suporte
    SUPORTE_CHANNEL_ID = int(os.getenv('CANAL_SUPORTE_ID', '0'))
    if ctx.channel.id != SUPORTE_CHANNEL_ID:
        await ctx.send("Este comando só pode ser usado no canal de suporte.")
        return
    if pergunta:
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
        return
    faqs = await carregar_faq()
    produtos = sorted(set(faq["produto"] for faq in faqs if faq["produto"]))
    if not produtos:
        await ctx.send("Nenhum produto encontrado na base de FAQ.")
        return
    async def send_produto_menu(interaction=None):
        class ProdutoSelect(discord.ui.Select):
            def __init__(self, produtos):
                options = [discord.SelectOption(label=p, value=p) for p in produtos]
                super().__init__(placeholder="Selecione o produto...", min_values=1, max_values=1, options=options)
            async def callback(self, interaction):
                await send_categoria_menu(interaction, self.values[0])
        class ProdutoView(discord.ui.View):
            def __init__(self, produtos):
                super().__init__(timeout=60)
                self.add_item(ProdutoSelect(produtos))
        if interaction:
            await interaction.response.edit_message(content="Selecione o produto desejado:", view=ProdutoView(produtos))
        else:
            await ctx.send("Selecione o produto desejado:", view=ProdutoView(produtos))
    async def send_categoria_menu(interaction, produto_escolhido):
        categorias = sorted(set(faq["categoria"] for faq in faqs if faq["produto"] == produto_escolhido and faq["categoria"]))
        class CategoriaSelect(discord.ui.Select):
            def __init__(self, categorias):
                options = [discord.SelectOption(label=c, value=c) for c in categorias]
                super().__init__(placeholder="Selecione a categoria...", min_values=1, max_values=1, options=options)
            async def callback(self, interaction2):
                await send_pergunta_menu(interaction2, produto_escolhido, self.values[0])
        class CategoriaView(discord.ui.View):
            def __init__(self, categorias):
                super().__init__(timeout=60)
                self.add_item(CategoriaSelect(categorias))
                self.add_item(self.VoltarButton())
            class VoltarButton(discord.ui.Button):
                def __init__(self):
                    super().__init__(label="Voltar", style=discord.ButtonStyle.secondary)
                async def callback(self, interaction3):
                    await send_produto_menu(interaction3)
        await interaction.response.edit_message(content=f"Selecione a categoria para o produto '{produto_escolhido}':", view=CategoriaView(categorias))
    async def send_pergunta_menu(interaction, produto_escolhido, categoria_escolhida):
        perguntas = [faq for faq in faqs if faq["produto"] == produto_escolhido and faq["categoria"] == categoria_escolhida]
        page_size = 10
        total_pages = (len(perguntas) - 1) // page_size + 1
        async def show_page(page, interaction_to_update=None):
            class PerguntaSelect(discord.ui.Select):
                def __init__(self, perguntas, page, total_pages):
                    start = page * page_size
                    end = start + page_size
                    self.perguntas = perguntas
                    self.page = page
                    self.total_pages = total_pages
                    options = [discord.SelectOption(label=p["pergunta"][:90], value=str(i+start)) for i, p in enumerate(perguntas[start:end])]
                    super().__init__(placeholder=f"Perguntas (página {page+1}/{total_pages})", min_values=1, max_values=1, options=options)
                async def callback(self, interaction3):
                    idx = int(self.values[0])
                    faq_item = perguntas[idx]
                    resposta = (
                        f"**Produto:** {faq_item['produto'] or 'Não informado'}\n"
                        f"**Categoria:** {faq_item['categoria'] or 'Não informado'}\n"
                        f"**Pergunta:** {faq_item['pergunta'] or 'Não informado'}\n"
                        f"**Tipo de solicitação:** {faq_item['tipo'] or 'Não informado'}\n"
                        f"**Procedimento:** {faq_item['procedimento'] or 'Não informado'}\n"
                        f"**Solução:** {faq_item['solucao'] or 'Não informado'}"
                    )
                    await interaction3.response.send_message(resposta, ephemeral=True)
            class PerguntaView(discord.ui.View):
                def __init__(self, perguntas, page, total_pages):
                    super().__init__(timeout=120)
                    self.page = page
                    self.perguntas = perguntas
                    self.total_pages = total_pages
                    self.add_item(PerguntaSelect(perguntas, page, total_pages))
                    if page > 0:
                        self.add_item(self.PrevButton(self))
                    if (page + 1) < total_pages:
                        self.add_item(self.NextButton(self))
                    self.add_item(self.VoltarButton())
                class PrevButton(discord.ui.Button):
                    def __init__(self, view):
                        super().__init__(label="Anterior", style=discord.ButtonStyle.secondary)
                        self.view_ref = view
                    async def callback(self, interaction):
                        await show_page(self.view_ref.page - 1, interaction)
                class NextButton(discord.ui.Button):
                    def __init__(self, view):
                        super().__init__(label="Próxima", style=discord.ButtonStyle.secondary)
                        self.view_ref = view
                    async def callback(self, interaction):
                        await show_page(self.view_ref.page + 1, interaction)
                class VoltarButton(discord.ui.Button):
                    def __init__(self):
                        super().__init__(label="Voltar", style=discord.ButtonStyle.secondary)
                    async def callback(self, interaction):
                        await send_categoria_menu(interaction, produto_escolhido)
            if interaction_to_update:
                await interaction_to_update.response.edit_message(content=f"Selecione a pergunta da categoria '{categoria_escolhida}':", view=PerguntaView(perguntas, page, total_pages))
            else:
                await interaction.response.edit_message(content=f"Selecione a pergunta da categoria '{categoria_escolhida}':", view=PerguntaView(perguntas, page, total_pages))
        await show_page(0)
    await send_produto_menu()