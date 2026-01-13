// static/js/my_account/ads.js
(() => {
  const tab = document.getElementById("tab-ads");
  const list = document.getElementById("adsList");
  const count = document.getElementById("adsCount");
  if (!tab || !list || !count) return;

  function ensureVisibleWhenActive() {
    if (!tab.classList.contains("active")) return;

    // Only remove accidental hiding; don't force layout
    list.classList.remove("hidden");
    list.style.removeProperty("display");

    const rows = list.querySelectorAll(".ad-row, .ad-card");
    rows.forEach((r) => {
      r.classList.remove("hidden");
      r.style.removeProperty("display");
      r.style.removeProperty("visibility");
      r.style.removeProperty("opacity");
      r.style.removeProperty("transform");
    });

    count.textContent = String(rows.length);
  }

  const mo = new MutationObserver(ensureVisibleWhenActive);
  mo.observe(tab, { attributes: true, attributeFilter: ["class"] });

  document.addEventListener("DOMContentLoaded", ensureVisibleWhenActive);

  list.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;

    const id = Number(btn.getAttribute("data-id"));
    const action = btn.getAttribute("data-action");

    if (action === "delete") window.myAccountDeleteAd?.(id);
    else if (action === "republish") window.myAccountRepublishAd?.(id);
    else if (action === "highlight") window.openHighlightModal?.("ad", id);
  });
})();
