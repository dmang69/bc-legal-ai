import type { ChatThread } from "../types";

interface SidebarProps {
  threads: ChatThread[];
  activeThreadId: string;
  collapsed: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  onSelectThread: (id: string) => void;
}

const navigation = ["Chat", "Matters", "Documents", "Evidence", "Research", "Drafts", "Agents", "Calendar", "Tasks", "Downloads"];

export function Sidebar({
  threads,
  activeThreadId,
  collapsed,
  onToggle,
  onNewChat,
  onSelectThread,
}: SidebarProps) {
  return (
    <aside className={`sidebar ${collapsed ? "sidebar--collapsed" : ""}`}>
      <div className="brand-row">
        <div className="brand-mark" aria-hidden="true">BC</div>
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
        <span>＋</span>{!collapsed && "New chat"}
      </button>

      {!collapsed && (
        <>
          <nav className="primary-nav" aria-label="Primary">
            {navigation.map((item, index) => (
              <button className={index === 0 ? "nav-item nav-item--active" : "nav-item"} key={item}>
                <span className="nav-dot" />
                {item}
              </button>
            ))}
          </nav>

          <div className="sidebar-section-title">Recent chats</div>
          <div className="thread-list">
            {threads.map((thread) => (
              <button
                key={thread.id}
                className={`thread-item ${thread.id === activeThreadId ? "thread-item--active" : ""}`}
                onClick={() => onSelectThread(thread.id)}
              >
                <span className="thread-title">{thread.title}</span>
                <span className="thread-meta">{thread.pinned ? "Pinned · " : ""}{thread.updatedAt}</span>
              </button>
            ))}
          </div>
        </>
      )}

      <div className="sidebar-footer">
        <div className="user-avatar">DO</div>
        {!collapsed && (
          <div className="user-info">
            <strong>Development User</strong>
            <span>Public demo mode</span>
          </div>
        )}
      </div>
    </aside>
  );
}
