"""Unit tests for group command handlers."""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.handlers.group_handlers import (
    cmd_start_help,
    cmd_startgame,
    cmd_endgame,
    cmd_status
)
from bot.services import game_manager


@pytest.fixture
def reset_game_manager():
    """Reset game manager before each test."""
    game_manager.games.clear()
    yield
    game_manager.games.clear()


@pytest.fixture
def mock_message():
    """Create a mock Message object for group chat."""
    message = Mock()
    message.chat = Mock()
    message.chat.id = 12345
    message.chat.type = "supergroup"
    message.from_user = Mock()
    message.from_user.id = 1001
    message.from_user.username = "testuser"
    message.text = "/test"
    message.answer = AsyncMock()
    return message


class TestStartHelpCommand:
    """Test cases for /start and /help commands."""

    @pytest.mark.asyncio
    async def test_cmd_start_help_sends_help_text(self, mock_message):
        """Test that /start and /help send help text."""
        await cmd_start_help(mock_message)

        mock_message.answer.assert_called_once()

        call_args = mock_message.answer.call_args
        assert call_args is not None
        text = call_args[0][0]

        assert "Угадай персонажа" in text
        assert "/startgame" in text
        assert "/endgame" in text
        assert "/status" in text


class TestStartGameCommand:
    """Test cases for /startgame command."""

    @pytest.mark.asyncio
    async def test_cmd_startgame_creates_game(self, mock_message, reset_game_manager):
        """Test that /startgame creates a new game."""
        await cmd_startgame(mock_message)

        game = game_manager.get_game(12345)

        assert game is not None
        assert game.host_id == 1001
        assert game.host_username == "testuser"
        assert game.state.value == "waiting_character"

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "стал загадывающим" in call_text
        assert "/mygame" in call_text

    @pytest.mark.asyncio
    async def test_cmd_startgame_without_username(self, mock_message, reset_game_manager):
        """Test /startgame with user without username."""
        mock_message.from_user.username = None

        await cmd_startgame(mock_message)

        game = game_manager.get_game(12345)
        assert game is not None
        assert game.host_username is None

        call_text = mock_message.answer.call_args[0][0]
        assert "ID 1001" in call_text

    @pytest.mark.asyncio
    async def test_cmd_startgame_when_game_exists(self, mock_message, reset_game_manager):
        """Test /startgame when game already exists."""
        # Create existing game
        game_manager.create_game(12345, 9999, "otheruser")

        await cmd_startgame(mock_message)

        # Should not create new game
        game = game_manager.get_game(12345)
        assert game.host_id == 9999  # Should remain the original host

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "Игра уже идёт" in call_text
        assert "/endgame" in call_text


class TestEndGameCommand:
    """Test cases for /endgame command."""

    @pytest.mark.asyncio
    async def test_cmd_endgame_by_host_with_character(self, mock_message, reset_game_manager):
        """Test /endgame by host when character is set."""
        # Setup game with character
        game_manager.create_game(12345, 1001, "testuser")
        game_manager.set_character(12345, "Harry Potter")

        await cmd_endgame(mock_message)

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "Игра окончена" in call_text
        assert "Harry Potter" in call_text

        # Game should be removed
        assert game_manager.get_game(12345) is None

    @pytest.mark.asyncio
    async def test_cmd_endgame_by_host_without_character(self, mock_message, reset_game_manager):
        """Test /endgame by host when character is not set."""
        game_manager.create_game(12345, 1001, "testuser")

        await cmd_endgame(mock_message)

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "остановлена до ввода персонажа" in call_text

        assert game_manager.get_game(12345) is None

    @pytest.mark.asyncio
    async def test_cmd_endgame_when_no_game(self, mock_message, reset_game_manager):
        """Test /endgame when no game exists."""
        await cmd_endgame(mock_message)

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "нет активной игры" in call_text

    @pytest.mark.asyncio
    async def test_cmd_endgame_by_non_host_non_admin(self, mock_message, reset_game_manager):
        """Test /endgame by non-host, non-admin user."""
        # Create game with different host
        game_manager.create_game(12345, 9999, "otheruser")

        with patch('bot.handlers.group_handlers.is_admin', return_value=False):
            await cmd_endgame(mock_message)

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "Завершить игру может только загадывающий или администратор" in call_text

        # Game should not be ended
        assert game_manager.get_game(12345) is not None

    @pytest.mark.asyncio
    async def test_cmd_endgame_by_admin(self, mock_message, reset_game_manager):
        """Test /endgame by admin user."""
        game_manager.create_game(12345, 9999, "otheruser")

        with patch('bot.handlers.group_handlers.is_admin', return_value=True):
            await cmd_endgame(mock_message)

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "Игра остановлена" in call_text

        # Game should be ended
        assert game_manager.get_game(12345) is None


class TestStatusCommand:
    """Test cases for /status command."""

    @pytest.mark.asyncio
    async def test_cmd_status_when_no_game(self, mock_message, reset_game_manager):
        """Test /status when no game exists."""
        await cmd_status(mock_message)

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "нет активной игры" in call_text

    @pytest.mark.asyncio
    async def test_cmd_status_waiting_character(self, mock_message, reset_game_manager):
        """Test /status when waiting for character."""
        game_manager.create_game(12345, 1001, "testuser")

        await cmd_status(mock_message)

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "Игра создаётся" in call_text
        assert "Загадывающий" in call_text
        assert "имя персонажа боту в личку" in call_text

    @pytest.mark.asyncio
    async def test_cmd_status_active(self, mock_message, reset_game_manager):
        """Test /status when game is active."""
        game_manager.create_game(12345, 1001, "testuser")
        game_manager.set_character(12345, "Test Character")

        await cmd_status(mock_message)

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "Игра идёт" in call_text
        assert "задавать вопросы" in call_text

    @pytest.mark.asyncio
    async def test_cmd_status_without_username(self, mock_message, reset_game_manager):
        """Test /status when host has no username."""
        game_manager.create_game(12345, 1001, None)

        await cmd_status(mock_message)

        mock_message.answer.assert_called_once()
        call_text = mock_message.answer.call_args[0][0]
        assert "ID 1001" in call_text
