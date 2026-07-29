const state = {
  workspaces: [],
  chats: [],
  messages: [],
  files: [],
  prompts: [],
  models: [],
  activeWorkspaceId: null,
  activeChatId: null,
  mode: 'general',
};

const els = {
  workspaceList: document.getElementById('workspace-list'),
  chatList: document.getElementById('chat-list'),
  thread: document.getElementById('message-thread'),
  messageInput: document.getElementById('message-input'),
  sendBtn: document.getElementById('send-btn'),
  modelSelect: document.getElementById('model-select'),
  workspaceName: document.getElementById('workspace-name'),
  chatTitle: document.getElementById('chat-title'),
  fileList: document.getElementById('file-list'),
  promptList: document.getElementById('prompt-list'),
  statusText: document.getElementById('status-text'),
  fileInput: document.getElementById('file-input'),
};

async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  const type = res.headers.get('content-type') || '';
  if (type.includes('application/json')) return res.json();
  return res.text();
}

function setStatus(text) {
  els.statusText.textContent = text;
}

function renderModels() {
  els.modelSelect.innerHTML = '';
  state.models.forEach((m) => {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = `${m.label} · ${m.provider}`;
    els.modelSelect.appendChild(opt);
  });
}

function renderWorkspaces() {
  els.workspaceList.innerHTML = '';
  state.workspaces.forEach((w) => {
    const btn = document.createElement('button');
    btn.className = `list-item ${w.id === state.activeWorkspaceId ? 'active' : ''}`;
    btn.textContent = `${w.name} · ${w.kind}`;
    btn.onclick = async () => {
      state.activeWorkspaceId = w.id;
      await loadChats();
      await loadFiles();
      renderWorkspaces();
    };
    els.workspaceList.appendChild(btn);
  });

  const active = state.workspaces.find((w) => w.id === state.activeWorkspaceId);
  els.workspaceName.textContent = active ? `${active.name} (${active.kind})` : 'No workspace selected';
}

function renderChats() {
  els.chatList.innerHTML = '';
  state.chats.forEach((c) => {
    const btn = document.createElement('button');
    btn.className = `list-item ${c.id === state.activeChatId ? 'active' : ''}`;
    btn.textContent = c.title;
    btn.onclick = async () => {
      state.activeChatId = c.id;
      await loadMessages();
      renderChats();
    };
    els.chatList.appendChild(btn);
  });

  const active = state.chats.find((c) => c.id === state.activeChatId);
  els.chatTitle.textContent = active ? active.title : 'Chat';
}

function renderMessages() {
  els.thread.innerHTML = '';
  state.messages.forEach((m) => {
    const wrap = document.createElement('div');
    wrap.className = `message ${m.role}`;
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    meta.textContent = `${m.role.toUpperCase()} · ${m.mode}`;
    const body = document.createElement('pre');
    body.className = 'message-body';
    body.textContent = m.content;
    wrap.appendChild(meta);
    wrap.appendChild(body);
    els.thread.appendChild(wrap);
  });
  els.thread.scrollTop = els.thread.scrollHeight;
}

function renderFiles() {
  els.fileList.innerHTML = '';
  if (!state.files.length) {
    els.fileList.innerHTML = '<div class="empty">No files yet</div>';
    return;
  }
  state.files.forEach((f) => {
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = `<strong>${f.filename}</strong><span>${f.content_type || 'unknown'}</span>`;
    els.fileList.appendChild(item);
  });
}

function renderPrompts() {
  els.promptList.innerHTML = '';
  state.prompts.forEach((p) => {
    const item = document.createElement('button');
    item.className = 'list-item';
    item.textContent = p.title;
    item.onclick = () => {
      els.messageInput.value = `${els.messageInput.value}\n${p.body}`.trim();
      els.messageInput.focus();
    };
    els.promptList.appendChild(item);
  });
}

async function loadBootstrap() {
  const data = await api('/api/bootstrap');
  state.models = data.models;
  state.workspaces = data.workspaces;
  state.activeWorkspaceId = data.active_workspace_id;
  state.chats = data.chats;
  state.activeChatId = data.active_chat_id;
  state.messages = data.messages;
  state.files = data.files;
  state.prompts = data.prompts;
  renderModels();
  renderWorkspaces();
  renderChats();
  renderMessages();
  renderFiles();
  renderPrompts();
}

