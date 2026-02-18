# Telegram Bot - Guess the Character

Telegram bot for group "guess the character" game.

## 📋 Features

- Group-based game play
- Players ask questions, host answers with buttons (Yes/No/Don't Know/Partially)
- Character input through private chat
- Permission system (host only, admin override)
- Full Russian language support

## 🚀 Deployment on Render

### Prerequisites
- Bot token from [@BotFather](https://t.me/botfather)
- Render account

### Setup Steps

1. **Fork or clone this repository**
   ```bash
   git clone https://github.com/Sidnayz/whoami-bot.git
   cd whoami-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create Bot on Telegram**
   - Message @BotFather on Telegram
   - Create new bot with `/newbot`
   - Copy the token

4. **Deploy on Render**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `whoami-bot` (or any name)
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python main.py`
   - In "Environment Variables", add:
     - `BOT_TOKEN`: your_bot_token_here
   - Click "Deploy Web Service"

5. **Verify Deployment**
   - Check logs in Render dashboard
   - Message your bot in Telegram: `/start`

## 🎮 How to Play

### For Host
1. Start game in group: `/startgame`
2. Bot will send you to private chat
3. Send `/mygame` in private chat
4. Send character name
5. Answer questions with buttons

### For Players
1. Wait for host to start game
2. Ask questions ending with `?`
3. See host's answers below each question

## 📝 Commands

| Command | Location | Description |
|---------|-----------|-------------|
| `/start` | Any | Show help |
| `/help` | Any | Show help |
| `/startgame` | Group | Start new game |
| `/endgame` | Group | End game (host or admin) |
| `/status` | Group | Show game status |
| `/mygame` | Private | Start character input |

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set bot token
set BOT_TOKEN=your_token_here  # Windows
export BOT_TOKEN=your_token_here  # Linux/Mac

# Run bot
python main.py
```

## 📊 Project Structure

```
whoami-bot/
├── main.py              # Entry point
├── requirements.txt      # Python dependencies
├── Procfile            # Render deployment config
├── .gitignore          # Git ignore patterns
├── .env.example        # Environment variables template
└── bot/
    ├── config/         # Configuration
    ├── handlers/       # Command & message handlers
    ├── keyboards/      # Inline keyboards
    └── services/       # Game state management
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bot --cov-report=html
```

## 🔐 Security

- Never commit `.env` file with real tokens
- Use environment variables for secrets
- Bot tokens are stored only in Render environment

## 📄 License

This project is open source and available under MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Built with ❤️ using [aiogram](https://docs.aiogram.dev/) 3.x
