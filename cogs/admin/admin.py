import discord
from discord.ext import commands
from discord import app_commands
from pathlib import Path
from verbose import log_command, log_error, log_event, log_system

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- UTILITÁRIO DE DM SEGURA ---
    async def safe_dm(self, member: discord.Member, content: str):
        try:
            await member.send(content)
        except discord.Forbidden:
            pass
        except Exception as e:
            log_error("admin.safe_dm", e)

    # --- COMANDO CLEAR ---
    @commands.hybrid_command(name="clear", description="Apaga mensagens do chat")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, quantidade: int):
        quantidade = min(quantidade, 100)

        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
            deleted = await ctx.channel.purge(limit=quantidade)
            log_command(str(ctx.author), f"/clear ({len(deleted)} msgs)", str(ctx.guild), str(ctx.channel))
            await ctx.interaction.followup.send(f"🧹 {len(deleted)} mensagens apagadas.", ephemeral=True)
        else:
            deleted = await ctx.channel.purge(limit=quantidade + 1)
            await ctx.send(f"🧹 {len(deleted)-1} mensagens apagadas.", delete_after=3)

    # --- COMANDO KICK ---
    @commands.hybrid_command(name="kick", description="Expulsa um membro do servidor")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, motivo: str = "Sem motivo especificado"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ Hierarquia insuficiente.", ephemeral=bool(ctx.interaction))
            return

        await self.safe_dm(member, f"👢 Você foi expulso de **{ctx.guild.name}**\nMotivo: {motivo}")
        await member.kick(reason=motivo)
        log_event("KICK", f"{member} expulso de {ctx.guild.name} por {ctx.author} | Motivo: {motivo}")
        await ctx.send(f"👢 {member.mention} expulso.", ephemeral=bool(ctx.interaction))

    # --- COMANDO BAN ---
    @commands.hybrid_command(name="ban", description="Bane um membro do servidor")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, motivo: str = "Sem motivo especificado"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ Hierarquia insuficiente.", ephemeral=bool(ctx.interaction))
            return

        await self.safe_dm(member, f"🔨 Banido de **{ctx.guild.name}**\nMotivo: {motivo}")
        await member.ban(reason=motivo)
        log_event("BAN", f"{member} banido de {ctx.guild.name} por {ctx.author} | Motivo: {motivo}")
        await ctx.send(f"🔨 {member.mention} banido.", ephemeral=bool(ctx.interaction))

    # --- RELOAD ---
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reloadall(self, ctx, sync: bool = False):
        msg = await ctx.send("🔄 Reiniciando sistemas...")
        sucesso, erro = 0, 0

        for file in Path("./cogs").rglob("*.py"):
            if not file.name.startswith("__"):
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

    # --- TRATAMENTO DE ERROS ---
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Você não tem as permissões necessárias.", delete_after=5)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("🤖 Eu não tenho permissão para executar essa ação!", delete_after=5)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("👤 Membro não encontrado.", delete_after=5)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ Argumento inválido.", delete_after=5)
        else:
            log_error("admin.cog_command_error", error)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            if not interaction.response.is_done():
                await interaction.response.send_message("🚫 Você não tem permissão para isso.", ephemeral=True)
            else:
                await interaction.followup.send("🚫 Você não tem permissão para isso.", ephemeral=True)
        else:
            log_error("admin.on_app_command_error", error)

async def setup(bot):
    await bot.add_cog(Admin(bot))