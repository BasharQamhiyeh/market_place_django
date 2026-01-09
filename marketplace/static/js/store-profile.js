/* =========================
   store-profile.js (UPDATED for Listings + Reviews mockup)
   ✅ Keeps everything else intact
   ✅ Fix: listings filters + correct count (ignore empty state)
   ✅ Fix: message form auth gating actually works (form had no data-auth)
   ✅ Fix: prevent double-init if script injected twice
   ✅ Keeps: top "التقييم" box + stars update without reload (JS-only)
   ✅ Source of truth = listUrl response (avg/count) inside loadPage()
========================= */

/* ========= HARD GUARD ========= */
(() => {
  const ROOT = document.documentElement;
  if (ROOT.dataset.storeProfileInit === "1") return;
  ROOT.dataset.storeProfileInit = "1";
})();

/* ========= Toast ========= */
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

/* ========= Login modal (same as item page) ========= */
function openLoginModal() {
  const m = document.getElementById("loginModal");
  if (m) m.classList.remove("hidden");
  console.log("🔒 openLoginModal()");
}
window.openLoginModal = openLoginModal;

function openLoginModalById(id) {
  const m = document.getElementById(id || "loginModal");
  if (m) m.classList.remove("hidden");
  console.log("🔒 openLoginModalById()", id || "loginModal");
}

