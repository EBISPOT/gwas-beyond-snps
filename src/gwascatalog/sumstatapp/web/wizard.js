/**
 * wizard.js — Minimal wizard navigation and PyScript bridge.
 *
 * This is the only JavaScript in the application. All validation logic lives
 * in Python (validate.py) running via PyScript/Pyodide.
 *
 * Interface (modelled on the pandoc wasm app):
 *
 *   validateFile()   — read wizard config + file, call Python, display results
 *   downloadOutput() — trigger standard file download of validated output
 *
 * Responsibilities:
 *   1. Wizard step navigation (show/hide sections via hidden attribute)
 *   2. Form state management (enable/disable Next based on input)
 *   3. Streaming file upload to Emscripten VFS (via FS API, no Python bridge)
 *   4. Bridge to Python validate_file(config_json) — file lives in VFS
 *   5. Display structured validation results returned by Python
 *   6. Download of validated output from VFS (via FS API, no Python bridge)
 */

"use strict";

// ── Constants ────────────────────────────────────────────────────
const STEPS = [
  "welcome",
  "variation",
  "effect-size",
  "p-value",
  "significance",
  "file",
  "validate",
];

const LOADING_MESSAGE =  "Validating summary statistics in your browser. Nothing is being sent to the server."

let currentStep = 0;
let hasValidatedOutput = false; // Whether validated output exists in VFS

// ── Web Worker (Pyodide runs off the main thread) ────────────────

let worker = null;
let workerReady = false;
let _nextId = 0;
const _pending = new Map();

/** Send a message to the validation worker and return a promise for the result. */
function callWorker(type, payload = {}, transfer = []) {
  return new Promise((resolve, reject) => {
    const id = ++_nextId;
    _pending.set(id, { resolve, reject });
    worker.postMessage({ type, id, ...payload }, transfer);
  });
}

// ── Wizard navigation ────────────────────────────────────────────

