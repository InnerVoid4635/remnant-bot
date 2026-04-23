import discord
from discord.ext import commands
from verbose import log_command, log_event, log_error, log_system

# --- SEU ID DO DISCORD ---
# Para encontrar: Ative o Modo Desenvolvedor no Discord
# Configurações → Avançado → Modo Desenvolvedor
# Depois clique com botão direito no seu usuário → Copiar ID
OWNER_ID = 741273661163569212  # substitua pelo seu ID

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

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        log_event("GUILD_JOIN", f"Bot adicionado em: {guild.name} ({guild.id}) | Dono: {guild.owner} | Membros: {guild.member_count}")

        if OWNER_ID == 0:
            return

        try:
            owner = await self.bot.fetch_user(OWNER_ID)
            embed = discord.Embed(
                title="🟢 Bot adicionado a um novo servidor!",
                color=discord.Color.green()
            )
            embed.add_field(name="🌐 Servidor", value=f"{guild.name} (`{guild.id}`)", inline=False)
            embed.add_field(name="👑 Dono", value=str(guild.owner), inline=True)
            embed.add_field(name="👥 Membros", value=str(guild.member_count), inline=True)
            embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty) # type: ignore
            await owner.send(embed=embed)
        except Exception as e:
            log_error("events.on_guild_join", e)

async def setup(bot):
    await bot.add_cog(Events(bot))