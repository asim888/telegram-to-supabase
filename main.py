import os
import logging
from datetime import datetime
from supabase import create_client
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv

# Load environment variables
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

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not found")
    exit(1)

# Initialize Supabase
supabase = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("✅ Supabase connected")
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
else:
    logger.warning("⚠️ Supabase credentials missing, posts won't be saved")

# ==================== SYNC FUNCTIONS ====================

def save_to_supabase(post_data):
    """Save post to Supabase (SYNC version)"""
    if not supabase:
        return False
    
    try:
        # Check for duplicate
        if post_data.get('telegram_message_id') and post_data.get('telegram_channel_id'):
            response = supabase.table('telegram_channel_posts') \
                .select('id') \
                .eq('telegram_message_id', post_data['telegram_message_id']) \
                .eq('telegram_channel_id', post_data['telegram_channel_id']) \
                .execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"⚠️ Post {post_data['telegram_message_id']} already exists")
                return True
        
        # Insert new post
        response = supabase.table('telegram_channel_posts').insert(post_data).execute()
        
        if response.data:
            logger.info(f"✅ Saved post {post_data.get('telegram_message_id')}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

# ==================== ASYNC HANDLERS ====================

async def handle_channel_post(update: Update, context):
    """Handle Telegram channel posts"""
    try:
        post = update.channel_post
        if not post:
            return
        
        # Extract data
        content = post.text or post.caption or "[Media post]"
        chat = update.effective_chat
        
        # Prepare post data
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
        
        logger.info(f"📢 Processing post: {post.message_id} from channel {chat.id}")
        
        # Save to Supabase (SYNC call from async handler)
        saved = save_to_supabase(post_data)
        
        if saved:
            logger.info(f"✅ Successfully saved post {post.message_id}")
        else:
            logger.error(f"❌ Failed to save post {post.message_id}")
            
    except Exception as e:
        logger.error(f"❌ Error handling post: {e}")

async def start_command(update: Update, context):
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 Telegram Channel to Supabase Bot\n\n"
        "I save channel posts to Supabase database."
    )

async def status_command(update: Update, context):
    """Handle /status command"""
    if supabase:
        try:
            response = supabase.table('telegram_channel_posts').select('*', count='exact').execute()
            count = len(response.data) if response.data else 0
            await update.message.reply_text(f"📊 Database Status:\nPosts saved: {count}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}")
    else:
        await update.message.reply_text("❌ Supabase not connected")

# ==================== MAIN APPLICATION ====================

def main():
    """Start the bot - FIXED for Render"""
    logger.info("🤖 Starting Telegram Bot...")
    
    # Create bot application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    
    # Get bot info - FIX: Use bot.get_me() which returns a coroutine
    # We need to run it in an async context or use sync version
    try:
        # This is the SYNC way to get bot info
        bot_info = app.bot.get_me()  # This should work in sync context
        logger.info(f"✅ Bot: @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        # If that fails, use async
        import asyncio
        bot_info = asyncio.run(app.bot.get_me())
        logger.info(f"✅ Bot: @{bot_info.username} (ID: {bot_info.id})")
    
    logger.info("""
🚀 Bot is running!
👉 Add bot as ADMIN to your Telegram channel
👉 Post messages to save to Supabase
    """)
    
    # Start polling
    app.run_polling()

if __name__ == '__main__':
    main()