function goToStep(index) {
  STEPS.forEach((id, i) => {
    const el = document.getElementById(`step-${id}`);
    if (el) el.hidden = i !== index;
  });
  currentStep = index;
  updateProgress();

  if (STEPS[currentStep] === "validate") populateSummary();

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function next() {
  if (currentStep < STEPS.length - 1) goToStep(currentStep + 1);
}

function prev() {
  if (currentStep > 0) goToStep(currentStep - 1);
}

function updateProgress() {
  document.querySelectorAll("#wizard-progress li").forEach((li, i) => {
    li.classList.toggle("completed", i < currentStep);
    li.classList.toggle("active", i === currentStep);
  });
}

// ── Form state (read via FormData — no manual state object) ──────

function readConfig() {
  const data = new FormData(document.getElementById("wizard"));
  return {
    variationType: data.get("variation_type"),
    assembly: data.get("assembly"),
    effectSize: data.get("effect_size"),
    pValueType: data.get("p_value_type"),
    allowZeroPvalues: data.get("zero_pvalues") === "yes",
  };
}

// ── Conditional UI logic ─────────────────────────────────────────

function handleVariationChange() {
  const value = document.querySelector(
    'input[name="variation_type"]:checked'
  )?.value;
  const nextBtn = document.getElementById("next-variation");

  // Reset warnings and conditional groups
  document.getElementById("warn-snp").hidden = true;
  document.getElementById("warn-other").hidden = true;
  document.getElementById("assembly-group").hidden = true;

  if (value === "SNP") {
    document.getElementById("warn-snp").hidden = false;
    nextBtn.disabled = true;
    return;
  }
  if (value === "other") {
    document.getElementById("warn-other").hidden = false;
    nextBtn.disabled = true;
    return;
  }
  if (value === "CNV") {
    document.getElementById("assembly-group").hidden = false;
    nextBtn.disabled = !document.getElementById("assembly").value;
    return;
  }
  nextBtn.disabled = false;
}

function handleAssemblyChange() {
  const variation = document.querySelector(
    'input[name="variation_type"]:checked'
  )?.value;
  if (variation === "CNV") {
    document.getElementById("next-variation").disabled =
      !document.getElementById("assembly").value;
  }
}

function handleEffectSizeChange() {
  const value = document.querySelector(
    'input[name="effect_size"]:checked'
  )?.value;
  document.getElementById("warn-no-effect-size").hidden = value !== "none";
  document.getElementById("next-effect").disabled = false;
}

function handlePValueChange() {
  document.getElementById("next-pvalue").disabled = false;
}

function handleZeroPvaluesChange() {
  const value = document.querySelector(
    'input[name="zero_pvalues"]:checked'
  )?.value;
  document.getElementById("warn-thresholded").hidden = value !== "yes";
  document.getElementById("next-significance").disabled = false;
}

// ── File handling ────────────────────────────────────────────────

function handleFileChange(input) {
  const file = input.files[0];
  if (!file) return;

  document.getElementById("file-name").textContent = file.name;
  document.getElementById("file-size").textContent = formatFileSize(file.size);
  document.getElementById("file-info").hidden = false;
  document.getElementById("next-file").disabled = false;
}

/**
 * Upload a file to the Emscripten virtual file system via a Web Worker.
 *
 * Reads the file into an ArrayBuffer on the main thread, then transfers
 * ownership to the worker (zero-copy via Transferable).  The worker
 * writes the bytes to the VFS in one FS.writeFile() call — off the
 * main thread, so the UI never freezes.
 */
async function uploadFileToVFS() {
  const file = document.getElementById("file-input").files[0];
  if (!file) throw new Error("No file selected");

  const buffer = await file.arrayBuffer();
  await callWorker("upload", { data: buffer }, [buffer]);
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

// ── Validation summary (definition list population) ──────────────

function populateSummary() {
  const config = readConfig();

  const variationLabels = { CNV: "Copy number variant (CNV)", GENE: "Genes" };
  const effectLabels = {
    beta: "Beta",
    odds_ratio: "Odds ratio",
    z_score: "Z-score",
    none: "Not measured",
  };
  const pLabels = { p_value: "p value", neg_log10: "negative log₁₀ p value" };

  document.getElementById("summary-variation").textContent =
    variationLabels[config.variationType] || "—";
  document.getElementById("summary-effect").textContent =
    effectLabels[config.effectSize] || "—";
  document.getElementById("summary-pvalue").textContent =
    pLabels[config.pValueType] || "—";
  document.getElementById("summary-zero").textContent =
    config.allowZeroPvalues ? "Yes" : "No";

  const assemblyRow = document.getElementById("summary-assembly-row");
  if (config.variationType === "CNV") {
    assemblyRow.hidden = false;
    document.getElementById("summary-assembly").textContent =
      config.assembly || "—";
  } else {
    assemblyRow.hidden = true;
  }

  document.getElementById("summary-file").textContent =
    document.getElementById("file-input").files[0]?.name || "—";
}

// ── Validation bridge (calls Python via PyScript) ────────────────

async function validateFile() {
  const btn = document.getElementById("btn-validate");
  btn.disabled = true;
  btn.textContent = "Validating...";

  try {
    if (!workerReady) {
      throw new Error(
        "Python environment not ready. Please wait for it to finish loading."
      );
    }

    showLoading("Uploading file...");
    await uploadFileToVFS();

    showLoading(LOADING_MESSAGE);
    const config = readConfig();
    const configJson = JSON.stringify(config);

    const resultJson = await callWorker("validate", { configJson });
    const result = JSON.parse(resultJson);
    displayResults(result);
  } catch (err) {
    console.error("Validation error:", err);
    displayResults({
      errorCount: 1,
      errors: [{ row: 0, message: err.message || String(err) }],
      validRowCount: 0,
      hasOutput: false,
    });
  } finally {
    hideLoading();
    btn.disabled = false;
    btn.textContent = "Validate";
  }
}

function displayResults(result) {
  const output = document.getElementById("validation-output");
  output.hidden = false;

  const heading = document.getElementById("result-heading");
  const summary = document.getElementById("result-summary");

  // Build performance summary suffix
  const perfParts = [];
  if (result.elapsedSeconds != null) {
    const s = result.elapsedSeconds;
    const m = Math.floor(s / 60);
    const rs = Math.round(s % 60);
    perfParts.push(m > 0 ? `${m}m ${rs}s` : `${rs}s`);
  }
  if (result.rowsPerSecond != null) {
    perfParts.push(`${result.rowsPerSecond.toLocaleString()} rows/sec`);
  }
  const perfSuffix = perfParts.length > 0 ? ` (${perfParts.join(", ")})` : "";

  if (result.errorCount === 0) {
    heading.textContent = "✅ Validation passed";
    heading.className = "result-success";
    summary.textContent = `All ${result.validRowCount.toLocaleString()} rows are valid.${perfSuffix}`;
  } else {
    heading.textContent = `⚠️ ${result.errorCount} validation error(s)`;
    heading.className = "result-error";
    summary.textContent =
      result.validRowCount > 0
        ? `${result.validRowCount.toLocaleString()} valid rows.${perfSuffix} Review the errors below.`
        : `No valid rows found.${perfSuffix} Review the errors below.`;
  }

  // Build error list
  const list = document.getElementById("error-list");
  list.innerHTML = "";
  for (const err of result.errors) {
    const div = document.createElement("div");
    div.className = "validation-error-row";
    if (err.row > 0) {
      const span = document.createElement("span");
      span.className = "row-num";
      span.textContent = `Row ${err.row}: `;
      div.appendChild(span);
      div.appendChild(document.createTextNode(err.message));
    } else {
      div.textContent = err.message;
    }
    list.appendChild(div);
  }

  // Checksum
  const checksumPanel = document.getElementById("checksum-panel");
  if (result.md5Checksum) {
    document.getElementById("checksum-value").textContent = result.md5Checksum;
    checksumPanel.hidden = false;
  } else {
    checksumPanel.hidden = true;
  }

  // Download button
  hasValidatedOutput = result.hasOutput;
  document.getElementById("btn-download").hidden = !result.hasOutput;
}

// ── Download (via Web Worker) ────────────────────────────────────

async function downloadOutput() {
  if (!hasValidatedOutput) return;

  showLoading("Preparing download…");

  try {
    const buffer = await callWorker("download");

    const rawName =
      document.getElementById("file-input").files[0]?.name || "output.tsv";
    const baseName = rawName.replace(/\.gz$/, "");
    const fileName = "validated_" + baseName + ".gz";

    const blob = new Blob([new Uint8Array(buffer)], { type: "application/gzip" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    await callWorker("cleanup");
    hasValidatedOutput = false;
  } catch (err) {
    console.error("Download failed:", err);
    displayResults({
      errorCount: 1,
      errors: [
        { row: 0, message: "Download failed: " + (err.message || String(err)) },
      ],
      validRowCount: 0,
      hasOutput: false,
    });
  } finally {
    hideLoading();
  }
}

// ── Loading dialog ───────────────────────────────────────────────

function showLoading(message) {
  const dialog = document.getElementById("loading-dialog");
  document.getElementById("loading-message").textContent = message;
  document.getElementById("loading-progress").hidden = true;
  if (!dialog.open) dialog.showModal();
}

function hideLoading() {
  document.getElementById("loading-dialog").close();
}

/** Update the loading dialog with live validation progress. */
function handleValidationProgress(msg) {
  document.getElementById("loading-message").textContent = LOADING_MESSAGE;
  const el = document.getElementById("loading-progress");
  el.hidden = false;

  const rows = msg.rowsProcessed.toLocaleString();
  const rate = msg.rowsPerSecond.toLocaleString();
  const secs = msg.elapsedSeconds;
  const mins = Math.floor(secs / 60);
  const remSecs = Math.round(secs % 60);
  const timeStr =
    mins > 0 ? `${mins}m ${String(remSecs).padStart(2, "0")}s` : `${remSecs}s`;

  document.getElementById("progress-rows").textContent = rows;
  document.getElementById("progress-rate").textContent = rate;
  document.getElementById("progress-time").textContent = timeStr;
  document.getElementById("progress-errors").textContent =
    msg.errorCount.toLocaleString();
}

// ── Example file downloads ──────────────────────────────────────

const EXAMPLE_HINTS = {
  "static/examples/valid-gene.csv":
    "This file passes validation. In the wizard, choose: Variation type -> Genes.",
  "static/examples/invalid-gene.csv":
    "This file contains deliberate errors. In the wizard, choose: Variation type -> Genes.",
  "static/examples/valid-cnv.csv":
    "This file passes validation. In the wizard, choose: Variation type -> CNV, Assembly -> GRCh38.",
  "static/examples/invalid-cnv.csv":
    "This file contains deliberate errors. In the wizard, choose: Variation type -> CNV, Assembly -> GRCh38.",
};

function handleExampleSelectChange() {
  const select = document.getElementById("example-select");
  const btn = document.getElementById("btn-download-example");
  const hint = document.getElementById("example-hint");
  const value = select.value;

  btn.disabled = !value;

  if (value && EXAMPLE_HINTS[value]) {
    hint.textContent = EXAMPLE_HINTS[value];
    hint.hidden = false;
  } else {
    hint.hidden = true;
    hint.textContent = "";
  }
}

function downloadExample() {
  const url = document.getElementById("example-select").value;
  if (!url) return;
  const a = document.createElement("a");
  a.href = url;
  a.download = url.split("/").pop();
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// ── Initialisation ───────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  // Radio change listeners
  document.querySelectorAll('input[name="variation_type"]').forEach((r) =>
    r.addEventListener("change", handleVariationChange)
  );
  document
    .getElementById("assembly")
    .addEventListener("change", handleAssemblyChange);
  document.querySelectorAll('input[name="effect_size"]').forEach((r) =>
    r.addEventListener("change", handleEffectSizeChange)
  );
  document.querySelectorAll('input[name="p_value_type"]').forEach((r) =>
    r.addEventListener("change", handlePValueChange)
  );
  document.querySelectorAll('input[name="zero_pvalues"]').forEach((r) =>
    r.addEventListener("change", handleZeroPvaluesChange)
  );

  // Example file panel
  document
    .getElementById("example-select")
    .addEventListener("change", handleExampleSelectChange);
  document
    .getElementById("btn-download-example")
    .addEventListener("click", downloadExample);

  // File input
  document
    .getElementById("file-input")
    .addEventListener("change", (e) => handleFileChange(e.target));

  // Navigation buttons (data-action="next" / data-action="prev")
  document.querySelectorAll('[data-action="next"]').forEach((btn) =>
    btn.addEventListener("click", next)
  );
  document.querySelectorAll('[data-action="prev"]').forEach((btn) =>
    btn.addEventListener("click", prev)
  );

  // Action buttons
  document
    .getElementById("btn-validate")
    .addEventListener("click", validateFile);
  document
    .getElementById("btn-download")
    .addEventListener("click", downloadOutput);
  document.getElementById("btn-reset").addEventListener("click", async () => {
    document.getElementById("wizard").reset();
    if (hasValidatedOutput) await callWorker("cleanup");
    hasValidatedOutput = false;
    document.getElementById("validation-output").hidden = true;
    document.getElementById("file-info").hidden = true;
    document.getElementById("assembly-group").hidden = true;
    document.querySelectorAll(".wizard-warning").forEach((w) => (w.hidden = true));
    document.querySelectorAll("[id^='next-']").forEach((b) => (b.disabled = true));
    goToStep(0);
  });

  // Start Web Worker (Pyodide loads off the main thread)
  worker = new Worker("validation-worker.js");
  showLoading("Loading Python environment...");
  worker.onmessage = ({ data: msg }) => {
    if (msg.type === "ready") {
      workerReady = true;
      hideLoading();
      return;
    }
    if (msg.type === "progress") {
      handleValidationProgress(msg);
      return;
    }
    const p = _pending.get(msg.id);
    if (!p) return;
    _pending.delete(msg.id);
    if (msg.type === "done") p.resolve(msg.result);
    if (msg.type === "error") p.reject(new Error(msg.error));
  };

  // Show initial step
  goToStep(0);
});
