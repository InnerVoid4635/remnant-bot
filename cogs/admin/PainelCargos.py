import discord
from discord.ext import commands
from discord import app_commands

# ─────────────────────────────────────────────────────────
# HELPERS MODIFICADOS (Suporte a Nome/Emoji customizado)
# ─────────────────────────────────────────────────────────
def parse_roles_input(raw: str) -> list[dict]:
    """Lê entradas como '✅ Vídeo novo=1455970332669116447' e separa o Rótulo do ID."""
    linhas = [item.strip() for item in raw.split(";") if item.strip()]
    resultado = []
    
    for linha in linhas:
        if "=" in linha:
            nome_custom, id_raw = linha.split("=", 1)
            id_raw = id_raw.strip()
            if id_raw.isdigit():
                resultado.append({"label": nome_custom.strip(), "id": int(id_raw)})
        else:
            if linha.isdigit():
                resultado.append({"label": None, "id": int(linha)})
            else:
                resultado.append({"label": linha, "id": linha})
                
    return resultado

def resolve_role(guild: discord.Guild, token) -> discord.Role | None:
    if isinstance(token, int):
        return guild.get_role(token)
        
    token_str = str(token).strip()
    if token_str.isdigit():
        return guild.get_role(int(token_str))

    return discord.utils.find(lambda r: r.name.lower() == token_str.lower(), guild.roles)

def build_panel_embed(title: str, description: str) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=discord.Color.gold())
    embed.set_footer(text="Remnant Bot — Sistema de Identidade")
    return embed


