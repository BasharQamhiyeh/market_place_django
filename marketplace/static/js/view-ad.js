console.log("✅ view-ad.js loaded");

window.addEventListener("error", (e) => {
  console.error("❌ JS error:", e.message, "at", e.filename, e.lineno + ":" + e.colno);
});
window.addEventListener("unhandledrejection", (e) => {
  console.error("❌ Unhandled rejection:", e.reason);
});



/* =========================
   Gallery (REAL DATA)
========================= */
function readGalleryImages() {
  const el = document.getElementById("gallery-data");
  if (!el) return [];
  try {
    const arr = JSON.parse(el.textContent || "[]");
    return Array.isArray(arr) ? arr.filter(Boolean) : [];
  } catch {
    return [];
  }
}

const galleryImages = readGalleryImages();

const mainImageEl = document.getElementById("mainImage");
const thumbsRow = document.getElementById("thumbsRow");
const imagesCountEl = document.getElementById("imagesCount");

let currentImageIndex = 0;

function renderGallery() {
  if (!galleryImages.length) {
    if (mainImageEl) {
      mainImageEl.src = "";
      mainImageEl.alt = "لا توجد صور";
    }
    if (imagesCountEl) imagesCountEl.textContent = "0";
    return;
  }

  mainImageEl.src = galleryImages[0];
  imagesCountEl.textContent = String(galleryImages.length);

  thumbsRow.innerHTML = "";
  galleryImages.forEach((src, index) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "thumb" + (index === 0 ? " active" : "");
    btn.dataset.index = String(index);
    btn.innerHTML = `<img src="${src}" alt="صورة مصغرة ${index + 1} للمنتج">`;
    btn.addEventListener("click", () => setMainImage(index));
    thumbsRow.appendChild(btn);
  });
}

function setMainImage(index) {
  currentImageIndex = index;
  mainImageEl.src = galleryImages[index];
  document.querySelectorAll(".thumb").forEach((t) => t.classList.remove("active"));
  const activeThumb = document.querySelector(`.thumb[data-index="${index}"]`);
  if (activeThumb) activeThumb.classList.add("active");
}

/* =========================
   Lightbox
========================= */
const lightbox = document.getElementById("lightbox");
const lightboxImage = document.getElementById("lightboxImage");

function openLightbox(index) {
  if (!galleryImages.length) return;
  currentImageIndex = index;
  lightboxImage.src = galleryImages[currentImageIndex];
  lightbox.classList.add("open");
}

function closeLightbox() {
  lightbox.classList.remove("open");
}

function changeLightboxImage(step) {
  if (!galleryImages.length) return;
  currentImageIndex = (currentImageIndex + step + galleryImages.length) % galleryImages.length;
  lightboxImage.src = galleryImages[currentImageIndex];
  setMainImage(currentImageIndex);
}

if (lightbox) {
  lightbox.addEventListener("click", (e) => {
    if (e.target === lightbox) closeLightbox();
  });
}

window.openLightbox = openLightbox;
window.closeLightbox = closeLightbox;
window.changeLightboxImage = changeLightboxImage;

/* =========================
   Toast
========================= */
function showRuknAlert(message) {
  const wrapper = document.getElementById("ruknAlert");
  const box = document.getElementById("ruknAlertBox");
  if (!wrapper || !box) return;

  box.textContent = message;
  wrapper.classList.remove("opacity-0");
  wrapper.classList.add("opacity-100");
  box.classList.remove("scale-75");
  box.classList.add("scale-100");

  setTimeout(() => {
    wrapper.classList.add("opacity-0");
    wrapper.classList.remove("opacity-100");
    box.classList.add("scale-75");
    box.classList.remove("scale-100");
  }, 2000);
}
window.showRuknAlert = showRuknAlert;

/* =========================
   Favorite (REAL backend)
   - Uses csrftoken cookie
   - No dataset.auth dependency
========================= */
/* === Favorite (REAL backend) — supports multiple buttons === */

