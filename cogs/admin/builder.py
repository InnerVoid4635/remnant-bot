"""
builder.py — Sistema de Builder/Templates para o Remnant Bot
Cog para criação automática de estrutura de servidores Discord.

Estrutura de arquivos esperada:
    cogs/
        builder.py
    templates/
        guilda.json
        minecraft.json
        streamer.json

Comandos:
    *copy                    — Lista os templates disponíveis (fallback)
    *copy list               — Lista os templates disponíveis
    *copy server <nome>      — Exporta o servidor atual como template JSON
    *copy roles <tipo>       — Cria apenas os cargos do template
    *copy channels <tipo>    — Cria apenas os canais do template

    *create server <tipo>    — Limpa e reconstrói o servidor completo
"""

import json
import asyncio
import re
from pathlib import Path

import discord
from discord.ext import commands
from discord import app_commands
from verbose import log_event, log_error, log_system, log_command

# ══════════════════════════════════════════════════════
# CARREGAMENTO DOS TEMPLATES
# ══════════════════════════════════════════════════════
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

def _carregar_templates() -> dict:
    templates = {}
    if not _TEMPLATES_DIR.exists():
        log_error("builder.carregar_templates", f"Pasta não encontrada: {_TEMPLATES_DIR}")
        return templates

    for path in sorted(_TEMPLATES_DIR.glob("*.json")):
        key = path.stem
        try:
            with path.open(encoding="utf-8") as f:
                templates[key] = json.load(f)
            log_system(f"Template carregado: '{key}' ({path.name})")
        except json.JSONDecodeError as e:
            log_error(f"builder.carregar_templates.{key}", f"JSON inválido — {e}")
        except Exception as e:
            log_error(f"builder.carregar_templates.{key}", e)

    return templates

TEMPLATES: dict = _carregar_templates()


# ══════════════════════════════════════════════════════
# PERMISSÕES
# ══════════════════════════════════════════════════════
def get_permissions(nivel: str) -> discord.Permissions:
    base = {
        "admin": discord.Permissions(administrator=True),
        "mod": discord.Permissions(
            kick_members=True, ban_members=True, manage_messages=True,
            manage_channels=True, mute_members=True, deafen_members=True,
            move_members=True, view_channel=True, send_messages=True,
            read_message_history=True
        ),
        "vip": discord.Permissions(
            view_channel=True, send_messages=True, read_message_history=True,
            attach_files=True, embed_links=True, add_reactions=True,
            use_external_emojis=True, connect=True, speak=True
        ),
        "membro": discord.Permissions(
            view_channel=True, send_messages=True, read_message_history=True,
            attach_files=True, embed_links=True, add_reactions=True,
            connect=True, speak=True
        ),
        "recruta": discord.Permissions(
            view_channel=True, send_messages=True, read_message_history=True, connect=True
        ),
    }
    result = base.get(nivel)
    if result is None:
        log_error("get_permissions", f"Nível desconhecido: '{nivel}' — retornando none()")
        return discord.Permissions.none()
    return result


