import { expect, test } from "@playwright/test";

test("second exposure shows the memory-hit banner", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("sk_consent_v1", "granted"));
  await page.goto("/simulate");
  await page.getByTestId("scenario").selectOption("kyc-expiry-bank");
  await page.getByTestId("start").click();
  await expect(page.getByRole("heading", { name: /simulation finished/i })).toBeVisible({ timeout: 60_000 });
  await page.getByTestId("start").click();
  await expect(page.getByTestId("memory-hit")).toContainText(/Recognised pattern from Incident #\d+/, {
    timeout: 45_000,
  });
});

test("parent view: check text and panic flow, Hindi toggle", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("sk_consent_v1", "granted"));
  await page.goto("/parent");
  await page.getByTestId("parent-text").fill(
    "You are under digital arrest. Do not tell anyone. Transfer Rs 50,000 to the RBI safe account now.",
  );
  await page.getByRole("button", { name: /^check$/i }).click();
  await expect(page.getByTestId("parent-verdict")).toHaveAttribute("data-level", /high|critical/);
  await expect(page.getByRole("link", { name: /call 1930/i }).first()).toHaveAttribute("href", "tel:1930");

  await page.getByTestId("panic-open").click();
  await page.getByLabel(/amount sent/i).fill("50000");
  await page.getByRole("button", { name: /prepare my steps/i }).click();
  await expect(page.getByTestId("panic-bundle")).toContainText("1930");

  await page.getByRole("button", { name: "हिन्दी" }).click();
  await expect(page.getByRole("heading", { name: "क्या यह ठगी है?" })).toBeVisible();
});

test("shield: pasted legit text stays low; delete-all works", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("sk_consent_v1", "granted"));
  await page.goto("/live");
  await page.getByTestId("paste").fill("Example Bank: Rs 1,250 debited. Never share your OTP with anyone.");
  await page.getByTestId("analyze").click();
  await expect(page.getByTestId("risk-level")).toHaveAttribute("data-level", "low", { timeout: 20_000 });

  await page.goto("/more");
  await page.getByTestId("delete-all").click();
  await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
  await expect(page.getByText(/all your data was deleted/i)).toBeVisible();
});

test("theme: light by default, switch to dark and it persists", async ({ page }) => {
  await page.goto("/");
  const html = page.locator("html");
  await expect(html).toHaveAttribute("data-theme", "light");
  await page.getByTestId("theme-dark").click();
  await expect(html).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(html).toHaveAttribute("data-theme", "dark");
  await page.getByTestId("theme-light").click();
  await expect(html).toHaveAttribute("data-theme", "light");
});

test("report assistant: copy-ready fields, official portal link, never submits", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("sk_consent_v1", "granted"));
  await page.goto("/live");
  await page.getByTestId("example-scam").click();
  await page.getByTestId("analyze").click();
  await expect(page.getByTestId("risk-level")).toHaveAttribute("data-level", "critical", { timeout: 20_000 });
  await page.getByRole("button", { name: /^stop$/i }).click();
  await page.getByTestId("to-report").click();
  await expect(page).toHaveURL(/\/report\?incident=\d+/);
  await expect(page.getByText(/never submits a report/i).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Suspect details" })).toBeVisible();
  await expect(page.getByTestId("copy-value").filter({ hasText: "simverify@examplebank" }).first()).toBeVisible();
  await expect(page.getByTestId("open-portal")).toHaveAttribute("href", "https://cybercrime.gov.in");
  await expect(page.getByRole("button", { name: /^submit/i })).toHaveCount(0);
  // step checklist persists progress
  await page.getByRole("checkbox").first().check();
  await expect(page.getByText(/1\/6 steps done/)).toBeVisible();
});

test("listen mode: tab opens, consent is requested before the mic starts", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("sk_consent_v1", "granted"));
  await page.goto("/live");
  await page.getByTestId("tab-listen").click();
  const toggle = page.getByTestId("listen-toggle");
  const unsupported = page.getByText(/cannot listen live/i);
  await expect(toggle.or(unsupported)).toBeVisible();
  if (await toggle.isVisible()) {
    await toggle.click();
    await expect(page.getByRole("dialog")).toContainText(/does not record or store audio/i);
    await page.getByRole("button", { name: /cancel/i }).click();
  }
});

// Keep the download test last: some browsers (Edge) tear down the browser after a blob download.
test("landing → consent → simulation → risk climbs → complaint PDF", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  // consent is required before any analysis
  await page.getByTestId("mode-simulate").click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText("30 days");
  const accept = dialog.getByRole("button", { name: /agree and continue/i });
  await expect(accept).toBeDisabled();
  await dialog.getByRole("checkbox").check();
  await accept.click();

  await expect(page).toHaveURL(/\/simulate/);
  await expect(page.getByText("SIMULATION", { exact: false }).first()).toBeVisible();

  await page.getByTestId("start").click();
  const level = page.getByTestId("risk-level");
  await expect(level).toHaveAttribute("data-level", "critical", { timeout: 45_000 });
  await expect(page.getByTestId("evidence")).toContainText("simverify@examplebank");
  await expect(page.getByTestId("transcript")).toContainText("Decoy");

  await expect(page.getByRole("heading", { name: /simulation finished/i })).toBeVisible({ timeout: 60_000 });
  const downloaded = page.waitForEvent("download");
  // noWaitAfter + catch: some browsers tear down the tab right after a blob download
  await page.getByTestId("dl-pdf").click({ noWaitAfter: true }).catch(() => undefined);
  const download = await downloaded;
  expect(download.suggestedFilename()).toMatch(/\.pdf$/);

  // the incident is listed
  // (fresh page: some browsers tear down the tab that triggered a blob download)
  const page2 = await page.context().newPage();
  await page2.goto("/incidents");
  await expect(page2.getByText("digital-arrest-parcel").first()).toBeVisible();
});
