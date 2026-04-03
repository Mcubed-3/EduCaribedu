let currentLessonData = null;
let currentUserContext = null;

function showUpgradeModal() {
  const modal = document.getElementById("upgradeModal");
  if (modal) modal.classList.remove("hidden");
}

function hideUpgradeModal() {
  const modal = document.getElementById("upgradeModal");
  if (modal) modal.classList.add("hidden");
}

async function fetchJSON(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!headers["Content-Type"] && options.body) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    let message = `Request failed: ${res.status}`;
    try {
      const data = await res.json();
      if (data.detail) message = data.detail;
    } catch (_) {}
    throw new Error(message);
  }

  if (res.status === 204) return {};
  return await res.json();
}

function setStatus(msg, kind = "neutral") {
  const statusEl = document.getElementById("status");
  if (!statusEl) return;
  statusEl.textContent = msg;
  statusEl.classList.remove("is-error", "is-success");
  if (kind === "error") statusEl.classList.add("is-error");
  if (kind === "success") statusEl.classList.add("is-success");
}

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

function populateSelect(id, values, placeholder = "Select...") {
  const el = document.getElementById(id);
  if (!el) return;

  const previousValue = el.value;
  el.innerHTML = "";

  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = placeholder;
  defaultOption.selected = true;
  el.appendChild(defaultOption);

  (values || []).forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    if (value === previousValue) option.selected = true;
    el.appendChild(option);
  });
}

function lessonToText(data) {
  const lesson = data.lesson;
  const lines = [];

  lines.push(`${data.title}`);
  lines.push("");
  lines.push(`Curriculum: ${lesson.curriculum}`);
  lines.push(`Subject: ${lesson.subject}`);
  lines.push(`Grade/Level: ${lesson.grade_level}`);
  lines.push(`Topic: ${lesson.topic}`);
  lines.push(`Structure: ${lesson.structure}`);
  lines.push(`Difficulty: ${lesson.difficulty}`);
  lines.push(`Generation Mode: ${lesson.generation_mode || "unknown"}`);
  lines.push("");
  lines.push("Objectives:");
  lesson.objectives.forEach((obj, i) => lines.push(`${i + 1}. ${obj}`));
  lines.push("");
  lines.push("Prior Knowledge:");
  lesson.prior_knowledge_questions.forEach((q) => lines.push(`- ${q}`));
  lines.push("");
  lines.push("Resources:");
  lesson.resources.forEach((r) => lines.push(`- ${r}`));
  lines.push("");

  Object.entries(lesson.sections).forEach(([section, items]) => {
    lines.push(`${section}:`);
    items.forEach((item) => lines.push(`- ${item}`));
    lines.push("");
  });

  lines.push("Assessment:");
  lesson.assessment.forEach((item) => lines.push(`- ${item}`));
  lines.push("");
  lines.push("Reflection:");
  lesson.reflection.forEach((item) => lines.push(`- ${item}`));

  return lines.join("\n");
}

function renderLesson(data) {
  currentLessonData = data;
  const output = document.getElementById("output");
  if (output) output.value = lessonToText(data);
}

function renderMatch(data) {
  const output = document.getElementById("output");
  if (!output) return;

  const match = data.match;
  if (!match) {
    output.value = "No curriculum match found.";
    return;
  }

  const lines = [
    `Best Match: ${match.name}`,
    `Curriculum: ${match.curriculum}`,
    `Subject: ${match.subject}`,
    `Level: ${match.level}`,
    `Strand: ${match.strand}`,
    `Confidence Score: ${data.score}`,
    "",
    "Objectives:",
  ];

  match.objectives.forEach((obj, i) => lines.push(`${i + 1}. ${obj.text} [${obj.bloom}]`));
  output.value = lines.join("\n");
}

function renderObjectives(data) {
  const output = document.getElementById("output");
  if (!output) return;

  const lines = ["Suggested Objectives:", ""];
  data.objectives.forEach((obj, i) => lines.push(`${i + 1}. ${obj.text} [${obj.bloom}]`));
  lines.push("", `Bloom verbs for selected difficulty: ${data.verbs.join(", ")}`);
  output.value = lines.join("\n");
}

function updateDashboardStats(summary) {
  const ids = [
    ["savedCount", summary.saved_count ?? 0],
    ["frameworkCount", summary.framework_count ?? 0],
    ["subjectCount", summary.subject_count ?? 0],
    ["levelCount", summary.level_count ?? 0],
    ["curriculumCount", summary.curriculum_count ?? 0],
  ];

  ids.forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  });

  const recentLessonsList = document.getElementById("recentLessonsList");
  if (!recentLessonsList) return;

  recentLessonsList.innerHTML = "";
  if (summary.recent_lessons && summary.recent_lessons.length) {
    summary.recent_lessons.forEach((lesson) => {
      const item = document.createElement("div");
      item.className = "recent-lesson-item";
      item.innerHTML = `
        <strong>${lesson.title}</strong>
        <small>${lesson.subject} • ${lesson.grade_level} • ${lesson.topic}</small>
      `;
      recentLessonsList.appendChild(item);
    });
  } else {
    recentLessonsList.innerHTML = `<p class="muted">No recent lessons yet.</p>`;
  }
}

