function setPricingStatus(msg) {
  const el = document.getElementById("pricingStatus");
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

async function startPayPalPlaceholder() {
  setPricingStatus("Preparing PayPal upgrade placeholder...");

  try {
    const config = await fetchJSON("/api/paypal/config");
    const res = await fetchJSON("/api/paypal/create-subscription", {
      method: "POST",
    });

    if (!config.client_id_present || !config.plan_id_pro_present) {
      setPricingStatus("PayPal placeholder is ready, but live PayPal credentials are not configured yet.");
      return;
    }

    setPricingStatus(res.message || "PayPal placeholder response received.");
  } catch (e) {
    setPricingStatus(e.message);
  }
}

function initPricing() {
  document.getElementById("upgradeBtn")?.addEventListener("click", () => {
    changePlan("pro");
  });

  document.getElementById("downgradeBtn")?.addEventListener("click", () => {
    changePlan("free");
  });

  document.getElementById("paypalUpgradeBtn")?.addEventListener("click", () => {
    startPayPalPlaceholder();
  });
}

document.addEventListener("DOMContentLoaded", initPricing);