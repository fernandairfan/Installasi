from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from config import TOKEN, ADMIN_IDS
from database import init_db, allow_user, is_allowed, add_vps, list_vps, set_active, delete_vps
from ssh_manager import run_command
from validator import validate

user_state = {}


def set_state(uid, state):
    user_state[uid] = state


def get_state(uid):
    return user_state.get(uid)


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
        res = run_command(uid, "reboot")
        await q.edit_message_text(res)

    elif q.data == "monitor":
        res = run_command(uid, "top -bn1 | head -5")
        await q.edit_message_text(res)

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
    text = update.message.text

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
            res = run_command(uid, text)
            await update.message.reply_text(res)
        else:
            await update.message.reply_text("Command ditolak")


if __name__ == "__main__":
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))

    app.run_polling()
