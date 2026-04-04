function setAdminStatus(msg, kind = "neutral") {
  const el = document.getElementById("adminStatus");
  if (!el) return;
  el.textContent = msg;
  el.classList.remove("is-error", "is-success");
  if (kind === "error") el.classList.add("is-error");
  if (kind === "success") el.classList.add("is-success");
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

  return await res.json();
}

function populateSelect(id, values, placeholder = "All") {
  const el = document.getElementById(id);
  if (!el) return;

  el.innerHTML = "";
  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = placeholder;
  el.appendChild(defaultOption);

  (values || []).forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    el.appendChild(option);
  });
}

function frameworkToForm(framework) {
  const topic = (framework.topics && framework.topics[0]) || {};

  document.getElementById("adminFrameworkId").value = framework.id || "";
  document.getElementById("framework_id").value = framework.id || "";
  document.getElementById("framework_curriculum").value = framework.curriculum || "";
  document.getElementById("framework_subject").value = framework.subject || "";
  document.getElementById("framework_level").value = framework.level || "";
  document.getElementById("framework_strand").value = framework.strand || "";
  document.getElementById("framework_topic_group").value = framework.topic_group || "";
  document.getElementById("framework_bands").value = (framework.bands || []).join(", ");
  document.getElementById("topic_name").value = topic.name || "";
  document.getElementById("topic_aliases").value = (topic.aliases || []).join(", ");
  document.getElementById("topic_keywords").value = (topic.keywords || []).join(", ");
  document.getElementById("topic_objectives").value = (topic.objectives || [])
    .map((obj) => `${obj.text || ""} | ${obj.bloom || ""}`)
    .join("\n");
  document.getElementById("topic_resources").value = (topic.resources || framework.resources || []).join("\n");
}

function formToFramework() {
  const id = document.getElementById("framework_id").value.trim();
  const curriculum = document.getElementById("framework_curriculum").value.trim();
  const subject = document.getElementById("framework_subject").value.trim();
  const level = document.getElementById("framework_level").value.trim();
  const strand = document.getElementById("framework_strand").value.trim();
  const topic_group = document.getElementById("framework_topic_group").value.trim();

  const bands = document.getElementById("framework_bands").value
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

  const topic_name = document.getElementById("topic_name").value.trim();

  const aliases = document.getElementById("topic_aliases").value
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

  const keywords = document.getElementById("topic_keywords").value
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

  const objectives = document.getElementById("topic_objectives").value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split("|");
      return {
        text: (parts[0] || "").trim(),
        bloom: (parts[1] || "Understand").trim(),
      };
    });

  const resources = document.getElementById("topic_resources").value
    .split("\n")
    .map((x) => x.trim())
    .filter(Boolean);

  return {
    id,
    curriculum,
    subject,
    level,
    bands,
    strand,
    topic_group,
    topics: [
      {
        name: topic_name,
        aliases,
        keywords,
        objectives,
        resources,
      },
    ],
  };
}

function clearAdminForm() {
  document.getElementById("adminFrameworkId").value = "";
  document.getElementById("framework_id").value = "";
  document.getElementById("framework_curriculum").value = "";
  document.getElementById("framework_subject").value = "";
  document.getElementById("framework_level").value = "";
  document.getElementById("framework_strand").value = "";
  document.getElementById("framework_topic_group").value = "";
  document.getElementById("framework_bands").value = "";
  document.getElementById("topic_name").value = "";
  document.getElementById("topic_aliases").value = "";
  document.getElementById("topic_keywords").value = "";
  document.getElementById("topic_objectives").value = "";
  document.getElementById("topic_resources").value = "";
}

function frameworkCardHTML(framework) {
  const topic = (framework.topics && framework.topics[0]) || {};
  return `
    <div class="admin-entry-card">
      <div class="admin-entry-card-head">
        <div>
          <strong>${topic.name || framework.id}</strong>
          <small>${framework.curriculum} • ${framework.subject} • ${framework.level}</small>
        </div>
        <button type="button" class="btn btn-secondary small-btn load-framework-btn" data-id="${framework.id}">Edit</button>
      </div>
      <div class="admin-entry-meta">
        <span>Strand: ${framework.strand || "—"}</span>
        <span>Topic group: ${framework.topic_group || "—"}</span>
      </div>
    </div>
  `;
}

