let currentLessonData = null;
let currentUserContext = null;
let currentActivityData = null;

function showUpgradeModal() {
  document.getElementById("upgradeModal")?.classList.remove("hidden");
}
function hideUpgradeModal() {
  document.getElementById("upgradeModal")?.classList.add("hidden");
}

async function fetchJSON(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!headers["Content-Type"] && options.body) headers["Content-Type"] = "application/json";
  const res = await fetch(url, { ...options, headers, credentials: "include" });
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
  statusEl.className = `status ${kind === "error" ? "is-error" : kind === "success" ? "is-success" : ""}`.trim();
}

function setActivityStatus(msg, kind = "neutral") {
  const statusEl = document.getElementById("activityStatus");
  if (!statusEl) return;
  statusEl.textContent = msg;
  statusEl.className = `status ${kind === "error" ? "is-error" : kind === "success" ? "is-success" : ""}`.trim();
}

async function loadCurrentUserContext() {
  try {
    currentUserContext = await fetchJSON("/api/me");
  } catch (_) {
    currentUserContext = null;
  }
}

function isDocxLocked() {
  return !(currentUserContext?.plan_status?.docx_export);
}
function canGenerateActivities() {
  return !!currentUserContext?.plan_status?.activity_generation;
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

function activityPayload() {
  const lessonText = document.getElementById("output")?.value || "";
  const base = formPayload();
  return {
    curriculum: base.curriculum,
    subject: base.subject,
    grade_level: base.grade_level,
    topic: base.topic,
    difficulty: base.difficulty,
    activity_type: document.getElementById("activity_type")?.value || "mixed_quiz",
    question_count: Number(document.getElementById("activity_question_count")?.value || 6),
    duration_minutes: Number(document.getElementById("activity_duration_minutes")?.value || 20),
    include_answer_key: !!document.getElementById("include_answer_key")?.checked,
    include_mark_scheme: !!document.getElementById("include_mark_scheme")?.checked,
    integrate_into_lesson: !!document.getElementById("integrate_into_lesson")?.checked,
    lesson_text: lessonText,
    additional_notes: document.getElementById("activity_additional_notes")?.value || "",
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

function populateActivityTypes(items) {
  const el = document.getElementById("activity_type");
  if (!el) return;
  el.innerHTML = "";
  (items || []).forEach((item) => {
    const option = document.createElement("option");
    option.value = item.value;
    option.textContent = item.label;
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
  [["savedCount", summary.saved_count ?? 0], ["frameworkCount", summary.framework_count ?? 0], ["subjectCount", summary.subject_count ?? 0], ["levelCount", summary.level_count ?? 0], ["curriculumCount", summary.curriculum_count ?? 0]].forEach(([id, value]) => {
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
      item.innerHTML = `<strong>${lesson.title}</strong><small>${lesson.subject} • ${lesson.grade_level} • ${lesson.topic}</small>`;
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
      <hr>
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
      } catch (e) { setStatus(e.message, "error"); }
    });
  });
  document.querySelectorAll(".delete-lesson-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const lessonId = btn.dataset.id;
        await fetchJSON(`/api/lessons/${lessonId}`, { method: "DELETE" });
        if (document.getElementById("currentLessonId").value === lessonId) document.getElementById("currentLessonId").value = "";
        await loadSavedLessons();
        await loadDashboardSummary();
        setStatus("Lesson deleted.", "success");
      } catch (e) { setStatus(e.message, "error"); }
    });
  });
  await loadDashboardSummary();
}

async function saveCurrentLesson() {
  if (!currentLessonData) return setStatus("Generate a lesson first before saving.", "error");
  try {
    const res = await fetchJSON("/api/lessons", { method: "POST", body: JSON.stringify({ lesson_payload: currentLessonData }) });
    document.getElementById("currentLessonId").value = res.lesson.id;
    await loadSavedLessons();
    await loadDashboardSummary();
    await loadCurrentUserContext();
    setStatus("Lesson saved.", "success");
  } catch (e) {
    if ((e.message || "").toLowerCase().includes("saved lesson limit")) return showUpgradeModal();
    setStatus(e.message, "error");
  }
}

