import discord
from discord.ext import commands
from verbose import log_command, log_event, log_error, log_system
import os
from dotenv import load_dotenv

load_dotenv()
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

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
            # Atualiza member count de todos os servidores no boot
            for guild in self.bot.guilds:
                await self._update_member_count(guild)
        else:
            log_system("Remnant reconectado com sucesso.")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        log_command(
            f"{ctx.author} ({ctx.author.id})",
            ctx.command.name,
            str(ctx.guild),
            str(ctx.channel)
        )

    # --- MEMBER COUNT AUTOMÁTICO ---
    async def _update_member_count(self, guild: discord.Guild):
        try:
            if self.bot.db:
                await self.bot.db.execute(
                    "INSERT OR REPLACE INTO guild_stats (guild_id, guild_name, member_count, updated_at) VALUES (?, ?, ?, datetime('now'))",
                    (guild.id, guild.name, guild.member_count)
                )
                await self.bot.db.commit()
        except Exception as e:
            log_error("events.update_member_count", e)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        log_event("MEMBER_JOIN", f"{member.name} ({member.id}) entrou em {member.guild.name}")
        await self._update_member_count(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self._update_member_count(member.guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        log_event("GUILD_JOIN", f"Bot adicionado em: {guild.name} ({guild.id}) | Dono: {guild.owner} | Membros: {guild.member_count}")
        await self._update_member_count(guild)

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
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            await owner.send(embed=embed)
        except Exception as e:
            log_error("events.on_guild_join", e)

async def setup(bot):
    await bot.add_cog(Events(bot))