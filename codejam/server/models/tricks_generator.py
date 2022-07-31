import asyncio
import random
from typing import Dict

from codejam.server.interfaces.message import Message
from codejam.server.interfaces.topics import Topic, TopicEnum, TrickOperations
from codejam.server.interfaces.trick_message import TrickMessage
from codejam.server.models.game import Game


class TrickGenerator:
    """Select and dispatch a trick/ bug on the drawing user."""

    def __init__(self, game: Game):
        self.game = game
        self.options = [x for x in TrickOperations]
        self.prankster = "Dirty Goblin"

        self.descriptions: Dict[TrickOperations, str] = {
            TrickOperations.SNAIL: (
                "The rouge snail overtook your tools,\n "
                "don't draw too quick or it won't be able to follow!"
            ),
            TrickOperations.EARTHQUAKE: (
                "Is it a bird? A plane? No it's an earthquake!\n "
                "Hold tight while it shakes you drawing!"
            ),
            TrickOperations.LANDSLIDE: (
                "Timbeeeer! Or rather land slide!\n " "An avalanche swept your drawing canvas!"
            ),
            TrickOperations.NOTHING: (
                f"The {self.prankster} decided to spare you,\n " f"you can draw in peace!"
            ),
            TrickOperations.PACMAN: (
                "The wild pacman was seen in your area,\n" " be careful he likes to eat drawings!"
            ),
        }

    def generate_trick(self) -> TrickOperations:
        """Chooses a trick to apply."""
        return random.choice(self.options)

    def choose_description(self, operation: TrickOperations) -> str:
        """Set description of trick message based on operation provided."""
        return self.descriptions[operation]

    def choose_delay(self) -> int:
        """Selects a delay for a trick from 3s to 1/2 of turn duration."""
        return random.randint(3, int(self.game.current_turn.duration / 3))

    def prepare_trick_message(self) -> Message:
        """Formats the trick message."""
        operation = self.generate_trick()
        return Message(
            topic=Topic(type=TopicEnum.TRICK, operation=operation),
            username=self.prankster,
            game_id=self.game.secret,
            value=TrickMessage(
                game_id=self.game.secret,
                description=self.choose_description(operation=operation),
            ),
        )

    async def release_the_kraken(self):
        """Release the trick on the drawing user."""
        await asyncio.sleep(self.choose_delay())
        await self.game.current_turn.drawer.send_message(self.prepare_trick_message())
