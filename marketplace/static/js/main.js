/* =========================================================
   main.js (HOME ONLY)
========================================================= */

console.log("✅ main.js loaded");

/* =========================================================
   Billboard Swiper Initialization (MOCKUP)
========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  const billboard = document.querySelector(".billboardSwiper");
  if (billboard) {
    new Swiper(".billboardSwiper", {
      slidesPerView: 1,
      loop: true,
      autoplay: {
        delay: 2000,
        pauseOnMouseEnter: true,
        disableOnInteraction: false,
      },
      pagination: {
        el: ".swiper-pagination",
        clickable: true,
      },
      navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
      },
      speed: 900,
    });
  }
});

/* =========================================================
   Horizontal Scroll (Stores / Trending) - keep your behavior
========================================================= */
function scrollRow(rowId, direction, scrollAmount) {
  const container = document.getElementById(rowId);
  if (!container) return;

  container.scrollBy({
    left: direction * scrollAmount,
    behavior: "smooth",
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const storesLeft = document.getElementById("storesLeft");
  const storesRight = document.getElementById("storesRight");

  if (storesLeft) storesLeft.addEventListener("click", () => scrollRow("storesRow", -1, 360));
  if (storesRight) storesRight.addEventListener("click", () => scrollRow("storesRow", 1, 360));

  const trendingLeft = document.getElementById("trendingLeft");
  const trendingRight = document.getElementById("trendingRight");

  if (trendingLeft) trendingLeft.addEventListener("click", () => scrollRow("trendingRow", -1, 340));
  if (trendingRight) trendingRight.addEventListener("click", () => scrollRow("trendingRow", 1, 340));

  addDragScroll("storesRow");
  addDragScroll("trendingRow");
});

/* =========================================================
   Drag to Scroll (match mockup class naming)
========================================================= */
function addDragScroll(elementId) {
  const row = document.getElementById(elementId);
  if (!row) return;

  let isDown = false;
  let startX = 0;
  let scrollLeft = 0;

  row.addEventListener("mousedown", (e) => {
    isDown = true;
    row.classList.add("cursor-grabbing");
    startX = e.pageX - row.offsetLeft;
    scrollLeft = row.scrollLeft;
  });

  row.addEventListener("mouseleave", () => {
    isDown = false;
    row.classList.remove("cursor-grabbing");
  });

  row.addEventListener("mouseup", () => {
    isDown = false;
    row.classList.remove("cursor-grabbing");
  });

  row.addEventListener("mousemove", (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - row.offsetLeft;
    const walk = (x - startX) * 1.6;
    row.scrollLeft = scrollLeft - walk;
  });
}

/* =========================================================
   Single-submit protection
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

/* =========================================================
   Load More Functionality (KEEP AS-IS)
========================================================= */
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
    const limit = 3 * cols;
    const offset = grid.children.length;

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
      console.error("Load more error:", e);
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
   Open login modal if redirected with ?login=1 (KEEP)
========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get("login") !== "1") return;

  const findLoginTrigger = () => {
    return (
      document.querySelector('[data-open-login]') ||
      document.querySelector('[data-auth-open="login"]') ||
      document.querySelector("button[data-login]") ||
      document.getElementById("openLoginBtn") ||
      document.querySelector('[data-modal-target="login"]') ||
      document.querySelector('[data-target="login"]') ||
      document.querySelector('[data-bs-target="#loginModal"]') ||
      document.querySelector('a[href="#loginModal"]') ||
      document.querySelector('a[href="#login"]') ||
      Array.from(document.querySelectorAll("a,button")).find((el) => {
        const t = (el.textContent || "").trim();
        return t === "تسجيل الدخول" || t === "دخول" || t.toLowerCase() === "login";
      }) ||
      null
    );
  };

  let tries = 0;
  const maxTries = 30;
  const intervalMs = 100;

  const timer = setInterval(() => {
    tries += 1;

    const trigger = findLoginTrigger();
    if (trigger) {
      clearInterval(timer);
      trigger.click();
      return;
    }

    if (tries >= maxTries) {
      clearInterval(timer);
      console.warn("Login trigger not found. Modal will not auto-open.");
    }
  }, intervalMs);
});
