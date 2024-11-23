#(c) Adarsh-Goel
#(c) @biisal
import os
import asyncio
import requests
from asyncio import TimeoutError
from biisal.bot import StreamBot
from biisal.utils.database import Database
from biisal.utils.human_readable import humanbytes
from biisal.vars import Var
from urllib.parse import quote_plus
from pyrogram import filters, Client
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
#from utils_bot import get_shortlink

from biisal.utils.file_properties import get_name, get_hash, get_media_file_size
db = Database(Var.DATABASE_URL, Var.name)


MY_PASS = os.environ.get("MY_PASS", None)
pass_dict = {}
pass_db = Database(Var.DATABASE_URL, "ag_passwords")

msg_text ="""<b>‣ ʏᴏᴜʀ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ! 😎

‣ Fɪʟᴇ ɴᴀᴍᴇ : <i>{}</i>
‣ Fɪʟᴇ ꜱɪᴢᴇ : {}

🔻 <a href="{}">𝗙𝗔𝗦𝗧 𝗗𝗢𝗪𝗡𝗟𝗢𝗔𝗗</a>
🔺 <a href="{}">𝗪𝗔𝗧𝗖𝗛 𝗢𝗡𝗟𝗜𝗡𝗘</a>

‣ ɢᴇᴛ <a href="https://t.me/bots_up">ᴍᴏʀᴇ ғɪʟᴇs</a></b> 🤡"""



@StreamBot.on_message((filters.private) & (filters.document | filters.video | filters.audio | filters.photo), group=4)
async def private_receive_handler(c: Client, m: Message):
    # Check if the user exists in the database, if not, add them
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id)
        await c.send_message(
            Var.BIN_CHANNEL,
            f"New User Joined! : \n\n Name : [{m.from_user.first_name}](tg://user?id={m.from_user.id}) Started Your Bot!!"
        )

    # Check if an updates channel is configured
    if Var.UPDATES_CHANNEL != "None":
        try:
            user = await c.get_chat_member(Var.UPDATES_CHANNEL, m.from_user.id)
            if user.status == "kicked":
                await m.reply_text(
                    "You are banned!\n\n**Contact Support [Support](https://t.me/Movielounge_File_Bot), They Will Help You**",
                    disable_web_page_preview=True
                )
                return
        except UserNotParticipant:
            await m.reply_photo(
                photo="https://telegra.ph/file/5eb253f28ed7ed68cb4e6.png",
                caption=(
                    "<b>Hey there!\n\nPlease join our updates channel to use me! 😊\n\n"
                    "Due to server overload, only our channel subscribers can use this bot!</b>"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join Now 🚩", url=f"https://t.me/{Var.UPDATES_CHANNEL}")]]
                ),
            )
            return
        except Exception as e:
            await m.reply_text(f"Error: {str(e)}")
            return

    # Check if the user is banned
    if await db.is_banned(m.from_user.id):
        return await m.reply(Var.BAN_ALERT)

    try:
        # Forward the message to the BIN_CHANNEL
        log_msg = await m.forward(chat_id=Var.BIN_CHANNEL)

        # Generate the stream, download, and share links
        stream_link = f"https://ddbots.blogspot.com/p/stream.html?link={log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        online_link = f"https://ddbots.blogspot.com/p/download.html?link={log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        share_link = f"https://ddlink57.blogspot.com/{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

        # POST data to Laravel route
        url = "https://movietop.link/upcoming-movies"
        data = {
            "file_name": quote_plus(get_name(log_msg)),
            "share_link": share_link,
        }
        response = requests.post(url, json=data)

        # Check response status
        if response.status_code != 200:
            await m.reply_text("Failed to send data to the server.")
            return

        # Log the request in the BIN_CHANNEL
        await log_msg.reply_text(
            text=f"**Requested by :** [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n**User ID :** `{m.from_user.id}`\n**Stream Link :** {stream_link}",
            disable_web_page_preview=True,
            quote=True
        )

        # Reply to the user with the stream and download links
        msg_text = (
            "**File Name:** {0}\n"
            "**File Size:** {1}\n"
            "[🔺 Stream Link]({2}) | [🔻 Download Link]({3})"
        )
        await m.reply_text(
            text=msg_text.format(get_name(log_msg), humanbytes(get_media_file_size(m)), stream_link, online_link),
            quote=True,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Stream 🔺", url=stream_link),
                        InlineKeyboardButton("Download 🔻", url=online_link)
                    ],
                    [
                        InlineKeyboardButton("⚡ Share Link ⚡", url=share_link)
                    ]
                ]
            )
        )

    except FloodWait as e:
        print(f"Sleeping for {e.x}s due to FloodWait")
        await asyncio.sleep(e.x)
        await c.send_message(
            chat_id=Var.BIN_CHANNEL,
            text=f"Got FloodWait of {e.x}s from [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n**User ID :** `{m.from_user.id}`",
            disable_web_page_preview=True
        )

    except Exception as e:
        await m.reply_text(f"Unexpected error: {str(e)}")






@StreamBot.on_message(filters.channel & ~filters.group & (filters.document | filters.video | filters.photo)  & ~filters.forwarded, group=-1)
async def channel_receive_handler(bot, broadcast):
    if int(broadcast.chat.id) in Var.BAN_CHNL:
        print("chat trying to get straming link is found in BAN_CHNL,so im not going to give stram link")
        return
    ban_chk = await db.is_banned(int(broadcast.chat.id))
    if (int(broadcast.chat.id) in Var.BANNED_CHANNELS) or (ban_chk == True):
        await bot.leave_chat(broadcast.chat.id)
        return
    try:
        log_msg = await broadcast.forward(chat_id=Var.BIN_CHANNEL)
        stream_link = f"{Var.URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        online_link = f"{Var.URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        await log_msg.reply_text(
            text=f"**Channel Name:** `{broadcast.chat.title}`\n**CHANNEL ID:** `{broadcast.chat.id}`\n**Rᴇǫᴜᴇsᴛ ᴜʀʟ:** {stream_link}",
            quote=True
        )
        await bot.edit_message_reply_markup(
            chat_id=broadcast.chat.id,
            message_id=broadcast.id,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("sᴛʀᴇᴀᴍ 🔺", url=stream_link),
                    InlineKeyboardButton('ᴅᴏᴡɴʟᴏᴀᴅ 🔻', url=online_link)] 
                ]
            )
        )
    except FloodWait as w:
        print(f"Sleeping for {str(w.x)}s")
        await asyncio.sleep(w.x)
        await bot.send_message(chat_id=Var.BIN_CHANNEL,
                            text=f"GOT FLOODWAIT OF {str(w.x)}s FROM {broadcast.chat.title}\n\n**CHANNEL ID:** `{str(broadcast.chat.id)}`",
                            disable_web_page_preview=True)
    except Exception as e:
        await bot.send_message(chat_id=Var.BIN_CHANNEL, text=f"**#ERROR_TRACKEBACK:** `{e}`", disable_web_page_preview=True)
        print(f"Cᴀɴ'ᴛ Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ!\nEʀʀᴏʀ:  **Give me edit permission in updates and bin Channel!{e}**")
