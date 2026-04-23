import discord
from discord.ext import commands
import asyncio
import aiosqlite
import datetime
import os
import sys
import time
import aioconsole
from pathlib import Path
from dotenv import load_dotenv
from verbose import log_system, log_error

load_dotenv()
TOKEN = os.getenv("TOKEN")

class RemnantBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        super().__init__(command_prefix="*", intents=intents, help_command=None)
        self.db: aiosqlite.Connection = None  # type: ignore
        self.start_time = time.time()

    # --- TERMINAL INTERATIVO ---
    async def terminal_listener(self):
        await self.wait_until_ready()
        print("💻 CONSOLE: Pronto para comandos (status, reload, stop, clear)")

        while True:
            try:
                cmd = await aioconsole.ainput("")
                cmd = cmd.strip().lower()

                if cmd == "stop":
                    log_system("Desligamento via Terminal.")
                    await self.close()
                    break

                elif cmd == "reload":
                    print("🔄 Recarregando módulos...")
                    count = 0
                    for file in Path("./cogs").rglob("*.py"):
                        if not file.name.startswith("__") and "pycache" not in str(file):
                            modulo = ".".join(file.with_suffix("").parts)
                            try:
                                await self.reload_extension(modulo)
                                count += 1
                            except Exception as e:
                                log_error(f"terminal.reload.{modulo}", e)
                    print(f"✅ {count} módulos atualizados.")

                elif cmd == "status":
                    delta = datetime.timedelta(seconds=int(time.time() - self.start_time))
                    print(f"📊 [STATUS] Uptime: {delta} | Servidores: {len(self.guilds)} | Ping: {round(self.latency * 1000)}ms")

                elif cmd == "clear":
                    os.system('clear' if os.name == 'posix' else 'cls')
                    print("🧹 Console limpo.")

                elif cmd == "":
                    continue

                else:
                    print(f"❓ Comando '{cmd}' desconhecido.")

            except Exception as e:
                print(f"⚠️ Erro no Console: {e}")

    async def setup_hook(self):
        # Conexão com Banco de Dados
        try:
            self.db = await aiosqlite.connect("bot.db")
            await self.db.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, command TEXT, date TEXT)")
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    channel_id INTEGER,
                    content TEXT,
                    timestamp TEXT
                )
            """)
            await self.db.commit()
            log_system("Banco de dados conectado.")
        except Exception as e:
            log_error("bot.setup_hook.db", e)
            sys.exit(1)

        # Carregamento de Cogs
        cogs_dir = Path("./cogs")
        if cogs_dir.exists():
            for file in cogs_dir.rglob("*.py"):
                if not file.name.startswith("__") and "pycache" not in str(file):
                    modulo = ".".join(file.with_suffix("").parts)
                    try:
                        await self.load_extension(modulo)
                        log_system(f"Módulo carregado: {modulo}")
                    except Exception as e:
                        log_error(f"bot.setup_hook.cog.{modulo}", e)

        # Inicia o terminal interativo em segundo plano
        asyncio.create_task(self.terminal_listener())

    async def close(self):
        if self.db:
            await self.db.close()
            log_system("Banco de dados encerrado.")
        await super().close()

bot = RemnantBot()

# --- ON_MESSAGE CENTRALIZADO ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

async def main():
    if not TOKEN:
        log_system("ERRO CRÍTICO: TOKEN não encontrado no .env")
        return
    try:
        async with bot:
            await bot.start(TOKEN)
    except discord.LoginFailure:
        log_error("bot.main", Exception("Token inválido."))
    except Exception as e:
        log_error("bot.main", e)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        print("✅ Remnant encerrado.")