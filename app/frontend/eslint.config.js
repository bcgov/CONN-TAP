// eslint.config.js
import { defineConfig } from "eslint/config";
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import globals from "globals";

export default defineConfig([
  // Base JS
  {
    files: ["**/*.{js,mjs,cjs}"],
    ...js.configs.recommended,
  },

  // TypeScript
  ...tseslint.configs.recommended,

  // App config
  {
    files: ["**/*.{ts,tsx,js,jsx}"],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      "no-unused-vars": "warn",
      "no-console": "warn",
    },
  },
]);