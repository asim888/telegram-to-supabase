// index.js on Render
const express = require('express');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const app = express();
app.use(express.json());

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

// OPTIONAL: lock to one channel (numeric ID like -1001234567890)
const allowedChannelId = process.env.TELEGRAM_CHANNEL_ID
  ? Number(process.env.TELEGRAM_CHANNEL_ID)
  : null;

app.post('/telegram/webhook', async (req, res) => {
  const update = req.body;

  // Only channel posts, ignore private/group
  const msg = update.channel_post;
  if (!msg) return res.sendStatus(200);

  if (allowedChannelId && msg.chat.id !== allowedChannelId) {
    return res.sendStatus(200);
  }

  const chat = msg.chat;
  const text = msg.text || msg.caption || '';
  const telegramChatId = chat.id;
  const telegramMessageId = msg.message_id;

  // Title from first sentence
  let title = null;
  if (text) {
    title = text.split(/[.!?]/)[0];
    if (title.length > 120) title = title.slice(0, 117) + '...';
  }

  let media_type = 'text';
  let media_url = null;

  if (msg.photo && msg.photo.length > 0) {
    media_type = 'image';
    // later: download + upload to Supabase Storage → set media_url
  } else if (msg.video) {
    media_type = 'video';
    // later: same idea for video
  }

  const { error } = await supabase.from('telegram_posts').insert({
    title,
    message: text,
    media_url,
    media_type,
    telegram_chat_id: telegramChatId,
    telegram_message_id: telegramMessageId
  });

  if (error) {
    console.error('Supabase insert error (telegram_posts):', error);
  }

  return res.sendStatus(200);
});

app.get('/', (req, res) => {
  res.send('Telegram channel → Supabase bot is running');
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
