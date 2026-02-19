# 🎮 Telegram Bot - Guess the Character

Telegram bot for group "guess the character" game with Railway deployment.

## 📋 Features

- Group-based game play
- Players ask questions, host answers with buttons (Yes/No/Don't Know/Partially)
- Character input through private chat
- Permission system (host only, admin override)
- Full Russian language support
- Optimized for Railway (fast deployment, minimal build)

## 🚀 Deployment on Railway

### Prerequisites
- Bot token from [@BotFather](https://t.me/BotFather)
- Railway account [https://dashboard.railway.app](https://dashboard.railway.app)
- GitHub repository connected to Railway

### Automatic Deployment (Recommended)

The bot will be automatically deployed to Railway when you push changes to GitHub!

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

## 📊 Project Structure

```
whoami-bot/
├── main.py              # Entry point
├── requirements.txt      # Python dependencies (aiogram + aiohttp + pydantic-core)
├── Dockerfile           # Docker configuration (optimized for Railway)
├── .gitignore          # Git ignore patterns
├── .env.example        # Environment variables template
├── bot/
│   ├── config/         # Configuration
│   ├── handlers/       # Command & message handlers
│   ├── keyboards/      # Inline keyboards
│   ├── services/       # Game state management
│   └── utils.py        # Utility functions
└── tests/               # Tests (for CI)
    ├── unit/          # Unit tests
    └── integration/     # Integration tests
```

## 📝 How to Deploy to Railway

### Automatic Deployment (Recommended)

The project is already set up for automatic deployment to Railway. Just push your changes:

```bash
git add .
git commit -m "your commit message"
git push
```

Railway will automatically deploy your bot within 1-2 minutes!

### Manual Deployment (if needed)

1. Go to [Railway Dashboard](https://dashboard.railway.app)
2. Login to your account
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Connect your GitHub repository: `Sidnayz/whoami-bot`
6. Click "Deploy"

### Environment Variables

On Railway dashboard, add:
```
BOT_TOKEN=your_bot_token_from_botfather
```

⚠️ **IMPORTANT:** Only add this variable on Railway, don't commit `.env` file with real tokens!

## 🧪 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run bot
python main.py
```

## 🔗 Bot Setup

1. Create bot on Telegram:
   - Message [@BotFather](https://t.me/BotFather)
   - Command: `/newbot`
   - Copy the token (starts with `123456789:ABC...`)

2. Add bot to group:
   - Open group in Telegram
   - Add bot as administrator
   - Make bot a member of the group

3. Test bot:
   - Send `/start` in group
   - Send `/startgame` to start game
   - Play a full game!

## 🔐 Security

- Never commit `.env` file with real tokens
- Use environment variables for secrets
- Bot tokens are stored only in Railway environment

## 📊 Monitoring

After deployment, monitor on Railway:
- Logs - see bot startup and errors
- Metrics - CPU and memory usage
- Status - ensure service is live

## 🐛 Troubleshooting

### Bot doesn't start
- Check logs in Railway dashboard
- Verify `BOT_TOKEN` is set correctly
- Ensure bot is added to group as admin

### Bot doesn't respond
- Check if bot has access to group
- Verify webhook status (should be polling)
- Check logs for errors

### Deployment fails
- Ensure Railway has GitHub access
- Check build logs for errors
- Verify Dockerfile syntax

## 📄 License

This project is open source and available under MIT License.

---

Deployed with ❤️ on Railway | Ready to play! 🎮
