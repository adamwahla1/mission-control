# Telegram Bot Setup Guide

## 1. Create Bot with BotFather

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot`
3. Follow prompts to name your bot
4. Save the API token (looks like: `123456789:ABCdefGHIjkl...`)

## 2. Configure Environment

Add to `.env`:
```
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook/your-bot-id
```

## 3. Setup Webhook

```bash
curl -X POST https://your-domain.com/api/v1/telegram/webhook/setup
```

Or manually:
```bash
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/api/v1/telegram/webhook/YOUR_BOT_ID"}'
```

## 4. Available Commands

- `/start` - Welcome message
- `/help` - Command list
- `/agents` - List all agents
- `/agent <id>` - Get agent details
- `/tasks` - List recent tasks
- `/task <id>` - Get task details
- `/assign <task_id> to <agent_id>` - Assign task
- `/status` - System status
- `/alert <message>` - Broadcast alert

## 5. Testing Locally

For local development without public URL, use polling:
```python
# In a separate script
from telegram import Update
from telegram.ext import Application, CommandHandler

async def start(update: Update, context):
    await update.message.reply_text('Hello!')

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
```

Note: Webhook requires HTTPS. Use ngrok for local testing:
```bash
ngrok http 8000
# Use the HTTPS URL as webhook URL
```
