// static/js/report-modal.js
document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("reportModal");
  const openBtn = document.getElementById("openReportModalBtn");
  const closeBtn = document.getElementById("closeReportModal");
  const form = document.getElementById("reportForm");

  if (!modal || !openBtn || !form) return;

  const reasonBtn = document.getElementById("reportReasonBtn");
  const reasonMenu = document.getElementById("reportReasonMenu");
  const reasonText = document.getElementById("reportReasonText");
  const reasonInput = document.getElementById("reportReason");
  const reasonError = document.getElementById("reportReasonError");
  const formError = document.getElementById("reportFormError");
  const details = document.getElementById("reportDetails");
  const submitBtn = form.querySelector('button[type="submit"]');

  // ✅ hidden inputs that backend expects
  const targetKindInput = document.getElementById("reportTargetKind");
  const targetIdInput = document.getElementById("reportTargetId");
  const listingTypeInput = document.getElementById("reportListingType");

  // ----------------------------
  // Kind-aware messages (item/request)
  // ----------------------------
  function getReportKind() {
    return (modal.getAttribute("data-report-kind") || "item").toLowerCase(); // "item" or "request"
  }

  function ownMessage() {
    return getReportKind() === "request"
      ? "هذا طلبك ولا يمكنك الإبلاغ عنه."
      : "هذا إعلانك ولا يمكنك الإبلاغ عنه.";
  }

  function alreadyMessage() {
    return getReportKind() === "request"
      ? "سبق أن قمت بالإبلاغ عن هذا الطلب."
      : "سبق أن قمت بالإبلاغ عن هذا الإعلان.";
  }

  function normalizeServerMessage(msg) {
    // if backend returns generic text, convert it to correct kind text
    if (!msg) return msg;

    // duplicate (generic)
    if (msg.includes("سبق") && (msg.includes("المحتوى") || msg.includes("هذا المحتوى"))) {
      return alreadyMessage();
    }

    // own listing (generic)
    if (msg.includes("لا يمكنك") && (msg.includes("المحتوى") || msg.includes("هذا المحتوى"))) {
      return ownMessage();
    }

    return msg;
  }

  function showModal() {
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function hideModal() {
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    closeReasonMenu();
    clearErrors();
  }

  function clearErrors() {
    if (formError) {
      formError.classList.add("hidden");
      formError.textContent = "";
    }
    if (reasonError) {
      reasonError.classList.add("invisible");
      reasonError.classList.remove("visible");
    }
    if (reasonBtn) reasonBtn.classList.remove("error-border");
  }

  function showFormError(msg) {
    if (!formError) return;
    formError.textContent = "⚠️ " + msg;
    formError.classList.remove("hidden");
  }

  function openReasonMenu() {
    if (!reasonMenu) return;
    reasonMenu.classList.remove("hidden");
    const chevron = document.getElementById("reportReasonChevron");
    if (chevron) chevron.style.transform = "rotate(180deg)";
  }

  function closeReasonMenu() {
    if (!reasonMenu) return;
    reasonMenu.classList.add("hidden");
    const chevron = document.getElementById("reportReasonChevron");
    if (chevron) chevron.style.transform = "";
  }

  function setLockedUI(isLocked, message) {
    if (isLocked) {
      showFormError(message || alreadyMessage());
      if (submitBtn) submitBtn.disabled = true;
      if (reasonBtn) reasonBtn.disabled = true;
      if (details) details.disabled = true;

      if (submitBtn) submitBtn.classList.add("opacity-60", "cursor-not-allowed");
      if (reasonBtn) reasonBtn.classList.add("opacity-60", "cursor-not-allowed");
      if (details) details.classList.add("opacity-60", "cursor-not-allowed");

      closeReasonMenu();
    } else {
      if (submitBtn) submitBtn.disabled = false;
      if (reasonBtn) reasonBtn.disabled = false;
      if (details) details.disabled = false;

      if (submitBtn) submitBtn.classList.remove("opacity-60", "cursor-not-allowed");
      if (reasonBtn) reasonBtn.classList.remove("opacity-60", "cursor-not-allowed");
      if (details) details.classList.remove("opacity-60", "cursor-not-allowed");
    }
  }

  function resetFormUI() {
    clearErrors();
    if (reasonInput) reasonInput.value = "";
    if (reasonText) reasonText.textContent = "اختر سبب الإبلاغ";
    if (details) details.value = "";
  }

  // ✅ Always sync hidden inputs from data-attrs
  function syncTargetHiddenInputs() {
    const tk = form.getAttribute("data-target-kind") || "";
    const tid = form.getAttribute("data-target-id") || "";
    const lt = form.getAttribute("data-listing-type") || "";

    if (targetKindInput) targetKindInput.value = tk;
    if (targetIdInput) targetIdInput.value = tid;
    if (listingTypeInput) listingTypeInput.value = lt;
  }

  // ---------- OPEN BUTTON ----------
  openBtn.addEventListener("click", () => {
    const isAuth = openBtn.getAttribute("data-auth") === "1";

    if (!isAuth) {
      const loginModalId = openBtn.getAttribute("data-login-modal");
      const loginModal = loginModalId ? document.getElementById(loginModalId) : null;
      if (loginModal) loginModal.classList.remove("hidden");
      return;
    }

    resetFormUI();
    syncTargetHiddenInputs();
    showModal();

    const isOwn = modal.getAttribute("data-own-listing") === "1";
    const already = modal.getAttribute("data-reported-already") === "1";

    if (isOwn) {
      setLockedUI(true, ownMessage());
    } else if (already) {
      setLockedUI(true, alreadyMessage());
    } else {
      setLockedUI(false);
    }
  });

  // ---------- CLOSE ----------
  if (closeBtn) closeBtn.addEventListener("click", hideModal);

  modal.addEventListener("click", (e) => {
    if (e.target === modal) hideModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.classList.contains("hidden")) hideModal();
  });

  // ---------- REASON DROPDOWN ----------
  if (reasonBtn) {
    reasonBtn.addEventListener("click", () => {
      const locked = modal.getAttribute("data-reported-already") === "1";
      const isOwn = modal.getAttribute("data-own-listing") === "1";
      if (locked || isOwn) return;

      if (reasonMenu && reasonMenu.classList.contains("hidden")) openReasonMenu();
      else closeReasonMenu();
    });
  }

  if (reasonMenu) {
    reasonMenu.querySelectorAll("button[data-value]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const val = btn.getAttribute("data-value") || "";
        if (reasonInput) reasonInput.value = val;
        if (reasonText) reasonText.textContent = val;
        closeReasonMenu();

        if (reasonError) {
          reasonError.classList.add("invisible");
          reasonError.classList.remove("visible");
        }
        if (reasonBtn) reasonBtn.classList.remove("error-border");
      });
    });
  }

  document.addEventListener("click", (e) => {
    if (!reasonMenu || !reasonBtn) return;
    if (reasonMenu.classList.contains("hidden")) return;
    const inside = reasonMenu.contains(e.target) || reasonBtn.contains(e.target);
    if (!inside) closeReasonMenu();
  });

  // ---------- SUBMIT (AJAX) ----------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors();

    const isOwn = modal.getAttribute("data-own-listing") === "1";
    if (isOwn) {
      showFormError(ownMessage());
      return;
    }

    const locked = modal.getAttribute("data-reported-already") === "1";
    if (locked) {
      showFormError(alreadyMessage());
      return;
    }

    const reason = (reasonInput?.value || "").trim();
    if (!reason) {
      if (reasonError) {
        reasonError.classList.remove("invisible");
        reasonError.classList.add("visible");
      }
      if (reasonBtn) reasonBtn.classList.add("error-border");
      return;
    }

    syncTargetHiddenInputs();

    const url = form.getAttribute("action");
    if (!url) {
      showFormError("مسار الإبلاغ غير مضبوط (form action).");
      return;
    }

    const fd = new FormData(form);

    // backend expects message, textarea is details
    const detailsVal = (fd.get("details") || "").toString();
    fd.set("message", detailsVal);

    try {
      const resp = await fetch(url, {
        method: "POST",
        body: fd,
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok || !data.ok) {
        const msg = normalizeServerMessage(data.message) || "تعذر إرسال الإبلاغ.";
        showFormError(msg);

        // lock local state
        if (msg.includes("سبق")) {
          modal.setAttribute("data-reported-already", "1");
          setLockedUI(true, alreadyMessage());
        }
        if (msg.includes("إعلانك") || msg.includes("طلبك")) {
          modal.setAttribute("data-own-listing", "1");
          setLockedUI(true, ownMessage());
        }
        return;
      }

      hideModal();
      if (window.showRuknAlert) window.showRuknAlert(data.message || "✔ تم استلام الإبلاغ");

      modal.setAttribute("data-reported-already", "1");
    } catch (err) {
      showFormError("تعذر الاتصال بالخادم. حاول مرة أخرى.");
    }
  });
});
