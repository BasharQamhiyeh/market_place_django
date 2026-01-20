/* static/js/my_account/noti.js
   ✅ Lazy load fragment when tab opens
   ✅ Apply mockup icons + badge colors based on kind/status
   ✅ Counts total/unread
   ✅ Mark single read + mark all read
*/

(function () {
  "use strict";

  let loaded = false;
  let loading = false;

  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function getCSRFToken() {
    return qs("input[name=csrfmiddlewaretoken]")?.value || "";
  }

  // ---------- Mockup icon SVGs (frontend decides) ----------
  function iconSvg(kind, status) {
    if (kind === "request") return `
      <svg class="noti-ic" viewBox="0 0 24 24" fill="none">
        <circle cx="9" cy="20" r="1.5" fill="currentColor"/>
        <circle cx="17" cy="20" r="1.5" fill="currentColor"/>
        <path d="M3 4h2l2.4 12h10.2l2-8H6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>`;

    if (kind === "ad") return `
      <svg class="noti-ic" viewBox="0 0 24 24" fill="none">
        <path d="M3 11v2a1 1 0 0 0 1 1h2l8 4V6l-8 4H4a1 1 0 0 0-1 1Z"
              stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        <path d="M14 6v12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>`;

    if (kind === "wallet") return `
      <svg class="noti-ic" viewBox="0 0 24 24" fill="none">
        <rect x="2" y="6" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"></rect>
        <path d="M16 12h4" stroke="currentColor" stroke-width="2"></path>
      </svg>`;

    if (kind === "fav") return `
      <svg class="noti-ic" viewBox="0 0 24 24" fill="none">
        <polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9"
                 stroke="currentColor" stroke-width="2" stroke-linejoin="round"></polygon>
      </svg>`;

    if (kind === "store_follow") return `
      <svg class="noti-ic" viewBox="0 0 24 24" fill="none">
        <path d="M3 9l1-5h16l1 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M5 9v10h14V9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M9 19v-6h6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>`;

    return `
      <svg class="noti-ic" viewBox="0 0 24 24" fill="none">
        <path d="M18 8a6 6 0 1 0-12 0c0 7-3 7-3 7h18s-3 0-3-7Z"
              stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0" stroke="currentColor" stroke-width="2"/>
      </svg>`;
  }

  // ---------- Mockup badge text + classes ----------
  function badgeInfo(kind, status) {
    // statuses (mockup)
    if (status === "pending") return { text: "قيد المراجعة", cls: "status-pending" };
    if (status === "approved") return { text: "مقبول", cls: "status-active" };
    if (status === "rejected") return { text: "مرفوض", cls: "status-rejected" };

    if (status === "featured_expired") return { text: "انتهى التمييز", cls: "status-featured" };

    if (status === "charged") return { text: "شحن", cls: "status-active" };
    if (status === "used") return { text: "خصم", cls: "status-rejected" };
    if (status === "reward") return { text: "مكافأة", cls: "status-active" };

    if (kind === "fav") return { text: "مفضلة", cls: "status-fav" };

    if (kind === "store_follow" && status === "followed") return { text: "متابعة", cls: "status-active" };
    if (kind === "store_follow" && status === "unfollowed") return { text: "إلغاء متابعة", cls: "status-unfollow" };

    if (kind === "system") return { text: "إشعار", cls: "status-system" };

    return { text: "", cls: "" };
  }

  // ---------- Apply UI to loaded HTML ----------
  function hydrateNotiUI(root) {
    const items = qsa(".timeline-item", root);

    items.forEach((row) => {
      const kind = row.dataset.kind || "system";
      const status = row.dataset.status || "";

      // icon
      const iconBox = qs(".noti-icon", row);
      if (iconBox) {
        iconBox.innerHTML = iconSvg(kind, status);
        row.classList.add("noti-kind-" + kind);
      }

      // badge near title
      const badgeEl = qs(".noti-badge", row);
      if (badgeEl) {
        const info = badgeInfo(kind, status);
        if (info.text) {
          badgeEl.textContent = info.text;
          badgeEl.className = "noti-badge status-badge " + info.cls;
        } else {
          badgeEl.className = "noti-badge";
          badgeEl.textContent = "";
        }
      }
    });

    // counts from hidden meta bar
    const meta = qs(".noti-meta-bar span", root);
    const total = meta ? parseInt(meta.dataset.total || "0", 10) : items.length;
    const unread = meta ? parseInt(meta.dataset.unread || "0", 10) : items.filter(i => i.classList.contains("is-unread")).length;

    const totalEl = document.getElementById("notiTotal");
    const unreadEl = document.getElementById("notiUnread");
    if (totalEl) totalEl.textContent = String(total);
    if (unreadEl) unreadEl.textContent = String(unread);

    // hide unread chip if 0
    const chip = qs(".noti-unread-chip");
    if (chip) chip.style.display = unread === 0 ? "none" : "inline-flex";

    bindRowActions();
  }

  function bindRowActions() {
    const tab = document.getElementById("notiTab");
    if (!tab) return;

    const readUrlTemplate = tab.dataset.readUrlTemplate || "";
    const csrf = getCSRFToken();

    qsa("[data-mark-read]", tab).forEach((btn) => {
      btn.addEventListener("click", async () => {
        const row = btn.closest(".timeline-item");
        if (!row) return;

        const id = row.dataset.nid;
        if (!id) return;

        const url = readUrlTemplate.replace("/0/", "/" + id + "/");
        try {
          const res = await fetch(url, {
            method: "POST",
            headers: { "X-CSRFToken": csrf },
          });
          if (!res.ok) return;

          // update UI locally
          row.classList.remove("is-unread");

          // swap button to "مقروء" pill
          const right = qs(".noti-right", row);
          if (right) {
            btn.remove();
            const pill = document.createElement("span");
            pill.className = "noti-read-pill";
            pill.textContent = "مقروء";
            right.prepend(pill);
          }

          // update unread count
          const unreadEl = document.getElementById("notiUnread");
          const chip = qs(".noti-unread-chip");
          if (unreadEl) {
            const v = Math.max(0, parseInt(unreadEl.textContent || "0", 10) - 1);
            unreadEl.textContent = String(v);
            if (chip) chip.style.display = v === 0 ? "none" : "inline-flex";
          }
        } catch (e) {}
      });
    });

    const markAllBtn = document.getElementById("notiMarkAllBtn");
    const readAllUrl = tab.dataset.readAllUrl || "";
    if (markAllBtn && readAllUrl) {
      markAllBtn.addEventListener("click", async () => {
        try {
          const res = await fetch(readAllUrl, {
            method: "POST",
            headers: { "X-CSRFToken": csrf },
          });
          if (!res.ok) return;

          // update all rows
          qsa(".timeline-item.is-unread", tab).forEach((row) => {
            row.classList.remove("is-unread");
            const btn = qs("[data-mark-read]", row);
            if (btn) btn.remove();
            const right = qs(".noti-right", row);
            if (right && !qs(".noti-read-pill", right)) {
              const pill = document.createElement("span");
              pill.className = "noti-read-pill";
              pill.textContent = "مقروء";
              right.prepend(pill);
            }
          });

          const unreadEl = document.getElementById("notiUnread");
          const chip = qs(".noti-unread-chip");
          if (unreadEl) unreadEl.textContent = "0";
          if (chip) chip.style.display = "none";
        } catch (e) {}
      });
    }
  }

  async function loadNoti() {
    if (loaded || loading) return;

    const tab = document.getElementById("notiTab");
    if (!tab) return;

    const url = tab.dataset.fragmentUrl;
    if (!url) return;

    loading = true;

    const loader = document.getElementById("notiLoader");
    const content = document.getElementById("notiContent");
    if (loader) loader.classList.remove("hidden");
    if (content) content.classList.add("hidden");

    try {
      const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
      const html = await res.text();

      if (content) {
        content.innerHTML = html;
        content.classList.remove("hidden");
      }
      if (loader) loader.classList.add("hidden");

      loaded = true;
      hydrateNotiUI(content || tab);
    } catch (e) {
      if (loader) loader.textContent = "حدث خطأ أثناء تحميل الإشعارات";
    } finally {
      loading = false;
    }
  }

  // expose for tabs.js
  window.__ruknLoadNotiTab = loadNoti;
})();
