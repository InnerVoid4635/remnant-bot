import discord
from discord.ext import commands
from discord import app_commands
import os

# 🔒 CHECK PREFIXO (ADMIN)
def is_admin():
    async def predicate(ctx):
        return ctx.guild and ctx.author.guild_permissions.administrator
    return commands.check(predicate)

# 🔒 CHECK SLASH (ADMIN)
def is_admin_slash():
    async def predicate(interaction: discord.Interaction):
        return interaction.guild and interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 🧹 CLEAR (PREFIXO)
    @commands.command()
    @is_admin()
    async def clear(self, ctx, amount: int):
        amount = min(amount, 100)  # limite de segurança

        deleted = await ctx.channel.purge(limit=amount + 1)

        await ctx.send(
            f"🧹 {len(deleted)-1} mensagens apagadas.",
            delete_after=3
        )

    # 🧹 CLEAR (SLASH)
    @app_commands.command(name="clear", description="Apaga mensagens")
    @is_admin_slash()
    async def clear_slash(self, interaction: discord.Interaction, amount: int):
        amount = min(amount, 100)

        await interaction.response.defer(ephemeral=True)

        deleted = await interaction.channel.purge(limit=amount + 1)

        await interaction.followup.send(
            f"🧹 {len(deleted)-1} mensagens apagadas.",
            ephemeral=True
        )

    # 👢 KICK (PREFIXO)
    @commands.command()
    @is_admin()
    async def kick(self, ctx, member: discord.Member, *, motivo=None):
        await member.kick(reason=motivo)
        await ctx.send(f"👢 {member.mention} foi expulso.")

    # 👢 KICK (SLASH)
    @app_commands.command(name="kick", description="Expulsa um usuário")
    @is_admin_slash()
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, motivo: str = None):
        await member.kick(reason=motivo)

        await interaction.response.send_message(
            f"👢 {member.mention} foi expulso.",
            ephemeral=True
        )

    # 🔨 BAN (PREFIXO)
    @commands.command()
    @is_admin()
    async def ban(self, ctx, member: discord.Member, *, motivo=None):
        await member.ban(reason=motivo)
        await ctx.send(f"🔨 {member.mention} foi banido.")

    # 🔨 BAN (SLASH)
    @app_commands.command(name="ban", description="Bane um usuário")
    @is_admin_slash()
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, motivo: str = None):
        await member.ban(reason=motivo)

        await interaction.response.send_message(
            f"🔨 {member.mention} foi banido.",
            ephemeral=True
        )

    # 🔄 RELOAD ALL
    @commands.command()
    @is_admin()
    async def reloadall(self, ctx):
        sucesso = 0
        erro = 0

        for root, dirs, files in os.walk("./cogs"):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    caminho = os.path.join(root, file)
                    caminho = caminho.replace("./", "").replace("/", ".").replace("\\", ".")[:-3]

                    try:
                        await self.bot.reload_extension(caminho)
                        sucesso += 1
                    except Exception:
                        erro += 1

        await ctx.send(f"🔄 Reload completo!\n✅ {sucesso} | ❌ {erro}")

    # ❌ ERROS PREFIXO
    @clear.error
    @kick.error
    @ban.error
    @reloadall.error
    async def admin_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("🚫 Você não tem permissão para usar esse comando.", delete_after=3)

async def setup(bot):
    await bot.add_cog(Admin(bot))