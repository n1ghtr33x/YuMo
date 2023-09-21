from sys import version_info
from .db import db

__all__ = [
    "modules_help",
    "requirements_list",
    "python_version",
    "prefix",
    "userbot_version",
]


modules_help = {}
requirements_list = []

python_version = f"{version_info[0]}.{version_info[1]}.{version_info[2]}"

prefix = db.get("core.main", "prefix", ".")

userbot_version = f"1.0.7"