async function updateCurrentLesson() {
  const lessonId = document.getElementById("currentLessonId").value;
  if (!lessonId) return setStatus("Load or save a lesson first before updating.", "error");
  if (!currentLessonData) return setStatus("No current lesson loaded.", "error");
  try {
    await fetchJSON(`/api/lessons/${lessonId}`, { method: "PUT", body: JSON.stringify({ lesson_payload: currentLessonData }) });
    await loadSavedLessons();
    await loadDashboardSummary();
    setStatus("Saved lesson updated.", "success");
  } catch (e) { setStatus(e.message, "error"); }
}

function toggleEditMode() {
  const output = document.getElementById("output");
  if (!output) return;
  output.readOnly = !output.readOnly;
  setStatus(output.readOnly ? "Edit mode off." : "Edit mode on.", "success");
}

async function downloadTextExport(format, title, content, statusSetter) {
  const endpoint = format === "pdf" ? "/api/export/pdf" : "/api/export/docx";
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ title, content }),
  });
  if (!res.ok) {
    let message = `Export failed: ${res.status}`;
    try {
      const data = await res.json();
      if (data.detail) message = data.detail;
    } catch (_) {}
    throw new Error(message);
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${title.replace(/[^\w\s-]/g, "").replace(/\s+/g, "_") || "export"}.${format}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
  statusSetter(`${format.toUpperCase()} exported.`, "success");
}

async function downloadLessonExport(format) {
  const output = document.getElementById("output");
  if (!output || !output.value.trim()) return setStatus("Nothing to export yet.", "error");
  if (format === "docx" && isDocxLocked()) return showUpgradeModal();
  let title = currentLessonData?.title || output.value.split("\n")[0].trim() || "Lesson Plan";
  return downloadTextExport(format, title, output.value, setStatus);
}

async function downloadActivityExport(format) {
  const output = document.getElementById("activityOutput");
  if (!output || !output.value.trim()) return setActivityStatus("No activity has been generated yet.", "error");
  if (format === "docx" && isDocxLocked()) return showUpgradeModal();
  const title = currentActivityData?.title || "Activity Sheet";
  return downloadTextExport(format, title, output.value, setActivityStatus);
}

function scrollToBuilder() { document.getElementById("builderSection")?.scrollIntoView({ behavior: "smooth", block: "start" }); }

function clearBuilderForm() {
  document.getElementById("lessonForm")?.reset();
  document.getElementById("currentLessonId").value = "";
  currentLessonData = null;
  const output = document.getElementById("output");
  if (output) { output.value = "Your curriculum match, objectives and lesson plan will appear here."; output.readOnly = true; }
  setStatus("Ready for a new lesson.", "success");
}

function bindSubjectCards() {
  document.querySelectorAll(".subject-card").forEach((card) => {
    card.addEventListener("click", () => {
      const subject = card.dataset.subject;
      const subjectSelect = document.getElementById("subject");
      if (subjectSelect) {
        if (![...subjectSelect.options].some(opt => opt.value === subject)) {
          const option = document.createElement("option");
          option.value = subject;
          option.textContent = subject;
          subjectSelect.appendChild(option);
        }
        subjectSelect.value = subject;
      }
      scrollToBuilder();
      setStatus(`${subject} selected. Continue building your lesson.`, "success");
    });
  });
}

async function generateActivity() {
  if (!canGenerateActivities()) return showUpgradeModal();
  const payload = activityPayload();
  if (!payload.curriculum || !payload.subject || !payload.grade_level || !payload.topic) {
    return setActivityStatus("Select curriculum, subject, level, and topic first.", "error");
  }
  setActivityStatus("Generating activity...");
  try {
    const data = await fetchJSON("/api/activities/generate", { method: "POST", body: JSON.stringify(payload) });
    currentActivityData = data;
    const output = document.getElementById("activityOutput");
    if (output) output.value = data.content || "";
    if (payload.integrate_into_lesson && data.lesson_snippet) {
      const lessonOutput = document.getElementById("output");
      if (lessonOutput && lessonOutput.value.trim()) {
        lessonOutput.value += `\n\nActivity Snippet:\n${data.lesson_snippet}`;
      }
    }
    setActivityStatus("Activity generated.", "success");
  } catch (e) {
    if ((e.message || "").toLowerCase().includes("plus")) return showUpgradeModal();
    setActivityStatus(e.message, "error");
  }
}

