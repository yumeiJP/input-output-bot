"""Function‑guessing game cog."""

import asyncio
from datetime import datetime

import numexpr as ne
from discord.ext import commands


class Game:  # pylint: disable=too-many-instance-attributes
    """Full game session"""

    def __init__(self, channel, initiator_user_id, max_queries_per_round):
        self.channel = channel
        self.initiator_user_id = initiator_user_id
        self.max_queries_per_round = max_queries_per_round
        self.players_score = {}
        self.recruitment_task = None
        self.recruitment_start = None
        self.player_list = []
        self.rounds = []
        self.current_round_index = -1


class Round:
    """Single round within the game"""

    def __init__(self, creator_user_id, max_queries):
        self.creator_id = creator_user_id
        self.max_queries = max_queries
        self.penalty = 1000.0 / max_queries
        self.secret_function = None
        self.players = {}
        self.active = False


class PlayerRoundState:
    """Player's state during a round"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.query_count = 0
        self.solved = False


class IOGame(commands.Cog):
    """Handles the I/O function-guessing game"""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot
        self.games = {}
        self.pending_creators = {}

    async def start_round(self, game, function_creator):
        """Starts the round"""
        max_queries = game.max_queries_per_round
        round = Round(function_creator, max_queries)
        game.rounds.append(round)

        await function_creator.send("Please choose a function.")
        self.pending_creators[function_creator] = game

    async def start_game(self, game):
        """Chooses a function creator and starts the game"""
        for player in game.player_list:

            function_creator = player
            self.start_round(game, function_creator)

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

        # Indicate round starting
        game.current_round_index = 0

        try:
            await game.channel.send("Game has started!")
        except Exception as e:
            print(f"Error sending message: {e}")

        await self.start_game(game)

    @commands.command()
    async def create(self, ctx, max_queries: int = 20):
        """Starts a new game (Recuritment phase)"""
        if ctx.channel.id in self.games:
            await ctx.send("There is already a game starting!")
            return

        if (
            not (max_queries >= 1 and isinstance(max_queries, int))
        ) or max_queries is None:
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

        game.player_list.append(player_id)
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

        game.player_list.append(player_id)
        game.players_score[player_id] = 0.0

        await ctx.send("You are now in the game!")

    async def check_valid_expression(self, expression):
        try:
            ne.evaluate(expression, local_dict={"x": 0})
            return True
        except Exception:
            return False

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handles messages from creators and players"""

        if message.author.bot:
            return
        if message.guild is not None:
            return

        if message.author.id in self.pending_creators:
            # Sent from creator
            # Trying to input a function

            content = message.content.strip()

            valid = self.check_valid_expression(content)

            user = message.author.id

            if not valid:
                await user.send(
                    "You did not send a valid expression! Please try again."
                )
                return

            await user.send("Valid expression")

            game = self.pending_creators[message.author.id]
            round_index = game.current_round_index
            round = game.rounds[round_index]
            round.secret_function = content

            self.pending_creators.pop(message.author.id)


async def setup(bot):
    """Add the IOGame cog to the bot."""
    await bot.add_cog(IOGame(bot))
