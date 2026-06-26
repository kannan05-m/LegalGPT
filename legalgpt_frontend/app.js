/* ── STATE ── */
const state = {
  documentId: null,
  documentText: "",
  analysis: null,
};

/* ── DOM REFS ── */
const $ = (sel) => document.querySelector(sel);

const statusText     = $("#statusText");
const fileInput      = $("#documentInput");
const dropzone       = $("#dropzone");
const sampleButton   = $("#sampleButton");
const exportButton   = $("#exportButton");
const rerunButton    = $("#rerunButton");
const questionInput  = $("#questionInput");
const askButton      = $("#askButton");
const documentSearch = $("#documentSearch");

/* ── HELPERS ── */
function setStatus(msg) {
  statusText.textContent = msg;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showError(err) {
  setStatus(err.message || "Something went wrong.");
}

/* ── RENDER ── */
function renderAnalysis(data, filename, chunkCount, text) {
  state.documentId   = data.document_id || state.documentId;
  state.analysis     = data.analysis || data;
  state.documentText = text || state.documentText;

  // Sidebar meta
  const fileNameEl = $("#fileName");
  fileNameEl.textContent = filename || "Loaded document";

  const fileCheck = $("#fileCheck");
  fileCheck.classList.remove("hidden");

  $("#docType").textContent    = state.analysis.document_type || "—";
  $("#chunkCount").textContent = chunkCount || "—";

  // Summary
  $("#summaryText").textContent = state.analysis.summary || "No summary returned.";

  // Document text (with section coloring)
  renderDocumentText(state.documentText || data.text_preview || "");

  // Clauses & risks
  renderClauses(state.analysis.key_clauses || {});
  renderRisks(state.analysis.risks || []);

  // Enable controls
  exportButton.disabled   = !state.documentId;
  rerunButton.disabled    = !state.documentId;
  questionInput.disabled  = !state.documentId;
  askButton.disabled      = !state.documentId;
}

function renderDocumentText(text) {
  const el = $("#documentText");

  if (!text) {
    el.textContent = "Upload a document to inspect its text here.";
    return;
  }

  // Colorize numbered section headings like "1. Purpose"
  const escaped = escapeHtml(text);
  const highlighted = escaped.replace(
    /^(\d+\.\s+[A-Z][^\n]{0,60})$/gm,
    '<span class="doc-section-label">$1</span>'
  );
  el.innerHTML = highlighted;
}

function renderClauses(clauses) {
  const entries = Object.entries(clauses);
  const container = $("#clauses");

  if (!entries.length) {
    container.innerHTML = '<p class="empty-hint">No clauses extracted yet.</p>';
    return;
  }

  container.innerHTML = entries.map(([name, text]) => `
    <article class="clause">
      <div class="clause-title">${escapeHtml(name.replaceAll("_", " "))}</div>
      <p>${escapeHtml(text)}</p>
    </article>
  `).join("");
}

function renderRisks(risks) {
  const container = $("#risks");

  if (!risks.length) {
    container.innerHTML = '<p class="empty-hint">No obvious risk flags were found.</p>';
    return;
  }

  container.innerHTML = risks.map((risk) => {
    const cls = risk.level.toLowerCase().includes("high")
      ? "high"
      : risk.level.toLowerCase().includes("low")
      ? "low"
      : "";

    return `
      <article class="risk ${cls}">
        <div class="risk-header">
          <strong>${escapeHtml(risk.title)}</strong>
          <span class="risk-pill">${escapeHtml(risk.level)}</span>
        </div>
        <p>${escapeHtml(risk.reason)}</p>
        <p><b>Watch out:</b> ${escapeHtml(risk.watch_out)}</p>
      </article>
    `;
  }).join("");
}

function appendMessage(role, text) {
  // Remove placeholder if present
  const placeholder = $("#chatLog .assistant-placeholder");
  if (placeholder) placeholder.remove();

  const node = document.createElement("div");
  node.className = `message ${role}`;
  node.textContent = text;
  $("#chatLog").appendChild(node);
  $("#chatLog").scrollTop = $("#chatLog").scrollHeight;
}

/* ── UPLOAD ── */
async function uploadFile(file) {
  if (!file) return;
  setStatus(`Uploading ${file.name}…`);

  const body = new FormData();
  body.append("file", file);

  const response = await fetch("/api/upload", { method: "POST", body });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Upload failed." }));
    throw new Error(err.detail || "Upload failed.");
  }

  const data = await response.json();

  // Fetch full document text
  const docResponse = await fetch(`/api/documents/${data.document_id}`);
  const doc = await docResponse.json();

  renderAnalysis(data, data.filename, data.chunk_count, doc.text);
  setStatus("Analysis complete. Ask a question or export a report.");
}

/* ── FILE INPUT EVENTS ── */
fileInput.addEventListener("change", () => {
  uploadFile(fileInput.files[0]).catch(showError);
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  uploadFile(e.dataTransfer.files[0]).catch(showError);
});

