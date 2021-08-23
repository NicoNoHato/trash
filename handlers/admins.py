from asyncio.queues import QueueEmpty
from config import que
from pyrogram import Client, filters
from pyrogram.types import Message
import sira
import tgcalls
from cache.admins import set
from helpers.decorators import authorized_users_only, errors
from helpers.channelmusic import get_chat_id
from helpers.filters import command, other_filters
from callsmusic import callsmusic


@Client.on_message(command(["pause", "jeda"]) & other_filters)
@errors
@authorized_users_only
async def pause(_, message: Message):
    callsmusic.pytgcalls.pause_stream(message.chat.id)
    await message.reply_text("⏸ Music dijeda.")


@Client.on_message(command(["resume", "lanjut", "r"]) & other_filters)
@errors
@authorized_users_only
async def resume(_, message: Message):
    callsmusic.pytgcalls.resume_stream(message.chat.id)
    await message.reply_text("▶️ Music diputar kembali.")


@Client.on_message(command(["end", "stop", "s"]) & other_filters)
@errors
@authorized_users_only
async def stop(_, message: Message):
    try:
       callsmusic.queues.clear(message.chat.id)
    except QueueEmpty:
       pass

    callsmusic.pytgcalls.leave_group_call(message.chat.id)
    await message.reply_text("❌ **Musik telah berhenti.**")


@Client.on_message(command(["skip", "sk"]) & other_filters)
@errors
@authorized_users_only
async def skip(_, message: Message):
    global que
    chat_id = get_chat_id(message.chat)
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply_text("❗ Tidak ada lagu untuk diskip.")
    else:
        callsmusic.queues.task_done(chat_id)

        if callsmusic.queues.is_empty(chat_id):
            callsmusic.pytgcalls.leave_group_call(chat_id)
        else:
            callsmusic.pytgcalls.change_stream(
                chat_id, callsmusic.queues.get(chat_id)["file"]
            )

    qeue = que.get(chat_id)
    if qeue:
        skip = qeue.pop(0)
    if not qeue:
        return
    await message.reply_text(f"- Diskip **{skip[0]}**\n- Sekarang memutar **{qeue[0][0]}**")


@Client.on_message(filters.command("reload"))
@errors
@authorized_users_only
async def admincache(client, message: Message):
    set(
        message.chat.id,
        (
            member.user
            for member in await message.chat.get_members(
                filter="administrators"
            )
        ),
    )

    await message.reply_text("✅️ **Daftar admin telah terupdate**")
