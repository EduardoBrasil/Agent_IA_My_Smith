import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import glob
from services.file_handler_service import FileHandlerService

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Agora pode ser ativado pois a intent foi liberada no portal

bot = commands.Bot(command_prefix="!", intents=intents)
file_handler_service = FileHandlerService()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

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
    await ctx.send(f"Recebido o arquivo '{nome_arquivo}'. O processamento para os públicos Comercial, Suporte e PM foi iniciado. Aguarde...")
    resumo = file_handler_service.get_pdf_preview(nome_arquivo)
    if 'Resumo IA (pt-BR):' in resumo:
        texto_tecnico = resumo.split('Resumo IA (pt-BR):', 1)[-1].strip()
    else:
        texto_tecnico = resumo.strip()
    for publico in ['comercial', 'suporte', 'pm']:
        adaptacao = file_handler_service.get_audience_adaptation(texto_tecnico, publico)
        titulo = publico.capitalize()
        for i in range(0, len(adaptacao), 2000):
            prefixo = f"**{titulo}:**\n" if i == 0 else ""
            await ctx.send(prefixo + adaptacao[i:i+2000])

def run_discord_bot():
    bot.run(TOKEN)