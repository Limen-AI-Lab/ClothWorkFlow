/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GEMINI_API_KEY: string
  readonly VITE_GEMINI_IMAGE_MODEL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
