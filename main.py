import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
# It's highly recommended to use environment variables for secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new posts in a channel and saves them to Supabase."""
    if update.channel_post:
        msg = update.channel_post
        logger.info(f"Received post from channel {msg.chat.title} (ID: {msg.chat.id})")

        content = {
            "title": msg.caption or msg.text,
            "media_url": msg.video.file_id if msg.video else None,
            "type": "video" if msg.video else "text",
        }

        try:
            supabase: Client = context.bot_data["supabase_client"]
            supabase.table("telegram_posts").insert(content).execute()
            logger.info("Successfully inserted post into Supabase.")
        except Exception as e:
            logger.error(f"Error inserting post into Supabase: {e}")


def main() -> None:
    """Start the bot."""
    if not all([BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
        logger.error("Missing one or more required environment variables.")
        return

    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.bot_data["supabase_client"] = supabase_client

    # Use a more specific filter for channel posts
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_post))

    logger.info("Bot started and polling...")
    app.run_polling()

if __name__ == "__main__":
    main()

