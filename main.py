import os
import logging
import sqlite3
import platform
import subprocess
from pathlib import Path

from pyrogram import Client, idle, errors
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.raw.functions.account import GetAuthorizations, DeleteAccount

from utils import config
from utils.db import db
from utils.misc import userbot_version
from utils.scripts import restart, load_module

script_path = os.path.dirname(os.path.realpath(__file__))
if script_path != os.getcwd():
    os.chdir(script_path)

app = Client(
    "my_account",
    api_id=config.api_id,
    api_hash=config.api_hash,
    hide_password=False,
    workdir=script_path,
    app_version=userbot_version,
    device_model=f"YuMo UserBot",
    system_version=platform.version() + " " + platform.machine(),
    sleep_threshold=30,
    test_mode=config.test_server,
    parse_mode=ParseMode.HTML,
)


async def main():
    logging.basicConfig(level=logging.INFO)
    DeleteAccount.__new__ = None

    try:
        await app.start()
    except sqlite3.OperationalError as e:
        if str(e) == "database is locked" and os.name == "posix":
            logging.warning(
                "Session file is locked. Trying to kill blocking process..."
            )
            subprocess.run(["fuser", "-k", "my_account.session"])
            restart()
        raise
    except (errors.NotAcceptable, errors.Unauthorized) as e:
        logging.error(
            f"{e.__class__.__name__}: {e}\n"
            f"Moving session file to my_account.session-old..."
        )
        os.rename("./my_account.session", "./my_account.session-old")
        restart()

    success_modules = 0
    failed_modules = 0

    for path in Path("modules").rglob("*.py"):
        try:
            await load_module(
                path.stem, app, core="custom_modules" not in path.parent.parts
            )
        except Exception:
            logging.warning(f"Can't import module {path.stem}", exc_info=True)
            failed_modules += 1
        else:
            success_modules += 1

    logging.info(f"Imported {success_modules} modules")
    if failed_modules:
        logging.warning(f"Failed to import {failed_modules} modules")

    if info := db.get("core.updater", "restart_info"):
        text = {
            "restart": "<b>Успешная перезагрузка!</b>",
            "update": "<b>Update process completed!</b>",
            "loadmodule": "<b>Модуль успешно загружен!</b>",
            "dellmodule": "<b>Все модули успешно удалены!</b>"
        }[info["type"]]
        try:
            await app.edit_message_text(
                info["chat_id"], info["message_id"], text
            )
        except errors.RPCError:
            pass
        db.remove("core.updater", "restart_info")

    if db.get("core.sessionkiller", "enabled", False):
        db.set(
            "core.sessionkiller",
            "auths_hashes",
            [
                auth.hash
                for auth in (
                    await app.invoke(GetAuthorizations())
                ).authorizations
            ],
        )

    logging.info("YuMo Userbot started!")

    await idle()

    await app.stop()


if __name__ == "__main__":
    app.run(main())
