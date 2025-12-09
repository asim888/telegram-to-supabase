import os
import logging
from datetime import datetime
from supabase import create_client
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get credentials
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not TOKEN:
    logger.error("Missing TELEGRAM_BOT_TOKEN")
    exit(1)

# Initialize Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase connected")
    except:
        logger.warning("Supabase connection failed")

async def save_post(update: Update, context):
    try:
        post = update.channel_post
        if not post:
            return
        
        content = post.text or post.caption or ""
        chat = update.effective_chat
        
        post_data = {
            'message': content[:5000],
            'telegram_message_id': str(post.message_id),
            'telegram_channel_id': str(chat.id),
            'created_at': datetime.utcnow().isoformat()
        }
        
        if supabase:
            response = supabase.table('telegram_channel_posts').insert(post_data).execute()
            if response.data:
                logger.info(f"Saved post {post.message_id}")
    
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    logger.info("Starting bot...")
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, save_post))
    
    bot = app.bot
    bot_info = bot.get_me()
    logger.info(f"Bot: @{bot_info.username}")
    
    logger.info("Bot running. Add as ADMIN to channel.")
    app.run_polling()

if __name__ == '__main__':
    main()
