// static/js/categories_browse.js
(() => {
  "use strict";

  const jsonEl = document.getElementById("categories-json");
  const categories = jsonEl ? JSON.parse(jsonEl.textContent || "[]") : [];

  const PLACEHOLDER = "/static/img/category-placeholder.png"; // ضع صورة Placeholder هنا (اختياري)

  const ITEM_LIST_BASE = "/items/"; // change if your route is different
  const itemListUrl = (categoryId) => `${ITEM_LIST_BASE}?category=${encodeURIComponent(categoryId)}`;

  const getImg = (obj) => obj?.photo || obj?.icon || PLACEHOLDER;

  // ✅ Read category from URL parameter (FIXED: better type handling)
  function getCategoryFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const categoryParam = params.get('category');

    if (categoryParam) {
      // Try to find matching category (comparing as strings for safety)
      const found = categories.find(cat => String(cat.id) === String(categoryParam));
      if (found) {
        return found.id; // Return the actual ID from the category object
      }
    }

    // Default to first category
    return categories.length ? categories[0].id : null;
  }

  let activeMainId = getCategoryFromUrl();

  /* ================= Banner Slider ================= */
  (function initBanner() {
    const banner = document.getElementById("adBanner");
    if (!banner) return;

    const slides = [...banner.querySelectorAll(".ad-slide")];
    const dots = [...banner.querySelectorAll(".ad-dot")];

    const ads = [
      {
        title: "عروض نهاية السنة — خصومات قوية على الإلكترونيات",
        desc: "مساحة إعلانية قابلة للاستبدال بصورة (Banner) — تصميم أنيق بدون صندوق الصفحة.",
        primaryText: "تسوّق الآن", primaryHref: "#",
        secondaryText: "تفاصيل", secondaryHref: "#"
      },
      {
        title: "إعلان مميز — أجهزة ولابتوبات بأسعار منافسة",
        desc: "اعرض إعلانك هنا للوصول إلى آلاف الزوار يومياً على ركن.",
        primaryText: "احجز الإعلان", primaryHref: "#",
        secondaryText: "تواصل معنا", secondaryHref: "#"
      },
      {
        title: "عقارات وعروض إيجار — فرص محدودة",
        desc: "أضف عقارك الآن أو تصفّح أحدث العروض في منطقتك.",
        primaryText: "استعرض العقارات", primaryHref: "#",
        secondaryText: "أضف إعلان", secondaryHref: "#"
      }
    ];

    const tEl = document.getElementById("bannerTitle");
    const dEl = document.getElementById("bannerDesc");
    const pEl = document.getElementById("bannerPrimary");
    const sEl = document.getElementById("bannerSecondary");

    function show(idx) {
      slides.forEach((s, i) => s.classList.toggle("is-active", i === idx));
      dots.forEach((d, i) => d.classList.toggle("is-active", i === idx));
      const a = ads[idx];
      if (tEl) tEl.textContent = a.title;
      if (dEl) dEl.textContent = a.desc;
      if (pEl) { pEl.textContent = a.primaryText; pEl.href = a.primaryHref; }
      if (sEl) { sEl.textContent = a.secondaryText; sEl.href = a.secondaryHref; }
    }

    let idx = Math.floor(Math.random() * slides.length);
    show(idx);

    dots.forEach(btn => btn.addEventListener("click", () => {
      idx = parseInt(btn.dataset.idx || "0", 10);
      show(idx);
    }));

    setInterval(() => {
      idx = (idx + 1) % slides.length;
      show(idx);
    }, 2500);
  })();

  /* ================= Page Render ================= */
  function init() {
    renderNav();
    renderContent();
    bindNavScroll();

    // ✅ Scroll active category into view on page load
    setTimeout(() => {
      scrollActiveCategoryIntoView();
    }, 100);
  }

  function renderNav() {
    const nav = document.getElementById("mainCategoryNav");
    if (!nav) return;

    nav.innerHTML = categories.map(cat => {
      const imgSrc = getImg(cat);
      const isActive = String(activeMainId) === String(cat.id);
      return `
        <button
          type="button"
          tabindex="-1"
          data-id="${cat.id}"
          class="main-cat-btn flex flex-col items-center gap-2 py-4 px-3 min-w-[150px] max-w-[150px] font-bold text-sm transition text-center ${isActive ? "active" : "text-gray-600"}"
        >
          <div class="w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg">
            <img src="${imgSrc}" class="w-full h-full object-cover rounded-2xl" alt="${cat.title}">
          </div>
          <span class="text-center leading-tight line-clamp-2">${cat.title}</span>
        </button>
      `;
    }).join("");

    nav.querySelectorAll("button[data-id]").forEach(btn => {
      btn.addEventListener("click", () => setActive(btn.dataset.id));
      btn.addEventListener("mousedown", (e) => e.preventDefault());
    });
  }

  function setActive(id) {
    // Compare as strings for safety
    if (String(id) === String(activeMainId)) return;

    activeMainId = id;

    // ✅ Update URL with the selected category
    const url = new URL(window.location);
    url.searchParams.set('category', id);
    window.history.pushState({}, '', url);

    // Update active state
    document.querySelectorAll(".main-cat-btn").forEach(btn => {
      const isActive = String(btn.dataset.id) === String(id);
      if (isActive) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    renderContent();
    window.scrollTo({ top: 370, behavior: "smooth" });
  }

  // ✅ Scroll active category into view
  function scrollActiveCategoryIntoView() {
    const activeBtn = document.querySelector(`.main-cat-btn[data-id="${String(activeMainId)}"]`);
    if (activeBtn) {
      activeBtn.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
    }
  }

  function renderContent() {
    const container = document.getElementById("categoryContent");
    if (!container) return;

    const cat = categories.find(c => String(c.id) === String(activeMainId));
    if (!cat) {
      container.innerHTML = '<div class="text-center text-gray-500 py-12">لم يتم العثور على القسم</div>';
      return;
    }

    const mainImg = getImg(cat);

    container.innerHTML = `
      <div class="flex items-center gap-4 mb-8">
        <div class="w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg">
          <img src="${mainImg}" class="w-full h-full object-cover rounded-2xl" alt="${cat.title}">
        </div>
        <div>
          <h2 class="text-2xl font-extrabold text-gray-800">${cat.title}</h2>
          <p class="text-gray-500 text-sm">تصفح أفضل العروض في قسم ${cat.title}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        ${(cat.subs || []).map((sub, index) => {
          const subImg = getImg(sub);
          return `
            <div class="sub-category-card bg-white rounded-3xl p-6 pro-shadow flex flex-col cursor-pointer">
              <div class="flex items-center gap-4 mb-6">
                <div class="w-16 h-16 rounded-2xl flex items-center justify-center">
                  <img src="${subImg}" class="w-full h-full object-cover rounded-2xl" alt="${sub.title}">
                </div>
                <h3 class="text-xl font-bold text-gray-800">
                    <a href="/items/?category=${sub.id}">${sub.title}</a>
                </h3>
              </div>

              <div id="sub-content-${cat.id}-${index}" class="expandable-content relative">
                <div class="flex flex-wrap gap-2 pb-4">
                  ${(sub.levels || []).map(level => `
                    <a href="/items/?category=${sub.id}"
                      class="bg-gray-50 hover:bg-[#fff5ed] hover:text-[#ff7a18] transition border border-gray-100 px-4 py-2 rounded-xl text-sm font-semibold text-gray-600">
                      ${level}
                    </a>
                  `).join("")}
                </div>
                <div class="overlay-gradient absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-white to-transparent pointer-events-none"></div>
              </div>

              <button type="button" data-expand="${index}"
                class="mt-4 text-[#ff7a18] font-bold text-sm flex items-center gap-1 hover:underline">
                <span>عرض المزيد</span>
                <svg class="w-4 h-4 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </button>
            </div>
          `;
        }).join("")}
      </div>
    `;

    // bind expand buttons
    container.querySelectorAll("button[data-expand]").forEach(btn => {
      btn.addEventListener("click", () => {
        const idx = btn.dataset.expand;
        toggleExpand(cat.id, idx, btn);
      });
    });
  }

  function toggleExpand(catId, index, btn) {
    const content = document.getElementById(`sub-content-${catId}-${index}`);
    if (!content) return;

    const overlay = content.querySelector(".overlay-gradient");
    const icon = btn.querySelector("svg");
    const text = btn.querySelector("span");

    content.classList.toggle("expanded");

    if (content.classList.contains("expanded")) {
      if (overlay) overlay.style.display = "none";
      if (text) text.innerText = "عرض أقل";
      if (icon) icon.style.transform = "rotate(180deg)";
    } else {
      if (overlay) overlay.style.display = "block";
      if (text) text.innerText = "عرض المزيد";
      if (icon) icon.style.transform = "rotate(0deg)";
    }
  }

  /* ===== Nav arrows + drag scroll ===== */
  function bindNavScroll() {
    const nav = document.getElementById("mainCategoryNav");
    if (!nav) return;

    const amount = 260;
    const isRTL = document.documentElement.dir === "rtl";

    const rightBtn = document.getElementById("catRight");
    const leftBtn = document.getElementById("catLeft");

    if (rightBtn) {
      rightBtn.addEventListener("click", () => {
        nav.scrollBy({ left: isRTL ? amount : -amount, behavior: "smooth" });
      });
    }
    if (leftBtn) {
      leftBtn.addEventListener("click", () => {
        nav.scrollBy({ left: isRTL ? -amount : amount, behavior: "smooth" });
      });
    }

    // Drag scrolling
    let isDown = false;
    let startX = 0;
    let scrollLeft = 0;

    nav.addEventListener("mousedown", (e) => {
      isDown = true;
      nav.classList.add("cursor-grabbing");
      startX = e.pageX - nav.offsetLeft;
      scrollLeft = nav.scrollLeft;
    });

    nav.addEventListener("mouseleave", () => {
      isDown = false;
      nav.classList.remove("cursor-grabbing");
    });

    nav.addEventListener("mouseup", () => {
      isDown = false;
      nav.classList.remove("cursor-grabbing");
    });

    nav.addEventListener("mousemove", (e) => {
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX - nav.offsetLeft;
      const walk = (x - startX) * 1.5;
      nav.scrollLeft = scrollLeft - walk;
    });
  }

  document.addEventListener("DOMContentLoaded", init);

  // ✅ Handle browser back/forward buttons
  window.addEventListener('popstate', () => {
    activeMainId = getCategoryFromUrl();
    renderNav();
    renderContent();
    setTimeout(() => scrollActiveCategoryIntoView(), 100);
  });
})();