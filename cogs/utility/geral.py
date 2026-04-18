import discord
from discord.ext import commands
from discord import app_commands
import time
import datetime

class Geral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_uptime(self):
        # 1. Correção Uptime: Busca o tempo inicial direto do bot para não resetar no reload
        # Certifique-se de que no bot.py você definiu self.start_time = time.time() no __init__
        start_time = getattr(self.bot, "start_time", time.time())
        difference = int(round(time.time() - start_time))
        return str(datetime.timedelta(seconds=difference))

    # --- COMANDO PING ---
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
            await target.response.send_message(embed=embed)
        else:
            await target.send(embed=embed)

    @commands.command(aliases=["p", "latency"])
    async def ping(self, ctx):
        await self.execute_ping(ctx)

    @app_commands.command(name="ping", description="Verifica a latência e o tempo de atividade do bot")
    async def ping_slash(self, interaction: discord.Interaction):
        await self.execute_ping(interaction)

    # --- COMANDO HELP (Agora com Slash Commands!) ---
    @app_commands.command(name="help", description="Lista todos os comandos disponíveis")
    async def help_slash(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Central de Comandos",
            description="Módulos ativos no sistema **Remnant**.\nPrefixos: `/` e `*`",
            color=discord.Color.blue()
        )
        
        for name, cog in self.bot.cogs.items():
            # 2. Correção Slash Ocultos: Pega comandos de prefixo E comandos de barra
            prefix_cmds = [f"`{c.name}`" for c in cog.get_commands()]
            slash_cmds = [f"`/{c.name}`" for c in cog.get_app_commands()]
            
            all_cmds = prefix_cmds + slash_cmds
            
            if all_cmds:
                # Remove duplicados (ex: ping e /ping) para manter o help limpo
                unique_cmds = sorted(list(set(all_cmds)))
                embed.add_field(name=f"📦 {name}", value=", ".join(unique_cmds), inline=False)

        await interaction.response.send_message(embed=embed)

    @commands.command()
    async def help(self, ctx):
        await ctx.send("💡 Dica: Use `/help` para ver a lista visual de todos os comandos!")

    # --- COMANDO INFO BOT ---
    @app_commands.command(name="info", description="Estatísticas técnicas do Remnant")
    async def info_bot(self, interaction: discord.Interaction):
        # 3. Correção Contagem: Soma membros únicos de todas as guildas
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