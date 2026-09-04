# Article Reader Bot

Telegram bot for reading cleaned articles from supported publishers. It can run locally with long polling, or on Vercel as a Telegram webhook.

## Requirements

- Python 3.12
- Telegram bot token from BotFather
- Article extraction endpoint
- PostgreSQL database for Vercel deployments

## Environment Variables

Create a `.env` file for local development, or set these in Vercel Production environment variables:

```sh
BOT_TOKEN="123456:telegram-bot-token"
ADMIN_ID="123456789"
ARTICLE_ENDPOINT="https://your-article-endpoint.example"
TELEGRAM_WEBHOOK_SECRET="random-secret-at-least-16-chars"
DATABASE_URL="postgresql://user:password@host/dbname"
```

`DATABASE_URL` is required on Vercel. The app also accepts `POSTGRES_URL`, `POSTGRES_PRISMA_URL`, or `POSTGRES_URL_NON_POOLING`.

## Install Locally

```sh
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

On Linux/macOS:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run Locally

Local mode uses SQLite and long polling:

```sh
python -m bot.main
```

The local database is created as `bot.db`.

## Deploy on Vercel

This project uses:

- `api/webhook.py` as the Vercel Python function
- `pyproject.toml` for the Vercel entrypoint
- `.python-version` to pin Python 3.12
- PostgreSQL for durable storage

After deploying, register the webhook:

```sh
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -d "url=https://YOUR-PROJECT.vercel.app/api/webhook" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}" \
  -d 'allowed_updates=["message","callback_query"]'
```

Check webhook status:

```sh
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
```

## Database

On Vercel, tables are created automatically on first use. You can also run `schema.sql` manually in your PostgreSQL console.

## Bot Commands

- `/start` - open the main menu
- `/help` - show usage help
- `/stats` - show the current user's usage
- `/admin` - owner-only bot statistics
- `/msg "message here"` - owner-only broadcast preview and confirmation
- `/errors` - owner-only recent error log

## Supported Publishers

- Financial Times
- Bloomberg
- Medium
- New York Times
- The Economist
- Washington Post
- Reuters
