"use strict";

// Everything the page remembers while it is open.
const state = {
  documentId: null,
  busy: false,
  answerCount: 0,
  limits: { max_upload_mb: 10, max_pages: 100, max_question_chars: 500, document_ttl_minutes: 60 },
};

const GENERAL_QUESTIONS = [
  "What is this document about?",
  "What are the main points?",
  "Are any dates or deadlines mentioned?",
];

const SAMPLE_QUESTIONS = [
  "How many days of paid leave do employees get?",
  "Can I work from home, and how often?",
  "How do I claim travel expenses?",
  "Does the handbook mention a pension plan?",
];

const NOT_FOUND_ANSWER = "I don't know based on the provided document";

const els = {
  dropzone: document.getElementById("dropzone"),
  fileInput: document.getElementById("file-input"),
  limitsHint: document.getElementById("limits-hint"),
  sampleButton: document.getElementById("sample-button"),
  sampleLine: document.getElementById("sample-line"),
  uploadStatus: document.getElementById("upload-status"),
  docCard: document.getElementById("doc-card"),
  docName: document.getElementById("doc-name"),
  docMeta: document.getElementById("doc-meta"),
  replaceDoc: document.getElementById("replace-doc"),
  suggestions: document.getElementById("suggestions"),
  suggestionList: document.getElementById("suggestion-list"),
  conversation: document.getElementById("conversation"),
  emptyState: document.getElementById("empty-state"),
  form: document.getElementById("ask-form"),
  question: document.getElementById("question"),
  charCount: document.getElementById("char-count"),
  askButton: document.getElementById("ask-button"),
};

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ---------- Small helpers ---------- */

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function readJson(response) {
  try {
    return await response.json();
  } catch (error) {
    return null;
  }
}

// FastAPI sends errors as {"detail": "..."} or, for invalid input, a list.
function errorMessage(data, fallback) {
  if (data && typeof data.detail === "string") {
    return data.detail;
  }
  if (data && Array.isArray(data.detail) && data.detail.length > 0 && data.detail[0].msg) {
    return data.detail[0].msg;
  }
  return fallback;
}

function networkMessage(error, fallback) {
  if (error instanceof TypeError) {
    return "Couldn't reach the server. Check your connection and try again.";
  }
  return error.message || fallback;
}

function plural(count, word) {
  return count + " " + word + (count === 1 ? "" : "s");
}

/* ---------- Limits ---------- */

async function loadLimits() {
  try {
    const response = await fetch("/api/limits");
    if (!response.ok) {
      return;
    }
    const data = await response.json();
    state.limits = data;
    els.limitsHint.textContent =
      "Up to " + data.max_upload_mb + " MB and " + data.max_pages + " pages. Text-based PDFs only.";
    els.question.maxLength = data.max_question_chars;
  } catch (error) {
    // The defaults above still work if this fails.
  }
}

/* ---------- Uploading ---------- */

function setUploadStatus(message, isError) {
  els.uploadStatus.hidden = message === "";
  els.uploadStatus.textContent = message;
  els.uploadStatus.classList.toggle("is-error", Boolean(isError));
}

function setUploading(isUploading) {
  els.dropzone.classList.toggle("is-busy", isUploading);
  els.fileInput.disabled = isUploading;
  els.sampleButton.disabled = isUploading;
  els.replaceDoc.disabled = isUploading;
}

async function uploadFile(file, isSample) {
  if (!file) {
    return;
  }

  const looksLikePdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  if (!looksLikePdf) {
    setUploadStatus("Choose a PDF file. " + file.name + " isn't a PDF.", true);
    return;
  }

  const maxBytes = state.limits.max_upload_mb * 1024 * 1024;
  if (file.size > maxBytes) {
    setUploadStatus("This file is larger than " + state.limits.max_upload_mb + " MB.", true);
    return;
  }

  setUploading(true);
  setUploadStatus("Reading and indexing " + file.name + "…", false);

  const form = new FormData();
  form.append("file", file);

  try {
    const response = await fetch("/api/documents", { method: "POST", body: form });
    const data = await readJson(response);
    if (!response.ok) {
      throw new Error(errorMessage(data, "The upload didn't work. Try again."));
    }
    setUploadStatus("", false);
    showDocument(data, isSample);
  } catch (error) {
    setUploadStatus(networkMessage(error, "The upload didn't work. Try again."), true);
  } finally {
    setUploading(false);
    els.fileInput.value = "";
  }
}