async function loadDashboardSummary() {
  const summary = await fetchJSON("/api/dashboard");
  updateDashboardStats(summary);
}

async function loadSavedLessons() {
  const res = await fetchJSON("/api/lessons");
  const container = document.getElementById("savedLessonsList");
  if (!container) return;

  container.innerHTML = "";
  if (!res.lessons.length) {
    container.innerHTML = "<p class='muted'>No saved lessons yet.</p>";
    await loadDashboardSummary();
    return;
  }

  res.lessons.forEach((lesson) => {
    const item = document.createElement("div");
    item.className = "saved-lesson-card";
    item.innerHTML = `
      <strong>${lesson.title}</strong>
      <small>${lesson.subject} • ${lesson.grade_level}</small>
      <div class="lesson-buttons">
        <button type="button" data-id="${lesson.id}" class="load-lesson-btn secondary small-btn">Load</button>
        <button type="button" data-id="${lesson.id}" class="delete-lesson-btn secondary small-btn">Delete</button>
      </div>
    `;
    container.appendChild(item);
  });

  document.querySelectorAll(".load-lesson-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const lessonId = btn.dataset.id;
        const data = await fetchJSON(`/api/lessons/${lessonId}`);
        currentLessonData = data.data;
        document.getElementById("currentLessonId").value = data.id;
        renderLesson(data.data);
        scrollToBuilder();
        setStatus("Saved lesson loaded.", "success");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });
  });

  document.querySelectorAll(".delete-lesson-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const lessonId = btn.dataset.id;
        await fetchJSON(`/api/lessons/${lessonId}`, { method: "DELETE" });
        if (document.getElementById("currentLessonId").value === lessonId) {
          document.getElementById("currentLessonId").value = "";
        }
        await loadSavedLessons();
        await loadDashboardSummary();
        await loadCurrentUserContext();
        setStatus("Lesson deleted.", "success");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });
  });

  await loadDashboardSummary();
}

async function saveCurrentLesson() {
  if (!currentLessonData) {
    setStatus("Generate a lesson first before saving.", "error");
    return;
  }

  try {
    const res = await fetchJSON("/api/lessons", {
      method: "POST",
      body: JSON.stringify({ lesson_payload: currentLessonData }),
    });

    document.getElementById("currentLessonId").value = res.lesson.id;
    await loadSavedLessons();
    await loadDashboardSummary();
    await loadCurrentUserContext();
    setStatus("Lesson saved.", "success");
  } catch (e) {
    if ((e.message || "").toLowerCase().includes("saved lesson limit")) {
      setStatus("Storage limit reached.", "error");
      showUpgradeModal();
      return;
    }
    setStatus(e.message, "error");
  }
}

async function updateCurrentLesson() {
  const lessonId = document.getElementById("currentLessonId").value;
  if (!lessonId) {
    setStatus("Load or save a lesson first before updating.", "error");
    return;
  }
  if (!currentLessonData) {
    setStatus("No current lesson loaded.", "error");
    return;
  }

  try {
    await fetchJSON(`/api/lessons/${lessonId}`, {
      method: "PUT",
      body: JSON.stringify({ lesson_payload: currentLessonData }),
    });

    await loadSavedLessons();
    await loadDashboardSummary();
    setStatus("Saved lesson updated.", "success");
  } catch (e) {
    setStatus(e.message, "error");
  }
}

function toggleEditMode() {
  const output = document.getElementById("output");
  if (!output) return;
  output.readOnly = !output.readOnly;
  setStatus(output.readOnly ? "Edit mode off." : "Edit mode on. You can edit the text area.", "success");
}

