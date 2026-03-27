import discord
from discord import app_commands
from discord.ext import commands

class FunSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Mostra o ping")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong! 🏓")

async def setup(bot):
    await bot.add_cog(FunSlash(bot))