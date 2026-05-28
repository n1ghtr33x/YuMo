# -*- coding: utf-8 -*-

import asyncio
from html import escape

from pyrogram import Client, filters
from pyrogram.types import Message

from utils.db import db
from utils.misc import modules_help, prefix
from utils.scripts import restart
from utils.i18n import Translator

strings = {
    "ru": {
        "git.not_return": 'Git не вернул вывод.',
        "updating": 'Обновление через git pull...',
        "toolong": "Git pull выполнялся слишком долго и был остановлен.",
        "git.not_found": "Git не установлен или недоступен.",
        "meta.description": "Обновление YuMo через git pull и перезапуск",
        "git.error": "Не удалось обновиться через git pull.",
        "git.succeful": "Обновление установлено. Перезапускаюсь...",
        "meta.help": "обновить YuMo",
    },
    "en": {
        "git_not_return": 'Git did not return any output.',
        "updating": 'Updating via git pull...',
        "toolong": "Git pull took too long and was stopped.",
        "git.not_found": "Git is not installed or unavailable.",
        "meta.description": "Updating YuMo via git pull and restarting.",
        "git.error": "Failed to update via git pull.",
        "git.succeful": "Update installed. Restarting...",
        "meta.help": "updade YuMo",
    },
}

tr = Translator("update", strings)


MAX_OUTPUT_LENGTH = 3000


def _format_output(stdout: str, stderr: str) -> str:
    output = "\n".join(part for part in (stdout.strip(), stderr.strip()) if part)

    if not output:
        return tr("git.not_return")

    if len(output) > MAX_OUTPUT_LENGTH:
        output = output[-MAX_OUTPUT_LENGTH:]

    return escape(output)


@Client.on_message(filters.command(["update", "pull", "upd"], prefix) & filters.me)
async def update_cmd(_, message: Message):
    await message.edit(f"<b>{tr("updating")}</b>")

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
            f"<b>{tr("toolong")}</b>"
        )
    except FileNotFoundError:
        return await message.edit(f"<b>{"git.not_found"}</b>")

    stdout = stdout_bytes.decode(errors="replace")
    stderr = stderr_bytes.decode(errors="replace")
    output = _format_output(stdout, stderr)

    if proc.returncode != 0:
        return await message.edit(
            f"<b>{tr("git.error")}</b>\n\n"
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
        f"<b>{tr("git.succeful")}</b>\n\n"
        f"<code>{output}</code>"
    )
    restart()


modules_help["update"] = {
    "__meta__": {
        "version": "1.0.0",
        "description": tr.lazy("meta.description"),
        "pic": "https://i.ibb.co/xSR9fQHH/restart.png",
    },
    "update/pull": tr.lazy("meta.help"),
}