async function downloadExport(format) {
  const output = document.getElementById("output");
  if (!output || !output.value.trim()) {
    setStatus("Nothing to export yet.", "error");
    return;
  }

  if (format === "docx" && isDocxLocked()) {
    showUpgradeModal();
    return;
  }

  let title = "Lesson Plan";
  if (currentLessonData && currentLessonData.title) {
    title = currentLessonData.title;
  } else {
    const firstLine = output.value.split("\n")[0].trim();
    if (firstLine) title = firstLine;
  }

  const endpoint = format === "pdf" ? "/api/export/pdf" : "/api/export/docx";
  setStatus(`Exporting ${format.toUpperCase()}...`);

  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ title, content: output.value }),
  });

  if (!res.ok) {
    let message = `Export failed: ${res.status}`;
    try {
      const data = await res.json();
      if (data.detail) message = data.detail;
    } catch (_) {}

    if ((message || "").toLowerCase().includes("pro plan only")) {
      showUpgradeModal();
      return;
    }

    throw new Error(message);
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const extension = format === "pdf" ? "pdf" : "docx";
  const safeTitle = title.replace(/[^\w\s-]/g, "").replace(/\s+/g, "_");
  a.download = `${safeTitle || "lesson_export"}.${extension}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);

  setStatus(`${format.toUpperCase()} exported.`, "success");
}

function scrollToBuilder() {
  const el = document.getElementById("builderSection");
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function clearBuilderForm() {
  document.getElementById("lessonForm")?.reset();
  document.getElementById("currentLessonId").value = "";
  currentLessonData = null;
  const output = document.getElementById("output");
  if (output) {
    output.value = "Your curriculum match, objectives and lesson plan will appear here.";
    output.readOnly = true;
  }
  setStatus("Ready for a new lesson.", "success");
}

function bindSubjectCards() {
  document.querySelectorAll(".subject-card").forEach((card) => {
    card.addEventListener("click", () => {
      const subject = card.dataset.subject;
      const subjectSelect = document.getElementById("subject");
      if (subjectSelect) subjectSelect.value = subject;
      scrollToBuilder();
      setStatus(`${subject} selected. Continue building your lesson.`, "success");
    });
  });
}

function bindPlanAwareActions() {
  const exportDocxBtn = document.getElementById("exportDocxBtn");
  if (exportDocxBtn && isDocxLocked()) {
    exportDocxBtn.setAttribute("title", "Upgrade to Pro to unlock DOCX export");
  }
}

async function init() {
  try {
    const [config] = await Promise.all([
      fetchJSON("/api/config"),
      loadCurrentUserContext(),
    ]);

    populateSelect("curriculum", config.curricula, "Select curriculum...");
    populateSelect("subject", config.subjects, "Select subject...");
    populateSelect("grade_level", config.levels, "Select grade/level...");
    populateSelect("structure", config.structures, "Select structure...");
    populateSelect("difficulty", config.difficulties, "Select difficulty...");
    populateSelect("lesson_type", config.lesson_types, "Select lesson type...");

    bindSubjectCards();
    bindPlanAwareActions();

    await loadSavedLessons();
    await loadDashboardSummary();

    document.getElementById("matchBtn")?.addEventListener("click", async () => {
      setStatus("Finding curriculum match...");
      try {
        const data = await fetchJSON("/api/curriculum/search", {
          method: "POST",
          body: JSON.stringify(formPayload()),
        });
        renderMatch(data);
        scrollToBuilder();
        setStatus("Curriculum match ready.", "success");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });

    document.getElementById("objectiveBtn")?.addEventListener("click", async () => {
      setStatus("Generating objectives...");
      try {
        const data = await fetchJSON("/api/objectives/generate", {
          method: "POST",
          body: JSON.stringify(formPayload()),
        });
        renderObjectives(data);
        scrollToBuilder();
        setStatus("Objectives generated.", "success");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });

    document.getElementById("lessonForm")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      setStatus("Generating lesson plan...");
      try {
        const data = await fetchJSON("/api/lesson/generate", {
          method: "POST",
          body: JSON.stringify(formPayload()),
        });
        document.getElementById("currentLessonId").value = "";
        renderLesson(data);
        await loadCurrentUserContext();
        await loadDashboardSummary();
        scrollToBuilder();
        setStatus("Lesson plan generated.", "success");
      } catch (e) {
        if ((e.message || "").toLowerCase().includes("monthly lesson generation limit")) {
          setStatus("Free limit reached.", "error");
          showUpgradeModal();
          return;
        }
        setStatus(e.message, "error");
      }
    });

    document.getElementById("saveLessonBtn")?.addEventListener("click", saveCurrentLesson);
    document.getElementById("updateLessonBtn")?.addEventListener("click", updateCurrentLesson);
    document.getElementById("toggleEditBtn")?.addEventListener("click", toggleEditMode);

    document.getElementById("refreshLessonsBtn")?.addEventListener("click", async () => {
      try {
        await loadCurrentUserContext();
        await loadSavedLessons();
        await loadDashboardSummary();
        bindPlanAwareActions();
        setStatus("Workspace refreshed.", "success");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });

    document.getElementById("exportDocxBtn")?.addEventListener("click", async () => {
      try {
        await downloadExport("docx");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });

    document.getElementById("exportPdfBtn")?.addEventListener("click", async () => {
      try {
        await downloadExport("pdf");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });

    document.getElementById("newLessonBtn")?.addEventListener("click", () => {
      clearBuilderForm();
      scrollToBuilder();
    });

    document.getElementById("heroNewLessonBtn")?.addEventListener("click", () => {
      clearBuilderForm();
      scrollToBuilder();
    });

    document.getElementById("scrollToBuilderBtn")?.addEventListener("click", scrollToBuilder);

    document.getElementById("closeUpgradeModal")?.addEventListener("click", hideUpgradeModal);
    document.getElementById("dismissUpgradeModal")?.addEventListener("click", hideUpgradeModal);

    const output = document.getElementById("output");
    if (output) output.readOnly = true;

    if (isFreePlan()) {
      setStatus("Free plan active. Generate lessons, then upgrade for unlimited use and DOCX export.");
    } else {
      setStatus("Ready.");
    }
  } catch (e) {
    console.error("Init failed:", e);
    setStatus(`Failed to load app config: ${e.message}`, "error");
  }
}

document.addEventListener("DOMContentLoaded", init);