import type { ThreadItem } from "../types";

interface SidebarProps {
  threads: ThreadItem[];
  activeThreadId: string;
  collapsed: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  onSelectThread: (id: string) => void;
  userLabel?: string;
  onLogout?: () => void;
}

export function Sidebar({
  threads,
  activeThreadId,
  collapsed,
  onToggle,
  onNewChat,
  onSelectThread,
  userLabel,
  onLogout,
}: SidebarProps) {
  return (
    <aside className={`sidebar ${collapsed ? "sidebar--collapsed" : ""}`}>
      <div className="brand-row">
        <div className="brand-mark" aria-hidden="true">
          BC
        </div>
        {!collapsed && (
          <div>
            <strong>BC Legal AI</strong>
            <span>Associate</span>
          </div>
        )}
        <button className="icon-button sidebar-toggle" onClick={onToggle} aria-label="Toggle sidebar">
          {collapsed ? "›" : "‹"}
        </button>
      </div>

      <button className="new-chat-button" onClick={onNewChat}>
        <span>＋</span>
        {!collapsed && "New chat"}
      </button>

      {!collapsed && (
        <>
          <div className="sidebar-section-title">Recent chats</div>
          <div className="thread-list">
            {threads.length === 0 && (
              <p className="thread-meta" style={{ padding: "0 12px" }}>
                No chats yet — start one.
              </p>
            )}
            {threads.map((thread) => (
              <button
                key={thread.id}
                className={`thread-item ${thread.id === activeThreadId ? "thread-item--active" : ""}`}
                onClick={() => onSelectThread(thread.id)}
              >
                <span className="thread-title">{thread.title}</span>
                <span className="thread-meta">{thread.updatedAt}</span>
              </button>
            ))}
          </div>
        </>
      )}

      <div className="sidebar-footer">
        <div className="user-avatar">AI</div>
        {!collapsed && (
          <div className="user-info">
            <strong>{userLabel || "User"}</strong>
            <span>Not legal advice</span>
            {onLogout && (
              <button type="button" className="linkish" onClick={onLogout}>
                Sign out
              </button>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
