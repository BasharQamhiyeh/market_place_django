// static/js/view-request.js

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
  if (!digits) return "•• •• ••• •07";
  const last2 = digits.slice(-2);
  return "•• •• ••• •" + last2;
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
(function initShare() {
  const shareBtn = document.getElementById("shareBtn");
  if (!shareBtn) return;

  shareBtn.addEventListener("click", async () => {
    const shareData = {
      title: "طلب على منصة ركن",
      text: "شاهد هذا الطلب",
      url: window.location.href
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(window.location.href);
        showRuknAlert("✔ تم نسخ الرابط");
      }
    } catch (e) {
      // ignore cancel
    }
  });
})();

/* ========= Phone Reveal (WORKING) ========= */
(function initPhoneReveal() {
  const sellerPhoneEl = document.getElementById("sellerPhone");
  const revealPhoneBtn = document.getElementById("revealPhoneBtn");
  const callBtn = document.getElementById("callBtn");
  const whatsappBtn = document.getElementById("whatsappBtn");
  const contactActions = document.getElementById("contactActions");

  if (!sellerPhoneEl || !revealPhoneBtn) return;

  // init masked
  const raw = (sellerPhoneEl.dataset.full || sellerPhoneEl.textContent || "").trim();
  const normalized = normalizeJordanPhone(raw);
  sellerPhoneEl.dataset.full = raw;          // keep original for display
  sellerPhoneEl.dataset.normalized = normalized; // store normalized for links
  sellerPhoneEl.dataset.revealed = "false";
  sellerPhoneEl.textContent = maskPhone(normalized);

  // prevent '#' jump if user clicks icons before reveal
  if (callBtn) callBtn.addEventListener("click", (e) => { if (callBtn.getAttribute("href") === "#") e.preventDefault(); });
  if (whatsappBtn) whatsappBtn.addEventListener("click", (e) => { if (whatsappBtn.getAttribute("href") === "#") e.preventDefault(); });

  revealPhoneBtn.addEventListener("click", () => {
    if (sellerPhoneEl.dataset.revealed === "true") return;

    const fullDisplay = (sellerPhoneEl.dataset.full || "").trim();
    const norm = (sellerPhoneEl.dataset.normalized || "").trim();

    if (!fullDisplay && !norm) {
      showRuknAlert("⚠️ رقم غير متوفر");
      return;
    }

    // show original as saved (user-friendly)
    sellerPhoneEl.textContent = fullDisplay || norm;
    sellerPhoneEl.dataset.revealed = "true";

    if (contactActions) contactActions.classList.remove("hidden");

    // links
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
(function initLoadMore() {
  const grid = document.getElementById("requestsGrid");
  const btn = document.getElementById("loadMoreBtn");
  const dataEl = document.getElementById("more-requests-data");
  if (!grid || !btn) return;

  if (!dataEl) {
    btn.classList.add("hidden");
    return;
  }

  let more = [];
  try { more = JSON.parse(dataEl.textContent || "[]"); } catch (e) { more = []; }

  const PAGE_SIZE = 8;
  let index = 0;

  function appendSimpleCard(r) {
    const url = r.url || "#";
    const title = r.title || r.listing_title || (r.listing && r.listing.title) || "طلب";
    const city = r.city || r.listing_city || (r.listing && r.listing.city) || "—";
    const created = r.created_at || (r.listing && r.listing.created_at) || "";

    const card = document.createElement("a");
    card.href = url;
    card.className = "req-card group cursor-pointer";
    card.innerHTML = `
      <div class="hover-mask"></div>
      <div class="hint-container">
        <div class="flex flex-col text-[11px] font-extrabold text-[var(--rukn-green)] leading-tight text-center">
          <span>عرض</span><span>الطلب</span>
        </div>
        <span class="hint-arrow text-[var(--rukn-green)]">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none"
               viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"
               class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round"
                  d="m18.75 4.5-7.5 7.5 7.5 7.5m-6-15L5.25 12l7.5 7.5" />
          </svg>
        </span>
      </div>

      <div class="p-4 pb-2 flex-1 relative">
        <h3 class="relative z-30 font-bold text-gray-900 text-sm line-clamp-2 min-h-[48px] leading-relaxed mb-3 transition group-hover:text-[var(--rukn-green)]">
          ${title}
        </h3>

        <div class="flex items-center gap-4 sm:text-xs text-gray-500 relative z-0">
          <span class="flex items-center gap-1">
            <svg class="w-3.5 h-3.5 text-green-500" viewBox="0 0 20 20" fill="none">
              <path d="M10 18s6-5.05 6-10a6 6 0 1 0-12 0c0 4.95 6 10 6 10z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" />
              <circle cx="10" cy="8" r="2.3" stroke="currentColor" stroke-width="1.6" />
            </svg>
            <span>${city}</span>
          </span>

          <span class="flex items-center gap-1">
            <svg class="w-3.5 h-3.5 text-green-500" viewBox="0 0 20 20" fill="none">
              <rect x="3" y="4" width="14" height="13" rx="2" stroke="currentColor" stroke-width="1.6" />
              <path d="M7 2v4M13 2v4M4 8h12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
            </svg>
            <span>${created}</span>
          </span>
        </div>
      </div>
    `;
    grid.appendChild(card);
  }

  function renderMore() {
    const chunk = more.slice(index, index + PAGE_SIZE);
    chunk.forEach(appendSimpleCard);
    index += chunk.length;

    if (index >= more.length) {
      btn.disabled = true;
      btn.textContent = "لا توجد طلبات أخرى";
    }
  }

  btn.addEventListener("click", renderMore);
})();
