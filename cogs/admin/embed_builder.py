import discord
from discord.ext import commands
from discord import app_commands

# 🔒 CHECK ADMIN
def is_admin():
    async def predicate(ctx):
        return ctx.guild and ctx.author.guild_permissions.administrator
    return commands.check(predicate)

def is_admin_slash():
    async def predicate(interaction: discord.Interaction):
        return interaction.guild and interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

# 🎨 cores simples
def get_color(color_name):
    cores = {
        "red": discord.Color.red(),
        "green": discord.Color.green(),
        "blue": discord.Color.blue(),
        "purple": discord.Color.purple(),
        "gold": discord.Color.gold()
    }
    return cores.get(color_name.lower(), discord.Color.blurple())

class EmbedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 📦 PREFIXO
    @commands.command()
    @is_admin()
    async def embed(self, ctx, *, texto):
        try:
            partes = texto.split("|")

            titulo = partes[0].strip()
            descricao = partes[1].strip()
            cor = partes[2].strip() if len(partes) > 2 else "blue"

            embed = discord.Embed(
                title=titulo,
                description=descricao,
                color=get_color(cor)
            )

            await ctx.send(embed=embed)

        except:
            await ctx.send(
                "❌ Uso correto:\n`*embed titulo | descrição | cor(opcional)`",
            )

    # 📦 SLASH
    @app_commands.command(name="embed", description="Cria um embed")
    @is_admin_slash()
    async def embed_slash(
        self,
        interaction: discord.Interaction,
        titulo: str,
        descricao: str,
        cor: str = "blue"
    ):
        embed = discord.Embed(
            title=titulo,
            description=descricao,
            color=get_color(cor)
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))