async function uploadSample() {
  setUploadStatus("Loading the sample handbook…", false);
  try {
    const response = await fetch("/sample-handbook.pdf");
    if (!response.ok) {
      throw new Error("The sample file is missing from the server.");
    }
    const blob = await response.blob();
    const file = new File([blob], "sample-handbook.pdf", { type: "application/pdf" });
    await uploadFile(file, true);
  } catch (error) {
    setUploadStatus(networkMessage(error, "Couldn't load the sample."), true);
  }
}

function showDocument(data, isSample) {
  state.documentId = data.document_id;

  els.dropzone.hidden = true;
  els.sampleLine.hidden = true;
  els.docCard.hidden = false;
  els.docName.textContent = data.filename;
  els.docMeta.textContent =
    plural(data.pages, "page") + ", " + plural(data.chunks, "passage") + " indexed";

  showSuggestions(isSample ? SAMPLE_QUESTIONS : GENERAL_QUESTIONS);
  setComposerEnabled(true);

  // A new document starts a new conversation.
  els.conversation.replaceChildren();
  const notice = document.createElement("p");
  notice.className = "notice";
  notice.textContent = "Now asking about " + data.filename + ".";
  els.conversation.appendChild(notice);

  els.question.focus();
}

function forgetDocument(message) {
  state.documentId = null;
  els.docCard.hidden = true;
  els.dropzone.hidden = false;
  els.sampleLine.hidden = false;
  els.suggestions.hidden = true;
  setComposerEnabled(false);
  setUploadStatus(message, true);
}

function showSuggestions(questions) {
  els.suggestionList.replaceChildren();
  for (const text of questions) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "suggestion";
    button.textContent = text;
    button.addEventListener("click", () => askQuestion(text));
    item.appendChild(button);
    els.suggestionList.appendChild(item);
  }
  els.suggestions.hidden = false;
}

/* ---------- Asking ---------- */

function setComposerEnabled(enabled) {
  els.question.disabled = !enabled;
  els.question.placeholder = enabled ? "Ask about your PDF" : "Upload a PDF to start asking";
  updateAskButton();
}

function updateAskButton() {
  const text = els.question.value.trim();
  const tooLong = text.length > state.limits.max_question_chars;
  els.askButton.disabled = state.busy || !state.documentId || text === "" || tooLong;
  for (const button of els.suggestionList.querySelectorAll("button")) {
    button.disabled = state.busy;
  }
}

function updateCharCount() {
  const length = els.question.value.length;
  const max = state.limits.max_question_chars;
  if (length < max * 0.8) {
    els.charCount.textContent = "";
  } else {
    els.charCount.textContent = length + " / " + max;
  }
  els.charCount.classList.toggle("is-over", length > max);
}

function resizeQuestionBox() {
  els.question.style.height = "auto";
  els.question.style.height = Math.min(els.question.scrollHeight + 3, 200) + "px";
}

async function askQuestion(text) {
  const question = text.trim();
  if (question === "" || state.busy || !state.documentId) {
    return;
  }

  state.busy = true;
  updateAskButton();

  const turn = document.createElement("article");
  turn.className = "turn";

  const questionEl = document.createElement("p");
  questionEl.className = "question";
  questionEl.textContent = question;
  turn.appendChild(questionEl);

  const answerEl = document.createElement("div");
  answerEl.className = "answer";
  const pending = document.createElement("p");
  pending.className = "pending";
  pending.textContent = "Searching the document";
  answerEl.appendChild(pending);
  turn.appendChild(answerEl);

  els.conversation.appendChild(turn);
  turn.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });

  try {
    const response = await fetch("/api/documents/" + encodeURIComponent(state.documentId) + "/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question }),
    });
    const data = await readJson(response);

    if (response.status === 404) {
      showAnswerError(answerEl, "This document was forgotten after an hour without use. Upload it again to keep asking.");
      forgetDocument("Upload the PDF again to continue.");
      return;
    }
    if (!response.ok) {
      throw new Error(errorMessage(data, "Something went wrong. Try again."));
    }

    renderAnswer(answerEl, data);
    els.question.value = "";
    resizeQuestionBox();
    updateCharCount();
  } catch (error) {
    showAnswerError(answerEl, networkMessage(error, "Something went wrong. Try again."));
  } finally {
    state.busy = false;
    updateAskButton();
    if (state.documentId) {
      els.question.focus();
    }
  }
}

