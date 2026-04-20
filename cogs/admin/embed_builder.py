import discord
from discord.ext import commands
from discord import app_commands, ui
import re
import json
from pathlib import Path
from verbose import log_command, log_error, log_event

# --- PASTA DE TEMPLATES ---
TEMPLATES_DIR = Path("./templates")
TEMPLATES_DIR.mkdir(exist_ok=True)

# --- PARSER DE CORES ---
def parse_color(color_str: str) -> discord.Color:
    cores = {
        "red": discord.Color.red(), "green": discord.Color.green(),
        "blue": discord.Color.blue(), "purple": discord.Color.purple(),
        "gold": discord.Color.gold(), "black": discord.Color.from_rgb(0, 0, 0)
    }
    color_clean = color_str.lower().strip()
    if color_clean in cores:
        return cores[color_clean]
    hex_match = re.search(r'^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', color_clean)
    if hex_match:
        hex_val = hex_match.group(1)
        if len(hex_val) == 3:
            hex_val = ''.join([c*2 for c in hex_val])
        return discord.Color(int(hex_val, 16))
    return discord.Color.blurple()

# --- FUNÇÕES DE TEMPLATE ---
def save_template(name: str, titulo: str, descricao: str, cor: str):
    path = TEMPLATES_DIR / f"{name}.json"
    data = {"titulo": titulo, "descricao": descricao, "cor": cor}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_template(name: str) -> dict | None:
    path = TEMPLATES_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def delete_template(name: str) -> bool:
    path = TEMPLATES_DIR / f"{name}.json"
    if not path.exists():
        return False
    path.unlink()
    return True

def list_templates() -> list[str]:
    return [f.stem for f in TEMPLATES_DIR.glob("*.json")]

# --- MODAL DE CRIAÇÃO/EDIÇÃO ---
class EmbedModal(ui.Modal, title="Criar Embed"):
    titulo = ui.TextInput(label="Título", placeholder="Título do embed...", max_length=100)
    descricao = ui.TextInput(label="Conteúdo", style=discord.TextStyle.paragraph, placeholder="Mensagem...", max_length=2000)
    cor = ui.TextInput(label="Cor (Nome ou Hex)", placeholder="Ex: red, #f00, #ff0000", default="blue", required=False)
    salvar_como = ui.TextInput(label="Salvar como template? (opcional)", placeholder="Ex: boas_vindas (deixe vazio para não salvar)", required=False)

    def __init__(self, canal_destino, autor, prefill: dict = None): # type: ignore
        super().__init__()
        self.canal_destino = canal_destino
        self.autor = autor
        # Preenche o modal com dados do template se fornecido
        if prefill:
            self.titulo.default = prefill.get("titulo", "")
            self.descricao.default = prefill.get("descricao", "")
            self.cor.default = prefill.get("cor", "blue")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title=self.titulo.value,
                description=self.descricao.value,
                color=parse_color(self.cor.value or "blue")
            )
            await self.canal_destino.send(embed=embed)
            log_event("EMBED", f"{self.autor} enviou embed em #{self.canal_destino.name} | Título: {self.titulo.value}")

            # Salva como template se o campo foi preenchido
            nome_template = self.salvar_como.value.strip()
            if nome_template:
                save_template(nome_template, self.titulo.value, self.descricao.value, self.cor.value or "blue")
                log_event("TEMPLATE_SAVE", f"{self.autor} salvou template '{nome_template}'")
                await interaction.response.send_message(
                    f"✅ Embed enviado em {self.canal_destino.mention} e salvo como template `{nome_template}`.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"✅ Embed enviado em {self.canal_destino.mention}",
                    ephemeral=True
                )
        except discord.Forbidden:
            log_error("EmbedModal.on_submit", Exception(f"Sem permissão no canal {self.canal_destino.name}"))
            await interaction.response.send_message("❌ Sem permissão para enviar naquele canal.", ephemeral=True)
        except Exception as e:
            log_error("EmbedModal.on_submit", e)
            await interaction.response.send_message("❌ Erro interno ao enviar o embed.", ephemeral=True)

