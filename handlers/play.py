import os
from os import path
from typing import Callable
from pyrogram import Client, filters
from pyrogram.types import Message, Voice, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserAlreadyParticipant
from callsmusic import callsmusic, queues
from callsmusic.callsmusic import client as USER
from helpers.admins import get_administrators
import requests
import aiohttp
import youtube_dl
from youtube_search import YoutubeSearch
import converter
from downloaders import youtube
from config import DURATION_LIMIT, que
from cache.admins import admins as a
from helpers.filters import command
from helpers.decorators import errors, authorized_users_only
from helpers.errors import DurationLimitError
from helpers.gets import get_url, get_file_name
from helpers.channelmusic import get_chat_id
import aiofiles
import ffmpeg
from PIL import Image, ImageFont, ImageDraw

# plus
chat_id = None
DISABLED_GROUPS = []
useer ="NaN"
def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        else:
            await cb.answer("Kamu ga diperbolehkan.", show_alert=True)
            return

    return decorator

def transcode(filename):
    ffmpeg.input(filename).output("input.raw", format='s16le', acodec='pcm_s16le', ac=2, ar='48k').overwrite_output().run() 
    os.remove(filename)

# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(':'))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage

async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    image1 = Image.open("./background.png")
    image2 = Image.open("etc/AR.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/font.otf", 42)
    judul = ImageFont.truetype("etc/judul.ttf", 32)
    draw.text((305, 550), f"Judul: {title}", (0, 0, 0), font=judul)
    draw.text(
        (305, 590), f"Durasi: {duration}", (51, 153, 255), font=font
    )
    draw.text((305, 630), f"Views: {views}", (51, 153, 255), font=font)
    draw.text((305, 670),
        f"Ditambah oleh: {requested_by}",
        (51, 153, 255),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(
    filters.command("musicplayer") & ~filters.edited & ~filters.bot & ~filters.private
)
@authorized_users_only
async def hfmm(_, message):
    global DISABLED_GROUPS
    try:
        user_id = message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text(
            "I only recognize `/musicplayer on` and /musicplayer `off only`"
        )
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status == "ON" or status == "on" or status == "On":
        lel = await message.reply("`Processing...`")
        if not message.chat.id in DISABLED_GROUPS:
            await lel.edit("Music Player Already Activated In This Chat")
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(
            f"Music Player Successfully Enabled For Users In The Chat {message.chat.id}"
        )

    elif status == "OFF" or status == "off" or status == "Off":
        lel = await message.reply("`Processing...`")
        
        if message.chat.id in DISABLED_GROUPS:
            await lel.edit("Music Player Already turned off In This Chat")
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(
            f"Music Player Successfully Deactivated For Users In The Chat {message.chat.id}"
        )
    else:
        await message.reply_text(
            "I only recognize `/musicplayer on` and /musicplayer `off only`"
        )

@Client.on_callback_query(filters.regex(pattern=r"^(cls)$"))
@cb_admin_check
async def m_cb(b, cb):
    global que    
    qeue = que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    chat_id = cb.message.chat.id
    m_chat = cb.message.chat

    if type_ == "cls":          
        await cb.answer("Closed menu")
        await cb.message.delete()

# play
@Client.on_message(filters.command("req") & filters.group & ~filters.edited & ~filters.forwarded & ~filters.via_bot)
async def play(_, message: Message):
    global que
    global useer
    if message.chat.id in DISABLED_GROUPS:
        return
    lel = await message.reply("🔄 **Memproses ...**")
    
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "@JefMusik"
    usar = user
    wew = usar.id
    try:
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                await lel.edit(
                        "<b>Lagi ngecek asistan bot.</b>",
                    )
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>Promosikan aku jadi Admin dulu.</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "Jef Userbot telah bergabung ke grup untuk berpesta."
                    )
                    await lel.edit(
                        "<b>Asisten sudah masuk ke dalam grup.</b>",
                    )
                    
                except UserAlreadyParticipant:
                    pass
                except Exception:
                    await lel.edit(
                        f"<b>🛑 Flood Wait Error 🛑</b> \n\Hey {user.first_name}, Userbot tidak bisa bergabung karna terlalu sulit, cek apakah userbot terbanned pada grup atau tidak.!")
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i>Hei {user.first_name}, Asisten Userbot tidak ada dalam grup, bilang ke admin untuk mengirim perintah /play atau menambah @JefMusik dengan manual!")
        return
    
    audio = (message.reply_to_message.audio or message.reply_to_message.voice) if message.reply_to_message else None
    url = get_url(message)

    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"❌ Lagu lebih dari {DURATION_LIMIT} menit tidak diizinkan untuk diputar!"
            )

        file_name = get_file_name(audio)
        title = "Audio Telegram"
        thumb_name = "https://telegra.ph/file/d3cd0d8da27cb2f0b9a62.jpg"
        thumbnail = thumb_name
        duration = "NaN"
        views = "NaN"

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 Support", url=f"t.me/AnimeIndoReborn"),
                    InlineKeyboardButton("📡 Updates", url=f"t.me/AnimeIndoReborn"),
                ],
                [InlineKeyboardButton(text="🗑 Tutup", callback_data="cls")],
            ]
        )
        
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)  
        file_path = await converter.convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name)) else file_name
        )

    elif url:
        try:
            results = YoutubeSearch(url, max_results=1).to_dict()
            # print results
            title = results[0]["title"]       
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f'thumb{title}.jpg'
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, 'wb').write(thumb.content)
            duration = results[0]["duration"]
            url_suffix = results[0]["url_suffix"]
            views = results[0]["views"]
            durl = url
            durl = durl.replace("youtube", "youtubepp")
            
            secmul, dur, dur_arr = 1, 0, duration.split(':')
            for i in range(len(dur_arr)-1, -1, -1):
                dur += (int(dur_arr[i]) * secmul)
                secmul *= 60
                
            keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🚨 Support", url=f"t.me/AnimeIndoReborn"),
                    InlineKeyboardButton("📡 Updates", url=f"t.me/AnimeIndoReborn"),
                ],
                [InlineKeyboardButton(text="🗑 Tutup", callback_data="cls")],
            ]
        )
        except Exception as e:
            title = "NaN"
            thumb_name = "https://telegra.ph/file/d3cd0d8da27cb2f0b9a62.jpg"
            duration = "NaN"
            views = "NaN"
            keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="YouTube 🎬",
                                url=f"https://youtube.com")

                        ]
                    ]
                )
        if (dur / 60) > DURATION_LIMIT:
             await lel.edit(f"❌ Lagu lebih dari {DURATION_LIMIT} menit tidak diizinkan untuk diputar!")
             return
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)     
        file_path = await converter.convert(youtube.download(url))
    else:
        if len(message.command) < 2:
            return await lel.edit("🧐 **Lagu apa yang mau kamu putar?**")
        await lel.edit("🔎 **Mencoba mencari judul lagu ...**")
        query = message.text.split(None, 1)[1]
        # print(query)
        await lel.edit("🎵 **Memproses Lagu ...**")
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print results
            title = results[0]["title"]       
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f'thumb{title}.jpg'
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, 'wb').write(thumb.content)
            duration = results[0]["duration"]
            url_suffix = results[0]["url_suffix"]
            views = results[0]["views"]
            durl = url
            durl = durl.replace("youtube", "youtubepp")

            secmul, dur, dur_arr = 1, 0, duration.split(':')
            for i in range(len(dur_arr)-1, -1, -1):
                dur += (int(dur_arr[i]) * secmul)
                secmul *= 60
                
        except Exception as e:
            await lel.edit(
                "❌ Lagu ga ketemu.\n\nCoba lagu lain, atau cari lagu dengan jelas dan benar."
            )
            print(str(e))
            return

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🚨 Support", url=f"t.me/AnimeIndoReborn"),
                    InlineKeyboardButton("📡 Updates", url=f"t.me/AnimeIndoReborn"),
                ],
                [InlineKeyboardButton(text="🗑 Tutup", callback_data="cls")],
            ]
        )
        
        if (dur / 60) > DURATION_LIMIT:
             await lel.edit(f"❌ Lagu lebih dari {DURATION_LIMIT} menit tidak diizinkan untuk diputar!")
             return
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)  
        file_path = await converter.convert(youtube.download(url))
  
    if message.chat.id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(message.chat.id, file=file_path)
        await message.reply_photo(
        photo="final.png", 
        caption="**🎵 Lagu:** {}\n**🕒 Durasi:** {} min\n**👤 Ditambah oleh:** {}\n\n**#⃣ Antrian ke:** {}".format(
        title, duration, message.from_user.mention(), position
        ),
        reply_markup=keyboard)
        os.remove("final.png")
        return await lel.delete()
    else:
        callsmusic.pytgcalls.join_group_call(message.chat.id, file_path)
        await message.reply_photo(
        photo="final.png",
        reply_markup=keyboard,
        caption="**🎵 Lagu:** {}\n**🕒 Durasi:** {} min\n**👤 Ditambah oleh:** {}\n\n**▶️ Sedang diputar di `{}`...**".format(
        title, duration, message.from_user.mention(), message.chat.title
        ), )
        os.remove("final.png")
        return await lel.delete()
