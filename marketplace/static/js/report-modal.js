console.log("✅ report-modal.js loaded");

(function () {
  const modal = document.getElementById("reportModal");
  if (!modal) return;

  const openBtn = document.getElementById("openReportModalBtn");
  const closeBtn = document.getElementById("closeReportModal");
  const form = document.getElementById("reportForm");

  const reasonBtn = document.getElementById("reportReasonBtn");
  const reasonMenu = document.getElementById("reportReasonMenu");
  const reasonText = document.getElementById("reportReasonText");
  const reasonInput = document.getElementById("reportReason");
  const reasonChevron = document.getElementById("reportReasonChevron");
  const reasonError = document.getElementById("reportReasonError");

  /* =========================
     Helpers
  ========================= */
  function openModal() {
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("overflow-hidden");
  }

  function closeModal() {
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("overflow-hidden");
    closeReasonMenu();
    clearErrors();
  }

  function openReasonMenu() {
    reasonMenu.classList.remove("hidden");
    reasonChevron.classList.add("rotate-180");
  }

  function closeReasonMenu() {
    reasonMenu.classList.add("hidden");
    reasonChevron.classList.remove("rotate-180");
  }

  function clearErrors() {
    if (reasonError) reasonError.classList.add("invisible");
  }

  // ✅ added (minimal)
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  /* =========================
     Open / Close modal
  ========================= */
  if (openBtn) {
    openBtn.addEventListener("click", (e) => {
      e.preventDefault();
      openModal();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", closeModal);
  }

  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  /* =========================
     Reason dropdown
  ========================= */
  if (reasonBtn) {
    reasonBtn.addEventListener("click", () => {
      if (reasonMenu.classList.contains("hidden")) {
        openReasonMenu();
      } else {
        closeReasonMenu();
      }
    });
  }

  if (reasonMenu) {
    reasonMenu.querySelectorAll("button[data-value]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const value = btn.dataset.value;
        reasonInput.value = value;
        reasonText.textContent = value;
        reasonText.classList.remove("text-gray-500");
        reasonText.classList.add("text-gray-900");
        clearErrors();
        closeReasonMenu();
      });
    });
  }

  document.addEventListener("click", (e) => {
    if (!reasonBtn.contains(e.target) && !reasonMenu.contains(e.target)) {
      closeReasonMenu();
    }
  });

  /* =========================
     Submit (AJAX -> backend)
  ========================= */
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (!reasonInput.value) {
        reasonError.classList.remove("invisible");
        return;
      }

      const details = document.getElementById("reportDetails")?.value || "";


      // from <form data-...>
      const targetKind = form.dataset.targetKind || "listing";
      const targetId = form.dataset.targetId || "";
      const listingType = form.dataset.listingType || "";

      const fd = new FormData();
      fd.append("target_kind", targetKind);
      fd.append("target_id", targetId);
      if (targetKind === "listing") fd.append("listing_type", listingType);

      fd.append("reason", reasonInput.value);
      fd.append("message", details);

      try {
        const res = await fetch("/reports/create/", {
          method: "POST",
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
          },
          body: fd,
        });

        const data = await res.json().catch(() => null);

        if (!res.ok || !data || data.ok !== true) {
          const msg = (data && data.message) ? data.message : "حدث خطأ أثناء إرسال البلاغ";
          if (window.showRuknAlert) showRuknAlert(msg);
          return; // keep modal open on error (no UX change)
        }

        if (window.showRuknAlert) {
          showRuknAlert(data.message || "✔ تم إرسال البلاغ بنجاح");
        }

        closeModal();
      } catch (err) {
        if (window.showRuknAlert) showRuknAlert("تعذر الاتصال بالخادم. حاول مرة أخرى.");
      }
    });
  }
})();
