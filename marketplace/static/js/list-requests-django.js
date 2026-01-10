// static/js/list-requests-django.js
(() => {
  "use strict";

  const ROOT = document.documentElement;
  if (ROOT.dataset.listRequestsInit === "1") return;
  ROOT.dataset.listRequestsInit = "1";

  const onReady = (fn) => {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn, { once: true });
    else fn();
  };

  onReady(() => {
    const pageRoot = document.querySelector(".list-requests-page[data-page='list-requests']");
    if (!pageRoot) return;

    // ---------- Elements ----------
    const form = document.getElementById("filtersForm");
    const filterCategory = document.getElementById("filterCategory");
    const filterCity = document.getElementById("filterCity");
    const filterMin = document.getElementById("filterPriceMin");
    const filterMax = document.getElementById("filterPriceMax");
    const pageField = document.getElementById("pageField");

    const listEl = document.getElementById("adsList");
    const totalEl = document.getElementById("resultsTotal");
    const visEl = document.getElementById("resultsVisible");
    const loadMoreBtn = document.getElementById("loadMoreBtn");
    const noResults = document.getElementById("noResults");

    const resetBtn = document.getElementById("resetFilters");
    const clearAfterNoResults = document.getElementById("clearAfterNoResults");


    function setLoadMoreState(hasMore) {
      if (!loadMoreBtn) return;

      if (hasMore) {
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = "تحميل المزيد من الطلبات";
        loadMoreBtn.classList.remove("opacity-60", "cursor-not-allowed");
        loadMoreBtn.classList.add("hover:bg-[--rukn-green-700]");
      } else {
        loadMoreBtn.disabled = true;
        loadMoreBtn.textContent = "لا يوجد طلبات جديدة لعرضها";
        loadMoreBtn.classList.add("opacity-60", "cursor-not-allowed");
        loadMoreBtn.classList.remove("hover:bg-[--rukn-green-700]");
      }
    }


    // ---------- Helpers ----------
    const setRadioGroupValue = (name, valueToCheck) => {
      const r = document.querySelector(`input[name="${name}"][value="${CSS.escape(String(valueToCheck))}"]`);
      if (r) r.checked = true;
    };

    const getRadioValue = (name, fallback = "") => {
      const r = document.querySelector(`input[name="${name}"]:checked`);
      return r ? r.value : fallback;
    };

    // ✅ robust select setter (works if option values are ids OR slugs OR stored in data-id)
    const setSelectSmart = (selectEl, desired) => {
      if (!selectEl) return false;
      const want = String(desired ?? "").trim();
      if (!want) return false;

      // 1) direct value match
      selectEl.value = want;
      if (String(selectEl.value) === want) return true;

      // 2) try data-id match (if your options are like <option value="cars" data-id="6">...)
      const opt = [...selectEl.options].find((o) => String(o.dataset?.id || "") === want);
      if (opt) {
        selectEl.value = opt.value;
        return true;
      }

      // 3) not found
      return false;
    };

    // ✅ Sync filters from URL (retry a few times in case options are injected later)
    const syncFiltersFromUrl = () => {
      const params = new URLSearchParams(window.location.search);

      const cat = params.get("categories") || params.get("category") || "";
      const city = params.get("city") || "";
      const minB = params.get("min_budget") || "";
      const maxB = params.get("max_budget") || "";

      if (city && filterCity) filterCity.value = city;
      if (minB && filterMin) filterMin.value = minB;
      if (maxB && filterMax) filterMax.value = maxB;

      if (params.has("condition")) setRadioGroupValue("condition", params.get("condition") || "");
      if (params.has("seller_type")) setRadioGroupValue("seller_type", params.get("seller_type") || "");
      if (params.has("time")) setRadioGroupValue("time", params.get("time") || "");
      if (params.has("sort")) setRadioGroupValue("sort", params.get("sort") || "latest");

      // page (optional)
      const p = params.get("page");
      if (p && pageField) pageField.value = p;

      // category (robust + retry)
      if (cat && filterCategory) {
        let tries = 0;
        const trySet = () => {
          tries += 1;
          const ok = setSelectSmart(filterCategory, cat);
          if (ok) return;

          // options might arrive later -> retry a bit
          if (tries < 10) setTimeout(trySet, 80);
        };
        trySet();
      }
    };

    // run once
    syncFiltersFromUrl();
    setLoadMoreState(!loadMoreBtn?.classList.contains("hidden"));


    const buildQuery = () => {
      const fd = new FormData(form);

      // normalize page
      if (!fd.get("page")) fd.set("page", pageField?.value || "1");

      // remove empty fields
      [...fd.keys()].forEach((k) => {
        const vals = fd.getAll(k);
        if (vals.length === 1 && (vals[0] === "" || vals[0] == null)) fd.delete(k);
      });

      const qs = new URLSearchParams();
      for (const [k, v] of fd.entries()) qs.append(k, v);
      return qs.toString();
    };

    const applyFilters = async ({ append = false } = {}) => {
      if (!form || !listEl) return;

      const url = new URL(form.action, window.location.origin);
      url.search = buildQuery();

      const res = await fetch(url.toString(), {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });

      if (!res.ok) return;

      const data = await res.json();

      if (!append) listEl.innerHTML = data.html || "";
      else listEl.insertAdjacentHTML("beforeend", data.html || "");

      if (totalEl) totalEl.textContent = String(data.total_count ?? 0);
      if (visEl) visEl.textContent = String(data.visible_count ?? 0);

      const total = Number(data.total_count ?? 0);
      if (noResults) noResults.classList.toggle("hidden", total !== 0);

      setLoadMoreState(!!data.has_more);


      if (!append) {
        document.getElementById("allAdsAnchor")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    };

    // ---------- Desktop listeners ----------
    [filterCategory, filterCity].forEach((el) =>
      el &&
      el.addEventListener("change", () => {
        if (pageField) pageField.value = "1";
        applyFilters({ append: false });
      })
    );

    document.querySelectorAll('input[name="condition"]').forEach((r) =>
      r.addEventListener("change", () => {
        if (pageField) pageField.value = "1";
        applyFilters({ append: false });
      })
    );

    document.querySelectorAll('input[name="seller_type"]').forEach((r) =>
      r.addEventListener("change", () => {
        if (pageField) pageField.value = "1";
        applyFilters({ append: false });
      })
    );

    document.querySelectorAll('input[name="time"]').forEach((r) =>
      r.addEventListener("change", () => {
        if (pageField) pageField.value = "1";
        applyFilters({ append: false });
      })
    );

    document.querySelectorAll('input[name="sort"]').forEach((r) =>
      r.addEventListener("change", () => {
        if (pageField) pageField.value = "1";
        applyFilters({ append: false });
      })
    );

    let priceTimer = null;
    const schedulePriceApply = (ms = 500) => {
      clearTimeout(priceTimer);
      priceTimer = setTimeout(() => {
        if (pageField) pageField.value = "1";
        applyFilters({ append: false });
      }, ms);
    };
    const flushPriceApply = () => {
      clearTimeout(priceTimer);
      if (pageField) pageField.value = "1";
      applyFilters({ append: false });
    };

    [filterMin, filterMax].forEach((el) => {
      if (!el) return;
      el.addEventListener("input", () => schedulePriceApply(500));
      el.addEventListener("change", () => flushPriceApply());
    });

    resetBtn?.addEventListener("click", () => {
      if (filterCategory) filterCategory.value = "";
      if (filterCity) filterCity.value = "";
      if (filterMin) filterMin.value = "";
      if (filterMax) filterMax.value = "";

      setRadioGroupValue("seller_type", "");
      setRadioGroupValue("time", "");
      setRadioGroupValue("sort", "latest");
      setRadioGroupValue("condition", "");

      if (pageField) pageField.value = "1";
      applyFilters({ append: false });
    });

    clearAfterNoResults?.addEventListener("click", () => resetBtn?.click());

    loadMoreBtn?.addEventListener("click", () => {
      if (loadMoreBtn.disabled) return;

      const current = parseInt(pageField?.value || "1", 10) || 1;
      if (pageField) pageField.value = String(current + 1);
      applyFilters({ append: true });
    });


    // ---------- VIP slider (same behavior as mockup) ----------
    let vipPage = 0;
    let vipBound = false;
    let vipScrollEndTimer = null;

    function initVip() {
      const rail = document.getElementById("featuredList");
      const dotsWrap = document.getElementById("vipDots");
      if (!rail || !dotsWrap) return;

      const cards = [...rail.querySelectorAll(".featured-card")];
      if (!cards.length) return;

      const logicalCount = Number(rail.dataset.logicalCount || cards.length);
      const perPage = window.innerWidth >= 1280 ? 4 : 1;
      const totalPages = Math.max(1, Math.ceil(logicalCount / perPage));

      dotsWrap.innerHTML = Array.from({ length: totalPages }, (_, i) =>
        `<button type="button" class="vip-dot ${i === 0 ? "is-active" : ""}" data-idx="${i}" aria-label="صفحة ${i + 1}"></button>`
      ).join("");

      const setVipDot = (i) => {
        [...dotsWrap.querySelectorAll(".vip-dot")].forEach((d, idx) =>
          d.classList.toggle("is-active", idx === i)
        );
      };

      const applySnapMode = (enabled) => {
        if (window.innerWidth >= 1280) return;
        rail.style.scrollSnapType = enabled ? "x mandatory" : "none";
      };

      const scrollToPage = (i, smooth = true) => {
        vipPage = Math.max(0, Math.min(totalPages - 1, i));
        const targetIndex = vipPage * perPage;
        const target = cards[Math.min(targetIndex, cards.length - 1)];
        if (!target) return;

        applySnapMode(false);
        rail.style.scrollBehavior = smooth ? "smooth" : "auto";
        target.scrollIntoView({ behavior: smooth ? "smooth" : "auto", inline: "start", block: "nearest" });

        setVipDot(vipPage);

        clearTimeout(vipScrollEndTimer);
        vipScrollEndTimer = setTimeout(() => {
          rail.style.scrollBehavior = "auto";
          applySnapMode(true);
        }, 260);
      };

      if (!vipBound) {
        vipBound = true;

        document.getElementById("vipPrev")?.addEventListener("click", () => scrollToPage(vipPage - 1, true));
        document.getElementById("vipNext")?.addEventListener("click", () => scrollToPage(vipPage + 1, true));

        dotsWrap.addEventListener("click", (e) => {
          const btn = e.target.closest(".vip-dot");
          if (!btn) return;
          const idx = parseInt(btn.dataset.idx || "0", 10);
          scrollToPage(idx, true);
        });

        rail.addEventListener(
          "scroll",
          () => {
            clearTimeout(vipScrollEndTimer);
            vipScrollEndTimer = setTimeout(() => {
              const railRect = rail.getBoundingClientRect();
              const center = railRect.left + railRect.width / 2;

              let bestIdx = 0;
              let bestDist = Infinity;

              for (let i = 0; i < cards.length; i++) {
                const r = cards[i].getBoundingClientRect();
                const cCenter = r.left + r.width / 2;
                const dist = Math.abs(cCenter - center);
                if (dist < bestDist) {
                  bestDist = dist;
                  bestIdx = i;
                }
              }

              const logicalIdx = bestIdx % logicalCount;
              const page = Math.floor(logicalIdx / perPage);

              if (page !== vipPage) {
                vipPage = page;
                setVipDot(vipPage);
              }

              rail.style.scrollBehavior = "auto";
              applySnapMode(true);
            }, 90);
          },
          { passive: true }
        );

        window.addEventListener("resize", () => initVip());
      }

      vipPage = 0;
      setVipDot(0);
      applySnapMode(true);
      scrollToPage(0, false);
    }

    initVip();

    // ---------- Mobile filter sheet ----------
    const mfDock = document.getElementById("mfDock");
    const mfSheet = document.getElementById("mfSheet");
    const mfBody = document.getElementById("mfBody");
    const mfClose = document.getElementById("mfClose");
    const mfApply = document.getElementById("mfApply");
    const resetOneBtn = document.getElementById("mfResetOne");
    const mfSheetTitle = document.getElementById("mfSheetTitle");
    const mfSheetSub = document.getElementById("mfSheetSub");
    const mfSheetIcon = document.getElementById("mfSheetIcon");

    let activeKey = null;

    function isMobile() { return window.matchMedia("(max-width: 767px)").matches; }

    function syncSheetPosition() {
      const dockH = mfDock?.getBoundingClientRect().height || 86;
      document.documentElement.style.setProperty("--mf-dock-h", dockH + "px");
    }

    function sheetIsOpen() { return mfSheet?.classList.contains("is-open"); }

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
      if (key === "category") {
        return `
          <div>
            <label class="filter-title">القسم</label>
            <select id="mfCategory" class="filter-select">${filterCategory?.innerHTML || ""}</select>
          </div>`;
      }

      if (key === "city") {
        return `
          <div>
            <label class="filter-title">المدينة</label>
            <select id="mfCity" class="filter-select">${filterCity?.innerHTML || ""}</select>
          </div>`;
      }

      if (key === "condition") {
        const v = getRadioValue("condition", "");
        return `
          <div>
            <label class="filter-title">حالة المنتج</label>
            ${segHTML("mfCondition", [
              { value: "", label: "الكل", id: "mf_cond_all" },
              { value: "new", label: "جديد", id: "mf_cond_new" },
              { value: "used", label: "مستعمل", id: "mf_cond_used" }
            ], v)}
          </div>`;
      }

      if (key === "price") {
        return `
          <div>
            <label class="filter-title">نطاق الميزانية (د.أ)</label>
            <div class="grid grid-cols-2 gap-2">
              <input id="mfPriceMin" type="number" min="0" placeholder="من" class="filter-input" value="${filterMin?.value || ""}">
              <input id="mfPriceMax" type="number" min="0" placeholder="إلى" class="filter-input" value="${filterMax?.value || ""}">
            </div>
          </div>`;
      }

      if (key === "time") {
        const v = getRadioValue("time", "");
        return `
          <div>
            <label class="filter-title">الفترة الزمنية</label>
            ${segHTML("mfTime", [
              { value: "", label: "أي وقت", id: "mf_time_any" },
              { value: "24", label: "24 ساعة", id: "mf_time_24" },
              { value: "168", label: "7 أيام", id: "mf_time_7" },
              { value: "720", label: "30 يوم", id: "mf_time_30" }
            ], v)}
          </div>`;
      }

      if (key === "sort") {
        const v = getRadioValue("sort", "latest");
        return `
          <div>
            <label class="filter-title">ترتيب حسب</label>
            ${segHTML("mfSort", [
              { value: "latest", label: "الأحدث", id: "mf_sort_latest" },
              { value: "budgetAsc", label: "الأقل", id: "mf_sort_asc" },
              { value: "budgetDesc", label: "الأعلى", id: "mf_sort_desc" }
            ], v)}
          </div>`;
      }

      return "";
    }

    function openSheet(key) {
      if (!mfSheet || !mfBody) return;

      if (sheetIsOpen() && activeKey === key) {
        closeSheet();
        return;
      }

      activeKey = key;

      mfDock?.querySelectorAll(".mf-item").forEach(b => b.classList.toggle("is-active", b.dataset.key === key));

      mfBody.innerHTML = buildSheetContent(key);
      initSheetControls(key);

      const map = {
        category: { title: "القسم", ico: "≡", sub: "اختر القسم وسيتم الإغلاق تلقائياً" },
        city: { title: "المدينة", ico: "📍", sub: "اختر المدينة وسيتم الإغلاق تلقائياً" },
        condition: { title: "الحالة", ico: "✓", sub: "اختر الحالة وسيتم الإغلاق تلقائياً" },
        price: { title: "السعر", ico: "د.أ", sub: "حدّد النطاق ثم اضغط تطبيق" },
        time: { title: "الوقت", ico: "⏱", sub: "اختر الفترة وسيتم الإغلاق تلقائياً" },
        sort: { title: "الترتيب", ico: "⇅", sub: "اختر الترتيب وسيتم الإغلاق تلقائياً" }
      };
      const meta = map[key] || { title: "تصفية", ico: "⚙", sub: "" };
      if (mfSheetTitle) mfSheetTitle.textContent = meta.title;
      if (mfSheetSub) mfSheetSub.textContent = meta.sub;
      if (mfSheetIcon) mfSheetIcon.textContent = meta.ico;

      syncSheetPosition();
      mfSheet.classList.add("is-open");
    }

    function closeSheet() {
      if (!mfSheet) return;
      mfSheet.classList.remove("is-open");
      mfDock?.querySelectorAll(".mf-item").forEach(b => b.classList.remove("is-active"));
      activeKey = null;
    }

    function commitFromSheet() {
      if (!activeKey) return;

      if (activeKey === "category") {
        const el = document.getElementById("mfCategory");
        if (el && filterCategory) filterCategory.value = el.value;
      }

      if (activeKey === "city") {
        const el = document.getElementById("mfCity");
        if (el && filterCity) filterCity.value = el.value;
      }

      if (activeKey === "condition") {
        const r = document.querySelector('input[name="mfCondition"]:checked');
        setRadioGroupValue("condition", r ? r.value : "");
      }

      if (activeKey === "price") {
        const minEl = document.getElementById("mfPriceMin");
        const maxEl = document.getElementById("mfPriceMax");
        if (filterMin) filterMin.value = minEl ? (minEl.value || "") : "";
        if (filterMax) filterMax.value = maxEl ? (maxEl.value || "") : "";
      }

      if (activeKey === "time") {
        const r = document.querySelector('input[name="mfTime"]:checked');
        setRadioGroupValue("time", r ? r.value : "");
      }

      if (activeKey === "sort") {
        const r = document.querySelector('input[name="mfSort"]:checked');
        setRadioGroupValue("sort", r ? (r.value || "latest") : "latest");
      }

      if (pageField) pageField.value = "1";
      applyFilters({ append: false });
    }

    function resetOnlyActiveKey() {
      if (!activeKey) return;

      if (activeKey === "category" && filterCategory) filterCategory.value = "";
      if (activeKey === "city" && filterCity) filterCity.value = "";
      if (activeKey === "condition") setRadioGroupValue("condition", "");
      if (activeKey === "price") { if (filterMin) filterMin.value = ""; if (filterMax) filterMax.value = ""; }
      if (activeKey === "time") setRadioGroupValue("time", "");
      if (activeKey === "sort") setRadioGroupValue("sort", "latest");

      if (pageField) pageField.value = "1";
      applyFilters({ append: false });
    }

    function initSheetControls(key) {
      if (key === "category") {
        const el = document.getElementById("mfCategory");
        if (el && filterCategory) el.value = filterCategory.value || "";
        el?.addEventListener("change", () => { commitFromSheet(); closeSheet(); });
        return;
      }

      if (key === "city") {
        const el = document.getElementById("mfCity");
        if (el && filterCity) el.value = filterCity.value || "";
        el?.addEventListener("change", () => { commitFromSheet(); closeSheet(); });
        return;
      }

      if (key === "condition") {
        document.querySelectorAll('input[name="mfCondition"]').forEach(r => {
          r.addEventListener("change", () => { commitFromSheet(); closeSheet(); });
        });
        return;
      }

      if (key === "time") {
        document.querySelectorAll('input[name="mfTime"]').forEach(r => {
          r.addEventListener("change", () => { commitFromSheet(); closeSheet(); });
        });
        return;
      }

      if (key === "sort") {
        document.querySelectorAll('input[name="mfSort"]').forEach(r => {
          r.addEventListener("change", () => { commitFromSheet(); closeSheet(); });
        });
        return;
      }

      // price uses Apply
    }

    mfDock?.querySelectorAll(".mf-item").forEach(btn => {
      btn.addEventListener("click", () => {
        if (!isMobile()) return;
        openSheet(btn.dataset.key);
      });
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
  });
})();
