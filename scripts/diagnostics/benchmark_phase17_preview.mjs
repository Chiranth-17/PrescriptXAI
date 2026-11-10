import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import path from "node:path";
import { cpus, platform, release } from "node:os";

const [address, output, configPath] = process.argv.slice(2);
const { PSX_PHASE17_PLAYWRIGHT: modulePath, PSX_PHASE17_CHROMIUM: executablePath,
  PSX_PHASE17_SOURCE: source } = process.env;
if (!address || !output || !configPath || !modulePath || !executablePath || !source) {
  throw new Error("Supply local server, output, committed plan, Playwright, Chromium and source");
}
const origin = new URL(address).origin;
if (new URL(origin).hostname !== "127.0.0.1") throw new Error("Expected a loopback server");
const planBytes = await fs.readFile(configPath);
const plan = JSON.parse(planBytes);
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const { chromium } = createRequire(import.meta.url)(modulePath);
const trials = await fs.open(path.join(output, "trials.jsonl"), "wx");
const started = new Date().toISOString();
const groups = [];
let browser;
let status = "failed";
let failure = null;

async function writeTrial(row) {
  await trials.appendFile(JSON.stringify(row) + "\n");
  await trials.sync();
}

function summarize(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const rank = (p) => sorted[Math.ceil(p * sorted.length) - 1];
  return { p50: rank(0.5), p95: rank(0.95), max: sorted.at(-1) };
}

async function selectPreset(page, preset) {
  await page.getByRole("button", { name: preset.name, exact: true }).click();
  await page.waitForFunction(({ preset, machine }) => {
    const query = new URL(location.href).searchParams;
    const app = document.querySelector('[data-testid="stApp"]');
    return query.get("machine") === machine && query.get("unit") === preset.unit
      && Number(query.get("time")) === preset.time && query.get("settings") === "{}"
      && app?.getAttribute("data-test-script-state") === "notRunning";
  }, { preset, machine: plan.machine_id }, { timeout: plan.trial_timeout_ms });
  if (plan.publication_mode === "Demonstration limits: not confirmed by an engineer") {
    await page.getByText("Calculating…", { exact: true }).waitFor({
      state: "hidden", timeout: plan.trial_timeout_ms,
    });
  }
}

async function measure(page, slider, key, before, preset) {
  await page.evaluate(({ key, before, preset, machine, spec }) => {
    window.psxPreviewTiming = null;
    function start(event) {
      if (!event.isTrusted || event.key !== key || event.target?.type !== "range") return;
      document.removeEventListener("keydown", start, true);
      const begin = performance.now();
      function frame() {
        const query = new URL(location.href).searchParams;
        const app = document.querySelector('[data-testid="stApp"]');
        const caption = [...document.querySelectorAll("p")].find((p) =>
          p.textContent?.includes("Predicted risk for the selected conditions"));
        const score = document.querySelector('[data-testid="stMetricValue"]')?.textContent;
        const elapsed = caption?.textContent?.match(/· ([\d.]+) ms$/)?.[1];
        if (query.get("settings") !== before && app?.getAttribute("data-test-script-state")
            === "notRunning" && /^\d+(\.\d+)?%$/.test(score ?? "") && elapsed !== undefined) {
          window.psxPreviewTiming = {
            browser_ms: performance.now() - begin,
            server_ms: Number(elapsed),
            risk: score,
            settings: query.get("settings"),
            scope_matches: query.get("machine") === machine && query.get("spec") === spec
              && query.get("unit") === preset.unit && Number(query.get("time")) === preset.time,
          };
        } else {
          requestAnimationFrame(frame);
        }
      }
      requestAnimationFrame(frame);
    }
    document.addEventListener("keydown", start, true);
  }, { key, before, preset, machine: plan.machine_id, spec: plan.spec_hash });
  await slider.press(key);
  const result = await page.waitForFunction(() => window.psxPreviewTiming, null,
    { timeout: plan.trial_timeout_ms });
  return result.jsonValue();
}

