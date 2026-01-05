/* =========================================================
   main.js (HOME ONLY)
   - Keep home-only logic here
   - Removed: navbar dropdowns + referral handling (moved to header.js)
========================================================= */

/* =========================================================
   FEATURE FLAG (kept but unused — harmless)
========================================================= */
const ENABLE_ITEM_SUGGESTIONS = true;

console.log("✅ home.js loaded");

/* =========================================================
   Categories scroll buttons
========================================================= */
function updateScrollButtons() {
  const container = document.getElementById("catsScroll");
  const leftBtn = document.querySelector(".scroll-btn.left");
  const rightBtn = document.querySelector(".scroll-btn.right");
  if (!container || !leftBtn || !rightBtn) return;

  leftBtn.style.opacity = container.scrollLeft > 0 ? "1" : "0.5";
  rightBtn.style.opacity =
    container.scrollLeft < (container.scrollWidth - container.clientWidth)
      ? "1"
      : "0.5";
}

document.getElementById("catsScroll")?.addEventListener("scroll", updateScrollButtons);
window.addEventListener("load", updateScrollButtons);

function scrollCats(dir) {
  const c = document.getElementById("catsScroll");
  if (!c) return;
  c.scrollBy({ left: dir * 220, behavior: "smooth" });
  setTimeout(updateScrollButtons, 300);
}

window.scrollCats = scrollCats;

/* =========================================================
   Single-submit protection (safe on all pages but ok to keep here
   since you currently load main.js only on home)
========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-single-submit]").forEach((form) => {
    let locked = false;

    form.addEventListener("submit", () => {
      if (locked) return;
      locked = true;

      const buttons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
      buttons.forEach((btn) => {
        btn.disabled = true;
        btn.classList.add("opacity-60", "cursor-not-allowed");
        btn.setAttribute("aria-busy", "true");
      });

      const primary = form.querySelector("[data-submit-btn]");
      if (primary) {
        primary.dataset.originalText = primary.textContent;
        primary.textContent = "جاري الإرسال...";
      }
    });
  });
});
