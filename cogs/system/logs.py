import discord
from discord.ext import commands
import os
import json
from pathlib import Path
from verbose import log_event, log_error, log_system

# --- SEU ID ---
OWNER_ID = 741273661163569212

# --- ARQUIVO DE CONFIGURAÇÃO DE CANAIS ---
CONFIG_PATH = Path("./log_channels.json")

def load_log_channels() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}

def save_log_channels(data: dict):
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dicionário: guild_id (str) → channel_id (int)
        self.log_channels: dict = load_log_channels()

    # --- UTILITÁRIO DE TRUNCAGEM ---
    def truncate(self, text: str, max_chars: int = 1024) -> str:
        if not text:
            return "*(Sem conteúdo)*"
        return (text[:max_chars - 3] + "...") if len(text) > max_chars else text

    # --- ENVIO: canal do servidor + DM para o dono ---
    async def send_log(self, embed, guild: discord.Guild):
        # Envia no canal de log do servidor
        guild_id = str(guild.id)
        channel_id = self.log_channels.get(guild_id)

        if channel_id:
            try:
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    channel = await self.bot.fetch_channel(channel_id)
                await channel.send(embed=embed)
            except discord.Forbidden:
                log_error("logs.send_log", Exception(f"Sem permissão no canal {channel_id}"))
            except Exception as e:
                log_error("logs.send_log", e)

        # Envia DM para o dono
        try:
            owner = await self.bot.fetch_user(OWNER_ID)
            await owner.send(embed=embed)
        except Exception as e:
            log_error("logs.send_log.dm", e)

    # --- COMANDO: define o canal de log do servidor ---
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlog(self, ctx, canal: discord.TextChannel):
        self.log_channels[str(ctx.guild.id)] = canal.id
        save_log_channels(self.log_channels)
        log_system(f"Canal de log de {ctx.guild.name} definido para #{canal.name} por {ctx.author}")
        await ctx.send(f"✅ Canal de log definido para {canal.mention}", delete_after=5)

    # --- COMANDO: remove o canal de log do servidor ---
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unsetlog(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.log_channels:
            del self.log_channels[guild_id]
            save_log_channels(self.log_channels)
            await ctx.send("✅ Canal de log removido.", delete_after=5)
        else:
            await ctx.send("⚠️ Nenhum canal de log definido para este servidor.", delete_after=5)

    # 📝 EVENTO: MENSAGEM DELETADA
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return

        log_event("MSG_DELETE", f"{message.author} em #{message.channel} ({message.guild})")

        embed = discord.Embed(
            title="🗑️ Mensagem Apagada",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="👤 Autor", value=message.author.mention, inline=True)
        embed.add_field(name="💬 Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="🌐 Servidor", value=str(message.guild), inline=True)
        embed.add_field(name="📝 Conteúdo", value=self.truncate(message.content), inline=False)
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text=f"ID: {message.author.id}")
        await self.send_log(embed, message.guild)

    # ✏️ EVENTO: MENSAGEM EDITADA
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return

        log_event("MSG_EDIT", f"{before.author} em #{before.channel} ({before.guild})")

        embed = discord.Embed(
            title="✏️ Mensagem Editada",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
        embed.add_field(name="👤 Autor", value=before.author.mention, inline=True)
        embed.add_field(name="💬 Canal", value=before.channel.mention, inline=True)
        embed.add_field(name="🌐 Servidor", value=str(before.guild), inline=True)
        embed.add_field(name="📝 Antes", value=self.truncate(before.content), inline=False)
        embed.add_field(name="✅ Depois", value=self.truncate(after.content), inline=False)
        embed.set_thumbnail(url=before.author.display_avatar.url)
        embed.set_footer(text=f"ID: {before.author.id}")
        await self.send_log(embed, before.guild)

    # 🚫 EVENTO: MEMBRO BANIDO
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        log_event("BAN", f"{user.name} ({user.id}) banido de {guild.name}")

        embed = discord.Embed(
            title="🔨 Usuário Banido",
            description=f"**{user.name}** foi banido do servidor.",
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.add_field(name="🆔 ID", value=f"`{user.id}`", inline=True)
        embed.add_field(name="🌐 Servidor", value=guild.name, inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        await self.send_log(embed, guild)

    # 🚪 EVENTO: MEMBRO SAIU
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        log_event("MEMBER_LEAVE", f"{member.name} ({member.id}) saiu de {member.guild.name}")

        embed = discord.Embed(
            title="🚪 Membro Saiu",
            description=f"**{member.name}** deixou o servidor.",
            color=discord.Color.light_grey(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(name="🌐 Servidor", value=member.guild.name, inline=True)
        embed.add_field(name="👥 Membros restantes", value=str(member.guild.member_count), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await self.send_log(embed, member.guild)

async def setup(bot):
    await bot.add_cog(Logs(bot))