function openLoginModal() {
  const m = document.getElementById("loginModal");
  if (m) m.classList.remove("hidden");
  console.log("🔒 openLoginModal()");
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return "";
}

function applyFavUI(btn, isFav) {
  if (!btn) return;

  btn.classList.toggle("is-fav", isFav);

  // text
  const textEl = btn.querySelector("[data-fav-text]");
  if (textEl) {
    textEl.textContent = isFav ? "تمت الإضافة إلى المفضلة" : "إضافة للمفضلة";
  }

  // icon wrapper
  const iconWrap = btn.querySelector("[data-fav-icon]");


  if (isFav) {
    // button background
    btn.classList.add("bg-orange-50", "border-orange-300");
    btn.classList.remove("bg-white", "border-gray-200");

    // 🔥 icon becomes orange
    if (iconWrap) {
      iconWrap.classList.add(
        "bg-orange-100",
        "border-orange-300",
        "text-[var(--rukn-orange)]"
      );
      iconWrap.classList.remove(
        "bg-gray-50",
        "border-gray-200",
        "text-gray-400"
      );
    }
  } else {
    // reset button
    btn.classList.remove("bg-orange-50", "border-orange-300");
    btn.classList.add("bg-white", "border-gray-200");

    // reset icon
    if (iconWrap) {
      iconWrap.classList.remove(
        "bg-orange-100",
        "border-orange-300",
        "text-[var(--rukn-orange)]"
      );
      iconWrap.classList.add(
        "bg-gray-50",
        "border-gray-200",
        "text-gray-400"
      );
    }
  }
}


const favBtns = Array.from(document.querySelectorAll('[data-fav-btn="1"][data-fav-scope="detail"]'));
console.log("⭐ fav buttons found:", favBtns.length, favBtns);

favBtns.forEach((btn) => {
  // init state if present
  if (btn.dataset.favorited != null) {
    applyFavUI(btn, btn.dataset.favorited === "1");
  }

  btn.addEventListener("click", async (e) => {
    e.preventDefault();
    e.stopPropagation();
    console.log("🖱️ fav clicked:", btn);

    // guest button
    if (btn.dataset.guest === "1" || !btn.dataset.url) {
      openLoginModal();
      return;
    }

    const url = btn.dataset.url;
    const csrftoken = getCookie("csrftoken");
    console.log("POST =>", url, "CSRF?", !!csrftoken);

    try {
      const res = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken,
        },
      });

      console.log("fav status:", res.status);

      const data = await res.json().catch(() => ({}));
      console.log("fav json:", data);

      if (!res.ok) {
        if (res.status === 403) openLoginModal();
        if (data && data.error === "cannot_favorite_own_item" && window.showRuknAlert) {
          showRuknAlert("لا يمكنك إضافة إعلانك إلى المفضلة");
        }
        return;
      }

      const isFav = !!data.is_favorited;
      btn.dataset.favorited = isFav ? "1" : "0";
      applyFavUI(btn, isFav);

      if (typeof data.favorite_count === "number" && typeof updateNavbarFavUI === "function") {
        updateNavbarFavUI(data.favorite_count, data.navbar_html || null);
      }

      if (window.showRuknAlert) {
        showRuknAlert(isFav ? "✔ تمت الإضافة للمفضلة" : "✳️ تم الحذف من المفضلة");
      }
    } catch (err) {
      console.error("❌ fav failed:", err);
    }
  });
});




/* =========================
   Share
========================= */
const shareBtn = document.getElementById("shareBtn");
if (shareBtn) {
  shareBtn.addEventListener("click", async () => {
    const shareData = {
      title: "إعلان على منصة ركن",
      text: "شاهد هذا الإعلان على منصة ركن",
      url: window.location.href,
    };
    try {
      if (navigator.share) await navigator.share(shareData);
      else {
        await navigator.clipboard.writeText(window.location.href);
        showRuknAlert("✔ تم نسخ رابط الإعلان");
      }
    } catch (e) {}
  });
}

