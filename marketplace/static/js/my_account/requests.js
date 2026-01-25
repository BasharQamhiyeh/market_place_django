// static/js/my_account/requests.js
(() => {
  "use strict";

  const getTab = () => document.getElementById("tab-requests");
  const getList = () => document.getElementById("requestsList");
  const getCountEl = () => document.getElementById("requestsCount");

  function getPoints() {
    return Number(window.__pointsBalance ?? window.points ?? 80);
  }
  function setPoints(v) {
    const n = Number(v);
    window.__pointsBalance = n;
    window.points = n;
  }

  function getCSRFToken() {
    const m = document.cookie.match(/(^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[2]) : "";
  }

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
      if (!res.ok) console.warn("[requests] backend call failed:", url, res.status);
      return res;
    } catch (e) {
      console.warn("[requests] backend call error:", url, e);
      return null;
    }
  }

  // =========================================================
  // ✅ Deletion state
  // =========================================================
  let requestToDelete = null;    // request id (UI)
  let listingToDelete = null;    // ✅ listing id (backend delete)

  let highlightTargetRequestId = null;
  let republishTargetRequestId = null;
  let republishCost = 0;

  // Only handle selectHighlightPackage when highlight title == "تمييز الطلب"
  const isRequestHighlightModal = () => {
    const t = document.getElementById("highlightModalTitle");
    const txt = (t?.innerText || t?.textContent || "").trim();
    return txt.includes("تمييز الطلب");
  };

  const mustEl = (id) => {
    const el = document.getElementById(id);
    if (!el) console.warn(`[my_account/requests] Missing element #${id} in DOM`);
    return el;
  };

  function getRow(id) {
    const list = getList();
    if (!list) return null;
    return list.querySelector(`.request-row[data-req-id="${id}"]`);
  }

  function updateCount() {
    const list = getList();
    const count = getCountEl();
    if (!list || !count) return;
    count.textContent = String(list.querySelectorAll(".request-row[data-req-id]").length);
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

  // ---------- Close republish confirm ----------
  if (!window.closeRepublishConfirmModal) {
    window.closeRepublishConfirmModal = () => {
      closeModal("republishConfirmModal");
      republishTargetRequestId = null;
      republishCost = 0;
    };
  }

  /* =========================================================
     ✅ Highlight helpers
  ========================================================= */
  function calcDaysLeftFromNowISO(isoDate) {
    if (!isoDate) return 0;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const end = new Date(isoDate);
    end.setHours(0, 0, 0, 0);
    const diff = end - today;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    return days > 0 ? days : 0;
  }

  function ensureFeatureBadge(row, daysLeft) {
    const header = row.querySelector(".req-header");
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
    const btn = row.querySelector('[data-action="highlight"]');
    if (!btn) return;
    btn.classList.add("opacity-40", "cursor-not-allowed", "pointer-events-none");
  }

  /* =========================================================
     ✅ Republish helpers
  ========================================================= */
  function parseISO(dateStr) {
    if (!dateStr) return null;
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? null : d;
  }
  function daysBetween(dateStr) {
    const d = parseISO(dateStr);
    if (!d) return 9999;
    const a = new Date(d);
    a.setHours(0, 0, 0, 0);
    const b = new Date();
    b.setHours(0, 0, 0, 0);
    return Math.floor((b - a) / 86400000);
  }
  function canRepublishWithCost(lastRepublishAt) {
    const days = daysBetween(lastRepublishAt);
    if (days >= 7) return { ok: true, cost: 0, daysLeft: 0 };
    return { ok: false, cost: 20, daysLeft: 7 - days };
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
    const formatted = `${today.getFullYear()}/${String(today.getMonth() + 1).padStart(2, "0")}/${String(
      today.getDate()
    ).padStart(2, "0")}`;

    const metaRow =
      row.querySelector("div.flex.items-center.gap-4.text-sm.text-gray-500.mt-1.mb-2.flex-wrap") ||
      row.querySelector("div.flex.items-center.gap-4.text-sm");

    if (!metaRow) return;
    const inlineSpans = metaRow.querySelectorAll("span.inline-flex.items-center.gap-1 > span");
    if (inlineSpans && inlineSpans.length >= 2) inlineSpans[1].textContent = formatted;
  }

  function doRepublishRequestUI(id, free) {
    const row = getRow(id);
    if (!row) return;

    const iso = new Date().toISOString().split("T")[0];
    row.dataset.lastRepublish = iso;

    setRowActiveUI(row);
    updateRowDateToToday(row);

    openSuccessModal(
      free ? "تم إعادة نشر الطلب مجاناً ✅ (تجربة)" : `تمت إعادة النشر مقابل ${republishCost} نقطة ✅ (تجربة)`,
      "🔄 تم إعادة النشر"
    );
  }

  /* =========================================================
     ✅ Enable Edit/Delete always
  ========================================================= */
  function enableEditDeleteAlways() {
    const list = getList();
    if (!list) return;

    list.querySelectorAll(".request-row").forEach((row) => {
      const editLink = row.querySelector(".pill-blue");
      if (editLink) editLink.classList.remove("opacity-40", "pointer-events-none");

      const delBtn = row.querySelector('[data-action="delete"]');
      if (delBtn) delBtn.classList.remove("opacity-40", "pointer-events-none", "cursor-not-allowed");
    });
  }

  /* =========================================================
     ✅ Highlight modal open (preserve SVG)
  ========================================================= */
  function openHighlightModalForRequest(id) {
    highlightTargetRequestId = id;

    const bal = document.getElementById("highlightPointsBalance");
    const title = document.getElementById("highlightModalTitle");
    if (bal) bal.innerText = String(getPoints());

    if (title) {
      const svg = title.querySelector("svg");

      title.childNodes.forEach((node) => {
        if (node.nodeType === Node.TEXT_NODE) node.remove();
      });

      if (!svg && title.childNodes.length === 0) {
        title.textContent = "تمييز الطلب";
      } else {
        title.appendChild(document.createTextNode(" تمييز الطلب"));
      }

      title.classList.add("text-orange-600");
    }

    if (!openModal("highlightModal")) alert("highlightModal is missing in DOM.");
  }

  if (!window.closeHighlightModal) window.closeHighlightModal = () => closeModal("highlightModal");

  /* =========================================================
     ✅ selectHighlightPackage wrapper (Requests only)
  ========================================================= */
  const prevSelectHighlight = window.selectHighlightPackage;

  if (!window.__requestsSelectHighlightWrapped) {
    window.__requestsSelectHighlightWrapped = true;

    window.selectHighlightPackage = async (days, cost) => {
      if (!highlightTargetRequestId || !isRequestHighlightModal()) {
        if (typeof prevSelectHighlight === "function") return prevSelectHighlight(days, cost);
        return;
      }

      const row = getRow(highlightTargetRequestId);
      if (!row) {
        highlightTargetRequestId = null;
        closeModal("highlightModal");
        return;
      }

      const listingId = Number(row.dataset.listingId || 0);
      if (!listingId) {
        console.warn("[requests] Missing data-listing-id on request row", row);
        return;
      }

      const pointsNow = getPoints();
      const c = Number(cost || 0);
      if (c && pointsNow < c) {
        closeModal("highlightModal");
        showNoPointsModal();
        highlightTargetRequestId = null;
        return;
      }

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
          highlightTargetRequestId = null;
          return;
        }

        if (!res.ok) console.warn("[requests] feature call failed:", res.status, data);
      } catch (e) {
        console.warn("[requests] feature call error:", e);
      }

      if (data && data.ok) {
        if (typeof data.points_balance !== "undefined") setPoints(data.points_balance);

        const featuredUntilISO = data.featured_until ? String(data.featured_until).slice(0, 10) : "";
        if (featuredUntilISO) {
          row.dataset.featuredExpiresAt = featuredUntilISO;
          const daysLeft = calcDaysLeftFromNowISO(featuredUntilISO);
          row.dataset.featuredDaysLeft = String(daysLeft);
          ensureFeatureBadge(row, daysLeft);
        } else {
          row.dataset.featuredDaysLeft = String(Number(days));
          ensureFeatureBadge(row, Number(days));
        }

        disableHighlightButton(row);

        closeModal("highlightModal");
        openSuccessModal("تم تمييز الطلب بنجاح!", "⭐ تم التمييز");
        highlightTargetRequestId = null;
        return;
      }

      if (c) setPoints(pointsNow - c);
      row.dataset.featuredDaysLeft = String(Number(days));
      ensureFeatureBadge(row, Number(days));
      disableHighlightButton(row);

      closeModal("highlightModal");
      openSuccessModal("تم تمييز الطلب بنجاح! (تجربة)", "⭐ تم التمييز");
      highlightTargetRequestId = null;
    };
  }

  /* =========================================================
     ✅ Delete modal (shared modal)
  ========================================================= */
  function setDeleteReasonsForRequest() {
    const select = document.getElementById("deleteReason");
    if (!select) return;

    const reasons = [
      { value: "found", label: "تم العثور على المطلوب" },
      { value: "not_needed", label: "لم أعد بحاجة للطلب" },
      { value: "update", label: "أريد تعديل الطلب ونشره مجدداً" },
      { value: "issue", label: "مشكلة في الطلب" },
      { value: "other", label: "سبب آخر…" },
    ];

    select.innerHTML =
      `<option value="">— اختر سبب الحذف —</option>` +
      reasons.map((r) => `<option value="${r.value}">${r.label}</option>`).join("");
  }

  function wireDeleteReasonChangeOnce() {
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
      else {
        other.classList.add("hidden");
        other.value = "";
      }
    });
  }

  function openDeleteModalForRequest(id) {
    requestToDelete = id;

    const row = getRow(id);
    if (!row) {
      console.warn("[requests] Missing request row for delete", id);
      requestToDelete = null;
      return;
    }

    const listingId = Number(row.dataset.listingId || 0);
    if (!listingId) {
      console.warn("[requests] Missing data-listing-id on request row", row);
      requestToDelete = null;
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

    if (t) t.textContent = "حذف طلب";
    if (s) s.textContent = "يرجى اختيار سبب حذف الطلب";
    if (b) b.textContent = "حذف الطلب";

    setDeleteReasonsForRequest();

    const select = document.getElementById("deleteReason");
    const other = document.getElementById("deleteReasonOther");
    const err = document.getElementById("deleteReasonError");
    if (select) select.value = "";
    if (other) {
      other.value = "";
      other.classList.add("hidden");
    }
    if (err) err.classList.add("hidden");

    openModal("deleteAdModal");
  }

  // share confirmDeleteAd without breaking ads.js
  const prevConfirmDeleteAd = window.confirmDeleteAd;
  window.confirmDeleteAd = async () => {
    // ✅ Requests tab delete flow
    if (requestToDelete != null) {
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
        reason === "other" && otherTxt.length ? otherTxt : select?.options?.[select.selectedIndex]?.text || "";

      // ✅ IMPORTANT: delete by LISTING id (not request id)
      await callBackend(`/listing/${listingToDelete}/delete/`, { reason: finalReason });

      // ✅ IMPORTANT: remove row by LISTING id ONLY (no fallback to request id)
      const row = document.querySelector(`.request-row[data-listing-id="${listingToDelete}"]`);
      if (row) row.remove();

      updateCount();

      closeModal("deleteAdModal");
      openSuccessModal(`تم حذف الطلب — السبب: ${finalReason}`, "✔️ تم الحذف");

      listingToDelete = null;
      requestToDelete = null;
      return;
    }

    // Not a request delete -> let ads.js handle
    if (typeof prevConfirmDeleteAd === "function") return prevConfirmDeleteAd();
  };

  /* =========================================================
     ✅ Republish
  ========================================================= */
  function openRepublishConfirmModalForRequest(id, cost) {
    republishTargetRequestId = id;
    republishCost = Number(cost);

    const bal = document.getElementById("republishPointsBalance");
    if (bal) bal.innerText = String(getPoints());

    const btn = document.getElementById("confirmRepublishBtn");
    if (btn) btn.onclick = () => confirmRepublishNow();

    if (!openModal("republishConfirmModal")) alert("republishConfirmModal is missing in DOM.");
  }

  function confirmRepublishNow() {
    if (!republishTargetRequestId) return;

    const pointsNow = getPoints();
    if (pointsNow < republishCost) {
      closeModal("republishConfirmModal");
      showNoPointsModal();
      return;
    }

    callBackend(`/request/${republishTargetRequestId}/republish/`, {});
    setPoints(pointsNow - republishCost);

    closeModal("republishConfirmModal");
    doRepublishRequestUI(republishTargetRequestId, false);

    republishTargetRequestId = null;
    republishCost = 0;
  }

  /* =========================================================
     ✅ Backdrop close
  ========================================================= */
  function wireBackdropClose() {
    document.getElementById("deleteAdModal")?.addEventListener("click", (e) => {
      if (e.target.id === "deleteAdModal") {
        closeModal("deleteAdModal");
        requestToDelete = null;
        listingToDelete = null;
      }
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

  /* =========================================================
     ✅ Click handling (delegated)
  ========================================================= */
  function onRequestsClick(e) {
    const list = getList();
    if (!list) return;

    // 1) EDIT link => just navigate (GET)
    const editLink = e.target.closest("a.pill-blue");
    if (editLink && list.contains(editLink)) {
      // إذا الرابط مش موجود أو فاضي، لا تعمل شي
      const href = (editLink.getAttribute("href") || "").trim();
      if (!href || href === "#") return;

      // لا تمنع الافتراضي إلا إذا بدك تضمن التنقل بنفسك
      e.preventDefault();
      e.stopPropagation();

      window.location.href = href;  // ✅ يفتح صفحة التعديل (GET)
      return;
    }


    // 2) Action buttons
    const btn = e.target.closest("[data-action]");
    if (!btn || !list.contains(btn)) return;

    e.preventDefault();
    e.stopPropagation();

    if (btn.classList.contains("pointer-events-none")) return;

    const action = btn.getAttribute("data-action");
    const id = Number(btn.getAttribute("data-id"));
    if (!id) return;

    const row = getRow(id);
    if (!row) return;

    const status = row.dataset.status || "";
    const featuredDays = Number(row.dataset.featuredDaysLeft || "0");
    const last = row.dataset.lastRepublish || "";

    if (action === "delete") {
      if (status === "pending") return;
      openDeleteModalForRequest(id);
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

      openHighlightModalForRequest(id);
      return;
    }

    if (action === "republish") {
      if (status !== "active") return;

      const check = canRepublishWithCost(last);
      if (check.ok) {
        callBackend(`/request/${id}/republish/`, {});
        doRepublishRequestUI(id, true);
      } else {
        openRepublishConfirmModalForRequest(id, check.cost);
      }
    }
  }

  function init() {
    updateCount();
    enableEditDeleteAlways();
    wireDeleteReasonChangeOnce();
    wireBackdropClose();

    ["deleteAdModal", "highlightModal", "successModal", "republishConfirmModal", "noPointsModal"].forEach(mustEl);
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.addEventListener("click", onRequestsClick, true);
    init();

    // retry init for lazy tab render
    let tries = 0;
    const t = setInterval(() => {
      tries += 1;
      if (getList() && getCountEl() && getTab()) {
        init();
        clearInterval(t);
      }
      if (tries >= 30) clearInterval(t);
    }, 100);
  });
})();
