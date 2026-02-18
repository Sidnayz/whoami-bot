"""Unit tests for private message handlers."""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.handlers.private_handlers import (
    cmd_start_help,
    cmd_mygame,
    process_character_input
)
from bot.services import game_manager


@pytest.fixture
def reset_game_manager():
    """Reset game manager before each test."""
    game_manager.games.clear()
    yield
    game_manager.games.clear()


@pytest.fixture
def mock_private_message():
    """Create a mock Message object for private chat."""
    message = Mock()
    message.chat = Mock()
    message.chat.id = 1001  # User ID same as private chat ID
    message.chat.type = "private"
    message.from_user = Mock()
    message.from_user.id = 1001
    message.from_user.username = "testuser"
    message.text = "test message"
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_state():
    """Create a mock FSM state."""
    state = AsyncMock()
    state.set_state = AsyncMock()
    state.get_state = AsyncMock(return_value=None)
    state.clear = AsyncMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    return state


class TestStartHelpCommand:
    """Test cases for /start and /help in private chat."""

    @pytest.mark.asyncio
    async def test_cmd_start_help_sends_help_text(self, mock_private_message):
        """Test that /start sends help text in private chat."""
        await cmd_start_help(mock_private_message)

        mock_private_message.answer.assert_called_once()

        call_args = mock_private_message.answer.call_args
        assert call_args is not None
        text = call_args[0][0]

        assert "Угадай персонажа" in text
        assert "/startgame" in text
        assert "/mygame" in text


class TestMyGameCommand:
    """Test cases for /mygame command."""

    @pytest.mark.asyncio
    async def test_cmd_mygame_with_active_game(self, mock_private_message, mock_state, reset_game_manager):
        """Test /mygame when user is host of waiting game."""
        # Setup game
        game_manager.create_game(12345, 1001, "testuser")

        await cmd_mygame(mock_private_message, mock_state)

        mock_private_message.answer.assert_called_once()
        call_text = mock_private_message.answer.call_args[0][0]
        assert "Отправь имя персонажа" in call_text

        mock_state.set_state.assert_called_once()

        # Verify waiting flag is set
        game = game_manager.get_game(12345)
        assert game.waiting_for_character is True

    @pytest.mark.asyncio
    async def test_cmd_mygame_no_game(self, mock_private_message, mock_state, reset_game_manager):
        """Test /mygame when user has no waiting game."""
        await cmd_mygame(mock_private_message, mock_state)

        mock_private_message.answer.assert_called_once()
        call_text = mock_private_message.answer.call_args[0][0]
        assert "Сейчас нет игр, где ты должен загадать персонажа" in call_text

        mock_state.set_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_cmd_mygame_wrong_user(self, mock_private_message, mock_state, reset_game_manager):
        """Test /mygame when user is not the host."""
        game_manager.create_game(12345, 9999, "otheruser")

        await cmd_mygame(mock_private_message, mock_state)

        mock_private_message.answer.assert_called_once()
        call_text = mock_private_message.answer.call_args[0][0]
        assert "нет игр, где ты должен загадать персонажа" in call_text