/* =========================
   Copy ad number
========================= */
function copyAdNumber() {
  const el = document.getElementById("adNumber");
  if (!el) return;

  const num = el.textContent.trim();
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard
      .writeText(num)
      .then(() => showRuknAlert("✔ تم نسخ رقم الإعلان"))
      .catch(() => fallbackCopy(num));
  } else {
    fallbackCopy(num);
  }
}

function fallbackCopy(text) {
  const temp = document.createElement("textarea");
  temp.value = text;
  document.body.appendChild(temp);
  temp.select();
  try {
    document.execCommand("copy");
  } catch (e) {}
  document.body.removeChild(temp);
  showRuknAlert("✔ تم نسخ رقم الإعلان");
}
window.copyAdNumber = copyAdNumber;

/* =========================
   Phone Reveal (mockup + login gating)
========================= */

(function () {

    console.log("🔎 phone bind-time elements:", {
  sellerPhoneEl: document.getElementById("sellerPhone"),
  revealPhoneBtn: document.getElementById("revealPhoneBtn"),
  callBtn: document.getElementById("callBtn"),
  whatsappBtn: document.getElementById("whatsappBtn"),
});

  const sellerPhoneEl = document.getElementById("sellerPhone");
  const revealPhoneBtn = document.getElementById("revealPhoneBtn");
  const callBtn = document.getElementById("callBtn");
  const whatsappBtn = document.getElementById("whatsappBtn");

  console.log("📞 phone elements:", { sellerPhoneEl, revealPhoneBtn, callBtn, whatsappBtn });

  // use ONE modal opener (don’t redefine openLoginModal twice)
  function openLoginModalSafe() {
    const m = document.getElementById("loginModal");
    if (m) m.classList.remove("hidden");
    console.log("🔒 login modal opened");
  }

  function isGuest() {
    return (
      (revealPhoneBtn && revealPhoneBtn.dataset.guest === "1") ||
      (callBtn && callBtn.dataset.guest === "1") ||
      (whatsappBtn && whatsappBtn.dataset.guest === "1")
    );
  }

  function normalizeToIntl962(phone) {
    const digits = String(phone || "").replace(/\D/g, "");
    if (digits.startsWith("07") && digits.length === 10) return "962" + digits.slice(1);
    if (digits.startsWith("9627") && digits.length === 12) return digits;
    return digits;
  }

  function setMasked() {
    if (!sellerPhoneEl) return;
    const masked = sellerPhoneEl.dataset.masked || sellerPhoneEl.textContent;
    sellerPhoneEl.textContent = masked;
    sellerPhoneEl.dataset.revealed = "false";
  }

  function enableLinks(full) {
    if (callBtn) callBtn.href = "tel:" + full;
    if (whatsappBtn) whatsappBtn.href = "https://wa.me/" + normalizeToIntl962(full);
  }

  function revealIfAllowed() {
      if (!sellerPhoneEl) return false;

      // ✅ guest => login modal
      if (isGuest()) {
        console.log("📞 guest -> open login");
        openLoginModalSafe();
        return false;
      }

      // ✅ seller doesn't want to show phone
      const allow = (sellerPhoneEl.dataset.allow || "1") === "1";
      if (!allow) {
        if (window.showRuknAlert) {
          showRuknAlert("⚠️ البائع يفضّل التواصل عبر الرسائل");
        }

        // (اختياري) افتح صندوق الرسائل تلقائيًا
        const msgBtn = document.getElementById("toggleMessageBox");
        if (msgBtn) msgBtn.click();

        return false;
      }

      // already revealed
      if (sellerPhoneEl.dataset.revealed === "true") return true;

      const full = sellerPhoneEl.dataset.full || "";
      if (!full) {
        console.log("⚠️ no full phone in data-full");
        return false;
      }

      sellerPhoneEl.textContent = full;
      sellerPhoneEl.dataset.revealed = "true";
      enableLinks(full);

      // ✅ show call/whatsapp only AFTER reveal
      const actions = document.getElementById("contactActions");
      if (actions) {
        actions.classList.remove("hidden");
        actions.classList.add("flex");
      }

      console.log("✅ phone revealed:", full);
      return true;
    }


  // init
  setMasked();
  if (callBtn) callBtn.href = "#";
  if (whatsappBtn) whatsappBtn.href = "#";

  const actions = document.getElementById("contactActions");
  if (actions) {
      actions.classList.add("hidden");
      actions.classList.remove("flex");
  }


  // click number
  if (revealPhoneBtn) {
    revealPhoneBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log("🖱️ clicked phone text");
      revealIfAllowed();
    });
  }

  // click call icon
  if (callBtn) {
    callBtn.addEventListener("click", (e) => {
      console.log("🖱️ clicked call icon");
      if (isGuest()) {
        e.preventDefault();
        openLoginModalSafe();
        return;
      }
      if (sellerPhoneEl && sellerPhoneEl.dataset.revealed !== "true") {
        e.preventDefault();
        if (revealIfAllowed()) window.location.href = callBtn.href;
      }
    });
  }

  // click whatsapp icon
  if (whatsappBtn) {
    whatsappBtn.addEventListener("click", (e) => {
      console.log("🖱️ clicked whatsapp icon");
      if (isGuest()) {
        e.preventDefault();
        openLoginModalSafe();
        return;
      }
      if (sellerPhoneEl && sellerPhoneEl.dataset.revealed !== "true") {
        e.preventDefault();
        if (revealIfAllowed()) window.open(whatsappBtn.href, "_blank", "noopener");
      }
    });
  }
})();



