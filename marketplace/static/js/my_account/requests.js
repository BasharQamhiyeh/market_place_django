// static/js/my_account/requests.js
(() => {
  const tab = document.getElementById("tab-requests");
  const list = document.getElementById("requestsList");
  const count = document.getElementById("requestsCount");
  if (!tab || !list || !count) return;

  function ensureVisibleWhenActive() {
    if (!tab.classList.contains("active")) return;

    list.classList.remove("hidden");
    list.style.removeProperty("display");

    const rows = list.querySelectorAll(".req-card, .request-row");
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
})();
