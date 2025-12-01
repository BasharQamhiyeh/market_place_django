/* =========================================================
   FEATURE FLAG (kept but unused — harmless)
========================================================= */
const ENABLE_ITEM_SUGGESTIONS = true;

/* =========================================================
   NAVBAR DROPDOWNS
========================================================= */
const menus ??= {
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
    }
  });
});

document.addEventListener("click", () => closeAll(null));
document.addEventListener("keydown", e => { if (e.key === "Escape") closeAll(null); });

/* =========================================================
   Categories scroll buttons
========================================================= */
function updateScrollButtons() {
  const container = document.getElementById('catsScroll');
  const leftBtn   = document.querySelector('.scroll-btn.left');
  const rightBtn  = document.querySelector('.scroll-btn.right');
  if (!container || !leftBtn || !rightBtn) return;

  leftBtn.style.opacity  = container.scrollLeft > 0 ? "1" : "0.5";
  rightBtn.style.opacity =
    container.scrollLeft < (container.scrollWidth - container.clientWidth)
      ? "1" : "0.5";
}

document.getElementById('catsScroll')?.addEventListener('scroll', updateScrollButtons);
window.addEventListener('load', updateScrollButtons);

function scrollCats(dir) {
  const c = document.getElementById('catsScroll');
  if (!c) return;
  c.scrollBy({ left: dir * 220, behavior: 'smooth' });
  setTimeout(updateScrollButtons, 300);
}

window.scrollCats = scrollCats;

/* =========================================================
   Referral link handling
========================================================= */
document.addEventListener("DOMContentLoaded", function() {
  const inviteLinkEl = document.getElementById("inviteFriendsLink");
  if (!inviteLinkEl) return;

  const referralCode = inviteLinkEl.dataset.referralCode || "";
  if (!referralCode) return;

  inviteLinkEl.addEventListener("click", function(e) {
    e.preventDefault();

    const registerUrl = inviteLinkEl.dataset.registerUrl || "/register/";
    const fullLink = window.location.origin + registerUrl + "?ref=" + referralCode;

    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(fullLink)
        .then(() => alert("✔️ تم نسخ رابط الدعوة:\n" + fullLink))
        .catch(() => alert("رابط الدعوة:\n" + fullLink));
    } else {
      alert("رابط الدعوة:\n" + fullLink);
    }
  });
});

