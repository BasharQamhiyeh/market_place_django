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

function gridCols(gridEl) {
  const cols = getComputedStyle(gridEl).gridTemplateColumns.split(" ").filter(Boolean).length;
  return Math.max(cols || 1, 1);
}

function disableBtn(btn, text) {
  btn.disabled = true;
  btn.classList.add("opacity-60", "cursor-not-allowed");
  btn.textContent = text;
}

async function loadMoreChunk({ btnId, gridId, url, noMoreText }) {
  const btn = document.getElementById(btnId);
  const grid = document.getElementById(gridId);
  if (!btn || !grid) return;

  let locked = false;

  btn.addEventListener("click", async () => {
    if (locked) return;
    locked = true;

    const cols = gridCols(grid);
    const limit = 3 * cols;              // ✅ 3 rows
    const offset = grid.children.length; // ✅ already rendered cards count

    btn.disabled = true;
    btn.classList.add("opacity-60");

    try {
      const res = await fetch(`${url}?offset=${offset}&limit=${limit}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" }
      });
      const data = await res.json();

      if (data.html && data.html.trim()) {
        grid.insertAdjacentHTML("beforeend", data.html);
      }

      if (!data.has_more) {
        disableBtn(btn, noMoreText);
        return;
      }

      btn.disabled = false;
      btn.classList.remove("opacity-60");
    } catch (e) {
      btn.disabled = false;
      btn.classList.remove("opacity-60");
    } finally {
      locked = false;
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadMoreChunk({
    btnId: "loadMoreAdsBtn",
    gridId: "latest-items-grid",
    url: "/home/more-items/",
    noMoreText: "لا يوجد المزيد من الإعلانات"
  });

  loadMoreChunk({
    btnId: "loadMoreRequestsBtn",
    gridId: "requestsGrid",
    url: "/home/more-requests/",
    noMoreText: "لا يوجد المزيد من الطلبات"
  });
});

/* =========================================================
   Open login modal if redirected with ?login=1
   - Open ONLY via existing trigger (so centering + close works)
   - Retry until header.js is ready
========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get("login") !== "1") return;

  const findLoginTrigger = () => {
    return (
      // 1) Preferred explicit triggers (your project may have one of these)
      document.querySelector('[data-open-login]') ||
      document.querySelector('[data-auth-open="login"]') ||
      document.querySelector('button[data-login]') ||
      document.getElementById("openLoginBtn") ||

      // 2) Common modal toggle patterns
      document.querySelector('[data-modal-target="login"]') ||
      document.querySelector('[data-target="login"]') ||
      document.querySelector('[data-bs-target="#loginModal"]') ||
      document.querySelector('a[href="#loginModal"]') ||
      document.querySelector('a[href="#login"]') ||

      // 3) Last resort: match by visible text
      Array.from(document.querySelectorAll("a,button")).find((el) => {
        const t = (el.textContent || "").trim();
        return t === "تسجيل الدخول" || t === "دخول" || t.toLowerCase() === "login";
      }) ||

      null
    );
  };

  let tries = 0;
  const maxTries = 30;   // ~3 seconds
  const intervalMs = 100;

  const timer = setInterval(() => {
    tries += 1;

    const trigger = findLoginTrigger();
    if (trigger) {
      clearInterval(timer);
      trigger.click();

      // optional: remove params so refresh doesn't reopen
      // history.replaceState({}, "", window.location.pathname);

      return;
    }

    if (tries >= maxTries) {
      clearInterval(timer);
      console.warn("Login trigger not found. Modal will not auto-open.");
    }
  }, intervalMs);
});
