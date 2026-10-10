import json
import os
import tempfile

import discord
import emoji as emoji_lib
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_FILE = "config.json"


# ---------- JSON ----------
def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_config(data: dict) -> None:
    """Grava em um arquivo temporário e troca no final, para o JSON nunca ficar corrompido."""
    pasta = os.path.dirname(os.path.abspath(CONFIG_FILE))
    fd, tmp_path = tempfile.mkstemp(dir=pasta, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, CONFIG_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


config = load_config()


def get_emojis(gid: str, cid: str) -> list:
    atuais = config.get(gid, {}).get(cid, [])
    if isinstance(atuais, str):  # compatível com configs antigas (um emoji só)
        atuais = [atuais]
    return list(atuais)


# ---------- BOT ----------
intents = discord.Intents.default()
intents.message_content = True  # ative também no Developer Portal


class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = Bot()


# ---------- VALIDAÇÕES ----------
def validar_emoji(e: str) -> str | None:
    """Retorna None se o emoji é válido, ou a mensagem de erro."""
    partial = discord.PartialEmoji.from_str(e)

    if partial.id:  # emoji customizado
        if bot.get_emoji(partial.id) is None:
            return f"{e}: o bot não tem acesso a esse emoji (ele precisa estar em um servidor onde o bot está)."
        return None

    if not emoji_lib.is_emoji(e):  # emoji padrão
        return f"{e}: não é um emoji válido."
    return None


def checar_permissoes(canal: discord.TextChannel, lista: list) -> str:
    """Retorna um aviso se o bot não conseguir reagir no canal, ou string vazia se estiver tudo certo."""
    perms = canal.permissions_for(canal.guild.me)
    faltando = []

    if not perms.view_channel:
        faltando.append("Ver Canal")
    if not perms.read_message_history:
        faltando.append("Ler Histórico de Mensagens")
    if not perms.add_reactions:
        faltando.append("Adicionar Reações")

    for e in lista:
        partial = discord.PartialEmoji.from_str(e)
        if partial.id:
            obj = bot.get_emoji(partial.id)
            if obj and obj.guild_id != canal.guild.id and not perms.use_external_emojis:
                faltando.append("Usar Emojis Externos")
                break

    if not faltando:
        return ""
    return (
        f"⚠️ O bot está sem permissão em {canal.mention}: **{', '.join(faltando)}**. "
        "Enquanto isso não for liberado, as reações não vão funcionar."
    )


# ---------- COMANDOS ----------
@bot.tree.command(name="autoreact", description="Adiciona emojis às reações automáticas de um canal")
@app_commands.describe(canal="Canal a configurar", emoji="Um ou mais emojis separados por espaço")
@app_commands.checks.has_permissions(manage_guild=True)
async def autoreact(interaction: discord.Interaction, canal: discord.TextChannel, emoji: str):
    lista = emoji.split()
    if not lista:
        await interaction.response.send_message("Informe pelo menos um emoji.", ephemeral=True)
        return

    for e in lista:
        erro = validar_emoji(e)
        if erro:
            await interaction.response.send_message(erro, ephemeral=True)
            return

    gid, cid = str(interaction.guild_id), str(canal.id)

    atuais = get_emojis(gid, cid)
    for e in lista:
        if e not in atuais:  # evita emoji repetido
            atuais.append(e)

    config.setdefault(gid, {})[cid] = atuais
    save_config(config)

    msg = f"Pronto! {canal.mention} agora reage com: {' '.join(atuais)}"
    aviso = checar_permissoes(canal, atuais)
    if aviso:
        msg += f"\n\n{aviso}"

    await interaction.response.send_message(msg, ephemeral=True)


@bot.tree.command(name="autoreact_remover", description="Remove um emoji (ou todos) da reação automática de um canal")
@app_commands.describe(canal="Canal a configurar", emoji="Emoji a remover (deixe vazio para remover todos)")
@app_commands.checks.has_permissions(manage_guild=True)
async def autoreact_remover(interaction: discord.Interaction, canal: discord.TextChannel, emoji: str | None = None):
    gid, cid = str(interaction.guild_id), str(canal.id)

    atuais = get_emojis(gid, cid)
    if not atuais:
        await interaction.response.send_message("Esse canal não tem reação configurada.", ephemeral=True)
        return

    if emoji is None:
        atuais = []  # sem emoji informado: remove todos
    else:
        emoji = emoji.strip()
        if emoji not in atuais:
            await interaction.response.send_message(
                f"{emoji} não está na lista de {canal.mention}.", ephemeral=True
            )
            return
        atuais.remove(emoji)

    if atuais:
        config[gid][cid] = atuais
        msg = f"Removido! {canal.mention} agora reage com: {' '.join(atuais)}"
    else:
        del config[gid][cid]
        if not config[gid]:
            del config[gid]
        msg = f"Todas as reações de {canal.mention} foram removidas."

    save_config(config)
    await interaction.response.send_message(msg, ephemeral=True)


@autoreact_remover.autocomplete("emoji")
async def emoji_autocomplete(interaction: discord.Interaction, current: str):
    canal = getattr(interaction.namespace, "canal", None)
    if canal is None:
        return []  # o canal precisa ser escolhido antes

    atuais = get_emojis(str(interaction.guild_id), str(canal.id))

    choices = []
    for e in atuais:
        partial = discord.PartialEmoji.from_str(e)
        nome = f":{partial.name}:" if partial.id else e  # emoji customizado aparece pelo nome
        if current.lower() in nome.lower() or current in e:
            choices.append(app_commands.Choice(name=nome, value=e))

    return choices[:25]  # limite do Discord


@bot.tree.command(name="autoreact_listar", description="Mostra os emojis configurados (de um canal ou do servidor todo)")
@app_commands.describe(canal="Canal específico (deixe vazio para ver todos)")
@app_commands.checks.has_permissions(manage_guild=True)
async def autoreact_listar(interaction: discord.Interaction, canal: discord.TextChannel | None = None):
    gid = str(interaction.guild_id)

    if canal:
        emojis = get_emojis(gid, str(canal.id))
        if not emojis:
            await interaction.response.send_message(
                f"{canal.mention} não tem reação configurada.", ephemeral=True
            )
            return
        await interaction.response.send_message(f"{canal.mention}: {' '.join(emojis)}", ephemeral=True)
        return

    canais = config.get(gid, {})
    if not canais:
        await interaction.response.send_message("Nenhum canal configurado neste servidor.", ephemeral=True)
        return

    texto = "\n".join(f"<#{cid}>: {' '.join(get_emojis(gid, cid))}" for cid in canais)
    if len(texto) > 1900:  # limite de 2000 caracteres por mensagem
        texto = texto[:1900] + "\n..."

    await interaction.response.send_message(f"**Reações automáticas:**\n{texto}", ephemeral=True)


@autoreact.error
@autoreact_remover.error
@autoreact_listar.error
async def on_cmd_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Você precisa da permissão **Gerenciar Servidor**.", ephemeral=True)
    else:
        raise error


# ---------- EVENTOS ----------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    emojis = get_emojis(str(message.guild.id), str(message.channel.id))
    if not emojis:
        return

    for emoji in emojis:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            pass  # emoji inválido, removido ou sem permissão


@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
    gid, cid = str(channel.guild.id), str(channel.id)
    if cid in config.get(gid, {}):
        del config[gid][cid]
        if not config[gid]:
            del config[gid]
        save_config(config)


@bot.event
async def on_guild_remove(guild: discord.Guild):
    gid = str(guild.id)
    if gid in config:
        del config[gid]
        save_config(config)


@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")


bot.run(TOKEN)