/* ========= Auth helpers ========= */
function isGuestFromEl(el) {
  if (!el) return false;
  return el.dataset.guest === "1";
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

/* ========= JSON script reader ========= */
function readJsonScript(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  try {
    return JSON.parse(el.textContent || "null");
  } catch {
    return null;
  }
}

/* ========= SVG Stars (half allowed) - CLIP method (RTL safe) ========= */
function renderStarsSVG(value, opts = {}) {
  const v = Math.max(0, Math.min(5, Number(value) || 0));
  const size = opts.size ?? 16;
  const gap = opts.gap ?? 4;
  const active = opts.activeColor ?? "var(--rukn-orange)";
  const inactive = opts.inactiveColor ?? "#e5e7eb";
  const uid = (opts.idBase ?? "s") + "-" + Math.random().toString(36).slice(2);
  const isRTL = opts.rtl ?? (document?.documentElement?.dir === "rtl");

  const STAR_PATH = "M12 17.3l6.2 3.7-1.6-7 5.4-4.7-7.1-.6L12 2 9.1 8.7l-7.1.6 5.4 4.7-1.6 7z";

  let html = `<span class="stars-row" style="gap:${gap}px">`;

  for (let i = 1; i <= 5; i++) {
    const frac = Math.max(0, Math.min(1, v - (i - 1)));
    const clipId = `${uid}-clip-${i}`;
    const w = 24 * frac;
    const x = isRTL ? 24 - w : 0;

    html += `
      <svg class="star-svg" width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true">
        <path d="${STAR_PATH}" fill="${inactive}"></path>
        <defs>
          <clipPath id="${clipId}">
            <rect x="${x}" y="0" width="${w}" height="24"></rect>
          </clipPath>
        </defs>
        <path d="${STAR_PATH}" fill="${active}" clip-path="url(#${clipId})"></path>
      </svg>`;
  }

  html += `</span>`;
  return html;
}

/* ========= Tabs ========= */
function setActiveTab(tabKey, doScroll = true) {
  const btns = document.querySelectorAll(".tab-btn[data-tab]");
  const panels = document.querySelectorAll(".tab-panel[data-panel]");

  btns.forEach((b) => b.classList.toggle("is-active", b.dataset.tab === tabKey));
  panels.forEach((p) => p.classList.toggle("hidden", p.dataset.panel !== tabKey));

  const url = new URL(window.location.href);
  url.searchParams.set("tab", tabKey);
  window.history.replaceState({}, "", url.toString());

  if (doScroll) {
    const wrapper = document.querySelector(".tab-btn")?.closest(".container-box");
    wrapper?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}
window.setActiveTab = setActiveTab;

function initTabs() {
  const btns = document.querySelectorAll(".tab-btn[data-tab]");
  if (!btns.length) return;

  btns.forEach((btn) => {
    btn.addEventListener("click", () => setActiveTab(btn.dataset.tab, false));
  });

  const tab = new URLSearchParams(window.location.search).get("tab");
  const allowed = ["ratings", "store", "ads"];
  setActiveTab(allowed.includes(tab) ? tab : "ads", false);
}

/* ========= Update averages in BOTH places ========= */
function updateStoreAverageUI(avg, count) {
  const ratingAvg = document.getElementById("ratingAvg");
  if (ratingAvg && avg != null) ratingAvg.textContent = String(avg);

  const ratingCount = document.getElementById("ratingCount");
  if (ratingCount && count != null) ratingCount.textContent = String(count);

  const topAvg = document.getElementById("topRatingAvg");
  if (topAvg && avg != null) topAvg.textContent = String(avg);

  const inline = document.getElementById("storeStarsInline");
  if (inline && avg != null) {
    inline.dataset.avg = String(avg);
    inline.innerHTML = renderStarsSVG(Number(avg) || 0, { size: 14, idBase: "storeInline" });
  }

  const avgStars = document.getElementById("avgStars");
  if (avgStars && avg != null) {
    avgStars.innerHTML = renderStarsSVG(Number(avg) || 0, { size: 16, idBase: "avgStars" });
  }
}

/* ========= Ads Filters (REAL DOM) ========= */
function bindStoreFilters() {
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




/* ========= Phone Reveal (login gated like item page) ========= */
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

/* ========= Share ========= */
function bindShare() {
  const shareBtn = document.getElementById("shareBtn");
  if (!shareBtn) return;

  shareBtn.addEventListener("click", async () => {
    const shareData = {
      title: "متجر على منصة ركن",
      text: "شاهد هذا المتجر على منصة ركن",
      url: window.location.href,
    };
    try {
      if (navigator.share) await navigator.share(shareData);
      else {
        await navigator.clipboard.writeText(window.location.href);
        showToast("✔ تم نسخ رابط المتجر");
      }
    } catch (e) {}
  });
}

/* ========= Message accordion ========= */
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
        setTimeout(() => {
          if (messageInputRef) messageInputRef.focus();
        }, 100);
      } else {
        messageBox.classList.add("hidden");
        if (messageChevron) messageChevron.classList.remove("rotate-180");
      }
    });
  }

  const messageForm = document.getElementById("messageForm");
  const messageText = document.getElementById("messageText");
  const messageError = document.getElementById("messageError");

  if (messageForm) {
    messageForm.addEventListener("submit", (e) => {
      // ✅ FIX: template form has no data-auth, so this always returned false before.
      const can = document.body?.dataset.auth === "1";
      if (!can) {
        e.preventDefault();
        openLoginModalById(messageForm.dataset.loginModal || "loginModal");
        return;
      }

      e.preventDefault();
      const val = (messageText?.value || "").trim();
      if (!val) {
        if (messageError) messageError.classList.remove("hidden");
        return;
      }
      if (messageError) messageError.classList.add("hidden");

      showToast("✔ تم إرسال الرسالة");
      messageForm.reset();
    });
  }
}

