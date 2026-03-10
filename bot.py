
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
import yt_dlp

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

bot = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
assistant = Client("assistant", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

calls = PyTgCalls(assistant)
queues = {}

async def ensure_assistant(chat_id):
    try:
        await assistant.get_chat_member(chat_id, "me")
    except:
        link = await bot.export_chat_invite_link(chat_id)
        await assistant.join_chat(link)

@bot.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply_text(
        "🎵 Music Bot Online!\n"
        "Commands:\n"
        "/play song\n"
        "/skip\n"
        "/pause\n"
        "/resume\n"
        "/stop"
    )

def yt_search(query):
    ydl_opts = {"format": "bestaudio", "noplaylist": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
        return info["url"], info["title"]

@bot.on_message(filters.command("play"))
async def play(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Song name do")

    query = " ".join(message.command[1:])
    await message.reply_text(f"🔎 Searching: {query}")

    url, title = yt_search(query)
    chat_id = message.chat.id

    await ensure_assistant(chat_id)

    if chat_id not in queues:
        queues[chat_id] = []
        await calls.join_group_call(chat_id, AudioPiped(url))
        await message.reply_text(f"▶️ Playing: {title}")
    else:
        queues[chat_id].append((url, title))
        await message.reply_text(f"📜 Added to queue: {title}")

@bot.on_message(filters.command("skip"))
async def skip(_, message: Message):
    chat_id = message.chat.id
    if chat_id in queues and queues[chat_id]:
        url, title = queues[chat_id].pop(0)
        await calls.change_stream(chat_id, AudioPiped(url))
        await message.reply_text(f"⏭ Playing: {title}")
    else:
        await message.reply_text("❌ Queue empty")

@bot.on_message(filters.command("pause"))
async def pause(_, message: Message):
    await calls.pause_stream(message.chat.id)
    await message.reply_text("⏸ Music paused")

@bot.on_message(filters.command("resume"))
async def resume(_, message: Message):
    await calls.resume_stream(message.chat.id)
    await message.reply_text("▶️ Music resumed")

@bot.on_message(filters.command("stop"))
async def stop(_, message: Message):
    chat_id = message.chat.id
    await calls.leave_group_call(chat_id)
    queues.pop(chat_id, None)
    await message.reply_text("⏹ Music stopped")

async def main():
    await bot.start()
    await assistant.start()
    await calls.start()
    print("Music Bot Started")
    from pyrogram import idle
    await idle()

asyncio.get_event_loop().run_until_complete(main())
