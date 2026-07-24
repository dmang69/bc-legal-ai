/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_APP_MODE?: "public_demo" | "private";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
