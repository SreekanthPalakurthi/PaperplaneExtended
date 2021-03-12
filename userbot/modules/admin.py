# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
"""
Userbot module to help you manage a group
"""

from asyncio import sleep
from os import remove

from telethon.errors import (
    BadRequestError,
    ChatAdminRequiredError,
    ImageProcessFailedError,
    PhotoCropSizeSmallError,
)
from telethon.errors.rpcerrorlist import (
    BadRequestError,
    MessageTooLongError,
    UserAdminInvalidError,
    UserIdInvalidError,
)
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
    EditPhotoRequest,
)
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from telethon.tl.types import (
    ChannelParticipantsAdmins,
    ChannelParticipantsBots,
    ChatAdminRights,
    ChatBannedRights,
    MessageEntityMentionName,
    MessageMediaPhoto,
    PeerChat,
)

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP
from userbot.events import register

# =================== CONSTANT ===================
PP_TOO_SMOL = "**The image is too small!**"
PP_ERROR = "**Failure while processing the image!**"
NO_ADMIN = "**I am not an admin!**"
NO_PERM = "**I don't have sufficient permissions!**"
NO_SQL = "**Running on Non-SQL mode!**"

CHAT_PP_CHANGED = "**Chat picture changed!**"
INVALID_MEDIA = "**Invalid extension!**"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)

UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)
# ================================================


@register(outgoing=True, pattern=r"^\.promote(?: |$)(.*)")
async def promote(promt):
    """ For .promote command, promotes the replied/tagged person """
    # Get targeted chat
    chat = await promt.get_chat()
    # Grab admin status or creator in a chat
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, also return
    if not (admin or creator):
        return await promt.edit(NO_ADMIN)

    new_rights = ChatAdminRights(
        add_admins=False,
        invite_users=True,
        change_info=False,
        ban_users=True,
        delete_messages=True,
        pin_messages=True,
    )

    await promt.edit("**Promoting...**")
    user, rank = await get_user_from_event(promt)
    if not rank:
        rank = "admin"  # Just in case.
    if not user:
        return

    # Try to promote if current user is admin or creator
    try:
        await promt.client(EditAdminRequest(promt.chat_id, user.id, new_rights, rank))
        await promt.edit("**Promoted successfully!**")

    # If Telethon spit BadRequestError, assume
    # we don't have Promote permission
    except BadRequestError:
        return await promt.edit(NO_PERM)

    # Announce to the logging group if we have promoted successfully
    if BOTLOG:
        await promt.client.send_message(
            BOTLOG_CHATID,
            "#PROMOTE\n"
            f"USER: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {promt.chat.title}(`{promt.chat_id}`)",
        )


@register(outgoing=True, pattern=r"^\.demote(?: |$)(.*)")
async def demote(dmod):
    """ For .demote command, demotes the replied/tagged person """
    # Admin right check
    chat = await dmod.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    if not (admin or creator):
        return await dmod.edit(NO_ADMIN)

    # If passing, declare that we're going to demote
    await dmod.edit("**Demoting...**")
    rank = "admeme"  # dummy rank, lol.
    user = await get_user_from_event(dmod)
    user = user[0]
    if not user:
        return

    # New rights after demotion
    newrights = ChatAdminRights(
        add_admins=None,
        invite_users=None,
        change_info=None,
        ban_users=None,
        delete_messages=None,
        pin_messages=None,
    )
    # Edit Admin Permission
    try:
        await dmod.client(EditAdminRequest(dmod.chat_id, user.id, newrights, rank))

    # If we catch BadRequestError from Telethon
    # Assume we don't have permission to demote
    except BadRequestError:
        return await dmod.edit(NO_PERM)
    await dmod.edit("**Demoted successfully!**")

    # Announce to the logging group if we have demoted successfully
    if BOTLOG:
        await dmod.client.send_message(
            BOTLOG_CHATID,
            "#DEMOTE\n"
            f"USER: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {dmod.chat.title}(`{dmod.chat_id}`)",
        )


@register(outgoing=True, pattern=r"^\.ban(?: |$)(.*)")
async def ban(bon):
    """ For .ban command, bans the replied/tagged person """
    # Here laying the sanity check
    chat = await bon.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not (admin or creator):
        return await bon.edit(NO_ADMIN)

    user, reason = await get_user_from_event(bon)
    if not user:
        return

    # Announce that we're going to whack the pest
    await bon.edit("**Banning...**")

    try:
        await bon.client(EditBannedRequest(bon.chat_id, user.id, BANNED_RIGHTS))
    except BadRequestError:
        return await bon.edit(NO_PERM)
    # Helps ban group join spammers more easily
    try:
        reply = await bon.get_reply_message()
        if reply:
            await reply.delete()
    except BadRequestError:
        return await bon.edit(
            "**I dont have message nuking rights, but the user was banned!**"
        )
    # Delete message and then tell that the command
    # is done gracefully
    # Shout out the ID, so that fedadmins can fban later
    if reason:
        await bon.edit(f"**{str(user.id)}** was banned!\nReason: {reason}")
    else:
        await bon.edit(f"**{str(user.id)}** was banned!")
    # Announce to the logging group if we have banned the person
    # successfully!
    if BOTLOG:
        await bon.client.send_message(
            BOTLOG_CHATID,
            "#BAN\n"
            f"USER: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {bon.chat.title}(`{bon.chat_id}`)",
        )


