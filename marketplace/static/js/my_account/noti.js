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

  // ---------- Lucide-based icon data — mirrors base.js getNotifIconData ----------
  function getNotifIconData(kind, status) {
    if (kind === "ad") {
      if (status === "pending")  return { icon: "clock",        bg: "#fff7ed", border: "#fdba74", color: "#c2410c" };
      if (status === "approved") return { icon: "check-circle", bg: "#dcfce7", border: "#86efac", color: "#15803d" };
      if (status === "rejected") return { icon: "x-circle",     bg: "#fee2e2", border: "#fca5a5", color: "#b91c1c" };
      if (status === "featured" || status === "featured_expired")
                                 return { icon: "star",          bg: "#fff7ed", border: "#fdba74", color: "#c2410c" };
      return                            { icon: "megaphone",     bg: "#fff7ed", border: "#fdba74", color: "#c2410c" };
    }
    if (kind === "request") {
      if (status === "pending")  return { icon: "clock",        bg: "#fff7ed", border: "#fdba74", color: "#c2410c" };
      if (status === "approved") return { icon: "check-circle", bg: "#dcfce7", border: "#86efac", color: "#15803d" };
      if (status === "rejected") return { icon: "x-circle",     bg: "#fee2e2", border: "#fca5a5", color: "#b91c1c" };
      if (status === "featured" || status === "featured_expired")
                                 return { icon: "star",          bg: "#dcfce7", border: "#86efac", color: "#15803d" };
      return                            { icon: "shopping-cart", bg: "#dcfce7", border: "#86efac", color: "#15803d" };
    }
    if (kind === "wallet") {
      if (status === "reward")   return { icon: "gift",          bg: "#f5f3ff", border: "#c4b5fd", color: "#7c3aed" };
      return                            { icon: "wallet",        bg: "#fef9c3", border: "#fde68a", color: "#b45309" };
    }
    if (kind === "fav")          return { icon: "heart",         bg: "#fdf2f8", border: "#f9a8d4", color: "#db2777" };
    if (kind === "store_follow") return { icon: "user-plus",     bg: "#eef2ff", border: "#a5b4fc", color: "#4338ca" };
    return                              { icon: "bell",          bg: "#f3f4f6", border: "#e5e7eb", color: "#6b7280" };
  }

  function safeLucide() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }
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
      const kind   = row.dataset.kind   || "system";
      const status = row.dataset.status || "";

      // icon — apply Lucide icon + inline colours
      const iconBox = qs(".noti-icon", row);
      if (iconBox) {
        const data = getNotifIconData(kind, status);
        iconBox.style.background  = data.bg;
        iconBox.style.borderColor = data.border;
        iconBox.style.color       = data.color;
        iconBox.innerHTML = "";
        const iconEl = document.createElement("i");
        iconEl.setAttribute("data-lucide", data.icon);
        // Size the Lucide SVG to match noti-ic
        iconEl.style.width  = "20px";
        iconEl.style.height = "20px";
        iconBox.appendChild(iconEl);
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

    // Activate Lucide icons injected into noti-icon boxes
    safeLucide();

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
