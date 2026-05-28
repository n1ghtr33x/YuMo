# -*- coding: utf-8 -*-

import os
import zipfile
from datetime import datetime
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message

from utils import config
from utils.i18n import Translator
from utils.misc import modules_help, prefix

strings = {
    "ru": {
        "creating": "Создаю backup...",
        "done": "Backup готов",
        "meta.description": "Backup базы, конфига и кастомных модулей",
        "help.backup": "создать архив backup и отправить его в чат.",
    },
    "en": {
        "creating": "Creating backup...",
        "done": "Backup ready",
        "meta.description": "Backup DB, config, and custom modules",
        "help.backup": "create backup archive and send it to chat.",
    },
}

tr = Translator("backup", strings)
BACKUP_DIR = Path("backups")


def _add_file(zipf: zipfile.ZipFile, path: Path) -> None:
    if path.exists() and path.is_file():
        zipf.write(path, path.as_posix())


def _add_dir(zipf: zipfile.ZipFile, path: Path) -> None:
    if not path.exists():
        return
    for file in path.rglob("*"):
        if file.is_file():
            zipf.write(file, file.as_posix())


@Client.on_message(filters.command("backup", prefix) & filters.me)
async def backup_cmd(client: Client, message: Message):
    await message.edit(tr("creating"))
    BACKUP_DIR.mkdir(exist_ok=True)
    archive = BACKUP_DIR / f"yumo_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        _add_file(zipf, Path(".env"))
        _add_file(zipf, Path("utils/config.py"))
        _add_file(zipf, Path(getattr(config, "db_name", "")))
        _add_file(zipf, Path("my_account.session"))
        _add_file(zipf, Path("inline_bot.session"))
        _add_dir(zipf, Path("modules/custom_modules"))

    await client.send_document(message.chat.id, str(archive), caption=tr("done"))
    await message.delete()


modules_help["backup"] = {
    "__meta__": {"version": "1.0.0", "description": tr.lazy("meta.description")},
    "backup": tr.lazy("help.backup"),
}
