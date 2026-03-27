import discord
from discord.ext import commands

class IOGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

async def setup(bot):
    await bot.add_cog(IOGame(bot))