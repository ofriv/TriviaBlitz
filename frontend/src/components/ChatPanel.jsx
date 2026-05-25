import { useState, useRef, useEffect } from 'react';
import Avatar from './Avatar';

const EMOJIS = ['👍', '😂', '😮', '🔥', '💯', '😭', '🤔', '🎉', '👏', '❤️'];

export default function ChatPanel({ messages, playerName, onSend, onEmoji }) {
  const [text, setText] = useState('');
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const endRef = useRef(null);
  const prevLen = useRef(messages.length);

  useEffect(() => {
    if (open) {
      endRef.current?.scrollIntoView({ behavior: 'smooth' });
      setUnread(0);
      prevLen.current = messages.length;
    } else if (messages.length > prevLen.current) {
      setUnread(v => v + (messages.length - prevLen.current));
      prevLen.current = messages.length;
    }
  }, [messages, open]);

  useEffect(() => {
    if (open) {
      setUnread(0);
      endRef.current?.scrollIntoView();
    }
  }, [open]);

  const handleSend = (e) => {
    e?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText('');
  };

  return (
    <>
      {/* Toggle button */}
      <button
        className="chat-toggle"
        onClick={() => setOpen(v => !v)}
        title="Chat"
      >
        💬
        {unread > 0 && (
          <span className="unread">{unread > 9 ? '9+' : unread}</span>
        )}
      </button>

      {/* Panel */}
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <div className="ttl">
              <div className="dot" />
              Chat
            </div>
            <button onClick={() => setOpen(false)}>✕</button>
          </div>

          {/* Messages */}
          <div className="chat-msgs">
            {messages.length === 0 && (
              <p style={{ color: 'var(--text-3)', fontSize: 13, textAlign: 'center', padding: '20px 0', fontStyle: 'italic' }}>
                No messages yet…
              </p>
            )}
            {messages.map((msg, i) => {
              const isMe = msg.player_name === playerName;

              if (msg.type === 'emoji') {
                return (
                  <div key={i} style={{ textAlign: 'center', fontSize: 11, color: 'var(--text-3)', padding: '2px 0' }}>
                    <span style={{ fontWeight: 700 }}>{msg.player_name}</span>
                    {' '}reacted {msg.emoji}
                  </div>
                );
              }

              return (
                <div key={i} className={`chat-msg ${isMe ? 'me' : ''}`}>
                  {!isMe && <Avatar name={msg.player_name} size={24} />}
                  <div className="bubble">
                    {!isMe && <div className="nm">{msg.player_name}</div>}
                    {msg.message || msg.text}
                    {isMe && <div className="nm">{playerName}</div>}
                  </div>
                </div>
              );
            })}
            <div ref={endRef} />
          </div>

          {/* Emoji quick-send */}
          <div className="chat-emoji">
            {EMOJIS.map(e => (
              <button key={e} onClick={() => onEmoji(e)}>{e}</button>
            ))}
          </div>

          {/* Input */}
          <div className="chat-input">
            <input
              value={text}
              onChange={e => setText(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Say something…"
              maxLength={200}
            />
            <button className="send" onClick={handleSend}>Send</button>
          </div>
        </div>
      )}
    </>
  );
}
