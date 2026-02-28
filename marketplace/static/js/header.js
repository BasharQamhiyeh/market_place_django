/* =========================================================
   header.js (GLOBAL)
   - Runs on every page (loaded from base.html)
   - Contains: login modal + password toggle + navbar dropdowns + referral link
   - Keeps your existing Buy/Sell logic and toggleFavorite exactly as-is
   - Uses `.show` (same as your CSS + old main.js)
========================================================= */

function getCSRFToken() {
  return (
    document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1] || ""
  );
}

// ===================== LOGIN SCRIPT =====================
const loginBtn    = document.getElementById("loginBtn");
const authButtons = document.getElementById("authButtons");
const userIcons   = document.getElementById("userIcons");
const loginModal  = document.getElementById("loginModal");
const closeLoginX = document.getElementById("closeLoginX");
const loginForm   = document.getElementById("loginForm");

const loginPhone = document.getElementById("loginPhone");
const loginPassword = document.getElementById("loginPassword");
const toggleLoginPassword = document.getElementById("toggleLoginPassword");


// ===== Password Icons =====
const LOGIN_EYE_OPEN_ICON = `
<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5"
     fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
  <path stroke-linecap="round" stroke-linejoin="round"
    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  <path stroke-linecap="round" stroke-linejoin="round"
    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7
       -1.274 4.057-5.065 7-9.542 7
       -4.477 0-8.268-2.943-9.542-7z" />
</svg>
`;

const LOGIN_EYE_CLOSED_ICON = `
<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5"
     fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
  <path stroke-linecap="round" stroke-linejoin="round" d="M3 3l18 18" />
  <path stroke-linecap="round" stroke-linejoin="round"
        d="M10.584 10.587A3 3 0 0113.413 13.41" />
  <path stroke-linecap="round" stroke-linejoin="round"
        d="M6.697 6.7C4.98 8.018 3.74 10.012 3 12
           c1.274 4.057 5.065 7 9.542 7
           1.53 0 2.984-.288 4.293-.812" />
  <path stroke-linecap="round" stroke-linejoin="round"
        d="M17.31 17.31C19.022 15.989 20.262 13.994 21 12
           c-.993-3.164-3.49-5.675-6.57-6.62" />
</svg>
`;


// فتح نافذة تسجيل الدخول
if (loginBtn && loginModal) {
  loginBtn.addEventListener("click", () => {
    loginModal.classList.remove("hidden");
  });
}

// إغلاق النافذة
if (closeLoginX && loginModal) {
  closeLoginX.addEventListener("click", () => {
    loginModal.classList.add("hidden");
  });
}


// ===== Phone: digits only + max 10 =====
if (loginPhone) {
  const sanitizePhone = () => {
    loginPhone.value = (loginPhone.value || "").replace(/\D+/g, "").slice(0, 10);
  };

  loginPhone.addEventListener("input", sanitizePhone);

  // handle paste too
  loginPhone.addEventListener("paste", () => {
    setTimeout(sanitizePhone, 0);
  });
}

// ===== Toggle password show/hide =====
if (loginPassword && toggleLoginPassword) {
  // default state: password hidden → show "eye"
  toggleLoginPassword.innerHTML = LOGIN_EYE_OPEN_ICON;

  toggleLoginPassword.addEventListener("click", () => {
    const isHidden = loginPassword.type === "password";

    loginPassword.type = isHidden ? "text" : "password";
    toggleLoginPassword.innerHTML = isHidden
      ? LOGIN_EYE_CLOSED_ICON
      : LOGIN_EYE_OPEN_ICON;

    toggleLoginPassword.setAttribute(
      "aria-label",
      isHidden ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"
    );
  });
}


