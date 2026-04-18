import discord
from discord.ext import commands
from discord import app_commands, ui
import re

# --- PARSER DE CORES ROBUSTO ---
def parse_color(color_str: str) -> discord.Color:
    cores = {
        "red": discord.Color.red(), "green": discord.Color.green(),
        "blue": discord.Color.blue(), "purple": discord.Color.purple(),
        "gold": discord.Color.gold(), "black": discord.Color.from_rgb(0, 0, 0)
    }
    
    color_clean = color_str.lower().strip()
    if color_clean in cores: 
        return cores[color_clean]
    
    # Regex para Hex de 3 ou 6 dígitos
    hex_match = re.search(r'^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', color_clean)
    if hex_match:
        hex_val = hex_match.group(1)
        # Se for 3 dígitos (ex: F00), expande para 6 (FF0000)
        if len(hex_val) == 3:
            hex_val = ''.join([c*2 for c in hex_val])
        return discord.Color(int(hex_val, 16))
    
    return discord.Color.blurple()

# --- MODAL COM TRATAMENTO DE ERRO ---
class AvisoModal(ui.Modal, title="Criar Novo Aviso"):
    titulo = ui.TextInput(label="Título", placeholder="Título do aviso...", max_length=100)
    descricao = ui.TextInput(label="Conteúdo", style=discord.TextStyle.paragraph, placeholder="Mensagem...", max_length=2000)
    cor = ui.TextInput(label="Cor (Nome ou Hex)", placeholder="Ex: red, #f00, #ff0000", default="blue", required=False)

    def __init__(self, canal_destino):
        super().__init__()
        self.canal_destino = canal_destino

    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title=self.titulo.value,
                description=self.descricao.value,
                color=parse_color(self.cor.value)
            )
            await self.canal_destino.send(embed=embed)
            await interaction.response.send_message(f"✅ Aviso enviado em {self.canal_destino.mention}", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Eu não tenho permissão para enviar mensagens naquele canal.", ephemeral=True)
        except Exception as e:
            print(f"🔥 Erro no Modal de Aviso: {e}")
            await interaction.response.send_message("❌ Ocorreu um erro interno ao enviar o aviso.", ephemeral=True)

class EmbedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 📦 SLASH: /aviso [canal]
    @app_commands.command(name="aviso", description="Envia um aviso para um canal específico")
    @app_commands.describe(canal="O canal onde o aviso será enviado")
    @app_commands.checks.has_permissions(administrator=True)
    async def aviso(self, interaction: discord.Interaction, canal: discord.TextChannel = None): # type: ignore
        canal_alvo = canal or interaction.channel
        await interaction.response.send_modal(AvisoModal(canal_alvo))

    # 📦 PREFIXO: *embed #canal | Titulo | Descrição | Cor
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def embed(self, ctx, canal: discord.TextChannel, *, texto):
        try:
            partes = [p.strip() for p in texto.split("|")]
            if len(partes) < 2:
                raise commands.BadArgument("Formato inválido. Use: Titulo | Descrição")

            titulo = partes[0]
            desc = partes[1]
            cor_str = partes[2] if len(partes) > 2 else "blue"

            embed = discord.Embed(
                title=titulo,
                description=desc,
                color=parse_color(cor_str)
            )

            await canal.send(embed=embed)
            await ctx.message.add_reaction("✅")

        except commands.BadArgument as e:
            await ctx.send(f"⚠️ {str(e)}", delete_after=5)
        except discord.Forbidden:
            await ctx.send("🚫 Sem permissão para enviar mensagens no canal destino.", delete_after=5)
        except Exception as e:
            print(f"🔥 Erro no comando *embed: {e}")
            await ctx.send("❌ Erro interno ao processar o embed.", delete_after=5)

    # --- HANDLERS DE ERRO ESPECÍFICOS ---
    @aviso.error
    async def aviso_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("🚫 Apenas administradores podem usar este comando.", ephemeral=True)
        else:
            print(f"🔥 Erro no Slash /aviso: {error}")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Você precisa ser Administrador para usar este comando.", delete_after=5)
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("👤 Canal não encontrado.", delete_after=5)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))