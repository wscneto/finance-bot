import os
import sqlite3
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load token
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database
conn = sqlite3.connect("finances.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    user_id INTEGER,
    type TEXT CHECK(type IN ('income','expense')),
    category TEXT,
    amount REAL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# --- Helpers ---
async def add_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, t_type: str, label: str):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if len(context.args) < 2:
        await update.message.reply_text(f"\u26A0 Uso correto: /{label} <valor> <categoria>")
        return

    amount_text, category = context.args[0], context.args[1]

    try:
        amount = float(amount_text)
    except ValueError:
        await update.message.reply_text("\u26A0 O valor deve ser um número. (Utilize ponto no lugar da vírgula)")
        return

    if amount <= 0:
        await update.message.reply_text("\u26A0 O valor deve ser um número positivo.")
        return

    cursor.execute(
        "INSERT INTO transactions (chat_id, user_id, type, category, amount) VALUES (?,?,?,?,?)",
        (chat_id, user_id, t_type, category, amount)
    )
    conn.commit()

    await update.message.reply_text(f"\u2705 Registrado {label} de {amount} em {category}")

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "\U0001F44B Olá! Eu sou o bot de finanças do Walter.\n\n"
        "Use os comandos:\n"
        "• /receita <valor> <categoria>\n"
        "• /despesa <valor> <categoria>\n"
        "• /resumo -> mostra o balanço deste chat"
    )

async def receita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_transaction(update, context, "income", "receita")

async def despesa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_transaction(update, context, "expense", "despesa")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cursor.execute(
        "SELECT type, SUM(amount) FROM transactions WHERE chat_id=? GROUP BY type",
        (chat_id,)
    )
    data = dict(cursor.fetchall())

    income_total = data.get("income", 0)
    expense_total = data.get("expense", 0)
    balance = income_total - expense_total

    await update.message.reply_text(
        f"\U0001F4CA Resumo deste chat:\n"
        f"\U0001F4B0 Receitas: {income_total}\n"
        f"\U0001F6D2 Despesas: {expense_total}\n"
        f"Saldo: {balance}"
    )

# --- Main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("receita", receita))
    app.add_handler(CommandHandler("despesa", despesa))
    app.add_handler(CommandHandler("resumo", resumo))

    app.run_polling()

if __name__ == "__main__":
    main()
