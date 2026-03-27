import discord
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # 🏓 PING PRINCIPAL (profissional)
    @commands.command(aliases=["p"])
    async def ping(self, ctx):
        api_latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🟢 Sistema de resposta",
            color=discord.Color.dark_green()
        )

        embed.add_field(name="API", value=f"{api_latency}ms")
        embed.add_field(name="Mensagem", value="Calculando...")

        msg = await ctx.send(embed=embed)

        latency = round((msg.created_at - ctx.message.created_at).total_seconds() * 1000)

        embed.set_field_at(1, name="Mensagem", value=f"{latency}ms")
        embed.set_footer(text="Spring Bot ⚠️ sistema instável")

        await msg.edit(embed=embed)
async def setup(bot):
    await bot.add_cog(Fun(bot))