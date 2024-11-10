import React, { useState, useEffect } from 'react';
import CrossPostMatrix from './components/CrossPostMatrix';
import './App.css';

function App() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [setupToken, setSetupToken] = useState(localStorage.getItem('setupToken'));

  useEffect(() => {
    if (!setupToken) {
      createUser();
    } else {
      fetchPosts();
    }
  }, [setupToken]);

  const createUser = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/users', {
        method: 'POST'
      });
      const data = await response.json();
      localStorage.setItem('setupToken', data.setup_token);
      setSetupToken(data.setup_token);
    } catch (error) {
      console.error('Error creating user:', error);
    }
  };

  const fetchPosts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/posts', {
        headers: {
          'Authorization': `Bearer ${setupToken}`
        }
      });
      const data = await response.json();
      setPosts(data);
    } catch (error) {
      console.error('Error fetching posts:', error);
      if (error.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('setupToken');
        setSetupToken(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (fromPlatform, toPlatform) => {
    // Здесь будет логика предпросмотра трансформированного поста
    console.log(`Preview from ${fromPlatform} to ${toPlatform}`);
  };

  const handleApprove = async (fromPlatform, toPlatform) => {
    // Здесь будет логика одобрения и публикации поста
    console.log(`Approve from ${fromPlatform} to ${toPlatform}`);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI Cross-Post</h1>
        <p>Cross-platform content management</p>
      </header>
      <main>
        <section className="matrix-section">
          <h2>Cross-Posting Matrix</h2>
          <CrossPostMatrix 
            posts={posts}
            onPreview={handlePreview}
            onApprove={handleApprove}
            setupToken={setupToken}
          />
        </section>
        <section className="posts-queue">
          <h2>Posts Queue</h2>
          {loading ? (
            <p>Loading posts...</p>
          ) : posts.length > 0 ? (
            <ul>
              {posts.map(post => (
                <li key={post.id}>
                  <p>{post.content}</p>
                  <small>
                    From: {post.platform} 
                    {post.channel_title && ` (${post.channel_title})`}
                  </small>
                </li>
              ))}
            </ul>
          ) : (
            <p>No posts in queue</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App; 