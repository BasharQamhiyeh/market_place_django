/* =========================
   delete-modal.js (Listing delete API)
   - Calls: POST /listing/<id>/delete/  (delete_listing_api)
   - Redirect from JS:
       item   -> /my-account/#tab-ads
       request-> /my-account/#tab-requests
   - Different reason lists per kind (item vs request)
========================= */

(() => {
  "use strict";

  const ROOT = document.documentElement;
  if (ROOT.dataset.deleteModalInit === "1") return;
  ROOT.dataset.deleteModalInit = "1";

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  function openModal(modal) {
    modal.classList.remove("hidden");
    modal.classList.add("flex");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("overflow-hidden");

    const first =
      modal.querySelector("[data-delete-reason]") ||
      modal.querySelector("button, [href], input, select, textarea");
    first?.focus?.();
  }

  function closeModal(modal) {
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("overflow-hidden");
  }

  function redirectAfterDelete(modal) {
    const kind = (modal.dataset.deleteKind || "item").toLowerCase();
    window.location.href = kind === "request" ? "/my-account/#tab-requests" : "/my-account/#tab-ads";
  }

  function setReasonsForKind(modal) {
    const sel = modal.querySelector("[data-delete-reason]");
    if (!sel) return;

    const kind = (modal.dataset.deleteKind || "item").toLowerCase();

    const reasonsItem = [
      { value: "sold_in", label: "تم البيع خلال منصة ركن" },
      { value: "sold_out", label: "تم البيع خارج منصة ركن" },
      { value: "republish", label: "أريد إعادة نشره لاحقاً" },
      { value: "issue", label: "مشكلة في الإعلان" },
      { value: "other", label: "سبب آخر…" },
    ];

    const reasonsRequest = [
      { value: "found", label: "تم العثور على المطلوب" },
      { value: "changed", label: "تغيّرت رغبتي / لم أعد بحاجة" },
      { value: "republish", label: "سأعيد نشر الطلب لاحقاً" },
      { value: "issue", label: "مشكلة في الطلب" },
      { value: "other", label: "سبب آخر…" },
    ];

    const reasons = kind === "request" ? reasonsRequest : reasonsItem;

    sel.innerHTML =
      `<option value="">— اختر سبب الحذف —</option>` +
      reasons.map((r) => `<option value="${r.value}">${r.label}</option>`).join("");
  }

  function resetModal(modal) {
    const reasonSel = modal.querySelector("[data-delete-reason]");
    const otherTa = modal.querySelector("[data-delete-other]");
    const errEl = modal.querySelector("[data-delete-error]");
    const confirmBtn = modal.querySelector("[data-delete-confirm]");

    // ✅ fill reasons every open (depends on delete_kind)
    setReasonsForKind(modal);

    errEl?.classList.add("hidden");
    if (reasonSel) reasonSel.value = "";
    if (otherTa) {
      otherTa.value = "";
      otherTa.classList.add("hidden");
    }
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.classList.remove("opacity-70", "cursor-not-allowed");
    }
  }

  function bindModal(modal) {
    const reasonSel = modal.querySelector("[data-delete-reason]");
    const otherTa = modal.querySelector("[data-delete-other]");
    const errEl = modal.querySelector("[data-delete-error]");
    const confirmBtn = modal.querySelector("[data-delete-confirm]");
    const cancelBtn = modal.querySelector("[data-delete-cancel]");

    if (!reasonSel || !confirmBtn || !cancelBtn) return;

    // show/hide "other"
    reasonSel.addEventListener("change", () => {
      errEl?.classList.add("hidden");
      if (!otherTa) return;
      if (reasonSel.value === "other") otherTa.classList.remove("hidden");
      else {
        otherTa.classList.add("hidden");
        otherTa.value = "";
      }
    });

    // cancel
    cancelBtn.addEventListener("click", (e) => {
      e.preventDefault();
      closeModal(modal);
    });

    // click outside
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal(modal);
    });

    // ESC
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !modal.classList.contains("hidden")) closeModal(modal);
    });

    // confirm delete
    confirmBtn.addEventListener("click", async (e) => {
      e.preventDefault();

      const url = modal.dataset.deleteUrl || "";
      if (!url) return;

      const reasonKey = (reasonSel.value || "").trim();
      if (!reasonKey) {
        errEl?.classList.remove("hidden");
        return;
      }
      errEl?.classList.add("hidden");

      const other = (otherTa && !otherTa.classList.contains("hidden")) ? otherTa.value.trim() : "";
      const finalReason =
        (reasonKey === "other" && other.length)
          ? other
          : (reasonSel?.options?.[reasonSel.selectedIndex]?.text || reasonKey);

      confirmBtn.disabled = true;
      confirmBtn.classList.add("opacity-70", "cursor-not-allowed");

      try {
        const csrftoken = getCookie("csrftoken");

        const res = await fetch(url, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ reason: finalReason }),
        });

        const data = await res.json().catch(() => ({}));

        if (res.ok && data.ok === true) {
          closeModal(modal);
          redirectAfterDelete(modal);
          return;
        }

        window.showRuknAlert?.(data?.error || "⚠️ لم يتم الحذف");
      } catch (err) {
        window.showRuknAlert?.("⚠️ حدث خطأ أثناء الحذف");
      } finally {
        confirmBtn.disabled = false;
        confirmBtn.classList.remove("opacity-70", "cursor-not-allowed");
      }
    });
  }

  // bind all delete modals on page
  document.querySelectorAll("div[id]").forEach((m) => {
    if (m.querySelector("[data-delete-confirm]")) bindModal(m);
  });

  // global trigger
  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-delete-trigger='1']");
    if (!trigger) return;

    e.preventDefault();
    e.stopPropagation();

    const modalId = trigger.dataset.deleteModal;
    const url = trigger.dataset.deleteUrl;

    const modal = modalId ? document.getElementById(modalId) : null;
    if (!modal) return;

    if (url) modal.dataset.deleteUrl = url;

    resetModal(modal);
    openModal(modal);
  });
})();
