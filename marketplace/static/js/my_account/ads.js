// static/js/my_account/ads.js
(() => {
  "use strict";

  const getList = () => document.getElementById("adsList");
  const getCountEl = () => document.getElementById("adsCount");

  /* =========================================================
     ✅ Wallet / Points
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

  function isFeaturedRow(row) {
    return Number(row?.dataset?.featuredDaysLeft || "0") > 0;
  }

  function isPendingRow(row) {
    return (row?.dataset?.status || "").toLowerCase() === "pending";
  }

  function isActiveRow(row) {
    return (row?.dataset?.status || "").toLowerCase() === "active";
  }

  function isRejectedRow(row) {
    return (row?.dataset?.status || "").toLowerCase() === "rejected";
  }

  /* =========================================================
     ✅ Success / No points
  ========================================================= */
  function openSuccessModal(message, title = "تم التنفيذ بنجاح") {
    const msg = document.getElementById("successMsg");
    const ttl = document.getElementById("successTitle");
    if (msg) msg.innerText = message;
    if (ttl) ttl.innerText = title;
    if (!openModal("successModal")) alert(`${title}\n\n${message}`);
  }
  if (!window.closeSuccessModal) window.closeSuccessModal = () => closeModal("successModal");

  function showNoPointsModal() {
    if (!openModal("noPointsModal")) alert("❌ لا يوجد نقاط كافية");
  }
  if (!window.closeNoPointsModal) window.closeNoPointsModal = () => closeModal("noPointsModal");
  window.openWalletTab = () => {
    closeModal("noPointsModal");
    document.querySelector('[data-tab="wallet"]')?.click();
  };

  /* =========================================================
     ✅ Cooldown
  ========================================================= */
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
     ✅ APPLY ACTION STATES - THE THREE RULES

     RULE 1: If pending → only edit & delete enabled
     RULE 2: If featured → NO actions allowed (all disabled)
     RULE 3: If active and not featured → all actions enabled
  ========================================================= */
  function applyActionStates() {
    const list = getList();
    if (!list) return;

    list.querySelectorAll(".ad-row").forEach((row) => {
      const status = (row.dataset.status || "").toLowerCase();
      const featured = isFeaturedRow(row);

      const editLink = row.querySelector('a[data-action="edit"]');
      const delBtn = row.querySelector('button[data-action="delete"]');
      const republishBtn = row.querySelector('button[data-action="republish"]');
      // Find highlight button - it might not have data-action if disabled in template
      const highlightBtn = row.querySelector('button[data-action="highlight"]') ||
                          Array.from(row.querySelectorAll('button')).find(btn => {
                            const text = (btn.textContent || '').trim();
                            return text === 'تمييز' || btn.classList.contains('pill-orange');
                          });

      // Reset all buttons to enabled state first
      [editLink, delBtn, republishBtn, highlightBtn].forEach(btn => {
        if (!btn) return;
        // IMPORTANT: Remove pointer-events-none so tooltips can work!
        btn.classList.remove("opacity-40", "cursor-not-allowed", "pointer-events-none");
        btn.removeAttribute("aria-disabled");
        btn.removeAttribute("title");

        // Remove any existing tooltip spans
        const existingTooltip = btn.querySelector('.tooltip-span');
        if (existingTooltip) existingTooltip.remove();

        // Remove relative and group classes if they were added
        btn.classList.remove("relative", "group");
      });

      // Ensure highlight button has proper data attributes
      if (highlightBtn && !highlightBtn.hasAttribute('data-action')) {
        highlightBtn.setAttribute('data-action', 'highlight');
        const adId = row.dataset.adId;
        if (adId) highlightBtn.setAttribute('data-id', adId);
      }

      // ========================================
      // RULE 2: If featured → disable ALL actions
      // ========================================
      if (featured) {
        if (editLink) {
          editLink.classList.add("opacity-40", "cursor-not-allowed", "relative", "group");
          editLink.setAttribute("aria-disabled", "true");
          editLink.setAttribute("title", "لا يمكنك تعديل الإعلان لأنه مميز");

          // Add tooltip span
          const tooltip = document.createElement("span");
          tooltip.className = "tooltip-span pointer-events-none absolute z-30 right-0 top-1/2 -translate-y-1/2 translate-x-full mr-2 hidden group-hover:block";
          tooltip.innerHTML = '<span class="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg whitespace-nowrap">لا يمكنك تعديل الإعلان لأنه مميز</span>';
          editLink.appendChild(tooltip);
        }

        if (delBtn) {
          delBtn.classList.add("opacity-40", "cursor-not-allowed", "relative", "group");
          delBtn.setAttribute("aria-disabled", "true");
          delBtn.setAttribute("title", "لا يمكنك حذف الإعلان لأنه مميز");

          const tooltip = document.createElement("span");
          tooltip.className = "tooltip-span pointer-events-none absolute z-30 right-0 top-1/2 -translate-y-1/2 translate-x-full mr-2 hidden group-hover:block";
          tooltip.innerHTML = '<span class="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg whitespace-nowrap">لا يمكنك حذف الإعلان لأنه مميز</span>';
          delBtn.appendChild(tooltip);
        }

        if (republishBtn) {
          republishBtn.classList.add("opacity-40", "cursor-not-allowed", "relative", "group");
          republishBtn.setAttribute("aria-disabled", "true");
          republishBtn.setAttribute("title", "لا يمكن إعادة نشر إعلان مميز");

          const tooltip = document.createElement("span");
          tooltip.className = "tooltip-span pointer-events-none absolute z-30 right-0 top-1/2 -translate-y-1/2 translate-x-full mr-2 hidden group-hover:block";
          tooltip.innerHTML = '<span class="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg whitespace-nowrap">لا يمكن إعادة نشر إعلان مميز</span>';
          republishBtn.appendChild(tooltip);
        }

        if (highlightBtn) {
          highlightBtn.classList.add("opacity-40", "cursor-not-allowed", "relative", "group");
          highlightBtn.setAttribute("aria-disabled", "true");
          highlightBtn.setAttribute("title", "الإعلان مميز بالفعل");

          const tooltip = document.createElement("span");
          tooltip.className = "tooltip-span pointer-events-none absolute z-30 right-0 top-1/2 -translate-y-1/2 translate-x-full mr-2 hidden group-hover:block";
          tooltip.innerHTML = '<span class="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg whitespace-nowrap">الإعلان مميز بالفعل</span>';
          highlightBtn.appendChild(tooltip);
        }
        return;
      }

      // ========================================
      // RULE 1: If pending → only edit & delete enabled
      // ========================================
      if (status === "pending") {
        if (republishBtn) {
          // Note: NO pointer-events-none so hover tooltip works!
          republishBtn.classList.add("opacity-40", "cursor-not-allowed", "relative", "group");
          republishBtn.setAttribute("aria-disabled", "true");
          republishBtn.setAttribute("title", "لا يمكن إعادة النشر أثناء المراجعة");

          const tooltip = document.createElement("span");
          tooltip.className = "tooltip-span pointer-events-none absolute z-30 right-0 top-1/2 -translate-y-1/2 translate-x-full mr-2 hidden group-hover:block";
          tooltip.innerHTML = '<span class="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg whitespace-nowrap">لا يمكن إعادة النشر أثناء المراجعة</span>';
          republishBtn.appendChild(tooltip);
        }

        if (highlightBtn) {
          // Note: NO pointer-events-none so hover tooltip works!
          highlightBtn.classList.add("opacity-40", "cursor-not-allowed", "relative", "group");
          highlightBtn.setAttribute("aria-disabled", "true");
          highlightBtn.setAttribute("title", "لا يمكن التمييز أثناء المراجعة");

          const tooltip = document.createElement("span");
          tooltip.className = "tooltip-span pointer-events-none absolute z-30 right-0 top-1/2 -translate-y-1/2 translate-x-full mr-2 hidden group-hover:block";
          tooltip.innerHTML = '<span class="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg whitespace-nowrap">لا يمكن التمييز أثناء المراجعة</span>';
          highlightBtn.appendChild(tooltip);
        }
        return;
      }

      // ========================================
      // If rejected → disable republish & highlight
      // ========================================
      if (status === "rejected") {
        if (republishBtn) {
          // Note: NO pointer-events-none so hover tooltip works!
          republishBtn.classList.add("opacity-40", "cursor-not-allowed", "relative", "group");
          republishBtn.setAttribute("aria-disabled", "true");
          republishBtn.setAttribute("title", "لا يمكن إعادة نشر إعلان مرفوض");

          const tooltip = document.createElement("span");
          tooltip.className = "tooltip-span pointer-events-none absolute z-30 right-0 top-1/2 -translate-y-1/2 translate-x-full mr-2 hidden group-hover:block";
          tooltip.innerHTML = '<span class="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg whitespace-nowrap">لا يمكن إعادة نشر إعلان مرفوض</span>';
          republishBtn.appendChild(tooltip);
        }

        if (highlightBtn) {
          // Note: NO pointer-events-none so hover tooltip works!
          highlightBtn.classList.add("opacity-40", "cursor-not-allowed", "relative", "group");
          highlightBtn.setAttribute("aria-disabled", "true");
          highlightBtn.setAttribute("title", "لا يمكن تمييز إعلان مرفوض");

          const tooltip = document.createElement("span");
          tooltip.className = "tooltip-span pointer-events-none absolute z-30 right-0 top-1/2 -translate-y-1/2 translate-x-full mr-2 hidden group-hover:block";
          tooltip.innerHTML = '<span class="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg whitespace-nowrap">لا يمكن تمييز إعلان مرفوض</span>';
          highlightBtn.appendChild(tooltip);
        }
        return;
      }

      // ========================================
      // RULE 3: If active and not featured → all actions enabled
      // (already reset above, nothing to do)
      // ========================================
    });
  }

  /* =========================================================
     ✅ Backend call helper
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
      if (!res.ok) console.warn("[ads] backend call failed:", url, res.status);
      return res;
    } catch (e) {
      console.warn("[ads] backend call error:", url, e);
      return null;
    }
  }

  /* =========================================================
     ✅ Delete Modal
  ========================================================= */
  let adToDelete = null;
  let listingToDelete = null;

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

    const row = getAdRow(id);
    if (!row) {
      console.warn("[ads] Missing ad row for delete", id);
      adToDelete = null;
      return;
    }

    const listingId = Number(row.dataset.listingId || 0);
    if (!listingId) {
      console.warn("[ads] Missing data-listing-id on ad row", row);
      adToDelete = null;
      return;
    }

    listingToDelete = listingId;

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
    listingToDelete = null;
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

    // Call backend to delete the listing
    if (listingToDelete) {
      await callBackend(`/listing/${listingToDelete}/delete/`, { reason: finalReason });
    }

    // Remove the row from UI
    const row = document.querySelector(`.ad-row[data-listing-id="${listingToDelete}"]`);
    if (row) row.remove();

    updateCount();

    closeModal("deleteAdModal");
    openSuccessModal(`تم حذف الإعلان — السبب: ${finalReason}`, "✔️ تم الحذف");

    adToDelete = null;
    listingToDelete = null;
  };

  /* =========================================================
     ✅ Highlight
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

      if (data && data.ok === false && data.error === "not_enough_points") {
        closeModal("highlightModal");
        showNoPointsModal();
        highlightTargetId = null;
        return;
      }

      if (!res.ok) console.warn("[ads] feature call failed:", res.status);
    } catch (e) {
      console.warn("[ads] feature call error:", e);
    }

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

      applyActionStates(); // Re-apply rules after featuring
      closeModal("highlightModal");
      openSuccessModal("تم تمييز الإعلان بنجاح!", "⭐ تم التمييز");
      highlightTargetId = null;
      return;
    }

    // Fallback (mock mode)
    row.dataset.featuredDaysLeft = String(days);
    ensureFeatureBadge(row, Number(days));
    applyActionStates(); // Re-apply rules
    closeModal("highlightModal");
    openSuccessModal("تم تمييز الإعلان بنجاح! (تجربة)", "⭐ تم التمييز");
    highlightTargetId = null;
  };

  /* =========================================================
     ✅ Republish
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

    if (!openModal("republishConfirmModal")) alert("republishConfirmModal is missing in DOM.");
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

    const metaRow =
      row.querySelector("div.flex.items-center.gap-4.text-sm.text-gray-500.mt-1.mb-2.flex-wrap") ||
      row.querySelector("div.flex.items-center.gap-4.text-sm");

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
    applyActionStates(); // Re-apply rules after republish

    openSuccessModal(
      free ? "تم إعادة نشر الإعلان مجاناً ✅" : `تمت إعادة النشر مقابل ${republishCost} نقطة ✅`,
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
     ✅ CLICK HANDLING - Enforce the three rules
  ========================================================= */
  function onAdsClick(e) {
    const list = getList();
    if (!list) return;

    // Handle EDIT link
    const edit = e.target.closest('a[data-action="edit"]');
    if (edit && list.contains(edit)) {
      const id = Number(edit.getAttribute("data-id"));
      const row = getAdRow(id);

      // Check if disabled
      if (edit.getAttribute("aria-disabled") === "true") {
        e.preventDefault();
        e.stopPropagation();
        return;
      }

      // RULE 2: Block if featured
      if (isFeaturedRow(row)) {
        e.preventDefault();
        e.stopPropagation();
        return;
      }

      // RULE 1: Allow if pending (edit is allowed)
      // RULE 3: Allow if active and not featured
      // (let it navigate normally)
      return;
    }

    // Handle action buttons
    const btn = e.target.closest("[data-action]");
    if (!btn || !list.contains(btn)) return;

    const action = btn.getAttribute("data-action");
    const id = Number(btn.getAttribute("data-id"));
    if (!id) return;

    // Check if button is disabled (aria-disabled instead of pointer-events-none)
    if (btn.getAttribute("aria-disabled") === "true") {
      e.preventDefault();
      e.stopPropagation();
      return;
    }

    const row = getAdRow(id);
    if (!row) return;

    const status = (row.dataset.status || "").toLowerCase();
    const featured = isFeaturedRow(row);
    const last = row.dataset.lastRepublish || "";

    // ========================================
    // DELETE button
    // ========================================
    if (action === "delete") {
      e.preventDefault();
      e.stopPropagation();

      // RULE 2: Block if featured
      if (featured) return;

      // RULE 1: Allow if pending
      // RULE 3: Allow if active and not featured

      openDeleteModalForAd(id);
      return;
    }

    // ========================================
    // HIGHLIGHT button
    // ========================================
    if (action === "highlight") {
      e.preventDefault();
      e.stopPropagation();

      // RULE 2: Block if featured
      if (featured) return;

      // RULE 1: Block if pending (highlight not allowed)
      if (status === "pending") return;

      // Only allow if active
      if (status !== "active") return;

      // Check if already featured (double check)
      let daysLeft = Number(row.dataset.featuredDaysLeft || "0");
      if (!daysLeft && row.dataset.featuredExpiresAt) {
        daysLeft = calcDaysLeftFromNowISO(row.dataset.featuredExpiresAt);
        row.dataset.featuredDaysLeft = String(daysLeft);
      }
      if (daysLeft > 0) return;

      openHighlightModalForAd(id);
      return;
    }

    // ========================================
    // REPUBLISH button
    // ========================================
    if (action === "republish") {
      e.preventDefault();
      e.stopPropagation();

      // RULE 2: Block if featured
      if (featured) return;

      // RULE 1: Block if pending (republish not allowed)
      if (status === "pending") return;

      // Only allow if active
      if (status !== "active") return;

      const check = canRepublishWithCost(last);
      if (check.ok) {
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
    applyActionStates(); // ✅ Apply the three rules on init
    wireDeleteReasonChange();
    updateBalance();
    renderTransactions();
    wireBackdropClose();

    ["deleteAdModal", "highlightModal", "successModal", "republishConfirmModal", "noPointsModal"].forEach(mustEl);
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.addEventListener("click", onAdsClick, true);

    init();

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