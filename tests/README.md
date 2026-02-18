# Testing

This directory contains all tests for the Telegram bot.

## Test Structure

### Unit Tests (`tests/unit/`)
- `test_game_state.py` - Tests for game state management and game data operations
- `test_group_handlers.py` - Tests for group chat command handlers
- `test_private_handlers.py` - Tests for private chat message handlers
- `test_question_handlers.py` - Tests for question handling and callback handlers

### Integration Tests (`tests/integration/`)
- `test_game_flow.py` - Tests for complete game lifecycle and flow

## Running Tests

### Run all tests:
```bash
pytest
```

### Run only unit tests:
```bash
pytest tests/unit/
```

### Run only integration tests:
```bash
pytest tests/integration/
```

### Run specific test file:
```bash
pytest tests/unit/test_game_state.py
```

### Run specific test:
```bash
pytest tests/unit/test_game_state.py::TestGameManager::test_create_game
```

### Run tests with coverage:
```bash
pytest --cov=bot --cov-report=html
```

## Test Coverage

The tests cover:
- Game state transitions (idle, waiting_character, active)
- All bot commands (/start, /help, /startgame, /endgame, /status, /mygame)
- Question detection and handling in groups
- Callback handling for answer buttons
- Permission checks (host only, admin access)
- Edge cases (empty input, duplicate games, invalid states)
- Multiple concurrent games
- Complete game flow from start to end

## Test Principles Used

1. **Isolation** - Each test is independent with proper setup/teardown
2. **Arrange-Act-Assert** - Clear test structure for readability
3. **Edge Cases** - Testing boundary conditions and error paths
4. **Mocking** - Using Mock and AsyncMock for external dependencies
5. **Fixtures** - Reusable test setup through pytest fixtures
6. **Descriptive Names** - Test names clearly describe what is being tested
