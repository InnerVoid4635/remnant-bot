import discord
from discord.ext import commands
from discord import app_commands
import time
import datetime
from verbose import log_command, log_error

class Geral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_uptime(self):
        start_time = getattr(self.bot, "start_time", time.time())
        difference = int(round(time.time() - start_time))
        return str(datetime.timedelta(seconds=difference))

    # --- COMANDO PING (HYBRID) ---
    async def execute_ping(self, target):
        api_latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="📡 Status de Conexão",
            color=discord.Color.dark_green()
        )
        embed.add_field(name="🌐 API Latency", value=f"`{api_latency}ms`", inline=True)
        embed.add_field(name="⏳ Uptime", value=f"`{self.get_uptime()}`", inline=True)
        embed.set_footer(text="Remnant System • Estabilidade garantida")

        if isinstance(target, discord.Interaction):
            log_command(str(target.user), "/ping", str(target.guild), str(target.channel))
            await target.response.send_message(embed=embed)
        else:
            await target.send(embed=embed)

    @commands.hybrid_command(aliases=["p", "latency"])
    async def ping(self, ctx):
        await self.execute_ping(ctx if not hasattr(ctx, "interaction") else ctx.interaction)

    # --- COMANDO HELP (HYBRID) ---
    @commands.hybrid_command(name="help")
    async def help(self, ctx):
        interaction = ctx.interaction if hasattr(ctx, "interaction") else None

        user = interaction.user if interaction else ctx.author
        guild = interaction.guild if interaction else ctx.guild
        channel = interaction.channel if interaction else ctx.channel

        log_command(str(user), "help", str(guild), str(channel))

        embed = discord.Embed(
            title="📖 Central de Comandos",
            description="Módulos ativos no sistema **Remnant**.\nPrefixos: `/` e `*`",
            color=discord.Color.blue()
        )

        for name, cog in self.bot.cogs.items():
            prefix_cmds = [f"`{c.name}`" for c in cog.get_commands()]
            slash_cmds = [f"`/{c.name}`" for c in cog.get_app_commands()]
            all_cmds = prefix_cmds + slash_cmds

            if all_cmds:
                unique_cmds = sorted(list(set(all_cmds)))
                embed.add_field(name=f"📦 {name}", value=", ".join(unique_cmds), inline=False)

        if interaction:
            await interaction.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

    # --- COMANDO INFO BOT ---
    @app_commands.command(name="info", description="Estatísticas técnicas do Remnant")
    async def info_bot(self, interaction: discord.Interaction):
        log_command(str(interaction.user), "/info", str(interaction.guild), str(interaction.channel))

        total_members = sum(guild.member_count for guild in self.bot.guilds)

        embed = discord.Embed(
            title="🤖 Ficha Técnica: Remnant",
            color=discord.Color.dark_grey()
        )
        embed.add_field(name="🐍 Linguagem", value="Python", inline=True)
        embed.add_field(name="💾 Servidores", value=f"{len(self.bot.guilds)}", inline=True)
        embed.add_field(name="👥 Usuários", value=f"{total_members}", inline=True)
        embed.set_footer(text=f"ID do Bot: {self.bot.user.id}")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Geral(bot))