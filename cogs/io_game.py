"""Function‑guessing game cog."""

import asyncio
from datetime import datetime

from discord.ext import commands


class Game:  # pylint: disable=too-many-instance-attributes
    """Full game session"""

    def __init__(self, channel, initiator_user_id, max_queries_per_round):
        self.channel = channel
        self.initiator_user_id = initiator_user_id
        self.max_queries_per_round = max_queries_per_round
        self.players_score = {}
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
        self.potential_points = 1000.0
        self.solved = False


class IOGame(commands.Cog):
    """Handles the I/O function-guessing game"""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot
        self.games = {}

    async def start_round(self, game):
        # will implement
        pass

    async def end_recruitment(self, game):
        """Called after recruitment ends"""

        if game.recruitment_task:
            game.recruitment_task.cancel()

        if len(game.players_score) < 1:

            try:
                await game.channel.send("Not enough players joined!")
            except Exception as e:
                print(f"Error sending message: {e}")

            del self.games[game.channel.id]
            return

        game.participant_list = game.join_order

        # Indicate round starting
        game.current_round_index = 0

        try:
            await game.channel.send("Game has started!")
        except Exception as e:
            print(f"Error sending message: {e}")

        await self.start_round(game)

    @commands.command()
    async def create(self, ctx, max_queries: int = 20):
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
            await asyncio.sleep(3)
            await self.end_recruitment(game)

        game.recruitment_task = asyncio.create_task(recruitment_timeout())
        game.recruitment_start = datetime.utcnow()

        player_id = ctx.author.id

        game.join_order.append(player_id)
        game.players_score[player_id] = 0.0

        await ctx.send("Game created! Use -join to join!")

    @commands.command()
    async def join(self, ctx):
        """Allows players to join the game started"""

        game = self.games.get(ctx.channel.id)

        if game is None:
            await ctx.send("There is no game to join! Try -create to start a game!")
            return

        if game.current_round_index != -1:
            await ctx.send("The game already started! Please wait till it ends.")
            return
            # TODO: allow players to join regardless, starting with 0 points though.

        player_id = ctx.author.id

        if player_id in game.players_score:
            await ctx.send("You are already in the game!")
            return

        game.join_order.append(player_id)
        game.players_score[player_id] = 0.0

        await ctx.send("You are now in the game!")


async def setup(bot):
    """Add the IOGame cog to the bot."""
    await bot.add_cog(IOGame(bot))
