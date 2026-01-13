// static/js/my_account/requests.js
(() => {
  const tab = document.getElementById("tab-requests");
  const list = document.getElementById("requestsList");
  const count = document.getElementById("requestsCount");
  if (!tab || !list || !count) return;

  let points = window.__pointsBalance ?? 80;

  let requestToDelete = null;
  let highlightTargetRequestId = null;
  let republishTargetRequestId = null;
  let republishCost = 0;

  const mustEl = (id) => {
    const el = document.getElementById(id);
    if (!el) console.warn(`[my_account/requests] Missing element #${id} in DOM`);
    return el;
  };

  function getRow(id) {
    return list.querySelector(`.request-row[data-req-id="${id}"]`);
  }

  function updateCount() {
    count.textContent = String(list.querySelectorAll(".request-row").length);
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
  window.closeSuccessModal = () => closeModal("successModal");

  // ---------- No points ----------
  function showNoPointsModal() {
    if (!openModal("noPointsModal")) alert("❌ لا يوجد نقاط كافية");
  }
  window.closeNoPointsModal = () => closeModal("noPointsModal");

  // ---------- Highlight (Requests) ----------
  function openHighlightModalForRequest(id) {
    highlightTargetRequestId = id;

    const bal = document.getElementById("highlightPointsBalance");
    const title = document.getElementById("highlightModalTitle");
    if (bal) bal.innerText = points;
    if (title) title.innerText = "⭐ تمييز الطلب";

    if (!openModal("highlightModal")) {
      alert("highlightModal is missing in DOM. Add the modal HTML to base page.");
    }
  }
  window.closeHighlightModal = () => closeModal("highlightModal");

  // Called by modal package buttons: onclick="selectHighlightPackage(7,50)"
  // IMPORTANT: We share this function name with ads.js — so we handle both safely:
  const prevSelectHighlight = window.selectHighlightPackage;
  window.selectHighlightPackage = (days, cost) => {
    // If requests highlight target exists -> handle here
    if (highlightTargetRequestId) {
      if (points < cost) {
        closeModal("highlightModal");
        showNoPointsModal();
        return;
      }

      points -= cost;

      const row = getRow(highlightTargetRequestId);
      if (row) row.dataset.featuredDaysLeft = String(days);

      closeModal("highlightModal");
      openSuccessModal("تم تمييز الطلب بنجاح!", "⭐ تم التمييز");

      highlightTargetRequestId = null;
      return;
    }

    // Otherwise fallback to whatever ads.js set (if any)
    if (typeof prevSelectHighlight === "function") {
      return prevSelectHighlight(days, cost);
    }
  };

  // ---------- Delete (Requests uses same delete modal) ----------
  function setDeleteReasonsForRequest() {
    const select = document.getElementById("deleteReason");
    if (!select) return;

    const reasons = [
      { value:"found", label:"تم العثور على المطلوب" },
      { value:"not_needed", label:"لم أعد بحاجة للطلب" },
      { value:"update", label:"أريد تعديل الطلب ونشره مجدداً" },
      { value:"issue", label:"مشكلة في الطلب" },
      { value:"other", label:"سبب آخر…" }
    ];

    select.innerHTML =
      `<option value="">— اختر سبب الحذف —</option>` +
      reasons.map(r => `<option value="${r.value}">${r.label}</option>`).join("");
  }

  function openDeleteModalForRequest(id) {
    requestToDelete = id;

    if (!document.getElementById("deleteAdModal")) {
      alert("deleteAdModal is missing in DOM. Add the modal HTML to base page.");
      return;
    }

    const t = document.getElementById("deleteTitle");
    const s = document.getElementById("deleteSubtitle");
    const b = document.getElementById("confirmDeleteBtn");

    if (t) t.textContent = "حذف طلب";
    if (s) s.textContent = "يرجى اختيار سبب حذف الطلب";
    if (b) b.textContent = "حذف الطلب";

    setDeleteReasonsForRequest();

    // reset UI
    const select = document.getElementById("deleteReason");
    const other = document.getElementById("deleteReasonOther");
    const err = document.getElementById("deleteReasonError");
    if (select) select.value = "";
    if (other) { other.value = ""; other.classList.add("hidden"); }
    if (err) err.classList.add("hidden");

    openModal("deleteAdModal");
  }

  // share existing close function
  const prevCloseDeleteModal = window.closeDeleteModal;
  window.closeDeleteModal = () => {
    closeModal("deleteAdModal");
    requestToDelete = null;
    if (typeof prevCloseDeleteModal === "function") prevCloseDeleteModal();
  };

  // reason change wiring (once)
  (function wireDeleteReasonChange() {
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
  })();

  // confirm delete (shared button in modal)
  const prevConfirmDeleteAd = window.confirmDeleteAd;
  window.confirmDeleteAd = () => {
    // If we are deleting a request -> handle here
    if (requestToDelete != null) {
      const select = document.getElementById("deleteReason");
      const other  = document.getElementById("deleteReasonOther");
      const err    = document.getElementById("deleteReasonError");

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

      const row = getRow(requestToDelete);
      if (row) row.remove();
      updateCount();

      closeModal("deleteAdModal");
      openSuccessModal(`تم حذف الطلب — السبب: ${finalReason}`, "✔️ تم الحذف");

      requestToDelete = null;
      return;
    }

    // otherwise fallback to ads behavior
    if (typeof prevConfirmDeleteAd === "function") return prevConfirmDeleteAd();
  };

  // ---------- Republish (Requests) ----------
  function parseISO(dateStr) {
    if (!dateStr) return null;
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? null : d;
  }
  function daysBetween(dateStr) {
    const d = parseISO(dateStr);
    if (!d) return 9999;
    const a = new Date(d); a.setHours(0,0,0,0);
    const b = new Date();  b.setHours(0,0,0,0);
    return Math.floor((b - a) / 86400000);
  }
  function canRepublishWithCost(lastRepublishAt) {
    const days = daysBetween(lastRepublishAt);
    if (days >= 7) return { ok: true, cost: 0 };
    return { ok: false, cost: 20 };
  }

  function openRepublishConfirmModalForRequest(id, cost) {
    republishTargetRequestId = id;
    republishCost = cost;

    const bal = document.getElementById("republishPointsBalance");
    if (bal) bal.innerText = points;

    const btn = document.getElementById("confirmRepublishBtn");
    if (btn) btn.onclick = () => confirmRepublishNow();

    if (!openModal("republishConfirmModal")) {
      alert("republishConfirmModal is missing in DOM.");
    }
  }

  // close is shared
  const prevCloseRepublish = window.closeRepublishConfirmModal;
  window.closeRepublishConfirmModal = () => {
    closeModal("republishConfirmModal");
    republishTargetRequestId = null;
    republishCost = 0;
    if (typeof prevCloseRepublish === "function") prevCloseRepublish();
  };

  function doRepublishRequestUI(id, free) {
    const row = getRow(id);
    if (!row) return;

    const iso = new Date().toISOString().split("T")[0];
    row.dataset.lastRepublish = iso;

    openSuccessModal(
      free ? "تم إعادة نشر الطلب مجاناً ✅" : `تمت إعادة النشر مقابل ${republishCost} نقطة ✅`,
      "🔄 تم إعادة النشر"
    );
  }

  function confirmRepublishNow() {
    if (!republishTargetRequestId) return;

    if (points < republishCost) {
      closeModal("republishConfirmModal");
      showNoPointsModal();
      return;
    }

    points -= republishCost;
    closeModal("republishConfirmModal");
    doRepublishRequestUI(republishTargetRequestId, false);

    republishTargetRequestId = null;
    republishCost = 0;
  }

  // ---------- Click handling ----------
  list.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;

    e.preventDefault();
    e.stopPropagation();

    const action = btn.getAttribute("data-action");
    const id = Number(btn.getAttribute("data-id"));
    if (!id) return;

    const row = getRow(id);
    const status = row?.dataset?.status || "";
    const featuredDays = Number(row?.dataset?.featuredDaysLeft || "0");

    if (btn.classList.contains("pointer-events-none")) return;

    if (action === "delete") {
      if (status === "pending") return;
      openDeleteModalForRequest(id);
      return;
    }

    if (action === "highlight") {
      if (status !== "active") return;
      if (featuredDays > 0) return;
      openHighlightModalForRequest(id);
      return;
    }

    if (action === "republish") {
      if (status !== "active") return;

      const last = row?.dataset?.lastRepublish || "";
      const check = canRepublishWithCost(last);

      if (check.ok) doRepublishRequestUI(id, true);
      else openRepublishConfirmModalForRequest(id, check.cost);
    }
  });

  document.addEventListener("DOMContentLoaded", () => {
    updateCount();
    // quick diagnostics
    ["deleteAdModal","highlightModal","successModal","republishConfirmModal","noPointsModal"].forEach(mustEl);
  });
})();