try {
  browser = await chromium.launch({ headless: true, executablePath });
  for (const { name, width, height } of plan.viewport_order) {
    const context = await browser.newContext({ viewport: { width, height }, colorScheme: "light" });
    const external = [];
    await context.route("**/*", async (route) => {
      if (new URL(route.request().url()).origin === origin) await route.continue();
      else {
        external.push(route.request().url());
        await route.abort();
      }
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(String(error)));
    await page.goto(address, { waitUntil: "domcontentloaded" });
    await page.getByText("Predicted risk now", { exact: true }).waitFor();
    const limitsLabel = plan.publication_mode === "Alerts only"
      ? "Alerts only: limits not yet confirmed by an engineer" : plan.publication_mode;
    await page.getByText(limitsLabel, { exact: true }).first().waitFor();
    for (const preset of plan.preset_order) {
      await selectPreset(page, preset);
      const slider = page.locator(
        '[data-testid="stSlider"] input[type="range"]:not([aria-label="Recorded time"])'
      ).first();
      const endpoint = new Map();
      const measured = [];
      let previousKey;
      const count = plan.warmups_per_preset_viewport + plan.measured_per_preset_viewport;
      for (let index = 0; index < count; index++) {
        const sample = { viewport: name, preset, trial: index + 1,
          warmup: index < plan.warmups_per_preset_viewport };
        try {
          const { value, max, min, label } = await slider.evaluate((element) => ({
            value: Number(element.value), min: Number(element.min), max: Number(element.max),
            label: element.getAttribute("aria-label"),
          }));
          if (!Number.isFinite(min) || !Number.isFinite(max) || min >= max || !label) {
            throw new Error("Missing measurable control");
          }
          const key = previousKey
            ? (previousKey === "End" ? "Home" : "End")
            : (value === max ? "Home" : "End");
          const before = new URL(page.url()).searchParams.get("settings");
          Object.assign(sample, { key, control: label, before });
          const result = await measure(page, slider, key, before, preset);
          Object.assign(sample, result);
          const setting = JSON.parse(result.settings);
          if (!result.scope_matches || Object.keys(setting).length > 1
              || Object.values(setting).some((item) => !Number.isFinite(item))
              || !Number.isFinite(result.browser_ms) || !Number.isFinite(result.server_ms)
              || pageErrors.length || external.length) {
            throw new Error("Incomplete or mismatched preview");
          }
          const identity = JSON.stringify([label, result.settings, result.risk]);
          if (endpoint.has(key) && endpoint.get(key) !== identity) {
            throw new Error("Control endpoint or displayed risk changed across repetitions");
          }
          endpoint.set(key, identity);
          previousKey = key;
          await writeTrial(sample);
          if (!sample.warmup) measured.push(sample);
        } catch (error) {
          await writeTrial({ ...sample, error: String(error), pageErrors, external });
          throw error;
        }
      }
      if (endpoint.size !== 2 || endpoint.get("Home") === endpoint.get("End")) {
        throw new Error("Expected two distinct control endpoints");
      }
      const browserMs = summarize(measured.map((sample) => sample.browser_ms));
      const serverMs = summarize(measured.map((sample) => sample.server_ms));
      groups.push({ viewport: name, width, height, preset, control: measured[0].control,
        count: measured.length, browser_ms: browserMs, server_ms: serverMs,
        browser_under_target: browserMs.p95 < plan.instant_target_ms });
    }
    await context.close();
  }
  status = "complete";
} catch (error) {
  failure = String(error);
  process.exitCode = 1;
} finally {
  const browserVersion = browser?.version();
  await browser?.close();
  await trials.close();
  const receipt = { status, failure, source, config: configPath, config_sha256: hash(planBytes),
    started_utc: started, completed_utc: new Date().toISOString(),
    host: { platform: platform(), release: release(), logical_cpu_count: cpus().length,
      cpu: cpus()[0]?.model, node: process.version, chromium: browserVersion },
    plan, groups };
  await fs.writeFile(path.join(output, "summary.json"), JSON.stringify(receipt, null, 2) + "\n",
    { flag: "wx" });
  console.log(JSON.stringify({ status, failure, groups }));
}
