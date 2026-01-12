/* user-profile.js (mirror store behaviors)
   ✅ Same toast
   ✅ Same filters logic
   ✅ Same phone reveal logic
   ✅ Same share logic (two buttons)
   ✅ Same message logic (AJAX, no redirect)
*/

(() => {
  const ROOT = document.documentElement;
  if (ROOT.dataset.userProfileInit === "1") return;
  ROOT.dataset.userProfileInit = "1";
})();

/* ========= Toast (same as store) ========= */
function showToast(message) {
  const box = document.getElementById("toastBox");
  if (!box) return;
  box.textContent = message;
  box.classList.remove("opacity-0", "scale-90");
  box.classList.add("opacity-100", "scale-100");
  setTimeout(() => {
    box.classList.remove("opacity-100", "scale-100");
    box.classList.add("opacity-0", "scale-90");
  }, 2200);
}
window.showRuknAlert = showToast;

/* ========= Login modal ========= */
function openLoginModalById(id) {
  const m = document.getElementById(id || "loginModal");
  if (m) m.classList.remove("hidden");
}
function isGuestFromEl(el) {
  return !!el && el.dataset.guest === "1";
}
function isAuthedFromEl(el) {
  if (!el) return false;
  if (el.dataset.auth != null) return el.dataset.auth === "1";
  if (document.body && document.body.dataset.auth != null) return document.body.dataset.auth === "1";
  return false;
}