# --- COG ---
class EmbedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- /embed ou *embed ---
    @commands.hybrid_command(name="embed", description="Envia um embed para um canal. Uso: *embed #canal | Título | Descrição | Cor")
    @commands.has_permissions(administrator=True)
    async def embed(self, ctx, canal: discord.TextChannel = None):  # type: ignore
        canal_alvo = canal or ctx.channel

        if ctx.interaction:
            log_command(str(ctx.author), f"/embed → #{canal_alvo.name}", str(ctx.guild))
            await ctx.interaction.response.send_modal(EmbedModal(canal_alvo, ctx.author))
            return

        # Prefixo: mostra instruções se não tiver conteúdo
        raw = ctx.message.content
        partes_raw = raw.split("|")

        if len(partes_raw) < 2:
            embed_help = discord.Embed(
                title="📋 Como usar o comando *embed",
                description="Envia um embed personalizado para um canal.",
                color=discord.Color.blue()
            )
            embed_help.add_field(name="📌 Sintaxe", value="`*embed #canal | Título | Descrição | Cor`", inline=False)
            embed_help.add_field(name="🎨 Cores", value="`red`, `green`, `blue`, `purple`, `gold`, `black` ou hex como `#ff0000`", inline=False)
            embed_help.add_field(
                name="✅ Exemplos",
                value=(
                    "`*embed #avisos | Manutenção | O servidor estará em manutenção às 20h. | red`\n"
                    "`*embed #geral | Bem-vindo! | Obrigado por entrar no servidor. | #00ff00`"
                ),
                inline=False
            )
            embed_help.add_field(name="📁 Templates", value="`*template load nome #canal` — carrega um template salvo", inline=False)
            embed_help.set_footer(text="A cor é opcional — padrão: blue")
            await ctx.send(embed=embed_help)
            return

        try:
            partes = [p.strip() for p in partes_raw]
            titulo = partes[1] if len(partes) > 1 else partes[0]
            desc = partes[2] if len(partes) > 2 else ""
            cor_str = partes[3] if len(partes) > 3 else "blue"

            if not titulo or not desc:
                raise commands.BadArgument("Título e Descrição são obrigatórios.")

            embed = discord.Embed(title=titulo, description=desc, color=parse_color(cor_str))
            await canal_alvo.send(embed=embed)
            log_event("EMBED", f"{ctx.author} enviou embed em #{canal_alvo.name} | Título: {titulo}")
            await ctx.message.add_reaction("✅")

        except commands.BadArgument as e:
            await ctx.send(f"⚠️ {str(e)}", delete_after=5)
        except discord.Forbidden:
            log_error("embed_builder.embed", Exception(f"Sem permissão no canal {canal_alvo.name}"))
            await ctx.send("🚫 Sem permissão para enviar mensagens no canal destino.", delete_after=5)
        except Exception as e:
            log_error("embed_builder.embed", e)
            await ctx.send("❌ Erro interno ao processar o embed.", delete_after=5)

    # --- TEMPLATE LOAD ---
    @commands.hybrid_command(name="template", description="Carrega um template de embed salvo")
    @commands.has_permissions(administrator=True)
    async def template(self, ctx, nome: str = None, canal: discord.TextChannel = None):  # type: ignore
        canal_alvo = canal or ctx.channel

        # Lista templates se não passar nome
        if not nome:
            templates = list_templates()
            if not templates:
                await ctx.send("📁 Nenhum template salvo ainda. Use `/embed` e preencha o campo 'Salvar como template'.", ephemeral=bool(ctx.interaction))
                return
            embed = discord.Embed(title="📁 Templates Disponíveis", color=discord.Color.blue())
            embed.description = "\n".join(f"• `{t}`" for t in templates)
            embed.set_footer(text="Use: *template load nome #canal")
            await ctx.send(embed=embed, ephemeral=bool(ctx.interaction))
            return

        # Carrega o template
        data = load_template(nome)
        if not data:
            await ctx.send(f"❌ Template `{nome}` não encontrado. Use `*template` para ver os disponíveis.", ephemeral=bool(ctx.interaction))
            return

        if ctx.interaction:
            log_command(str(ctx.author), f"/template {nome} → #{canal_alvo.name}", str(ctx.guild))
            await ctx.interaction.response.send_modal(EmbedModal(canal_alvo, ctx.author, prefill=data))
        else:
            # No prefixo envia direto com os dados do template
            embed = discord.Embed(
                title=data["titulo"],
                description=data["descricao"],
                color=parse_color(data.get("cor", "blue"))
            )
            await canal_alvo.send(embed=embed)
            log_event("TEMPLATE_LOAD", f"{ctx.author} carregou template '{nome}' em #{canal_alvo.name}")
            await ctx.message.add_reaction("✅")

    # --- TEMPLATE DELETE ---
    @commands.hybrid_command(name="template_delete", description="Deleta um template salvo")
    @commands.has_permissions(administrator=True)
    async def template_delete(self, ctx, nome: str):
        if delete_template(nome):
            log_event("TEMPLATE_DELETE", f"{ctx.author} deletou template '{nome}'")
            await ctx.send(f"🗑️ Template `{nome}` deletado.", ephemeral=bool(ctx.interaction))
        else:
            await ctx.send(f"❌ Template `{nome}` não encontrado.", ephemeral=bool(ctx.interaction))

    # --- HANDLERS DE ERRO ---
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Você precisa ser Administrador para usar este comando.", delete_after=5)
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ Canal não encontrado.", delete_after=5)
        else:
            log_error("embed_builder.cog_command_error", error)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))