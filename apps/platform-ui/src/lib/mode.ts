/** Product surface modes (Section G §4). */

export type AppMode = "workbench" | "client" | "self_rep" | "portal";

export function getAppMode(): AppMode {
  const raw = (import.meta.env.VITE_APP_MODE as string | undefined)?.toLowerCase() ?? "portal";
  if (raw === "workbench" || raw === "client" || raw === "self_rep" || raw === "portal") {
    return raw;
  }
  return "portal";
}
