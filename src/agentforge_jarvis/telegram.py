"""Optional Telegram adapter for the complete AgentForge service."""

from __future__ import annotations

import base64
import os
from pathlib import Path

from .engine import Engine
from .media import extract_image
from .models import ChatRequest
from .providers import Settings, public_error
from .storage import Store


def text_response(engine: Engine, team: str, message: str) -> str:
    if not message.strip():
        raise ValueError("Send a business question or a fictional workshop image.")
    return engine.chat(ChatRequest(team=team, message=message))["answer"]


def image_response(engine: Engine, team: str, data: bytes, mime: str) -> str:
    encoded = base64.b64encode(data).decode()
    text = extract_image(engine, team, encoded, mime)
    return (
        "EXTRACTED EVIDENCE FOR REVIEW\n"
        + text
        + "\n\nReview and correct this text in the local AgentForge app before saving it to memory."
    )


def build_engine() -> Engine:
    return Engine(Store(Path(".agentforge")), Settings.from_env())


def run() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    team = os.getenv("AGENTFORGE_TELEGRAM_TEAM", "telegram-workshop")
    engine = build_engine()

    from telegram.ext import Application, MessageHandler, filters

    async def handle_text(update, context):
        try:
            await update.message.reply_text(text_response(engine, team, update.message.text or ""))
        except Exception as error:
            await update.message.reply_text(public_error(error))

    async def handle_image(update, context):
        try:
            photo = update.message.photo[-1]
            remote = await photo.get_file()
            data = bytes(await remote.download_as_bytearray())
            await update.message.reply_text(image_response(engine, team, data, "image/jpeg"))
        except Exception as error:
            await update.message.reply_text(public_error(error))

    application = Application.builder().token(token).build()
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    try:
        application.run_polling()
    finally:
        engine.close()
