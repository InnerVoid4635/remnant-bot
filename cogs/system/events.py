import discord
from discord.ext import commands
import re

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._ready_fired = False # 1. Controle para evitar múltiplos disparos do on_ready

    @commands.Cog.listener()
    async def on_ready(self):
        if not self._ready_fired:
            print(f"--- SISTEMA REMNANT INICIALIZADO ---")
            print(f"🟢 Usuário: {self.bot.user}")
            print(f"📡 Status: Monitoramento ativo")
            print(f"------------------------------------")
            self._ready_fired = True
        else:
            print("🔄 Remnant reconectado com sucesso.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignora bots (incluindo ele mesmo)
        if message.author.bot:
            return

        # 2. Verificação de Menção Robusta
        clean_content = re.sub(r'<@!?(\d+)>', '', message.content).strip()
        if self.bot.user in message.mentions and not clean_content:
            embed = discord.Embed(
                title="🟢 Remnant System", 
                description="Estou online! Use `/help` para ver meus comandos.",
                color=discord.Color.dark_green()
            )
            embed.set_footer(text=f"Latência: {round(self.bot.latency * 1000)}ms")
            await message.channel.send(embed=embed)

        # 3. CORREÇÃO CRÍTICA: process_commands (Severidade Alta)
        # Sem isso, os comandos em outras Cogs param de funcionar!
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # Log no Banco de Dados SQLite
        try:
            if self.bot.db:
                await self.bot.db.execute(
                    "INSERT INTO logs (user, command, date) VALUES (?, ?, datetime('now'))",
                    (str(ctx.author), ctx.command.name)
                )
                await self.bot.db.commit()
        except Exception as e:
            print(f"⚠️ Erro ao salvar log no SQLite: {e}")

async def setup(bot):
    await bot.add_cog(Events(bot))