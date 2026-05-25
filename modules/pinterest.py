import json
import re
import urllib.parse
import urllib.request

from pyrogram.types import (
    InlineQueryResultPhoto,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from utils.inline import inline_command
from utils.misc import modules_help


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def request_url(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def ddg_pinterest_search(query: str, limit: int = 20):
    search = f"site:pinterest.com {query}"
    encoded = urllib.parse.quote(search)

    html = request_url(f"https://duckduckgo.com/?q={encoded}&iax=images&ia=images")

    match = re.search(r"vqd='([^']+)'", html) or re.search(r'vqd="([^"]+)"', html)

    if not match:
        return []

    vqd = match.group(1)

    api_url = (
        "https://duckduckgo.com/i.js?"
        f"l=us-en&o=json&q={encoded}&vqd={vqd}&f=,,,&p=1"
    )

    data = json.loads(request_url(api_url))

    results = []

    for item in data.get("results", []):
        image = item.get("image")
        thumb = item.get("thumbnail") or image
        title = item.get("title") or query

        if not image:
            continue

        results.append(
            {
                "image": image,
                "thumb": thumb,
                "title": title,
            }
        )

        if len(results) >= limit:
            break

    return results


@inline_command("pinterest", "Поиск картинок Pinterest")
async def inline_pinterest(app, query, args):
    search_query = args.strip()

    if not search_query:
        return [
            InlineQueryResultArticle(
                title="Pinterest Search",
                description="Пример: pinterest cats",
                input_message_content=InputTextMessageContent(
                    "<b>Использование:</b> <code>pinterest cats</code>"
                ),
            )
        ]

    try:
        images = ddg_pinterest_search(search_query)

        if not images:
            return [
                InlineQueryResultArticle(
                    title="Ничего не найдено",
                    description=search_query,
                    input_message_content=InputTextMessageContent(
                        "<b>Ничего не найдено.</b>"
                    ),
                )
            ]

        return [
            InlineQueryResultPhoto(
                id=str(i),
                photo_url=item["image"],
                thumb_url=item["thumb"],
                title=item["title"][:64],
            )
            for i, item in enumerate(images)
        ]

    except Exception as e:
        return [
            InlineQueryResultArticle(
                title="Ошибка поиска",
                description=str(e),
                input_message_content=InputTextMessageContent(
                    f"<b>Ошибка:</b>\n<code>{e}</code>"
                ),
            )
        ]


modules_help["pinterest"] = {
    "pinterest [query]": "поиск картинок Pinterest через inline.",
}