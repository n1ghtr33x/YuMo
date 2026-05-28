# -*- coding: utf-8 -*-

import importlib
import os
import shutil
import subprocess
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message

from utils import config
from utils.db import db
from utils.i18n import Translator, available_langs, get_lang
from utils.misc import modules_help, prefix

strings = {
    "ru": {
        "title": "YuMo Doctor",
        "ok": "OK",
        "bad": "FAIL",
        "meta.description": "Проверка состояния YuMo",
        "help.doctor": "проверить inline-бота, БД, git, папки и зависимости.",
    },
    "en": {
        "title": "YuMo Doctor",
        "ok": "OK",
        "bad": "FAIL",
        "meta.description": "YuMo health checks",
        "help.doctor": "check inline bot, DB, git, folders, and dependencies.",
    },
}

tr = Translator("doctor", strings)


def _missing_requirements() -> list[str]:
    req = Path("requirements.txt")
    if not req.exists():
        return []

    missing = []
    for line in req.read_text(encoding="utf-8", errors="replace").splitlines():
        package = line.strip()
        if not package or package.startswith("#"):
            continue
        name = package.split("==")[0].split(">=")[0].split("<=")[0].replace("-", "_")
        try:
            importlib.import_module(name)
        except Exception:
            missing.append(package)
    return missing


def _mark(value: bool) -> str:
    return tr("ok") if value else tr("bad")


@Client.on_message(filters.command("doctor", prefix) & filters.me)
async def doctor_cmd(client: Client, message: Message):
    checks = []
    checks.append(("bot_token", bool(getattr(config, "bot_token", None))))
    checks.append(("inline_bot", bool(getattr(client, "bot", None))))

    try:
        db.set("core.doctor", "ping", "pong")
        checks.append(("database", db.get("core.doctor", "ping") == "pong"))
    except Exception:
        checks.append(("database", False))

    checks.append(("git", shutil.which("git") is not None))
    try:
        git_ok = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, timeout=5).returncode == 0
    except Exception:
        git_ok = False
    checks.append(("git_repo", git_ok))

    checks.append(("custom_modules_dir", Path("modules/custom_modules").exists()))
    checks.append(("backups_dir", Path("backups").exists() or os.access(".", os.W_OK)))
    checks.append(("language", get_lang() in available_langs()))
    missing_requirements = _missing_requirements()
    checks.append(("dependencies", not missing_requirements))

    disabled = db.get("core.modules", "disabled", [])
    text = f"<b>{tr('title')}</b>\n\n"
    for name, ok in checks:
        text += f"<b>{name}:</b> <code>{_mark(ok)}</code>\n"
    text += f"\n<b>disabled modules:</b> <code>{', '.join(disabled) or '-'}</code>"
    text += f"\n<b>missing deps:</b> <code>{', '.join(missing_requirements) or '-'}</code>"

    await message.edit(text)


modules_help["doctor"] = {
    "__meta__": {"version": "1.0.0", "description": tr.lazy("meta.description")},
    "doctor": tr.lazy("help.doctor"),
}