/* =========================================================
   NAVBAR DROPDOWNS (moved from main.js -> header.js)
   - Uses `.show` (same as your old main.js)
   - Safe: won't break if elements are missing
   - Keeps your "mark notifications read" behavior
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
          body: JSON.stringify({})
        }).catch(() => {});
      }
    }
  });
});

document.addEventListener("click", () => closeAll(null));
document.addEventListener("keydown", e => { if (e.key === "Escape") closeAll(null); });


/* =========================================================
   Referral link handling (moved from main.js -> header.js)
========================================================= */
document.addEventListener("DOMContentLoaded", function () {
  const inviteLinkEl = document.getElementById("inviteFriendsLink");
  if (!inviteLinkEl) return;

  const referralCode = inviteLinkEl.dataset.referralCode || "";
  if (!referralCode) return;

  inviteLinkEl.addEventListener("click", function (e) {
    e.preventDefault();

    const registerUrl = inviteLinkEl.dataset.registerUrl || "/register/";
    const u = new URL(registerUrl, window.location.origin);
    u.searchParams.set("ref", referralCode);
    const fullLink = u.toString();

    function showInviteToast(msg) {
      const toast = document.createElement("div");
      toast.textContent = msg;
      toast.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#ff7a18;color:#fff;padding:10px 22px;border-radius:10px;font-weight:bold;z-index:99999;box-shadow:0 4px 16px rgba(0,0,0,.18);transition:opacity .3s";
      document.body.appendChild(toast);
      setTimeout(() => { toast.style.opacity = "0"; setTimeout(() => toast.remove(), 300); }, 2200);
    }

    if (navigator.clipboard?.writeText) {
      navigator.clipboard
        .writeText(fullLink)
        .then(() => showInviteToast("✔ تم نسخ رابط الدعوة"))
        .catch(() => showInviteToast("رابط الدعوة: " + fullLink));
    } else {
      const t = document.createElement("textarea");
      t.value = fullLink;
      t.style.cssText = "position:fixed;left:-9999px";
      document.body.appendChild(t);
      t.select();
      document.execCommand("copy");
      t.remove();
      showInviteToast("✔ تم نسخ رابط الدعوة");
    }
  });
});


/* =========================================================
   ✅ Store account: block creating requests from GLOBAL "Add" button
========================================================= */
(function () {
  function isStoreAccountGlobal() {
    return document.documentElement?.dataset?.isStore === "1";
  }

  function openStoreNoRequestsModalGlobal() {
    const m = document.getElementById("storeNoRequestsModalGlobal");
    if (!m) return alert("هذا الحساب حساب متجر ولا يمكن إضافة طلبات.");
    m.classList.remove("hidden");
    m.classList.add("flex");
    document.body.classList.add("overflow-hidden");
  }

  function closeStoreNoRequestsModalGlobal() {
    const m = document.getElementById("storeNoRequestsModalGlobal");
    if (!m) return;
    m.classList.add("hidden");
    m.classList.remove("flex");
    document.body.classList.remove("overflow-hidden");
  }

  function isCreateRequestUrl(url) {
    if (!url) return false;
    const u = String(url);
    return u.includes("/request/create/") || u.includes("/requests/create/") || u.includes("create_request");
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!isStoreAccountGlobal()) return;

    const addAdBtn = document.getElementById("addAdBtn");
    if (!addAdBtn) return;

    // Close wiring
    document.getElementById("closeStoreNoRequestsModalGlobalBtn")?.addEventListener("click", (e) => {
      e.preventDefault();
      closeStoreNoRequestsModalGlobal();
    });
    document.getElementById("closeStoreNoRequestsModalGlobalX")?.addEventListener("click", (e) => {
      e.preventDefault();
      closeStoreNoRequestsModalGlobal();
    });
    document.getElementById("storeNoRequestsModalGlobal")?.addEventListener("click", (e) => {
      const modal = document.getElementById("storeNoRequestsModalGlobal");
      if (e.target === modal) closeStoreNoRequestsModalGlobal();
      if (e.target?.classList?.contains("bg-black/40")) closeStoreNoRequestsModalGlobal();
    });

    // Block only when in request-create mode
    addAdBtn.addEventListener(
      "click",
      function (e) {
        const targetUrl =
          addAdBtn.dataset.targetUrl ||
          addAdBtn.getAttribute("data-target-url") ||
          addAdBtn.getAttribute("href") ||
          "";

        if (isCreateRequestUrl(targetUrl)) {
          e.preventDefault();
          e.stopPropagation();
          openStoreNoRequestsModalGlobal();
        }
      },
      true
    );
  });
})();


