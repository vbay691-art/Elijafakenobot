from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import os

# --- Veritabanı ---
conn = sqlite3.connect("refbot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    ref_by INTEGER,
    refs INTEGER DEFAULT 0
)""")
conn.commit()

# --- Ayarlar ---
CHANNEL = "@elijahchanel"
BOT_USERNAME = "Elijahfakenobot"   # başına @ koyma
BOT_TOKEN = os.getenv("BOT_TOKEN", "BURAYA_TOKENİNİ_YAZ")  # Render'da env var'dan alabilirsin

# --- Ana Menü Fonksiyonu ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Referanslarım", callback_data="refs")],
        [InlineKeyboardButton("🛒 Market", callback_data="market")],
        [InlineKeyboardButton("👤 Kurucu", callback_data="kurucu")]
    ])

# --- Start Komutu ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user.id,))
    conn.commit()

    if args:  # referans ile geldiyse
        referrer_id = int(args[0])
        if referrer_id != user.id:
            cursor.execute("UPDATE users SET refs = refs + 1 WHERE user_id=?", (referrer_id,))
            cursor.execute("UPDATE users SET ref_by=? WHERE user_id=? AND ref_by IS NULL", (referrer_id, user.id))
            conn.commit()

    # --- Kanal kontrolü ---
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL, user_id=user.id)
        if member.status in ["left", "kicked"]:  # Katılmamış
            await update.message.reply_text(
                f"📌 Önce kanala katılmalısın:\n➡️ https://t.me/elionchannel\n\nSonra tekrar /start yaz."
            )
            return
    except Exception:
        await update.message.reply_text("⚠️ Botu @elionchannel kanalına admin yapmalısın.")
        return

    # Menü aç
    await update.message.reply_text("✅ Kanala katıldın!\n📍 Menüden seçim yap:", reply_markup=main_menu())

# --- Buton Kontrolleri ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "refs":
        cursor.execute("SELECT refs FROM users WHERE user_id=?", (user_id,))
        refs = cursor.fetchone()[0]
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        keyboard = [[InlineKeyboardButton("⬅️ Geri", callback_data="back")]]
        await query.edit_message_text(
            f"👥 Referansların: {refs}\n🔗 Referans linkin:\n{ref_link}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "market":
        keyboard = [
            [InlineKeyboardButton("+90 Telegram Fake No (20 ref)", callback_data="tg90")],
            [InlineKeyboardButton("+1 Telegram Fake No (15 ref)", callback_data="tg1")],
            [InlineKeyboardButton("+90 WhatsApp Fake No (20 ref)", callback_data="wa90")],
            [InlineKeyboardButton("+1 WhatsApp Fake No (10 ref)", callback_data="wa1")],
            [InlineKeyboardButton("⬅️ Geri", callback_data="back")]
        ]
        await query.edit_message_text("🛒 Market Seçenekleri:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "kurucu":
        keyboard = [[InlineKeyboardButton("⬅️ Geri", callback_data="back")]]
        await query.edit_message_text("👤 Kurucu: @drnpy", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "back":
        await query.edit_message_text("📍 Menüden seçim yap:", reply_markup=main_menu())

# --- Market Ürünleri / Referans Kontrol ---
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    rewards = {
        "tg90": 20,
        "tg1": 15,
        "wa90": 20,
        "wa1": 10
    }
    names = {
        "tg90": "+90 Telegram Fake No",
        "tg1": "+1 Telegram Fake No",
        "wa90": "+90 WhatsApp Fake No",
        "wa1": "+1 WhatsApp Fake No"
    }

    if query.data in rewards:
        cost = rewards[query.data]
        cursor.execute("SELECT refs FROM users WHERE user_id=?", (user_id,))
        refs = cursor.fetchone()[0]

        keyboard = [[InlineKeyboardButton("⬅️ Geri", callback_data="market")]]

        if refs >= cost:
            # Yeterli referans → Kurucu mesajı
            await query.edit_message_text(
                f"✅ Referansın yeterli!\nKurucu: @drnpy",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Yetersiz referans
            await query.edit_message_text(
                f"ℹ️ {names[query.data]} almak için {cost} referans kasmalısın.\n"
                f"Senin referansların: {refs}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

# --- Bot Çalıştır ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CallbackQueryHandler(claim))

    app.run_polling()

if __name__ == "__main__":
    main()
