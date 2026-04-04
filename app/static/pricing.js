function setPricingStatus(msg) {
  const el = document.getElementById("pricingStatus");
  if (el) el.textContent = msg;
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
  return res.status === 204 ? {} : await res.json();
}

async function changePlan(plan) {
  setPricingStatus("Updating plan...");
  try {
    await fetchJSON("/api/plan/update", {
      method: "POST",
      body: JSON.stringify({ plan }),
    });
    setPricingStatus("Plan updated successfully.");
    window.location.reload();
  } catch (e) {
    setPricingStatus(e.message);
  }
}

async function startStripeCheckout(targetPlan) {
  setPricingStatus(`Redirecting to Stripe for ${targetPlan}...`);
  try {
    const data = await fetchJSON("/api/stripe/create-checkout-session", {
      method: "POST",
      body: JSON.stringify({ target_plan: targetPlan }),
    });
    if (!data.url) throw new Error("Stripe checkout URL was not returned.");
    window.location.href = data.url;
  } catch (e) {
    setPricingStatus(e.message);
  }
}

async function openBillingPortal() {
  setPricingStatus("Opening billing portal...");
  try {
    const data = await fetchJSON("/api/stripe/create-portal-session", { method: "POST" });
    if (!data.url) throw new Error("Billing portal URL was not returned.");
    window.location.href = data.url;
  } catch (e) {
    setPricingStatus(e.message);
  }
}

function showCheckoutStateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const checkout = params.get("checkout");
  const plan = params.get("plan");
  if (checkout === "success") {
    setPricingStatus(`Payment completed for ${plan || "your new plan"}. Your account will update in a few moments.`);
  } else if (checkout === "cancelled") {
    setPricingStatus("Checkout was cancelled.");
  }
}

function initPricing() {
  showCheckoutStateFromUrl();
  document.getElementById("downgradeBtn")?.addEventListener("click", () => changePlan("free"));
  document.querySelectorAll(".checkout-btn").forEach((btn) => {
    btn.addEventListener("click", () => startStripeCheckout(btn.dataset.plan || "pro"));
  });
  document.getElementById("manageBillingBtn")?.addEventListener("click", openBillingPortal);
}

document.addEventListener("DOMContentLoaded", initPricing);
