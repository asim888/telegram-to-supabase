import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing Supabase credentials in .env")
    print("Add these to your .env file:")
    print("SUPABASE_URL=https://your-project.supabase.co")
    print("SUPABASE_SERVICE_ROLE_KEY=your-service-role-key")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("📝 Checking telegram_channel_posts table...")

try:
    # Try to query the table
    response = supabase.table('telegram_channel_posts').select('count').limit(1).execute()
    print("✅ Table already exists!")
    
    # Get count
    count_response = supabase.table('telegram_channel_posts').select('*', count='exact').execute()
    print(f"   Total posts: {count_response.count}")
    
except Exception as e:
    print("❌ Table does not exist!")
    print("\n👉 MANUAL STEP REQUIRED:")
    print("Go to Supabase → SQL Editor and run this SQL:")
    print("""
CREATE TABLE telegram_channel_posts (
    id BIGSERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    media_url TEXT,
    views INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    telegram_message_id TEXT,
    telegram_channel_id TEXT,
    date_posted TIMESTAMPTZ,
    media_type TEXT,
    CONSTRAINT unique_telegram_post UNIQUE(telegram_message_id, telegram_channel_id)
);

-- Enable Row Level Security
ALTER TABLE telegram_channel_posts ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Allow public read access" 
ON telegram_channel_posts 
FOR SELECT USING (true);

-- Allow insert for authenticated
CREATE POLICY "Allow insert for authenticated" 
ON telegram_channel_posts 
FOR INSERT WITH CHECK (true);
    """)

# Test connection after
print("\n🔍 Testing Supabase connection...")
try:
    response = supabase.table('telegram_channel_posts').select('*').limit(1).execute()
    print("✅ Connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
