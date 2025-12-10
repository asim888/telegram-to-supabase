# legacy_bot.py - Using older stable version
import os
import logging
from datetime import datetime
from supabase import create_client

# OLDER python-telegram-bot API (v13.15)
from telegram.ext import Updater, MessageHandler, Filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not found")
    exit(1)

# Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase connected")
    except Exception as e:
        logger.error(f"❌ Supabase error: {e}")
else:
    logger.warning("⚠️ Supabase credentials missing")

def save_post(bot, update):
    """Handle channel posts"""
    try:
        # In older API, channel_post is in update
        post = update.channel_post
        if not post:
            return
        
        content = post.text or post.caption or ""
        chat = post.chat
        
        post_data = {
            'message': content[:5000],
            'telegram_message_id': str(post.message_id),
            'telegram_channel_id': str(chat.id),
            'created_at': datetime.utcnow().isoformat()
        }
        
        if supabase:
            response = supabase.table('telegram_channel_posts').insert(post_data).execute()
            if response.data:
                logger.info(f"✅ Saved post {post.message_id}")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")

def main():
    logger.info("🤖 Starting Telegram Bot (Legacy API)...")
    
    # Create updater (older API)
    updater = Updater(TOKEN, use_context=True)
    
    # Get bot info (sync in older API)
    bot = updater.bot
    bot_info = bot.get_me()  # This works in older API
    logger.info(f"✅ Bot: @{bot_info.username} (ID: {bot_info.id})")
    
    # Add handler
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.chat_type.channel, save_post))
    
    logger.info(f"""
🚀 Bot is running!
👉 Add @{bot_info.username} as ADMIN to your Telegram channel
👉 Post messages in channel to save to Supabase
    """)
    
    # Start polling
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