async function loadAdminConfig() {
  const config = await fetchJSON("/api/config");
  populateSelect("adminCurriculumFilter", config.curricula, "All curricula");
  populateSelect("adminSubjectFilter", config.subjects, "All subjects");
  populateSelect("adminLevelFilter", config.levels, "All levels");
}

async function loadFrameworkList() {
  const curriculum = document.getElementById("adminCurriculumFilter").value;
  const subject = document.getElementById("adminSubjectFilter").value;
  const level = document.getElementById("adminLevelFilter").value;
  const query = document.getElementById("adminQueryFilter").value.trim();

  const params = new URLSearchParams();
  if (curriculum) params.append("curriculum", curriculum);
  if (subject) params.append("subject", subject);
  if (level) params.append("level", level);
  if (query) params.append("query", query);

  const res = await fetchJSON(`/api/admin/frameworks?${params.toString()}`);
  const container = document.getElementById("adminFrameworkList");
  if (!container) return;

  container.innerHTML = "";

  if (!res.frameworks.length) {
    container.innerHTML = "<p class='muted'>No framework entries found.</p>";
    return;
  }

  res.frameworks.forEach((framework) => {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = frameworkCardHTML(framework);
    container.appendChild(wrapper.firstElementChild);
  });

  document.querySelectorAll(".load-framework-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const frameworkId = btn.dataset.id;
        const res = await fetchJSON(`/api/admin/frameworks/${frameworkId}`);
        frameworkToForm(res.framework);
        setAdminStatus("Framework loaded.", "success");
      } catch (e) {
        setAdminStatus(e.message, "error");
      }
    });
  });
}

async function saveFrameworkChanges() {
  const frameworkId = document.getElementById("adminFrameworkId").value.trim();
  if (!frameworkId) {
    setAdminStatus("Load an entry first or create a new one.", "error");
    return;
  }

  try {
    const framework = formToFramework();

    await fetchJSON(`/api/admin/frameworks/${frameworkId}`, {
      method: "PUT",
      body: JSON.stringify({ framework }),
    });

    await loadFrameworkList();
    setAdminStatus("Framework updated. Engine reloaded automatically.", "success");
  } catch (e) {
    setAdminStatus(e.message, "error");
  }
}

async function createNewFramework() {
  try {
    const framework = formToFramework();

    const res = await fetchJSON("/api/admin/frameworks", {
      method: "POST",
      body: JSON.stringify({ framework }),
    });

    document.getElementById("adminFrameworkId").value = res.framework.id;
    document.getElementById("framework_id").value = res.framework.id;

    await loadFrameworkList();
    setAdminStatus("New framework created. Engine reloaded automatically.", "success");
  } catch (e) {
    setAdminStatus(e.message, "error");
  }
}

async function deleteCurrentFramework() {
  const frameworkId = document.getElementById("adminFrameworkId").value.trim();
  if (!frameworkId) {
    setAdminStatus("No framework loaded.", "error");
    return;
  }

  try {
    await fetchJSON(`/api/admin/frameworks/${frameworkId}`, {
      method: "DELETE",
    });

    clearAdminForm();
    await loadFrameworkList();
    setAdminStatus("Framework deleted. Engine reloaded automatically.", "success");
  } catch (e) {
    setAdminStatus(e.message, "error");
  }
}

async function initAdmin() {
  try {
    await loadAdminConfig();
    await loadFrameworkList();

    document.getElementById("applyAdminFiltersBtn")?.addEventListener("click", loadFrameworkList);
    document.getElementById("saveFrameworkBtn")?.addEventListener("click", saveFrameworkChanges);
    document.getElementById("createFrameworkBtn")?.addEventListener("click", createNewFramework);
    document.getElementById("deleteFrameworkBtn")?.addEventListener("click", deleteCurrentFramework);
    document.getElementById("newFrameworkBtn")?.addEventListener("click", () => {
      clearAdminForm();
      setAdminStatus("Ready to create a new framework entry.", "success");
    });

    setAdminStatus("Curriculum admin ready.", "success");
  } catch (e) {
    console.error(e);
    setAdminStatus(`Admin failed to load: ${e.message}`, "error");
  }
}

document.addEventListener("DOMContentLoaded", initAdmin);