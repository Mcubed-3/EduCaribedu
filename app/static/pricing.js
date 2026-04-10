function setPricingStatus(msg, kind = "neutral") {
  const el = document.getElementById("pricingStatus");
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

  return res.status === 204 ? {} : await res.json();
}

async function changePlan(plan) {
  setPricingStatus(`Updating plan to ${plan}...`);

  try {
    await fetchJSON("/api/plan/update", {
      method: "POST",
      body: JSON.stringify({ plan }),
    });

    setPricingStatus("Plan updated successfully.", "success");
    window.location.reload();
  } catch (e) {
    setPricingStatus(e.message || "Failed to update plan.", "error");
  }
}

async function startStripeCheckout(targetPlan) {
  if (userIsGuest()) {
    window.location.href = `/signup?next=/pricing&plan=${encodeURIComponent(targetPlan)}`;
    return;
  }

  setPricingStatus(`Redirecting to Stripe for ${targetPlan}...`);

  if (typeof gtag === "function") {
    gtag("event", "begin_checkout", {
      event_category: "conversion",
      event_label: targetPlan,
    });
  }

  try {
    const data = await fetchJSON("/api/stripe/create-checkout-session", {
      method: "POST",
      body: JSON.stringify({ target_plan: targetPlan }),
    });

    if (!data.url) {
      throw new Error("Stripe checkout URL was not returned.");
    }

    window.location.href = data.url;
  } catch (e) {
    setPricingStatus(e.message || "Failed to start checkout.", "error");
  }
}

async function openBillingPortal() {
  setPricingStatus("Opening billing portal...");

  try {
    const data = await fetchJSON("/api/stripe/create-portal-session", {
      method: "POST",
    });

    if (!data.url) {
      throw new Error("Billing portal URL was not returned.");
    }

    window.location.href = data.url;
  } catch (e) {
    setPricingStatus(e.message || "Failed to open billing portal.", "error");
  }
}

function showCheckoutStateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const checkout = params.get("checkout");
  const plan = params.get("plan");

  if (checkout === "success") {
    const planName =
      plan === "plus"
        ? "Pro Teacher Plus"
        : plan === "pro"
        ? "Pro Teacher"
        : "your new plan";

    if (typeof gtag === "function") {
      gtag("event", "purchase", {
        event_category: "conversion",
        event_label: plan || "unknown",
        value: plan === "plus" ? 15 : 10,
        currency: "USD",
      });
    }

    setPricingStatus(
      `Payment completed for ${planName}. Your account will update in a few moments.`,
      "success"
    );
  } else if (checkout === "cancelled") {
    setPricingStatus("Checkout was cancelled.", "error");
  }
}

function bindCheckoutButtons() {
  const proBtn = document.getElementById("stripeUpgradeBtn");
  if (proBtn) {
    proBtn.addEventListener("click", () => {
      const targetPlan = proBtn.dataset.plan || "pro";
      startStripeCheckout(targetPlan);
    });
  }

  const plusBtn = document.getElementById("stripePlusUpgradeBtn");
  if (plusBtn) {
    plusBtn.addEventListener("click", () => {
      const targetPlan = plusBtn.dataset.plan || "plus";
      startStripeCheckout(targetPlan);
    });
  }

  document.querySelectorAll(".checkout-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      startStripeCheckout(btn.dataset.plan || "pro");
    });
  });
}

function bindPlanChangeButtons() {
  const downgradeBtn = document.getElementById("downgradeBtn");
  if (downgradeBtn) {
    downgradeBtn.addEventListener("click", () => changePlan("free"));
  }

  const downgradeToProBtn = document.getElementById("downgradeToProBtn");
  if (downgradeToProBtn) {
    downgradeToProBtn.addEventListener("click", () => changePlan("pro"));
  }
}

function bindBillingPortalButton() {
  const manageBillingBtn = document.getElementById("manageBillingBtn");
  if (manageBillingBtn) {
    manageBillingBtn.addEventListener("click", openBillingPortal);
  }
}

function initPricing() {
  showCheckoutStateFromUrl();
  bindCheckoutButtons();
  bindPlanChangeButtons();
  bindBillingPortalButton();
}
function pricingMeta() {
  const el = document.getElementById("pricingPageMeta");
  return {
    role: el?.dataset.role || "",
    plan: el?.dataset.plan || "",
  };
}

function userIsGuest() {
  return pricingMeta().role === "guest";
}

document.addEventListener("DOMContentLoaded", initPricing);