let currentLessonData = null;
let currentUserContext = null;

/* =========================
   MODAL FUNCTIONS
========================= */
function showUpgradeModal() {
  const modal = document.getElementById("upgradeModal");
  if (modal) modal.classList.remove("hidden");
}

function hideUpgradeModal() {
  const modal = document.getElementById("upgradeModal");
  if (modal) modal.classList.add("hidden");
}

/* =========================
   FETCH WRAPPER
========================= */
async function fetchJSON(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...options,
  });

  if (!res.ok) {
    let message = `Request failed: ${res.status}`;
    try {
      const data = await res.json();
      if (data.detail) message = data.detail;
    } catch (_) {}
    throw new Error(message);
  }

  return await res.json();
}

/* =========================
   STATUS
========================= */
function setStatus(msg, kind = "neutral") {
  const statusEl = document.getElementById("status");
  if (!statusEl) return;
  statusEl.textContent = msg;
  statusEl.classList.remove("is-error", "is-success");
  if (kind === "error") statusEl.classList.add("is-error");
  if (kind === "success") statusEl.classList.add("is-success");
}

/* =========================
   USER CONTEXT
========================= */
async function loadCurrentUserContext() {
  try {
    currentUserContext = await fetchJSON("/api/me");
  } catch (e) {
    currentUserContext = null;
  }
}

function isDocxLocked() {
  return !(currentUserContext?.plan_status?.docx_export);
}

function isFreePlan() {
  return currentUserContext?.user?.plan === "free";
}

/* =========================
   FORM
========================= */
function formPayload() {
  return {
    curriculum: document.getElementById("curriculum")?.value || "",
    subject: document.getElementById("subject")?.value || "",
    grade_level: document.getElementById("grade_level")?.value || "",
    structure: document.getElementById("structure")?.value || "",
    difficulty: document.getElementById("difficulty")?.value || "",
    lesson_type: document.getElementById("lesson_type")?.value || "",
    topic: document.getElementById("topic")?.value || "",
    subtopic: document.getElementById("subtopic")?.value || "",
    objective_count: Number(document.getElementById("objective_count")?.value || 3),
    duration_minutes: Number(document.getElementById("duration_minutes")?.value || 60),
    description: document.getElementById("description")?.value || "",
    resources: document.getElementById("resources")?.value || "",
  };
}

/* =========================
   LESSON RENDER
========================= */
function lessonToText(data) {
  const lesson = data.lesson;
  let text = `${data.title}\n\n`;

  text += `Subject: ${lesson.subject}\n`;
  text += `Level: ${lesson.grade_level}\n\n`;

  text += "Objectives:\n";
  lesson.objectives.forEach((o, i) => (text += `${i + 1}. ${o}\n`));

  return text;
}

function renderLesson(data) {
  currentLessonData = data;
  const output = document.getElementById("output");
  if (output) output.value = lessonToText(data);
}

/* =========================
   EXPORT
========================= */
async function downloadExport(format) {
  const output = document.getElementById("output");

  if (!output || !output.value.trim()) {
    setStatus("Nothing to export.", "error");
    return;
  }

  if (format === "docx" && isDocxLocked()) {
    showUpgradeModal();
    return;
  }

  const res = await fetch(`/api/export/${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      title: "Lesson Plan",
      content: output.value,
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    if (err.detail?.toLowerCase().includes("pro")) {
      showUpgradeModal();
      return;
    }
    throw new Error(err.detail || "Export failed");
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `lesson.${format}`;
  a.click();
}

/* =========================
   SAVE
========================= */
async function saveCurrentLesson() {
  if (!currentLessonData) {
    setStatus("Generate a lesson first.", "error");
    return;
  }

  try {
    await fetchJSON("/api/lessons", {
      method: "POST",
      body: JSON.stringify({ lesson_payload: currentLessonData }),
    });

    setStatus("Lesson saved.", "success");
  } catch (e) {
    if (e.message.toLowerCase().includes("limit")) {
      showUpgradeModal();
      return;
    }
    setStatus(e.message, "error");
  }
}

/* =========================
   GENERATE
========================= */
async function generateLesson() {
  setStatus("Generating lesson...");

  try {
    const data = await fetchJSON("/api/lesson/generate", {
      method: "POST",
      body: JSON.stringify(formPayload()),
    });

    renderLesson(data);
    setStatus("Lesson generated.", "success");
  } catch (e) {
    if (e.message.toLowerCase().includes("limit")) {
      showUpgradeModal();
      return;
    }
    setStatus(e.message, "error");
  }
}

/* =========================
   INIT
========================= */
async function init() {
  await loadCurrentUserContext();

  document
    .getElementById("generateBtn")
    ?.addEventListener("click", generateLesson);

  document
    .getElementById("saveLessonBtn")
    ?.addEventListener("click", saveCurrentLesson);

  document
    .getElementById("exportDocxBtn")
    ?.addEventListener("click", () => downloadExport("docx"));

  document
    .getElementById("exportPdfBtn")
    ?.addEventListener("click", () => downloadExport("pdf"));

  document
    .getElementById("closeUpgradeModal")
    ?.addEventListener("click", hideUpgradeModal);

  document
    .getElementById("dismissUpgradeModal")
    ?.addEventListener("click", hideUpgradeModal);

  if (isFreePlan()) {
    setStatus("Free plan active. Upgrade for full access.");
  } else {
    setStatus("Pro plan active.");
  }
}

document.addEventListener("DOMContentLoaded", init);