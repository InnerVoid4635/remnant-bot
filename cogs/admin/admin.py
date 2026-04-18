import discord
from discord.ext import commands
from discord import app_commands
from pathlib import Path

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
            print(f"⚠️ Erro ao enviar DM: {e}")

    # --- COMANDO CLEAR ---
    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        amount = min(amount, 100)
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 {len(deleted)-1} mensagens apagadas.", delete_after=3)

    @app_commands.command(name="clear", description="Apaga mensagens do chat")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear_slash(self, interaction: discord.Interaction, quantidade: int):
        quantidade = min(quantidade, 100)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=quantidade) # type: ignore
        await interaction.followup.send(f"🧹 {len(deleted)} mensagens apagadas.", ephemeral=True)

    # --- COMANDO KICK ---
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, motivo: str = "Sem motivo especificado"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ Hierarquia insuficiente.")
        
        await self.safe_dm(member, f"👢 Você foi expulso de **{ctx.guild.name}**\nMotivo: {motivo}")
        await member.kick(reason=motivo)
        await ctx.send(f"👢 {member.mention} expulso.")

    @app_commands.command(name="kick", description="Expulsa um membro")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_slash(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
        if membro.top_role >= interaction.user.top_role: # type: ignore
            return await interaction.response.send_message("❌ Hierarquia insuficiente.", ephemeral=True)
        
        await self.safe_dm(membro, f"👢 Expulso de **{interaction.guild.name}**\nMotivo: {motivo}") # type: ignore
        await membro.kick(reason=motivo)
        await interaction.response.send_message(f"👢 {membro.mention} expulso.", ephemeral=True)

    # --- COMANDO BAN ---
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, motivo: str = "Sem motivo especificado"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ Hierarquia insuficiente.")
        
        await self.safe_dm(member, f"🔨 Banido de **{ctx.guild.name}**\nMotivo: {motivo}")
        await member.ban(reason=motivo)
        await ctx.send(f"🔨 {member.mention} banido.")

    @app_commands.command(name="ban", description="Bane um membro do servidor")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_slash(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
        if membro.top_role >= interaction.user.top_role: # type: ignore
            return await interaction.response.send_message("❌ Hierarquia insuficiente.", ephemeral=True)
        
        await self.safe_dm(membro, f"🔨 Banido de **{interaction.guild.name}**\nMotivo: {motivo}") # type: ignore
        await membro.ban(reason=motivo)
        await interaction.response.send_message(f"🔨 {membro.mention} banido.", ephemeral=True)

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
                    print(f"Erro no reload de {modulo}: {e}")
                    erro += 1
        
        if sync:
            await self.bot.tree.sync()
            sync_status = " | 🌳 Árvore Sincronizada"
        else:
            sync_status = ""

        await msg.edit(content=f"🔄 **Sistemas Recarregados!**\n✅ {sucesso} | ❌ {erro}{sync_status}")

    # --- TRATAMENTO DE ERROS DE PREFIXO (COSTA A COSTA) ---
    async def cog_command_error(self, ctx, error):
        """Handler que captura erros de qualquer comando de prefixo desta Cog."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Você não tem as permissões necessárias.", delete_after=5)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("🤖 Eu não tenho permissão para executar essa ação!", delete_after=5)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("👤 Membro não encontrado.", delete_after=5)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ Argumento inválido. Verifique se digitou o número ou menção corretamente.", delete_after=5)
        else:
            print(f"🔥 Erro não tratado no prefixo: {error}")

    # --- TRATAMENTO DE ERROS SLASH ---
    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            if not interaction.response.is_done():
                await interaction.response.send_message("🚫 Você não tem permissão para isso.", ephemeral=True)
            else:
                await interaction.followup.send("🚫 Você não tem permissão para isso.", ephemeral=True)
        else:
            print(f"🔥 Erro no Slash Command: {error}")

async def setup(bot):
    await bot.add_cog(Admin(bot))