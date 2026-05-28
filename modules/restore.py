# -*- coding: utf-8 -*-

import os
import zipfile
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message

from utils import config
from utils.i18n import Translator
from utils.misc import modules_help, prefix
from utils.scripts import restart

strings = {
    "ru": {
        "need_reply": "Ответь на backup .zip файл.",
        "bad_file": "Это не .zip backup.",
        "restoring": "Восстанавливаю backup...",
        "done": "Backup восстановлен. Перезапускаюсь...",
        "meta.description": "Восстановление backup YuMo",
        "help.restore": "восстановить backup из zip-файла.",
    },
    "en": {
        "need_reply": "Reply to a backup .zip file.",
        "bad_file": "This is not a .zip backup.",
        "restoring": "Restoring backup...",
        "done": "Backup restored. Restarting...",
        "meta.description": "Restore YuMo backup",
        "help.restore": "restore backup from zip file.",
    },
}

tr = Translator("restore", strings)
TMP = Path("/tmp/yumo_restore.zip")
ALLOWED_PREFIXES = (
    "modules/custom_modules/",
    "utils/config.py",
    ".env",
    "my_account.session",
    "inline_bot.session",
    getattr(config, "db_name", ""),
)


def _is_allowed(name: str) -> bool:
    clean = name.replace("\\", "/")
    return not clean.startswith("/") and ".." not in Path(clean).parts and any(
        prefix and (clean == prefix or clean.startswith(prefix))
        for prefix in ALLOWED_PREFIXES
    )


@Client.on_message(filters.command("restore", prefix) & filters.me)
async def restore_cmd(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.edit(tr("need_reply"))
        return

    document = message.reply_to_message.document
    if Path(document.file_name or "").suffix != ".zip":
        await message.edit(tr("bad_file"))
        return

    await message.edit(tr("restoring"))
    await client.download_media(document.file_id, str(TMP))

    with zipfile.ZipFile(TMP) as zipf:
        for member in zipf.infolist():
            if member.is_dir() or not _is_allowed(member.filename):
                continue
            target = Path(member.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipf.open(member) as src, open(target, "wb") as dst:
                dst.write(src.read())

    os.remove(TMP)
    await message.edit(f"<b>{tr('done')}</b>")
    restart()


modules_help["restore"] = {
    "__meta__": {"version": "1.0.0", "description": tr.lazy("meta.description")},
    "restore [reply to zip]": tr.lazy("help.restore"),
}
