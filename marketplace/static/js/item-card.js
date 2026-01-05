// static/js/item-card.js
(() => {
  "use strict";

  console.log("✅ item-card.js loaded");

  const ROOT = document.documentElement;
  if (ROOT.dataset.itemCardInit === "1") return;
  ROOT.dataset.itemCardInit = "1";

  function openLoginModal() {
    const m = document.getElementById("loginModal");
    if (m) m.classList.remove("hidden");
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  function toast(msg) {
    if (window.showRuknAlert) window.showRuknAlert(msg);
    else alert(msg);
  }

  function updateNavbarFavBadge(count) {
    const favBtn = document.getElementById("favBtn");
    if (!favBtn) return;

    const counter = favBtn.querySelector(".badge");
    if (counter) {
      if (count === 0) counter.remove();
      else counter.textContent = String(count);
      return;
    }

    if (count > 0) {
      const badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = String(count);
      favBtn.appendChild(badge);
    }
  }

  function applyFavUI(btn, isFav) {
    if (!btn) return;
    btn.classList.toggle("is-active", !!isFav);
    btn.dataset.favorited = isFav ? "1" : "0";
    btn.setAttribute("aria-pressed", isFav ? "true" : "false");
  }

  // ✅ IMPORTANT: init can be called multiple times (after HTMX / load more)
  function initFavButtons(scope = document) {
    const btns = scope.querySelectorAll('[data-fav-btn="1"]');

    btns.forEach((btn) => {
      // don’t re-init same button twice
      if (btn.dataset.favInit === "1") return;
      btn.dataset.favInit = "1";

      // Initialize visual state based on server-rendered data-favorited
      // If attribute is missing, do nothing.
      if (btn.dataset.favorited != null) {
        applyFavUI(btn, btn.dataset.favorited === "1");
      }
    });
  }

  // Run init AFTER DOM is ready (fixes script-in-head / timing)
  function boot() {
    initFavButtons(document);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }

  // Expose for your own "append" code if needed
  window.initItemCardFavs = initFavButtons;

  // ✅ HTMX support: when new HTML is swapped/added, re-init buttons inside it
  document.body.addEventListener("htmx:afterSwap", (e) => {
    if (e && e.target) initFavButtons(e.target);
  });
  document.body.addEventListener("htmx:afterSettle", (e) => {
    if (e && e.target) initFavButtons(e.target);
  });

  // card click -> details
  document.addEventListener("click", (e) => {
    const card = e.target.closest(".ad-card[data-href]");
    if (!card) return;
    if (e.target.closest("button,a,input,select,textarea,label")) return;
    const href = card.dataset.href;
    if (href) window.location.href = href;
  });

  // favorite toggle (delegated)
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest('[data-fav-btn="1"]');
    if (!btn) return;

    e.preventDefault();
    e.stopPropagation();

    // guest -> open login modal (heart stays visible)
    if (btn.dataset.guest === "1" || !btn.dataset.url) {
      openLoginModal();
      return;
    }

    // owner safety (only relevant if owner heart is shown)
    if (btn.dataset.isOwner === "1") {
      toast("⚠️ لا يمكنك إضافة إعلانك إلى المفضلة");
      return;
    }

    // lock
    if (btn.dataset.busy === "1") return;
    btn.dataset.busy = "1";
    btn.setAttribute("aria-busy", "true");

    const url = btn.dataset.url;
    const csrftoken = getCookie("csrftoken");

    // optimistic UI
    const wasFav = btn.dataset.favorited === "1" || btn.classList.contains("is-active");
    applyFavUI(btn, !wasFav);

    try {
      const res = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken,
        },
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        console.error("❌ fav failed:", res.status, data);

        if (res.status === 403) openLoginModal();
        if (data && data.error === "cannot_favorite_own_item") {
          toast("⚠️ لا يمكنك إضافة إعلانك إلى المفضلة");
        }

        // rollback
        applyFavUI(btn, wasFav);
        return;
      }

      const isFav = !!data.is_favorited;
      applyFavUI(btn, isFav);

      if (typeof data.favorite_count === "number") {
        updateNavbarFavBadge(data.favorite_count);
      }

      toast(isFav ? "✔ تمت الإضافة للمفضلة" : "✳️ تم الحذف من المفضلة");
    } catch (err) {
      console.error("❌ fav failed:", err);
      applyFavUI(btn, wasFav);
    } finally {
      btn.dataset.busy = "0";
      btn.removeAttribute("aria-busy");
    }
  });
})();