async function init() {
  try {
    const [config] = await Promise.all([fetchJSON("/api/config"), loadCurrentUserContext()]);
    populateSelect("curriculum", config.curricula, "Select curriculum...");
    populateSelect("subject", config.subjects, "Select subject...");
    populateSelect("grade_level", config.levels, "Select grade/level...");
    populateSelect("structure", config.structures, "Select structure...");
    populateSelect("difficulty", config.difficulties, "Select difficulty...");
    populateSelect("lesson_type", config.lesson_types, "Select lesson type...");
    populateActivityTypes(config.activity_types || []);

    bindSubjectCards();
    await loadSavedLessons();
    await loadDashboardSummary();

    document.getElementById("matchBtn")?.addEventListener("click", async () => {
      setStatus("Finding curriculum match...");
      try { const data = await fetchJSON("/api/curriculum/search", { method: "POST", body: JSON.stringify(formPayload()) }); renderMatch(data); scrollToBuilder(); setStatus("Curriculum match ready.", "success"); }
      catch (e) { setStatus(e.message, "error"); }
    });

    document.getElementById("objectiveBtn")?.addEventListener("click", async () => {
      setStatus("Generating objectives...");
      try { const data = await fetchJSON("/api/objectives/generate", { method: "POST", body: JSON.stringify(formPayload()) }); renderObjectives(data); scrollToBuilder(); setStatus("Objectives generated.", "success"); }
      catch (e) { setStatus(e.message, "error"); }
    });

    document.getElementById("lessonForm")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      setStatus("Generating lesson plan...");
      try {
        const data = await fetchJSON("/api/lesson/generate", { method: "POST", body: JSON.stringify(formPayload()) });
        document.getElementById("currentLessonId").value = "";
        renderLesson(data);
        await loadCurrentUserContext();
        await loadDashboardSummary();
        scrollToBuilder();
        setStatus("Lesson plan generated.", "success");
      } catch (e) {
        if ((e.message || "").toLowerCase().includes("monthly lesson generation limit")) return showUpgradeModal();
        setStatus(e.message, "error");
      }
    });

    document.getElementById("saveLessonBtn")?.addEventListener("click", saveCurrentLesson);
    document.getElementById("updateLessonBtn")?.addEventListener("click", updateCurrentLesson);
    document.getElementById("toggleEditBtn")?.addEventListener("click", toggleEditMode);
    document.getElementById("refreshLessonsBtn")?.addEventListener("click", async () => { await loadCurrentUserContext(); await loadSavedLessons(); await loadDashboardSummary(); setStatus("Workspace refreshed.", "success"); });
    document.getElementById("exportDocxBtn")?.addEventListener("click", async () => { try { await downloadLessonExport("docx"); } catch (e) { setStatus(e.message, "error"); } });
    document.getElementById("exportPdfBtn")?.addEventListener("click", async () => { try { await downloadLessonExport("pdf"); } catch (e) { setStatus(e.message, "error"); } });
    document.getElementById("generateActivityBtn")?.addEventListener("click", generateActivity);
    document.getElementById("exportActivityDocxBtn")?.addEventListener("click", async () => { try { await downloadActivityExport("docx"); } catch (e) { setActivityStatus(e.message, "error"); } });
    document.getElementById("exportActivityPdfBtn")?.addEventListener("click", async () => { try { await downloadActivityExport("pdf"); } catch (e) { setActivityStatus(e.message, "error"); } });
    document.getElementById("newLessonBtn")?.addEventListener("click", () => { clearBuilderForm(); scrollToBuilder(); });
    document.getElementById("heroNewLessonBtn")?.addEventListener("click", () => { clearBuilderForm(); scrollToBuilder(); });
    document.getElementById("scrollToBuilderBtn")?.addEventListener("click", scrollToBuilder);
    document.getElementById("closeUpgradeModal")?.addEventListener("click", hideUpgradeModal);
    document.getElementById("dismissUpgradeModal")?.addEventListener("click", hideUpgradeModal);

    const output = document.getElementById("output");
    if (output) output.readOnly = true;
    setStatus("Ready.");
  } catch (e) {
    console.error("Init failed:", e);
    setStatus(`Failed to load app config: ${e.message}`, "error");
  }
}

document.addEventListener("DOMContentLoaded", init);
