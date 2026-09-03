"""Telegram webhook entry point for Vercel."""
import asyncio
import json
import logging
import os
from http.server import BaseHTTPRequestHandler

from telegram import Update
from bot.main import build_application


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._respond(200, {"ok": True, "service": "paywalled-articles webhook"})

    def do_POST(self):
        secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
        if not secret or self.headers.get("X-Telegram-Bot-Api-Secret-Token") != secret:
            self._respond(401, {"ok": False})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size))
            asyncio.run(self._process(payload))
        except Exception:
            logging.exception("Failed to process Telegram update")
            self._respond(500, {"ok": False})
            return
        self._respond(200, {"ok": True})

    async def _process(self, payload):
        app = build_application()
        async with app:
            await app.process_update(Update.de_json(payload, app.bot))

    def _respond(self, status, body):
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
