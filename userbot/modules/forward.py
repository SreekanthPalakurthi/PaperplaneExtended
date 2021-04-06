# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
# You can find misc modules, which dont fit in anything xD
""" Userbot module for other small commands. """

import io
import sys
from os import environ, execle
from random import randint
from time import sleep

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP, bot
from userbot.events import register
from userbot.utils import time_formatter

@register(outgoing=True, pattern=r"^\.send (.*)")
async def send(event):
    await event.edit("**Processing...**")

    if not event.is_reply:
        return await event.edit("**Reply to a message!**")

    chat = event.pattern_match.group(1)
    try:
        chat = await event.client.get_entity(chat)
    except (TypeError, ValueError):
        return await event.edit("**Invalid link provided!**")

    message = await event.get_reply_message()

    await event.client.send_message(entity=chat, message=message)
    await event.edit(f"**Sent this message to** `{chat.title}`**!**")


CMD_HELP.update(
    {
        "send": ">`.send <username/id>` (as a reply)"
        '\nUsage: Forwards the replied message to given chat without the "Forwarded from" tag.',
    }
)

