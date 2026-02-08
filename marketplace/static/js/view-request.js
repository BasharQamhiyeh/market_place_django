// static/js/view-request.js
console.log("view-request.js LOADED");

/* ========= Helpers ========= */
function showRuknAlert(message) {
  const wrapper = document.getElementById("ruknAlert");
  const box = document.getElementById("ruknAlertBox");
  if (!wrapper || !box) return;

  box.textContent = message || "✔ تم الإجراء";
  wrapper.classList.remove("opacity-0");
  wrapper.classList.add("opacity-100");
  box.classList.remove("scale-75");
  box.classList.add("scale-100");

  clearTimeout(window.__ruknToastTimer);
  window.__ruknToastTimer = setTimeout(() => {
    wrapper.classList.add("opacity-0");
    wrapper.classList.remove("opacity-100");
    box.classList.add("scale-75");
    box.classList.remove("scale-100");
  }, 2000);
}

function fallbackCopy(text) {
  const temp = document.createElement("textarea");
  temp.value = text;
  document.body.appendChild(temp);
  temp.select();
  try { document.execCommand("copy"); } catch (e) {}
  document.body.removeChild(temp);
  showRuknAlert("✔ تم النسخ");
}

function normalizeJordanPhone(raw) {
  // returns digits only; tries to become 9627xxxxxxxx if possible
  let s = (raw || "").trim();
  if (!s) return "";

  // remove spaces, dashes, parentheses, etc.
  s = s.replace(/[^\d+]/g, "");
  if (s.startsWith("+")) s = s.slice(1);
  s = s.replace(/\D/g, "");

  // cases:
  // 07xxxxxxxx -> 9627xxxxxxxx
  if (s.startsWith("07") && s.length === 10) return "962" + s.slice(1);

  // 7xxxxxxxx -> 9627xxxxxxxx (sometimes user saves without leading 0)
  if (s.startsWith("7") && s.length === 9) return "962" + s;

  // 9627xxxxxxxx already OK
  if (s.startsWith("9627") && s.length === 12) return s;

  // fallback: return digits as-is (still usable for tel:)
  return s;
}

function maskPhone(raw) {
  const digits = (raw || "").replace(/\D/g, "");
  if (!digits) return "07•• ••• •••";
  const first2 = digits.slice(0, 2);
  return first2 + "•• ••• •••";
}


/* ========= Copy Number ========= */
window.copyAdNumber = function copyAdNumber() {
  const el = document.getElementById("adNumber");
  if (!el) return;
  const num = (el.textContent || "").trim();
  if (!num) return;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(num)
      .then(() => showRuknAlert("✔ تم نسخ الرقم"))
      .catch(() => fallbackCopy(num));
  } else {
    fallbackCopy(num);
  }
};

/* ========= Favorite (UI only) ========= */
(function initFavorite() {
  const favBtn = document.getElementById("favBtn");
  const favText = document.getElementById("favText");
  if (!favBtn || !favText) return;

  favBtn.addEventListener("click", function () {
    const isActive = this.classList.contains("is-fav");
    const iconWrapper = this.querySelector("span > svg");

    if (!isActive) {
      this.classList.add("is-fav");
      favText.textContent = "تمت المتابعة";
      this.classList.add("bg-green-50", "border-green-300", "text-[var(--rukn-green)]");
      this.classList.remove("bg-white", "border-gray-200");
      if (iconWrapper) iconWrapper.classList.add("text-[var(--rukn-green)]");
      showRuknAlert("✔ تمت المتابعة");
    } else {
      this.classList.remove("is-fav");
      favText.textContent = "متابعة الطلب";
      this.classList.remove("bg-green-50", "border-green-300");
      this.classList.add("bg-white", "border-gray-200");
      if (iconWrapper) iconWrapper.classList.remove("text-[var(--rukn-green)]");
      showRuknAlert("✔ تم الإلغاء");
    }
  });
})();

/* ========= Share ========= */
/* ========= Share ========= */
(function initShare() {
  const shareBtn = document.getElementById("shareBtn");
  if (!shareBtn) return;

  shareBtn.addEventListener("click", async (e) => {
    e.preventDefault();

    const shareData = {
      title: "طلب على منصة ركن",
      text: "شاهد هذا الطلب على منصة ركن",
      url: window.location.href,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
        return;
      }

      // fallback: copy link
      const url = window.location.href;

      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(url);
        showRuknAlert("✔ تم نسخ رابط الطلب");
      } else {
        fallbackCopy(url);
      }
    } catch (err) {
      // ignore share cancel, but if clipboard fails show fallback
      // (no need to alert on cancel)
      console.warn("share failed:", err);
    }
  });
})();


