import asyncio
import os
from pyrogram import Client, filters, utils
from pyrogram.raw import functions
from pyrogram.raw.types import InputPeerChannel, ReactionEmoji
from pyrogram.types import Message

# Config
API_ID = int(os.environ.get("API_ID", 0)) or None
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

if not all([API_ID, API_HASH, SESSION_STRING]):
    raise ValueError(
        "Pastikan API_ID, API_HASH, dan SESSION_STRING sudah diisi di Environment Variables Railway."
    )


# Monkey patch helper Pyrogram
def get_peer_type_new(peer_id: int) -> str:
    peer_id_str = str(peer_id)
    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    else:
        return "chat"


utils.get_peer_type = get_peer_type_new

app = Client("my_userbot11", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)


async def process_reaction_list(client: Client, message: Message):
    """Mencari pemberi reaks MA (❤️) dan SA (🔥) pada pesan yang di-reply."""
    target_msg = message.reply_to_message
    pemberi_ma = []
    pemberi_sa = []

    try:
        if message.chat.type in ["supergroup", "channel"]:
            channel_id = int(str(message.chat.id).replace("-100", ""))
            resolved_peer = await client.resolve_peer(message.chat.id)
            access_hash = getattr(resolved_peer, "access_hash", 0)
            chat_peer = InputPeerChannel(channel_id=channel_id, access_hash=access_hash)
        else:
            chat_peer = await client.resolve_peer(message.chat.id)

        raw_reply = await client.invoke(
            functions.messages.GetMessageReactionsList(
                peer=chat_peer, id=target_msg.id, limit=100
            )
        )

        users_map = {u.id: u for u in raw_reply.users}

        if hasattr(raw_reply, "reactions"):
            for r in raw_reply.reactions:
                user_id = getattr(r.peer_id, "user_id", None)
                if not user_id:
                    continue

                raw_user = users_map.get(user_id)
                if not raw_user:
                    continue

                # Ambil username jika ada
                username = None
                if getattr(raw_user, "username", None):
                    username = raw_user.username
                elif getattr(raw_user, "usernames", None):
                    for u in raw_user.usernames:
                        if getattr(u, "active", False) or getattr(u, "editable", False):
                            username = u.username
                            break

                user_mention = f"@{username}" if username else (raw_user.first_name or "No Name")

                # Cek tipe reaksi
                if isinstance(r.reaction, ReactionEmoji):
                    emoji = r.reaction.emoticon
                    if emoji in ["❤️", "♥️", "\u2764\ufe0f", "\u2764"]:
                        pemberi_ma.append(user_mention)
                    elif emoji == "🔥":
                        pemberi_sa.append(user_mention)

    except Exception as e:
        print(f"Error saat mengambil reaksi: {str(e)}")

    # Clear duplicate entries
    pemberi_ma = list(set(pemberi_ma))
    pemberi_sa = list(set(pemberi_sa))

    return pemberi_ma, pemberi_sa


# Commands
@app.on_message(filters.command("done", prefixes=["/", "."]) & filters.group)
async def cmd_done(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Rep ke pesan yg ingin dihitung reactnya")
        return

    pemberi_ma, pemberi_sa = await process_reaction_list(client, message)

    if not pemberi_ma and not pemberi_sa:
        await message.reply_text("Gak ada react")
        return

    bagian_done = []
    if pemberi_ma:
        str_ma = ", ".join(pemberi_ma)
        bagian_done.append(f"{str_ma} [{len(pemberi_ma)} MA]")
    if pemberi_sa:
        str_sa = ", ".join(pemberi_sa)
        bagian_done.append(f"{str_sa} [{len(pemberi_sa)} SA]")

    teks_reaksi = " ".join(bagian_done)

    caption_template = (
        "ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ\n"
        "Hark! We bring forth the most joyous of tidings from the Olive Hills: "
        "the covenant is sealed, and our sincere obligation is now delightfully met!\n\n"
        "With a heart full of felicity and a commitment as sound as the ancient foundation "
        "of our homestead, we have, in this very instant, confirmed our mutual patronage "
        "and are now firmly numbered amongst thy loyal supporters. "
        f"Thou mayest verify our adherence through the following {teks_reaksi}. "
        "It is with profound sincerity that we look forward to the advancement and plentiful "
        "harvest which this union shall yield, and we anticipate with great eagerness the stories "
        "and wisdom thy future endeavours shall bring forth to our view.\n\n"
        "We do, however, implore thee to attend to one final, crucial matter, lest the record "
        "be incomplete: kindly ensure all the necessary mensive data of thy family is duly "
        "entered into the available space here [https://t.me/DiCasaHect/29]. "
        "This diligence will secure the permanence of our accord and permit us to maintain "
        "accurate annals of our growing history.\n\n"
        "Yours with much esteem,\n"
        "@CathectLaFamilie"
    )

    await message.reply_text(text=caption_template, disable_web_page_preview=True)


async def main():
    async with app:
        print("Memperbarui database...")
        async for dialog in app.get_dialogs():
            pass
        print("Berhasil! Userbot aktif.")
        await asyncio.Event().wait()


if __name__ == "__main__":
    print("Memulai bot...")
    app.run(main())
                              
