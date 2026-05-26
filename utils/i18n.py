from collections import UserDict
from typing import Any

from utils.db import db


DEFAULT_LANG = "ru"

STRINGS: dict[str, dict[str, str]] = {
    "ru": {
        "i18n.current": "<b>Текущий язык:</b> <code>{lang}</code>\n<b>Доступно:</b> <code>{available}</code>",
        "i18n.changed": "<b>Язык изменен на:</b> <code>{lang}</code>",
        "i18n.unknown": "<b>Неизвестный язык:</b> <code>{lang}</code>\n<b>Доступно:</b> <code>{available}</code>",
        "i18n.meta.description": "Настройка языка юзербота",
        "i18n.help.lang": "посмотреть или изменить язык.",
        "ping.wait": '<emoji id="6255963511252322252">✔️</emoji> понг..',
        "ping.done": '<emoji id="6255963511252322252">✔️</emoji> понг.. ({ms} ms)',
        "ping.inline.description": "Проверить работу inline",
        "ping.meta.description": "Проверка задержки соединения",
        "ping.help.ping": "проверить скорость отклика Telegram.",
    },
    "en": {
        "i18n.current": "<b>Current language:</b> <code>{lang}</code>\n<b>Available:</b> <code>{available}</code>",
        "i18n.changed": "<b>Language changed to:</b> <code>{lang}</code>",
        "i18n.unknown": "<b>Unknown language:</b> <code>{lang}</code>\n<b>Available:</b> <code>{available}</code>",
        "i18n.meta.description": "Userbot language settings",
        "i18n.help.lang": "show or change language.",
        "ping.wait": '<emoji id="6255963511252322252">✔️</emoji> pong..',
        "ping.done": '<emoji id="6255963511252322252">✔️</emoji> pong.. ({ms} ms)',
        "ping.inline.description": "Check inline response",
        "ping.meta.description": "Connection latency check",
        "ping.help.ping": "check Telegram response speed.",
    },
}


class _SafeFormatDict(UserDict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def available_langs() -> list[str]:
    return sorted(STRINGS)


def get_lang() -> str:
    lang = db.get("core.i18n", "lang", DEFAULT_LANG)
    return lang if lang in STRINGS else DEFAULT_LANG


def set_lang(lang: str) -> None:
    if lang not in STRINGS:
        raise ValueError(f"unknown language: {lang}")

    db.set("core.i18n", "lang", lang)


def t(key: str, lang: str | None = None, **kwargs: Any) -> str:
    lang = lang or get_lang()
    text = STRINGS.get(lang, {}).get(key)

    if text is None:
        text = STRINGS[DEFAULT_LANG].get(key, key)

    if kwargs:
        return text.format_map(_SafeFormatDict(kwargs))

    return text


_ = t
