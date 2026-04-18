import discord
from discord.ext import commands
from discord import app_commands
import random

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_scan_embed(self, member: discord.Member, requester: discord.Member):
        # Cor baseada no cargo mais alto
        cor = member.color if member.color.value != 0 else discord.Color.blue()
        
        embed = discord.Embed(
            title="🔍 Scanner de Perfil",
            description=f"Alvo: {member.mention}",
            color=cor
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        # 1. Correção Status: Menos aleatório, mais informativo
        if member.bot:
            tipo = "🤖 Bot"
            status = "Processamento Automatizado"
        else:
            tipo = "👤 Usuário"
            # Mostra o status real se possível, senão um padrão estável
            status = str(member.status).title() if member.status else "Invisível/Offline"

        embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=False)
        embed.add_field(name="👤 Tag", value=f"`{member.name}`", inline=True)
        embed.add_field(name="🏷️ Tipo", value=tipo, inline=True)
        embed.add_field(name="📡 Status Real", value=f"`{status}`", inline=False)

        # Datas
        criacao = discord.utils.format_dt(member.created_at, "D")
        criacao_rel = discord.utils.format_dt(member.created_at, "R")
        embed.add_field(name="📅 Conta criada", value=f"{criacao} ({criacao_rel})", inline=False)

        if member.joined_at:
            entrada = discord.utils.format_dt(member.joined_at, "D")
            entrada_rel = discord.utils.format_dt(member.joined_at, "R")
            embed.add_field(name="📥 Entrada no Servidor", value=f"{entrada} ({entrada_rel})", inline=False)

        # Cargos
        roles = [role.mention for role in reversed(member.roles) if role.name != "@everyone"]
        top_role = member.top_role.mention if len(roles) > 0 else "Nenhum"
        embed.add_field(name="🎭 Cargo principal", value=top_role, inline=True)
        embed.add_field(name="📊 Total de cargos", value=f"{len(roles)}", inline=True)

        # 2. Correção Footer: Agora mostra quem REALMENTE pediu o comando
        embed.set_footer(text=f"Solicitado por {requester.name}", icon_url=requester.display_avatar.url)
        return embed

    @app_commands.command(name="scan", description="Mostra o perfil detalhado de um usuário")
    async def scan_slash(self, interaction: discord.Interaction, member: discord.Member = None): # type: ignore
        target = member or interaction.user
        await interaction.response.send_message(embed=self.create_scan_embed(target, interaction.user)) # type: ignore

    @commands.command()
    async def scan(self, ctx, member: discord.Member = None):  # type: ignore
        target = member or ctx.author
        await ctx.send(embed=self.create_scan_embed(target, ctx.author))

    # --- AVATAR ---
    @app_commands.command(name="avatar", description="Mostra o avatar ampliado")
    async def avatar_slash(self, interaction: discord.Interaction, member: discord.Member = None): # type: ignore
        target = member or interaction.user
        embed = discord.Embed(title=f"🖼️ Avatar de {target.name}", color=discord.Color.purple())
        embed.set_image(url=target.display_avatar.url)
        embed.set_footer(text=f"Requisitado por {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):  # type: ignore
        target = member or ctx.author
        embed = discord.Embed(title=f"🖼️ Avatar de {target.name}", color=discord.Color.purple())
        embed.set_image(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    # --- SERVER INFO ---
    def create_server_embed(self, guild: discord.Guild, requester: discord.Member):
        embed = discord.Embed(title=f"🌐 {guild.name}", color=discord.Color.green())
        if guild.icon: embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👑 Dono", value=guild.owner.mention if guild.owner else "N/A", inline=True)
        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👥 Membros", value=f"`{guild.member_count}`", inline=True)
        embed.add_field(name="🎭 Cargos", value=f"`{len(guild.roles)}`", inline=True)
        embed.add_field(name="📅 Criado em", value=discord.utils.format_dt(guild.created_at, "D"), inline=False)
        
        embed.set_footer(text=f"Consultado por {requester.name}")
        return embed

    @app_commands.command(name="server", description="Exibe informações do servidor")
    @app_commands.guild_only()
    async def server_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.create_server_embed(interaction.guild, interaction.user)) # type: ignore

    @commands.command()
    @commands.guild_only()
    async def server(self, ctx):
        await ctx.send(embed=self.create_server_embed(ctx.guild, ctx.author))

    # 3. Handler de Erros da Cog
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("👤 Não consegui encontrar esse membro. Verifique o nome ou ID.", delete_after=5)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("🚫 Este comando só pode ser usado dentro de um servidor.")
        else:
            print(f"🔥 Erro na Cog Info: {error}")

async def setup(bot):
    await bot.add_cog(Info(bot))