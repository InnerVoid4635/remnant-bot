import discord
from discord.ext import commands
from verbose import log_command, log_event, log_error, log_system

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._ready_fired = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self._ready_fired:
            log_system("--- SISTEMA REMNANT INICIALIZADO ---")
            log_system(f"Usuário: {self.bot.user}")
            log_system("Status: Monitoramento ativo")
            self._ready_fired = True
        else:
            log_system("Remnant reconectado com sucesso.")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        log_command(str(ctx.author), ctx.command.name, str(ctx.guild), str(ctx.channel))
        try:
            if self.bot.db:
                await self.bot.db.execute(
                    "INSERT INTO logs (user, command, date) VALUES (?, ?, datetime('now'))",
                    (str(ctx.author), ctx.command.name)
                )
                await self.bot.db.commit()
        except Exception as e:
            log_error("events.on_command", e)

async def setup(bot):
    await bot.add_cog(Events(bot))