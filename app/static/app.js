let currentLessonData = null;
let currentUserContext = null;
let currentActivityText = "";

function byId(id) {
  return document.getElementById(id);
}

function parseCommaList(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function showProfileModal() {
  const modal = byId("profileModal");
  if (modal) modal.classList.remove("hidden");
}

function hideProfileModal() {
  const modal = byId("profileModal");
  if (modal) modal.classList.add("hidden");
}

function profileSummaryText(profile) {
  const subjects = (profile?.subjects || []).join(", ") || "No subjects set";
  const levels = (profile?.grade_levels || []).join(", ") || "No grade levels set";
  const curriculum = profile?.curriculum || "No curriculum set";
  return `${subjects} • ${levels} • ${curriculum}`;
}

function populateProfileModal(profile) {
  if (byId("profile_subjects")) byId("profile_subjects").value = (profile?.subjects || []).join(", ");
  if (byId("profile_grade_levels")) byId("profile_grade_levels").value = (profile?.grade_levels || []).join(", ");
  if (byId("profile_curriculum")) byId("profile_curriculum").value = profile?.curriculum || "";
}

function applyProfileDefaultsToBuilder() {
  const profile = currentUserContext?.profile || {};
  const completed = !!profile.profile_completed;
  const banner = byId("profileSummaryBanner");
  const summaryText = byId("profileSummaryText");
  const drivenFields = document.querySelectorAll(".profile-driven-field");

  if (summaryText) {
    summaryText.textContent = profileSummaryText(profile);
  }

  if (completed) {
    if (banner) banner.classList.remove("hidden");

    if (profile.curriculum && byId("curriculum")) byId("curriculum").value = profile.curriculum;
    if (profile.curriculum && byId("activity_curriculum")) byId("activity_curriculum").value = profile.curriculum;

    if (Array.isArray(profile.subjects) && profile.subjects.length && byId("subject")) {
      byId("subject").value = profile.subjects[0];
    }
    if (Array.isArray(profile.subjects) && profile.subjects.length && byId("activity_subject")) {
      byId("activity_subject").value = profile.subjects[0];
    }

    if (Array.isArray(profile.grade_levels) && profile.grade_levels.length && byId("grade_level")) {
      byId("grade_level").value = profile.grade_levels[0];
    }
    if (Array.isArray(profile.grade_levels) && profile.grade_levels.length && byId("activity_grade_level")) {
      byId("activity_grade_level").value = profile.grade_levels[0];
    }

    drivenFields.forEach((field) => {
      field.style.display = "none";
    });
  } else {
    if (banner) banner.classList.add("hidden");
    drivenFields.forEach((field) => {
      field.style.display = "";
    });
    showProfileModal();
  }
}

async function saveProfileFromModal() {
  const subjects = parseCommaList(byId("profile_subjects")?.value || "");
  const gradeLevels = parseCommaList(byId("profile_grade_levels")?.value || "");
  const curriculum = byId("profile_curriculum")?.value || "";

  if (!subjects.length || !gradeLevels.length || !curriculum) {
    setStatus("Complete subject, grade level, and curriculum before saving your profile.", "error");
    return;
  }

  await fetchJSON("/api/profile", {
    method: "POST",
    body: JSON.stringify({
      subjects,
      grade_levels: gradeLevels,
      curriculum,
    }),
  });

  await loadCurrentUserContext();
  populateProfileModal(currentUserContext?.profile || {});
  applyProfileDefaultsToBuilder();
  hideProfileModal();
  setStatus("Profile saved. Your dashboard will now use those defaults.", "success");
}

function showUpgradeModal() {
  const modal = byId("upgradeModal");
  if (modal) modal.classList.remove("hidden");
}

function hideUpgradeModal() {
  const modal = byId("upgradeModal");
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
  const statusEl = byId("status");
  if (!statusEl) return;
  statusEl.textContent = msg;
  statusEl.classList.remove("is-error", "is-success");
  if (kind === "error") statusEl.classList.add("is-error");
  if (kind === "success") statusEl.classList.add("is-success");
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
  return !!(currentUserContext?.plan_status?.activity_generation);
}

function formPayload() {
  const profile = currentUserContext?.profile || {};

  return {
    curriculum: profile.curriculum || byId("curriculum")?.value || "",
    subject: profile.subjects?.[0] || byId("subject")?.value || "",
    grade_level: profile.grade_levels?.[0] || byId("grade_level")?.value || "",
    structure: byId("structure")?.value || "5Es",
    difficulty: byId("difficulty")?.value || "Intermediate",
    lesson_type: byId("lesson_type")?.value || "Theory",
    topic: byId("topic")?.value || "",
    subtopic: byId("subtopic")?.value || "",
    objective_count: Number(byId("objective_count")?.value || 3),
    duration_minutes: Number(byId("duration_minutes")?.value || 60),
    description: byId("description")?.value || "",
    resources: byId("resources")?.value || "",
  };
}

function populateSelect(id, values, placeholder = "Select...") {
  const el = byId(id);
  if (!el) return;

  const previousValue = el.value;
  el.innerHTML = "";

  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = placeholder;
  el.appendChild(defaultOption);

  (values || []).forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    if (value === previousValue) option.selected = true;
    el.appendChild(option);
  });
}

