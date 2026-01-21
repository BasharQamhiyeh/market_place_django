/* static/js/my_account/fav.js
   Favorites tab:
   - In favorites page: clicking heart opens confirm modal
   - Confirm => POST toggle_favorite then removes the card from DOM
*/

(function () {
  let pendingBtn = null;
  let pendingCard = null;
  let pendingUrl = null;

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  function qs(sel, root = document) { return root.querySelector(sel); }
  function qsa(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

  function openModal() {
    const modal = qs("#confirmFavModal");
    if (!modal) return;
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
  }

  function closeModal() {
    const modal = qs("#confirmFavModal");
    if (!modal) return;
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");

    pendingBtn = null;
    pendingCard = null;
    pendingUrl = null;
  }

  function updateCountAndEmpty() {
    const countEl = qs("#favCount");
    const list = qs("#favList");
    if (!countEl || !list) return;

    const cards = qsa('[data-fav-item="1"]', list);
    countEl.textContent = String(cards.length);

    const existingEmpty = qs("#favEmpty", list);
    if (cards.length === 0) {
      if (!existingEmpty) {
        list.innerHTML = `
          <div id="favEmpty" class="fav-empty">
            <svg class="fav-empty-ico" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1
                       a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21
                       l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8Z"
                    stroke="currentColor" stroke-width="2"/>
            </svg>
            <span>لا يوجد إعلانات في المفضلة حالياً</span>
          </div>
        `;
      }
    } else {
      if (existingEmpty) existingEmpty.remove();
    }
  }

  async function confirmRemove() {
    if (!pendingUrl || !pendingCard) return;

    const csrftoken = getCookie("csrftoken");

    try {
      const res = await fetch(pendingUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken || "",
          "X-Requested-With": "XMLHttpRequest"
        }
      });

      if (!res.ok) throw new Error("Bad response: " + res.status);

      // Remove from DOM (favorites tab only)
      pendingCard.remove();
      closeModal();
      updateCountAndEmpty();

      // If you already have a global success modal function, it will work:
      if (typeof window.openSuccessModal === "function") {
        window.openSuccessModal("تم حذف الإعلان من المفضلة بنجاح", "تم الحذف من المفضلة");
      }
    } catch (e) {
      // keep it simple (don’t silently fail)
      closeModal();
      console.error(e);
      alert("تعذر حذف الإعلان من المفضلة. حاول مرة أخرى.");
    }
  }

  function bindModalButtons() {
    const cancel = qs('[data-fav-cancel]');
    const confirm = qs('[data-fav-confirm]');
    const modal = qs("#confirmFavModal");

    if (cancel) cancel.addEventListener("click", closeModal);
    if (confirm) confirm.addEventListener("click", confirmRemove);

    // click on backdrop closes
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
      });
    }

    // Esc closes
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });
  }

  function bindFavHeartsInFavTab() {
    const tab = qs("#tab-fav");
    if (!tab) return;

    tab.addEventListener("click", (e) => {
      const btn = e.target.closest(".ad-fav-btn[data-fav-btn='1']");
      if (!btn) return;

      // In favorites tab: we DON’T toggle immediately. Confirm first.
      e.preventDefault();
      e.stopPropagation();

      pendingBtn = btn;
      pendingUrl = btn.getAttribute("data-url") || null;

      // card wrapper (your cell) or the article itself
      pendingCard = btn.closest('[data-fav-item="1"]') || btn.closest("article");

      // If no URL (guest), just ignore
      if (!pendingUrl) return;

      openModal();
    });
  }

  window.addEventListener("load", () => {
    bindModalButtons();
    bindFavHeartsInFavTab();
    updateCountAndEmpty();
  });
})();
