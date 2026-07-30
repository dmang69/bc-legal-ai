/**
 * Desktop auto-update helpers (Tauri 2).
 * No-ops in pure browser / PWA builds.
 *
 * Upgrades:
 * - Desktop (Windows/macOS/Linux): GitHub Releases latest.json via tauri-plugin-updater
 * - Chrome PWA: browser fetch of new assets on reload
 * - Android / iOS: store versionCode / CFBundleVersion (not this module)
 */

export type UpdateCheckResult =
  | { available: false; reason: string }
  | {
      available: true;
      version: string;
      body?: string;
      date?: string;
    };

function isTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

/** Check for a newer desktop release. */
export async function checkForDesktopUpdate(): Promise<UpdateCheckResult> {
  if (!isTauri()) {
    return { available: false, reason: "not_tauri_shell" };
  }
  try {
    const { check } = await import("@tauri-apps/plugin-updater");
    const update = await check();
    if (!update) {
      return { available: false, reason: "up_to_date" };
    }
    return {
      available: true,
      version: update.version,
      body: update.body ?? undefined,
      date: update.date ?? undefined,
    };
  } catch (e) {
    return {
      available: false,
      reason: e instanceof Error ? e.message : String(e),
    };
  }
}

/** Download + install desktop update, then relaunch. */
export async function installDesktopUpdateAndRelaunch(): Promise<void> {
  if (!isTauri()) {
    throw new Error("Desktop updates only run inside the Tauri shell");
  }
  const { check } = await import("@tauri-apps/plugin-updater");
  const { relaunch } = await import("@tauri-apps/plugin-process");
  const update = await check();
  if (!update) {
    throw new Error("No update available");
  }
  await update.downloadAndInstall();
  await relaunch();
}
