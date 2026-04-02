function setAdminUserStatus(msg) {
  const el = document.getElementById("adminUserStatus");
  if (el) el.textContent = msg;
}

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
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

let cachedUsers = [];

function userToForm(user) {
  document.getElementById("adminUserId").value = user.id || "";
  document.getElementById("user_email").value = user.email || "";
  document.getElementById("user_role").value = user.role || "user";
  document.getElementById("user_plan").value = user.plan || "free";
  document.getElementById("user_subscription_status").value = user.subscription_status || "inactive";
  document.getElementById("user_payment_provider").value = user.payment_provider || "";
  document.getElementById("user_paypal_customer_id").value = user.paypal_customer_id || "";
  document.getElementById("user_paypal_subscription_id").value = user.paypal_subscription_id || "";
  document.getElementById("user_subscription_started_at").value = user.subscription_started_at || "";
  document.getElementById("user_subscription_renews_at").value = user.subscription_renews_at || "";
  document.getElementById("user_billing_notes").value = user.billing_notes || "";
  document.getElementById("user_created_at").value = user.created_at || "";
}

async function loadUsers() {
  const res = await fetchJSON("/api/admin/users");
  cachedUsers = res.users || [];
  const container = document.getElementById("adminUserList");
  container.innerHTML = "";

  if (!cachedUsers.length) {
    container.innerHTML = "<p class='muted'>No users found.</p>";
    return;
  }

  cachedUsers.forEach((user) => {
    const card = document.createElement("div");
    card.className = "saved-lesson-card";
    card.innerHTML = `
      <strong>${user.email}</strong>
      <small>Role: ${user.role} • Plan: ${user.plan} • Status: ${user.subscription_status || "inactive"}</small>
      <div class="lesson-buttons">
        <button type="button" class="load-user-btn secondary small-btn" data-id="${user.id}">Edit</button>
      </div>
      <hr>
    `;
    container.appendChild(card);
  });

  document.querySelectorAll(".load-user-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const userId = Number(btn.dataset.id);
      const user = cachedUsers.find((u) => u.id === userId);
      if (user) {
        userToForm(user);
        setAdminUserStatus("User loaded.");
      }
    });
  });
}

async function saveUserChanges() {
  const userId = document.getElementById("adminUserId").value;
  if (!userId) {
    setAdminUserStatus("Select a user first.");
    return;
  }

  const payload = {
    role: document.getElementById("user_role").value,
    plan: document.getElementById("user_plan").value,
    subscription_status: document.getElementById("user_subscription_status").value,
    payment_provider: document.getElementById("user_payment_provider").value.trim(),
    paypal_customer_id: document.getElementById("user_paypal_customer_id").value.trim(),
    paypal_subscription_id: document.getElementById("user_paypal_subscription_id").value.trim(),
    subscription_started_at: document.getElementById("user_subscription_started_at").value.trim(),
    subscription_renews_at: document.getElementById("user_subscription_renews_at").value.trim(),
    billing_notes: document.getElementById("user_billing_notes").value.trim(),
  };

  await fetchJSON(`/api/admin/users/${userId}/billing`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

  await loadUsers();
  setAdminUserStatus("User billing updated.");
}

async function initAdminUsers() {
  try {
    await loadUsers();
    document.getElementById("saveUserBtn")?.addEventListener("click", saveUserChanges);
    setAdminUserStatus("User management ready.");
  } catch (e) {
    console.error(e);
    setAdminUserStatus(`Failed to load users: ${e.message}`);
  }
}

document.addEventListener("DOMContentLoaded", initAdminUsers);