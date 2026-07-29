import type { ChatMessage } from "../types";

interface MessageListProps {
  messages: ChatMessage[];
}

function renderContent(content: string) {
  return content.split("\n").map((line, index) => (
    <span key={`${line}-${index}`}>
      {line}
      {index < content.split("\n").length - 1 && <br />}
    </span>
  ));
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <section className="message-list" aria-live="polite">
      {messages.map((message) => (
        <article className={`message message--${message.role}`} key={message.id}>
          <div className="message-avatar" aria-hidden="true">
            {message.role === "assistant" ? "AI" : message.role === "user" ? "YOU" : "!"}
          </div>
          <div className="message-body">
            <div className="message-heading">
              <strong>{message.role === "assistant" ? "BC Legal AI Associate" : message.role === "user" ? "You" : "System notice"}</strong>
              <span>{message.createdAt}</span>
            </div>
            <div className="message-content">{renderContent(message.content)}</div>

            {message.citations && message.citations.length > 0 && (
              <div className="citation-row">
                {message.citations.map((citation) => (
                  <button className="citation-card" key={citation.id}>
                    <span className={`citation-status citation-status--${citation.status}`} />
                    <span>
                      <strong>{citation.title}</strong>
                      <small>{citation.locator} · {citation.status}</small>
                    </span>
                  </button>
                ))}
              </div>
            )}

            {message.role === "assistant" && message.status !== "streaming" && (
              <div className="message-actions">
                <button>Open analysis</button>
                <button>Add to draft</button>
                <button>Verify sources</button>
                <button>Ask Devil's Advocate</button>
              </div>
            )}
          </div>
        </article>
      ))}
    </section>
  );
}
