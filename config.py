import os

TOKEN = os.getenv("BOT_TOKEN", "ISI_TOKEN_ANDA")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]

DB_NAME = "database.db"
