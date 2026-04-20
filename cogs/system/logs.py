import discord
from discord.ext import commands
import os
from verbose import log_event, log_error, log_system

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = int(os.getenv("LOG_CHANNEL_ID", 0))

    # --- UTILITÁRIO DE TRUNCAGEM ---
    def truncate(self, text: str, max_chars: int = 1024) -> str:
        if not text:
            return "*(Sem conteúdo)*"
        return (text[:max_chars - 3] + "...") if len(text) > max_chars else text

    # --- ENVIO SEGURO COM TRY/EXCEPT ---
    async def send_log(self, embed):
        if self.log_channel_id == 0:
            return
        try:
            channel = self.bot.get_channel(self.log_channel_id)
            if not channel:
                channel = await self.bot.fetch_channel(self.log_channel_id)
            await channel.send(embed=embed)
        except discord.Forbidden:
            log_error("logs.send_log", Exception(f"Sem permissão no canal {self.log_channel_id}"))
        except Exception as e:
            log_error("logs.send_log", e)

    # 📝 EVENTO: MENSAGEM DELETADA
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return

        log_event("MSG_DELETE", f"{message.author} em #{message.channel} ({message.guild}) | Conteúdo: {self.truncate(message.content, 200)}")

        embed = discord.Embed(
            title="🗑️ Mensagem Apagada",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Autor", value=message.author.mention, inline=True)
        embed.add_field(name="Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="Conteúdo", value=self.truncate(message.content), inline=False)
        await self.send_log(embed)

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
        embed.add_field(name="Autor", value=before.author.mention, inline=True)
        embed.add_field(name="Canal", value=before.channel.mention, inline=True)
        embed.add_field(name="Antes", value=self.truncate(before.content), inline=False)
        embed.add_field(name="Depois", value=self.truncate(after.content), inline=False)
        await self.send_log(embed)

    # 🚫 EVENTO: MEMBRO BANIDO
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        log_event("BAN", f"{user.name} ({user.id}) banido de {guild.name}")

        embed = discord.Embed(
            title="🔨 Usuário Banido",
            description=f"**{user.name}** (`{user.id}`) foi banido do servidor.",
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await self.send_log(embed)

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
        embed.set_footer(text=f"ID do Usuário: {member.id}")
        await self.send_log(embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
