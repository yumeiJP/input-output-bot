"""Function‑guessing game cog."""

import asyncio
from datetime import datetime

from discord.ext import commands


class Game:
    """Full game session"""

    def __init__(self, channel, initiator_user_id, max_queries_per_round):
        self.channel = channel
        self.initiator_user_id = initiator_user_id
        self.max_queries_per_round = max_queries_per_round
        self.players = {}
        self.join_order = []
        self.recruitment_task = None
        self.recruitment_start = None
        self.participant_list = []
        self.rounds = []
        self.current_round_index = -1


class Round:
    """Single round within the game"""

    def __init__(self, creator_user_id, max_queries):
        self.creator_id = creator_user_id
        self.max_queries = max_queries
        self.penalty = 1000.0 / max_queries
        self.secret_expr = None
        self.players = {}
        self.active = False


class PlayerRoundState:
    """Player's state during a round"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.potential_points = 1000
        self.solved = False


class IOGame(commands.Cog):
    """Handles the I/O function-guessing game"""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot
        self.games = {}

    @commands.command()
    async def create(self, ctx, max_queries):
        """Starts a new game (Recuritment phase)"""
        if ctx.channel.id in self.games:
            await ctx.send("There is already a game starting!")
            return

        if not (max_queries >= 1 and isinstance(max_queries, int)):
            await ctx.send("Please send how many max queries you want!")
            return

        game = Game(ctx.channel, ctx.author.id, max_queries)
        self.games[ctx.channel.id] = game

        async def recruitment_timeout():
            await asyncio.sleep(30)
            await self.end_recruitment(game)

        game.recruitment_task = asyncio.create_task(recruitment_timeout())
        game.recruitment_start = datetime.utcnow()

        await ctx.send("Game created! Use -join to join!")


async def setup(bot):
    """Add the IOGame cog to the bot."""
    await bot.add_cog(IOGame(bot))