# ─────────────────────────────────────────────────────────
# VIEW + SELECT (SISTEMA DE DROPDOWN)
# ─────────────────────────────────────────────────────────
class CargoSelect(discord.ui.Select):
    def __init__(self, roles_data: list[dict], guild: discord.Guild, placeholder_text: str):
        self.roles = []
        options = []

        for data in roles_data[:25]:
            role = resolve_role(guild, data["id"])
            if role is None: continue
                
            self.roles.append(role)
            label_text = data["label"] if data["label"] else role.name
            
            options.append(discord.SelectOption(
                label=label_text[:100],
                value=str(role.id),
                description=f"Adicionar/Remover {role.name}"
            ))

        super().__init__(
            placeholder=placeholder_text[:150],
            min_values=0,
            max_values=len(options) if options else 1,
            options=options,
            custom_id="remnant:cargos_dropdown"
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("❌ Erro de ambiente.", ephemeral=True)

        member = interaction.user
        selected_ids = {int(value) for value in self.values}
        added, removed = [], []

        try:
            for role in self.roles:
                if role.id in selected_ids:
                    if role not in member.roles:
                        await member.add_roles(role, reason="Remnant — Dropdown")
                        added.append(role.mention)
                else:
                    if role in member.roles:
                        await member.remove_roles(role, reason="Remnant — Dropdown")
                        removed.append(role.mention)
        except discord.Forbidden:
            return await interaction.response.send_message("🚫 Sem permissão para gerenciar estes cargos.", ephemeral=True)

        partes = []
        if added: partes.append("✅ Adicionados: " + ", ".join(added))
        if removed: partes.append("❌ Removidos: " + ", ".join(removed))
        if not partes: partes.append("ℹ️ Nenhuma alteração feita.")

        await interaction.response.send_message("\n".join(partes), ephemeral=True)


class RolePanelView(discord.ui.View):
    def __init__(self, roles_data: list[dict], guild: discord.Guild, placeholder_text: str):
        super().__init__(timeout=None)
        self.add_item(CargoSelect(roles_data, guild, placeholder_text))


# ─────────────────────────────────────────────────────────
# MODAL (SLASH COMMAND DO DROPDOWN)
# ─────────────────────────────────────────────────────────
class PainelCargosModal(discord.ui.Modal):
    def __init__(self, canal: discord.TextChannel):
        super().__init__(title="Configurar Painel de Cargos")
        self.canal = canal

        self.titulo_input = discord.ui.TextInput(label="Título do embed", default="🎭 Registro de Cargos", max_length=100)
        self.desc_input = discord.ui.TextInput(label="Descrição do embed", style=discord.TextStyle.long, default="Selecione abaixo as opções desejadas.", max_length=1000)
        self.placeholder_input = discord.ui.TextInput(label="Texto da Aba", default="Escolha seus cargos...", max_length=100)
        self.cargos_input = discord.ui.TextInput(
            label="Cargos (Emoji Nome=ID separados por ;)", 
            placeholder="✅ Vídeo novo=1455970332669116447; 🎨 Artes=1455970327820505373", 
            style=discord.TextStyle.long, max_length=1000
        )

        self.add_item(self.titulo_input)
        self.add_item(self.desc_input)
        self.add_item(self.placeholder_input)
        self.add_item(self.cargos_input)

    async def on_submit(self, interaction: discord.Interaction):
        roles_data = parse_roles_input(self.cargos_input.value)
        embed = build_panel_embed(self.titulo_input.value, self.desc_input.value)
        view = RolePanelView(roles_data, self.canal.guild, self.placeholder_input.value)

        try:
            await self.canal.send(embed=embed, view=view)
            await interaction.response.send_message(f"✅ Painel enviado em {self.canal.mention}", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Erro ao enviar. Verifique as permissões.", ephemeral=True)


# ─────────────────────────────────────────────────────────
# COG PRINCIPAL
# ─────────────────────────────────────────────────────────
class PainelCargos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── DROPDOWNS (SELECT MENUS) ─────────────────────────
    @commands.command(name="painelcargos")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def painelcargos_prefix(self, ctx: commands.Context, channel: discord.TextChannel, *, texto: str):
        """Uso: *painelcargos #canal Título | Descrição | Placeholder | ✅ Nome=ID; ❌ Nome=ID"""
        try:
            partes = [p.strip() for p in texto.split("|")]
            if len(partes) < 4:
                return await ctx.send("❌ Uso correto:\n`*painelcargos #canal Título | Descrição | Aba | Nome=ID;Nome2=ID2`")

            roles_data = parse_roles_input(partes[3].replace("\n", " "))
            embed = build_panel_embed(partes[0], partes[1])
            view = RolePanelView(roles_data, ctx.guild, partes[2])

            await channel.send(embed=embed, view=view)
            await ctx.send(f"✅ Painel enviado em {channel.mention}")
        except Exception:
            await ctx.send("❌ Falha ao criar o painel. Verifique a sintaxe.")

    @app_commands.command(name="config_painel", description="Cria um painel de cargos com embed e dropdown")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_painel(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await interaction.response.send_modal(PainelCargosModal(canal))

    # ── REACTION ROLES (EMBED + REAÇÕES) ─────────────────
    @commands.command(name="reactionroles")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def reactionroles_prefix(self, ctx: commands.Context, channel: discord.TextChannel, *, texto: str):
        """Uso: *reactionroles #canal Título | Descrição | 🍎=ID; 🍌=ID"""
        try:
            partes = [p.strip() for p in texto.split("|")]
            if len(partes) < 3:
                return await ctx.send("❌ Uso correto:\n`*reactionroles #canal Título | Descrição | 🍎=ID; 🍌=ID`")

            titulo, descricao_base = partes[0], partes[1]
            cargos_raw = partes[2].replace("\n", " ")
            
            roles_data = parse_roles_input(cargos_raw)
            
            # Constrói o texto mapeado que ficará visível no Embed
            linhas_cargos = ["\n\n**Cargos Disponíveis:**"]
            emojis_validos = []

            for data in roles_data:
                role = resolve_role(ctx.guild, data["id"])
                if role is None: continue
                
                # A chave aqui é extrair só o emoji. Ex de data["label"]: "✅ Vídeo novo" -> Pega o "✅"
                emoji = data["label"].split()[0] if data["label"] else "🔘"
                emojis_validos.append(emoji)
                
                # Formatamos de um jeito que o evento consiga ler depois!
                linhas_cargos.append(f"{emoji} ⸺ {role.mention}")

            descricao_final = descricao_base + "\n".join(linhas_cargos)
            embed = build_panel_embed(titulo, descricao_final)

            msg = await channel.send(embed=embed)
            
            # Adiciona as reações uma por uma
            for emj in emojis_validos:
                try: await msg.add_reaction(emj)
                except discord.HTTPException: pass

            await ctx.send(f"✅ Painel de Reações enviado em {channel.mention}")

        except Exception as e:
            await ctx.send(f"❌ Falha ao criar as Reaction Roles. Erro: {e}")

    # ── EVENTOS PARA PROCESSAR AS REAÇÕES ────────────────
    async def handle_reaction_role(self, payload: discord.RawReactionActionEvent, action: str):
        if payload.user_id == self.bot.user.id: return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild: return
        
        channel = guild.get_channel(payload.channel_id)
        if not channel: return
        
        try: message = await channel.fetch_message(payload.message_id)
        except: return

        # Checa se é uma mensagem do bot e possui Embed
        if message.author != self.bot.user or not message.embeds: return
        embed = message.embeds[0]
        
        if not embed.description or "⸺ <@&" not in embed.description: return

        emoji_str = payload.emoji.name
        alvo_id = None

        # Lê o Embed para achar qual cargo foi atribuído a este Emoji
        for linha in embed.description.split('\n'):
            if linha.strip().startswith(emoji_str) and "⸺ <@&" in linha:
                try:
                    # Isola o ID numérico da menção: "✅ ⸺ <@&12345>" -> "12345"
                    trecho = linha.split("⸺ <@&")[1]
                    alvo_id = int(trecho.split(">")[0])
                    break
                except: pass

        if alvo_id:
            role = guild.get_role(alvo_id)
            if not role: return
            
            member = guild.get_member(payload.user_id)
            if not member:
                # Caso a reaction venha sem cache de membro
                try: member = await guild.fetch_member(payload.user_id)
                except: return

            try:
                if action == "add" and role not in member.roles:
                    await member.add_roles(role, reason="Remnant — Reaction Role")
                elif action == "remove" and role in member.roles:
                    await member.remove_roles(role, reason="Remnant — Reaction Role")
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.handle_reaction_role(payload, action="add")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.handle_reaction_role(payload, action="remove")


async def setup(bot):
    await bot.add_cog(PainelCargos(bot))