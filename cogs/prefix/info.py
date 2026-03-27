import discord
from discord.ext import commands
from discord import app_commands
import random

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 🔍 SCAN (PREFIXO)
    @commands.command()
    async def scan(self, ctx, member: discord.Member = None):  # type: ignore
        member = member or ctx.author
        embed = self.create_scan_embed(member)
        await ctx.send(embed=embed)

    # 🔍 SCAN (SLASH)
    @app_commands.command(name="scan", description="Mostra informações de um usuário")
    async def scan_slash(self, interaction: discord.Interaction, member: discord.Member = None):  # type: ignore
        member = member or interaction.user
        embed = self.create_scan_embed(member)
        await interaction.response.send_message(embed=embed)

    # 🧠 EMBED SCAN
    def create_scan_embed(self, member):
        cor = discord.Color.red() if member.bot else discord.Color.green()

        embed = discord.Embed(
            title="🔍 Informações do usuário",
            description=f"Usuário: {member.mention}",
            color=cor
        )

        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_thumbnail(url=avatar_url)

        # tipo + status
        if member.bot:
            tipo = "🤖 Bot"
            status_lista = [
                "Sistema automatizado",
                "Bot verificado",
                "Executando normalmente",
                "Atividade automatizada detectada"
            ]
        else:
            tipo = "👤 Usuário"
            status_lista = [
                "Usuário ativo",
                "Conta válida",
                "Sem anomalias detectadas",
                "Atividade normal"
            ]

        status = random.choice(status_lista)

        # dados principais
        embed.add_field(name="🆔 ID", value=member.id, inline=False)
        embed.add_field(name="👤 Nome", value=member.name, inline=True)
        embed.add_field(name="Tipo", value=tipo, inline=True)
        embed.add_field(name="Status", value=status, inline=False)

        # datas
        embed.add_field(
            name="📅 Conta criada em",
            value=member.created_at.strftime("%d/%m/%Y"),
            inline=False
        )

        embed.add_field(
            name="📥 Entrou no servidor",
            value=member.joined_at.strftime("%d/%m/%Y") if member.joined_at else "Desconhecido",
            inline=False
        )

        # cargo
        embed.add_field(
            name="🎭 Cargo mais alto",
            value=member.top_role.mention if member.top_role else "Nenhum",
            inline=False
        )

        # footer aleatório (mais leve)
        mensagens = [
            "Informações coletadas com sucesso.",
            "Dados atualizados.",
            "Consulta finalizada.",
            "Sistema operacional estável."
        ]

        embed.set_footer(text=random.choice(mensagens))

        return embed

    # 🖼️ AVATAR (PREFIXO)
    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):  # type: ignore
        member = member or ctx.author
        embed = self.create_avatar_embed(member)
        await ctx.send(embed=embed)

    # 🖼️ AVATAR (SLASH)
    @app_commands.command(name="avatar", description="Mostra o avatar do usuário")
    async def avatar_slash(self, interaction: discord.Interaction, member: discord.Member = None):  # type: ignore
        member = member or interaction.user
        embed = self.create_avatar_embed(member)
        await interaction.response.send_message(embed=embed)

    def create_avatar_embed(self, member):
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url

        embed = discord.Embed(
            title=f"🖼️ Avatar de {member.name}",
            color=discord.Color.purple()
        )

        embed.set_image(url=avatar_url)
        return embed

    # 🌐 SERVER (PREFIXO)
    @commands.command()
    async def server(self, ctx):
        if not ctx.guild:
            return await ctx.send("❌ Esse comando só funciona em servidores.")
        embed = self.create_server_embed(ctx.guild)
        await ctx.send(embed=embed)

    # 🌐 SERVER (SLASH)
    @app_commands.command(name="server", description="Mostra informações do servidor")
    async def server_slash(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("❌ Esse comando só funciona em servidores.", ephemeral=True)
        embed = self.create_server_embed(interaction.guild)
        await interaction.response.send_message(embed=embed)

    def create_server_embed(self, guild):
        embed = discord.Embed(
            title=f"🌐 {guild.name}",
            color=discord.Color.green()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👥 Membros", value=guild.member_count)
        embed.add_field(name="👑 Dono", value=guild.owner)
        embed.add_field(name="📅 Criado em", value=guild.created_at.strftime("%d/%m/%Y"))

        embed.set_footer(text="Informações do servidor")

        return embed

async def setup(bot):
    await bot.add_cog(Info(bot))