async function loadChats() {
  state.chats = await api(`/api/chats?workspace_id=${state.activeWorkspaceId}`);
  state.activeChatId = state.chats[0] ? state.chats[0].id : null;
  renderChats();
  await loadMessages();
}

async function loadMessages() {
  if (!state.activeChatId) {
    state.messages = [];
    renderMessages();
    return;
  }
  const data = await api(`/api/chats/${state.activeChatId}`);
  state.messages = data.messages;
  renderMessages();
}

async function loadFiles() {
  state.files = await api(`/api/files?workspace_id=${state.activeWorkspaceId}`);
  renderFiles();
}

async function createWorkspace() {
  const name = prompt('Workspace name');
  if (!name) return;
  const kind = prompt('Type: general, legal, research, developer', 'general') || 'general';
  await api('/api/workspaces', {
    method: 'POST',
    body: JSON.stringify({ name, kind }),
  });
  await loadBootstrap();
}

async function createChat() {
  if (!state.activeWorkspaceId) {
    alert('Create a workspace first.');
    return;
  }
  const title = prompt('Chat title', 'New Chat') || 'New Chat';
  const data = await api('/api/chats', {
    method: 'POST',
    body: JSON.stringify({ workspace_id: state.activeWorkspaceId, title }),
  });
  state.activeChatId = data.id;
  await loadChats();
}

async function createPrompt() {
  const title = prompt('Prompt title');
  if (!title) return;
  const body = prompt('Prompt body');
  if (!body) return;
  await api('/api/prompts', {
    method: 'POST',
    body: JSON.stringify({ title, body, scope: 'personal' }),
  });
  state.prompts = await api('/api/prompts');
  renderPrompts();
}

async function sendMessage() {
  const content = els.messageInput.value.trim();
  if (!content || !state.activeChatId) return;
  setStatus('Thinking...');
  els.sendBtn.disabled = true;
  try {
    await api(`/api/chats/${state.activeChatId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        content,
        mode: state.mode,
        model_id: els.modelSelect.value,
      }),
    });
    els.messageInput.value = '';
    await loadMessages();
    setStatus('Done.');
  } catch (err) {
    console.error(err);
    alert('Message failed to send.');
    setStatus('Error.');
  } finally {
    els.sendBtn.disabled = false;
  }
}

async function uploadFile() {
  const file = els.fileInput.files[0];
  if (!file || !state.activeWorkspaceId) return;
  const form = new FormData();
  form.append('workspace_id', state.activeWorkspaceId);
  form.append('file', file);
  setStatus('Uploading file...');
  const res = await fetch('/api/files', { method: 'POST', body: form });
  if (!res.ok) {
    alert('Upload failed');
    setStatus('Upload failed.');
    return;
  }
  els.fileInput.value = '';
  await loadFiles();
  setStatus('File uploaded.');
}

function initModeButtons() {
  document.querySelectorAll('.mode-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.mode-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      state.mode = btn.dataset.mode;
      setStatus(`Mode: ${state.mode}`);
    });
  });
}

function initEvents() {
  document.getElementById('new-workspace-btn').onclick = createWorkspace;
  document.getElementById('new-chat-btn').onclick = createChat;
  document.getElementById('new-prompt-btn').onclick = createPrompt;
  document.getElementById('send-btn').onclick = sendMessage;
  document.getElementById('refresh-btn').onclick = loadBootstrap;
  document.getElementById('use-prompt-btn').onclick = () => alert('Click a prompt on the right to insert it.');
  els.fileInput.addEventListener('change', uploadFile);
  els.messageInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') sendMessage();
  });
  initModeButtons();
}

async function start() {
  initEvents();
  await loadBootstrap();
  setStatus('Ready. Ctrl/Cmd + Enter to send.');
}

start().catch((err) => {
  console.error(err);
  setStatus('Bootstrap failed.');
});