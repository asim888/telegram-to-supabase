const express = require('express');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const app = express();
app.use(express.json());

// Supabase client (server-side, use service role key)
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

// Webhook endpoint for Telegram
app.post('/telegram/webhook', async (req, res) => {
  const update = req.body;

  const msg = update.channel_post || update.message;
  if (!msg) return res.sendStatus(200);

  const chat = msg.chat;
  const text = msg.text || msg.caption || '';
  const telegramChatId = chat.id;
  const channelUsername = chat.username || null;
  const telegramMessageId = msg.message_id;

  const media = {};
  if (msg.photo) media.photo = msg.photo;
  if (msg.video) media.video = msg.video;
  const mediaValue = Object.keys(media).length ? media : null;

  const { error } = await supabase.from('channel_posts').insert({
    telegram_chat_id: telegramChatId,
    channel_username: channelUsername,
    telegram_message_id: telegramMessageId,
    text,
    media: mediaValue
  });

  if (error) {
    console.error('Supabase insert error:', error);
  }

  return res.sendStatus(200);
});

app.get('/', (req, res) => {
  res.send('Telegram → Supabase bot is running');
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
