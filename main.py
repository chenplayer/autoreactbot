import json
import os

import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_FILE = "config.json"


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


config = load_config()


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


@bot.tree.command(name="autoreact", description="Define o emoji que o bot usará para reagir neste canal")
@app_commands.describe(canal="Canal a configurar", emoji="Emoji que será usado nas reações")
@app_commands.checks.has_permissions(manage_guild=True)
async def autoreact(interaction: discord.Interaction, canal: discord.TextChannel, emoji: str):
    # Valida o emoji tentando interpretá-lo
    try:
        partial = discord.PartialEmoji.from_str(emoji.strip())
        # Testa de verdade: reage em uma mensagem não é possível aqui, então só checa formato
        if not partial.name:
            raise ValueError
    except Exception:
        await interaction.response.send_message("Emoji inválido.", ephemeral=True)
        return

    gid, cid = str(interaction.guild_id), str(canal.id)
    config.setdefault(gid, {})[cid] = emoji.strip()
    save_config(config)

    await interaction.response.send_message(
        f"Pronto! Vou reagir com {emoji} nas mensagens de {canal.mention}.", ephemeral=True
    )


@bot.tree.command(name="autoreact_remover", description="Remove a reação automática de um canal")
@app_commands.checks.has_permissions(manage_guild=True)
async def autoreact_remover(interaction: discord.Interaction, canal: discord.TextChannel):
    gid, cid = str(interaction.guild_id), str(canal.id)
    if cid in config.get(gid, {}):
        del config[gid][cid]
        if not config[gid]:
            del config[gid]
        save_config(config)
        await interaction.response.send_message(f"Reação removida de {canal.mention}.", ephemeral=True)
    else:
        await interaction.response.send_message("Esse canal não tem reação configurada.", ephemeral=True)


@autoreact.error
@autoreact_remover.error
async def on_cmd_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Você precisa da permissão **Gerenciar Servidor**.", ephemeral=True)
    else:
        raise error


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    emoji = config.get(str(message.guild.id), {}).get(str(message.channel.id))
    if not emoji:
        return

    try:
        await message.add_reaction(emoji)
    except discord.HTTPException:
        pass  # emoji inválido, removido ou sem permissão


@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")


bot.run(TOKEN)
