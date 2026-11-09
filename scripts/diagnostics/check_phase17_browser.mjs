// Render the actual local simulator at both registered viewport widths.
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import path from "node:path";

const [address, output] = process.argv.slice(2);
const modulePath = process.env.PSX_PHASE17_PLAYWRIGHT;
const executablePath = process.env.PSX_PHASE17_CHROMIUM;
if (!address || !output || !modulePath || !executablePath) {
  throw new Error("Supply the local address, output directory, Playwright module and Chromium executable");
}
const origin = new URL(address).origin;
const { chromium } = createRequire(import.meta.url)(modulePath);
const browser = await chromium.launch({ headless: true, executablePath });
const results = [];
try {
  for (const [name, width, height] of [["desktop", 1360, 900], ["phone", 390, 844]]) {
    const context = await browser.newContext({ viewport: { width, height }, colorScheme: "light" });
    const external = [];
    await context.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.origin !== origin) {
        external.push(url.origin);
        await route.abort();
      } else {
        await route.continue();
      }
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    await page.goto(address, { waitUntil: "domcontentloaded" });
    await page.getByRole("heading", { name: "PrescriptXAI Operations Dashboard" }).waitFor();
    await page.getByText("Predicted risk now", { exact: true }).waitFor();
    const preset = page.getByRole("button", { name: "Case study (selected by rule)" });
    const before = new URL(page.url()).searchParams.get("unit");
    await preset.click();
    await page.waitForFunction((unit) => {
      const current = new URL(location.href).searchParams.get("unit");
      return current && current !== unit
        && document.querySelector('[data-testid="stApp"]')?.getAttribute("data-test-script-state") === "notRunning";
    }, before);
    const cards = ["1. Set the conditions", "2. Predicted risk", "3. Prescription", "4. Was it followed?"];
    for (const title of cards) await page.getByRole("heading", { name: title, exact: true }).waitFor();
    await page.getByText("Alerts only: limits not yet confirmed by an engineer", { exact: true }).waitFor();
    if (await page.getByText("Predicted risk with the prescription", { exact: true }).count()
        || await page.getByRole("button", { name: "Record this follow-up" }).count()) {
      throw new Error("An unconfirmed machine offered a prescription");
    }
    const bounds = await page.evaluate(() => ({
      viewportWidth: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
    }));
    if (bounds.viewportWidth !== width || bounds.documentWidth > width) {
      throw new Error("Dashboard overflowed the requested viewport");
    }
    if (errors.length || external.length) {
      throw new Error(JSON.stringify({ errors, external }));
    }
    await page.getByRole("heading", { name: "PrescriptXAI Operations Dashboard" }).click();
    await page.mouse.move(width - 2, 62);
    await page.getByText("Example selected by rule", { exact: true }).waitFor({ state: "hidden" });
    const pageHeight = await page.locator('[data-testid="stMain"]').evaluate((main) => main.scrollHeight);
    const captureHeight = Math.max(height, pageHeight + 60);
    await page.setViewportSize({ width, height: captureHeight });
    const file = path.join(output, name + ".png");
    await page.screenshot({ path: file, fullPage: true });
    const sha256 = createHash("sha256").update(await fs.readFile(file)).digest("hex");
    const risk = await page.locator('[data-testid="stMetricValue"]').first().innerText();
    const downloadReady = page.waitForEvent("download");
    await page.getByRole("button", { name: "Download scenario report" }).click();
    const download = await downloadReady;
    const reportFile = path.join(output, name + "-scenario.html");
    await download.saveAs(reportFile);
    const report = await fs.readFile(reportFile, "utf8");
    if (!report.includes("Alerts only: limits not yet confirmed by an engineer.")
        || !report.includes("Predicted risk now: " + risk)
        || !report.includes("Synthetic or sample machine data")
        || report.includes("Predicted risk with prescription:")) {
      throw new Error("Downloaded scenario does not match the Alerts-only view");
    }
    if (errors.length || external.length) {
      throw new Error(JSON.stringify({ errors, external }));
    }
    const reportSha256 = createHash("sha256").update(report).digest("hex");
    results.push({
      name, viewport: { width, height }, captureHeight, bounds, risk, sha256, file,
      reportFile, reportSha256,
    });
    await context.close();
  }
} finally {
  await browser.close();
}
await fs.writeFile(path.join(output, "browser.json"), JSON.stringify(results, null, 2) + "\n", {
  flag: "wx",
});
console.log(JSON.stringify(results));
