# simple_main.py
import os
import logging
import asyncio
from datetime import datetime
from supabase import create_client
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get credentials
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Validate
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN missing")
    exit(1)

# Initialize Supabase
supabase = None
try:
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("✅ Supabase connected")
except Exception as e:
    logger.error(f"❌ Supabase error: {e}")

async def handle_channel_post(update: Update, context):
    """Save channel posts to Supabase"""
    try:
        post = update.channel_post
        if not post:
            return
        
        # Extract data
        content = post.text or post.caption or "[Media post]"
        chat = update.effective_chat
        
        # Prepare data
        post_data = {
            'message': content[:5000],
            'telegram_message_id': str(post.message_id),
            'telegram_channel_id': str(chat.id),
            'date_posted': datetime.fromtimestamp(post.date).isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'views': getattr(post, 'views', 0) or 0
        }
        
        # Add media info
        if post.photo:
            photo = post.photo[-1]
            post_data['media_url'] = f"photo_{photo.file_id}"
            post_data['media_type'] = 'photo'
        elif post.video:
            post_data['media_url'] = f"video_{post.video.file_id}"
            post_data['media_type'] = 'video'
        elif post.document:
            post_data['media_url'] = f"document_{post.document.file_id}"
            post_data['media_type'] = 'document'
        
        # Save to Supabase
        if supabase:
            response = supabase.table('telegram_channel_posts').insert(post_data).execute()
            if response.data:
                logger.info(f"✅ Saved post {post.message_id}")
            else:
                logger.error("❌ Save failed")
        else:
            logger.error("❌ Supabase not available")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

async def start_command(update: Update, context):
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 Telegram Channel to Supabase Bot\n\n"
        "I save channel posts to database."
    )

async def main():
    """Start the bot"""
    logger.info("🤖 Starting bot...")
    
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    
    # Get bot info
    bot = app.bot
    bot_info = await bot.get_me()
    logger.info(f"✅ Bot: @{bot_info.username}")
    
    logger.info("🚀 Bot running. Add as ADMIN to channel...")
    
    await app.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped")
