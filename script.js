// === DOM ELEMENTS ===
const chatBox = document.getElementById('chat-box');
const questionInput = document.getElementById('question');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const speakBtn = document.getElementById('speak-toggle');
const historyList = document.getElementById('chat-history-list');
const newChatBtn = document.getElementById('new-chat');
const clearChatBtn = document.getElementById('clear-chat');

let currentChatId = null;
let lastAnswer = "";
let isMicInput = false; // ✅ mic used flag

// === INITIALIZATION ===
window.addEventListener('DOMContentLoaded', () => {
  loadHistoryList();
  const last = localStorage.getItem('lastChatId');
  if (last) loadChat(last);
  else createNewChat();
});

// === STORAGE HELPERS ===
function getAllChats() {
  return JSON.parse(localStorage.getItem('allChats') || '{}');
}
function saveAllChats(obj) {
  localStorage.setItem('allChats', JSON.stringify(obj));
}

// === CREATE NEW CHAT ===
newChatBtn.addEventListener('click', createNewChat);
function createNewChat() {
  currentChatId = Date.now().toString();
  const all = getAllChats();
  all[currentChatId] = { title: 'New Chat', messages: [] };
  saveAllChats(all);
  localStorage.setItem('lastChatId', currentChatId);
  renderChatBox([]);
  renderHistoryList();
}

// === CLEAR ALL CHATS ===
clearChatBtn.addEventListener('click', () => {
  if (confirm("Are you sure you want to delete ALL chat history?")) {
    localStorage.removeItem('allChats');
    localStorage.removeItem('lastChatId');
    chatBox.innerHTML = '';
    renderHistoryList();
    currentChatId = null;
    appendLocal('bot', '🧹 All chat history has been cleared.');
  }
});

// === SAVE MESSAGE ===
function saveMessage(role, text) {
  if (!currentChatId) createNewChat();
  const all = getAllChats();
  if (!all[currentChatId]) all[currentChatId] = { title: 'New Chat', messages: [] };
  all[currentChatId].messages.push({ role, text });
  if (role === 'user')
    all[currentChatId].title = text.slice(0, 30) + (text.length > 30 ? '...' : '');
  saveAllChats(all);
  renderHistoryList();
}

// === RENDER HISTORY LIST (with rename/delete) ===
function renderHistoryList() {
  const all = getAllChats();
  historyList.innerHTML = '';

  Object.keys(all).forEach((id) => {
    const chat = all[id];

    const li = document.createElement('li');
    li.className = 'history-item';

    // Title text
    const titleSpan = document.createElement('span');
    titleSpan.className = 'chat-title';
    titleSpan.textContent = chat.title || 'Untitled Chat';
    titleSpan.addEventListener('click', () => loadChat(id));

    // Edit ✏️
    const renameBtn = document.createElement('button');
    renameBtn.innerHTML = '<i class="fa-solid fa-pen"></i>';
    renameBtn.className = 'rename-btn';
    renameBtn.title = 'Rename Chat';
    renameBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const newTitle = prompt('Enter new chat name:', chat.title || 'New Chat');
      if (newTitle && newTitle.trim()) {
        all[id].title = newTitle.trim();
        saveAllChats(all);
        renderHistoryList();
      }
    });

    // Delete 🗑️
    const deleteBtn = document.createElement('button');
    deleteBtn.innerHTML = '<i class="fa-solid fa-trash"></i>';
    deleteBtn.className = 'delete-btn';
    deleteBtn.title = 'Delete Chat';
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (confirm('Delete this chat permanently?')) {
        delete all[id];
        saveAllChats(all);
        renderHistoryList();
      }
    });

    // Control buttons container
    const controls = document.createElement('div');
    controls.className = 'chat-controls';
    controls.append(renameBtn, deleteBtn);

    li.append(titleSpan, controls);
    historyList.appendChild(li);
  });
}

// === LOAD CHAT ===
function loadChat(id) {
  const all = getAllChats();
  if (!all[id]) return;
  currentChatId = id;
  localStorage.setItem('lastChatId', id);
  renderChatBox(all[id].messages || []);
}

// === RENDER CHAT BOX ===
function renderChatBox(messages) {
  chatBox.innerHTML = '';
  (messages || []).forEach((m) => appendLocal(m.role, m.text, false));
  chatBox.scrollTop = chatBox.scrollHeight;
}

// === APPEND MESSAGE LOCALLY ===
function appendLocal(role, text, save = true) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  if (save) saveMessage(role, text);
}

// === SEND MESSAGE ===
sendBtn.addEventListener('click', sendMessage);
questionInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});

function sendMessage() {
  const q = questionInput.value.trim();
  if (!q) return;
  appendLocal('user', q);
  questionInput.value = '';

  fetch('/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: q }),
  })
    .then((r) => r.json())
    .then((data) => {
      const ans = data.answer || 'No answer.';
      appendLocal('bot', ans);
      lastAnswer = ans;

      if (isMicInput) {
        speakAnswer(ans);
        isMicInput = false;
      }
    })
    .catch(() => appendLocal('bot', '⚠️ Error fetching answer.'));
}

// === SPEAK ANSWER ===
speakBtn.addEventListener('click', () => {
  if (!lastAnswer) return;
  speakAnswer(lastAnswer);
});

function speakAnswer(text) {
  if (speechSynthesis.speaking) speechSynthesis.cancel();
  const clean = text.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{26FF}]/gu, '').trim();
  const u = new SpeechSynthesisUtterance(clean);
  const voices = speechSynthesis.getVoices();
  const female = voices.find((v) => /female|zira|google.*female/i.test(v.name)) || voices[0];
  if (female) u.voice = female;
  u.rate = 1.05;
  u.pitch = 1.15;
  u.lang = 'en-US';
  speechSynthesis.speak(u);
}

// === MIC (SPEECH-TO-TEXT) ===
micBtn.addEventListener('click', () => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    alert('Speech recognition not supported in this browser. Use Chrome.');
    return;
  }
  const rec = new SR();
  rec.lang = 'en-US';
  rec.interimResults = false;

  rec.onresult = (e) => {
    questionInput.value = e.results[0][0].transcript;
    isMicInput = true;
    sendMessage();
  };

  rec.onerror = (e) => console.error(e);
  rec.start();
});

// === LOAD HISTORY ON START ===
function loadHistoryList() {
  renderHistoryList();
}
