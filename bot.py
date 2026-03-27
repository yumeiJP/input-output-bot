"""Main bot module."""

import asyncio

import discord
import yaml
from discord.ext import commands

# Load bot token
with open("token.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
TOKEN = config["token"]

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="-", intents=intents)


async def load_extensions():
    """Load all cogs."""
    await bot.load_extension("cogs.io_game")


async def main():
    """Main entry point."""
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
