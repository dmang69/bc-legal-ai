const blockedPatterns: Array<{ label: string; pattern: RegExp }> = [
  { label: "possible BC court file number", pattern: /\b[A-Z]{2,5}-S-[A-Z]-?\d{4,8}\b/i },
  { label: "possible RTB file number", pattern: /\b9\d{8}\b/ },
  { label: "possible email address", pattern: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i },
  { label: "possible Canadian postal code", pattern: /\b[A-Z]\d[A-Z][ -]?\d[A-Z]\d\b/i },
];

export function findSensitiveText(value: string): string[] {
  return blockedPatterns
    .filter(({ pattern }) => pattern.test(value))
    .map(({ label }) => label);
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
