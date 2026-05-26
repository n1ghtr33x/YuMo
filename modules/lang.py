# -*- coding: utf-8 -*-

from pyrogram import Client, filters
from pyrogram.types import Message

from utils.i18n import available_langs, get_lang, set_lang, t
from utils.misc import modules_help, prefix


def _available() -> str:
    return ", ".join(available_langs())


@Client.on_message(filters.command("lang", prefix) & filters.me)
async def lang_cmd(_, message: Message):
    if len(message.command) == 1:
        await message.edit(
            t("i18n.current", lang=get_lang(), available=_available())
        )
        return

    lang = message.command[1].lower()

    if lang not in available_langs():
        await message.edit(
            t("i18n.unknown", lang=lang, available=_available())
        )
        return

    set_lang(lang)
    await message.edit(t("i18n.changed", lang=lang))


modules_help["lang"] = {
    "__meta__": {
        "version": "1.0.0",
        "description": t("i18n.meta.description"),
    },
    "lang [ru/en]": t("i18n.help.lang"),
}
