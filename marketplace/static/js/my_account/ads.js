// static/js/my_account/ads.js
(() => {
  "use strict";

  // Ads tab may not be in DOM at page load (tabs / partial render)
  // So: resolve elements lazily.
  const getList = () => document.getElementById("adsList");
  const getCountEl = () => document.getElementById("adsCount");

  /* =========================================================
     ✅ Wallet / Points (same mockup behavior, but safe)
  ========================================================= */
  let points = Number(window.__pointsBalance ?? window.points ?? 80);
  let transactions = Array.isArray(window.__pointsTransactions ?? window.transactions)
    ? (window.__pointsTransactions ?? window.transactions)
    : [];

  function updateBalance() {
    const el = document.getElementById("pointsBalance");
    if (!el) return;
    el.innerHTML = points + " 🔥";
  }

  function renderTransactions() {
    const container = document.getElementById("pointsLog");
    if (!container) return;
    container.innerHTML = "";
    if (!transactions.length) return;

    const groups = {};
    transactions.forEach((t) => {
      const date = t.date || new Date().toISOString().split("T")[0];
      groups[date] ??= [];
      groups[date].push(t);
    });

    const sortedDates = Object.keys(groups).sort((a, b) => new Date(b) - new Date(a));
    const today = new Date().toISOString().split("T")[0];
    const yesterday = new Date(Date.now() - 86400000).toISOString().split("T")[0];

    sortedDates.forEach((date) => {
      const dateLabel = document.createElement("div");
      dateLabel.className = "timeline-date";
      dateLabel.innerText =
        date === today ? "اليوم" :
        date === yesterday ? "الأمس" :
        date.replace(/-/g, "/");
      container.appendChild(dateLabel);

      groups[date].forEach((t) => {
        const row = document.createElement("div");
        row.className = "timeline-item";
        row.innerHTML = `
          <span>${t.text}</span>
          <span class="font-bold ${t.amount > 0 ? "text-green-600" : "text-red-600"}">
            ${t.amount > 0 ? "+" : ""}${t.amount} نقطة
          </span>`;
        container.appendChild(row);
      });
    });
  }

  function pushTxn(entry) {
    const date = new Date().toISOString().split("T")[0];
    transactions.unshift({ ...entry, date });
    window.__pointsTransactions = transactions;
    window.transactions = transactions;
    renderTransactions();
  }

  function setPoints(v) {
    points = Number(v);
    window.__pointsBalance = points;
    window.points = points;
    updateBalance();
  }

  /* =========================================================
     ✅ Helpers
  ========================================================= */
  function updateCount() {
    const list = getList();
    const count = getCountEl();
    if (!list || !count) return;
    count.textContent = String(list.querySelectorAll(".ad-row[data-ad-id]").length);
  }

  function getAdRow(id) {
    const list = getList();
    if (!list) return null;
    return list.querySelector(`.ad-row[data-ad-id="${id}"]`);
  }

  function mustEl(id) {
    const el = document.getElementById(id);
    if (!el) console.warn(`[my_account/ads] Missing element #${id}`);
    return el;
  }

  function openModal(id) {
    const m = mustEl(id);
    if (!m) return false;
    m.classList.remove("hidden");
    m.classList.add("flex");
    return true;
  }

  function closeModal(id) {
    const m = document.getElementById(id);
    if (!m) return;
    m.classList.add("hidden");
    m.classList.remove("flex");
  }

  function getCSRFToken() {
    const m = document.cookie.match(/(^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[2]) : "";
  }

  // ---------- Success ----------
  function openSuccessModal(message, title = "تم التنفيذ بنجاح") {
    const msg = document.getElementById("successMsg");
    const ttl = document.getElementById("successTitle");
    if (msg) msg.innerText = message;
    if (ttl) ttl.innerText = title;
    if (!openModal("successModal")) alert(`${title}\n\n${message}`);
  }
  if (!window.closeSuccessModal) window.closeSuccessModal = () => closeModal("successModal");

  // ---------- No points ----------
  function showNoPointsModal() {
    if (!openModal("noPointsModal")) alert("❌ لا يوجد نقاط كافية");
  }
  if (!window.closeNoPointsModal) window.closeNoPointsModal = () => closeModal("noPointsModal");
  window.openWalletTab = () => {
    closeModal("noPointsModal");
    document.querySelector('[data-tab="wallet"]')?.click();
  };

  // ---------- Cooldown ----------
  function parseISO(dateStr) {
    if (!dateStr) return null;
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? null : d;
  }
  function daysBetween(dateStr) {
    const d = parseISO(dateStr);
    if (!d) return 9999;
    const a = new Date(d); a.setHours(0, 0, 0, 0);
    const b = new Date();  b.setHours(0, 0, 0, 0);
    return Math.floor((b - a) / 86400000);
  }
  function canRepublishWithCost(lastRepublishAt) {
    const days = daysBetween(lastRepublishAt);
    if (days >= 7) return { ok: true, cost: 0, daysLeft: 0 };
    return { ok: false, cost: 20, daysLeft: 7 - days };
  }

  /* =========================================================
     ✅ FORCE: Edit/Delete always active
  ========================================================= */
  function enableEditDeleteAlways() {
    const list = getList();
    if (!list) return;

    list.querySelectorAll(".ad-row").forEach((row) => {
      const editLink = row.querySelector(".pill-blue");
      if (editLink) editLink.classList.remove("opacity-40", "pointer-events-none");

      const delBtn = row.querySelector('[data-action="delete"]');
      if (delBtn) {
        delBtn.classList.remove("opacity-40", "pointer-events-none", "cursor-not-allowed");
      }
    });
  }

  /* =========================================================
     ✅ Backend call helper (call anyway even if it 404s)
  ========================================================= */
  async function callBackend(url, payload) {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: payload ? JSON.stringify(payload) : "{}",
      });
      // we don't care if it fails now, but we log
      if (!res.ok) {
        console.warn("[ads] backend call failed:", url, res.status);
      }
      return res;
    } catch (e) {
      console.warn("[ads] backend call error:", url, e);
      return null;
    }
  }

  /* =========================================================
     ✅ Delete Modal (same mockup)
  ========================================================= */
  let adToDelete = null;

  function setDeleteReasons() {
    const select = document.getElementById("deleteReason");
    if (!select) return;

    const reasons = [
      { value: "sold_in", label: "تم البيع خلال منصة ركن" },
      { value: "sold_out", label: "تم البيع خارج منصة ركن" },
      { value: "republish", label: "أريد إعادة نشره لاحقاً" },
      { value: "issue", label: "مشكلة في الإعلان" },
      { value: "other", label: "سبب آخر…" },
    ];

    select.innerHTML =
      `<option value="">— اختر سبب الحذف —</option>` +
      reasons.map((r) => `<option value="${r.value}">${r.label}</option>`).join("");
  }

  function openDeleteModalForAd(id) {
    adToDelete = id;

    if (!document.getElementById("deleteAdModal")) {
      alert("deleteAdModal is missing in DOM.");
      return;
    }

    const t = document.getElementById("deleteTitle");
    const s = document.getElementById("deleteSubtitle");
    const b = document.getElementById("confirmDeleteBtn");
    if (t) t.textContent = "حذف إعلان";
    if (s) s.textContent = "يرجى اختيار سبب حذف الإعلان";
    if (b) b.textContent = "حذف الإعلان";

    setDeleteReasons();

    const select = document.getElementById("deleteReason");
    const other = document.getElementById("deleteReasonOther");
    const err = document.getElementById("deleteReasonError");
    if (select) select.value = "";
    if (other) { other.value = ""; other.classList.add("hidden"); }
    if (err) err.classList.add("hidden");

    openModal("deleteAdModal");
  }

  window.closeDeleteModal = () => {
    closeModal("deleteAdModal");
    adToDelete = null;
  };

  function wireDeleteReasonChange() {
    const select = document.getElementById("deleteReason");
    if (!select) return;
    if (select.dataset.wired === "1") return;
    select.dataset.wired = "1";

    select.addEventListener("change", () => {
      const other = document.getElementById("deleteReasonOther");
      const err = document.getElementById("deleteReasonError");
      if (err) err.classList.add("hidden");
      if (!other) return;
      if (select.value === "other") other.classList.remove("hidden");
      else { other.classList.add("hidden"); other.value = ""; }
    });
  }

  window.confirmDeleteAd = async () => {
    const select = document.getElementById("deleteReason");
    const other = document.getElementById("deleteReasonOther");
    const err = document.getElementById("deleteReasonError");

    const reason = select ? select.value : "";
    const otherTxt = other ? other.value.trim() : "";

    if (!reason) {
      if (err) err.classList.remove("hidden");
      return;
    }
    if (err) err.classList.add("hidden");

    const finalReason =
      (reason === "other" && otherTxt.length)
        ? otherTxt
        : (select?.options?.[select.selectedIndex]?.text || "");

    // ✅ CALL BACKEND ANYWAY (even if view not implemented yet)
    if (adToDelete != null) {
      const row = getAdRow(adToDelete);
      const listingId = Number(row?.dataset?.listingId || 0);
      if (!listingId) {
        console.warn("[ads] Missing data-listing-id on ad row", row);
        return;
      }
      callBackend(`/listing/${listingId}/delete/`, { reason: finalReason });
    }

    // ✅ Optimistic UI
    if (adToDelete != null) {
      const row = getAdRow(adToDelete);
      if (row) row.remove();
      updateCount();
      openSuccessModal(`تم حذف الإعلان — السبب: ${finalReason}`, "✔️ تم الحذف");
    }

    closeModal("deleteAdModal");
    adToDelete = null;
  };

  /* =========================================================
     ✅ Highlight (backend-powered) - you already had fetch here
  ========================================================= */
  let highlightTargetId = null;

  function calcDaysLeftFromNowISO(isoDate) {
    if (!isoDate) return 0;
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const end = new Date(isoDate); end.setHours(0, 0, 0, 0);
    const diff = end - today;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    return days > 0 ? days : 0;
  }

  function ensureFeatureBadge(row, daysLeft) {
    const header = row.querySelector(".ad-header");
    if (!header) return;

    let badge = header.querySelector(".feature-badge");
    if (!badge) {
      badge = document.createElement("span");
      badge.className = "feature-badge flex items-center gap-1";
      header.appendChild(badge);
    }
    badge.textContent = daysLeft > 0 ? `⭐ مميز — متبقّي: ${daysLeft} يوم` : "⭐ مميز";
  }

  function disableHighlightButton(row) {
    const enabled = row.querySelector('[data-action="highlight"]');
    if (enabled) {
      enabled.classList.add("opacity-40", "cursor-not-allowed", "pointer-events-none");
    }
  }

  function openHighlightModalForAd(id) {
    highlightTargetId = id;

    const bal = document.getElementById("highlightPointsBalance");
    const title = document.getElementById("highlightModalTitle");
    if (bal) bal.innerText = points;
    if (title) title.innerText = "⭐ تمييز الإعلان";

    if (!openModal("highlightModal")) alert("highlightModal is missing in DOM.");
  }
  if (!window.closeHighlightModal) window.closeHighlightModal = () => closeModal("highlightModal");

  window.selectHighlightPackage = async (days) => {
    if (!highlightTargetId) return;

    const row = getAdRow(highlightTargetId);
    if (!row) return;

    const listingId = Number(row.dataset.listingId || highlightTargetId);

    // ✅ call backend anyway (already exists in your old file)
    let data = null;
    try {
      const res = await fetch(`/listing/${listingId}/feature/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({ days: Number(days) }),
      });

      data = await res.json().catch(() => null);

      // If backend not ready, res may be 404 or html -> we still continue with UI
      if (!res.ok) console.warn("[ads] feature call failed:", res.status);
    } catch (e) {
      console.warn("[ads] feature call error:", e);
    }

    // ✅ If backend returned real values, use them. Otherwise do mock UI.
    if (data && data.ok) {
      setPoints(data.points_balance);

      pushTxn({
        type: "use",
        text: `⭐ تمييز إعلان رقم ${highlightTargetId} لمدة ${data.days} يوم`,
        amount: -Number(data.cost),
      });

      const featuredUntilISO = data.featured_until ? String(data.featured_until).slice(0, 10) : null;
      if (featuredUntilISO) {
        row.dataset.featuredExpiresAt = featuredUntilISO;
        const daysLeft = calcDaysLeftFromNowISO(featuredUntilISO);
        row.dataset.featuredDaysLeft = String(daysLeft);
        ensureFeatureBadge(row, daysLeft);
      } else {
        row.dataset.featuredDaysLeft = String(days);
        ensureFeatureBadge(row, Number(days));
      }

      disableHighlightButton(row);
      closeModal("highlightModal");
      openSuccessModal("تم تمييز الإعلان بنجاح!", "⭐ تم التمييز");
      highlightTargetId = null;
      return;
    }

    // ✅ MOCK fallback (backend missing)
    row.dataset.featuredDaysLeft = String(days);
    ensureFeatureBadge(row, Number(days));
    disableHighlightButton(row);
    closeModal("highlightModal");
    openSuccessModal("تم تمييز الإعلان بنجاح! (تجربة)", "⭐ تم التمييز");
    highlightTargetId = null;
  };

  /* =========================================================
     ✅ Republish - ADD backend call now
  ========================================================= */
  let republishTargetId = null;
  let republishCost = 0;

  function openRepublishConfirmModalForAd(id, cost) {
    republishTargetId = id;
    republishCost = Number(cost);

    const bal = document.getElementById("republishPointsBalance");
    if (bal) bal.innerText = points;

    const btn = document.getElementById("confirmRepublishBtn");
    if (btn) btn.onclick = () => confirmRepublishNow();

    if (!openModal("republishConfirmModal")) {
      alert("republishConfirmModal is missing in DOM.");
    }
  }

  if (!window.closeRepublishConfirmModal) {
    window.closeRepublishConfirmModal = () => {
      closeModal("republishConfirmModal");
      republishTargetId = null;
      republishCost = 0;
    };
  }

  function setRowActiveUI(row) {
    if (!row) return;

    row.dataset.status = "active";

    row.classList.remove("bg-yellow-50", "border-yellow-300", "bg-red-50", "border-red-300");
    row.classList.add("bg-white", "border", "border-gray-200");

    const badge = row.querySelector(".status-badge");
    if (badge) {
      badge.classList.remove("status-pending", "status-rejected");
      badge.classList.add("status-active");
      badge.innerHTML = `
        <span class="inline-flex items-center gap-1">
          <svg class="w-3 h-3 text-green-600" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <circle cx="12" cy="12" r="10"></circle>
          </svg>
        </span>
        مفعّل
      `;
    }
  }

  function updateRowDateToToday(row) {
    const today = new Date();
    const formatted = `${today.getFullYear()}/${String(today.getMonth() + 1).padStart(2, "0")}/${String(today.getDate()).padStart(2, "0")}`;

    const meta = row.querySelector(".flex.items-center.gap-4.text-sm, .flex.items-center.gap-4.text-sm.text-gray-500, .flex.items-center.gap-4.text-sm.text-gray-500.flex-wrap, .flex.items-center.gap-4.text-sm.text-gray-500.mt-1");
    const metaRow = meta || row.querySelector("div.flex.items-center.gap-4.text-sm.text-gray-500.mt-1.mb-2.flex-wrap") || row.querySelector("div.flex.items-center.gap-4.text-sm");
    if (!metaRow) return;

    const inlineSpans = metaRow.querySelectorAll("span.inline-flex.items-center.gap-1 > span");
    if (inlineSpans && inlineSpans.length >= 2) inlineSpans[1].textContent = formatted;
  }

  function doRepublishAdUI(id, free) {
    const row = getAdRow(id);
    if (!row) return;

    const iso = new Date().toISOString().split("T")[0];
    row.dataset.lastRepublish = iso;

    setRowActiveUI(row);
    updateRowDateToToday(row);

    openSuccessModal(
      free ? "تم إعادة نشر الإعلان مجاناً ✅ (تجربة)" : `تمت إعادة النشر مقابل ${republishCost} نقطة ✅ (تجربة)`,
      "🔄 تم إعادة النشر"
    );
  }

  function confirmRepublishNow() {
    if (!republishTargetId) return;

    if (points < republishCost) {
      closeModal("republishConfirmModal");
      showNoPointsModal();
      return;
    }

    const row = getAdRow(republishTargetId);
    const listingId = Number(row?.dataset?.listingId || republishTargetId);

    // ✅ CALL BACKEND ANYWAY
    callBackend(`/listing/${listingId}/republish/`, {});

    setPoints(points - republishCost);
    pushTxn({
      type: "use",
      text: `🔄 إعادة نشر إعلان رقم ${republishTargetId} قبل انتهاء 7 أيام`,
      amount: -republishCost,
    });

    closeModal("republishConfirmModal");
    doRepublishAdUI(republishTargetId, false);

    republishTargetId = null;
    republishCost = 0;
  }

  /* =========================================================
     ✅ CLICK HANDLING (delegated so it works with tabs)
     + intercept EDIT so it doesn't refresh
  ========================================================= */
  function onAdsClick(e) {
    const list = getList();
    if (!list) return;

    // 1) EDIT link: allow navigation to /items/<id>/edit/
    const editLink = e.target.closest("a.pill-blue");
    if (editLink && list.contains(editLink)) {
      // ما تمنعش التنقل — خلّي المتصفح يفتح الرابط
      return;
    }

    // 2) Actions buttons
    const btn = e.target.closest("[data-action]");
    if (!btn || !list.contains(btn)) return;

    e.preventDefault();
    e.stopPropagation();

    if (btn.classList.contains("pointer-events-none")) return;

    const action = btn.getAttribute("data-action");
    const id = Number(btn.getAttribute("data-id"));
    if (!id) return;

    const row = getAdRow(id);
    if (!row) return;

    const status = row.dataset.status || "";
    const featuredDays = Number(row.dataset.featuredDaysLeft || "0");
    const last = row.dataset.lastRepublish || "";

    if (action === "delete") {
      openDeleteModalForAd(id);
      return;
    }

    if (action === "highlight") {
      if (status !== "active") return;

      let daysLeft = featuredDays;
      if (!daysLeft && row.dataset.featuredExpiresAt) {
        daysLeft = calcDaysLeftFromNowISO(row.dataset.featuredExpiresAt);
        row.dataset.featuredDaysLeft = String(daysLeft);
      }
      if (daysLeft > 0) return;

      openHighlightModalForAd(id);
      return;
    }

    if (action === "republish") {
      if (status !== "active") return;

      const check = canRepublishWithCost(last);
      if (check.ok) {
        // ✅ call backend anyway (free republish)
        const listingId = Number(row.dataset.listingId || id);
        callBackend(`/listing/${listingId}/republish/`, {});
        doRepublishAdUI(id, true);
      } else {
        openRepublishConfirmModalForAd(id, check.cost);
      }
      return;
    }
  }

  /* =========================================================
     ✅ Init + backdrop closes
  ========================================================= */
  function wireBackdropClose() {
    document.getElementById("deleteAdModal")?.addEventListener("click", (e) => {
      if (e.target.id === "deleteAdModal") window.closeDeleteModal();
    });

    const rep = document.getElementById("republishConfirmModal");
    if (rep) {
      rep.addEventListener("click", (e) => {
        if (e.target === rep) window.closeRepublishConfirmModal();
      });
    }

    document.getElementById("highlightModal")?.addEventListener("click", (e) => {
      if (e.target.id === "highlightModal") window.closeHighlightModal();
    });
  }

  function init() {
    updateCount();
    enableEditDeleteAlways();
    wireDeleteReasonChange();
    setDeleteReasons();
    updateBalance();
    renderTransactions();
    wireBackdropClose();

    ["deleteAdModal", "highlightModal", "successModal", "republishConfirmModal", "noPointsModal"].forEach(mustEl);
  }

  document.addEventListener("DOMContentLoaded", () => {
    // delegated click so it works even if tab renders later
    document.addEventListener("click", onAdsClick, true);

    init();

    // retry init for lazy tabs
    let tries = 0;
    const t = setInterval(() => {
      tries += 1;
      if (getList() && getCountEl()) {
        init();
        clearInterval(t);
      }
      if (tries >= 30) clearInterval(t);
    }, 100);
  });
})();
