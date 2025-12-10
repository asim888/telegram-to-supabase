app.post('/telegram/webhook', async (req, res) => {
  const update = req.body;
  console.log('Received update:', JSON.stringify(update, null, 2));

  const msg = update.channel_post;
  if (!msg) {
    console.log('No channel_post in update, ignoring');
    return res.sendStatus(200);
  }

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
  if (msg.photo && msg.photo.length > 0) media_type = 'image';
  else if (msg.video) media_type = 'video';

  const { error } = await supabase.from('telegram_posts').insert({
    title,
    message: text,
    media_url,
    media_type,
    telegram_chat_id: telegramChatId,
    telegram_message_id: telegramMessageId
  });

  if (error) console.error('Supabase insert error (telegram_posts):', error);
  else console.log('Inserted telegram_post successfully');

  return res.sendStatus(200);
});