function updateDashboardStats(summary) {
  const saved = byId("savedCount");
  if (saved) saved.textContent = summary.saved_count ?? 0;

  const recentLessonsList = byId("recentLessonsList");
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
  const container = byId("savedLessonsList");
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
        <button type="button" data-id="${lesson.id}" class="load-lesson-btn btn btn-secondary small-btn">Load</button>
        <button type="button" data-id="${lesson.id}" class="delete-lesson-btn btn btn-secondary small-btn">Delete</button>
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
        const currentLessonId = byId("currentLessonId");
        if (currentLessonId) currentLessonId.value = data.id;
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
        const currentLessonId = byId("currentLessonId");
        if (currentLessonId && currentLessonId.value === lessonId) {
          currentLessonId.value = "";
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

function lessonToText(data) {
  const lesson = data.lesson || {};
  const lines = [];

  lines.push(`${data.title || "Lesson Plan"}`);
  lines.push("");

  const meta = [
    ["Curriculum", lesson.curriculum],
    ["Subject", lesson.subject],
    ["Grade/Level", lesson.grade_level],
    ["Topic", lesson.topic],
    ["Structure", lesson.structure],
    ["Difficulty", lesson.difficulty],
    ["Generation Mode", lesson.generation_mode || "unknown"],
  ];

  meta.forEach(([label, value]) => {
    if (value) lines.push(`${label}: ${value}`);
  });

  lines.push("");

  if (lesson.attainment_target) {
    lines.push("Attainment Target:");
    lines.push(lesson.attainment_target);
    lines.push("");
  }

  if (lesson.theme || lesson.strand) {
    if (lesson.theme) lines.push(`Theme: ${lesson.theme}`);
    if (lesson.strand) lines.push(`Strand: ${lesson.strand}`);
    lines.push("");
  }

  if (lesson.class_profile && Object.keys(lesson.class_profile).length) {
    lines.push("Class Profile:");
    Object.entries(lesson.class_profile).forEach(([key, value]) => {
      if (value == null || value === "") return;
      const rendered = Array.isArray(value) ? value.join(", ") : value;
      lines.push(`- ${toTitle(key)}: ${rendered}`);
    });
    lines.push("");
  }

  if (lesson.domain_objectives && Object.keys(lesson.domain_objectives).length) {
    lines.push("Specific Objectives:");
    if (lesson.domain_objectives.cognitive) {
      lines.push(`- Cognitive: ${lesson.domain_objectives.cognitive}`);
    }
    if (lesson.domain_objectives.affective) {
      lines.push(`- Affective: ${lesson.domain_objectives.affective}`);
    }
    if (lesson.domain_objectives.psychomotor) {
      lines.push(`- Psychomotor: ${lesson.domain_objectives.psychomotor}`);
    }
    lines.push("");
  }

  if (lesson.prior_learning) {
    lines.push("Prior Learning:");
    lines.push(lesson.prior_learning);
    lines.push("");
  }

  if (Array.isArray(lesson.prior_knowledge_questions) && lesson.prior_knowledge_questions.length) {
    lines.push("Prior Knowledge:");
    lesson.prior_knowledge_questions.forEach((q) => {
      lines.push(`- ${q}`);
    });
    lines.push("");
  }

  if (Array.isArray(lesson.resources) && lesson.resources.length) {
    lines.push("Resources:");
    lesson.resources.forEach((r) => {
      lines.push(`- ${r}`);
    });
    lines.push("");
  }

  if (lesson.sections && typeof lesson.sections === "object") {
    Object.entries(lesson.sections).forEach(([section, items]) => {
      if (!items || !items.length) return;
      lines.push(`${section}:`);
      items.forEach((item) => {
        lines.push(`- ${item}`);
      });
      lines.push("");
    });
  }

  if (Array.isArray(lesson.apse_pathways) && lesson.apse_pathways.length) {
    lines.push("APSE Pathways:");
    lesson.apse_pathways.forEach((item) => {
      lines.push(`- ${item}`);
    });
    lines.push("");
  }

  if (Array.isArray(lesson.stem_skills) && lesson.stem_skills.length) {
    lines.push("STEM / Skills:");
    lesson.stem_skills.forEach((item) => {
      lines.push(`- ${item}`);
    });
    lines.push("");
  }

  if (lesson.assessment_criteria) {
    lines.push("Assessment Criteria:");
    lines.push(lesson.assessment_criteria);
    lines.push("");
  }

  if (Array.isArray(lesson.assessment) && lesson.assessment.length) {
    lines.push("Assessment:");
    lesson.assessment.forEach((item) => {
      lines.push(`- ${item}`);
    });
    lines.push("");
  }

  if (Array.isArray(lesson.reflection) && lesson.reflection.length) {
    lines.push("Reflection:");
    lesson.reflection.forEach((item) => {
      lines.push(`- ${item}`);
    });
  }

  return lines.join("\n").trim();
}

function renderLesson(data) {
  currentLessonData = data;
  const raw = lessonToText(data);
  const output = byId("output");
  if (output) output.value = raw;
  renderMathPreview("output", "outputPreview");
}

function escapeHtml(text) {
  return String(text || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function normalizeMathText(text) {
  if (!text) return "";

  let out = String(text);

  // Convert double-escaped delimiters into real MathJax delimiters
  out = out.replace(/\\\\\(/g, "\\(").replace(/\\\\\)/g, "\\)");
  out = out.replace(/\\\\\[/g, "\\[").replace(/\\\\\]/g, "\\]");

  // Remove stray inline delimiters around single plain letters in normal prose:
  // "\(a\) short real-life scenario" -> "a short real-life scenario"
  out = out.replace(/\\\(([A-Za-z])\\\)(?=\s+[A-Za-z])/g, "$1");

  // Remove stray inline delimiters around simple unit symbols:
  // "\(m\)" -> "m"
  out = out.replace(/\\\(([A-Za-z])\\\)(?=[\s).,;:!?]|$)/g, "$1");

  // Common symbols
  out = out.replace(/÷/g, "/");
  out = out.replace(/×/g, "\\times ");
  out = out.replace(/√\s*([A-Za-z0-9]+)/g, "\\\\(\\\\sqrt{$1}\\\\)");

  // Wrap simple powers like x^2
  out = out.replace(
    /(^|[\s:(=+-])([A-Za-z][A-Za-z0-9]*)\^([A-Za-z0-9]+)(?=$|[\s),.;:!?+\-])/g,
    '$1\\\\($2^{$3}\\\\)'
  );

  // Wrap simple fractions like 3/4
  out = out.replace(
    /(^|[\s:(=+-])(\d+)\s*\/\s*(\d+)(?=$|[\s),.;:!?])/g,
    '$1\\\\(\\\\frac{$2}{$3}\\\\)'
  );

  // Wrap simple coordinates like (2, -1)
  out = out.replace(
    /(^|[\s:=])\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)(?=$|[\s.,;:!?])/g,
    '$1\\\\(($2, $3)\\\\)'
  );

  // Wrap simple expressions like x^2 - 5x, 2x + 3, 3a - 2b
  out = out.replace(
    /(^|[\s:(=])((?:[+-]?\d*[A-Za-z](?:\^\d+)?)(?:\s*[+\-]\s*\d*[A-Za-z](?:\^\d+)?)*(?:\s*[+\-]\s*\d+)?)(?=$|[\s),.;:!?])/g,
    (match, prefix, expr) => {
      if (expr.includes("\\(") || expr.includes("\\[")) return match;
      if (!/[A-Za-z]/.test(expr)) return match;
      return `${prefix}\\\\(${expr.replace(/\^(\d+)/g, '^{$1}')}\\\\)`;
    }
  );

  // Clean accidental double wrapping like \(\(x^2\)\)
  out = out.replace(/\\\(\s*\\\((.*?)\\\)\s*\\\)/g, "\\\\($1\\\\)");

  return out;
}

async function renderMathPreview(textareaId, previewId) {
  const src = byId(textareaId);
  const dest = byId(previewId);
  if (!src || !dest) return;

  const normalized = normalizeMathText(src.value || "");
  const html = escapeHtml(normalized).replace(/\n/g, "<br>");
  dest.innerHTML = html;

  if (window.MathJax && window.MathJax.typesetClear) {
    try {
      window.MathJax.typesetClear([dest]);
    } catch (_) {}
  }

  if (window.MathJax && window.MathJax.typesetPromise) {
    try {
      await window.MathJax.typesetPromise([dest]);
    } catch (e) {
      console.error("MathJax render failed", e);
    }
  }
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

    const currentLessonId = byId("currentLessonId");
    if (currentLessonId) currentLessonId.value = res.lesson.id;

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
  const lessonId = byId("currentLessonId")?.value || "";
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
  const output = byId("output");
  if (!output) return;
  output.readOnly = !output.readOnly;
  setStatus(output.readOnly ? "Edit mode off." : "Edit mode on. Edit the raw text, preview updates below.", "success");
}

async function triggerFileDownloadFromResponse(res, fallbackName) {
  if (!res.ok) {
    let message = "Export failed";
    try {
      const data = await res.json();
      if (data.detail) message = data.detail;
    } catch (_) {}
    throw new Error(message);
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fallbackName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function downloadLessonExport(format) {
  const title = currentLessonData?.title || "Lesson Plan";
  const textContent = byId("output")?.value || "";
  const htmlContent = byId("outputPreview")?.innerHTML || "";

  if (format === "docx") {
    if (isDocxLocked()) {
      showUpgradeModal();
      return;
    }

    const res = await fetch("/api/export/docx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        title,
        content: textContent,
      }),
    });

    await triggerFileDownloadFromResponse(res, "lesson.docx");
    setStatus("DOCX exported", "success");
    return;
  }

  const res = await fetch("/api/export/pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      title,
      html: htmlContent,
    }),
  });

  await triggerFileDownloadFromResponse(res, "lesson.pdf");
  setStatus("PDF exported", "success");
}

