"""Game state management module."""

from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class GameState(str, Enum):
    """Game states."""
    IDLE = "idle"
    WAITING_CHARACTER = "waiting_character"
    ACTIVE = "active"


@dataclass
class GameData:
    """Game data structure."""
    state: GameState = GameState.IDLE
    host_id: Optional[int] = None
    host_username: Optional[str] = None
    character: Optional[str] = None
    waiting_for_character: bool = False


class GameManager:
    """Manages game state for all groups."""

    def __init__(self):
        self.games: Dict[int, GameData] = {}

    def create_game(self, chat_id: int, host_id: int, host_username: Optional[str] = None) -> None:
        """Create a new game in waiting_character state."""
        self.games[chat_id] = GameData(
            state=GameState.WAITING_CHARACTER,
            host_id=host_id,
            host_username=host_username
        )

    def get_game(self, chat_id: int) -> Optional[GameData]:
        """Get game data for a chat."""
        return self.games.get(chat_id)

    def set_character(self, chat_id: int, character: str) -> bool:
        """Set character and transition to active state."""
        game = self.games.get(chat_id)
        if game and game.state == GameState.WAITING_CHARACTER:
            game.character = character
            game.state = GameState.ACTIVE
            game.waiting_for_character = False
            return True
        return False

    def set_waiting_for_character(self, chat_id: int, user_id: int, waiting: bool) -> bool:
        """Mark if user is waiting to input character."""
        game = self.games.get(chat_id)
        if game and game.host_id == user_id and game.state == GameState.WAITING_CHARACTER:
            game.waiting_for_character = waiting
            return True
        return False

    def is_waiting_for_character(self, chat_id: int, user_id: int) -> bool:
        """Check if user is waiting to input character."""
        game = self.games.get(chat_id)
        return (
            game is not None
            and game.host_id == user_id
            and game.state == GameState.WAITING_CHARACTER
            and game.waiting_for_character
        )

    def end_game(self, chat_id: int) -> Optional[GameData]:
        """End a game and return the game data."""
        return self.games.pop(chat_id, None)

    def has_active_game(self, chat_id: int) -> bool:
        """Check if chat has any non-idle game."""
        game = self.games.get(chat_id)
        return game is not None and game.state != GameState.IDLE

    def get_host_game(self, user_id: int) -> Optional[tuple[int, GameData]]:
        """Get a game where user is host and waiting for character."""
        for chat_id, game in self.games.items():
            if game.host_id == user_id and game.state == GameState.WAITING_CHARACTER:
                return chat_id, game
        return None


# Global instance
game_manager = GameManager()
