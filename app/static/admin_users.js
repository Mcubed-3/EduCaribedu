function setAdminUserStatus(msg, kind = "neutral") {
  const el = document.getElementById("adminUserStatus");
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

let cachedUsers = [];

function userToForm(user) {
  document.getElementById("adminUserId").value = user.id || "";
  document.getElementById("user_email").value = user.email || "";
  document.getElementById("user_role").value = user.role || "user";
  document.getElementById("user_plan").value = user.plan || "free";
  document.getElementById("user_subscription_status").value = user.subscription_status || "inactive";
  document.getElementById("user_payment_provider").value = user.payment_provider || "";
  document.getElementById("user_stripe_customer_id").value = user.stripe_customer_id || "";
  document.getElementById("user_stripe_subscription_id").value = user.stripe_subscription_id || "";
  document.getElementById("user_subscription_started_at").value = user.subscription_started_at || "";
  document.getElementById("user_subscription_renews_at").value = user.subscription_renews_at || "";
  document.getElementById("user_billing_notes").value = user.billing_notes || "";
  document.getElementById("user_created_at").value = user.created_at || "";
}

function userCardHTML(user) {
  return `
    <div class="admin-entry-card">
      <div class="admin-entry-card-head">
        <div>
          <strong>${user.email}</strong>
          <small>Role: ${user.role} • Plan: ${user.plan} • Status: ${user.subscription_status || "inactive"}</small>
        </div>
        <button type="button" class="btn btn-secondary small-btn load-user-btn" data-id="${user.id}">Edit</button>
      </div>
      <div class="admin-entry-meta">
        <span>Provider: ${user.payment_provider || "manual"}</span>
        <span>Created: ${user.created_at || "—"}</span>
      </div>
    </div>
  `;
}

async function loadUsers() {
  const res = await fetchJSON("/api/admin/users");
  cachedUsers = res.users || [];

  const container = document.getElementById("adminUserList");
  if (!container) return;

  container.innerHTML = "";

  if (!cachedUsers.length) {
    container.innerHTML = "<p class='muted'>No users found.</p>";
    return;
  }

  cachedUsers.forEach((user) => {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = userCardHTML(user);
    container.appendChild(wrapper.firstElementChild);
  });

  document.querySelectorAll(".load-user-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const userId = Number(btn.dataset.id);
      const user = cachedUsers.find((u) => u.id === userId);
      if (user) {
        userToForm(user);
        setAdminUserStatus("User loaded.", "success");
      }
    });
  });
}

async function saveUserChanges() {
  const userId = document.getElementById("adminUserId").value;
  if (!userId) {
    setAdminUserStatus("Select a user first.", "error");
    return;
  }

  const payload = {
    role: document.getElementById("user_role").value,
    plan: document.getElementById("user_plan").value,
    subscription_status: document.getElementById("user_subscription_status").value,
    payment_provider: document.getElementById("user_payment_provider").value.trim(),
    stripe_customer_id: document.getElementById("user_stripe_customer_id").value.trim(),
    stripe_subscription_id: document.getElementById("user_stripe_subscription_id").value.trim(),
    subscription_started_at: document.getElementById("user_subscription_started_at").value.trim(),
    subscription_renews_at: document.getElementById("user_subscription_renews_at").value.trim(),
    billing_notes: document.getElementById("user_billing_notes").value.trim(),
  };

  try {
    await fetchJSON(`/api/admin/users/${userId}/billing`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });

    await loadUsers();
    setAdminUserStatus("User billing updated.", "success");
  } catch (e) {
    setAdminUserStatus(e.message, "error");
  }
}

async function initAdminUsers() {
  try {
    await loadUsers();
    document.getElementById("saveUserBtn")?.addEventListener("click", saveUserChanges);
    setAdminUserStatus("User management ready.", "success");
  } catch (e) {
    console.error(e);
    setAdminUserStatus(`Failed to load users: ${e.message}`, "error");
  }
}

document.addEventListener("DOMContentLoaded", initAdminUsers);