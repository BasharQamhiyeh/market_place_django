/* static/js/my_account/tabs.js
   ✅ Mockup tabs controller (mobile sticky buttons)
   ✅ Works with your new DOM:
      - buttons: .tab-btn[data-tab="info|ads|requests|noti|msgs|fav|wallet"]
      - panes:   #tab-info, #tab-ads, #tab-requests, #tab-noti, #tab-msgs, #tab-fav, #tab-wallet
   ✅ Also toggles Save button visibility (only in info tab)
*/

(function () {
  "use strict";

  const btns = Array.from(document.querySelectorAll(".tab-btn"));
  if (!btns.length) return;

  const saveBtn = document.getElementById("saveBtn");

  function setActiveTab(tabKey) {
    // buttons
    btns.forEach((b) => b.classList.toggle("active", b.dataset.tab === tabKey));

    // panes
    const panes = [
      "info",
      "ads",
      "requests",
      "noti",
      "msgs",
      "fav",
      "wallet",
    ];

    panes.forEach((k) => {
      const el = document.getElementById("tab-" + k);
      if (!el) return;

      const isActive = k === tabKey;
      el.classList.toggle("active", isActive);

      // mockup behavior: hide inactive panes
      el.classList.toggle("hidden", !isActive);
    });

    // save button only in info
    if (saveBtn) {
      saveBtn.style.display = tabKey === "info" ? "inline-flex" : "none";
    }
  }

  // bind
  btns.forEach((btn) => {
    btn.addEventListener("click", () => setActiveTab(btn.dataset.tab || "info"));
  });

  // initial state: respect existing "active" button if present
  const initial =
    btns.find((b) => b.classList.contains("active"))?.dataset.tab || "info";
  setActiveTab(initial);
})();
