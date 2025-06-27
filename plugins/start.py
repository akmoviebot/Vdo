import random
import requests
import humanize
import base64
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import LOG_CHANNEL, LINK_URL, ADMIN
from plugins.database import (
    checkdb, db, get_count, get_withdraw,
    record_withdraw, record_visit
)
from urllib.parse import urlencode
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
from TechVJ.util.human_readable import humanbytes

# --- UTILITIES ---
def is_admin(user_id):
    return str(user_id) in ADMIN

async def encode(string):
    b = string.encode("ascii")
    e = base64.urlsafe_b64encode(b)
    return e.decode("ascii").strip("=")

async def decode(s):
    s = s.strip("=")
    b = (s + "=" * (-len(s) % 4)).encode("ascii")
    return base64.urlsafe_b64decode(b).decode("ascii")

# --- /start ---
@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid = message.from_user.id
    if is_admin(uid) and not await checkdb.is_user_exist(uid):
        await db.add_user(uid, message.from_user.first_name)
        name = await client.ask(uid, "<b>Welcome to Ak Disk… Step 1: Send your Business Name:</b>")
        if not name.text:
            return await message.reply("❌ Invalid input—use /start again.")
        await db.set_name(uid, name=name.text)
        link = await client.ask(uid, "<b>📢 Step 2: Send Telegram Channel Link (must start with http/https):</b>")
        if not (link.text and link.text.startswith(("http://", "https://"))):
            return await message.reply("❌ Invalid link—use /start again.")
        await db.set_link(uid, link=link.text)
        await checkdb.add_user(uid, message.from_user.first_name)
        return await message.reply(
            "<b>🎉 BOOM! Admin account created successfully! 🎉\n\n"
            "Use 🔧 /quality before sending files to choose quality, or just send files directly to get a link.</b>"
        )
    elif is_admin(uid):
        rm = InlineKeyboardMarkup([[InlineKeyboardButton("✨ Update Channel", url=LINK_URL)]])
        await client.send_message(uid, script.START_TXT.format(message.from_user.mention),
                                  reply_markup=rm, parse_mode=enums.ParseMode.HTML)
    else:
        # Normal user
        await message.reply_text(
            "👋 Welcome to Ak Disk! Just send any document or video to instantly generate a sharing link, "
            "or use 🔧 /quality for custom-quality upload."
        )

# --- /update (admin-only) ---
@Client.on_message(filters.command("update") & filters.private)
async def update(client, message):
    uid = message.from_user.id
    if not is_admin(uid):
        return await message.reply("❌ This command is for admins only.")
    name = await client.ask(uid, "<b>Send your new Business Name or /cancel:</b>")
    if name.text == "/cancel":
        return await message.reply("🛑 Process cancelled.")
    if not name.text:
        return await message.reply("❌ Invalid input—use /update again.")
    await db.set_name(uid, name=name.text)
    link = await client.ask(uid, "<b>Send new Telegram Channel Link:</b>")
    if not (link.text and link.text.startswith(("http://", "https://"))):
        return await message.reply("❌ Invalid link—use /update again.")
    await db.set_link(uid, link=link.text)
    return await message.reply("✅ Profile updated successfully.")

# --- File uploader (all users) ---
@Client.on_message(filters.private & (filters.document | filters.video))
async def stream_start(client, message):
    file = getattr(message, message.media.value)
    fid = file.file_id
    uid = message.from_user.id
    log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=fid)
    params = {'u': uid, 'w': str(log_msg.id), 's': "0", 't': "0"}
    encoded_url = f"{LINK_URL}?Tech_VJ={await encode(urlencode(params))}"
    rm = InlineKeyboardMarkup([[InlineKeyboardButton("🖇️ Your Link Open", url=encoded_url)]])
    await message.reply_text(f"<code>{encoded_url}</code>", reply_markup=rm)

# --- /quality (all users) ---
@Client.on_message(filters.private & filters.command("quality"))
async def quality_link(client, message):
    # Paste the entire block from your original quality handler here
    # (including first/second/third quality logic and /getlink branch)
    pass

# --- Re-streaming link (all users) ---
@Client.on_message(filters.private & filters.text &
                   ~filters.command(["start", "update", "quality", "account", "withdraw", "notify"]))
async def link_start(client, message):
    text = message.text.strip()
    if not text.startswith(LINK_URL):
        return
    try:
        decoded = await decode(text.split("?Tech_VJ=")[1])
        parts = decoded.split("=")
        if len(parts) != 5:
            raise ValueError
        _, orig_u, w, s, t = parts
    except:
        return await message.reply("❌ Link invalid.")
    uid = message.from_user.id
    params = {'u': uid, 'w': w, 's': s, 't': t}
    encoded_url = f"{LINK_URL}?Tech_VJ={await encode(urlencode(params))}"
    rm = InlineKeyboardMarkup([[InlineKeyboardButton("🖇️ Your Link Open", url=encoded_url)]])
    return await message.reply_text(f"<code>{encoded_url}</code>", reply_markup=rm)

# --- /account (admin-only) ---
@Client.on_message(filters.command("account") & filters.private)
async def show_account(client, message):
    uid = message.from_user.id
    if not is_admin(uid):
        return await message.reply("❌ Admins only.")
    clicks = get_count(uid) or 0
    balance = clicks / 1000.0
    await message.reply(f"<b>API Key: {uid}\nPlays: {clicks}\nBalance: ${balance:.2f}</b>")

# --- /withdraw (admin-only) ---
@Client.on_message(filters.command("withdraw") & filters.private)
async def show_withdraw(client, message):
    uid = message.from_user.id
    if not is_admin(uid):
        return await message.reply("❌ Admins only.")
    # Paste your original withdrawal flow here intact
    pass

# --- /notify (admin-only) ---
@Client.on_message(filters.command("notify") & filters.private & filters.chat(ADMIN))
async def show_notify(client, message):
    uid = message.from_user.id
    if not is_admin(uid):
        return await message.reply("❌ Admins only.")
    # Paste your original notify logic here intact
    pass
