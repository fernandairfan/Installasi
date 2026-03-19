from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import asyncio

from config import TOKEN, ADMIN_IDS
from database import init_db, allow_user, is_allowed, add_vps, list_vps, set_active, delete_vps
from ssh_manager import run_command
from validator import validate

user_state = {}


def set_state(uid, state):
    user_state[uid] = state


def get_state(uid):
    return user_state.get(uid)


def progress_bar(percent: int, width: int = 10) -> str:
    filled = int((percent / 100) * width)
    empty = width - filled
    return f"[{'|' * filled}{'-' * empty}] {percent}%"


async def animate_progress(message, label: str, done_event: asyncio.Event):
    percent = 0
    while not done_event.is_set():
        if percent < 90:
            percent += 3
        elif percent < 95:
            percent += 1
        try:
            await message.edit_text(f"{label}\n{progress_bar(percent)}")
        except Exception:
            pass
        await asyncio.sleep(2)


async def run_command_with_progress(update_target, uid: int, command: str, label: str):
    status_message = await update_target.reply_text(f"{label}\n{progress_bar(0)}")
    done_event = asyncio.Event()
    progress_task = asyncio.create_task(animate_progress(status_message, label, done_event))

    try:
        result = await asyncio.to_thread(run_command, uid, command)
    finally:
        done_event.set()
        try:
            await progress_task
        except Exception:
            pass

    if result is None:
        result = "Done"

    output = str(result).strip() or "Done"
    if len(output) > 3500:
        output = output[:3500] + "\n\n...output dipotong"

    final_text = f"{label}\n{progress_bar(100)}\n\n{output}"
    try:
        await status_message.edit_text(final_text)
    except Exception:
        await update_target.reply_text(final_text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid in ADMIN_IDS:
        allow_user(uid)

    if not is_allowed(uid):
        await update.message.reply_text("Not allowed")
        return

    kb = [
        [InlineKeyboardButton("Login VPS", callback_data="login"), InlineKeyboardButton("Install", callback_data="install")],
        [InlineKeyboardButton("Switch VPS", callback_data="switch"), InlineKeyboardButton("Delete VPS", callback_data="delete")],
        [InlineKeyboardButton("Reboot", callback_data="reboot"), InlineKeyboardButton("Monitor", callback_data="monitor")]
    ]

    await update.message.reply_text("Menu", reply_markup=InlineKeyboardMarkup(kb))


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "login":
        set_state(uid, "add_name")
        await q.edit_message_text("Input nama VPS:")

    elif q.data == "install":
        set_state(uid, "install")
        await q.edit_message_text("Ketik command:")

    elif q.data == "reboot":
        await q.edit_message_text("Menjalankan reboot...")
        await run_command_with_progress(q.message, uid, "reboot", "Proses reboot VPS sedang berjalan")

    elif q.data == "monitor":
        await q.edit_message_text("Mengambil monitoring...")
        await run_command_with_progress(q.message, uid, "top -bn1 | head -5", "Mengambil status CPU/RAM VPS")

    elif q.data == "switch":
        vps = list_vps(uid)
        kb = [[InlineKeyboardButton(name, callback_data=f"use_{vid}")] for vid, name in vps]
        await q.edit_message_text("Pilih VPS", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("use_"):
        vid = int(q.data.split("_")[1])
        set_active(uid, vid)
        await q.edit_message_text("Switched")

    elif q.data == "delete":
        vps = list_vps(uid)
        kb = [[InlineKeyboardButton(name, callback_data=f"del_{vid}")] for vid, name in vps]
        await q.edit_message_text("Hapus VPS", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("del_"):
        vid = int(q.data.split("_")[1])
        delete_vps(vid)
        await q.edit_message_text("Deleted")


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if not is_allowed(uid):
        return

    state = get_state(uid)

    if state == "add_name":
        context.user_data["name"] = text
        set_state(uid, "add_host")
        await update.message.reply_text("IP VPS:")

    elif state == "add_host":
        context.user_data["host"] = text
        set_state(uid, "add_user")
        await update.message.reply_text("Username:")

    elif state == "add_user":
        context.user_data["user"] = text
        set_state(uid, "add_pass")
        await update.message.reply_text("Password:")

    elif state == "add_pass":
        add_vps(uid,
                context.user_data["name"],
                context.user_data["host"],
                context.user_data["user"],
                text)
        set_state(uid, None)
        await update.message.reply_text("VPS tersimpan")

    elif state == "install":
        if validate(text):
            await run_command_with_progress(update.message, uid, text, f"Menjalankan command: {text}")
        else:
            await update.message.reply_text("Command ditolak")


if __name__ == "__main__":
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))

    app.run_polling()