function showAnswerError(answerEl, message) {
  answerEl.replaceChildren();
  const error = document.createElement("p");
  error.className = "answer-error";
  error.textContent = message;
  answerEl.appendChild(error);
}

/* ---------- Showing an answer ---------- */

function renderAnswer(answerEl, data) {
  state.answerCount = state.answerCount + 1;
  const prefix = "answer" + state.answerCount;
  const isUnknown = data.answer.trim().startsWith(NOT_FOUND_ANSWER);

  answerEl.replaceChildren();
  answerEl.classList.toggle("is-unknown", isUnknown);

  const textEl = document.createElement("div");
  textEl.className = "answer-text";
  const citedNumbers = new Set();
  // formatAnswer escapes the AI's text before adding any HTML of our own.
  textEl.innerHTML = formatAnswer(data.answer, data.sources, prefix, citedNumbers);
  answerEl.appendChild(textEl);

  if (data.sources.length === 0) {
    return;
  }

  if (isUnknown) {
    // Nothing answered the question, so keep the closest passages tucked away.
    answerEl.appendChild(buildFoldedSources("Closest passages found", data.sources, prefix));
    return;
  }

  const cited = [];
  const others = [];
  for (const source of data.sources) {
    if (citedNumbers.has(source.number)) {
      cited.push(source);
    } else {
      others.push(source);
    }
  }

  if (cited.length === 0) {
    // The AI didn't cite anything we recognise, so show everything it was given.
    answerEl.appendChild(buildOpenSources("Passages searched", data.sources, prefix));
    return;
  }

  answerEl.appendChild(buildOpenSources("Passages cited", cited, prefix));
  if (others.length > 0) {
    answerEl.appendChild(buildFoldedSources("Other passages searched", others, prefix));
  }
}

function buildOpenSources(title, sources, prefix) {
  const wrapper = document.createElement("section");
  wrapper.className = "sources";
  const heading = document.createElement("h3");
  heading.className = "sources-title";
  heading.textContent = title;
  wrapper.append(heading, buildSourceList(sources, prefix));
  return wrapper;
}

function buildFoldedSources(title, sources, prefix) {
  const wrapper = document.createElement("details");
  wrapper.className = "sources";
  const summary = document.createElement("summary");
  summary.textContent = title + " (" + sources.length + ")";
  wrapper.append(summary, buildSourceList(sources, prefix));
  return wrapper;
}

function buildSourceList(sources, prefix) {
  const list = document.createElement("ol");
  list.className = "source-list";

  for (const source of sources) {
    const item = document.createElement("li");
    item.className = "source is-clamped";
    item.id = prefix + "-source-" + source.number;
    item.tabIndex = -1;

    const tab = document.createElement("div");
    tab.className = "page-tab";
    tab.textContent = "p. " + source.page;
    const score = document.createElement("small");
    score.textContent = "match " + source.score.toFixed(2);
    tab.appendChild(score);

    const excerpt = document.createElement("blockquote");
    excerpt.className = "excerpt";
    const excerptText = document.createElement("span");
    excerptText.className = "excerpt-text";
    excerptText.textContent = source.text;
    excerpt.appendChild(excerptText);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "text-button source-toggle";
    toggle.textContent = "Show full passage";
    toggle.addEventListener("click", () => {
      const clamped = item.classList.toggle("is-clamped");
      toggle.textContent = clamped ? "Show full passage" : "Show less";
    });

    item.append(tab, excerpt, toggle);
    list.appendChild(item);
  }

  return list;
}