/* ========= Reviews (FULL mockup: list + pagination + summary) ========= */
function bindStoreReviews() {
  const cfg = readJsonScript("store-reviews-data") || {};
  const listUrl = cfg.listUrl || "";
  const submitUrl = cfg.submitUrl || "";
  const perPage = Number(cfg.perPage || 4);
  const loginModalId = cfg.loginModalId || "loginModal";

  if (!listUrl || !submitUrl) return;

  const ratingAvgEl = document.getElementById("ratingAvg");
  const ratingCountEl = document.getElementById("ratingCount");
  const avgStarsEl = document.getElementById("avgStars");
  const breakdownEl = document.getElementById("ratingBreakdown");

  const reviewsBox = document.getElementById("latestReviews");
  const reviewsMeta = document.getElementById("reviewsMeta");
  const prevBtn = document.getElementById("prevPage");
  const nextBtn = document.getElementById("nextPage");
  const pageNumbers = document.getElementById("pageNumbers");

  const starsWrap = document.getElementById("stars");
  const ratingSubject = document.getElementById("ratingSubject");
  const ratingNote = document.getElementById("ratingNote");
  const submitBtn = document.getElementById("submitRating");
  const ratingMsg = document.getElementById("ratingMsg");

  if (!reviewsBox || !submitBtn || !starsWrap) return;

  let selected = 0;
  let page = 1;
  let pages = 1;

  const STAR_LABELS = { 5: "5 نجوم", 4: "4 نجوم", 3: "3 نجوم", 2: "2 نجوم", 1: "1 نجوم" };

  function formatArabicDate(iso) {
    if (!iso) return "";
    const d = new Date(String(iso).slice(0, 10) + "T00:00:00");
    return new Intl.DateTimeFormat("ar-JO", { day: "2-digit", month: "long", year: "numeric" }).format(d);
  }

  function renderBreakdown(breakdown, count) {
    if (!breakdownEl) return;
    breakdownEl.innerHTML = "";
    [5, 4, 3, 2, 1].forEach((s) => {
      const c = Number((breakdown && (breakdown[String(s)] ?? breakdown[s])) || 0);
      const percent = count ? (c / count) * 100 : 0;
      breakdownEl.insertAdjacentHTML(
        "beforeend",
        `
        <div class="flex items-center gap-3">
          <div class="w-16 text-xs font-bold text-gray-700">${STAR_LABELS[s]}</div>
          <div class="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
            <div class="bg-orange-500 h-full" style="width:${percent}%"></div>
          </div>
          <div class="w-10 text-left text-xs font-bold text-gray-600">${c}</div>
        </div>
      `
      );
    });
  }

  function renderSummary(avg, count, breakdown) {
    if (ratingAvgEl) ratingAvgEl.textContent = String(avg ?? 0);
    if (ratingCountEl) ratingCountEl.textContent = String(count ?? 0);
    if (avgStarsEl) avgStarsEl.innerHTML = renderStarsSVG(avg, { size: 16, idBase: "avg" });
    renderBreakdown(breakdown, count);
  }

  function renderReviewsMeta(total) {
    if (!reviewsMeta) return;
    if (!total) {
      reviewsMeta.textContent = "لا توجد مراجعات بعد";
      return;
    }
    const start = (page - 1) * perPage + 1;
    const end = Math.min(page * perPage, total);
    reviewsMeta.textContent = `عرض ${start}–${end} من ${total} مراجعة`;
  }

  function renderPageNumbers() {
    if (!pageNumbers) return;
    pageNumbers.innerHTML = "";

    const tp = pages;
    const cur = page;

    const wanted = new Set([1, tp, cur - 2, cur - 1, cur, cur + 1, cur + 2]);
    const sorted = [...wanted].filter((p) => p >= 1 && p <= tp).sort((a, b) => a - b);

    let last = 0;
    sorted.forEach((p) => {
      if (p - last > 1) pageNumbers.insertAdjacentHTML("beforeend", `<span class="px-2 text-gray-400 font-extrabold">…</span>`);
      pageNumbers.insertAdjacentHTML(
        "beforeend",
        `<button type="button" class="page-btn ${p === cur ? "active" : ""}" data-page="${p}">${p}</button>`
      );
      last = p;
    });

    pageNumbers.querySelectorAll("button[data-page]").forEach((btn) => {
      btn.addEventListener("click", () => {
        page = Number(btn.dataset.page || 1);
        loadPage(true);
      });
    });
  }

  function reviewerAvatar(name) {
    const safe = encodeURIComponent(name || "User");
    return `https://ui-avatars.com/api/?name=${safe}&background=eee&color=444`;
  }

  function renderReviews(results) {
    reviewsBox.innerHTML = "";

    if (!results || !results.length) {
      reviewsBox.innerHTML = `<div class="text-center text-sm text-gray-500 py-6">لا يوجد تقييمات بعد.</div>`;
      return;
    }

    (results || []).forEach((r) => {
      const name = r.reviewer || "مستخدم";
      const avatar = r.avatar || reviewerAvatar(name);
      const dateTxt = r.created_at ? formatArabicDate(r.created_at) : "";
      const subject = (r.subject || "").trim();
      const note = (r.comment || "").trim();
      const isUser = !!r.is_user;

      const wholeStars = Math.round(Number(r.rating || 0));

      reviewsBox.insertAdjacentHTML(
        "beforeend",
        `
        <article class="rounded-2xl border ${isUser ? "bg-orange-50 border-orange-200" : "bg-white border-gray-200"} p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-3">
              <img src="${avatar}" alt="${name}" class="w-10 h-10 rounded-full object-cover border border-gray-200 bg-gray-100">
              <div class="text-right">
                <div class="text-sm font-extrabold text-gray-900">${name}</div>
                ${dateTxt ? `<div class="text-[11px] text-gray-500 mt-0.5">تمت المراجعة بتاريخ ${dateTxt}</div>` : ""}
              </div>
            </div>
            ${isUser ? `<span class="text-[11px] font-extrabold text-[var(--rukn-orange)]">تعليقك</span>` : ""}
          </div>

          <div class="mt-3 flex items-center gap-3">
            <div>${renderStarsSVG(wholeStars, { size: 16, idBase: "rv-" + Math.random().toString(36).slice(2) })}</div>
            ${subject ? `<div class="text-sm font-extrabold text-gray-900">${subject}</div>` : ""}
          </div>

          ${note ? `<div class="mt-2 text-sm text-gray-800 leading-7">${note}</div>` : ""}
        </article>
      `
      );
    });
  }

  async function fetchPage(p) {
    const url = new URL(listUrl, window.location.origin);
    url.searchParams.set("page", String(p));
    url.searchParams.set("per_page", String(perPage));

    const res = await fetch(url.toString(), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.message || "Failed to load reviews");
    return data;
  }

  async function loadPage(doScroll = false) {
    try {
      const data = await fetchPage(page);
      page = Number(data.page || 1);
      pages = Number(data.pages || 1);

      renderSummary(data.avg, data.count, data.breakdown);
      updateStoreAverageUI(data.avg, data.count);

      renderReviewsMeta(data.count);
      renderReviews(data.results);
      renderPageNumbers();

      if (prevBtn) prevBtn.disabled = page <= 1;
      if (nextBtn) nextBtn.disabled = page >= pages;

      if (doScroll) document.getElementById("reviewSection")?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
      console.error(e);
    }
  }

  if (prevBtn)
    prevBtn.addEventListener("click", () => {
      page = Math.max(1, page - 1);
      loadPage(true);
    });
  if (nextBtn)
    nextBtn.addEventListener("click", () => {
      page = Math.min(pages, page + 1);
      loadPage(true);
    });

  const nodes = Array.from(starsWrap.querySelectorAll(".star[data-v]")).length
    ? Array.from(starsWrap.querySelectorAll(".star[data-v]"))
    : Array.from(starsWrap.querySelectorAll("[data-v]"));

  function updateStars() {
    nodes.forEach((star) => star.classList.toggle("active", +star.dataset.v <= selected));
  }
  function previewStars(v) {
    nodes.forEach((star) => star.classList.toggle("active", +star.dataset.v <= v));
  }

  nodes.forEach((star) => {
    const val = +star.dataset.v;
    star.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      selected = val;
      updateStars();
      if (ratingMsg) ratingMsg.textContent = `تقييمك: ${selected}/5`;
    });
    star.addEventListener("mouseenter", () => previewStars(val));
    star.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        selected = val;
        updateStars();
        if (ratingMsg) ratingMsg.textContent = `تقييمك: ${selected}/5`;
      }
    });
  });
  starsWrap.addEventListener("mouseleave", updateStars);

  (function preloadUserReview() {
    const ur = readJsonScript("user-review-json");
    if (!ur) {
      updateStars();
      return;
    }
    const r = Number(ur.rating || 0);
    if (r >= 1 && r <= 5) selected = r;
    if (ratingSubject && ur.subject != null) ratingSubject.value = String(ur.subject || "");
    if (ratingNote && ur.comment != null) ratingNote.value = String(ur.comment || "");
    submitBtn.textContent = "تعديل التقييم";
    if (ratingMsg) ratingMsg.textContent = "بإمكانك تعديل تقييمك";
    updateStars();
  })();

  async function submitReview() {
    const isAuth = document.body?.dataset.auth === "1";
    if (!isAuth) {
      openLoginModalById(loginModalId);
      return;
    }
    if (!selected) {
      showToast("يرجى اختيار عدد النجوم");
      if (ratingMsg) ratingMsg.textContent = "⚠️ اختر التقييم أولاً";
      return;
    }

    const fd = new FormData();
    fd.set("rating", String(selected));
    fd.set("subject", (ratingSubject?.value || "").trim());
    fd.set("comment", (ratingNote?.value || "").trim());

    const csrftoken = getCookie("csrftoken");

    submitBtn.disabled = true;
    submitBtn.classList.add("opacity-60", "cursor-not-allowed");

    try {
      const res = await fetch(submitUrl, {
        method: "POST",
        body: fd,
        credentials: "same-origin",
        headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrftoken },
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        showToast(data.message || "تعذر إرسال المراجعة.");
        return;
      }

      submitBtn.textContent = "تعديل التقييم";
      if (ratingMsg) ratingMsg.textContent = "تم حفظ تقييمك ✔";
      showToast(data.message || "✔ تم حفظ تقييمك");

      page = 1;
      await loadPage(true);
    } catch (err) {
      console.error(err);
      showToast("تعذر الاتصال بالخادم");
    } finally {
      submitBtn.disabled = false;
      submitBtn.classList.remove("opacity-60", "cursor-not-allowed");
    }
  }

  submitBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    submitReview();
  });

  loadPage(false);
}

