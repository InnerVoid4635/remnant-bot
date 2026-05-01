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
        # CORRIGIDO: removida a inserção manual no banco com esquema antigo.
        # O verbose.py já grava tudo no banco via SQLiteHandler automaticamente.
        # Esta linha é suficiente — não duplica e usa o esquema correto.
        log_command(
            f"{ctx.author} ({ctx.author.id})",
            ctx.command.name,
            str(ctx.guild),
            str(ctx.channel)
        )

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

            # CORRIGIDO: discord.Embed.Empty foi removido no discord.py v2.
            # set_thumbnail ignora silenciosamente se não for chamado — não precisa de fallback.
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)

            await owner.send(embed=embed)
        except Exception as e:
            log_error("events.on_guild_join", e)

async def setup(bot):
    await bot.add_cog(Events(bot))