# ══════════════════════════════════════════════════════
# COG
# ══════════════════════════════════════════════════════
class Builder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── Autocomplete ──────────────────────────────────

    async def template_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=t["nome"], value=key)
            for key, t in TEMPLATES.items()
            if current.lower() in key.lower() or current.lower() in t["nome"].lower()
        ]

    # ── Helpers internos ──────────────────────────────

    async def _verificar_permissoes(self, guild: discord.Guild | None) -> bool:
        """Verifica se o bot tem permissão de administrador no servidor."""
        if guild is None:
            return False
        if not guild.me.guild_permissions.administrator:
            log_error("builder.verificar_permissoes", "Bot sem permissão de administrador.")
            return False
        return True

    def _resolver_staff_roles(
        self,
        roles: dict[str, discord.Role],
        keywords: list[str]
    ) -> list[discord.Role]:
        """Retorna TODOS os cargos cujo nome contenha alguma das keywords."""
        return [
            role_obj
            for nome_role, role_obj in roles.items()
            if any(k in nome_role.lower() for k in keywords)
        ]

    async def _limpar_servidor(self, guild: discord.Guild):
        """Remove todos os canais e cargos não vitais."""
        for channel in list(guild.channels):
            try:
                await channel.delete(reason="Remnant Builder — Limpeza")
                await asyncio.sleep(0.2)
            except Exception as e:
                log_error(f"builder.limpar.canal.{channel.name}", e)

        bot_role = guild.me.top_role
        for role in list(guild.roles):
            if not role.is_default() and role < bot_role and not role.managed:
                try:
                    await role.delete(reason="Remnant Builder — Limpeza")
                    await asyncio.sleep(0.2)
                except Exception as e:
                    log_error(f"builder.limpar.cargo.{role.name}", e)

    async def _criar_cargos(
        self,
        guild: discord.Guild,
        template: dict
    ) -> dict[str, discord.Role]:
        """Cria os cargos do template e retorna um dict nome → Role."""
        roles_criados = {}
        for cargo in template["cargos"]:  # removed reversed()
            try:
                role = await guild.create_role(
                    name=cargo["nome"],
                    color=discord.Color(cargo["cor"]),
                    hoist=cargo["hoist"],
                    permissions=get_permissions(cargo["perms"]),
                    reason="Remnant Builder — Setup"
                )
                roles_criados[cargo["nome"]] = role
                await asyncio.sleep(0.4)
            except Exception as e:
                log_error(f"builder.criar_cargos.{cargo['nome']}", e)
        return roles_criados

    async def _criar_canais(
        self,
        guild: discord.Guild,
        template: dict,
        roles: dict[str, discord.Role],
        status_callback=None
    ):
        """
        Cria categorias e canais do template.
        status_callback: coroutine  async def(texto: str)  para atualizar progresso.
        """
        everyone = guild.default_role
        total_cats = len(template["categorias"])

        for idx, categoria_data in enumerate(template["categorias"], start=1):
            if status_callback:
                await status_callback(
                    f"⚙️ Criando categoria {idx}/{total_cats}: **{categoria_data['nome']}**..."
                )
            try:
                categoria = await guild.create_category(
                    name=categoria_data["nome"],
                    reason="Remnant Builder — Setup"
                )
                await asyncio.sleep(0.4)

                for canal_data in categoria_data["canais"]:
                    overwrites: dict[discord.Role | discord.Member | discord.Object, discord.PermissionOverwrite] = {
                        everyone: discord.PermissionOverwrite(view_channel=True)
                    }

                    if canal_data.get("somente_leitura"):
                        overwrites[everyone] = discord.PermissionOverwrite(
                            view_channel=True, send_messages=False
                        )

                    # Canal exclusivo para um cargo específico (ex: Subs)
                    if canal_data.get("cargo_exclusivo"):
                        nome_exclusivo = canal_data["cargo_exclusivo"]
                        role_exclusivo = roles.get(nome_exclusivo)
                        if role_exclusivo:
                            overwrites[everyone] = discord.PermissionOverwrite(view_channel=False)
                            overwrites[role_exclusivo] = discord.PermissionOverwrite(
                                view_channel=True, send_messages=True, connect=True, speak=True
                            )
                        else:
                            log_error(
                                "builder.criar_canais",
                                f"cargo_exclusivo '{nome_exclusivo}' não encontrado para "
                                f"'{canal_data['nome']}' — canal bloqueado para todos."
                            )
                            overwrites[everyone] = discord.PermissionOverwrite(view_channel=False)

                    # Canal restrito a múltiplos cargos de staff
                    elif canal_data.get("staff_only"):
                        keywords = canal_data.get("staff_roles", [])
                        staff_roles_encontrados = self._resolver_staff_roles(roles, keywords)

                        if staff_roles_encontrados:
                            overwrites[everyone] = discord.PermissionOverwrite(view_channel=False)
                            for sr in staff_roles_encontrados:
                                overwrites[sr] = discord.PermissionOverwrite(
                                    view_channel=True, send_messages=True, connect=True, speak=True
                                )
                        else:
                            log_error(
                                "builder.criar_canais",
                                f"Canal staff_only '{canal_data['nome']}' sem roles para "
                                f"keywords {keywords} — canal bloqueado para todos."
                            )
                            overwrites[everyone] = discord.PermissionOverwrite(view_channel=False)

                    if canal_data["tipo"] == "voice":
                        await categoria.create_voice_channel(
                            name=canal_data["nome"],
                            overwrites=overwrites,
                            reason="Remnant Builder — Setup"
                        )
                    else:
                        await categoria.create_text_channel(
                            name=canal_data["nome"],
                            overwrites=overwrites,
                            reason="Remnant Builder — Setup"
                        )
                    await asyncio.sleep(0.3)

            except Exception as e:
                log_error("builder.criar_categoria", e)

    def _exportar_servidor(self, guild: discord.Guild) -> dict:
        """
        Lê a estrutura atual do servidor e gera um dict no formato de template.

        Detecção de permissões:
        - somente_leitura: @everyone pode ver mas não enviar mensagens
        - staff_only: @everyone não pode ver, outros cargos sim
        - cargo_exclusivo: apenas UM cargo não-padrão pode ver (ex: Subs)
        """
        everyone = guild.default_role

        # ── Cargos ──────────────────────────────────
        cargos = []
        for role in guild.roles:
            if role.is_default() or role.managed:
                continue
            cargos.append({
                "nome": role.name,
                "cor": role.color.value,
                "hoist": role.hoist,
                "perms": "recruta"  # conservador — ajuste manual se necessário
            })

        # ── Categorias e canais ──────────────────────
        categorias = []

        # Canais sem categoria
        sem_cat = [
            c for c in guild.channels
            if c.category is None and not isinstance(c, discord.CategoryChannel)
        ]
        if sem_cat:
            canais_sem_cat = []
            for ch in sorted(sem_cat, key=lambda c: c.position):
                canais_sem_cat.append(self._exportar_canal(ch, everyone))
            categorias.append({"nome": "Sem Categoria", "canais": canais_sem_cat})

        # Canais dentro de categorias
        for categoria in sorted(guild.categories, key=lambda c: c.position):
            canais = []
            for ch in sorted(categoria.channels, key=lambda c: c.position):
                canais.append(self._exportar_canal(ch, everyone))
            categorias.append({"nome": categoria.name, "canais": canais})

        return {
            "nome": guild.name,
            "padrao": False,
            "cargos": cargos,
            "categorias": categorias
        }

    def _exportar_canal(
        self,
        channel: discord.abc.GuildChannel,
        everyone: discord.Role
    ) -> dict:
        """Exporta um canal para o formato de template, detectando permissões."""
        tipo = "voice" if isinstance(channel, discord.VoiceChannel) else "text"
        canal: dict = {"nome": channel.name, "tipo": tipo}

        ow = channel.overwrites

        # Sem overwrites customizados — canal público normal
        if not ow or list(ow.keys()) == [everyone]:
            everyone_ow = ow.get(everyone)
            if everyone_ow and everyone_ow.send_messages is False:
                canal["somente_leitura"] = True
            return canal

        everyone_ow = ow.get(everyone)
        everyone_can_view = (
            everyone_ow is None
            or everyone_ow.view_channel is None
            or everyone_ow.view_channel is True
        )

        if everyone_ow and everyone_ow.view_channel is False:
            # Canal oculto para @everyone — staff_only ou cargo_exclusivo
            roles_com_acesso = [
                target for target, perms in ow.items()
                if isinstance(target, discord.Role)
                and not target.is_default()
                and perms.view_channel is True
            ]

            if len(roles_com_acesso) == 1:
                # Apenas um cargo tem acesso — cargo_exclusivo
                canal["cargo_exclusivo"] = roles_com_acesso[0].name
            elif len(roles_com_acesso) > 1:
                # Múltiplos cargos — staff_only com keywords extraídas dos nomes
                canal["staff_only"] = True
                canal["staff_roles"] = [
                    # Pega a primeira palavra sem emoji como keyword
                    re.sub(r"[^\w\s]", "", r.name).strip().lower().split()[0]
                    if re.sub(r"[^\w\s]", "", r.name).strip()
                    else r.name.lower()
                    for r in roles_com_acesso
                ]
            else:
                # Bloqueado para todos sem exceção
                canal["staff_only"] = True
                canal["staff_roles"] = []

        elif everyone_can_view and everyone_ow and everyone_ow.send_messages is False:
            canal["somente_leitura"] = True

        return canal

    # ══════════════════════════════════════════════════
    # GRUPO: copy
    # ══════════════════════════════════════════════════

    @commands.hybrid_group(name="copy", fallback="list")
    @commands.is_owner()
    async def copy(self, ctx: commands.Context):
        """Lista os templates disponíveis (use 'copy list' ou apenas 'copy')."""
        log_command(ctx.author, "copy list", ctx.guild, ctx.channel)
        embed = discord.Embed(title="📋 Templates Disponíveis", color=0x3498DB)
        for key, t in TEMPLATES.items():
            num_canais = sum(len(c["canais"]) for c in t["categorias"])
            embed.add_field(
                name=f"`{key}`",
                value=f"**{t['nome']}**\n{len(t['cargos'])} cargos · {num_canais} canais",
                inline=True
            )
        await ctx.send(embed=embed)

    @copy.command(name="server")
    @commands.is_owner()
    async def copy_server(self, ctx: commands.Context, nome: str):
        """
        Exporta a estrutura do servidor atual como um template JSON.
        O arquivo será salvo como <nome>.json na pasta templates/.
        Uso: *copy server meu_servidor
        """
        log_command(ctx.author, f"copy server {nome}", ctx.guild, ctx.channel)

        if not ctx.guild:
            return await ctx.send("❌ Este comando só pode ser usado em servidores.")

        # Sanitiza o nome para uso como nome de arquivo
        nome_arquivo = re.sub(r"[^\w\-]", "_", nome.strip().lower())
        if not nome_arquivo:
            return await ctx.send("❌ Nome inválido para o template.")

        destino = _TEMPLATES_DIR / f"{nome_arquivo}.json"
        if destino.exists():
            return await ctx.send(
                f"⚠️ Já existe um template com o nome `{nome_arquivo}`. "
                "Escolha outro nome ou delete o arquivo existente."
            )

        msg = await ctx.send(f"⏳ Exportando estrutura de **{ctx.guild.name}**...")

        try:
            template = self._exportar_servidor(ctx.guild)

            _TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
            with destino.open("w", encoding="utf-8") as f:
                json.dump(template, f, ensure_ascii=False, indent=2)

            # Registra no dict em memória para uso imediato sem reiniciar
            TEMPLATES[nome_arquivo] = template

            num_cargos = len(template["cargos"])
            num_canais = sum(len(c["canais"]) for c in template["categorias"])

            log_event("BUILDER", f"copy server '{nome_arquivo}' exportado por {ctx.author}")
            await msg.edit(
                content=(
                    f"✅ Template `{nome_arquivo}` exportado com sucesso!\n"
                    f"**{num_cargos}** cargos · **{num_canais}** canais · "
                    f"**{len(template['categorias'])}** categorias\n\n"
                    f"Use `create server {nome_arquivo}` para aplicar em qualquer servidor."
                )
            )
        except Exception as e:
            log_error("builder.copy_server", e)
            await msg.edit(content=f"❌ Erro ao exportar: `{e}`")

    @copy.command(name="roles")
    @commands.is_owner()
    @app_commands.autocomplete(tipo=template_autocomplete)
    async def copy_roles(self, ctx: commands.Context, tipo: str):
        """Cria apenas os cargos de um template no servidor atual."""
        log_command(ctx.author, f"copy roles {tipo}", ctx.guild, ctx.channel)

        if not ctx.guild:
            return await ctx.send("❌ Este comando só pode ser usado em servidores.")
        if tipo not in TEMPLATES:
            return await ctx.send("❌ Template inválido. Use `copy list` para ver as opções.")
        if not await self._verificar_permissoes(ctx.guild):
            return await ctx.send("❌ O bot precisa de permissão de **Administrador**.")

        msg = await ctx.send(f"⏳ Criando cargos do template `{tipo}`...")
        roles = await self._criar_cargos(ctx.guild, TEMPLATES[tipo])
        await msg.edit(content=f"✅ {len(roles)} cargos criados com sucesso!")

    @copy.command(name="channels")
    @commands.is_owner()
    @app_commands.autocomplete(tipo=template_autocomplete)
    async def copy_channels(self, ctx: commands.Context, tipo: str):
        """Cria apenas os canais de um template no servidor atual."""
        log_command(ctx.author, f"copy channels {tipo}", ctx.guild, ctx.channel)

        if not ctx.guild:
            return await ctx.send("❌ Este comando só pode ser usado em servidores.")
        if tipo not in TEMPLATES:
            return await ctx.send("❌ Template inválido. Use `copy list` para ver as opções.")
        if not await self._verificar_permissoes(ctx.guild):
            return await ctx.send("❌ O bot precisa de permissão de **Administrador**.")

        msg = await ctx.send(f"⏳ Criando canais do template `{tipo}`...")

        async def atualizar_status(texto: str):
            try:
                await msg.edit(content=texto)
            except discord.NotFound:
                pass

        roles_atuais = {r.name: r for r in ctx.guild.roles}
        await self._criar_canais(ctx.guild, TEMPLATES[tipo], roles_atuais, status_callback=atualizar_status)
        await msg.edit(content=f"✅ Canais do template `{tipo}` criados com sucesso!")

    # ══════════════════════════════════════════════════
    # GRUPO: create
    # ══════════════════════════════════════════════════

    @commands.hybrid_group(name="create")
    @commands.is_owner()
    async def create(self, ctx: commands.Context):
        """Comandos de reconstrução completa do servidor."""
        await ctx.send(
            "❓ Use `create server <tipo>` para reconstruir o servidor do zero.\n"
            "Use `copy list` para ver os templates disponíveis."
        )

    @create.command(name="server")
    @commands.is_owner()
    @app_commands.autocomplete(tipo=template_autocomplete)
    async def create_server(self, ctx: commands.Context, tipo: str):
        """Limpa o servidor inteiro e aplica um template completo do zero."""
        log_command(ctx.author, f"create server {tipo}", ctx.guild, ctx.channel)

        if not ctx.guild:
            return await ctx.send("❌ Este comando só pode ser usado em servidores.")
        if tipo not in TEMPLATES:
            return await ctx.send("❌ Template inválido. Use `copy list` para ver as opções.")
        if not await self._verificar_permissoes(ctx.guild):
            return await ctx.send("❌ O bot precisa de permissão de **Administrador**.")

        template = TEMPLATES[tipo]
        autor = ctx.author
        guild = ctx.guild

        confirm_msg = await ctx.send(
            f"⚠️ **PERIGO:** Isso apagará **TODOS** os canais e cargos e aplicará o template `{tipo}`.\n"
            "Reaja com ✅ em 30 segundos para confirmar."
        )
        await confirm_msg.add_reaction("✅")

        def check(r, u):
            return (
                u == autor
                and str(r.emoji) == "✅"
                and r.message.id == confirm_msg.id
            )

        try:
            await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await confirm_msg.edit(content="❌ Operação cancelada por timeout.")

        try:
            await confirm_msg.edit(content="⏳ Limpando servidor...")
        except discord.NotFound:
            pass

        await self._limpar_servidor(guild)

        canal_obra = await guild.create_text_channel(
            "🏗️・canteiro-de-obras",
            reason="Remnant Builder — Canal temporário de progresso"
        )
        msg_progresso = await canal_obra.send(
            f"🏗️ **Canteiro de obras aberto!** Aplicando template `{tipo}`..."
        )

        async def atualizar_status(texto: str):
            try:
                await msg_progresso.edit(content=texto)
            except discord.NotFound:
                pass

        await atualizar_status("⚙️ Criando cargos...")
        roles = await self._criar_cargos(guild, template)

        await atualizar_status(f"⚙️ {len(roles)} cargos criados. Criando canais...")
        await self._criar_canais(guild, template, roles, status_callback=atualizar_status)

        log_event("BUILDER", f"create server '{tipo}' finalizado por {autor}")
        await atualizar_status(
            f"✅ **{template['nome']} pronto!**\n\n"
            "Próximos passos:\n"
            "• Mova o cargo do bot para o topo da lista de cargos\n"
            "• Delete este canal quando quiser"
        )


# ══════════════════════════════════════════════════════
async def setup(bot):
    await bot.add_cog(Builder(bot))