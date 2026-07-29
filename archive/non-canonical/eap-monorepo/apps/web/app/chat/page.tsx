'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { auth, chat, ApiError, type BootstrapPayload, type Chat, type Message } from '../../lib/api';

type Mode = 'general' | 'legal' | 'research' | 'code';

export default function ChatPage() {
  const router = useRouter();
  const [boot, setBoot] = useState<BootstrapPayload | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<Mode>('general');
  const [modelId, setModelId] = useState('mock-general');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Bootstrap on mount; redirect to /login on 401
  useEffect(() => {
    let cancelled = false;
    chat
      .bootstrap()
      .then((b) => {
        if (cancelled) return;
        setBoot(b);
        setMessages(b.messages);
        setChats(b.chats);
        setActiveChatId(b.active_chat_id);
      })
      .catch((e) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 401) {
          router.replace('/login');
        } else {
          setError(String(e));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  const loadChat = useCallback(async (chatId: number) => {
    try {
      const { messages: msgs } = await chat.getChat(chatId);
      setMessages(msgs);
      setActiveChatId(chatId);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) router.replace('/login');
      else setError(String(e));
    }
  }, [router]);

  const handleNewChat = useCallback(async () => {
    if (!boot?.active_workspace_id) return;
    try {
      const c = await chat.createChat(boot.active_workspace_id, 'New Chat');
      setChats((cs) => [c, ...cs]);
      setActiveChatId(c.id);
      setMessages([]);
    } catch (e) {
      setError(String(e));
    }
  }, [boot?.active_workspace_id]);

  const handleNewWorkspace = useCallback(async () => {
    const name = window.prompt('Workspace name');
    if (!name) return;
    try {
      const ws = await chat.createWorkspace(name);
      // Simplest path: just reload bootstrap
      const b = await chat.bootstrap();
      setBoot(b);
      setChats(b.chats);
      setMessages(b.messages);
      setActiveChatId(b.active_chat_id);
    } catch (e) {
      setError(String(e));
    }
  }, []);

  const handleSend = useCallback(async () => {
    if (!input.trim() || !activeChatId || sending) return;
    setSending(true);
    setError(null);

    // Optimistic: show user message immediately
    const userMsg: Message = {
      id: Date.now(), chat_id: activeChatId, role: 'user',
      content: input, mode, model_id: modelId,
    };
    setMessages((m) => [...m, userMsg]);
    const contentToSend = input;
    setInput('');

    try {
      const { reply } = await chat.sendMessage(activeChatId, contentToSend, mode, modelId);
      const asstMsg: Message = {
        id: Date.now() + 1, chat_id: activeChatId, role: 'assistant',
        content: reply, mode, model_id: modelId,
      };
      setMessages((m) => [...m, asstMsg]);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) router.replace('/login');
      else setError(String(e));
    } finally {
      setSending(false);
    }
  }, [input, activeChatId, mode, modelId, sending, router]);

  const handleLogout = useCallback(async () => {
    try { await auth.logout(); } catch { /* ignore */ }
    router.replace('/login');
  }, [router]);

  if (!boot) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted">{error ?? 'Loading…'}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen grid grid-cols-[280px_1fr]">
      {/* Sidebar */}
      <aside className="bg-panel border-r border-border p-4 flex flex-col gap-4 overflow-y-auto">
        <div>
          <h1 className="text-lg font-semibold">Enterprise AI</h1>
          <p className="text-xs text-muted">Multi-model workspace</p>
        </div>

        {/* User badge */}
        <div className="bg-card border border-border rounded-lg p-3 flex items-center justify-between gap-2">
          <div className="min-w-0">
            <div className="text-sm font-medium truncate">
              {boot.user.display_name}
              {boot.user.role === 'admin' && <span className="text-xs text-muted"> (admin)</span>}
            </div>
            <div className="text-xs text-muted truncate">{boot.user.email}</div>
          </div>
          <button
            onClick={handleLogout}
            className="text-xs bg-border rounded px-2 py-1 shrink-0"
          >
            Sign out
          </button>
        </div>

        {/* Workspaces */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-sm text-muted">Workspaces</h2>
            <button onClick={handleNewWorkspace} className="text-xs bg-card border border-border rounded px-2 py-1">+</button>
          </div>
          <div className="flex flex-col gap-1">
            {boot.workspaces.map((w) => (
              <div
                key={w.id}
                className={`text-sm rounded px-3 py-2 border ${w.id === boot.active_workspace_id ? 'bg-accent border-accent' : 'bg-card border-border'}`}
              >
                {w.name}
              </div>
            ))}
            {boot.workspaces.length === 0 && (
              <p className="text-xs text-muted">No workspaces yet.</p>
            )}
          </div>
        </div>

        {/* Chats */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-sm text-muted">Chats</h2>
            <button onClick={handleNewChat} className="text-xs bg-card border border-border rounded px-2 py-1">+</button>
          </div>
          <div className="flex flex-col gap-1">
            {chats.map((c) => (
              <button
                key={c.id}
                onClick={() => loadChat(c.id)}
                className={`text-sm text-left rounded px-3 py-2 border ${c.id === activeChatId ? 'bg-accent border-accent' : 'bg-card border-border'}`}
              >
                {c.title}
              </button>
            ))}
          </div>
        </div>

        {/* Mode */}
        <div>
          <h2 className="text-sm text-muted mb-2">Mode</h2>
          <div className="grid grid-cols-2 gap-1">
            {(['general', 'legal', 'research', 'code'] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`text-xs rounded px-2 py-1.5 border ${mode === m ? 'bg-accent border-accent' : 'bg-card border-border'}`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex flex-col min-h-0">
        {/* Topbar */}
        <header className="border-b border-border bg-panel px-6 py-3 flex justify-between items-center">
          <div>
            <h2 className="text-lg">
              {chats.find((c) => c.id === activeChatId)?.title ?? 'No chat selected'}
            </h2>
            <p className="text-xs text-muted">
              {boot.workspaces.find((w) => w.id === boot.active_workspace_id)?.name ?? 'No workspace'}
            </p>
          </div>
          <select
            value={modelId}
            onChange={(e) => setModelId(e.target.value)}
            className="bg-card border border-border rounded-lg px-3 py-2 text-sm"
          >
            {boot.models.map((m) => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
        </header>

        {/* Thread */}
        <section className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
          {messages.map((m) => (
            <article
              key={m.id}
              className={`max-w-[85%] rounded-xl border p-4 ${
                m.role === 'user'
                  ? 'self-end bg-indigo-900/40 border-indigo-800'
                  : 'self-start bg-panel border-border'
              }`}
            >
              <div className="text-xs text-muted mb-1">
                {m.role} · {m.mode} · {m.model_id}
              </div>
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed m-0">
                {m.content}
              </pre>
            </article>
          ))}
          {messages.length === 0 && (
            <p className="text-muted text-sm">No messages yet. Ask something below.</p>
          )}
        </section>

        {/* Composer */}
        <section className="border-t border-border bg-panel px-6 py-4">
          {error && (
            <div className="mb-2 text-sm text-red-300">{error}</div>
          )}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask anything. Ctrl+Enter to send."
            className="w-full bg-card border border-border rounded-lg p-3 min-h-[100px] resize-y focus:outline-none focus:border-accent"
          />
          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-muted">
              {sending ? 'Sending…' : activeChatId ? 'Ready' : 'Create a chat first'}
            </span>
            <button
              onClick={handleSend}
              disabled={sending || !activeChatId || !input.trim()}
              className="bg-accent text-white rounded-lg px-4 py-2 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
