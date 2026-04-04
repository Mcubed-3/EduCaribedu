function setFeedbackStatus(msg, kind = "neutral") {
  const el = document.getElementById("feedbackStatus");
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

function feedbackCardHTML(item, adminView = false) {
  return `
    <div class="feedback-entry-card">
      <div class="feedback-entry-head">
        <div>
          <strong>${item.subject}</strong>
          <small>${item.category}${item.page ? ` • ${item.page}` : ""}</small>
        </div>
        <span class="feedback-status-pill">${item.status}</span>
      </div>
      ${adminView ? `<div class="feedback-entry-meta">${item.email} • ${item.role}</div>` : ""}
      <p>${item.message}</p>
      <div class="feedback-entry-time">${item.created_at}</div>
    </div>
  `;
}

async function loadFeedbackList() {
  const container = document.getElementById("feedbackList");
  if (!container) return;

  container.innerHTML = "<p class='muted'>Loading feedback...</p>";

  try {
    const data = await fetchJSON("/api/feedback");
    const entries = data.items || [];
    const adminView = !!data.admin_view;

    if (!entries.length) {
      container.innerHTML = "<p class='muted'>No submissions yet.</p>";
      return;
    }

    container.innerHTML = entries
      .map((item) => feedbackCardHTML(item, adminView))
      .join("");
  } catch (e) {
    container.innerHTML = `<p class="muted">${e.message}</p>`;
  }
}

async function submitFeedback(event) {
  event.preventDefault();

  const category = document.getElementById("feedback_category")?.value || "";
  const subject = document.getElementById("feedback_subject")?.value || "";
  const page = document.getElementById("feedback_page")?.value || "";
  const message = document.getElementById("feedback_message")?.value || "";

  if (!category || !subject.trim() || !message.trim()) {
    setFeedbackStatus("Please complete category, subject, and message.", "error");
    return;
  }

  setFeedbackStatus("Sending message...");

  try {
    await fetchJSON("/api/feedback", {
      method: "POST",
      body: JSON.stringify({
        category,
        subject,
        page,
        message,
      }),
    });

    document.getElementById("feedbackForm")?.reset();
    setFeedbackStatus("Your message was sent successfully.", "success");
    await loadFeedbackList();
  } catch (e) {
    setFeedbackStatus(e.message, "error");
  }
}

function initFeedback() {
  document.getElementById("feedbackForm")?.addEventListener("submit", submitFeedback);
  loadFeedbackList();
  setFeedbackStatus("Ready.");
}

document.addEventListener("DOMContentLoaded", initFeedback);