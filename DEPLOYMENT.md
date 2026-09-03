# Deploy to Vercel

Create a separate Vercel project with `paywalled-articles` as its Root Directory. The static root page is intentionally only a status page; Telegram calls `/api/webhook`.

1. Provision a Neon (or another PostgreSQL) database in the Vercel Marketplace and add its pooled connection string as `DATABASE_URL`. The app also accepts Vercel-style `POSTGRES_URL`, `POSTGRES_PRISMA_URL`, or `POSTGRES_URL_NON_POOLING`.
2. Run `schema.sql` once in that database.
3. Add `BOT_TOKEN`, `ADMIN_ID`, `ARTICLE_ENDPOINT`, and a random `TELEGRAM_WEBHOOK_SECRET` (at least 16 characters) as Production environment variables.
4. Deploy. Then register the production URL with Telegram (substitute values, and URL-encode the secret if needed):

```sh
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -d "url=https://YOUR-PROJECT.vercel.app/api/webhook" \
  -d "secret_token=$TELEGRAM_WEBHOOK_SECRET" \
  -d 'allowed_updates=["message","callback_query"]'
```

Do not run `bot/main.py` on Vercel: it is retained only for local long-polling development. Vercel invokes the webhook on demand, so no cron job is required.
