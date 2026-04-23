import discord
from discord.ext import commands
from pathlib import Path
from verbose import log_system, log_error

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- RELOAD ---
    @commands.command()
    @commands.is_owner()
    async def reloadall(self, ctx, sync: bool = False):
        msg = await ctx.send("🔄 Reiniciando sistemas...")
        sucesso, erro = 0, 0

        for file in Path("./cogs").rglob("*.py"):
            if not file.name.startswith("__") and "pycache" not in str(file):
                modulo = ".".join(file.with_suffix("").parts)
                try:
                    await self.bot.reload_extension(modulo)
                    sucesso += 1
                except Exception as e:
                    log_error(f"reloadall.{modulo}", e)
                    erro += 1

        if sync:
            await self.bot.tree.sync()
            sync_status = " | 🌳 Árvore Sincronizada"
            log_system("Árvore de comandos sincronizada via reloadall.")
        else:
            sync_status = ""

        log_system(f"Reloadall por {ctx.author} | ✅ {sucesso} | ❌ {erro}")
        await msg.edit(content=f"🔄 **Sistemas Recarregados!**\n✅ {sucesso} | ❌ {erro}{sync_status}")

    # --- ERRO: não é o dono ---
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("🚫 Apenas o dono do bot pode usar este comando.", delete_after=5)
        else:
            log_error("owner.cog_command_error", error)

async def setup(bot):
    await bot.add_cog(Owner(bot))
