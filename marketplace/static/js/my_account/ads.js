window.addEventListener("load", () => {
  const countEl = document.getElementById("adsCount");
  if (!countEl) return;

  const rows = document.querySelectorAll(".ad-row");
  countEl.textContent = rows.length;
});
