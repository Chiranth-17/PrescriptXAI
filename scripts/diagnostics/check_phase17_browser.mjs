// Render the actual local simulator at both registered viewport widths.
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import path from "node:path";

const [address, output] = process.argv.slice(2);
const modulePath = process.env.PSX_PHASE17_PLAYWRIGHT;
const executablePath = process.env.PSX_PHASE17_CHROMIUM;
const colorScheme = process.env.PSX_PHASE17_COLOR_SCHEME || "light";
if (!["light", "dark"].includes(colorScheme)) throw new Error("Expected light or dark theme");
if (!address || !output || !modulePath || !executablePath) {
  throw new Error("Supply the local address, output directory, Playwright module and Chromium executable");
}
const origin = new URL(address).origin;
const { chromium } = createRequire(import.meta.url)(modulePath);
const browser = await chromium.launch({ headless: true, executablePath });
const results = [];
const limitsLabel = "Demonstration limits: not confirmed by an engineer";

async function presetAccess(button) {
  return button.evaluate((element) => {
    const numbers = (color) => color.match(/[\d.]+/g).map(Number);
    const luminance = ([r, g, b]) =>
      [r, g, b].map((v) => {
        const value = v / 255;
        return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
      }).reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
    let surface = element;
    let background;
    while (surface && !background) {
      const rgb = numbers(getComputedStyle(surface).backgroundColor);
      if (rgb.length === 3 || rgb[3] === 1) background = rgb;
      surface = surface.parentElement;
    }
    const style = getComputedStyle(element);
    const levels = [luminance(numbers(style.color)), luminance(background || [255, 255, 255])];
    return {
      buttonHeight: element.getBoundingClientRect().height,
      contrast: (Math.max(...levels) + 0.05) / (Math.min(...levels) + 0.05),
      focusVisible: document.activeElement === element && element.matches(":focus-visible")
        && style.outlineStyle !== "none" && parseFloat(style.outlineWidth) >= 2,
    };
  });
}
async function keyboardSettings(page, originalRisk) {
  const controls = page.locator(
    '[data-testid="stSlider"] input[type="range"]:not([aria-label="Recorded time"])'
  );
  const value = page.locator('[data-testid="stMetricValue"]').first();
  const edits = [];
  for (let index = 0; index < await controls.count(); index++) {
    const control = controls.nth(index);
    const { now, maximum } = await control.evaluate((element) => ({
      now: Number(element.value),
      maximum: Number(element.max),
    }));
    const before = new URL(page.url()).searchParams.get("settings");
    const key = now === maximum ? "Home" : "End";
    await control.press(key);
    const sliderFocus = await control.evaluate((element) => {
      const style = getComputedStyle(element.closest('[data-testid="stSlider"]'));
      return element.matches(":focus-visible") && style.outlineStyle !== "none"
        && parseFloat(style.outlineWidth) >= 2;
    });
    if (!sliderFocus) throw new Error("Adjustable slider has no visible focus outline");
    try {
      await page.waitForFunction((previous) =>
        new URL(location.href).searchParams.get("settings") !== previous
        && document.querySelector('[data-testid="stApp"]')?.getAttribute("data-test-script-state") === "notRunning",
      before, { timeout: 5000 });
    } catch (error) {
      const state = await control.evaluate((element) => ({
        markup: element.outerHTML, focused: document.activeElement === element,
        input: new URL(location.href).searchParams.get("settings"),
      }));
      throw new Error("Keyboard did not update the slider: " + JSON.stringify(state), { cause: error });
    }
    const risk = await value.innerText();
    const settings = new URL(page.url()).searchParams.get("settings");
    edits.push({ settings, risk });
    if (risk !== originalRisk) {
      await page.reload({ waitUntil: "domcontentloaded" });
      await page.waitForFunction((expected) =>
        document.querySelector('[data-testid="stMetricValue"]')?.textContent === expected,
      risk);
      if (new URL(page.url()).searchParams.get("settings") !== settings) {
        throw new Error("Reloaded link did not restore the keyboard settings");
      }
      return { edits, restored: true, sliderFocus: true };
    }
  }
  throw new Error("No keyboard-edited control changed the displayed risk");
}

try {
  for (const [name, width, height] of [["desktop", 1360, 900], ["phone", 390, 844]]) {
    const context = await browser.newContext({ viewport: { width, height }, colorScheme });
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
    await preset.focus();
    const accessibility = await presetAccess(preset);
    if (accessibility.buttonHeight < 44 || accessibility.contrast < 4.5 || !accessibility.focusVisible) {
      throw new Error("Preset accessibility failed: " + JSON.stringify(accessibility));
    }
    const targetSizes = await page.evaluate(() => {
      const sizes = (selector) => [...document.querySelectorAll(selector)]
        .filter((element) => element.getBoundingClientRect().width > 0)
        .map((element) => element.getBoundingClientRect().height);
      return {
        actions: sizes(".stButton button, .stDownloadButton button"),
        selectors: sizes('.stSelectbox [role="combobox"]'),
        expanders: sizes(".stExpander summary"),
      };
    });
    if (Object.values(targetSizes).some((sizes) => !sizes.length || Math.min(...sizes) < 44)) {
      const selector = await page.locator('[data-testid="stSelectbox"]').first().innerHTML();
      throw new Error("Dashboard target heights failed: " + JSON.stringify(targetSizes) + " " + selector);
    }
    await preset.press("Enter");
    await page.waitForFunction((unit) => {
      const current = new URL(location.href).searchParams.get("unit");
      return current && current !== unit
        && document.querySelector('[data-testid="stApp"]')?.getAttribute("data-test-script-state") === "notRunning";
    }, before);
    const cards = ["1. Set the conditions", "2. Predicted risk", "3. Prescription", "4. Was it followed?"];
    for (const title of cards) await page.getByRole("heading", { name: title, exact: true }).waitFor();
    await page.getByText(limitsLabel, { exact: true }).first().waitFor();
    await page.getByText("Predicted risk with the prescription", { exact: true }).waitFor({
      timeout: 90000,
    });
    await page.getByRole("button", { name: "Record this follow-up" }).waitFor();
    const about = page.locator("details").filter({ hasText: "About this view and how it was checked" });
    await about.locator("summary").click();
    await about.getByText(limitsLabel, { exact: true }).waitFor();
    await about.locator("summary").click();
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
    if (!report.includes(limitsLabel)
        || !report.includes("Predicted risk now: " + risk)
        || !report.includes("Synthetic or sample machine data")
        || !report.includes("Predicted risk with prescription:")) {
      throw new Error("Downloaded scenario does not match the demonstration view");
    }
    const keyboard = await keyboardSettings(page, risk);
    if (await page.getByText("Predicted risk with the prescription", { exact: true }).count()
        || await page.getByRole("button", { name: "Record this follow-up" }).count()) {
      throw new Error("A manual edit retained a recorded-input prescription");
    }
    if (errors.length || external.length) {
      throw new Error(JSON.stringify({ errors, external }));
    }
    const reportSha256 = createHash("sha256").update(report).digest("hex");
    results.push({
      name, viewport: { width, height }, captureHeight, bounds, risk, sha256, file,
      reportFile, reportSha256, accessibility, keyboard, colorScheme, targetSizes,
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
