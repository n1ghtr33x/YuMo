import os
import uuid
import asyncio
import tempfile
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineQueryResultArticle,
    InlineQueryResultCachedAudio,
    InputTextMessageContent,
)

from utils.misc import modules_help, prefix
from utils.inline import inline_command
from utils.scripts import format_exc


_audio_cache = {}


def is_spotify_track(link: str):
    return "https://open.spotify.com/track/" in link


async def run_spotdl(link: str):
    temp_dir = tempfile.mkdtemp(prefix="yumo_spotdl_")

    proc = await asyncio.create_subprocess_shell(
        f'cd "{temp_dir}" && python3 -m spotdl download "{link}"',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    stdout_text = stdout.decode(errors="ignore").strip()
    stderr_text = stderr.decode(errors="ignore").strip()

    if proc.returncode != 0:
        raise RuntimeError(
            stderr_text
            or stdout_text
            or f"spotdl exited with code {proc.returncode}"
        )

    files = list(Path(temp_dir).glob("*.mp3"))

    if not files:
        all_files = [str(p.name) for p in Path(temp_dir).iterdir()]
        raise FileNotFoundError(
            "MP3 файл не найден. Вывод spotdl:\n"
            f"{stdout_text}\n\n"
            f"Файлы в папке: {all_files}"
        )

    return str(files[0]), temp_dir


async def upload_audio_to_cache(app, link: str):
    if link in _audio_cache:
        return _audio_cache[link]

    bot = app.bot
    me = await app.get_me()

    audio_path, temp_dir = await run_spotdl(link)

    try:
        msg = await bot.send_audio(me.id, audio_path)
        file_id = msg.audio.file_id

        await msg.delete()

        _audio_cache[link] = file_id
        return file_id

    finally:
        try:
            os.remove(audio_path)
        except Exception:
            pass

        try:
            os.rmdir(temp_dir)
        except Exception:
            pass


@Client.on_message(filters.command(["spotdl", "spotify"], prefix) & filters.me)
async def spotdl_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit("<b>Укажи Spotify track link</b>")
        return

    link = message.command[1]

    if not is_spotify_track(link):
        await message.edit("<b>Нужна ссылка на Spotify track</b>")
        return

    await message.edit("<b>🎧 Скачиваю...</b>")

    try:
        audio_path, temp_dir = await run_spotdl(link)

        try:
            await client.send_audio(
                message.chat.id,
                audio_path,
                caption="<b>🎧 Spotify download</b>",
            )
            await message.delete()

        finally:
            try:
                os.remove(audio_path)
            except Exception:
                pass

            try:
                os.rmdir(temp_dir)
            except Exception:
                pass

    except Exception as e:
        await message.edit(format_exc(e))


@inline_command("spotdl", "Скачать Spotify track")
async def inline_spotdl(app, query, args):
    link = args.strip()

    if not link:
        return [
            InlineQueryResultArticle(
                title="Spotify Downloader",
                description="Пример: spotdl https://open.spotify.com/track/...",
                input_message_content=InputTextMessageContent(
                    "<b>Использование:</b> "
                    "<code>spotdl https://open.spotify.com/track/...</code>"
                ),
            )
        ]

    if not is_spotify_track(link):
        return [
            InlineQueryResultArticle(
                title="Неверная ссылка",
                description="Нужна ссылка на Spotify track",
                input_message_content=InputTextMessageContent(
                    "<b>Нужна ссылка на Spotify track</b>"
                ),
            )
        ]

    try:
        file_id = await upload_audio_to_cache(app, link)

        return [
            InlineQueryResultCachedAudio(
                id=uuid.uuid4().hex,
                audio_file_id=file_id,
                caption="<b>🎧 Spotify download</b>",
            )
        ]

    except Exception as e:
        return [
            InlineQueryResultArticle(
                title="Ошибка загрузки",
                description=str(e)[:100],
                input_message_content=InputTextMessageContent(
                    f"<b>Ошибка:</b>\n<code>{str(e)}</code>"
                ),
            )
        ]


modules_help["spotdl"] = {
    "spotdl [spotify_track_link]": "скачать трек через spotdl.",
    "spotify [spotify_track_link]": "то же самое.",
}