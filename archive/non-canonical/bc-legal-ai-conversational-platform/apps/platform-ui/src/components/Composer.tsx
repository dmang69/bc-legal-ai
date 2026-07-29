import { useRef } from "react";
import type { AgentDefinition, AppMode, AttachmentItem } from "../types";
import { formatFileSize } from "../lib/security";

interface ComposerProps {
  value: string;
  appMode: AppMode;
  busy: boolean;
  attachments: AttachmentItem[];
  agents: AgentDefinition[];
  selectedAgentId: string;
  warning: string | null;
  onChange: (value: string) => void;
  onAgentChange: (agentId: string) => void;
  onFilesSelected: (files: FileList) => void;
  onRemoveAttachment: (id: string) => void;
  onSend: () => void;
}

export function Composer({
  value,
  appMode,
  busy,
  attachments,
  agents,
  selectedAgentId,
  warning,
  onChange,
  onAgentChange,
  onFilesSelected,
  onRemoveAttachment,
  onSend,
}: ComposerProps) {
  const fileInput = useRef<HTMLInputElement>(null);

  return (
    <div className="composer-shell">
      {warning && <div className="composer-warning">{warning}</div>}
      {attachments.length > 0 && (
        <div className="attachment-list">
          {attachments.map((attachment) => (
            <div className={`attachment-chip attachment-chip--${attachment.state}`} key={attachment.id}>
              <div>
                <strong>{attachment.name}</strong>
                <span>{formatFileSize(attachment.size)} · {attachment.state}{attachment.reason ? ` · ${attachment.reason}` : ""}</span>
              </div>
              <button onClick={() => onRemoveAttachment(attachment.id)} aria-label={`Remove ${attachment.name}`}>×</button>
            </div>
          ))}
        </div>
      )}

      <div className="composer">
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Ask BC Legal AI Associate…"
          rows={3}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              onSend();
            }
          }}
        />

        <div className="composer-toolbar">
          <div className="composer-tools">
            <input
              ref={fileInput}
              hidden
              type="file"
              multiple
              onChange={(event) => event.target.files && onFilesSelected(event.target.files)}
            />
            <button onClick={() => fileInput.current?.click()} title="Attach files">＋ Attach</button>
            <button title="Voice input">◉ Voice</button>
            <button title="Enable tools">⌘ Tools</button>
            <select value={selectedAgentId} onChange={(event) => onAgentChange(event.target.value)} aria-label="Select agent">
              {agents.map((agent) => <option value={agent.id} key={agent.id}>{agent.name}</option>)}
            </select>
          </div>
          <div className="send-area">
            <span>{appMode === "public_demo" ? "Synthetic data only" : "Matter-restricted"}</span>
            <button className="send-button" disabled={busy || !value.trim()} onClick={onSend}>
              {busy ? "Working…" : "Send"}
            </button>
          </div>
        </div>
      </div>
      <div className="composer-disclaimer">AI-generated legal work requires evidence, citation, privilege, procedural, and human review.</div>
    </div>
  );
}
