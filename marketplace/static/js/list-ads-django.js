(() => {
  "use strict";

  // ---------- hard guard: prevent double init even if script is injected twice ----------
  const ROOT = document.documentElement;
  if (ROOT.dataset.listAdsInit === "1") return;
  ROOT.dataset.listAdsInit = "1";

  const onReady = (fn) => {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn, { once: true });
    else fn();
  };

  onReady(() => {
    const pageRoot = document.querySelector(".list-ads-page[data-page='list-ads']");
    if (!pageRoot) return; // not on this page

    // Shared across IIFEs – will be set by initCategoryTree inside initFilters
    let _syncCatTree = () => {};

    // =====================================================================
    // VIP Slider (no conflicting sizing, no fixed-width fighting, RTL-safe)
    // =====================================================================
    (function initVip() {
      const rail = document.getElementById("featuredList");
      const dotsWrap = document.getElementById("vipDots");
      const section = document.getElementById("featuredSection");
      if (!rail || !dotsWrap) return;

      // Guard
      if (rail.dataset.init === "1") return;
      rail.dataset.init = "1";

      // REQUIRE: cards must have .featured-card in server-rendered HTML
      const logicalCards = [...rail.querySelectorAll(".featured-card")];
      const logicalCount = logicalCards.length;

      if (!logicalCount) {
        // If you don’t see VIP, it means your partial didn’t output featured-card.
        if (section) section.style.display = "none";
        return;
      }

      let vipPage = 0;
      let scrollEndTimer = null;

      const perPage = () => (window.innerWidth >= 1280 ? 4 : 1);

      const totalPages = () => Math.max(1, Math.ceil(logicalCount / perPage()));

      function buildDots() {
        const tp = totalPages();
        dotsWrap.innerHTML = Array.from({ length: tp }, (_, i) =>
          `<button type="button" class="vip-dot ${i === vipPage ? "is-active" : ""}" data-idx="${i}" aria-label="صفحة ${i + 1}"></button>`
        ).join("");
      }

      function setDot(i) {
        [...dotsWrap.querySelectorAll(".vip-dot")].forEach((d, k) =>
          d.classList.toggle("is-active", k === i)
        );
      }

      function applySnap(enabled) {
        if (window.innerWidth >= 1280) return; // desktop: no snap by design
        rail.style.scrollSnapType = enabled ? "x mandatory" : "none";
      }

      // RTL-safe: use scrollLeft directly based on element offset
      function scrollToCardIndex(cardIndex, smooth) {
          const cards = [...rail.querySelectorAll(".featured-card")];
          const target = cards[Math.max(0, Math.min(cards.length - 1, cardIndex))];
          if (!target) return;

          applySnap(false);

          // RTL-safe: works correctly in RTL across browsers
          target.scrollIntoView({
            behavior: smooth ? "smooth" : "auto",
            inline: "start",
            block: "nearest"
          });

          clearTimeout(scrollEndTimer);
          scrollEndTimer = setTimeout(() => applySnap(true), 260);
        }

      function scrollToPage(pageIdx, smooth = true) {
        const tp = totalPages();
        vipPage = Math.max(0, Math.min(tp - 1, pageIdx));
        const targetIndex = vipPage * perPage();
        scrollToCardIndex(targetIndex, smooth);
        setDot(vipPage);
      }

      // Dots + buttons (delegate + guard against double-bind)
      document.getElementById("vipPrev")?.addEventListener("click", () => scrollToPage(vipPage - 1, true));
      document.getElementById("vipNext")?.addEventListener("click", () => scrollToPage(vipPage + 1, true));

      dotsWrap.addEventListener("click", (e) => {
        const btn = e.target.closest(".vip-dot");
        if (!btn) return;
        const i = parseInt(btn.dataset.idx || "0", 10);
        if (!Number.isNaN(i)) scrollToPage(i, true);
      });

      // dot sync after manual scroll settles
      rail.addEventListener("scroll", () => {
        clearTimeout(scrollEndTimer);
        scrollEndTimer = setTimeout(() => {
          const cards = [...rail.querySelectorAll(".featured-card")];
          const pp = perPage();
          const tp = totalPages();

          const center = rail.scrollLeft + rail.clientWidth / 2;
          let best = 0;
          let bestDist = Infinity;

          for (let i = 0; i < cards.length; i++) {
            const c = cards[i];
            const cCenter = c.offsetLeft + c.offsetWidth / 2;
            const dist = Math.abs(cCenter - center);
            if (dist < bestDist) { bestDist = dist; best = i; }
          }

          const logicalIdx = Math.max(0, Math.min(logicalCount - 1, best));
          const page = Math.max(0, Math.min(tp - 1, Math.floor(logicalIdx / pp)));

          vipPage = page;
          setDot(vipPage);
          applySnap(true);
        }, 90);
      }, { passive: true });

      window.addEventListener("resize", () => {
        // rebuild dots, keep current vipPage in bounds
        const tp = totalPages();
        vipPage = Math.max(0, Math.min(tp - 1, vipPage));
        buildDots();
        setDot(vipPage);
        applySnap(true);
      });

      // init
      buildDots();
      applySnap(true);
      scrollToPage(0, false);
    })();

    // =====================================================================
    // AJAX filtering + load more (init-guarded)
    // =====================================================================
    (function initFilters() {
      const form = document.getElementById("filtersForm");
      const adsList = document.getElementById("adsList");
      if (!form || !adsList) return;

      if (form.dataset.init === "1") return;
      form.dataset.init = "1";

      const loadMoreBtn = document.getElementById("loadMoreBtn");
      const noResults = document.getElementById("noResults");
      const clearAfterNoResults = document.getElementById("clearAfterNoResults");
      const resetFiltersBtn = document.getElementById("resetFilters");
      const pageField = document.getElementById("pageField");
      const resultsTotal = document.getElementById("resultsTotal");
      const resultsVisible = document.getElementById("resultsVisible");

      const priceMin = document.getElementById("filterPriceMin");
      const priceMax = document.getElementById("filterPriceMax");

      // ✅ sync UI from URL on first load (supports ?categories=3 while select is name="category")
        (function syncFiltersFromUrl() {
          const params = new URLSearchParams(window.location.search);

          // alias: URL uses "categories" but form uses "category"
          if (!params.has("category") && params.has("categories")) {
            params.set("category", params.get("categories") || "");
          }

          // selects (includes #filterCategory)
          form.querySelectorAll("select").forEach(sel => {
            if (!sel.name) return;
            if (params.has(sel.name)) sel.value = params.get(sel.name) || "";
          });

          // radios
          const radioNames = new Set();
          form.querySelectorAll('input[type="radio"]').forEach(r => r.name && radioNames.add(r.name));
          radioNames.forEach(name => {
            if (!params.has(name)) return;
            const v = params.get(name) || "";
            const target = form.querySelector(
              `input[type="radio"][name="${CSS.escape(name)}"][value="${CSS.escape(v)}"]`
            );
            if (target) target.checked = true;
          });

          // price inputs
          if (priceMin?.name && params.has(priceMin.name)) priceMin.value = params.get(priceMin.name) || "";
          if (priceMax?.name && params.has(priceMax.name)) priceMax.value = params.get(priceMax.name) || "";

          // page
          if (pageField && params.has("page")) pageField.value = params.get("page") || "1";
        })();


      let isLoading = false;

        function setLoadMoreState(hasMore) {
          if (!loadMoreBtn) return;

          if (hasMore) {
            loadMoreBtn.disabled = false;
            loadMoreBtn.textContent = "تحميل المزيد من الإعلانات";
            loadMoreBtn.classList.remove("opacity-60", "cursor-not-allowed");
            loadMoreBtn.classList.add("hover:bg-[#e06600]");
          } else {
            loadMoreBtn.disabled = true;
            loadMoreBtn.textContent = "لا يوجد إعلانات جديدة لعرضها";
            loadMoreBtn.classList.add("opacity-60", "cursor-not-allowed");
            loadMoreBtn.classList.remove("hover:bg-[#e06600]");
          }
        }

      function resetToFirstPage() {
        if (pageField) pageField.value = "1";
      }

      function qsFromForm() {
        const fd = new FormData(form);
        const params = new URLSearchParams();
        for (const [k, v] of fd.entries()) {
          const val = (v || "").toString().trim();
          if (val !== "") params.set(k, val);
        }
        if (!params.get("page")) params.set("page", "1");
        return params;
      }

      async function fetchResults({ append = false } = {}) {
        if (isLoading) return;
        isLoading = true;

        const params = qsFromForm();
        const url = `${form.action}?${params.toString()}`;

        try {
          const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
          if (!res.ok) throw new Error("Bad response");
          const data = await res.json();

          if (!append) adsList.innerHTML = data.html || "";
          else adsList.insertAdjacentHTML("beforeend", data.html || "");

          if (resultsTotal) resultsTotal.textContent = String(data.total_count ?? 0);
          if (resultsVisible) resultsVisible.textContent = String(data.visible_count ?? 0);

          if (noResults) noResults.classList.toggle("hidden", (data.total_count ?? 0) !== 0);

          setLoadMoreState(!!data.has_more);

          const clean = new URL(window.location.href);
          clean.search = params.toString();
          window.history.replaceState({}, "", clean.toString());
        } finally {
          isLoading = false;
        }
      }

      // Submit prevention (we use AJAX)
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        resetToFirstPage();
        fetchResults({ append: false });
      });

      // Apply on selects + radios
      form.querySelectorAll("select").forEach(el => {
        el.addEventListener("change", () => {
          resetToFirstPage();
          fetchResults({ append: false });
          document.getElementById("allAdsAnchor")?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      });

      form.querySelectorAll('input[type="radio"]').forEach(el => {
        el.addEventListener("change", () => {
          resetToFirstPage();
          fetchResults({ append: false });
          document.getElementById("allAdsAnchor")?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      });

      // Debounced price typing
      let priceTimer = null;
      function scheduleApply(ms = 450) {
        clearTimeout(priceTimer);
        priceTimer = setTimeout(() => {
          resetToFirstPage();
          fetchResults({ append: false });
          document.getElementById("allAdsAnchor")?.scrollIntoView({ behavior: "smooth", block: "start" });
        }, ms);
      }

      [priceMin, priceMax].forEach(el => {
        if (!el) return;
        el.addEventListener("input", () => scheduleApply(450));
        el.addEventListener("change", () => {
          resetToFirstPage();
          fetchResults({ append: false });
          document.getElementById("allAdsAnchor")?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      });

      // reset filters (desktop)
      resetFiltersBtn?.addEventListener("click", () => {
        form.querySelectorAll("select").forEach(s => (s.value = ""));
        ["condition", "seller_type", "time"].forEach(name => {
          const r = form.querySelector(`input[name="${name}"][value=""]`);
          if (r) r.checked = true;
        });
        const sortLatest = form.querySelector(`input[name="sort"][value="latest"]`);
        if (sortLatest) sortLatest.checked = true;

        if (priceMin) priceMin.value = "";
        if (priceMax) priceMax.value = "";

        resetToFirstPage();
        fetchResults({ append: false });
      });

      clearAfterNoResults?.addEventListener("click", () => resetFiltersBtn?.click());

      // load more
      loadMoreBtn?.addEventListener("click", () => {
          if (loadMoreBtn.disabled) return;
          const current = parseInt(pageField?.value || "1", 10) || 1;
          if (pageField) pageField.value = String(current + 1);
          fetchResults({ append: true });
        });

      // ---- Category Tree ----

      (function initCategoryTree() {
        const tree = document.getElementById("filterCategoryTree");
        const sel  = document.getElementById("filterCategory");
        if (!tree || !sel) return;

        // Expand/collapse arrow click
        tree.addEventListener("click", (e) => {
          const arrow = e.target.closest(".cat-tree-arrow");
          if (arrow) {
            e.stopPropagation();
            const catId   = arrow.dataset.for;
            const children = document.getElementById("cat-children-" + catId);
            if (!children) return;
            const isOpen  = children.style.display !== "none";
            children.style.display = isOpen ? "none" : "";
            arrow.classList.toggle("is-open", !isOpen);
            arrow.setAttribute("aria-expanded", String(!isOpen));
            return;
          }

          // Category label click
          const item = e.target.closest(".cat-tree-item");
          if (!item) return;
          const catId = item.dataset.catId ?? "";

          sel.value = catId;
          _syncCatTree();

          resetToFirstPage();
          fetchResults({ append: false });
          document.getElementById("allAdsAnchor")?.scrollIntoView({ behavior: "smooth", block: "start" });
        });

        // Sync visual selection + auto-expand parents of selected item
        function syncVisualSelection() {
          const v = sel.value ?? "";
          tree.querySelectorAll(".cat-tree-item").forEach(el => {
            el.classList.toggle("is-selected", (el.dataset.catId ?? "") === v);
          });

          if (!v) return;

          // Walk up the DOM from the selected item and open each cat-tree-children ancestor
          const selectedEl = tree.querySelector(`.cat-tree-item[data-cat-id="${CSS.escape(v)}"]`);
          if (!selectedEl) return;

          let node = selectedEl.parentElement;
          while (node && node !== tree) {
            if (node.classList.contains("cat-tree-children")) {
              node.style.display = "";
              const parentId = node.dataset.parentId;
              if (parentId) {
                const arrowBtn = tree.querySelector(`.cat-tree-arrow[data-for="${CSS.escape(parentId)}"]`);
                if (arrowBtn) {
                  arrowBtn.classList.add("is-open");
                  arrowBtn.setAttribute("aria-expanded", "true");
                }
              }
            }
            node = node.parentElement;
          }
        }

        _syncCatTree = syncVisualSelection;
        syncVisualSelection();
      })();

      // Sync tree after reset (fires after the existing reset listener that clears sel.value)
      resetFiltersBtn?.addEventListener("click", () => _syncCatTree());

    })();

    // =====================================================================
    // Mobile Dock + Sheet (init-guarded)
    // =====================================================================
    (function initMobileFilters() {
      const mfDock = document.getElementById("mfDock");
      const mfSheet = document.getElementById("mfSheet");
      const mfBody = document.getElementById("mfBody");
      const mfClose = document.getElementById("mfClose");
      const mfApply = document.getElementById("mfApply");
      const resetOneBtn = document.getElementById("mfResetOne");
      const mfSheetTitle = document.getElementById("mfSheetTitle");
      const mfSheetSub = document.getElementById("mfSheetSub");
      const mfSheetIcon = document.getElementById("mfSheetIcon");

      const form = document.getElementById("filtersForm");
      if (!mfDock || !mfSheet || !mfBody || !form) return;

      if (mfDock.dataset.init === "1") return;
      mfDock.dataset.init = "1";

      const priceMin = document.getElementById("filterPriceMin");
      const priceMax = document.getElementById("filterPriceMax");


      let activeKey = null;

      function isMobile() { return window.matchMedia("(max-width: 767px)").matches; }
      function sheetIsOpen() { return mfSheet.classList.contains("is-open"); }

      function syncSheetPosition() {
        const dockH = mfDock.getBoundingClientRect().height || 86;
        document.documentElement.style.setProperty("--mf-dock-h", dockH + "px");
      }

      function getChecked(name) {
        const r = form.querySelector(`input[name="${name}"]:checked`);
        return r ? r.value : "";
      }

      function setRadioValue(name, value) {
        const r = form.querySelector(`input[name="${name}"][value="${CSS.escape(String(value))}"]`);
        if (r) r.checked = true;
      }

      function segHTML(name, options, checkedValue) {
        return `
          <div class="seg-btn" role="group" aria-label="${name}">
            ${options.map(o => `
              <input type="radio" id="${o.id}" name="${name}" value="${o.value}" ${String(o.value) === String(checkedValue) ? "checked" : ""}>
              <label for="${o.id}">${o.label}</label>
            `).join("")}
          </div>`;
      }

      function buildSheetContent(key) {
        const catSel = document.getElementById("filterCategory");
        const citySel = document.getElementById("filterCity");

        if (key === "category") {
          return `
            <div>
              <label class="filter-title">القسم</label>
              <select id="mfCategory" class="filter-select">${catSel?.innerHTML || ""}</select>
            </div>`;
        }
        if (key === "city") {
          return `
            <div>
              <label class="filter-title">المدينة</label>
              <select id="mfCity" class="filter-select">${citySel?.innerHTML || ""}</select>
            </div>`;
        }
        if (key === "condition") {
          return `
            <div>
              <label class="filter-title">حالة المنتج</label>
              ${segHTML("mfCondition", [
                { value: "", label: "الكل", id: "mf_cond_all" },
                { value: "new", label: "جديد", id: "mf_cond_new" },
                { value: "used", label: "مستعمل", id: "mf_cond_used" }
              ], getChecked("condition"))}
            </div>`;
        }
        if (key === "price") {
          return `
            <div>
              <label class="filter-title">نطاق السعر (د.أ)</label>
              <div class="grid grid-cols-2 gap-2">
                <input id="mfPriceMin" type="number" min="0" placeholder="من" class="filter-input" value="${priceMin?.value || ""}">
                <input id="mfPriceMax" type="number" min="0" placeholder="إلى" class="filter-input" value="${priceMax?.value || ""}">
              </div>
            </div>`;
        }
        if (key === "time") {
          return `
            <div>
              <label class="filter-title">الفترة الزمنية</label>
              ${segHTML("mfTime", [
                { value: "", label: "أي وقت", id: "mf_time_any" },
                { value: "24", label: "24 ساعة", id: "mf_time_24" },
                { value: "168", label: "7 أيام", id: "mf_time_7" },
                { value: "720", label: "30 يوم", id: "mf_time_30" }
              ], getChecked("time"))}
            </div>`;
        }
        if (key === "sort") {
          return `
            <div>
              <label class="filter-title">ترتيب حسب</label>
              ${segHTML("mfSort", [
                { value: "latest", label: "الأحدث", id: "mf_sort_latest" },
                { value: "priceAsc", label: "الأقل", id: "mf_sort_asc" },
                { value: "priceDesc", label: "الأعلى", id: "mf_sort_desc" }
              ], getChecked("sort") || "latest")}
            </div>`;
        }
        return "";
      }

      function commitFromSheet() {
        if (!activeKey) return;

        if (activeKey === "category") {
          const el = document.getElementById("mfCategory");
          const desktop = document.getElementById("filterCategory");
          if (el && desktop) { desktop.value = el.value; _syncCatTree(); }
        }

        if (activeKey === "city") {
          const el = document.getElementById("mfCity");
          const desktop = document.getElementById("filterCity");
          if (el && desktop) desktop.value = el.value;
        }

        if (activeKey === "condition") {
          const r = document.querySelector('input[name="mfCondition"]:checked');
          setRadioValue("condition", r ? r.value : "");
        }

        if (activeKey === "price") {
          const minEl = document.getElementById("mfPriceMin");
          const maxEl = document.getElementById("mfPriceMax");
          if (priceMin) priceMin.value = minEl ? (minEl.value || "") : "";
          if (priceMax) priceMax.value = maxEl ? (maxEl.value || "") : "";
        }

        if (activeKey === "time") {
          const r = document.querySelector('input[name="mfTime"]:checked');
          setRadioValue("time", r ? r.value : "");
        }

        if (activeKey === "sort") {
          const r = document.querySelector('input[name="mfSort"]:checked');
          setRadioValue("sort", r ? r.value : "latest");
        }

        // trigger desktop flow by dispatching submit
        const submit = new Event("submit", { cancelable: true });
        form.dispatchEvent(submit);
        document.getElementById("allAdsAnchor")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }

      function resetOnlyActiveKey() {
        if (!activeKey) return;
        if (activeKey === "category") { document.getElementById("filterCategory").value = ""; _syncCatTree(); }
        if (activeKey === "city") document.getElementById("filterCity").value = "";
        if (activeKey === "condition") setRadioValue("condition", "");
        if (activeKey === "price") { if (priceMin) priceMin.value = ""; if (priceMax) priceMax.value = ""; }
        if (activeKey === "time") setRadioValue("time", "");
        if (activeKey === "sort") setRadioValue("sort", "latest");

        const submit = new Event("submit", { cancelable: true });
        form.dispatchEvent(submit);
      }

      function openSheet(key) {
        if (!isMobile()) return;

        if (sheetIsOpen() && activeKey === key) {
          closeSheet();
          return;
        }

        activeKey = key;
        mfDock.querySelectorAll(".mf-item").forEach(b => b.classList.toggle("is-active", b.dataset.key === key));

        mfBody.innerHTML = buildSheetContent(key);

        const meta = {
          category: { title: "القسم", ico: "≡", sub: "اختر القسم وسيتم الإغلاق تلقائياً" },
          city: { title: "المدينة", ico: "📍", sub: "اختر المدينة وسيتم الإغلاق تلقائياً" },
          condition: { title: "الحالة", ico: "✓", sub: "اختر الحالة وسيتم الإغلاق تلقائياً" },
          price: { title: "السعر", ico: "د.أ", sub: "حدّد النطاق ثم اضغط تطبيق" },
          time: { title: "الوقت", ico: "⏱", sub: "اختر الفترة وسيتم الإغلاق تلقائياً" },
          sort: { title: "الترتيب", ico: "⇅", sub: "اختر الترتيب وسيتم الإغلاق تلقائياً" }
        }[key] || { title: "تصفية", ico: "⚙", sub: "" };

        if (mfSheetTitle) mfSheetTitle.textContent = meta.title;
        if (mfSheetSub) mfSheetSub.textContent = meta.sub;
        if (mfSheetIcon) mfSheetIcon.textContent = meta.ico;

        // init controls
        if (key === "category") {
          const el = document.getElementById("mfCategory");
          const desktop = document.getElementById("filterCategory");
          if (el && desktop) el.value = desktop.value || "";
          el?.addEventListener("change", () => { commitFromSheet(); closeSheet(); });
        }

        if (key === "city") {
          const el = document.getElementById("mfCity");
          const desktop = document.getElementById("filterCity");
          if (el && desktop) el.value = desktop.value || "";
          el?.addEventListener("change", () => { commitFromSheet(); closeSheet(); });
        }

        if (key === "condition") {
          document.querySelectorAll('input[name="mfCondition"]').forEach(r =>
            r.addEventListener("change", () => { commitFromSheet(); closeSheet(); })
          );
        }

        if (key === "time") {
          document.querySelectorAll('input[name="mfTime"]').forEach(r =>
            r.addEventListener("change", () => { commitFromSheet(); closeSheet(); })
          );
        }

        if (key === "sort") {
          document.querySelectorAll('input[name="mfSort"]').forEach(r =>
            r.addEventListener("change", () => { commitFromSheet(); closeSheet(); })
          );
        }

        syncSheetPosition();
        mfSheet.classList.add("is-open");
      }

      function closeSheet() {
        mfSheet.classList.remove("is-open");
        mfDock.querySelectorAll(".mf-item").forEach(b => b.classList.remove("is-active"));
        activeKey = null;
      }

      mfDock.querySelectorAll(".mf-item").forEach(btn => {
        btn.addEventListener("click", () => openSheet(btn.dataset.key));
      });

      mfClose?.addEventListener("click", closeSheet);

      mfApply?.addEventListener("click", () => {
        if (activeKey === "price") commitFromSheet();
        closeSheet();
      });

      resetOneBtn?.addEventListener("click", () => {
        resetOnlyActiveKey();
        if (activeKey && activeKey !== "price") closeSheet();
      });

      window.addEventListener("resize", () => {
        if (!isMobile()) { closeSheet(); return; }
        syncSheetPosition();
      });

      syncSheetPosition();
    })();
  });
})();
