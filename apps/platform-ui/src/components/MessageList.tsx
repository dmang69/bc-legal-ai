import type { ChatMessage } from "../types";

interface MessageListProps {
  messages: ChatMessage[];
}

function renderContent(content: string) {
  const lines = content.split("\n");
  return lines.map((line, index) => (
    <span key={`${index}-${line.slice(0, 12)}`}>
      {line}
      {index < lines.length - 1 && <br />}
    </span>
  ));
}

export function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <section className="message-list empty-state">
        <div className="empty-card">
          <h2>Start a conversation</h2>
          <p>
            Use slash tools (<code>/summarize</code>, <code>/research</code>, <code>/code</code>), pick a
            provider (Ollama / safe local), or open Arena and Org Admin in the work panel.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="message-list" aria-live="polite">
      {messages.map((message) => (
        <article className={`message message--${message.role}`} key={message.id}>
          <div className="message-avatar" aria-hidden="true">
            {message.role === "assistant" ? "AI" : message.role === "user" ? "YOU" : "!"}
          </div>
          <div className="message-body">
            <div className="message-heading">
              <strong>
                {message.role === "assistant"
                  ? "BC Legal AI Associate"
                  : message.role === "user"
                    ? "You"
                    : "System"}
              </strong>
              <span>{message.createdAt}</span>
              {message.provider && (
                <span className="provider-pill">
                  {message.provider}
                  {message.model ? `/${message.model}` : ""}
                </span>
              )}
            </div>
            <div className="message-content">{renderContent(message.content)}</div>

            {message.warnings && message.warnings.length > 0 && (
              <div className="warning-stack">
                {message.warnings.map((w) => (
                  <div className="inline-warning" key={w.slice(0, 40)}>
                    {w}
                  </div>
                ))}
              </div>
            )}

            {message.toolActivity && message.toolActivity.length > 0 && (
              <div className="tool-row">
                {message.toolActivity.map((t) => (
                  <span className="tool-chip" key={t}>
                    {t}
                  </span>
                ))}
              </div>
            )}

            {message.actions && message.actions.length > 0 && (
              <div className="message-actions">
                {message.actions.map((a) => (
                  <button type="button" key={a.id}>
                    {a.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </article>
      ))}
    </section>
  );
}
