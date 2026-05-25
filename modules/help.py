from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import format_module_help
from pyrogram.errors import WebpageMediaEmpty, PhotoInvalidDimensions, MediaEmpty


@Client.on_message(filters.command(["help", "h"], prefix) & filters.me)
async def help_cmd(_, message: Message):
    if len(message.command) == 1:
        msg_edited = False
        text = (
            "<b>Помощь для <emoji id='5435965782414602696'>🕊</emoji><a href=https://t.me/n1ghtr33x_channel>-YuMo "
            "UserBot-</a><emoji id='5435965782414602696'>🕊</emoji>\n"
            f"Для большей информации о модуле,\nпиши <code>{prefix}help</code> <code>[module]</code>\n\n"
            f"<emoji id='5188377234380954537'>🌘</emoji> {int(len(modules_help) / 1)} доступных модулей:</b>\n\n"
        )
        for module_name, module_data in sorted(modules_help.items(), key=lambda x: x[0]):
            commands = {
                k: v for k, v in module_data.items()
                if k != "__meta__"
            }

            text += "[<emoji id='6298505110779594363'>❤️</emoji>] • {}: {}\n".format(
                module_name.title(),
                " ".join(
                    [
                        f"<code>{prefix + cmd_name.split()[0]}</code>"
                        for cmd_name in commands.keys()
                    ]
                ),
            )
            if len(text) >= 2048:
                text += "</b>"
                if msg_edited:
                    await message.reply(text, disable_web_page_preview=True)
                else:
                    await message.edit(text, disable_web_page_preview=True)
                    msg_edited = True

        if msg_edited:
            await message.reply(text, disable_web_page_preview=True)
        else:
            await message.edit(text, disable_web_page_preview=True)
    elif message.command[1].lower() in modules_help:
        text, pic = format_module_help(message.command[1].lower())

        if pic:
            try:
                await message.reply_photo(
                    photo=pic,
                    caption=text
                )
                await message.delete()
            except (WebpageMediaEmpty, PhotoInvalidDimensions, MediaEmpty):
                await message.edit(text)
        else:
            await message.edit(text)
    else:
        command_name = message.command[1].lower()
        for name, module_data in modules_help.items():
            commands = {
                k: v for k, v in module_data.items()
                if k != "__meta__"
            }

            for command in commands.keys():
                if command.split()[0] == command_name:
                    cmd = command.split(maxsplit=1)
                    cmd_desc = commands[command]
                    return await message.edit(
                        f"<b>Help for command <code>{prefix}{command_name}</code>\n"
                        f"Module: {name} (<code>{prefix}help {name}</code>)</b>\n\n"
                        f"<code>{prefix}{cmd[0]}</code>"
                        f"{' <code>' + cmd[1] + '</code>' if len(cmd) > 1 else ''}"
                        f" — <i>{cmd_desc}</i>"
                    )
        await message.edit(f"<b>Module {command_name} not found</b>")


modules_help["help"] = {
    "__meta__": {
        "version": "1.0.0",
        "description": "Система помощи по модулям",
        "pic": "https://st3.depositphotos.com/13324256/18639/i/450/depositphotos_186397504-stock-photo-help.jpg",
    },
    "help [module/command name]": "Get common/module/command help",
}