/* ── SAMPLE CONTRACT ── */
sampleButton.addEventListener("click", () => {
  const sample = `NON-DISCLOSURE AGREEMENT (SAMPLE)
Effective Date: June 26, 2026

Disclosing Party
NovaTech Solutions Pvt. Ltd.
245 Innovation Park, Sector 18
Noida, Uttar Pradesh 201301
India

Receiving Party
Arjun Mehta
Flat 12B, Sunrise Residency
Dwarka Sector 10
New Delhi, Delhi 110075
India

1. Purpose
The parties wish to discuss and evaluate a potential collaboration involving software development, artificial intelligence solutions, and related business opportunities. During these discussions, confidential information may be shared.

2. Confidential Information
Confidential information includes, but is not limited to, technical data, business plans, customer information, financial projections, research, algorithms, AI models, and internal documentation.

3. Obligations of Receiving Party
The Receiving Party agrees to maintain confidentiality, use information only for evaluation purposes, avoid unauthorized disclosure, and apply reasonable security measures.

4. Exclusions
Information that is public, previously known, independently developed, or lawfully obtained from third parties is excluded.

5. Term
This Agreement remains effective for two years from the Effective Date. Confidentiality obligations survive for three years after termination.

6. Governing Law
This Agreement shall be governed by the laws of India, with disputes subject to the courts of New Delhi.`;

  const file = new File([sample], "sample-nda.txt", { type: "text/plain" });
  uploadFile(file).catch(showError);
});

/* ── RERUN ── */
rerunButton.addEventListener("click", async () => {
  if (!state.documentId) return;
  setStatus("Re-running analysis…");
  const response = await fetch(`/api/analysis/${state.documentId}`, { method: "POST" });
  if (!response.ok) return showError(new Error("Analysis failed."));
  const analysis = await response.json();
  renderAnalysis(
    analysis,
    $("#fileName").textContent,
    $("#chunkCount").textContent,
    state.documentText
  );
  setStatus("Analysis refreshed.");
});

/* ── EXPORT ── */
exportButton.addEventListener("click", () => {
  if (state.documentId) window.location.href = `/api/export/${state.documentId}`;
});

/* ── CHAT ── */
$("#askButton").addEventListener("click", async () => {
  const question = questionInput.value.trim();
  if (!question || !state.documentId) return;

  appendMessage("user", question);
  questionInput.value = "";
  setStatus("Answering…");

  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: state.documentId, question }),
  });

  if (!response.ok) return showError(new Error("Chat failed."));
  const data = await response.json();
  appendMessage("assistant", data.answer);
  setStatus("Answer ready.");
});

// Allow Enter key in chat input
questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    askButton.click();
  }
});

/* ── DOCUMENT SEARCH ── */
documentSearch.addEventListener("input", () => {
  const query = documentSearch.value.trim();

  if (!query) {
    renderDocumentText(state.documentText);
    return;
  }

  // Re-render with search highlights on top of section coloring
  const escaped = escapeHtml(state.documentText || "");
  const sectionColored = escaped.replace(
    /^(\d+\.\s+[A-Z][^\n]{0,60})$/gm,
    '<span class="doc-section-label">$1</span>'
  );
  const pattern = new RegExp(
    query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
    "gi"
  );
  $("#documentText").innerHTML = sectionColored.replace(
    pattern,
    (match) => `<mark>${match}</mark>`
  );
});

/* ── COMPARE ── */
$("#compareButton").addEventListener("click", async () => {
  const a = $("#compareA").files[0];
  const b = $("#compareB").files[0];
  if (!a || !b) return showError(new Error("Choose two files to compare."));

  setStatus("Comparing documents…");
  const body = new FormData();
  body.append("file_a", a);
  body.append("file_b", b);

  const response = await fetch("/api/compare", { method: "POST", body });
  if (!response.ok) return showError(new Error("Compare failed."));

  const data = await response.json();
  const result = [
    data.modified_summary,
    "",
    "Added:",
    ...(data.added.length ? data.added.map((i) => `- ${i}`) : ["- None detected"]),
    "",
    "Removed:",
    ...(data.removed.length ? data.removed.map((i) => `- ${i}`) : ["- None detected"]),
  ].join("\n");

  const el = $("#compareResult");
  el.textContent = result;
  el.classList.remove("hidden");
  setStatus("Comparison complete.");
});

/* ── TEMPLATE ── */
$("#templateForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  setStatus("Generating template…");

  const form = new FormData(e.currentTarget);
  const payload = Object.fromEntries(form.entries());

  const response = await fetch("/api/template", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) return showError(new Error("Template generation failed."));

  const data = await response.json();
  const el = $("#templateResult");
  el.textContent = data.content;
  el.classList.remove("hidden");
  setStatus("Template generated.");
});