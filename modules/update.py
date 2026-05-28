# -*- coding: utf-8 -*-

import asyncio
from html import escape

from pyrogram import Client, filters
from pyrogram.types import Message

from utils.db import db
from utils.misc import modules_help, prefix
from utils.scripts import restart


MAX_OUTPUT_LENGTH = 3000


def _format_output(stdout: str, stderr: str) -> str:
    output = "\n".join(part for part in (stdout.strip(), stderr.strip()) if part)

    if not output:
        return "Git не вернул вывод."

    if len(output) > MAX_OUTPUT_LENGTH:
        output = output[-MAX_OUTPUT_LENGTH:]

    return escape(output)


@Client.on_message(filters.command(["update", "pull"], prefix) & filters.me)
async def update_cmd(_, message: Message):
    await message.edit("<b>Обновление через git pull...</b>")

    proc = None

    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "pull",
            "--ff-only",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=120,
        )
    except asyncio.TimeoutError:
        if proc:
            proc.kill()
            await proc.wait()

        return await message.edit(
            "<b>Git pull выполнялся слишком долго и был остановлен.</b>"
        )
    except FileNotFoundError:
        return await message.edit("<b>Git не установлен или недоступен.</b>")

    stdout = stdout_bytes.decode(errors="replace")
    stderr = stderr_bytes.decode(errors="replace")
    output = _format_output(stdout, stderr)

    if proc.returncode != 0:
        return await message.edit(
            "<b>Не удалось обновиться через git pull.</b>\n\n"
            f"<code>{output}</code>"
        )

    db.set(
        "core.updater",
        "restart_info",
        {
            "type": "update",
            "chat_id": message.chat.id,
            "message_id": message.id,
        },
    )

    await message.edit(
        "<b>Обновление установлено. Перезапускаюсь...</b>\n\n"
        f"<code>{output}</code>"
    )
    restart()


modules_help["update"] = {
    "__meta__": {
        "version": "1.0.0",
        "description": "Обновление YuMo через git pull и перезапуск",
        "pic": "https://i.ibb.co/xSR9fQHH/restart.png",
    },
    "update/pull": "обновить YuMo",
}
