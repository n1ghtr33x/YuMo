# -*- coding: utf-8 -*-

import ast
import difflib
import os
import shutil
import uuid
from datetime import datetime
from html import escape
from pathlib import Path

from pyrogram import Client, filters, errors
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from utils.db import db
from utils.i18n import Translator
from utils.inline import inline_command
from utils.misc import modules_help, prefix
from utils.scripts import (
    format_exc,
    load_module,
    parse_meta_file,
    restart,
    unload_module,
)

BASE_PATH = os.path.abspath(os.getcwd())
PENDING_DIR = Path("./yumo_loader")
_pending_modules = {}
_handlers_registered = False
_owner_id = None

strings = {
    "ru": {
        "download": "Скачивание модуля...",
        "not_module": "Это не Python-модуль.",
        "no_reply": "Ответь на файл модуля.",
        "no_bot": "<b>Inline-бот не запущен.</b>\nДобавь <code>bot_token</code> в конфиг, чтобы loader preview работал.",
        "inline_empty": "<b>Inline-бот не вернул preview модуля.</b>",
        "inline_error": "<b>Не удалось открыть preview:</b> <code>{error}</code>",
        "owner_only": "Это меню не для тебя.",
        "expired": "Preview устарел. Отправь .loadmod заново.",
        "title": "Preview модуля",
        "module": "Модуль",
        "file": "Файл",
        "version": "Версия",
        "description": "Описание",
        "author": "Автор",
        "requires": "Зависимости",
        "warnings": "Предупреждения",
        "warnings_none": "нет",
        "diff": "Diff",
        "diff_none": "нет изменений / новый модуль",
        "requires_none": "нет",
        "installing": "Загрузка модуля...",
        "installed": "Модуль {module} загружен. Перезапускаюсь...",
        "cancelled": "Загрузка отменена.",
        "code_sent": "Код отправлен в чат.",
        "btn.install": "Загрузить",
        "btn.code": "Код",
        "btn.cancel": "Отмена",
        "meta.description": "Загрузка и управление модулями",
        "help.load": "показать preview модуля и загрузить его кнопкой.",
        "help.unload": "выгрузить и удалить модуль.",
        "help.del_all": "удалить все кастомные модули.",
    },
    "en": {
        "download": "Downloading module...",
        "not_module": "This is not a Python module.",
        "no_reply": "Reply to a module file.",
        "no_bot": "<b>Inline bot is not running.</b>\nAdd <code>bot_token</code> to config to use loader preview.",
        "inline_empty": "<b>Inline bot did not return module preview.</b>",
        "inline_error": "<b>Failed to open preview:</b> <code>{error}</code>",
        "owner_only": "This menu is not yours.",
        "expired": "Preview expired. Send .loadmod again.",
        "title": "Module preview",
        "module": "Module",
        "file": "File",
        "version": "Version",
        "description": "Description",
        "author": "Author",
        "requires": "Dependencies",
        "warnings": "Warnings",
        "warnings_none": "none",
        "diff": "Diff",
        "diff_none": "no changes / new module",
        "requires_none": "none",
        "installing": "Loading module...",
        "installed": "Module {module} loaded. Restarting...",
        "cancelled": "Loading cancelled.",
        "code_sent": "Code sent to chat.",
        "btn.install": "Load",
        "btn.code": "Code",
        "btn.cancel": "Cancel",
        "meta.description": "Module loading and management",
        "help.load": "show module preview and load it with a button.",
        "help.unload": "unload and delete module.",
        "help.del_all": "delete all custom modules.",
    },
}

tr = Translator("loader", strings)

TOP = "╭─────────────────────"
MID = "├─────────────────────"
BOT = "╰─────────────────────"
ITEM = "│"


def _target_path(module_name: str) -> Path:
    return Path("modules/custom_modules") / f"{module_name}.py"


def _backup_path(module_name: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("backups/modules") / f"{module_name}_{stamp}.py"


def _scan_dangerous(path: str) -> list[str]:
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]

    warnings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    warnings.append("import subprocess")

        elif isinstance(node, ast.ImportFrom):
            if node.module == "subprocess":
                warnings.append("from subprocess import ...")

        elif isinstance(node, ast.Call):
            func = node.func

            if isinstance(func, ast.Name) and func.id in {"eval", "exec"}:
                warnings.append(f"{func.id}(...)")

            elif isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name) and func.value.id == "os" and func.attr in {"remove", "unlink", "rmdir", "removedirs"}:
                    warnings.append(f"os.{func.attr}(...)")

    return sorted(set(warnings))