// Turns the AI's plain text into simple HTML: paragraphs, lists, bold,
// and clickable page marks for citations like [1] or [2, 3].
function formatAnswer(text, sources, prefix, citedNumbers) {
  const pageByNumber = new Map();
  for (const source of sources) {
    pageByNumber.set(source.number, source.page);
  }

  function inline(segment) {
    let html = escapeHtml(segment);
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(
      /\[(?:Sources?\s*)?(\d+(?:\s*,\s*\d+)*)\]|【(?:Sources?\s*)?(\d+(?:\s*,\s*\d+)*)】/g,
      (match, squareNumbers, cornerNumbers) => {
        const numbers = (squareNumbers || cornerNumbers).match(/\d+/g);
        let marks = "";
        for (const numberText of numbers) {
          const number = Number(numberText);
          if (pageByNumber.has(number)) {
            citedNumbers.add(number);
            const page = pageByNumber.get(number);
            marks +=
              '<button type="button" class="cite" data-target="' + prefix + "-source-" + number +
              '" aria-label="Show source ' + number + ", page " + page + '">p.&nbsp;' + page + "</button>";
          }
        }
        return marks === "" ? match : marks;
      }
    );
    return html;
  }

  const lines = text.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let paragraph = [];
  let listType = null;

  function flushParagraph() {
    if (paragraph.length > 0) {
      html += "<p>" + inline(paragraph.join(" ")) + "</p>";
      paragraph = [];
    }
  }

  function closeList() {
    if (listType !== null) {
      html += "</" + listType + ">";
      listType = null;
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();
    const bullet = line.match(/^[-*•]\s+(.*)$/);
    const numbered = line.match(/^\d+[.)]\s+(.*)$/);
    const heading = line.match(/^#{1,6}\s+(.*)$/);

    if (line === "") {
      flushParagraph();
      closeList();
    } else if (bullet || numbered) {
      flushParagraph();
      const type = bullet ? "ul" : "ol";
      if (listType !== type) {
        closeList();
        html += "<" + type + ">";
        listType = type;
      }
      html += "<li>" + inline((bullet || numbered)[1]) + "</li>";
    } else if (heading) {
      flushParagraph();
      closeList();
      html += '<p class="answer-heading">' + inline(heading[1]) + "</p>";
    } else {
      closeList();
      paragraph.push(line);
    }
  }
  flushParagraph();
  closeList();
  return html;
}

// Clicking a page mark highlights the passage it came from.
function showSource(targetId) {
  const item = document.getElementById(targetId);
  if (!item) {
    return;
  }
  const details = item.closest("details");
  if (details) {
    details.open = true;
  }
  item.classList.remove("is-clamped");
  const toggle = item.querySelector(".source-toggle");
  if (toggle) {
    toggle.textContent = "Show less";
  }
  item.classList.remove("is-marked");
  void item.offsetWidth; // restart the highlighter animation
  item.classList.add("is-marked");
  item.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "nearest" });
  item.focus({ preventScroll: true });
}

/* ---------- Wiring it all up ---------- */

els.fileInput.addEventListener("change", () => {
  uploadFile(els.fileInput.files[0], false);
});

els.sampleButton.addEventListener("click", uploadSample);

els.replaceDoc.addEventListener("click", () => {
  els.fileInput.click();
});

for (const eventName of ["dragenter", "dragover"]) {
  els.dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    els.dropzone.classList.add("is-dragging");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  els.dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    els.dropzone.classList.remove("is-dragging");
  });
}

els.dropzone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  uploadFile(file, false);
});

// Stop a PDF dropped outside the box from opening in the browser tab.
window.addEventListener("dragover", (event) => event.preventDefault());
window.addEventListener("drop", (event) => event.preventDefault());

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  askQuestion(els.question.value);
});

els.question.addEventListener("keydown", (event) => {
  // Enter sends; Shift+Enter starts a new line.
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    askQuestion(els.question.value);
  }
});

els.question.addEventListener("input", () => {
  resizeQuestionBox();
  updateCharCount();
  updateAskButton();
});

els.conversation.addEventListener("click", (event) => {
  const mark = event.target.closest(".cite");
  if (mark) {
    showSource(mark.dataset.target);
  }
});

loadLimits();
