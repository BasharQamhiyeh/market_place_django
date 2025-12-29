/* =========================================================
   FEATURE FLAG (kept but unused — harmless)
========================================================= */
const ENABLE_ITEM_SUGGESTIONS = true;

function getCSRFToken() {
  return (
    document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1] || ""
  );
}

/* ✅ FIX: this was breaking the whole file (CSRF_TOKEN is not defined)
console.log(CSRF_TOKEN);
*/
console.log("✅ home.js loaded");

/* =========================================================
   NAVBAR DROPDOWNS
========================================================= */
window.menus = window.menus || {
  fav:  { btn: document.getElementById("favBtn"),  menu: document.getElementById("favMenu") },
  msg:  { btn: document.getElementById("msgBtn"),  menu: document.getElementById("msgMenu") },
  noti: { btn: document.getElementById("notiBtn"), menu: document.getElementById("notiMenu") },
  user: { btn: document.getElementById("userBtn"), menu: document.getElementById("userMenu") }
};

function closeAll(except) {
  Object.keys(menus).forEach(k => {
    const o = menus[k];
    if (!o.btn || !o.menu) return;
    if (k !== except) {
      o.menu.classList.remove("show");
      o.btn.setAttribute("aria-expanded", "false");
    }
  });
}

Object.keys(menus).forEach(key => {
  const o = menus[key];
  if (!o.btn || !o.menu) return;

  o.btn.addEventListener("click", e => {
    e.stopPropagation();
    const isOpen = o.menu.classList.contains("show");
    closeAll(key);

    if (!isOpen) {
      o.menu.classList.add("show");
      o.btn.setAttribute("aria-expanded", "true");

      // REMOVE BADGE VISUALLY + MARK AS READ
      if (key === "noti") {
        const badge = document.querySelector("#notiBtn .badge");
        if (badge) badge.remove();

        fetch(`/${document.documentElement.lang}/notifications/mark-read/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({}) // REQUIRED FOR CSRF
        }).catch(() => {});
      }
    }
  });
});

document.addEventListener("click", () => closeAll(null));
document.addEventListener("keydown", e => { if (e.key === "Escape") closeAll(null); });

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
   Referral link handling
========================================================= */
document.addEventListener("DOMContentLoaded", function () {
  const inviteLinkEl = document.getElementById("inviteFriendsLink");
  if (!inviteLinkEl) return;

  const referralCode = inviteLinkEl.dataset.referralCode || "";
  if (!referralCode) return;

  inviteLinkEl.addEventListener("click", function (e) {
    e.preventDefault();

    const registerUrl = inviteLinkEl.dataset.registerUrl || "/register/";
    const fullLink = window.location.origin + registerUrl + "?ref=" + referralCode;

    if (navigator.clipboard?.writeText) {
      navigator.clipboard
        .writeText(fullLink)
        .then(() => alert("✔️ تم نسخ رابط الدعوة:\n" + fullLink))
        .catch(() => alert("رابط الدعوة:\n" + fullLink));
    } else {
      alert("رابط الدعوة:\n" + fullLink);
    }
  });
});

/* =========================================================
   Favorites on Home (event delegation, won't break other parts)
   - expects buttons in latest items block:
     data-fav-btn="1"
     data-url="...toggle favorite url..."
     data-guest="1|0"
     data-favorited="1|0"   (optional)
========================================================= */

function openLoginModal() {
  const m = document.getElementById("loginModal");
  if (m) m.classList.remove("hidden");
}

function applyFavUI(btn, isFav) {
  if (!btn) return;

  btn.dataset.favorited = isFav ? "1" : "0";

  const heart = btn.querySelector(".fav-heart");
  if (heart) {
    heart.textContent = isFav ? "❤️" : "🤍";
  }
}


// ✅ Delegation: works even if latest items are re-rendered
document.addEventListener("click", async (e) => {
  const btn = e.target.closest('[data-fav-btn="1"]');
  if (!btn) return;

  e.preventDefault();
  e.stopPropagation();

  if (btn.dataset.guest === "1" || !btn.dataset.url) {
    openLoginModal();
    return;
  }

  const url = btn.dataset.url;
  const csrftoken = getCSRFToken();

  try {
    const res = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrftoken,
      },
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      if (res.status === 403) openLoginModal();
      return;
    }

    const isFav = !!data.is_favorited;
    btn.dataset.favorited = isFav ? "1" : "0";
    applyFavUI(btn, isFav);

    if (window.showRuknAlert) {
      window.showRuknAlert(isFav ? "✔ تمت الإضافة للمفضلة" : "✳️ تم الحذف من المفضلة");
    }
  } catch (err) {
    console.error("❌ fav failed:", err);
  }
});


document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-single-submit]").forEach((form) => {
    let locked = false;

    form.addEventListener("submit", () => {
      if (locked) return;           // extra safety
      locked = true;

      // disable all submit buttons in this form
      const buttons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
      buttons.forEach((btn) => {
        btn.disabled = true;
        btn.classList.add("opacity-60", "cursor-not-allowed");
        btn.setAttribute("aria-busy", "true");
      });

      // optional: update primary button text
      const primary = form.querySelector("[data-submit-btn]");
      if (primary) {
        primary.dataset.originalText = primary.textContent;
        primary.textContent = "جاري الإرسال...";
      }
    });
  });
});
