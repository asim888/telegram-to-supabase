import { useState, useEffect } from 'react'
import { supabase } from './supabase' // Your existing supabase.js

function TelegramPosts() {
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPosts()
    
    // Subscribe to new posts
    const subscription = supabase
      .channel('telegram-posts-channel')
      .on('postgres_changes', 
        { event: 'INSERT', schema: 'public', table: 'telegram_channel_posts' },
        (payload) => {
          setPosts(current => [payload.new, ...current])
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(subscription)
    }
  }, [])

  async function fetchPosts() {
    const { data, error } = await supabase
      .from('telegram_channel_posts')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(50)

    if (error) {
      console.error('Error:', error)
    } else {
      setPosts(data)
    }
    setLoading(false)
  }

  if (loading) return <div>Loading posts...</div>

  return (
    <div className="posts-container">
      <h2>Telegram Channel Posts</h2>
      {posts.length === 0 ? (
        <p>No posts yet. Post in your Telegram channel.</p>
      ) : (
        posts.map(post => (
          <div key={post.id} className="post-card">
            <p>{post.message}</p>
            {post.media_url && (
              <div className="media-preview">
                <small>{post.media_type}: {post.media_url}</small>
              </div>
            )}
            <small>
              Posted: {new Date(post.created_at).toLocaleString()}
              {post.views > 0 && ` • 👁️ ${post.views} views`}
            </small>
          </div>
        ))
      )}
    </div>
  )
}

export default TelegramPosts
