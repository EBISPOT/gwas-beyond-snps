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
 *   3. File reading and optional gzip decompression
 *   4. Bridge to Python validate_file(file_text, config_json)
 *   5. Display structured validation results returned by Python
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

let currentStep = 0;
let validatedOutput = null; // TSV content for download

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

// ── File handling (standard file input — not File System Access) ──

function handleFileChange(input) {
  const file = input.files[0];
  if (!file) return;

  document.getElementById("file-name").textContent = file.name;
  document.getElementById("file-size").textContent = formatFileSize(file.size);
  document.getElementById("file-info").hidden = false;
  document.getElementById("next-file").disabled = false;
}

async function readUploadedFile() {
  const file = document.getElementById("file-input").files[0];
  if (!file) throw new Error("No file selected");

  if (file.name.endsWith(".gz")) {
    const buffer = await file.arrayBuffer();
    const stream = new Blob([buffer])
      .stream()
      .pipeThrough(new DecompressionStream("gzip"));
    return new Response(stream).text();
  }
  return file.text();
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
  btn.textContent = "Validating…";
  showLoading("Validating summary statistics…");

  try {
    const config = readConfig();
    const fileText = await readUploadedFile();
    const configJson = JSON.stringify(config);

    const pyValidate = globalThis.validate_file;
    if (!pyValidate) {
      throw new Error(
        "Python environment not ready. Please wait for it to finish loading."
      );
    }

    const resultJson = await pyValidate(fileText, configJson);
    const result = JSON.parse(resultJson);
    displayResults(result);
  } catch (err) {
    console.error("Validation error:", err);
    displayResults({
      errorCount: 1,
      errors: [{ row: 0, message: err.message || String(err) }],
      validRowCount: 0,
      output: null,
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

  if (result.errorCount === 0) {
    heading.textContent = "✅ Validation passed";
    heading.className = "result-success";
    summary.textContent = `All ${result.validRowCount} rows are valid.`;
  } else {
    heading.textContent = `⚠️ ${result.errorCount} validation error(s)`;
    heading.className = "result-error";
    summary.textContent =
      result.validRowCount > 0
        ? `${result.validRowCount} valid rows. Review the errors below.`
        : "No valid rows found. Review the errors below.";
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

  // Download button
  validatedOutput = result.output;
  document.getElementById("btn-download").hidden = !result.output;
}

// ── Download (standard file download — not File System Access) ───

function downloadOutput() {
  if (!validatedOutput) return;

  const fileName =
    "validated_" +
    (document.getElementById("file-input").files[0]?.name || "output.tsv");

  const blob = new Blob([validatedOutput], {
    type: "text/tab-separated-values",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── Loading dialog ───────────────────────────────────────────────

function showLoading(message) {
  const dialog = document.getElementById("loading-dialog");
  dialog.querySelector("p").textContent = message;
  dialog.showModal();
}

function hideLoading() {
  document.getElementById("loading-dialog").close();
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
  document.getElementById("btn-reset").addEventListener("click", () => {
    document.getElementById("wizard").reset();
    validatedOutput = null;
    document.getElementById("validation-output").hidden = true;
    document.getElementById("file-info").hidden = true;
    document.getElementById("assembly-group").hidden = true;
    document.querySelectorAll(".wizard-warning").forEach((w) => (w.hidden = true));
    document.querySelectorAll("[id^='next-']").forEach((b) => (b.disabled = true));
    goToStep(0);
  });

  // Show initial step
  goToStep(0);
});