/* ========= Safe Init ========= */
function safeRun(fn, name) {
  try {
    fn();
  } catch (e) {
    console.error("Error in " + name, e);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  safeRun(initTabs, "initTabs");

  safeRun(() => {
    const inline = document.getElementById("storeStarsInline");
    if (!inline) return;
    const avg = Number(inline.dataset.avg || 0);
    inline.innerHTML = renderStarsSVG(avg, { size: 14, idBase: "storeInline" });
  }, "storeStarsInline");

  safeRun(bindStoreFilters, "bindStoreFilters");
  safeRun(bindPhoneReveal, "bindPhoneReveal");
  safeRun(bindShare, "bindShare");
  safeRun(bindMessage, "bindMessage");
  safeRun(bindStoreReviews, "bindStoreReviews");

  // ✅ DO NOT bind report modal here (report-modal.js handles it)
});

/* ========= Parallax (unchanged) ========= */
(() => {
  const hero = document.getElementById("heroParallax");
  const img = document.getElementById("heroParallaxImg");
  if (!hero || !img) return;

  img.style.willChange = "transform";
  img.style.transformOrigin = "top center";

  const SCROLL_RATIO = 0.9;
  const SCALE = 1.35;
  const MAX_MOVE_FACTOR = 0.7;

  let heroTop = 0,
    heroH = 0,
    maxMove = 0,
    ticking = false;
  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

  function measure() {
    const r = hero.getBoundingClientRect();
    heroTop = r.top + window.scrollY;
    heroH = r.height || 1;
    maxMove = heroH * MAX_MOVE_FACTOR;
    img.style.transform = `translate3d(0,0,0) scale(${SCALE})`;
  }
  function update() {
    ticking = false;
    const scrollY = window.scrollY;
    const vh = window.innerHeight;
    if (scrollY > heroTop + heroH + vh || scrollY + vh < heroTop - vh) return;
    const delta = (scrollY - heroTop) * SCROLL_RATIO;
    const y = clamp(delta, -maxMove, maxMove);
    img.style.transform = `translate3d(0, ${y}px, 0) scale(${SCALE})`;
  }
  function onScroll() {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(update);
    }
  }

  if (!img.complete)
    img.addEventListener("load", () => {
      measure();
      update();
    });
  window.addEventListener(
    "resize",
    () => {
      measure();
      update();
    },
    { passive: true }
  );
  window.addEventListener("scroll", onScroll, { passive: true });

  measure();
  update();
})();