/* =========================================================
   Buy / Sell toggle (kept exactly, already in header.js)
========================================================= */
document.addEventListener('DOMContentLoaded', () => {
  const sellBtn     = document.getElementById('sellBtn');
  const buyBtn      = document.getElementById('buyBtn');
  const searchInput = document.getElementById('searchInput');
  const searchBtn   = document.getElementById('searchBtn');
  const addAdBtn    = document.getElementById('addAdBtn');
  const intentBox   = document.getElementById('intentBox');
  const modeInput   = document.getElementById('searchMode');
  const form        = document.getElementById('siteSearch');

  if (!sellBtn || !buyBtn || !searchInput || !searchBtn || !addAdBtn || !intentBox) {
    return;
  }

  let isBuy = false;  // default = إعلان

  function refreshSearchUI() {
    const color   = isBuy ? '#16a34a' : 'var(--rukn-orange)';
    const btnText = isBuy ? 'أضف طلبك' : 'أضف إعلانك';

    // placeholder
    searchInput.placeholder = isBuy ? 'ابحث عن طلب' : 'ابحث عن إعلان';

    // hidden mode
    if (modeInput) modeInput.value = isBuy ? 'buy' : 'sell';

    // button colors
    sellBtn.style.backgroundColor = isBuy ? '#fff' : 'var(--rukn-orange)';
    sellBtn.style.color           = isBuy ? '#6b7280' : '#fff';

    buyBtn.style.backgroundColor  = isBuy ? '#16a34a' : '#fff';
    buyBtn.style.color            = isBuy ? '#fff' : '#6b7280';

    intentBox.style.borderColor   = color;

    // add button
    addAdBtn.textContent           = btnText;
    addAdBtn.style.backgroundColor = color;
    const url = isBuy ? '/request/create/' : '/item/create/';
    addAdBtn.dataset.targetUrl = url;
    addAdBtn.setAttribute("href", url);

    // search field and btn color
    searchInput.style.borderColor   = color;
    searchBtn.style.backgroundColor = color;

    const hasText = searchInput.value.trim() !== '';
    searchBtn.disabled = !hasText;
    searchBtn.style.opacity = hasText ? '1' : '0.5';

    // change search form URL
    if (form) {
      form.action = isBuy ? '/ar/requests/' : '/ar/items/';
    }
  }

  sellBtn.addEventListener('click', () => {
    isBuy = false;
    refreshSearchUI();
  });

  buyBtn.addEventListener('click', () => {
    isBuy = true;
    refreshSearchUI();
  });

  searchInput.addEventListener('input', refreshSearchUI);

  // ================ SEARCH SPINNER (WORKS 100%) =================
  if (searchBtn) {
    searchBtn.addEventListener("click", function () {
      searchBtn.innerHTML =
        '<svg class="animate-spin w-4 h-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">' +
          '<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>' +
          '<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4zm2 5.29A7.96 7.96 0 014 12H0c0 3.04 1.13 5.82 3 7.94l3-2.65z"></path>' +
        '</svg>';
    });
  }

  // initial setup
  refreshSearchUI();
});


/* =========================================================
   toggleFavorite (global, kept exactly)
========================================================= */
function toggleFavorite(e, itemId, formElement) {
  e.preventDefault(); // Stop page refresh

  const csrfToken = formElement.querySelector("[name=csrfmiddlewaretoken]").value;

  fetch(`/${document.documentElement.lang}/favorites/toggle/${itemId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken,
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then(response => response.json())
    .then(data => {
      // Update heart icon
      formElement.querySelector("button").textContent =
        data.is_favorited ? "❤️" : "🤍";

      // Update navbar favorite counter
      const counter = document.querySelector("#favBtn .badge");

      if (counter) {
        // If no favorites left — remove badge
        if (data.favorite_count === 0) {
          counter.remove();
        } else {
          counter.textContent = data.favorite_count;
        }
      } else {
        // If badge does not exist (first favorite) — create one
        if (data.favorite_count > 0) {
          const badge = document.createElement("span");
          badge.className = "badge";
          badge.textContent = data.favorite_count;
          document.querySelector("#favBtn").appendChild(badge);
        }
      }
    })
    .catch(err => console.error(err));
}


/* =========================================================
   Add Ad button: guests only (kept, but safer)
   - Only binds if loginModal exists (guest)
========================================================= */
document.addEventListener("DOMContentLoaded", function () {
  const addAdBtn = document.getElementById("addAdBtn");
  const loginModal = document.getElementById("loginModal");
  const loginNext = document.getElementById("loginNext");

  // If any element is missing, do nothing
  if (!addAdBtn || !loginModal) return;

  addAdBtn.addEventListener("click", function (e) {
    // user is NOT logged in → modal exists
    e.preventDefault(); // ⛔ stop page refresh

    // remember where user wanted to go
    const targetUrl = addAdBtn.dataset.targetUrl || addAdBtn.getAttribute("data-target-url");

    if (loginNext && targetUrl) {
      loginNext.value = targetUrl;
    }

    // show login modal
    loginModal.classList.remove("hidden");
  });
});
