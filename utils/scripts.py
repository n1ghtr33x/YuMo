import os
import re
import sys
import asyncio
import traceback
import importlib
import subprocess

from io import BytesIO
from types import ModuleType
from typing import Any

from PIL import Image
from pyrogram import Client, errors, types

from .misc import modules_help, prefix, requirements_list


META_COMMENTS = re.compile(
    r"^\s*#\s*meta\s+(\w+)\s*:\s*(.*?)\s*$",
    re.MULTILINE
)

interact_with_to_delete = []


def parse_meta_comments(code: str) -> dict[str, str]:
    return {
        key: value.strip()
        for key, value in META_COMMENTS.findall(code)
    }


def parse_meta_file(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as file:
        return parse_meta_comments(file.read())


def text(message: types.Message) -> str | None:
    return message.text or message.caption


def restart() -> None:
    os.execvp(sys.executable, [sys.executable, "main.py"])


def format_exc(e: Exception, suffix: str = "") -> str:
    traceback.print_exc()

    if isinstance(e, errors.RPCError):
        return (
            "<b>Telegram API error!</b>\n"
            f"<code>[{e.CODE} {e.ID or e.NAME}] — "
            f"{e.MESSAGE.format(value=e.value)}</code>\n\n"
            f"<b>{suffix}</b>"
        )

    return (
        "<b>Error!</b>\n"
        f"<code>{e.__class__.__name__}: {e}</code>\n\n"
        f"<b>{suffix}</b>"
    )


def with_reply(func):
    async def wrapped(client: Client, message: types.Message):
        if not message.reply_to_message:
            await message.edit("<b>Reply to message is required</b>")
            return

        return await func(client, message)

    return wrapped


async def interact_with(message: types.Message) -> types.Message:
    await asyncio.sleep(1)

    response = [
        msg async for msg in message._client.get_chat_history(
            message.chat.id,
            limit=1
        )
    ]

    seconds_waiting = 0

    while response[0].from_user.is_self:
        seconds_waiting += 1

        if seconds_waiting >= 5:
            raise RuntimeError("bot didn't answer in 5 seconds")

        await asyncio.sleep(1)

        response = [
            msg async for msg in message._client.get_chat_history(
                message.chat.id,
                limit=1
            )
        ]

    interact_with_to_delete.extend([message.id, response[0].id])

    return response[0]


def format_module_help(module_name: str, full: bool = True) -> str:
    commands = modules_help[module_name]

    help_text = (
        f"<b>Помощь для |{module_name}|\n\nИспользование:</b>\n"
        if full
        else "<b>Использование:</b>\n"
    )

    for command, desc in commands.items():
        cmd = command.split(maxsplit=1)
        args = f" <code>{cmd[1]}</code>" if len(cmd) > 1 else ""

        help_text += (
            f"<code>{prefix}{cmd[0]}</code>{args} — "
            f"<i>{desc}</i>\n"
        )

    return help_text


def format_small_module_help(module_name: str, full: bool = True) -> str:
    commands = modules_help[module_name]

    help_text = (
        f"<b>Помощь для |{module_name}|\n\nСписок команд:\n"
        if full
        else "<b>Список команд:\n"
    )

    for command in commands:
        cmd = command.split(maxsplit=1)
        args = f" <code>{cmd[1]}</code>" if len(cmd) > 1 else ""
        help_text += f"<code>{prefix}{cmd[0]}</code>{args}\n"

    help_text += (
        f"\nGet full usage: <code>{prefix}help {module_name}</code></b>"
    )

    return help_text


def import_library(library_name: str, package_name: str | None = None):
    if package_name is None:
        package_name = library_name

    if package_name not in requirements_list:
        requirements_list.append(package_name)

    try:
        return importlib.import_module(library_name)

    except ImportError:
        completed = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", package_name]
        )

        if completed.returncode != 0:
            raise RuntimeError(
                f"Failed to install library {package_name} "
                f"(pip exited with code {completed.returncode})"
            )

        return importlib.import_module(library_name)


async def install_requirements(
    packages: list[str],
    message: types.Message | None = None
) -> None:
    if not packages:
        return

    for package in packages:
        if package not in requirements_list:
            requirements_list.append(package)

    if message:
        await message.edit(
            f"<b>Installing requirements:</b> "
            f"<code>{' '.join(packages)}</code>"
        )

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "pip",
        "install",
        "-U",
        *packages,
    )

    try:
        await asyncio.wait_for(proc.wait(), timeout=120)

    except asyncio.TimeoutError:
        if message:
            await message.edit(
                "<b>Timeout while installing requirements. "
                "Install them manually.</b>"
            )

        raise RuntimeError("timeout while installing requirements")

    if proc.returncode != 0:
        if message:
            await message.edit(
                f"<b>Failed to install requirements. "
                f"pip exited with code {proc.returncode}</b>"
            )

        raise RuntimeError(
            f"failed to install requirements: {' '.join(packages)}"
        )


async def ensure_requirements(
    packages: list[str],
    message: types.Message | None = None
) -> None:
    missing_packages = []

    for package in packages:
        import_name = package.split("==")[0].split(">=")[0].split("<=")[0]
        import_name = import_name.replace("-", "_")

        try:
            importlib.import_module(import_name)

        except ImportError:
            missing_packages.append(package)

    await install_requirements(missing_packages, message)


def resize_image(
    input_img,
    output=None,
    img_type: str = "PNG",
    size: int = 512,
    size2: int | None = None
):
    if output is None:
        output = BytesIO()
        output.name = f"sticker.{img_type.lower()}"

    with Image.open(input_img) as img:
        if size2 is not None:
            new_size = (size, size2)

        elif img.width == img.height:
            new_size = (size, size)

        elif img.width < img.height:
            new_size = (
                max(size * img.width // img.height, 1),
                size
            )

        else:
            new_size = (
                size,
                max(size * img.height // img.width, 1)
            )

        img.resize(new_size).save(output, img_type)

    return output


async def load_module(
    module_name: str,
    client: Client,
    message: types.Message | None = None,
    core: bool = False,
) -> ModuleType:
    if module_name in modules_help and not core:
        await unload_module(module_name, client)

    module_path = f"modules.{'custom_modules.' if not core else ''}{module_name}"
    file_path = f"{module_path.replace('.', '/')}.py"

    with open(file_path, encoding="utf-8") as file:
        code = file.read()

    meta = parse_meta_comments(code)
    packages = meta.get("requires", "").split()

    if not core:
        await ensure_requirements(packages, message)

    module = importlib.import_module(module_path)

    for obj in vars(module).values():
        handlers = getattr(obj, "handlers", [])

        if isinstance(handlers, list):
            for handler, group in handlers:
                client.add_handler(handler, group)

    module.__meta__ = meta

    return module


async def unload_module(module_name: str, client: Client) -> bool:
    module_path = f"modules.custom_modules.{module_name}"

    if module_path not in sys.modules:
        return False

    module = importlib.import_module(module_path)

    for obj in vars(module).values():
        handlers = getattr(obj, "handlers", [])

        if isinstance(handlers, list):
            for handler, group in handlers:
                client.remove_handler(handler, group)

    modules_help.pop(module_name, None)
    sys.modules.pop(module_path, None)

    return True