def _format_diff(old_path: Path, new_path: Path) -> str:
    if not old_path.exists():
        return tr("diff_none")

    old_lines = old_path.read_text(encoding="utf-8", errors="replace").splitlines()
    new_lines = new_path.read_text(encoding="utf-8", errors="replace").splitlines()
    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=str(old_path),
        tofile=new_path.name,
        lineterm="",
        n=2,
    ))

    if not diff:
        return tr("diff_none")

    text = "\n".join(diff[:40])
    if len(diff) > 40:
        text += "\n..."

    return text[-1800:]


def _safe_file_name(name: str) -> str:
    return os.path.basename(name).replace("/", "_")


def _module_name(file_name: str) -> str:
    return Path(file_name).stem


def _preview_text(pending_id: str) -> str:
    data = _pending_modules[pending_id]
    meta = data["meta"]
    requires = meta.get("requires", "").strip() or tr("requires_none")
    warnings = ", ".join(data["warnings"]) or tr("warnings_none")
    diff = data["diff"]

    return (
        f"{TOP}\n"
        f"{ITEM} <b>{tr('title')}</b>\n"
        f"{MID}\n"
        f"{ITEM} <b>{tr('module')}:</b> <code>{data['module_name']}</code>\n"
        f"{ITEM} <b>{tr('file')}:</b> <code>{escape(data['file_name'])}</code>\n"
        f"{ITEM} <b>{tr('version')}:</b> <code>{escape(meta.get('version', 'unknown'))}</code>\n"
        f"{ITEM} <b>{tr('description')}:</b> <i>{escape(meta.get('description', '-'))}</i>\n"
        f"{ITEM} <b>{tr('author')}:</b> <code>{escape(meta.get('author', '-'))}</code>\n"
        f"{MID}\n"
        f"{ITEM} <b>{tr('requires')}:</b> <code>{escape(requires)}</code>\n"
        f"{ITEM} <b>{tr('warnings')}:</b> <code>{escape(warnings)}</code>\n"
        f"{MID}\n"
        f"{ITEM} <b>{tr('diff')}:</b>\n<code>{escape(diff)}</code>\n"
        f"{BOT}"
    )


def _preview_markup(pending_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(tr("btn.install"), callback_data=f"loader:install:{pending_id}")],
            [InlineKeyboardButton(tr("btn.code"), callback_data=f"loader:code:{pending_id}")],
            [InlineKeyboardButton(tr("btn.cancel"), callback_data=f"loader:cancel:{pending_id}")],
        ]
    )


def _remove_pending(pending_id: str) -> None:
    data = _pending_modules.pop(pending_id, None)
    if data and os.path.exists(data["path"]):
        os.remove(data["path"])


async def _edit_callback_text(client: Client, callback, text: str) -> None:
    if callback.message:
        await callback.message.edit_text(text)
        return

    await client.edit_inline_text(callback.inline_message_id, text)


def _register_loader_handlers(app: Client, owner_id: int) -> bool:
    global _handlers_registered, _owner_id

    bot = getattr(app, "bot", None)
    if not bot:
        return False

    _owner_id = owner_id

    if _handlers_registered:
        return True

    _handlers_registered = True

    @bot.on_callback_query(filters.regex(r"^loader:"))
    async def loader_callback(client, callback):
        if _owner_id and callback.from_user.id != _owner_id:
            await callback.answer(tr("owner_only"), show_alert=True)
            return

        try:
            _, action, pending_id = callback.data.split(":", 2)
            data = _pending_modules.get(pending_id)

            if not data:
                await callback.answer(tr("expired"), show_alert=True)
                return

            if action == "cancel":
                _remove_pending(pending_id)
                await _edit_callback_text(client, callback, f"<b>{tr('cancelled')}</b>")
                await callback.answer()
                return

            if action == "code":
                await app.send_document(data["chat_id"], data["path"], caption=_preview_text(pending_id))
                await callback.answer(tr("code_sent"))
                return

            if action == "install":
                app_client = getattr(client, "userbot", app)
                module_name = data["module_name"]
                target = _target_path(module_name)
                target.parent.mkdir(parents=True, exist_ok=True)

                await _edit_callback_text(client, callback, f"<b>{tr('installing')}</b>")

                if target.exists():
                    backup = _backup_path(module_name)
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup)

                shutil.move(data["path"], target)
                _pending_modules.pop(pending_id, None)

                disabled_modules = set(db.get("core.modules", "disabled", []))
                if module_name in disabled_modules:
                    disabled_modules.discard(module_name)
                    db.set("core.modules", "disabled", sorted(disabled_modules))

                try:
                    await load_module(module_name, app_client)
                except Exception as e:
                    return await _edit_callback_text(client, callback, format_exc(e))

                await _edit_callback_text(
                    client,
                    callback,
                    f"<b>{tr('installed', module=module_name)}</b>",
                )
                await callback.answer()
                restart()

        except errors.MessageNotModified:
            await callback.answer()
        except Exception as e:
            await callback.answer(str(e), show_alert=True)

    return True


