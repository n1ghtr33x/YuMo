# meta requires: yt_dlp

import os
import tempfile
import asyncio

from pyrogram import Client, filters, types
from utils.misc import modules_help, prefix

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


@Client.on_message(filters.command("dlp", prefix) & filters.me)
async def inst_downloader(_, message: types.Message):
    if yt_dlp is None:
        return await message.edit(
            "<b>Установи yt-dlp:</b>\n"
            "<code>pip install -U yt-dlp</code>"
        )

    args = message.text.split(maxsplit=1)

    if len(args) >= 2:
        url = args[1]
    elif message.reply_to_message and message.reply_to_message.text:
        url = message.reply_to_message.text
    else:
        return await message.edit("<b>Используй:</b> <code>.dlp ссылка</code>")

    await message.edit("<b>Скачиваю видео...</b>")

    with tempfile.TemporaryDirectory() as temp_dir:
        output = os.path.join(temp_dir, "%(title).80s.%(ext)s")

        ydl_opts = {
            "outtmpl": output,
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
        }

        try:
            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(info)

            file_path = await asyncio.to_thread(download)

            await message.edit("<b>Отправляю видео...</b>")

            await message.reply_video(
                video=file_path,
            )

            await message.delete()

        except Exception as e:
            await message.edit(f"<b>Ошибка:</b>\n<code>{e}</code>")


modules_help["dlp"] = {
    "dpl [ссылка]": "Скачать видео и отправить в чат"
}