/* =========================================================
   main.js (HOME ONLY)
========================================================= */

console.log("✅ main.js loaded");

/* =========================================================
   Billboard Swiper Initialization (MOCKUP)
========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  const billboard = document.querySelector(".billboardSwiper");
  if (billboard) {
    new Swiper(".billboardSwiper", {
      slidesPerView: 1,
      loop: true,
      autoplay: {
        delay: 2000,
        pauseOnMouseEnter: true,
        disableOnInteraction: false,
      },
      pagination: {
        el: ".swiper-pagination",
        clickable: true,
      },
      navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
      },
      speed: 900,
    });
  }
});

/* =========================================================
   Horizontal Scroll (Stores / Trending) - keep your behavior
========================================================= */
function scrollRow(rowId, direction, scrollAmount) {
  const container = document.getElementById(rowId);
  if (!container) return;

  container.scrollBy({
    left: direction * scrollAmount,
    behavior: "smooth",
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const storesLeft = document.getElementById("storesLeft");
  const storesRight = document.getElementById("storesRight");

  if (storesLeft) storesLeft.addEventListener("click", () => scrollRow("storesRow", -1, 360));
  if (storesRight) storesRight.addEventListener("click", () => scrollRow("storesRow", 1, 360));

  const trendingLeft = document.getElementById("trendingLeft");
  const trendingRight = document.getElementById("trendingRight");

  if (trendingLeft) trendingLeft.addEventListener("click", () => scrollRow("trendingRow", -1, 340));
  if (trendingRight) trendingRight.addEventListener("click", () => scrollRow("trendingRow", 1, 340));

  addDragScroll("storesRow");
  addDragScroll("trendingRow");
});

/* =========================================================
   Drag to Scroll (match mockup class naming)
========================================================= */
function addDragScroll(elementId) {
  const row = document.getElementById(elementId);
  if (!row) return;

  let isDown = false;
  let startX = 0;
  let scrollLeft = 0;

  row.addEventListener("mousedown", (e) => {
    isDown = true;
    row.classList.add("cursor-grabbing");
    startX = e.pageX - row.offsetLeft;
    scrollLeft = row.scrollLeft;
  });

  row.addEventListener("mouseleave", () => {
    isDown = false;
    row.classList.remove("cursor-grabbing");
  });

  row.addEventListener("mouseup", () => {
    isDown = false;
    row.classList.remove("cursor-grabbing");
  });

  row.addEventListener("mousemove", (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - row.offsetLeft;
    const walk = (x - startX) * 1.6;
    row.scrollLeft = scrollLeft - walk;
  });
}

/* =========================================================
   Single-submit protection
========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-single-submit]").forEach((form) => {
    let locked = false;

    form.addEventListener("submit", () => {
      if (locked) return;
      locked = true;

      const buttons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
      buttons.forEach((btn) => {
        btn.disabled = true;
        btn.classList.add("opacity-60", "cursor-not-allowed");
        btn.setAttribute("aria-busy", "true");
      });

      const primary = form.querySelector("[data-submit-btn]");
      if (primary) {
        primary.dataset.originalText = primary.textContent;
        primary.textContent = "جاري الإرسال...";
      }
    });
  });
});

/* =========================================================
   Load More Functionality (KEEP AS-IS)
========================================================= */
function gridCols(gridEl) {
  const cols = getComputedStyle(gridEl).gridTemplateColumns.split(" ").filter(Boolean).length;
  return Math.max(cols || 1, 1);
}

function disableBtn(btn, text) {
  btn.disabled = true;
  btn.classList.add("opacity-60", "cursor-not-allowed");
  btn.textContent = text;
}

async function loadMoreChunk({ btnId, gridId, url, noMoreText }) {
  const btn = document.getElementById(btnId);
  const grid = document.getElementById(gridId);
  if (!btn || !grid) return;

  let locked = false;

  btn.addEventListener("click", async () => {
    if (locked) return;
    locked = true;

    const cols = gridCols(grid);
    const limit = 3 * cols;
    const offset = grid.children.length;

    btn.disabled = true;
    btn.classList.add("opacity-60");

    try {
      const res = await fetch(`${url}?offset=${offset}&limit=${limit}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" }
      });
      const data = await res.json();

      if (data.html && data.html.trim()) {
        grid.insertAdjacentHTML("beforeend", data.html);
      }

      if (!data.has_more) {
        disableBtn(btn, noMoreText);
        return;
      }

      btn.disabled = false;
      btn.classList.remove("opacity-60");
    } catch (e) {
      console.error("Load more error:", e);
      btn.disabled = false;
      btn.classList.remove("opacity-60");
    } finally {
      locked = false;
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadMoreChunk({
    btnId: "loadMoreAdsBtn",
    gridId: "latest-items-grid",
    url: "/home/more-items/",
    noMoreText: "لا يوجد المزيد من الإعلانات"
  });

  loadMoreChunk({
    btnId: "loadMoreRequestsBtn",
    gridId: "requestsGrid",
    url: "/home/more-requests/",
    noMoreText: "لا يوجد المزيد من الطلبات"
  });
});

/* =========================================================
   Intercept Add Item/Request buttons for guests (HOME PAGE)
========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  // Check if user is authenticated
  const isAuthenticated = window.RUKN?.isAuthenticated || false;

  // If user is logged in, do nothing
  if (isAuthenticated) return;

  // Find all "create item" and "create request" links on the home page
  const createLinks = document.querySelectorAll('a[href*="create_item"], a[href*="create_request"], a[href*="/item/create"], a[href*="/request/create"]');

  createLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault(); // Stop navigation

      // Get the target URL they wanted to go to
      const targetUrl = link.getAttribute("href");

      // Set the "next" field in login form so they're redirected after login
      const loginNext = document.getElementById("loginNext");
      if (loginNext && targetUrl) {
        loginNext.value = targetUrl;
      }

      // Open login modal using the global function
      if (window.RUKN_UI && window.RUKN_UI.openLogin) {
        window.RUKN_UI.openLogin();
      } else {
        // Fallback: try to find and click a login button
        const loginBtn = document.querySelector('[data-open-login]');
        if (loginBtn) loginBtn.click();
      }
    });
  });
});

/* =========================================================
   Open login modal if redirected with ?login=1 (KEEP)
========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get("login") !== "1") return;

  const findLoginTrigger = () => {
    return (
      document.querySelector('[data-open-login]') ||
      document.querySelector('[data-auth-open="login"]') ||
      document.querySelector("button[data-login]") ||
      document.getElementById("openLoginBtn") ||
      document.querySelector('[data-modal-target="login"]') ||
      document.querySelector('[data-target="login"]') ||
      document.querySelector('[data-bs-target="#loginModal"]') ||
      document.querySelector('a[href="#loginModal"]') ||
      document.querySelector('a[href="#login"]') ||
      Array.from(document.querySelectorAll("a,button")).find((el) => {
        const t = (el.textContent || "").trim();
        return t === "تسجيل الدخول" || t === "دخول" || t.toLowerCase() === "login";
      }) ||
      null
    );
  };

  let tries = 0;
  const maxTries = 30;
  const intervalMs = 100;

  const timer = setInterval(() => {
    tries += 1;

    const trigger = findLoginTrigger();
    if (trigger) {
      clearInterval(timer);
      trigger.click();
      return;
    }

    if (tries >= maxTries) {
      clearInterval(timer);
      console.warn("Login trigger not found. Modal will not auto-open.");
    }
  }, intervalMs);
});

/* =================== TIP CHOOSER (LOGGED-IN SECTION) =================== */

(function () {
  "use strict";

  // ── Tip data (exact same as mockup) ──────────────────────────────────────

  const tipsForAds = [
    "اكتب عنوانًا واضحًا ودقيقًا: (نوع المنتج + الحالة + المدينة)",
    "استخدم صورًا حقيقية وواضحة للمنتج من زوايا متعددة.",
    "تأكد أن الإضاءة جيدة والخلفية نظيفة عند التصوير.",
    "أضف صورة تُظهر أي عيب أو ملاحظة لزيادة المصداقية.",
    "حدد سعرًا منطقيًا قريبًا من السوق مع ترك مجال بسيط للتفاوض.",
    "اكتب وصفًا صادقًا لحالة المنتج دون مبالغة.",
    "اذكر سبب البيع إن أمكن، فهذا يعزز ثقة المشتري.",
    "حدّد موقعك أو مدينتك بدقة لتسهيل التواصل.",
    "استخدم كلمات مفتاحية شائعة ليسهل العثور على إعلانك.",
    "تجنب العناوين العامة مثل (للبيع فقط) فهي تقلل التفاعل.",
    "رتّب وصف الإعلان بنقاط ليسهل قراءته.",
    "اذكر إن كان السعر نهائيًا أو قابلًا للتفاوض.",
    "حدّد طريقة التواصل المفضلة (رسائل، اتصال).",
    "رد بسرعة على الرسائل، فالرد خلال أول ساعة يضاعف فرص البيع.",
    "حدّث إعلانك إذا تغيّر السعر أو الحالة.",
    "لا تكرر نفس الإعلان أكثر من مرة، التحديث أفضل من الإعادة.",
    "تابع الأسئلة المتكررة وأضف إجاباتها في الوصف.",
    "اختر وقت نشر مناسب (المساء غالبًا أفضل).",
    "تأكد أن الإعلان خالٍ من الأخطاء الإملائية.",
    "كن محترمًا وواضحًا في التواصل، السمعة الجيدة تبيع عنك."
  ];

  const tipsForRequests = [
    "اكتب طلبك بشكل محدد: النوع + الموديل + الميزانية.",
    "حدّد المدينة أو المنطقة لتصلك عروض قريبة.",
    "اذكر الميزانية بوضوح بدل كتابة (أبغى أفضل سعر).",
    "حدّد إن كان الطلب جديدًا أو مستعملًا.",
    "اذكر أهم المواصفات التي تهمك.",
    "وضّح إن كنت تقبل ببدائل أو موديلات مشابهة.",
    "اكتب طلبك بلغة واضحة ومختصرة.",
    "تجنب الطلبات العامة جدًا التي يصعب تلبيتها.",
    "اطلب صورًا حديثة وحقيقية للمنتج.",
    "اطلب فيديو قصير إذا كان المنتج مستعملًا.",
    "اسأل عن حالة المنتج بالتفصيل قبل الاتفاق.",
    "تأكد من السعر النهائي قبل الانتقال للخاص.",
    "اتفق داخل المنصة قبل مشاركة رقمك الشخصي.",
    "قارن بين أكثر من عرض قبل اتخاذ القرار.",
    "تحقق من تقييم أو سمعة البائع إن وُجدت.",
    "كن مرنًا في التفاوض لكن واقعيًا.",
    "حدّد طريقة الاستلام أو الشحن مسبقًا.",
    "لا تدفع أي مبلغ قبل التأكد من جدية العرض.",
    "احذر من العروض غير المنطقية أو الرخيصة جدًا.",
    "التعامل باحترام ووضوح يزيد فرص حصولك على عرض مناسب."
  ];

  // ── State ─────────────────────────────────────────────────────────────────

  let mode     = null;  // "ad" | "request"
  let lastTip  = null;
  const shownTips = { ad: null, request: null };

  // ── Helpers ───────────────────────────────────────────────────────────────

  function pickRandom(arr) {
    let tip;
    do { tip = arr[Math.floor(Math.random() * arr.length)]; }
    while (tip === lastTip && arr.length > 1);
    lastTip = tip;
    return tip;
  }

  function safeLucide() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }
  }

  // ── Main init ─────────────────────────────────────────────────────────────

  function initTipChooser() {

    const tipAdBtn      = document.getElementById("tipAdBtn");
    const tipRequestBtn = document.getElementById("tipRequestBtn");

    // Guard: section only exists for logged-in users
    if (!tipAdBtn || !tipRequestBtn) return;

    const tipText      = document.getElementById("tipText");
    const newTipBtn    = document.getElementById("newTipBtn");
    const goBtn        = document.getElementById("goBtn");
    const tipBox       = document.getElementById("tipBox");
    const tipIconBox   = document.getElementById("tipIconBox");
    const tipIcon      = document.getElementById("tipIcon");
    const tipTitle     = document.getElementById("tipTitle");
    const tipHighlight = document.getElementById("tipHighlightBox");

    // ── Card selection styling ──

    function resetCards() {
      // Remove active state from both cards
      tipAdBtn.classList.remove("border-orange-600", "bg-orange-50", "ring-4", "ring-orange-600");
      tipRequestBtn.classList.remove("border-green-600", "bg-green-50", "ring-4", "ring-green-600");
      // Restore default state
      tipAdBtn.classList.add("border-slate-300", "bg-white");
      tipRequestBtn.classList.add("border-slate-300", "bg-white");
    }

    // ── Tip box theming ──
    // Instead of resetting className (which breaks the fixed sm:* classes),
    // we remove/add only the color tokens that change between ad and request.

    function clearThemeColors() {
      // tipBox border color
      tipBox.classList.remove("border-orange-600", "border-green-600");
      // tipHighlight bg + border (also remove HTML-baked-in defaults)
      tipHighlight.classList.remove(
        "bg-slate-50",   "border-orange-400",
        "bg-orange-50",  "border-orange-600",
        "bg-green-50",   "border-green-600"
      );
      // tipIconBox border
      tipIconBox.classList.remove("border-orange-600", "border-green-600");
      // tipIcon color
      tipIcon.classList.remove("text-orange-600", "text-green-600");
      // tipTitle color
      tipTitle.classList.remove("text-orange-600", "text-green-600");
      // newTipBtn bg (also remove the default gray)
      newTipBtn.classList.remove(
        "bg-slate-500",
        "bg-orange-600", "hover:bg-orange-700",
        "bg-green-600",  "hover:bg-green-700"
      );
    }

    function applyTheme() {
      clearThemeColors();

      const isAd = mode === "ad";

      const color   = isAd ? "orange" : "green";
      const icon    = isAd ? "megaphone" : "search";
      const title   = isAd
        ? "نصيحة الخبراء لإضافة إعلان ناجح"
        : "نصيحة الخبراء لإضافة طلب ناجح";
      const btnText = isAd ? "أضف إعلان" : "أضف طلب";

      // Apply theme classes
      tipBox.classList.add(`border-${color}-600`);
      tipHighlight.classList.add(`bg-${color}-50`, `border-${color}-600`);
      tipIconBox.classList.add(`border-${color}-600`);
      tipIcon.classList.add(`text-${color}-600`);
      tipTitle.classList.add(`text-${color}-600`);
      newTipBtn.classList.add(`bg-${color}-600`, "text-white", `hover:bg-${color}-700`);

      // Update icon + title text
      tipIcon.setAttribute("data-lucide", icon);
      tipTitle.textContent = title;

      // Update go button (set style directly to avoid class conflicts)
      goBtn.style.backgroundColor = isAd ? "#ea580c" : "#16a34a";
      goBtn.style.setProperty("--hover-bg", isAd ? "#c2410c" : "#15803d");
      goBtn.textContent = btnText;

      safeLucide();
    }

    // ── Show / cycle tip text ──

    function showTip(forceNew) {
      if (!mode) return;

      const tips = mode === "ad" ? tipsForAds : tipsForRequests;

      // Re-show previously displayed tip unless forceNew
      if (shownTips[mode] && !forceNew) {
        tipText.textContent = shownTips[mode];
        return;
      }

      // Fade out → update → fade in
      tipText.style.opacity    = "0";
      tipText.style.transform  = "translateY(4px)";
      tipText.style.transition = "opacity 0.18s ease, transform 0.18s ease";

      setTimeout(() => {
        const next = pickRandom(tips);
        shownTips[mode]       = next;
        tipText.textContent   = next;
        tipText.style.opacity   = "1";
        tipText.style.transform = "translateY(0)";
      }, 180);
    }

    // ── Wire buttons ──

    tipAdBtn.addEventListener("click", () => {
      if (mode === "ad") return;
      mode = "ad";

      resetCards();
      tipAdBtn.classList.remove("border-slate-300", "bg-white");
      tipAdBtn.classList.add("border-orange-600", "bg-orange-50", "ring-4", "ring-orange-600");

      applyTheme();
      newTipBtn.classList.remove("hidden");
      goBtn.classList.remove("hidden");
      showTip(false);
    });

    tipRequestBtn.addEventListener("click", () => {
      if (mode === "request") return;
      mode = "request";

      resetCards();
      tipRequestBtn.classList.remove("border-slate-300", "bg-white");
      tipRequestBtn.classList.add("border-green-600", "bg-green-50", "ring-4", "ring-green-600");

      applyTheme();
      newTipBtn.classList.remove("hidden");
      goBtn.classList.remove("hidden");
      showTip(false);
    });

    // "نصيحة جديدة" → force new random tip
    newTipBtn.addEventListener("click", () => showTip(true));

    // "ابدأ الآن" → navigate to add-ad or add-request
    goBtn.addEventListener("click", () => {
      const url = mode === "ad"
        ? (goBtn.dataset.urlAd      || "#")
        : (goBtn.dataset.urlRequest || "#");
      window.location.href = url;
    });

    // Initial lucide render
    safeLucide();
  }

  document.addEventListener("DOMContentLoaded", initTipChooser);

})();