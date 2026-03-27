"""Function‑guessing game cog."""

from discord.ext import commands


class IOGame(commands.Cog):
    """Handles the I/O function-guessing game"""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot
        self.games = {}


async def setup(bot):
    """Add the IOGame cog to the bot."""
    await bot.add_cog(IOGame(bot))
