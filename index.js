const express = require('express');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const app = express();
app.use(express.json());

// Log Supabase env to be sure we hit the right project
console.log('SUPABASE_URL:', process.env.SUPABASE_URL);
console.log(
  'SERVICE_ROLE_KEY present:',
  !!process.env.SUPABASE_SERVICE_ROLE_KEY
);

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

// For now: NO TELEGRAM_CHANNEL_ID filter (to avoid silently ignoring posts)
// We'll add it back once it's working.

app.post('/telegram/webhook', async (req, res) => {
  const update = req.body;
  console.log('Received update:', JSON.stringify(update, null, 2));

  // For debugging: accept both channel_post and normal message
  const msg = update.channel_post || update.message;
  if (!msg) {
    console.log('No channel_post or message in update, ignoring');
    return res.sendStatus(200);
  }

  console.log('Message chat type:', msg.chat.type, 'chat id:', msg.chat.id);

  const text = msg.text || msg.caption || '';
  const telegramChatId = msg.chat.id;
  const telegramMessageId = msg.message_id;

  let title = null;
  if (text) {
    title = text.split(/[.!?]/)[0];
    if (title.length > 120) title = title.slice(0, 117) + '...';
  }

  let media_type = 'text';
  let media_url = null;
  if (msg.photo && msg.photo.length > 0) {
    media_type = 'image';
  } else if (msg.video) {
    media_type = 'video';
  }

  console.log('Inserting into telegram_posts:', {
    title,
    message: text,
    media_type,
    telegram_chat_id: telegramChatId,
    telegram_message_id: telegramMessageId
  });

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
  } else {
    console.log('Inserted telegram_post successfully');
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