/* ========= Phone Reveal (WORKING + HIDE ICONS UNTIL REVEAL + ALLOW FLAG) ========= */
/* ========= Phone Reveal (AUTH + HIDE ICONS UNTIL REVEAL + ALLOW FLAG) ========= */
(function initPhoneReveal() {
  const sellerPhoneEl = document.getElementById("sellerPhone");
  const revealPhoneBtn = document.getElementById("revealPhoneBtn");
  const callBtn = document.getElementById("callBtn");
  const whatsappBtn = document.getElementById("whatsappBtn");
  const contactActions = document.getElementById("contactActions");

  if (!sellerPhoneEl || !revealPhoneBtn) return;

  function openLoginModal() {
    const modalId = revealPhoneBtn.dataset.loginModal || "loginModal";
    const m = document.getElementById(modalId);
    if (m) m.classList.remove("hidden");
  }

  function openMessageBox() {
    const msgBtn = document.getElementById("toggleMessageBox");
    if (msgBtn) msgBtn.click();
  }

  const raw = (sellerPhoneEl.dataset.full || "").trim();
  const normalized = normalizeJordanPhone(raw);

  sellerPhoneEl.dataset.full = raw;
  sellerPhoneEl.dataset.normalized = normalized;
  sellerPhoneEl.dataset.revealed = "false";

  sellerPhoneEl.textContent = (sellerPhoneEl.dataset.masked || sellerPhoneEl.textContent || "").trim();

  // hide icons until reveal
  if (contactActions) {
    contactActions.classList.add("hidden");
    contactActions.classList.remove("flex");
  }

  if (callBtn) callBtn.href = "#";
  if (whatsappBtn) whatsappBtn.href = "#";

  // prevent '#' jump
  if (callBtn) callBtn.addEventListener("click", (e) => { if ((callBtn.getAttribute("href") || "#") === "#") e.preventDefault(); });
  if (whatsappBtn) whatsappBtn.addEventListener("click", (e) => { if ((whatsappBtn.getAttribute("href") || "#") === "#") e.preventDefault(); });

  revealPhoneBtn.addEventListener("click", () => {
    // ✅ auth gate
    const auth = (revealPhoneBtn.dataset.auth || "0") === "1";
    if (!auth) {
      openLoginModal();
      return;
    }

    // ✅ check allow flag
    const allow = (sellerPhoneEl.dataset.allow || "1") === "1";
    if (!allow) {
      showRuknAlert("⚠️ صاحب الطلب يفضّل التواصل عبر الرسائل");
      openMessageBox();
      return;
    }

    if (sellerPhoneEl.dataset.revealed === "true") return;

    const fullDisplay = (sellerPhoneEl.dataset.full || "").trim();
    const norm = (sellerPhoneEl.dataset.normalized || "").trim();

    if (!fullDisplay && !norm) {
      showRuknAlert("⚠️ سجّل الدخول لعرض الرقم");
      openLoginModal();
      return;
    }

    sellerPhoneEl.textContent = fullDisplay || norm;
    sellerPhoneEl.dataset.revealed = "true";

    if (contactActions) {
      contactActions.classList.remove("hidden");
      contactActions.classList.add("flex");
    }

    if (callBtn) callBtn.href = "tel:" + (norm || fullDisplay);

    if (whatsappBtn) {
      const wa = norm || normalizeJordanPhone(fullDisplay);
      whatsappBtn.href = wa ? ("https://wa.me/" + wa) : "#";
    }
  });
})();



/* ========= Message Box (FALLBACK, so it ALWAYS opens) ========= */
(function initMessageBoxFallback() {
  const toggleBtn = document.getElementById("toggleMessageBox");
  const box = document.getElementById("messageBox");
  const chevron = document.getElementById("messageChevron");
  const input = document.getElementById("messageText");

  if (!toggleBtn || !box) return;

  // if shared script already bound, don't double-bind
  if (toggleBtn.dataset.bound === "1") return;
      toggleBtn.dataset.bound = "1";

      toggleBtn.addEventListener("click", () => {
      // ✅ auth gate
      const isAuth = (toggleBtn.dataset.auth || "0") === "1";
      if (!isAuth) {
        const modalId = toggleBtn.dataset.loginModal || "loginModal";
        const m = document.getElementById(modalId);
        if (m) m.classList.remove("hidden");
        return;
      }

      const isHidden = box.classList.contains("hidden");
      if (isHidden) {
        box.classList.remove("hidden");
        if (chevron) chevron.classList.add("rotate-180");
        setTimeout(() => input && input.focus(), 80);
      } else {
        box.classList.add("hidden");
        if (chevron) chevron.classList.remove("rotate-180");
      }
    });


})();

/* ========= Similar Requests Load More ========= */
/* ========= Similar Requests Load More (ROW BY ROW via endpoint) ========= */
(function () {
  async function handleLoadMore(btn) {
    const grid = document.getElementById("similarRequestsGrid");
    if (!grid) {
      console.log("❌ similarRequestsGrid NOT FOUND");
      return;
    }

    const requestId = btn.dataset.requestId;
    console.log("LOAD MORE START", { requestId, currentCount: grid.children.length });

    const cols = Math.max(
      (getComputedStyle(grid).gridTemplateColumns.split(" ").filter(Boolean).length) || 1,
      1
    );
    const limit = cols; // row by row
    const offset = grid.children.length;

    btn.disabled = true;
    btn.classList.add("opacity-60");

    try {
      const url = `/requests/${requestId}/more-similar/?offset=${offset}&limit=${limit}`;
      console.log("FETCH", url);

      const res = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });

      console.log("RESPONSE", res.status);

      if (!res.ok) throw new Error("Bad response " + res.status);

      const data = await res.json();
      console.log("DATA", data);

      if (data.html && data.html.trim()) {
        grid.insertAdjacentHTML("beforeend", data.html);
      }

      if (!data.has_more) {
        btn.disabled = true;
        btn.textContent = "لا يوجد المزيد من الطلبات";
        btn.classList.add("cursor-not-allowed");
        return;
      }

      btn.disabled = false;
      btn.classList.remove("opacity-60");
    } catch (err) {
      console.error("LOAD MORE ERROR", err);
      btn.disabled = false;
      btn.classList.remove("opacity-60");
    }
  }

  // ✅ event delegation (always works)
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("#loadMoreSimilarRequestsBtn");
    if (!btn) return;
    e.preventDefault();
    if (btn.dataset.loading === "1") return;
    btn.dataset.loading = "1";
    handleLoadMore(btn).finally(() => (btn.dataset.loading = "0"));
  });

  console.log("✅ load-more handler READY");
})();

