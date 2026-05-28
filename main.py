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
from utils.inline import setup_inline


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
    device_model="YuMo UserBot",
    system_version=platform.version() + " " + platform.machine(),
    sleep_threshold=30,
    test_mode=config.test_server,
    parse_mode=ParseMode.HTML,
)


bot = None

if getattr(config, "bot_token", None):
    bot = Client(
        "inline_bot",
        api_id=config.api_id,
        api_hash=config.api_hash,
        bot_token=config.bot_token,
        hide_password=False,
        workdir=script_path,
        app_version=userbot_version,
        device_model="YuMo Inline Bot",
        system_version=platform.version() + " " + platform.machine(),
        sleep_threshold=30,
        test_mode=config.test_server,
        parse_mode=ParseMode.HTML,
    )


async def main():
    global bot

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

    app.bot = None

    if bot:
        try:
            await bot.start()

            app.bot = bot
            bot.userbot = app

            logging.info("Inline bot started!")

        except Exception:
            logging.warning("Can't start inline bot", exc_info=True)
            bot = None
            app.bot = None

    success_modules = 0
    failed_modules = 0
    skipped_modules = 0
    disabled_modules = set(db.get("core.modules", "disabled", []))

    for path in Path("modules").rglob("*.py"):
        if path.stem in disabled_modules:
            logging.info(f"Skipped disabled module {path.stem}")
            skipped_modules += 1
            continue

        try:
            await load_module(
                path.stem,
                app,
                core="custom_modules" not in path.parent.parts,
            )
        except Exception:
            logging.warning(f"Can't import module {path.stem}", exc_info=True)
            failed_modules += 1
        else:
            success_modules += 1

    logging.info(f"Imported {success_modules} modules")

    if skipped_modules:
        logging.info(f"Skipped {skipped_modules} disabled modules")

    if failed_modules:
        logging.warning(f"Failed to import {failed_modules} modules")
    
    await setup_inline(app, app.bot)

    if info := db.get("core.updater", "restart_info"):
        text = {
            "restart": "<b>Успешная перезагрузка!</b>",
            "update": "<b>Обновление успешно установлено!</b>",
            "loadmodule": "<b>Модуль успешно загружен!</b>",
            "dellmodule": "<b>Все модули успешно удалены!</b>",
        }[info["type"]]

        try:
            await app.edit_message_text(
                info["chat_id"],
                info["message_id"],
                text,
            )
        except Exception as e:
            logging.warning(f"Can't edit restart message: {e}")
        finally:
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

    if bot:
        await bot.stop()

    await app.stop()


if __name__ == "__main__":
    app.run(main())