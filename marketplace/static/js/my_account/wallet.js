/* static/js/my_account/wallet.js
   - Loads wallet data via AJAX when wallet tab opens
   - Renders timeline into #pointsLog
   - Invite friends link uses SAME logic as header dropdown:
       register_url + "?ref=" + referral_code
*/

(function () {
  function getWalletEndpoint() {
    return window.WALLET_ENDPOINT || "";
  }

  // ---------- helpers ----------
  function todayISO() {
    return new Date().toISOString().split("T")[0];
  }

  function daysAgo(n) {
    const d = new Date();
    d.setDate(d.getDate() - n);
    return d.toISOString().split("T")[0];
  }

  function escapeHTML(s) {
    return String(s || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function safeCopy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    const t = document.createElement("textarea");
    t.value = text;
    t.style.position = "fixed";
    t.style.left = "-9999px";
    document.body.appendChild(t);
    t.focus();
    t.select();
    document.execCommand("copy");
    t.remove();
    return Promise.resolve();
  }

  function formatTxText(t) {
    if (!t.meta) return t.text || "";

    const m = t.meta;
    const title = m.title ? `«${m.title}»` : "";

    if (m.action === "highlight") {
      return `تمييز ${m.targetType === "ad" ? "إعلان" : "طلب"} رقم ${m.id} — ${title} لمدة ${m.days} أيام`;
    }
    if (m.action === "republish") {
      return `إعادة نشر ${m.targetType === "ad" ? "إعلان" : "طلب"} رقم ${m.id} — ${title}`;
    }
    if (m.action === "invite") {
      return `مكافأة دعوة صديق ${title}`.trim();
    }
    return t.text || "";
  }

  function getTxIcon(type, meta) {
    if (type === "reward") {
      return `
        <svg class="w-5 h-5 text-red-600" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="3" y="8" width="18" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
          <path d="M12 8V3M7 5h10" stroke="currentColor" stroke-width="2"/>
          <path d="M3 13h18" stroke="currentColor" stroke-width="2"/>
        </svg>
      `;
    }

    if (meta && meta.action === "republish") {
      const color = meta.targetType === "ad" ? "text-orange-600" : "text-green-600";
      return `
        <svg class="w-5 h-5 ${color}" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M21 12a9 9 0 1 1-3-6.7" stroke="currentColor" stroke-width="2"/>
          <path d="M21 3v6h-6" stroke="currentColor" stroke-width="2"/>
        </svg>
      `;
    }

    if (meta && meta.targetType === "ad") {
      return `
        <svg class="w-5 h-5 text-orange-600" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 2l3 6 7 1-5 4 1 7-6-3-6 3 1-7-5-4 7-1z" stroke="currentColor" stroke-width="2"/>
        </svg>
      `;
    }

    if (meta && meta.targetType === "request") {
      return `
        <svg class="w-5 h-5 text-green-600" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 2l3 6 7 1-5 4 1 7-6-3-6 3 1-7-5-4 7-1z" stroke="currentColor" stroke-width="2"/>
        </svg>
      `;
    }

    return `
      <svg class="w-5 h-5 text-blue-600" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="3" y="7" width="18" height="10" stroke="currentColor" stroke-width="2"/>
      </svg>
    `;
  }

  function getTxBadge(type) {
    if (type === "buy") return `<span class="status-badge pill-blue">شراء</span>`;
    if (type === "reward") return `<span class="status-badge pill-green">مكافأة</span>`;
    return `<span class="status-badge pill-red">خصم</span>`;
  }

  // ---------------------------------------------------------
  // Wallet state
  // ---------------------------------------------------------
  let points = 0;
  let transactions = [];
  let loadedOnce = false;

  // ---------------------------------------------------------
  // DOM
  // ---------------------------------------------------------
  function updateBalance() {
    const el = document.getElementById("pointsBalance");
    if (el) el.textContent = String(points);
  }

  function renderLoading() {
    const container = document.getElementById("pointsLog");
    if (!container) return;
    container.innerHTML = `
      <div class="timeline-item justify-between">
        <div class="flex items-center gap-3">
          <div class="w-5 h-5 rounded bg-gray-200"></div>
          <div class="space-y-2">
            <div class="h-3 w-40 bg-gray-200 rounded"></div>
            <div class="h-3 w-24 bg-gray-100 rounded"></div>
          </div>
        </div>
        <div class="h-4 w-20 bg-gray-200 rounded"></div>
      </div>
    `;
  }

  function renderEmpty() {
    const container = document.getElementById("pointsLog");
    if (!container) return;
    container.innerHTML = `
      <div class="timeline-item justify-between">
        <div class="text-gray-600 font-semibold">لا يوجد سجل نقاط حالياً</div>
        <div class="text-gray-400 text-sm">${todayISO().replace(/-/g, "/")}</div>
      </div>
    `;
  }

  function renderTransactions() {
    const container = document.getElementById("pointsLog");
    if (!container) return;

    container.innerHTML = "";
    if (!transactions.length) {
      renderEmpty();
      return;
    }

    const groups = {};
    transactions.forEach((t) => {
      const d = t.date || todayISO();
      groups[d] ??= [];
      groups[d].push(t);
    });

    const dates = Object.keys(groups);
    if (!dates.length) {
      renderEmpty();
      return;
    }

    dates
      .sort((a, b) => new Date(b) - new Date(a))
      .forEach((date) => {
        const title = document.createElement("div");
        title.className = "timeline-date";
        title.innerText =
          date === daysAgo(0) ? "اليوم" :
          date === daysAgo(1) ? "الأمس" :
          date.replace(/-/g, "/");
        container.appendChild(title);

        groups[date].forEach((t) => {
          const row = document.createElement("div");
          row.className = "timeline-item items-center gap-3 justify-between";

          const txt = escapeHTML(formatTxText(t));
          const badge = getTxBadge(t.type);
          const icon = getTxIcon(t.type, t.meta);
          const amt = Number(t.amount || 0);
          const amtText = `${amt > 0 ? "+" : ""}${amt} نقطة`;

          row.innerHTML = `
            <div class="flex items-center gap-3">
              ${icon}
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span class="font-semibold text-gray-800">${txt}</span>
                  ${badge}
                </div>
              </div>
            </div>

            <div class="font-extrabold text-left ${amt > 0 ? "text-green-600" : "text-red-600"}">
              ${escapeHTML(amtText)}
            </div>
          `;

          container.appendChild(row);
        });
      });
  }

  // ---------------------------------------------------------
  // Modals (existing in template)
  // ---------------------------------------------------------
  function openSuccessModal(message, title = "تم التنفيذ بنجاح") {
    const m = document.getElementById("successModal");
    const msg = document.getElementById("successMsg");
    const ttl = document.getElementById("successTitle");
    if (!m || !msg || !ttl) return;

    ttl.innerText = title;
    msg.innerText = message;

    m.classList.remove("hidden");
    m.classList.add("flex");
  }

  window.closeSuccessModal = function () {
    const m = document.getElementById("successModal");
    if (!m) return;
    m.classList.add("hidden");
    m.classList.remove("flex");
  };

  window.openBuyModal = function () {
    const modal = document.getElementById("buyPointsModal");
    if (!modal) return;
    modal.classList.remove("hidden");
    modal.classList.add("flex");
  };

  window.closeBuyModal = function () {
    const modal = document.getElementById("buyPointsModal");
    const notice = document.getElementById("buyNotice");
    if (!modal) return;
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    if (notice) notice.classList.add("hidden");
  };

  window.buyPointsDisabled = function () {
    const notice = document.getElementById("buyNotice");
    if (!notice) return;
    notice.classList.remove("hidden");
    notice.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  // ---------------------------------------------------------
  // ✅ Invite link = register_url + ?ref=CODE  (same as header)
  // ---------------------------------------------------------
  function buildInviteLinkFromDOM() {
    // Primary source: #refLink span data attributes (wallet tab)
    const refEl = document.getElementById("refLink");
    const registerUrl = (refEl && refEl.dataset && refEl.dataset.registerUrl) ? refEl.dataset.registerUrl : "";
    const code = (refEl && refEl.dataset && refEl.dataset.referralCode) ? refEl.dataset.referralCode : "";

    // Fallback: header dropdown item if present
    const headerInvite = document.getElementById("inviteFriendsLink");
    const reg2 = (!registerUrl && headerInvite && headerInvite.dataset) ? (headerInvite.dataset.registerUrl || "") : "";
    const code2 = (!code && headerInvite && headerInvite.dataset) ? (headerInvite.dataset.referralCode || "") : "";

    const finalRegister = registerUrl || reg2 || "/register/";
    const finalCode = (code || code2 || "").trim();

    if (!finalCode) return finalRegister; // no code => plain register

    // append ?ref=... safely
    const u = new URL(finalRegister, window.location.origin);
    u.searchParams.set("ref", finalCode);
    return u.toString();
  }

  // ---------------------------------------------------------
  // Invite + QR
  // ---------------------------------------------------------
  function loadQRCodeLib() {
    return new Promise((resolve) => {
      if (window.QRCode) return resolve();
      const s = document.createElement("script");
      s.src = "https://cdn.jsdelivr.net/npm/qrcodejs/qrcode.min.js";
      s.onload = () => resolve();
      s.onerror = () => resolve();
      document.head.appendChild(s);
    });
  }

  async function generateQR() {
    await loadQRCodeLib();
    const linkEl = document.getElementById("refLink");
    const qrEl = document.getElementById("qrCode");
    if (!linkEl || !qrEl) return;

    const link = linkEl.innerText.trim();
    qrEl.innerHTML = "";
    if (!window.QRCode) return;

    // eslint-disable-next-line no-new
    new window.QRCode(qrEl, {
      text: link,
      width: 150,
      height: 150,
      colorDark: "#000000",
      colorLight: "#ffffff",
      correctLevel: window.QRCode.CorrectLevel.H
    });
  }

  window.openInvitePage = async function () {
    const page = document.getElementById("invitePage");
    if (!page) return;

    const linkEl = document.getElementById("refLink");
    if (linkEl) {
      const link = buildInviteLinkFromDOM();
      linkEl.innerText = link;
    }

    page.classList.remove("hidden");
    await generateQR();
  };

  window.closeInvitePage = function () {
    const page = document.getElementById("invitePage");
    if (page) page.classList.add("hidden");
  };

  window.copyRefLink = function () {
    const linkEl = document.getElementById("refLink");
    const link = linkEl ? linkEl.innerText : "";
    safeCopy(link);
    openSuccessModal("تم نسخ رابط الدعوة بنجاح!", "تم النسخ");
  };

  window.shareRefLink = function () {
    const linkEl = document.getElementById("refLink");
    const link = linkEl ? linkEl.innerText : "";

    if (navigator.share) {
      navigator.share({ title: "دعوة ركن", text: "سجل واحصل على نقاط مجانية!", url: link })
        .catch(() => {
          safeCopy(link);
          openSuccessModal("تم نسخ الرابط لأن المشاركة لم تعمل على جهازك.", "تم النسخ");
        });
    } else {
      safeCopy(link);
      openSuccessModal("تم نسخ الرابط — خاصية المشاركة غير مدعومة.", "تم النسخ");
    }
  };

  // ---------------------------------------------------------
  // Normalize backend rows (so history always shows)
  // ---------------------------------------------------------
  function normalizeTxRows(raw) {
    const arr = Array.isArray(raw) ? raw : [];
    return arr.map((t) => {
      const meta = t && t.meta ? t.meta : {};

      const amount = Number(
        t && t.amount !== undefined ? t.amount :
        t && t.delta !== undefined ? t.delta :
        0
      );

      let date = "";
      if (t && t.date) date = String(t.date).slice(0, 10);
      else if (t && t.created_at) date = String(t.created_at).slice(0, 10);
      else date = todayISO();

      const text = String((t && (t.text || t.title || t.reason)) || "");

      let type = String((t && t.type) || "");
      if (!type && t && t.kind) {
        if (t.kind === "spend") type = "use";
        else if (t.kind === "earn") type = "reward";
        else type = amount >= 0 ? "reward" : "use";
      }
      if (!type) type = amount >= 0 ? "reward" : "use";

      return { type, text, amount, date, meta };
    }).filter((x) => x && x.date);
  }

  // ---------------------------------------------------------
  // AJAX load wallet from server
  // ---------------------------------------------------------
  async function fetchWalletFromServer() {
    const endpoint = getWalletEndpoint();

    if (!endpoint) {
      points = Number(window.__pointsBalance || 0);
      transactions = [
        { type: "reward", text: "مكافأة تسجيل حساب", amount: +20, date: daysAgo(7), meta: {} },
        { type: "reward", text: "مكافأة دعوة صديق", amount: +10, date: daysAgo(5), meta: {} },
        { type: "buy", text: "شراء نقاط — باقة 120 نقطة", amount: +120, date: daysAgo(3), meta: {} },
        { type: "use", text: "", amount: -30, date: daysAgo(2), meta: { action: "highlight", targetType: "ad", id: 101, title: "لابتوب HP", days: 3 } },
      ];
      loadedOnce = true;
      return;
    }

    renderLoading();
    try {
      const res = await fetch(endpoint, { credentials: "same-origin" });
      const data = await res.json();
      if (!data || data.ok !== true) throw new Error("bad_response");

      points = Number(data.points_balance || data.points || 0);
      transactions = normalizeTxRows(data.transactions || []);
      loadedOnce = true;
    } catch (e) {
      points = Number(window.__pointsBalance || 0);
      transactions = [];
      loadedOnce = true;
    }
  }

  window.walletRefresh = async function () {
    if (!document.getElementById("tab-wallet")) return;
    await fetchWalletFromServer();
    updateBalance();
    renderTransactions();
  };

  async function initWalletUI(forceReload) {
    if (!document.getElementById("tab-wallet")) return;

    // prepare correct link early (so invite opens instantly)
    const linkEl = document.getElementById("refLink");
    if (linkEl && !linkEl.innerText.trim()) {
      linkEl.innerText = buildInviteLinkFromDOM();
    }

    if (forceReload || !loadedOnce) {
      await fetchWalletFromServer();
    }

    updateBalance();
    renderTransactions();
  }

  window.addEventListener("load", () => {
    const walletTab = document.getElementById("tab-wallet");
    if (walletTab && !walletTab.classList.contains("hidden")) {
      initWalletUI(true);
    }

    document.addEventListener("click", (e) => {
      const btn = e.target && e.target.closest && e.target.closest('[data-tab="wallet"]');
      if (btn) setTimeout(() => initWalletUI(true), 0);
    });
  });
})();
