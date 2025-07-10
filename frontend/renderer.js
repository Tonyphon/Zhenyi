const chatArea = document.getElementById('chat-area');
const inputForm = document.getElementById('input-form');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

document.getElementById('min-btn').onclick = () => window.electronAPI?.minimize();
document.getElementById('close-btn').onclick = () => window.electronAPI?.close();

function appendMessage(text, sender) {
  const bubble = document.createElement('div');
  bubble.className = 'bubble ' + sender;
  bubble.textContent = text;
  chatArea.appendChild(bubble);
  chatArea.scrollTop = chatArea.scrollHeight;
}

inputForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const msg = chatInput.value.trim();
  if (!msg) return;
  appendMessage(msg, 'user');
  chatInput.value = '';
  chatInput.focus();

  try {
    const res = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    if (!res.ok) throw new Error('Network error');
    const data = await res.json();
    appendMessage(data.reply, 'bot');
  } catch (err) {
    appendMessage('⚠️ 网络错误或后端无响应', 'bot');
  }
});

window.onload = () => {
  chatInput.focus();
};