/* static/js/my_account/tabs.js
   ✅ Mockup tabs controller (mobile sticky buttons)
   ✅ Persists active tab on refresh (localStorage + hash)
   ✅ Lazy-load notifications only when tab opens
   ✅ Clears msgs deep-link (?tab=msgs&c=ID) when leaving msgs tab
   ✅ Supports #tab-info links and opens page from TOP
*/

(function () {
  "use strict";

  const btns = Array.from(document.querySelectorAll(".tab-btn"));
  if (!btns.length) return;

  const saveBtn = document.getElementById("saveBtn");

  const panes = ["info", "ads", "requests", "noti", "msgs", "fav", "wallet"];
  const STORAGE_KEY = "my_account_active_tab";

  function normalizeTabKey(v) {
    const key = (v || "").toString().trim();
    return panes.includes(key) ? key : "info";
  }

  function maybeLoadTabExtras(tabKey) {
    if (tabKey === "noti" && window.__ruknLoadNotiTab) {
      window.__ruknLoadNotiTab();
    }
  }

  function clearMsgsQueryParamsIfPresent() {
    try {
      const url = new URL(window.location.href);

      const hadTabMsgs = url.searchParams.get("tab") === "msgs";
      const hadC = url.searchParams.has("c");

      if (!hadTabMsgs && !hadC) return;

      if (hadTabMsgs) url.searchParams.delete("tab");
      if (hadC) url.searchParams.delete("c");

      const qs = url.searchParams.toString();
      const next = url.pathname + (qs ? "?" + qs : "") + (url.hash || "");
      history.replaceState(null, "", next);
    } catch (e) {}
  }

  function setActiveTab(tabKey, opts = {}) {
    const key = normalizeTabKey(tabKey);

    if (key !== "msgs") clearMsgsQueryParamsIfPresent();

    // buttons
    btns.forEach((b) => b.classList.toggle("active", b.dataset.tab === key));

    // panes
    panes.forEach((k) => {
      const el = document.getElementById("tab-" + k);
      if (!el) return;
      const isActive = k === key;
      el.classList.toggle("active", isActive);
      el.classList.toggle("hidden", !isActive);
    });

    // save button only in info
    if (saveBtn) {
      saveBtn.style.display = key === "info" ? "inline-flex" : "none";
    }

    if (!opts.skipStore) {
      try { localStorage.setItem(STORAGE_KEY, key); } catch (e) {}
    }

    // IMPORTANT: replaceState does NOT cause scroll-jump
    if (!opts.skipHash) {
      history.replaceState(null, "", "#tab-" + key);
    }

    maybeLoadTabExtras(key);

    if (opts.forceTop) {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => window.scrollTo(0, 0));
      });
    }
  }

  // bind click
  btns.forEach((btn) => {
    btn.addEventListener("click", () => {
      setActiveTab(btn.dataset.tab || "info");
    });
  });

  function readInitialTab() {
    // 0) forced from inline script (highest priority)
    if (window.__MYACCOUNT_FORCED_TAB) {
      const k = normalizeTabKey(window.__MYACCOUNT_FORCED_TAB);
      window.__MYACCOUNT_FORCED_TAB = null;
      return { key: k, forced: true };
    }

    // 1) from URL hash: #tab-noti OR #noti
    const h = (window.location.hash || "").replace("#", "").trim();
    if (h) {
      if (h.startsWith("tab-")) return { key: normalizeTabKey(h.slice(4)), forced: false };
      return { key: normalizeTabKey(h), forced: false };
    }

    // 2) from localStorage
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return { key: normalizeTabKey(saved), forced: false };
    } catch (e) {}

    // 3) from existing active button in HTML
    const initialFromDom = btns.find((b) => b.classList.contains("active"))?.dataset.tab;
    return { key: normalizeTabKey(initialFromDom || "info"), forced: false };
  }

  // initial
  const init = readInitialTab();
  setActiveTab(init.key, {
    skipStore: true,
    skipHash: false,   // restore #tab-... (no scroll jump)
    forceTop: init.forced
  });
})();
