import { defineConfig, devices } from "@playwright/test";
import path from "node:path";
import os from "node:os";

const dbFile = path.join(os.tmpdir(), `scamkhel-e2e-${process.pid}.db`).split(path.sep).join("/");

export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: "http://localhost:3000", trace: "retain-on-failure", acceptDownloads: true },
  projects: [
    {
      name: "chromium",
      // PW_CHANNEL=msedge|chrome runs the system browser (useful where the bundled Chromium cannot launch)
      use: { ...devices["Desktop Chrome"], ...(process.env.PW_CHANNEL ? { channel: process.env.PW_CHANNEL } : {}) },
    },
  ],
  webServer: [
    {
      // Backend in offline mode (no API keys needed): rules + scripted fallbacks, real DB, real PDF.
      command: "python -m uvicorn app.main:create_app --factory --port 8000",
      cwd: "../backend",
      url: "http://localhost:8000/healthz",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        DATABASE_URL: `sqlite+aiosqlite:///${dbFile}`,
        FRONTEND_ORIGIN: "http://localhost:3000",
        LLM_OFFLINE: "true",
        PER_IP_SESSIONS_PER_HOUR: "100",
      },
    },
    {
      command: "npm run dev",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: { NEXT_PUBLIC_API_URL: "http://localhost:8000" },
    },
  ],
});
