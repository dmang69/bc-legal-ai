/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_APP_MODE?: "public_demo" | "private";
  /** Default Puter model id (https://developer.puter.com/ai/) */
  readonly VITE_PUTER_MODEL?: string;
  /** Default Kimi model via Puter (moonshotai/kimi-k2.5) */
  readonly VITE_KIMI_MODEL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

/** Global injected by https://js.puter.com/v2/ */
interface Window {
  puter?: {
    ai?: {
      chat: (...args: unknown[]) => Promise<unknown>;
      listModels?: () => Promise<unknown>;
    };
  };
}