/* =========================
   Message accordion
========================= */
/* === Message accordion (auth-gated) === */
const toggleMessageBox = document.getElementById("toggleMessageBox");
const messageBox = document.getElementById("messageBox");
const messageChevron = document.getElementById("messageChevron");
const messageInputRef = document.getElementById("messageText");

function openLoginModalById(id) {
  const m = document.getElementById(id || "loginModal");
  if (m) m.classList.remove("hidden");
}

if (toggleMessageBox && messageBox) {
  toggleMessageBox.addEventListener("click", () => {
    const isAuth = toggleMessageBox.dataset.auth === "1";
    if (!isAuth) {
      openLoginModalById(toggleMessageBox.dataset.loginModal);
      return;
    }

    const isHidden = messageBox.classList.contains("hidden");
    if (isHidden) {
      messageBox.classList.remove("hidden");
      if (messageChevron) messageChevron.classList.add("rotate-180");
      setTimeout(() => { if (messageInputRef) messageInputRef.focus(); }, 100);
    } else {
      messageBox.classList.add("hidden");
      if (messageChevron) messageChevron.classList.remove("rotate-180");
    }
  });
}



/* =========================
   init
========================= */
renderGallery();


(function initLoadMoreSimilar() {
  const btn = document.getElementById("loadMoreSimilarBtn");
  const grid = document.getElementById("similarItemsGrid");
  if (!btn || !grid) return;

  function gridCols(gridEl) {
    const cols = getComputedStyle(gridEl).gridTemplateColumns.split(" ").filter(Boolean).length;
    return Math.max(cols || 1, 1);
  }

  function disableBtn(text) {
    btn.disabled = true;
    btn.classList.add("opacity-60", "cursor-not-allowed");
    btn.textContent = text;
  }

  let locked = false;

  btn.addEventListener("click", async () => {
    if (locked) return;
    locked = true;

    const cols = gridCols(grid);
    const limit = 3 * cols;               // ✅ 3 rows
    const offset = grid.children.length;  // ✅ already visible cards
    const itemId = btn.dataset.itemId;

    btn.disabled = true;
    btn.classList.add("opacity-60");

    try {
      const url = `/items/${itemId}/more-similar/?offset=${offset}&limit=${limit}`;

      const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
      if (!res.ok) throw new Error("Bad response");

      const data = await res.json();

      if (data.html && data.html.trim()) {
        grid.insertAdjacentHTML("beforeend", data.html);
      }

      if (!data.has_more) {
        disableBtn("لا يوجد المزيد من الإعلانات");
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

})();
