import discord
from discord.ext import commands
import yaml
import asyncio

# Load bot token
with open("token.yml") as f:
    config = yaml.safe_load(f)
TOKEN = config["token"]

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='-', intents=intents)

async def load_extensions():
    """Load all cogs from the cogs folder."""
    await bot.load_extension("cogs.io_game")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())