class TestProcessCharacterInput:
    """Test cases for processing character input."""

    @pytest.mark.asyncio
    async def test_process_character_input_success(self, mock_private_message, mock_state, reset_game_manager):
        """Test successful character input."""
        # Setup game
        game_manager.create_game(12345, 1001, "testuser")
        game_manager.set_waiting_for_character(12345, 1001, True)

        mock_private_message.text = "Harry Potter"
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        await process_character_input(mock_private_message, mock_state, mock_bot)

        # Verify character was saved
        game = game_manager.get_game(12345)
        assert game.character == "Harry Potter"
        assert game.state.value == "active"

        # Verify responses
        mock_private_message.answer.assert_called()
        call1 = mock_private_message.answer.call_args_list[0]
        assert "Harry Potter" in call1[0][0]

        mock_bot.send_message.assert_called_once()
        bot_call = mock_bot.send_message.call_args
        assert bot_call[0][0] == 12345
        assert "можно задавать вопросы" in bot_call[0][1].lower()

        mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_character_input_empty_string(self, mock_private_message, mock_state, reset_game_manager):
        """Test character input with empty string."""
        game_manager.create_game(12345, 1001, "testuser")
        game_manager.set_waiting_for_character(12345, 1001, True)

        mock_private_message.text = "   "
        mock_bot = Mock()

        await process_character_input(mock_private_message, mock_state, mock_bot)

        mock_private_message.answer.assert_called_once()
        call_text = mock_private_message.answer.call_args[0][0]
        assert "не может быть пустым" in call_text

        mock_state.clear.assert_not_called()

        # Game should remain unchanged
        game = game_manager.get_game(12345)
        assert game.character is None

    @pytest.mark.asyncio
    async def test_process_character_input_no_game(self, mock_private_message, mock_state, reset_game_manager):
        """Test character input when no game exists."""
        mock_private_message.text = "Test Character"
        mock_bot = Mock()

        await process_character_input(mock_private_message, mock_state, mock_bot)

        mock_private_message.answer.assert_called_once()
        call_text = mock_private_message.answer.call_args[0][0]
        assert "Ошибка: игра не найдена" in call_text

        mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_character_input_not_waiting(self, mock_private_message, mock_state, reset_game_manager):
        """Test character input when not marked as waiting."""
        game_manager.create_game(12345, 1001, "testuser")
        # Don't set waiting flag

        mock_private_message.text = "Test Character"
        mock_bot = Mock()

        await process_character_input(mock_private_message, mock_state, mock_bot)

        mock_private_message.answer.assert_called_once()
        call_text = mock_private_message.answer.call_args[0][0]
        assert "неверное состояние игры" in call_text

        mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_character_input_bot_send_error(self, mock_private_message, mock_state, reset_game_manager):
        """Test character input when bot fails to send message to group."""
        game_manager.create_game(12345, 1001, "testuser")
        game_manager.set_waiting_for_character(12345, 1001, True)

        mock_private_message.text = "Harry Potter"
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock(side_effect=Exception("Bot blocked in group"))

        await process_character_input(mock_private_message, mock_state, mock_bot)

        # Character should still be saved
        game = game_manager.get_game(12345)
        assert game.character == "Harry Potter"
        assert game.state.value == "active"

        # Should inform user about the error
        assert mock_private_message.answer.call_count >= 1

        mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_character_input_multiple_games(self, mock_private_message, mock_state, reset_game_manager):
        """Test character input when user is host of multiple games (should pick first)."""
        # Create multiple games with same host
        game_manager.create_game(11111, 1001, "testuser")
        game_manager.create_game(22222, 1001, "testuser")
        game_manager.set_waiting_for_character(11111, 1001, True)
        game_manager.set_waiting_for_character(22222, 1001, True)

        mock_private_message.text = "Test Character"
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        await process_character_input(mock_private_message, mock_state, mock_bot)

        # Should set character in one game (implementation picks first found)
        game111 = game_manager.get_game(11111)
        game222 = game_manager.get_game(22222)

        # At least one should have character set
        character_set = (game111.character == "Test Character") or (game222.character == "Test Character")
        assert character_set

    @pytest.mark.asyncio
    async def test_process_character_input_special_characters(self, mock_private_message, mock_state, reset_game_manager):
        """Test character input with special characters."""
        game_manager.create_game(12345, 1001, "testuser")
        game_manager.set_waiting_for_character(12345, 1001, True)

        mock_private_message.text = "Дарт Вейдер ™ ©"
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        await process_character_input(mock_private_message, mock_state, mock_bot)

        game = game_manager.get_game(12345)
        assert game.character == "Дарт Вейдер ™ ©"
