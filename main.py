# threaded_bot.py - Uses threading to avoid event loop issues
import os
import logging
import threading
from datetime import datetime
from supabase import create_client
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
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

def save_post_sync(post_data):
    """Thread-safe save function"""
    if not supabase:
        return False
    
    try:
        response = supabase.table('telegram_channel_posts').insert(post_data).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"❌ Save error: {e}")
        return False

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel posts"""
    try:
        post = update.channel_post
        if not post:
            return
        
        chat = update.effective_chat
        content = post.text or post.caption or ""
        
        post_data = {
            'message': content[:5000],
            'telegram_message_id': str(post.message_id),
            'telegram_channel_id': str(chat.id),
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Save in a thread to avoid blocking
        thread = threading.Thread(
            target=save_post_sync,
            args=(post_data,)
        )
        thread.start()
        
        logger.info(f"✅ Processing post {post.message_id}")
        
    except Exception as e:
        logger.error(f"❌ Handler error: {e}")

def run_bot():
    """Run bot in a separate thread"""
    logger.info("🤖 Starting bot thread...")
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    
    # Get bot info
    bot = app.bot
    bot_info = bot.get_me()
    logger.info(f"✅ Bot: @{bot_info.username}")
    
    logger.info("🚀 Bot thread started")
    app.run_polling()

def main():
    """Main function"""
    logger.info("🚀 Starting Telegram Bot Service...")
    
    # Run bot in a thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Keep main thread alive
    try:
        bot_thread.join()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")

if __name__ == '__main__':
    main()
