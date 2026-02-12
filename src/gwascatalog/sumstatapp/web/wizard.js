/**
 * wizard.js — Minimal wizard navigation and File System Access API bridge.
 *
 * This is the only JavaScript in the application. All validation logic lives
 * in Python (validate.py) running via PyScript/Pyodide.
 *
 * Responsibilities:
 *   1. Wizard step navigation (show/hide sections, update progress bar)
 *   2. Form input change handlers (enable/disable Next buttons, show warnings)
 *   3. File System Access API for reading input files and writing output
 */

"use strict";

// ── Wizard state ─────────────────────────────────────────────────
const STEPS = [
  "welcome",
  "genetic_variation",
  "effect_size",
  "p_value",
  "highly_significant",
  "file_picker",
  "validate",
];

let currentStep = 0;

// Collected wizard answers (read by Python via globalThis)
const wizardState = {
  variationType: null,   // "CNV" | "GENE"
  assembly: null,         // "GRCh38" | ... (CNV only)
  effectSize: null,       // "beta" | "odds_ratio" | "z_score" | "none"
  pValueType: null,       // "p_value" | "neg_log10"
  allowZeroPvalues: false,
  fileHandle: null,       // FileSystemFileHandle (modern API)
  fileObject: null,       // File object (fallback)
  fileName: null,
  outputDirHandle: null,  // FileSystemDirectoryHandle (modern API)
};
globalThis.wizardState = wizardState;

// ── Feature detection ────────────────────────────────────────────
const hasFileSystemAccess = ("showOpenFilePicker" in window);

document.addEventListener("DOMContentLoaded", () => {
  if (!hasFileSystemAccess) {
    document.getElementById("file-picker-modern").style.display = "none";
    document.getElementById("file-picker-fallback").style.display = "block";
  } else {
    document.getElementById("btn-pick-output").style.display = "inline-block";
  }

  // Attach radio change listeners
  attachRadioListeners("variation_type", handleVariationChange);
  attachRadioListeners("effect_size", handleEffectSizeChange);
  attachRadioListeners("p_value_type", handlePValueChange);
  attachRadioListeners("zero_pvalues", handleZeroPvaluesChange);

  // Assembly select listener
  document.getElementById("assembly").addEventListener("change", handleAssemblyChange);
});

// ── Navigation ───────────────────────────────────────────────────
function wizardNext() {
  if (currentStep < STEPS.length - 1) {
    goToStep(currentStep + 1);
  }
}

function wizardPrev() {
  if (currentStep > 0) {
    goToStep(currentStep - 1);
  }
}

function wizardReset() {
  // Reset state
  wizardState.variationType = null;
  wizardState.assembly = null;
  wizardState.effectSize = null;
  wizardState.pValueType = null;
  wizardState.allowZeroPvalues = false;
  wizardState.fileHandle = null;
  wizardState.fileObject = null;
  wizardState.fileName = null;
  wizardState.outputDirHandle = null;

  // Reset all radio buttons
  document.querySelectorAll('input[type="radio"]').forEach(r => r.checked = false);
  document.getElementById("assembly").value = "";

  // Reset warnings
  document.querySelectorAll(".wizard-warning").forEach(w => w.classList.remove("visible"));
  document.getElementById("assembly-group").classList.remove("visible");

  // Reset file info
  document.getElementById("file-info").classList.remove("visible");
  document.getElementById("output-dir-info").classList.remove("visible");

  // Reset validation output
  document.getElementById("validation-output").style.display = "none";
  document.getElementById("validation-summary").style.display = "none";

  // Disable all Next buttons
  document.querySelectorAll("[id^='next-']").forEach(b => b.disabled = true);

  goToStep(0);
}

