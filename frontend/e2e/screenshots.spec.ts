// Captures the README screenshots from the real running app (offline mode).
// Run:  SCREENSHOTS=1 PW_CHANNEL=msedge npx playwright test screenshots
import path from "node:path";
import { expect, test } from "@playwright/test";

const OUT = path.resolve(__dirname, "../../docs/screenshots");
test.skip(!process.env.SCREENSHOTS, "set SCREENSHOTS=1 to regenerate docs/screenshots");
test.use({ viewport: { width: 1360, height: 900 }, colorScheme: "dark" });

const consent = (page: import("@playwright/test").Page) =>
  page.addInitScript(() => window.localStorage.setItem("sk_consent_v1", "granted"));

test("landing", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.screenshot({ path: `${OUT}/01-landing.png` });
  await page.getByTestId("mode-simulate").click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.screenshot({ path: `${OUT}/02-consent.png` });
});

test("simulate", async ({ page }) => {
  await consent(page);
  await page.goto("/simulate");
  await page.getByTestId("start").click();
  await expect(page.getByTestId("risk-level")).toHaveAttribute("data-level", "critical", { timeout: 45_000 });
  await expect(page.getByRole("heading", { name: /simulation finished/i })).toBeVisible({ timeout: 60_000 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `${OUT}/03-simulate.png`, fullPage: true });
  // second run of a seen script -> memory banner
  await page.getByTestId("start").click();
  await expect(page.getByTestId("memory-hit")).toBeVisible({ timeout: 45_000 });
  await expect(page.getByRole("heading", { name: /simulation finished/i })).toBeVisible({ timeout: 60_000 });
  await page.screenshot({ path: `${OUT}/04-memory-hit.png`, fullPage: true });
});

test("shield and parent", async ({ page }) => {
  await consent(page);
  await page.goto("/live");
  await page.getByTestId("paste").fill(
    "This is Inspector Rao (SIMULATION). Your Aadhaar is linked to money laundering, a warrant is ready.\n" +
      "You are under digital arrest. Stay on the video call and do not tell anyone.\n" +
      "Transfer Rs 90,000 to the RBI safe account simverify@examplebank now.",
  );
  await page.getByTestId("analyze").click();
  await expect(page.getByTestId("risk-level")).toHaveAttribute("data-level", "critical", { timeout: 20_000 });
  await page.screenshot({ path: `${OUT}/05-shield.png`, fullPage: true });

  await page.setViewportSize({ width: 430, height: 900 });
  await page.goto("/parent");
  await page.getByTestId("parent-text").fill("You are under digital arrest. Transfer Rs 50,000 to the safe account now.");
  await page.getByRole("button", { name: /^check$/i }).click();
  await expect(page.getByTestId("parent-verdict")).toBeVisible();
  await page.screenshot({ path: `${OUT}/06-parent-mobile.png`, fullPage: true });
});

test("light mode and about", async ({ page }) => {
  await consent(page);
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/about");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.screenshot({ path: `${OUT}/07-about-light.png`, fullPage: true });
});
