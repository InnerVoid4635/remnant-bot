"""
bcf.py — Cog da Cifra BCF V4.0 para o Remnant Bot

Comandos:
    *bcf cifrar <chave> <texto>    — Cifra um texto com a chave informada
    *bcf decifrar <chave> <codigo> — Decifra um código com a chave informada

Chaves válidas: 3 a 12
Separadores aceitos: hífen (1-2-3), espaço (1 2 3) ou nenhum (123)
"""

import discord
from discord.ext import commands
from discord import app_commands
from verbose import log_command, log_error

# ══════════════════════════════════════════════════════
# MOTOR DA CIFRA BCF V4.0
# ══════════════════════════════════════════════════════

CHAVE_MIN = 3
CHAVE_MAX = 12

HELP_CIFRAR = discord.Embed(
    title="🔒 BCF — Cifrar",
    description="Cifra um texto usando a Cifra BCF V4.0.",
    color=0xE74C3C
).add_field(
    name="📌 Uso",
    value="`*bcf cifrar <chave> <texto>`",
    inline=False
).add_field(
    name="✅ Exemplo",
    value="`*bcf cifrar 5 ola mundo`",
    inline=False
).set_footer(text=f"Chaves válidas: {CHAVE_MIN} a {CHAVE_MAX}")

HELP_DECIFRAR = discord.Embed(
    title="🔓 BCF — Decifrar",
    description="Decifra um código usando a Cifra BCF V4.0.",
    color=0x2ECC71
).add_field(
    name="📌 Uso",
    value="`*bcf decifrar <chave> <codigo>`",
    inline=False
).add_field(
    name="✅ Exemplos",
    value="`*bcf decifrar 5 20-19-6`\n`*bcf decifrar 5 20 19 6`\n`*bcf decifrar 5 20196`",
    inline=False
).add_field(
    name="Separadores aceitos",
    value="`1-2-3` · `1 2 3` · `123`",
    inline=False
).set_footer(text=f"Chaves válidas: {CHAVE_MIN} a {CHAVE_MAX}")


def validar_chave(chave: int) -> bool:
    return CHAVE_MIN <= chave <= CHAVE_MAX


def mapear_letra(letra: str) -> int:
    return ord(letra.upper()) - ord('A') + 1


def mapear_numero(numero: int) -> str:
    numero = (numero - 1) % 26 + 1
    return chr(numero + ord('A') - 1)


def aplicar_modular(valor: int) -> int:
    return (valor - 1) % 26 + 1


def _modo_subtracao(i: int, tamanho: int) -> bool:
    ponto_flip = tamanho // 2
    modo_sub = i >= ponto_flip
    if tamanho % 2 != 0 and i == tamanho - 1:
        modo_sub = not modo_sub
    return modo_sub


def cifrar_palavra(palavra: str, chave: int) -> str:
    palavra = palavra.upper()
    tamanho = len(palavra)
    if tamanho == 0:
        return ""
    numeros = []
    for i, letra in enumerate(palavra):
        val = mapear_letra(letra)
        if _modo_subtracao(i, tamanho):
            resultado = aplicar_modular(val - chave)
        else:
            resultado = aplicar_modular(val + chave)
        numeros.append(str(resultado))
    return "-".join(numeros)


def _extrair_numeros(codigo: str) -> list[int]:
    codigo = codigo.replace("/", "").strip()

    if "-" in codigo:
        tokens = codigo.split("-")
        return [int(t.strip()) for t in tokens if t.strip().isdigit()]

    if " " in codigo:
        tokens = codigo.split()
        return [int(t) for t in tokens if t.isdigit()]

    # Sem separador: grupos de 2 dígitos (01-26)
    numeros = []
    i = 0
    while i < len(codigo):
        if i + 1 < len(codigo) and codigo[i:i+2].isdigit():
            val = int(codigo[i:i+2])
            if 1 <= val <= 26:
                numeros.append(val)
                i += 2
                continue
        if codigo[i].isdigit():
            numeros.append(int(codigo[i]))
            i += 1
        else:
            i += 1
    return numeros


def decifrar_palavra(codigo: str, chave: int) -> str:
    numeros = _extrair_numeros(codigo)
    tamanho = len(numeros)
    if tamanho == 0:
        return ""
    letras = []
    for i, val in enumerate(numeros):
        if _modo_subtracao(i, tamanho):
            original = aplicar_modular(val + chave)
        else:
            original = aplicar_modular(val - chave)
        letras.append(mapear_numero(original))
    return "".join(letras)


def cifrar_frase(frase: str, chave: int) -> str:
    palavras = frase.upper().split()
    return " // ".join(cifrar_palavra(p, chave) for p in palavras)


def decifrar_frase(criptograma: str, chave: int) -> str:
    partes = criptograma.split("//")
    return " ".join(decifrar_palavra(p.strip(), chave) for p in partes)


# ══════════════════════════════════════════════════════
# COG
# ══════════════════════════════════════════════════════

