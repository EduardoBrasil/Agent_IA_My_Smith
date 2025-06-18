import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import glob
from services.file_handler_service import FileHandlerService
from asyncio import Lock

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

@bot.event
async def on_ready():
    import os
    print(f'Logged in as {bot.user} | PID: {os.getpid()}')

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

def run_discord_bot():
    bot.run(TOKEN)