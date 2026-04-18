import discord
from discord.ext import commands
import asyncio
import aiosqlite
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

class RemnantBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        super().__init__(command_prefix="*", intents=intents, help_command=None)
        self.db: aiosqlite.Connection = None # type: ignore
        self.start_time = time.time()  #type: ignore

    async def setup_hook(self):
        # Conexão com Banco de Dados
        try:
            self.db = await aiosqlite.connect("bot.db")
            await self.db.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, command TEXT, date TEXT)")
            await self.db.commit()
            print("🗄️ Banco de dados pronto.")
        except Exception as e:
            print(f"❌ Erro no banco: {e}")
            sys.exit(1)

        # Carregamento de Cogs
        cogs_dir = Path("./cogs")
        if cogs_dir.exists():
            for file in cogs_dir.rglob("*.py"):
                if not file.name.startswith("__"):
                    modulo = ".".join(file.with_suffix("").parts)
                    try:
                        await self.load_extension(modulo)
                        print(f"✅ Módulo: {modulo}")
                    except Exception as e:
                        print(f"❌ Erro em {modulo}: {e}")

    async def close(self):
        if self.db:
            await self.db.close()
        await super().close()

bot = RemnantBot()

async def main():
    if not TOKEN:
        print("❌ TOKEN não encontrado!")
        return
    try:
        async with bot:
            await bot.start(TOKEN)
    except discord.LoginFailure:
        print("❌ Token inválido.")
    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Desligando...")
    finally:
        print("✅ Remnant encerrado.")