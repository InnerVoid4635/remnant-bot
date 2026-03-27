import discord
from discord.ext import commands
import asyncio
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

# 🔗 BANCO DE DADOS
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    command TEXT,
    date TEXT
)
""")
conn.commit()

def salvar_log(user, command):
    cursor.execute(
        "INSERT INTO logs (user, command, date) VALUES (?, ?, datetime('now'))",
        (str(user), command)
    )
    conn.commit()

# 🤖 BOT
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 🔥 importante pra moderação

bot = commands.Bot(command_prefix="*", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'🟢 Remnant online como {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content == f"<@{bot.user.id}>" or message.content == f"<@!{bot.user.id}>":  # type: ignore
        embed = discord.Embed(
            title="🟢 Remnant System",
            description="Sistema ativo...\nPrefixo atual: `*`",
            color=discord.Color.dark_green()
        )

        embed.set_footer(text="⚠️ Fragmentos detectados...")
        await message.channel.send(embed=embed)

    await bot.process_commands(message)

# 🔥 LOG AUTOMÁTICO
@bot.event
async def on_command(ctx):
    salvar_log(ctx.author, ctx.command.name)

# 🔥 AUTO LOAD DE COGS
async def load_cogs():
    print("🔄 Carregando cogs...")

    for root, dirs, files in os.walk("./cogs"):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                caminho = os.path.join(root, file)

                # transforma caminho em formato importável
                caminho = caminho.replace("./", "").replace("/", ".").replace("\\", ".")[:-3]

                try:
                    await bot.load_extension(caminho)
                    print(f"✅ Carregado: {caminho}")
                except Exception as e:
                    print(f"❌ Erro ao carregar {caminho}: {e}")

# 🚀 MAIN
async def main():
    async with bot:
        await load_cogs()  # 🔥 aqui está a mágica
        await bot.start(TOKEN) # type: ignore

asyncio.run(main())
