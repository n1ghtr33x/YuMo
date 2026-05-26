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
    },
    "en": {
        "i18n.current": "<b>Current language:</b> <code>{lang}</code>\n<b>Available:</b> <code>{available}</code>",
        "i18n.changed": "<b>Language changed to:</b> <code>{lang}</code>",
        "i18n.unknown": "<b>Unknown language:</b> <code>{lang}</code>\n<b>Available:</b> <code>{available}</code>",
        "i18n.meta.description": "Userbot language settings",
        "i18n.help.lang": "show or change language.",
    },
}

MODULE_STRINGS: dict[str, dict[str, dict[str, str]]] = {}


class _SafeFormatDict(UserDict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _format(text: str, kwargs: dict[str, Any]) -> str:
    if not kwargs:
        return text

    return text.format_map(_SafeFormatDict(kwargs))


def available_langs() -> list[str]:
    langs = set(STRINGS)

    for module_strings in MODULE_STRINGS.values():
        langs.update(module_strings)

    return sorted(langs)


def get_lang() -> str:
    lang = db.get("core.i18n", "lang", DEFAULT_LANG)
    return lang if lang in available_langs() else DEFAULT_LANG


def set_lang(lang: str) -> None:
    if lang not in available_langs():
        raise ValueError(f"unknown language: {lang}")

    db.set("core.i18n", "lang", lang)


def register_module_strings(
    module_name: str,
    strings: dict[str, dict[str, str]],
) -> None:
    MODULE_STRINGS[module_name] = strings


def t(key: str, locale: str | None = None, **kwargs: Any) -> str:
    locale = locale or get_lang()
    text = STRINGS.get(locale, {}).get(key)

    if text is None:
        text = STRINGS[DEFAULT_LANG].get(key, key)

    return _format(text, kwargs)


class Translator:
    def __init__(self, module_name: str, strings: dict[str, dict[str, str]]):
        self.module_name = module_name
        register_module_strings(module_name, strings)

    def __call__(
        self,
        key: str,
        locale: str | None = None,
        **kwargs: Any,
    ) -> str:
        locale = locale or get_lang()
        module_strings = MODULE_STRINGS.get(self.module_name, {})
        text = module_strings.get(locale, {}).get(key)

        if text is None:
            text = module_strings.get(DEFAULT_LANG, {}).get(key, key)

        return _format(text, kwargs)


_ = t