@inline_command("loadmod", tr("meta.description"))
async def inline_loadmod(app: Client, query, args):
    pending_id = args.strip()
    _register_loader_handlers(app, query.from_user.id)

    if pending_id not in _pending_modules:
        return [
            InlineQueryResultArticle(
                title=tr("expired"),
                description=pending_id,
                input_message_content=InputTextMessageContent(f"<b>{tr('expired')}</b>"),
            )
        ]

    return [
        InlineQueryResultArticle(
            title=f"{tr('title')}: {_pending_modules[pending_id]['module_name']}",
            description=_pending_modules[pending_id]["file_name"],
            input_message_content=InputTextMessageContent(_preview_text(pending_id)),
            reply_markup=_preview_markup(pending_id),
        )
    ]


@Client.on_message(filters.command(["loadmod", "lm"], prefix) & filters.me)
async def loadmod(client: Client, message: Message):
    if not message.reply_to_message:
        await message.edit(tr("no_reply"))
        return

    document = message.reply_to_message.document
    if not document or Path(document.file_name or "").suffix != ".py":
        await message.edit(tr("not_module"))
        return

    if not _register_loader_handlers(client, message.from_user.id):
        await message.edit(tr("no_bot"))
        return

    await message.edit(tr("download"))

    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    file_name = _safe_file_name(document.file_name)
    pending_id = uuid.uuid4().hex[:10]
    pending_path = PENDING_DIR / f"{pending_id}_{file_name}"

    await client.download_media(document.file_id, str(pending_path))

    _pending_modules[pending_id] = {
        "path": str(pending_path),
        "file_name": file_name,
        "module_name": _module_name(file_name),
        "meta": parse_meta_file(str(pending_path)),
        "warnings": _scan_dangerous(str(pending_path)),
        "diff": _format_diff(_target_path(_module_name(file_name)), pending_path),
        "chat_id": message.chat.id,
        "message_id": message.id,
        "user_id": message.from_user.id,
    }

    try:
        bot_me = await client.bot.get_me()
        results = await client.get_inline_bot_results(
            bot_me.username,
            f"loadmod {pending_id}",
        )

        if not results.results:
            await message.edit(tr("inline_empty"))
            _remove_pending(pending_id)
            return

        await client.send_inline_bot_result(
            message.chat.id,
            results.query_id,
            results.results[0].id,
            reply_to_message_id=message.reply_to_message_id,
        )
        await message.delete()
    except Exception as e:
        _remove_pending(pending_id)
        await message.edit(tr("inline_error", error=escape(str(e))))


@Client.on_message(filters.command(["unloadmod", "ulm"], prefix) & filters.me)
async def unload_mods(client: Client, message: Message):
    if len(message.command) <= 1:
        return await message.edit("<b>Выбери модуль для выгрузки\n<code>.unloadmod</code> [module name] </b>")

    module_name = message.command[1].lower()

    if os.path.exists(f"{BASE_PATH}/modules/custom_modules/{module_name}.py"):
        try:
            await unload_module(module_name, client)
        except Exception as e:
            return await message.edit(format_exc(e))

        os.remove(f"{BASE_PATH}/modules/custom_modules/{module_name}.py")
        await message.edit(
            f"<b>Модуль <code>{module_name}</code> выгружен и удален!</b>")


@Client.on_message(filters.command("del_all", prefix) & filters.me)
async def del_all(_, message: Message):
    await message.edit("Удаление..")
    db.set(
        "core.updater",
        "restart_info",
        {
            "type": "dellmodule",
            "chat_id": message.chat.id,
            "message_id": message.id,
        },
    )
    files = os.listdir("modules/custom_modules")
    if files:
        for i in files:
            if len(i.split(".")) == 2:
                os.remove(f"modules/custom_modules/{i}")
    restart()


modules_help["loader"] = {
    "__meta__": {
        "version": "1.1.0",
        "description": tr.lazy("meta.description"),
        "pic": "https://i.ibb.co/FbNycfVQ/loader.png",
    },
    "loadmod/lm [ответ на модуль]": tr.lazy("help.load"),
    "unloadmod/ulm [название модуля]": tr.lazy("help.unload"),
    "del_all": tr.lazy("help.del_all"),
}
