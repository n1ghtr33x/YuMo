# -*- coding: utf-8 -*-

import os
import uuid

from pyrogram import Client, filters, errors
from pyrogram.types import (
    Message,
    InlineQueryResultArticle,
    InlineQueryResultCachedDocument,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from utils.misc import modules_help, prefix
from utils.inline import inline_command
from utils.scripts import (
    format_exc,
    format_module_help,
    format_small_module_help,
)


_handlers_registered = False
_inline_results = {}
_file_cache = {}


def get_module_path(module_name: str):
    for path in (
        f"modules/{module_name}.py",
        f"modules/custom_modules/{module_name}.py",
    ):
        if os.path.isfile(path):
            return path
    return None


def get_module_help_text(module_name: str):
    text = format_module_help(module_name)
    if len(text) >= 1024:
        text = format_small_module_help(module_name)
    return text


def get_sendmod_keyboard(result_id: str):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "ℹ️ Инфо",
                    callback_data=f"sendmod:info:{result_id}",
                )
            ]
        ]
    )


async def get_cached_document_file_id(app, module_name: str, module_path: str):
    bot = app.bot

    cache_key = f"{module_name}:{os.path.getmtime(module_path)}"

    if cache_key in _file_cache:
        return _file_cache[cache_key]

    me = await app.get_me()

    msg = await bot.send_document(me.id, module_path)
    file_id = msg.document.file_id

    _file_cache.clear()
    _file_cache[cache_key] = file_id

    await msg.delete()

    return file_id


def register_sendmod_handlers(app):
    global _handlers_registered

    if _handlers_registered:
        return

    bot = getattr(app, "bot", None)
    if not bot:
        return

    _handlers_registered = True

    @bot.on_callback_query(filters.regex(r"^sendmod:info:"))
    async def sendmod_callback(client, callback):
        try:
            _, _, result_id = callback.data.split(":", 2)

            data = _inline_results.get(result_id)
            if not data:
                await callback.answer(
                    "Данные inline-сообщения не найдены",
                    show_alert=True,
                )
                return
            
            if callback.from_user.id != data["user_id"]:
                await callback.answer(
                    "Это не ваше inline-сообщение",
                    show_alert=True,
                )
                return

            module_name = data["module_name"]

            if module_name not in modules_help:
                await callback.answer("Модуль не найден", show_alert=True)
                return

            text = get_module_help_text(module_name)
            markup = get_sendmod_keyboard(result_id)

            try:
                if callback.message:
                    if callback.message.text == text:
                        await callback.answer("Информация уже открыта")
                        return

                    await callback.message.edit_text(
                        text,
                        reply_markup=markup,
                    )
                else:
                    await client.edit_inline_text(
                        callback.inline_message_id,
                        text,
                        reply_markup=markup,
                    )

                await callback.answer()

            except errors.MessageNotModified:
                await callback.answer("Информация уже открыта")

        except Exception as e:
            await callback.answer(str(e), show_alert=True)


@Client.on_message(filters.command(["sendmod", "sm"], prefix) & filters.me)
async def sendmod(client: Client, message: Message):
    if len(message.command) == 1:
        await message.edit("<b>Пожалуйста введите имя модуля!</b>")
        return

    await message.edit("<b>Загрузка...</b>")

    try:
        module_name = message.command[1]

        if module_name not in modules_help:
            await message.edit(
                f"<b>Модуль <code>{module_name}</code> не найден!</b>"
            )
            return

        module_path = get_module_path(module_name)

        if not module_path:
            await message.edit(
                f"<b>Файл модуля <code>{module_name}</code> не найден!</b>"
            )
            return

        await client.send_document(
            message.chat.id,
            module_path,
            caption=get_module_help_text(module_name),
        )

        await message.delete()

    except Exception as e:
        await message.edit(format_exc(e))


@inline_command("sendmod", "Отправить модуль через inline")
async def inline_sendmod(app, query, args):
    register_sendmod_handlers(app)

    module_name = args.strip()

    if not module_name:
        return [
            InlineQueryResultArticle(
                title="Укажи имя модуля",
                description="Пример: sendmod ping",
                input_message_content=InputTextMessageContent(
                    "<b>Использование:</b> <code>sendmod [module_name]</code>"
                ),
            )
        ]

    if module_name not in modules_help:
        return [
            InlineQueryResultArticle(
                title="Модуль не найден",
                description=module_name,
                input_message_content=InputTextMessageContent(
                    f"<b>Модуль <code>{module_name}</code> не найден!</b>"
                ),
            )
        ]

    module_path = get_module_path(module_name)

    if not module_path:
        return [
            InlineQueryResultArticle(
                title="Файл модуля не найден",
                description=f"{module_name}.py",
                input_message_content=InputTextMessageContent(
                    f"<b>Файл модуля <code>{module_name}</code> не найден!</b>"
                ),
            )
        ]

    result_id = f"sendmod_{module_name}_{query.from_user.id}_{uuid.uuid4().hex[:8]}"

    _inline_results[result_id] = {
        "module_name": module_name,
        "user_id": query.from_user.id,
    }

    file_id = await get_cached_document_file_id(app, module_name, module_path)

    return [
        InlineQueryResultCachedDocument(
            id=result_id,
            title=f"📦 {module_name}",
            document_file_id=file_id,
            description="Отправить файл модуля",
            caption=get_module_help_text(module_name),
            reply_markup=get_sendmod_keyboard(result_id),
        )
    ]


modules_help["sendmod"] = {
    "__meta__": {
        "version": "1.0.0",
        "description": "Отправка модулей юзербота в чат",
        "pic": "https://i.ibb.co/xtHGHQZ1/sendmod.png",
    },
    "sendmod [module_name]": "отправить модуль в чат.",
}