async function downloadActivityExport(format) {
  const title = "Classroom Activity";
  const textContent = byId("activityOutput")?.value || "";
  const htmlContent = byId("activityPreview")?.innerHTML || "";

  if (format === "docx") {
    if (isDocxLocked()) {
      showUpgradeModal();
      return;
    }

    const res = await fetch("/api/export/docx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        title,
        content: textContent,
      }),
    });

    await triggerFileDownloadFromResponse(res, "activity.docx");
    setStatus("Activity DOCX exported", "success");
    return;
  }

  const res = await fetch("/api/export/pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      title,
      html: htmlContent,
    }),
  });

  await triggerFileDownloadFromResponse(res, "activity.pdf");
  setStatus("Activity PDF exported", "success");
}

function scrollToBuilder() {
  const el = byId("builderSection");
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function clearBuilderForm() {
  byId("lessonForm")?.reset();

  const currentLessonId = byId("currentLessonId");
  if (currentLessonId) currentLessonId.value = "";

  currentLessonData = null;
  currentActivityText = "";

  const output = byId("output");
  if (output) {
    output.value = "Your curriculum-aligned lesson plan will appear here.";
    output.readOnly = true;
  }

  const activityOutput = byId("activityOutput");
  if (activityOutput) {
    activityOutput.value = "Generated activity content will appear here.";
  }

  renderMathPreview("output", "outputPreview");
  renderMathPreview("activityOutput", "activityPreview");
  setStatus("Ready for a new lesson.", "success");
}

function getActivitySourceMode() {
  return byId("activity_source_mode")?.value || "lesson";
}

function activityPayload() {
  const sourceMode = getActivitySourceMode();

  const base = {
    activity_type: byId("activity_type")?.value || "",
    item_count: Number(byId("activity_item_count")?.value || 8),
    include_answer_key: (byId("activity_answer_key")?.value || "yes") === "yes",
    include_mark_scheme: (byId("activity_mark_scheme")?.value || "no") === "yes",
    source_mode: sourceMode,
  };

  if (sourceMode === "lesson") {
    return {
      ...base,
      lesson_payload: currentLessonData,
    };
  }

  return {
    ...base,
    curriculum: byId("activity_curriculum")?.value || "",
    subject: byId("activity_subject")?.value || "",
    grade_level: byId("activity_grade_level")?.value || "",
    difficulty: byId("activity_difficulty")?.value || "",
    topic: byId("activity_topic")?.value || "",
  };
}

function formatActivityContent(content) {
  if (content == null) return "";
  if (typeof content === "string") return content.trim();

  if (Array.isArray(content)) {
    return content.map((item, index) => formatActivityItem(item, index)).join("\n\n").trim();
  }

  if (typeof content === "object") {
    const orderedKeys = [
      "title",
      "student_instructions",
      "worksheet_items",
      "activity",
      "questions",
      "answer_key",
      "mark_scheme",
    ];

    const lines = [];

    orderedKeys.forEach((key) => {
      if (!(key in content)) return;

      const value = content[key];
      if (!value || (Array.isArray(value) && !value.length)) return;

      if (key === "title") {
        lines.push(String(value).trim());
        lines.push("");
        return;
      }

      lines.push(`${toTitle(key)}:`);

      if (Array.isArray(value)) {
        value.forEach((item, index) => {
          if (["worksheet_items", "activity", "questions"].includes(key)) {
            lines.push(formatActivityItem(item, index));
          } else {
            lines.push(`- ${formatActivityValue(item)}`);
          }
        });
      } else {
        lines.push(formatActivityValue(value));
      }

      lines.push("");
    });

    return lines.join("\n").trim();
  }

  return String(content).trim();
}


function formatActivityItem(item, index = 0) {
  if (typeof item === "string") return `${index + 1}. ${item.trim()}`;
  if (item == null) return `${index + 1}.`;
  if (typeof item !== "object") return `${index + 1}. ${String(item).trim()}`;

  const lines = [];
  const prompt =
    item.question ||
    item.prompt ||
    item.text ||
    item.title ||
    item.clue ||
    `Question ${index + 1}`;

  lines.push(`${index + 1}. ${String(prompt).trim()}`);

  if (Array.isArray(item.options) && item.options.length) {
    item.options.forEach((opt, i) => {
      const label = String.fromCharCode(65 + i);
      lines.push(`   ${label}. ${typeof opt === "string" ? opt.trim() : formatActivityValue(opt)}`);
    });
  }

  if (item.answer) {
    lines.push(`   Answer: ${formatActivityValue(item.answer).trim()}`);
  }

  if (item.explanation) {
    lines.push(`   Explanation: ${formatActivityValue(item.explanation).trim()}`);
  }

  if (item.mark_scheme) {
    lines.push(`   Mark Scheme: ${formatActivityValue(item.mark_scheme).trim()}`);
  }

  return lines.join("\n");
}

function formatActivityValue(value) {
  if (value == null) return "";
  if (typeof value === "string") return value.trim();

  if (Array.isArray(value)) {
    return value.map((v) => formatActivityValue(v)).join(", ");
  }

  if (typeof value === "object") {
    return Object.entries(value)
      .filter(([k]) => !["teacher_notes", "teachernotes"].includes(String(k).toLowerCase()))
      .map(([k, v]) => `${toTitle(k)}: ${formatActivityValue(v)}`)
      .join("; ");
  }

  return String(value).trim();
}

async function generateActivity() {
  if (!canGenerateActivities()) {
    showUpgradeModal();
    return;
  }

  const mode = getActivitySourceMode();
  const activityType = byId("activity_type")?.value || "";
  if (!activityType) {
    setStatus("Select an activity type first.", "error");
    return;
  }

  if (mode === "lesson" && !currentLessonData) {
    setStatus("Generate or load a lesson first, or switch to standalone activity.", "error");
    return;
  }

  if (mode === "standalone") {
    const curriculum = byId("activity_curriculum")?.value || "";
    const subject = byId("activity_subject")?.value || "";
    const gradeLevel = byId("activity_grade_level")?.value || "";
    const difficulty = byId("activity_difficulty")?.value || "";
    const topic = byId("activity_topic")?.value || "";

    if (!curriculum || !subject || !gradeLevel || !difficulty || !topic.trim()) {
      setStatus("Complete all standalone activity fields first.", "error");
      return;
    }
  }

  setStatus("Generating activity...");
  try {
    const data = await fetchJSON("/api/activity/generate", {
      method: "POST",
      body: JSON.stringify(activityPayload()),
    });

    currentActivityText = formatActivityContent(
      data.content ?? data.activity ?? data.items ?? data.questions ?? data
    );

    const activityOutput = byId("activityOutput");
    if (activityOutput) activityOutput.value = currentActivityText || "No activity content returned.";

    await renderMathPreview("activityOutput", "activityPreview");
    await loadCurrentUserContext();
    setStatus("Activity generated.", "success");
  } catch (e) {
    if ((e.message || "").toLowerCase().includes("plus")) {
      showUpgradeModal();
      return;
    }
    setStatus(e.message, "error");
  }
}

async function insertActivitySnippetIntoLesson() {
  const output = byId("output");
  if (!output) return;

  if (!currentActivityText.trim()) {
    setStatus("Generate an activity first.", "error");
    return;
  }

  const cleaned = currentActivityText
    .split("\n")
    .filter((line) => !line.trim().toLowerCase().startsWith("teacher notes"))
    .join("\n");

  const snippet = `\n\nClassroom Activity:\n${cleaned}\n`;
  output.value = `${output.value}${snippet}`;
  await renderMathPreview("output", "outputPreview");
  setStatus("Activity inserted into lesson.", "success");
}

async function loadConfig() {
  const config = await fetchJSON("/api/config");

  populateSelect("curriculum", config.curricula, "Select curriculum...");
  populateSelect("subject", config.subjects, "Select subject...");
  populateSelect("grade_level", config.levels, "Select grade/level...");
  populateSelect("structure", config.structures, "Select structure...");
  populateSelect("difficulty", config.difficulties, "Select difficulty...");
  populateSelect("lesson_type", config.lesson_types, "Select lesson type...");

  populateSelect("activity_curriculum", config.curricula, "Select curriculum...");
  populateSelect("activity_subject", config.subjects, "Select subject...");
  populateSelect("activity_grade_level", config.levels, "Select grade/level...");
  populateSelect("activity_difficulty", config.difficulties, "Select difficulty...");

  populateProfileModal(config.profile || currentUserContext?.profile || {});
  applyProfileDefaultsToBuilder();
}

function updateActivityModeUI() {
  const mode = getActivitySourceMode();

  const standaloneIds = [
    "activity_curriculum",
    "activity_subject",
    "activity_grade_level",
    "activity_difficulty",
    "activity_topic",
  ];

  standaloneIds.forEach((id) => {
    const el = byId(id);
    if (!el) return;

    const wrapper = el.closest(".field");
    if (!wrapper) return;

    wrapper.style.display = mode === "standalone" ? "" : "none";
  });

  const insertBtn = byId("insertActivitySnippetBtn");
  if (insertBtn) {
    insertBtn.style.display = mode === "lesson" ? "" : "none";
  }
}

async function init() {
  try {
    await loadCurrentUserContext();
    await loadConfig();
    await loadSavedLessons();
    await loadDashboardSummary();

    const lessonForm = byId("lessonForm");
    lessonForm?.addEventListener("submit", async (event) => {
      event.preventDefault();
      setStatus("Generating lesson plan...");
      try {
        const data = await fetchJSON("/api/lesson/generate", {
          method: "POST",
          body: JSON.stringify(formPayload()),
        });

        const currentLessonId = byId("currentLessonId");
        if (currentLessonId) currentLessonId.value = "";

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

    byId("saveLessonBtn")?.addEventListener("click", saveCurrentLesson);
    byId("updateLessonBtn")?.addEventListener("click", updateCurrentLesson);
    byId("toggleEditBtn")?.addEventListener("click", toggleEditMode);

    byId("output")?.addEventListener("input", () => renderMathPreview("output", "outputPreview"));
    byId("activityOutput")?.addEventListener("input", () => renderMathPreview("activityOutput", "activityPreview"));

    byId("refreshLessonsBtn")?.addEventListener("click", async () => {
      try {
        await loadCurrentUserContext();
        await loadSavedLessons();
        await loadDashboardSummary();
        setStatus("Workspace refreshed.", "success");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });

    byId("exportDocxBtn")?.addEventListener("click", async () => {
      try {
        await downloadLessonExport("docx");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });

    byId("exportPdfBtn")?.addEventListener("click", async () => {
      try {
        await downloadLessonExport("pdf");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });

    byId("generateActivityBtn")?.addEventListener("click", generateActivity);
    byId("insertActivitySnippetBtn")?.addEventListener("click", insertActivitySnippetIntoLesson);

    byId("exportActivityPdfBtn")?.addEventListener("click", async () => {
      try {
        await downloadActivityExport("pdf");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });

    byId("exportActivityDocxBtn")?.addEventListener("click", async () => {
      try {
        await downloadActivityExport("docx");
      } catch (e) {
        setStatus(e.message, "error");
      }
    });

    byId("newLessonBtn")?.addEventListener("click", () => {
      clearBuilderForm();
      scrollToBuilder();
    });

    byId("heroNewLessonBtn")?.addEventListener("click", () => {
      clearBuilderForm();
      scrollToBuilder();
    });

    byId("activity_source_mode")?.addEventListener("change", updateActivityModeUI);

    byId("saveProfileBtn")?.addEventListener("click", saveProfileFromModal);
    byId("closeProfileModal")?.addEventListener("click", hideProfileModal);
    byId("editProfileSidebarBtn")?.addEventListener("click", () => {
      populateProfileModal(currentUserContext?.profile || {});
      showProfileModal();
    });
    byId("editProfileBannerBtn")?.addEventListener("click", () => {
      populateProfileModal(currentUserContext?.profile || {});
      showProfileModal();
    });

    byId("closeUpgradeModal")?.addEventListener("click", hideUpgradeModal);
    byId("dismissUpgradeModal")?.addEventListener("click", hideUpgradeModal);

    const output = byId("output");
    if (output) output.readOnly = true;

    updateActivityModeUI();
    await renderMathPreview("output", "outputPreview");
    await renderMathPreview("activityOutput", "activityPreview");
    setStatus("Ready.");
  } catch (e) {
    console.error("Init failed:", e);
    setStatus(`Failed to load app config: ${e.message}`, "error");
  }
}

document.addEventListener("DOMContentLoaded", init);