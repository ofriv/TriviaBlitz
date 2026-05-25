const AVATAR_COLORS = [
  'linear-gradient(135deg, #c9a878, #8a6b3d)',
  'linear-gradient(135deg, #e8d5a8, #a08769)',
  'linear-gradient(135deg, #b88670, #6e4434)',
  'linear-gradient(135deg, #d4a574, #7a4a2e)',
  'linear-gradient(135deg, #a8896d, #5c4530)',
  'linear-gradient(135deg, #d9b88e, #8a6741)',
  'linear-gradient(135deg, #bf9974, #6f5234)',
  'linear-gradient(135deg, #e0c39a, #8e6e4a)',
];

function avatarStyle(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return { background: AVATAR_COLORS[h % AVATAR_COLORS.length] };
}

export default function Avatar({ name, size }) {
  const initial = (name || '?').trim().charAt(0).toUpperCase();
  const style = { ...avatarStyle(name || '?') };
  if (size) {
    style.width  = size;
    style.height = size;
    style.fontSize = Math.round(size * 0.4);
  }
  return (
    <span className="avatar" style={style}>
      {initial}
    </span>
  );
}
