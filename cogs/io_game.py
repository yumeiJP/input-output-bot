"""Function‑guessing game cog."""

from discord.ext import commands


class IOGame(commands.Cog):
    """Handles the I/O function-guessing game"""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot
        self.games = {}


class Game:
    """Full game session"""

    def __init__(self, channel, initiator_user_id, max_queries_per_round):
        self.channel = channel
        self.initiator_user_id = initiator_user_id
        self.max_queries_per_round = max_queries_per_round
        self.players = {}


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


async def setup(bot):
    """Add the IOGame cog to the bot."""
    await bot.add_cog(IOGame(bot))
