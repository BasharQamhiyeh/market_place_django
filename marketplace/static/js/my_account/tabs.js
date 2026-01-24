/* static/js/my_account/tabs.js
   ✅ Mockup tabs controller (mobile sticky buttons)
   ✅ Persists active tab on refresh (localStorage + hash)
   ✅ Lazy-load notifications only when tab opens
   ✅ Clears msgs deep-link (?tab=msgs&c=ID) when leaving msgs tab
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
    // ✅ Lazy-load notifications
    if (tabKey === "noti" && window.__ruknLoadNotiTab) {
      window.__ruknLoadNotiTab();
    }
  }

  // ✅ NEW: remove deep-link params when user leaves msgs tab
  function clearMsgsQueryParamsIfPresent() {
    try {
      const url = new URL(window.location.href);

      const hadTabMsgs = url.searchParams.get("tab") === "msgs";
      const hadC = url.searchParams.has("c");

      if (!hadTabMsgs && !hadC) return;

      // remove these so msgs tab doesn't auto-open old chat
      if (hadTabMsgs) url.searchParams.delete("tab");
      if (hadC) url.searchParams.delete("c");

      const qs = url.searchParams.toString();
      const next = url.pathname + (qs ? "?" + qs : "") + (url.hash || "");
      history.replaceState(null, "", next);
    } catch (e) {
      // no-op: never break tabs if URL API not available
    }
  }

  function setActiveTab(tabKey, opts = {}) {
    const key = normalizeTabKey(tabKey);

    // ✅ if leaving msgs, clear ?tab=msgs&c=... from URL
    if (key !== "msgs") {
      clearMsgsQueryParamsIfPresent();
    }

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

    // persist selected tab (unless disabled)
    if (!opts.skipStore) {
      try {
        localStorage.setItem(STORAGE_KEY, key);
      } catch (e) {}
    }

    // optional: reflect in URL hash
    if (!opts.skipHash) {
      // keep it stable (no scroll jump if you don’t have anchors)
      history.replaceState(null, "", "#tab-" + key);
    }

    // run tab-specific behavior after it becomes active
    maybeLoadTabExtras(key);
  }

  // bind click
  btns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = normalizeTabKey(btn.dataset.tab || "info");
      setActiveTab(key);
    });
  });

  function readInitialTab() {
    // 1) from URL hash: #tab-noti OR #noti
    const h = (window.location.hash || "").replace("#", "").trim();
    if (h) {
      if (h.startsWith("tab-")) return normalizeTabKey(h.slice(4));
      return normalizeTabKey(h);
    }

    // 2) from localStorage
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return normalizeTabKey(saved);
    } catch (e) {}

    // 3) from existing active button in HTML
    const initialFromDom =
      btns.find((b) => b.classList.contains("active"))?.dataset.tab;
    return normalizeTabKey(initialFromDom || "info");
  }

  // initial
  setActiveTab(readInitialTab(), { skipStore: true, skipHash: true });
})();
