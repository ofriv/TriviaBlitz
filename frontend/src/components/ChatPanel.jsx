import { useState, useRef, useEffect } from 'react';
import './ChatPanel.css';

const EMOJIS = ['👍', '😂', '😮', '🔥', '💯', '😭', '🤔', '🎉', '👏', '❤️'];

export default function ChatPanel({ messages, playerName, onSend, onEmoji }) {
  const [text, setText]   = useState('');
  const [open, setOpen]   = useState(false);
  const [bump, setBump]   = useState(false);  // unread badge pulse
  const endRef = useRef(null);
  const prevLen = useRef(messages.length);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (open) {
      endRef.current?.scrollIntoView({ behavior: 'smooth' });
      prevLen.current = messages.length;
    } else if (messages.length > prevLen.current) {
      setBump(true);
      prevLen.current = messages.length;
    }
  }, [messages, open]);

  useEffect(() => {
    if (open) { setBump(false); endRef.current?.scrollIntoView(); }
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
        className={`chat__toggle ${bump ? 'chat__toggle--bump' : ''}`}
        onClick={() => setOpen(v => !v)}
        title="Chat"
      >
        💬
        {bump && <span className="chat__badge" />}
      </button>

      {/* Panel */}
      {open && (
        <div className="chat__panel fade-in">
          <div className="chat__header">
            <span>💬 Chat</span>
            <button className="chat__close" onClick={() => setOpen(false)}>✕</button>
          </div>

          {/* Emoji quick-send */}
          <div className="chat__emojis">
            {EMOJIS.map(e => (
              <button key={e} className="chat__emoji-btn" onClick={() => onEmoji(e)}>{e}</button>
            ))}
          </div>

          {/* Messages */}
          <div className="chat__messages">
            {messages.length === 0 && (
              <p className="chat__empty">No messages yet…</p>
            )}
            {messages.map((msg, i) => {
              const isMe = msg.player_name === playerName;
              if (msg.type === 'emoji') {
                return (
                  <div key={i} className="chat__emoji-msg">
                    <span className="chat__emoji-who">{msg.player_name}</span>
                    <span className="chat__emoji-val">{msg.emoji}</span>
                  </div>
                );
              }
              return (
                <div key={i} className={`chat__msg ${isMe ? 'chat__msg--me' : ''}`}>
                  {!isMe && <span className="chat__who">{msg.player_name}</span>}
                  <span className="chat__bubble">{msg.message || msg.text}</span>
                </div>
              );
            })}
            <div ref={endRef} />
          </div>

          {/* Input */}
          <form className="chat__form" onSubmit={handleSend}>
            <input
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Say something…"
              maxLength={200}
            />
            <button type="submit" className="chat__send">Send</button>
          </form>
        </div>
      )}
    </>
  );
}