@register(outgoing=True, pattern=r"^\.unban(?: |$)(.*)")
async def nothanos(unbon):
    """ For .unban command, unbans the replied/tagged person """
    # Here laying the sanity check
    chat = await unbon.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not (admin or creator):
        return await unbon.edit(NO_ADMIN)

    # If everything goes well...
    await unbon.edit("**Unbanning...**")

    user = await get_user_from_event(unbon)
    user = user[0]
    if not user:
        return

    try:
        await unbon.client(EditBannedRequest(unbon.chat_id, user.id, UNBAN_RIGHTS))
        await unbon.edit("**Unbanned successfully!**")

        if BOTLOG:
            await unbon.client.send_message(
                BOTLOG_CHATID,
                "#UNBAN\n"
                f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {unbon.chat.title}(`{unbon.chat_id}`)",
            )
    except UserIdInvalidError:
        await unbon.edit("**Uh oh my unban logic broke!**")

@register(outgoing=True, pattern=r"^\.zombies(?: |$)(.*)", groups_only=False)
async def rm_deletedacc(show):
    """ For .zombies command, list all the ghost/deleted/zombie accounts in a chat. """

    con = show.pattern_match.group(1).lower()
    del_u = 0
    del_status = "**No deleted accounts found, group is clean.**"

    if con != "clean":
        await show.edit("**Searching for deleted accounts...**")
        async for user in show.client.iter_participants(show.chat_id):

            if user.deleted:
                del_u += 1
                await sleep(1)
        if del_u > 0:
            del_status = (
                f"Found **{del_u}** deleted account(s) in this group."
                "\nClean them by using `.zombies clean`"
            )
        return await show.edit(del_status)

    # Here laying the sanity check
    chat = await show.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not (admin or creator):
        return await show.edit(NO_ADMIN)

    await show.edit("**Removing deleted accounts...**")
    del_u = 0
    del_a = 0

    async for user in show.client.iter_participants(show.chat_id):
        if user.deleted:
            try:
                await show.client(
                    EditBannedRequest(show.chat_id, user.id, BANNED_RIGHTS)
                )
            except ChatAdminRequiredError:
                return await show.edit(NO_PERM)
            except UserAdminInvalidError:
                del_u -= 1
                del_a += 1
            await show.client(EditBannedRequest(show.chat_id, user.id, UNBAN_RIGHTS))
            del_u += 1

    if del_u > 0:
        del_status = f"Removed **{del_u}** deleted account(s)."

    if del_a > 0:
        del_status = (
            f"Removed **{del_u}** deleted account(s)."
            f"\n**{del_a}** deleted admin accounts are not removed."
        )
    await show.edit(del_status)
    await sleep(2)
    await show.delete()

    if BOTLOG:
        await show.client.send_message(
            BOTLOG_CHATID,
            "#CLEANUP\n"
            f"Removed **{del_u}** deleted account(s)."
            f"\nCHAT: {show.chat.title}(`{show.chat_id}`)",
        )

@register(outgoing=True, pattern=r"^\.pin(?: |$)(.*)")
async def pin(msg):
    """ For .pin command, pins the replied/tagged message on the top the chat. """
    # Admin or creator check
    chat = await msg.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not (admin or creator):
        return await msg.edit(NO_ADMIN)

    to_pin = msg.reply_to_msg_id

    if not to_pin:
        return await msg.edit("**Reply to a message to pin it.**")

    options = msg.pattern_match.group(1)

    is_silent = True

    if options.lower() == "loud":
        is_silent = False

    try:
        await msg.client(UpdatePinnedMessageRequest(msg.to_id, to_pin, is_silent))
    except BadRequestError:
        return await msg.edit(NO_PERM)

    await msg.edit("**Pinned successfully!**")


@register(outgoing=True, pattern=r"^\.kick(?: |$)(.*)")
async def kick(usr):
    """ For .kick command, kicks the replied/tagged person from the group. """
    # Admin or creator check
    chat = await usr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not (admin or creator):
        return await usr.edit(NO_ADMIN)

    user, reason = await get_user_from_event(usr)
    if not user:
        return await usr.edit("**Couldn't fetch user.**")

    await usr.edit("**Kicking...**")

    try:
        await usr.client.kick_participant(usr.chat_id, user.id)
        await sleep(0.5)
    except Exception as e:
        return await usr.edit(NO_PERM + f"\n{str(e)}")

    if reason:
        await usr.edit(
            f"**Kicked** [{user.first_name}](tg://user?id={user.id})**!**\nReason: {reason}"
        )
    else:
        await usr.edit(f"**Kicked** [{user.first_name}](tg://user?id={user.id})**!**")

CMD_HELP.update(
    {
        "admin": ">`.promote <username/reply> <custom rank (optional)>`"
        "\nUsage: Provides admin rights to the person in the chat."
        "\n\n>`.demote <username/reply>`"
        "\nUsage: Revokes the person's admin permissions in the chat."
        "\n\n>`.ban <username/reply> <reason (optional)>`"
        "\nUsage: Bans the person off your chat."
        "\n\n>`.unban <username/reply>`"
        "\nUsage: Removes the ban from the person in the chat."
        "\n\n>`.zombies`"
        "\nUsage: Searches for deleted accounts in a group. "
        "Use .zombies clean to remove deleted accounts from the group."
    }
)