function goToStep(stepIndex) {
  // Hide current step
  const currentEl = document.getElementById(`step-${STEPS[currentStep]}`);
  if (currentEl) currentEl.classList.remove("active");

  // Show new step
  currentStep = stepIndex;
  const newEl = document.getElementById(`step-${STEPS[currentStep]}`);
  if (newEl) newEl.classList.add("active");

  // Update progress bar
  updateProgress();

  // If we're on the validate step, populate the summary
  if (STEPS[currentStep] === "validate") {
    populateValidationSummary();
  }

  // Scroll to top
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateProgress() {
  const items = document.querySelectorAll(".wizard-progress li");
  items.forEach((li, idx) => {
    li.classList.remove("active", "completed");
    if (idx < currentStep) li.classList.add("completed");
    if (idx === currentStep) li.classList.add("active");
  });
}

// ── Radio change handlers ────────────────────────────────────────
function attachRadioListeners(name, handler) {
  document.querySelectorAll(`input[name="${name}"]`).forEach(radio => {
    radio.addEventListener("change", handler);
  });
}

function handleVariationChange(e) {
  const val = e.target.value;

  // Hide all warnings first
  document.getElementById("warn-snp").classList.remove("visible");
  document.getElementById("warn-other").classList.remove("visible");
  document.getElementById("assembly-group").classList.remove("visible");

  const nextBtn = document.getElementById("next-variation");

  if (val === "SNP") {
    document.getElementById("warn-snp").classList.add("visible");
    nextBtn.disabled = true;
    wizardState.variationType = null;
    return;
  }

  if (val === "other") {
    document.getElementById("warn-other").classList.add("visible");
    nextBtn.disabled = true;
    wizardState.variationType = null;
    return;
  }

  wizardState.variationType = val;

  // Show assembly selector for CNV
  if (val === "CNV") {
    document.getElementById("assembly-group").classList.add("visible");
    // If assembly already selected, enable next
    nextBtn.disabled = !wizardState.assembly;
  } else {
    wizardState.assembly = null;
    nextBtn.disabled = false;
  }
}

function handleAssemblyChange(e) {
  wizardState.assembly = e.target.value || null;
  const nextBtn = document.getElementById("next-variation");
  // CNV requires assembly
  if (wizardState.variationType === "CNV") {
    nextBtn.disabled = !wizardState.assembly;
  }
}

function handleEffectSizeChange(e) {
  const val = e.target.value;
  wizardState.effectSize = val;

  const warnEl = document.getElementById("warn-no-effect-size");
  warnEl.classList.toggle("visible", val === "none");

  // Allow progressing even with "none" (gene-based GWAS allows it)
  document.getElementById("next-effect").disabled = false;
}

function handlePValueChange(e) {
  wizardState.pValueType = e.target.value;
  document.getElementById("next-pvalue").disabled = false;
}

function handleZeroPvaluesChange(e) {
  const val = e.target.value;
  wizardState.allowZeroPvalues = (val === "yes");

  const warnEl = document.getElementById("warn-thresholded");
  warnEl.classList.toggle("visible", val === "yes");

  document.getElementById("next-significant").disabled = false;
}

// ── File System Access API ───────────────────────────────────────
async function pickFile() {
  try {
    const [handle] = await window.showOpenFilePicker({
      types: [
        {
          description: "Summary statistics files",
          accept: {
            "text/tab-separated-values": [".tsv"],
            "text/csv": [".csv"],
            "text/plain": [".txt"],
            "application/gzip": [".gz"],
          },
        },
      ],
      multiple: false,
    });

    wizardState.fileHandle = handle;
    wizardState.fileName = handle.name;

    const file = await handle.getFile();
    wizardState.fileObject = file;

    showFileInfo(handle.name, file.size);
    document.getElementById("next-file").disabled = false;
  } catch (err) {
    // User cancelled the picker
    if (err.name !== "AbortError") {
      console.error("File picker error:", err);
    }
  }
}

async function pickOutputDir() {
  try {
    const dirHandle = await window.showDirectoryPicker({ mode: "readwrite" });
    wizardState.outputDirHandle = dirHandle;

    document.getElementById("output-dir-info").classList.add("visible");
    document.getElementById("output-dir-name").textContent = dirHandle.name;
  } catch (err) {
    if (err.name !== "AbortError") {
      console.error("Directory picker error:", err);
    }
  }
}

function handleFallbackFile(input) {
  const file = input.files[0];
  if (!file) return;

  wizardState.fileObject = file;
  wizardState.fileName = file.name;

  showFileInfo(file.name, file.size);
  document.getElementById("next-file").disabled = false;
}

function showFileInfo(name, sizeBytes) {
  document.getElementById("file-info").classList.add("visible");
  document.getElementById("file-name").textContent = name;

  const sizeMB = (sizeBytes / (1024 * 1024)).toFixed(2);
  document.getElementById("file-size").textContent =
    sizeBytes < 1024 * 1024
      ? `${(sizeBytes / 1024).toFixed(1)} KB`
      : `${sizeMB} MB`;
}

// ── Validation summary ──────────────────────────────────────────
function populateValidationSummary() {
  const labels = {
    CNV: "Copy number variant (CNV)",
    GENE: "Genes",
  };
  document.getElementById("summary-variation").textContent =
    labels[wizardState.variationType] || wizardState.variationType || "—";

  const effectLabels = {
    beta: "Beta",
    odds_ratio: "Odds ratio",
    z_score: "Z-score",
    none: "Not measured",
  };
  document.getElementById("summary-effect").textContent =
    effectLabels[wizardState.effectSize] || "—";

  const pLabels = {
    p_value: "p value",
    neg_log10: "negative log₁₀ p value",
  };
  document.getElementById("summary-pvalue").textContent =
    pLabels[wizardState.pValueType] || "—";

  document.getElementById("summary-zero").textContent =
    wizardState.allowZeroPvalues ? "Yes" : "No";

  if (wizardState.variationType === "CNV") {
    document.getElementById("summary-assembly-row").style.display = "";
    document.getElementById("summary-assembly").textContent =
      wizardState.assembly || "—";
  } else {
    document.getElementById("summary-assembly-row").style.display = "none";
  }

  document.getElementById("summary-file").textContent =
    wizardState.fileName || "—";
}

// ── Bridge to Python validation ─────────────────────────────────
// Called by the HTML button; delegates to Python via PyScript.
async function runValidation() {
  const btn = document.getElementById("btn-validate");
  btn.disabled = true;
  btn.textContent = "⏳ Validating…";

  // Show loading overlay
  showLoading("Validating summary statistics…");

  try {
    // Read file content
    let fileText;
    if (wizardState.fileHandle) {
      const file = await wizardState.fileHandle.getFile();
      if (file.name.endsWith(".gz")) {
        const buffer = await file.arrayBuffer();
        const ds = new DecompressionStream("gzip");
        const readable = new Blob([buffer]).stream().pipeThrough(ds);
        fileText = await new Response(readable).text();
      } else {
        fileText = await file.text();
      }
    } else if (wizardState.fileObject) {
      if (wizardState.fileObject.name.endsWith(".gz")) {
        const buffer = await wizardState.fileObject.arrayBuffer();
        const ds = new DecompressionStream("gzip");
        const readable = new Blob([buffer]).stream().pipeThrough(ds);
        fileText = await new Response(readable).text();
      } else {
        fileText = await wizardState.fileObject.text();
      }
    }

    // Store on globalThis for Python to read
    globalThis._fileContent = fileText;

    // Call Python validation via PyScript
    // The Python function `validate_file` is exposed on globalThis
    const pyValidate = globalThis.validate_file;
    if (pyValidate) {
      await pyValidate();
    } else {
      throw new Error(
        "Python environment not ready. Please wait for it to finish loading."
      );
    }
  } catch (err) {
    console.error("Validation error:", err);
    displayValidationError(err.message || String(err));
  } finally {
    hideLoading();
    btn.disabled = false;
    btn.textContent = "🔬 Validate";
  }
}

// ── Save results ────────────────────────────────────────────────
async function saveResults() {
  const validatedContent = globalThis._validatedContent;
  if (!validatedContent) {
    alert("No validated content to save.");
    return;
  }

  if (wizardState.outputDirHandle) {
    // Use File System Access API to write to chosen directory
    try {
      const outName = "validated_" + (wizardState.fileName || "output.tsv");
      const fileHandle = await wizardState.outputDirHandle.getFileHandle(
        outName, { create: true }
      );
      const writable = await fileHandle.createWritable();
      await writable.write(validatedContent);
      await writable.close();
      alert(`File saved as ${outName} in ${wizardState.outputDirHandle.name}/`);
    } catch (err) {
      console.error("Save error:", err);
      alert("Failed to save file: " + err.message);
    }
  } else {
    // Fallback: trigger a download
    const blob = new Blob([validatedContent], { type: "text/tab-separated-values" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "validated_" + (wizardState.fileName || "output.tsv");
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

// ── UI helpers (called from Python and JS) ──────────────────────
function showLoading(message) {
  document.getElementById("loading-message").textContent = message;
  document.getElementById("loading-overlay").classList.add("visible");
}

function hideLoading() {
  document.getElementById("loading-overlay").classList.remove("visible");
}

function displayValidationError(message) {
  const output = document.getElementById("validation-output");
  output.style.display = "block";

  const heading = document.getElementById("validation-summary-heading");
  const text = document.getElementById("validation-summary-text");
  const summary = document.getElementById("validation-summary");

  heading.textContent = "❌ Validation failed";
  heading.style.color = "#c00";
  text.textContent = message;
  summary.style.display = "block";
}

// Exposed for Python to call
globalThis.showLoading = showLoading;
globalThis.hideLoading = hideLoading;
globalThis.displayValidationError = displayValidationError;

globalThis.displayValidationResults = function(errorCount, errorHtml, hasValidRows) {
  const output = document.getElementById("validation-output");
  output.style.display = "block";

  const summary = document.getElementById("validation-summary");
  const heading = document.getElementById("validation-summary-heading");
  const text = document.getElementById("validation-summary-text");
  summary.style.display = "block";

  if (errorCount === 0) {
    heading.textContent = "✅ Validation passed";
    heading.style.color = "#18974c";
    text.textContent = "All rows are valid.";
  } else {
    heading.textContent = `⚠️ ${errorCount} validation error(s)`;
    heading.style.color = "#c00";
    text.textContent = "Review the errors below. Valid rows can still be saved.";
  }

  document.getElementById("error-count").textContent =
    `${errorCount} error(s) found`;
  document.getElementById("error-list").innerHTML = errorHtml;

  if (hasValidRows) {
    document.getElementById("btn-save").style.display = "inline-block";
  }
};