/* ========= Cookies ========= */
function getCookie(name) {
  const value = `; ${document.cookie || ""}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return "";
}

/* ========= Ads Filters (same as store) ========= */
function bindUserFilters() {
  const grid = document.getElementById("storeAdsGrid");
  const adsCount = document.getElementById("adsCount");
  const categoryFilter = document.getElementById("categoryFilter");
  const cityFilter = document.getElementById("cityFilter");

  if (!grid || !adsCount || !categoryFilter || !cityFilter) return;

  const cards = () => Array.from(grid.querySelectorAll(".store-ad-wrap"));

  function apply() {
    const selectedRoot = String(categoryFilter.value || "all").trim();
    const selectedCity = String(cityFilter.value || "all").trim();
    let visible = 0;

    cards().forEach((el) => {
      const rootId = String(el.getAttribute("data-root-category-id") || "").trim();
      const cityId = String(el.getAttribute("data-city-id") || "").trim();
      const okCat = selectedRoot === "all" || rootId === selectedRoot;
      const okCity = selectedCity === "all" || cityId === selectedCity;
      const show = okCat && okCity;
      el.classList.toggle("hidden", !show);
      if (show) visible++;
    });

    adsCount.textContent = String(visible);
  }

  categoryFilter.addEventListener("change", apply);
  cityFilter.addEventListener("change", apply);
  apply();
}

/* ========= Phone Reveal (same behavior) ========= */
function bindPhoneReveal() {
  const sellerPhoneEl = document.getElementById("sellerPhone");
  const revealPhoneBtn = document.getElementById("revealPhoneBtn");
  const callBtn = document.getElementById("callBtn");
  const whatsappBtn = document.getElementById("whatsappBtn");
  const contactActions = document.getElementById("contactActions");

  if (!sellerPhoneEl || !revealPhoneBtn) return;

  function normalizeToIntl962(phone) {
    const digits = String(phone || "").replace(/\D/g, "");
    if (digits.startsWith("07") && digits.length === 10) return "962" + digits.slice(1);
    if (digits.startsWith("9627") && digits.length === 12) return digits;
    return digits;
  }

  function setMasked() {
    const masked = sellerPhoneEl.dataset.masked || sellerPhoneEl.textContent;
    sellerPhoneEl.textContent = masked;
    sellerPhoneEl.dataset.revealed = "false";
  }

  function reveal() {
    if (isGuestFromEl(revealPhoneBtn) || !isAuthedFromEl(revealPhoneBtn)) {
      openLoginModalById(revealPhoneBtn.dataset.loginModal);
      return false;
    }
    if (sellerPhoneEl.dataset.revealed === "true") return true;

    const full = sellerPhoneEl.dataset.full || "";
    if (!full) return false;

    sellerPhoneEl.textContent = full;
    sellerPhoneEl.dataset.revealed = "true";

    if (callBtn) callBtn.href = "tel:" + full;
    if (whatsappBtn) whatsappBtn.href = "https://wa.me/" + normalizeToIntl962(full);

    if (contactActions) {
      contactActions.classList.remove("hidden");
      contactActions.classList.add("flex");
    }

    showToast("✔ تم إظهار الرقم");
    return true;
  }

  setMasked();

  if (callBtn) callBtn.href = "#";
  if (whatsappBtn) whatsappBtn.href = "#";
  if (contactActions) {
    contactActions.classList.add("hidden");
    contactActions.classList.remove("flex");
  }

  revealPhoneBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    reveal();
  });

  if (callBtn) {
    callBtn.addEventListener("click", (e) => {
      if (isGuestFromEl(callBtn) || !isAuthedFromEl(callBtn)) {
        e.preventDefault();
        openLoginModalById(callBtn.dataset.loginModal);
        return;
      }
      if (sellerPhoneEl.dataset.revealed !== "true") {
        e.preventDefault();
        if (reveal()) window.location.href = callBtn.href;
      }
    });
  }

  if (whatsappBtn) {
    whatsappBtn.addEventListener("click", (e) => {
      if (isGuestFromEl(whatsappBtn) || !isAuthedFromEl(whatsappBtn)) {
        e.preventDefault();
        openLoginModalById(whatsappBtn.dataset.loginModal);
        return;
      }
      if (sellerPhoneEl.dataset.revealed !== "true") {
        e.preventDefault();
        if (reveal()) window.open(whatsappBtn.href, "_blank", "noopener");
      }
    });
  }
}

/* ========= Share (bind both buttons) ========= */
function bindShare() {
  const btns = [document.getElementById("shareBtn"), document.getElementById("shareBtnSide")].filter(Boolean);
  if (!btns.length) return;

  async function doShare() {
    const shareData = {
      title: "مستخدم على منصة ركن",
      text: "شاهد هذا المستخدم على منصة ركن",
      url: window.location.href,
    };
    try {
      if (navigator.share) await navigator.share(shareData);
      else {
        await navigator.clipboard.writeText(window.location.href);
        showToast("✔ تم نسخ رابط المستخدم");
      }
    } catch {}
  }

  btns.forEach((b) => b.addEventListener("click", doShare));
}

/* ========= Message accordion + AJAX (same as store) ========= */
function bindMessage() {
  const toggleMessageBox = document.getElementById("toggleMessageBox");
  const messageBox = document.getElementById("messageBox");
  const messageChevron = document.getElementById("messageChevron");
  const messageInputRef = document.getElementById("messageText");

  if (toggleMessageBox && messageBox) {
    toggleMessageBox.addEventListener("click", () => {
      const isAuth = toggleMessageBox.dataset.auth === "1" || isAuthedFromEl(toggleMessageBox);
      if (!isAuth) {
        openLoginModalById(toggleMessageBox.dataset.loginModal);
        return;
      }

      const isHidden = messageBox.classList.contains("hidden");
      if (isHidden) {
        messageBox.classList.remove("hidden");
        if (messageChevron) messageChevron.classList.add("rotate-180");
        setTimeout(() => messageInputRef?.focus(), 100);
      } else {
        messageBox.classList.add("hidden");
        if (messageChevron) messageChevron.classList.remove("rotate-180");
      }
    });
  }

  const messageForm = document.getElementById("messageForm");
  const messageText = document.getElementById("messageText");
  const messageError = document.getElementById("messageError");
  if (!messageForm) return;

  messageForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const isAuth = document.body?.dataset.auth === "1";
    if (!isAuth) {
      openLoginModalById(messageForm.dataset.loginModal || "loginModal");
      return;
    }

    const val = (messageText?.value || "").trim();
    if (!val) {
      messageError?.classList.remove("hidden");
      return;
    }
    messageError?.classList.add("hidden");

    const url = messageForm.dataset.action || messageForm.getAttribute("action");
    if (!url) {
      showToast("تعذر إرسال الرسالة");
      return;
    }

    const fd = new FormData();
    fd.set("body", val);

    const submitBtn = messageForm.querySelector("button[type='submit']");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.classList.add("opacity-60", "cursor-not-allowed");
    }

    try {
      const res = await fetch(url, {
        method: "POST",
        body: fd,
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCookie("csrftoken"),
        },
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok || !data.ok) {
        if (data.error === "self_message") showToast("لا يمكنك مراسلة نفسك");
        else showToast(data.message || "تعذر إرسال الرسالة");
        return;
      }

      showToast("✔ تم إرسال الرسالة");
      messageForm.reset();
      messageBox?.classList.add("hidden");
      messageChevron?.classList.remove("rotate-180");
    } catch (err) {
      console.error(err);
      showToast("تعذر الاتصال بالخادم");
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove("opacity-60", "cursor-not-allowed");
      }
    }
  });
}

/* ========= init ========= */
function safeRun(fn, name) {
  try { fn(); } catch (e) { console.error("Error in " + name, e); }
}

function initUserProfile() {
  safeRun(bindUserFilters, "bindUserFilters");
  safeRun(bindPhoneReveal, "bindPhoneReveal");
  safeRun(bindShare, "bindShare");
  safeRun(bindMessage, "bindMessage");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initUserProfile);
} else {
  initUserProfile();
}
