// static/js/my_account/ads.js
(() => {
  const tab = document.getElementById("tab-ads");
  const list = document.getElementById("adsList");
  const count = document.getElementById("adsCount");
  if (!tab || !list || !count) return;

  let points = window.__pointsBalance ?? 80;

  let adToDelete = null;
  let highlightTargetId = null;
  let republishTargetId = null;
  let republishCost = 0;

  function getAdRow(id) {
    return list.querySelector(`.ad-row[data-ad-id="${id}"]`);
  }

  function updateCount() {
    count.textContent = String(list.querySelectorAll(".ad-row").length);
  }

  function mustEl(id) {
    const el = document.getElementById(id);
    if (!el) {
      console.warn(`[my_account/ads] Missing element #${id} in DOM`);
    }
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

  // ---------- Success ----------
  function openSuccessModal(message, title = "تم التنفيذ بنجاح") {
    const msg = document.getElementById("successMsg");
    const ttl = document.getElementById("successTitle");
    if (msg) msg.innerText = message;
    if (ttl) ttl.innerText = title;

    // if modal doesn't exist, show something anyway
    if (!openModal("successModal")) alert(`${title}\n\n${message}`);
  }
  window.closeSuccessModal = () => closeModal("successModal");

  // ---------- No points ----------
  function showNoPointsModal() {
    if (!openModal("noPointsModal")) alert("❌ لا يوجد نقاط كافية");
  }
  window.closeNoPointsModal = () => closeModal("noPointsModal");

  // ---------- Highlight ----------
  function openHighlightModalForAd(id) {
    highlightTargetId = id;

    const bal = document.getElementById("highlightPointsBalance");
    const title = document.getElementById("highlightModalTitle");
    if (bal) bal.innerText = points;
    if (title) title.innerText = "⭐ تمييز الإعلان";

    if (!openModal("highlightModal")) {
      alert("highlightModal is missing in DOM. Add the modal HTML to base page.");
    }
  }
  window.closeHighlightModal = () => closeModal("highlightModal");

  // Called by highlight package buttons in the modal HTML: onclick="selectHighlightPackage(3,30)"
  window.selectHighlightPackage = (days, cost) => {
    if (!highlightTargetId) return;

    if (points < cost) {
      closeModal("highlightModal");
      showNoPointsModal();
      return;
    }

    points -= cost;

    const row = getAdRow(highlightTargetId);
    if (row) row.dataset.featuredDaysLeft = String(days);

    closeModal("highlightModal");
    openSuccessModal("تم تمييز الإعلان بنجاح!", "⭐ تم التمييز");
  };

  // ---------- Delete ----------
  function setDeleteReasons() {
    const select = document.getElementById("deleteReason");
    if (!select) return;

    const reasons = [
      { value:"sold_in", label:"تم البيع خلال منصة ركن" },
      { value:"sold_out", label:"تم البيع خارج منصة ركن" },
      { value:"republish", label:"أريد إعادة نشره لاحقاً" },
      { value:"issue", label:"مشكلة في الإعلان" },
      { value:"other", label:"سبب آخر…" }
    ];

    select.innerHTML =
      `<option value="">— اختر سبب الحذف —</option>` +
      reasons.map(r => `<option value="${r.value}">${r.label}</option>`).join("");
  }

  function openDeleteModalForAd(id) {
    adToDelete = id;

    // if modal missing -> fallback immediately
    if (!document.getElementById("deleteAdModal")) {
      alert("deleteAdModal is missing in DOM. Add the modal HTML to base page.");
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

  // wire reason change (only if modal exists)
  function wireDeleteReasonChange() {
    const select = document.getElementById("deleteReason");
    if (!select) return;
    select.addEventListener("change", () => {
      const other = document.getElementById("deleteReasonOther");
      const err = document.getElementById("deleteReasonError");
      if (err) err.classList.add("hidden");
      if (!other) return;
      if (select.value === "other") other.classList.remove("hidden");
      else { other.classList.add("hidden"); other.value = ""; }
    });
  }

  window.confirmDeleteAd = () => {
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

    if (adToDelete != null) {
      const row = getAdRow(adToDelete);
      if (row) row.remove();
      updateCount();
      openSuccessModal(`تم حذف الإعلان — السبب: ${finalReason}`, "✔️ تم الحذف");
    }

    closeModal("deleteAdModal");
    adToDelete = null;
  };

  // ---------- Republish ----------
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

  function openRepublishConfirmModalForAd(id, cost) {
    republishTargetId = id;
    republishCost = cost;

    const bal = document.getElementById("republishPointsBalance");
    if (bal) bal.innerText = points;

    const btn = document.getElementById("confirmRepublishBtn");
    if (btn) btn.onclick = () => confirmRepublishNow();

    if (!openModal("republishConfirmModal")) {
      alert("republishConfirmModal is missing in DOM.");
    }
  }

  window.closeRepublishConfirmModal = () => {
    closeModal("republishConfirmModal");
    republishTargetId = null;
    republishCost = 0;
  };

  function doRepublishAdUI(id, free) {
    const row = getAdRow(id);
    if (!row) return;

    const iso = new Date().toISOString().split("T")[0];
    row.dataset.lastRepublish = iso;

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

    points -= republishCost;
    closeModal("republishConfirmModal");
    doRepublishAdUI(republishTargetId, false);

    republishTargetId = null;
    republishCost = 0;
  }

  // ---------- Click handling ----------
  list.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;

    // IMPORTANT: prevent any weird default behaviors
    e.preventDefault();
    e.stopPropagation();

    const action = btn.getAttribute("data-action");
    const id = Number(btn.getAttribute("data-id"));
    if (!id) return;

    const row = getAdRow(id);
    const status = row?.dataset?.status || "";
    const featuredDays = Number(row?.dataset?.featuredDaysLeft || "0");

    // If button is disabled via CSS class, don't do anything
    if (btn.classList.contains("pointer-events-none")) return;

    if (action === "delete") {
      if (status === "pending") return;
      openDeleteModalForAd(id);
      return;
    }

    if (action === "highlight") {
      if (status !== "active") return;
      if (featuredDays > 0) return;
      openHighlightModalForAd(id);
      return;
    }

    if (action === "republish") {
      if (status === "pending" || status === "rejected") return;

      const last = row?.dataset?.lastRepublish || "";
      const check = canRepublishWithCost(last);

      if (check.ok) doRepublishAdUI(id, true);
      else openRepublishConfirmModalForAd(id, check.cost);
    }
  });

  // Init
  document.addEventListener("DOMContentLoaded", () => {
    updateCount();
    wireDeleteReasonChange();
    setDeleteReasons();

    // Quick diagnostics so you see missing parts immediately
    ["deleteAdModal", "highlightModal", "successModal", "republishConfirmModal"].forEach(mustEl);
  });
})();
