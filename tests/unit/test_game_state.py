"""Unit tests for game state management."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.services import game_manager, GameState


class TestGameManager:
    """Test cases for GameManager."""

    def setup_method(self):
        """Reset game manager before each test."""
        game_manager.games.clear()

    def test_initial_state(self):
        """Test that game manager starts with empty games dict."""
        assert len(game_manager.games) == 0
        assert game_manager.get_game(12345) is None

    def test_create_game(self):
        """Test creating a new game."""
        chat_id = 12345
        host_id = 1001
        username = "testuser"

        game_manager.create_game(chat_id, host_id, username)

        game = game_manager.get_game(chat_id)

        assert game is not None
        assert game.state == GameState.WAITING_CHARACTER
        assert game.host_id == host_id
        assert game.host_username == username
        assert game.character is None
        assert game.waiting_for_character is False

    def test_create_game_without_username(self):
        """Test creating a game without username."""
        chat_id = 12345
        host_id = 1001

        game_manager.create_game(chat_id, host_id, None)

        game = game_manager.get_game(chat_id)

        assert game is not None
        assert game.host_username is None

    def test_get_nonexistent_game(self):
        """Test getting a game that doesn't exist."""
        game = game_manager.get_game(99999)
        assert game is None

    def test_set_character_success(self):
        """Test successfully setting a character."""
        chat_id = 12345
        host_id = 1001
        game_manager.create_game(chat_id, host_id)

        character = "Harry Potter"
        success = game_manager.set_character(chat_id, character)

        assert success is True

        game = game_manager.get_game(chat_id)
        assert game.character == character
        assert game.state == GameState.ACTIVE
        assert game.waiting_for_character is False

    def test_set_character_wrong_state(self):
        """Test setting character in wrong state."""
        chat_id = 12345
        host_id = 1001
        game_manager.create_game(chat_id, host_id)
        game_manager.set_character(chat_id, "Test Character")

        # Try to set character again when already active
        success = game_manager.set_character(chat_id, "Another Character")

        assert success is False
        game = game_manager.get_game(chat_id)
        assert game.character == "Test Character"  # Should not change

    def test_set_character_nonexistent_game(self):
        """Test setting character for nonexistent game."""
        success = game_manager.set_character(99999, "Test")
        assert success is False

    def test_set_waiting_for_character_success(self):
        """Test successfully marking user as waiting for character."""
        chat_id = 12345
        host_id = 1001
        game_manager.create_game(chat_id, host_id)

        success = game_manager.set_waiting_for_character(chat_id, host_id, True)

        assert success is True
        game = game_manager.get_game(chat_id)
        assert game.waiting_for_character is True

    def test_set_waiting_for_character_wrong_user(self):
        """Test marking waiting status for wrong user."""
        chat_id = 12345
        host_id = 1001
        other_user = 2002
        game_manager.create_game(chat_id, host_id)

        success = game_manager.set_waiting_for_character(chat_id, other_user, True)

        assert success is False
        game = game_manager.get_game(chat_id)
        assert game.waiting_for_character is False

    def test_set_waiting_for_character_wrong_state(self):
        """Test marking waiting status in wrong game state."""
        chat_id = 12345
        host_id = 1001
        game_manager.create_game(chat_id, host_id)
        game_manager.set_character(chat_id, "Test Character")

        success = game_manager.set_waiting_for_character(chat_id, host_id, True)

        assert success is False

    def test_is_waiting_for_character_true(self):
        """Test checking if user is waiting for character (true case)."""
        chat_id = 12345
        host_id = 1001
        game_manager.create_game(chat_id, host_id)
        game_manager.set_waiting_for_character(chat_id, host_id, True)

        is_waiting = game_manager.is_waiting_for_character(chat_id, host_id)

        assert is_waiting is True

    def test_is_waiting_for_character_false(self):
        """Test checking if user is waiting for character (false case)."""
        chat_id = 12345
        host_id = 1001
        game_manager.create_game(chat_id, host_id)

        # Not marked as waiting
        is_waiting = game_manager.is_waiting_for_character(chat_id, host_id)
        assert is_waiting is False

        # Wrong user
        is_waiting = game_manager.is_waiting_for_character(chat_id, 99999)
        assert is_waiting is False

        # Wrong chat
        is_waiting = game_manager.is_waiting_for_character(99999, host_id)
        assert is_waiting is False

    def test_end_game_with_character(self):
        """Test ending a game with character set."""
        chat_id = 12345
        host_id = 1001
        game_manager.create_game(chat_id, host_id)
        game_manager.set_character(chat_id, "Test Character")

        game_data = game_manager.end_game(chat_id)

        assert game_data is not None
        assert game_data.character == "Test Character"
        assert game_data.host_id == host_id

        # Game should be removed
        assert game_manager.get_game(chat_id) is None

    def test_end_game_without_character(self):
        """Test ending a game without character set."""
        chat_id = 12345
        host_id = 1001
        game_manager.create_game(chat_id, host_id)

        game_data = game_manager.end_game(chat_id)

        assert game_data is not None
        assert game_data.character is None

        assert game_manager.get_game(chat_id) is None

    def test_end_nonexistent_game(self):
        """Test ending a game that doesn't exist."""
        game_data = game_manager.end_game(99999)
        assert game_data is None

    def test_has_active_game_true(self):
        """Test checking for active game (true case)."""
        chat_id = 12345
        host_id = 1001
        game_manager.create_game(chat_id, host_id)

        has_active = game_manager.has_active_game(chat_id)
        assert has_active is True

    def test_has_active_game_false(self):
        """Test checking for active game (false case)."""
        # Nonexistent game
        has_active = game_manager.has_active_game(99999)
        assert has_active is False

        # Create and immediately end game
        chat_id = 12345
        host_id = 1001
        game_manager.create_game(chat_id, host_id)
        game_manager.end_game(chat_id)

        has_active = game_manager.has_active_game(chat_id)
        assert has_active is False

    def test_get_host_game_found(self):
        """Test finding a game where user is host."""
        chat_id = 12345
        host_id = 1001
        username = "testuser"
        game_manager.create_game(chat_id, host_id, username)

        result = game_manager.get_host_game(host_id)

        assert result is not None
        found_chat_id, game = result
        assert found_chat_id == chat_id
        assert game.host_id == host_id
        assert game.host_username == username

    def test_get_host_game_not_found(self):
        """Test finding game for non-host user."""
        result = game_manager.get_host_game(99999)
        assert result is None

    def test_multiple_games(self):
        """Test managing multiple games simultaneously."""
        # Create multiple games
        games_data = [
            (11111, 1001, "user1"),
            (22222, 2002, "user2"),
            (33333, 3003, "user3"),
        ]

        for chat_id, host_id, username in games_data:
            game_manager.create_game(chat_id, host_id, username)

        # Check all games exist
        assert len(game_manager.games) == 3

        for chat_id, host_id, username in games_data:
            game = game_manager.get_game(chat_id)
            assert game is not None
            assert game.host_id == host_id
            assert game.host_username == username

        # Modify one game
        game_manager.set_character(22222, "Character 2")

        # Verify other games are unaffected
        game1 = game_manager.get_game(11111)
        assert game1.character is None

        game3 = game_manager.get_game(33333)
        assert game3.character is None

        game2 = game_manager.get_game(22222)
        assert game2.character == "Character 2"
        assert game2.state == GameState.ACTIVE

    def test_game_isolation(self):
        """Test that games are properly isolated."""
        chat1 = 11111
        chat2 = 22222

        game_manager.create_game(chat1, 1001, "user1")
        game_manager.create_game(chat2, 2002, "user2")

        game_manager.set_character(chat1, "Character 1")

        game1 = game_manager.get_game(chat1)
        game2 = game_manager.get_game(chat2)

        assert game1.character == "Character 1"
        assert game1.state == GameState.ACTIVE
        assert game2.character is None
        assert game2.state == GameState.WAITING_CHARACTER

        # End first game
        game_manager.end_game(chat1)

        assert game_manager.get_game(chat1) is None
        assert game_manager.get_game(chat2) is not None