class BCF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _apagar_mensagem(self, ctx: commands.Context):
        """Apaga a mensagem de prefixo silenciosamente."""
        if not ctx.interaction:  # só apaga se for prefixo
            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass  # sem permissão ou já apagada

    # ── GRUPO BASE ────────────────────────────────────
    @commands.hybrid_group(name="bcf", invoke_without_command=True)
    async def cifra(self, ctx: commands.Context):
        """Grupo de comandos da Cifra BCF V4.0."""
        embed = discord.Embed(
            title="🔐 Cifra BCF V4.0",
            description="Motor de cifragem por blocos com Flip Central.",
            color=0x2ECC71
        )
        embed.add_field(name="Cifrar",   value="`*bcf cifrar <chave> <texto>`",   inline=False)
        embed.add_field(name="Decifrar", value="`*bcf decifrar <chave> <codigo>`", inline=False)
        embed.add_field(name="Separadores aceitos", value="`1-2-3` · `1 2 3` · `123`", inline=False)
        embed.set_footer(text=f"Chaves válidas: {CHAVE_MIN} a {CHAVE_MAX}")
        await ctx.send(embed=embed)

    # ── CIFRAR ────────────────────────────────────────
    @cifra.command(name="cifrar")
    @app_commands.describe(
        chave=f"Chave de cifragem ({CHAVE_MIN}-{CHAVE_MAX})",
        texto="Texto a ser cifrado (sem acentos)"
    )
    async def cifrar(self, ctx: commands.Context, chave: int = None, *, texto: str = None):  # type: ignore
        """Cifra um texto usando a Cifra BCF V4.0."""

        # Mostra help se faltar argumento
        if chave is None or texto is None:
            await self._apagar_mensagem(ctx)
            return await ctx.send(embed=HELP_CIFRAR, ephemeral=bool(ctx.interaction))

        if not validar_chave(chave):
            await self._apagar_mensagem(ctx)
            return await ctx.send(
                f"❌ Chave inválida. Use um número entre **{CHAVE_MIN}** e **{CHAVE_MAX}**.",
                ephemeral=True, delete_after=8
            )

        await self._apagar_mensagem(ctx)
        log_command(str(ctx.author), f"bcf cifrar [chave={chave}]", str(ctx.guild), str(ctx.channel))

        try:
            resultado = cifrar_frase(texto, chave)
            embed = discord.Embed(title="🔒 Cifra BCF V4.0", color=0xE74C3C)
            embed.add_field(name="🔐 Criptograma", value=f"```\n{resultado}\n```", inline=False)
            embed.set_footer(text=f"Cifra BCF V4.0 · Chave: {chave}")
            await ctx.send(embed=embed)
        except Exception as e:
            log_error("bcf.cifrar", e)
            await ctx.send("❌ Erro ao cifrar o texto.", ephemeral=True)

    # ── DECIFRAR ──────────────────────────────────────
    @cifra.command(name="decifrar")
    @app_commands.describe(
        chave=f"Chave de decifragem ({CHAVE_MIN}-{CHAVE_MAX})",
        codigo="Código cifrado (aceita hífen, espaço ou sem separador)"
    )
    async def decifrar(self, ctx: commands.Context, chave: int = None, *, codigo: str = None):  # type: ignore
        """Decifra um código usando a Cifra BCF V4.0."""

        # Mostra help se faltar argumento
        if chave is None or codigo is None:
            await self._apagar_mensagem(ctx)
            return await ctx.send(embed=HELP_DECIFRAR, ephemeral=bool(ctx.interaction))

        if not validar_chave(chave):
            await self._apagar_mensagem(ctx)
            return await ctx.send(
                f"❌ Chave inválida. Use um número entre **{CHAVE_MIN}** e **{CHAVE_MAX}**.",
                ephemeral=True, delete_after=8
            )

        await self._apagar_mensagem(ctx)
        log_command(str(ctx.author), f"bcf decifrar [chave={chave}]", str(ctx.guild), str(ctx.channel))

        try:
            resultado = decifrar_frase(codigo, chave)
            embed = discord.Embed(title="🔓 Cifra BCF V4.0", color=0x2ECC71)
            embed.add_field(name="📝 Texto Revelado", value=f"```\n{resultado}\n```", inline=False)
            embed.set_footer(text=f"Cifra BCF V4.0 · Chave: {chave}")
            await ctx.send(embed=embed)
        except Exception as e:
            log_error("bcf.decifrar", e)
            await ctx.send("❌ Erro ao decifrar o código.", ephemeral=True)

    # ── HANDLER DE ERROS ──────────────────────────────
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await self._apagar_mensagem(ctx)
            await ctx.send("⚠️ Chave inválida — use um número inteiro.", delete_after=8)
        else:
            log_error("bcf.cog_command_error", error)


# ══════════════════════════════════════════════════════
async def setup(bot):
    await bot.add_cog(BCF(bot))