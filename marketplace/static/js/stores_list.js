// static/js/stores_list.js
(() => {
  "use strict";

  const filtersForm = document.getElementById("storesFiltersForm");
  const searchInput = document.getElementById("searchInput");
  const catLeft     = document.getElementById("catLeft");
  const catRight    = document.getElementById("catRight");
  const catScroll   = document.getElementById("categoryFilters");

  if (!filtersForm) return;

  const STORES_URL = document.getElementById("storesSearchForm")
    ? document.getElementById("storesSearchForm").action   // e.g. /stores/
    : "/stores/";

  // ── helpers ──────────────────────────────────────────────────────────────

  function getSelectedCategories() {
    return Array.from(filtersForm.querySelectorAll('input[name="categories"]')).map(i => i.value);
  }

  function setSelectedCategories(selected) {
    filtersForm.querySelectorAll('input[name="categories"]').forEach(el => el.remove());
    selected.forEach(id => {
      const inp = document.createElement("input");
      inp.type  = "hidden";
      inp.name  = "categories";
      inp.value = id;
      filtersForm.appendChild(inp);
    });
  }

  function syncChipsUI() {
    const selected = getSelectedCategories();
    document.querySelectorAll(".category-chip").forEach(btn => {
      const id = btn.getAttribute("data-category-id") || "";
      if (!id) btn.classList.toggle("active", selected.length === 0);
      else     btn.classList.toggle("active", selected.includes(id));
    });
  }

  function buildStoresUrl(q, categories) {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    categories.forEach(id => params.append("categories", id));
    const qs = params.toString();
    return qs ? `${STORES_URL}?${qs}` : STORES_URL;
  }

  function toggleCategory(categoryId) {
    let selected = getSelectedCategories();
    if (!categoryId) {
      selected = [];
    } else if (selected.includes(categoryId)) {
      selected = selected.filter(x => x !== categoryId);
    } else {
      selected.push(categoryId);
    }
    setSelectedCategories(selected);
    syncChipsUI();
  }

  // ── chip clicks ───────────────────────────────────────────────────────────

  document.addEventListener("click", (e) => {
    const chip = e.target.closest(".category-chip");
    if (!chip) return;
    e.preventDefault();

    const categoryId = chip.getAttribute("data-category-id") || "";
    toggleCategory(categoryId);
    chip.dataset.resetPage = "1";

    if (window.htmx) window.htmx.trigger(chip, "filtersChanged");
  });

  // ── htmx:configRequest: inject q for chips; fix push-url for both ────────

  document.body.addEventListener("htmx:configRequest", (e) => {
    const elt = e.detail.elt;
    if (!elt) return;

    const isChip   = elt.classList && elt.classList.contains("category-chip");
    const isSearch = elt.id === "searchInput";

    if (isChip) {
      // pass current search query alongside the category filters
      if (searchInput) e.detail.parameters.q = searchInput.value;

      // reset pagination
      if (elt.dataset.resetPage === "1") {
        e.detail.parameters.page = "1";
        delete elt.dataset.resetPage;
      }

      // set correct push URL (shows /stores/?q=...&categories=...)
      const q        = (searchInput ? searchInput.value : "") || "";
      const selected = getSelectedCategories();
      elt.setAttribute("hx-push-url", buildStoresUrl(q, selected));
    }

    if (isSearch) {
      // fix push URL: replace /partial/ path with the main stores URL
      const q        = e.detail.parameters.q || "";
      const selected = getSelectedCategories();
      searchInput.setAttribute("hx-push-url", buildStoresUrl(q, selected));
    }
  });

  document.body.addEventListener("htmx:afterSwap", () => syncChipsUI());

  // ── search button: trigger HTMX on the input ─────────────────────────────

  const searchForm = document.getElementById("storesSearchForm");
  if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      if (window.htmx && searchInput) window.htmx.trigger(searchInput, "search");
    });
  }

  // ── arrow scroll ─────────────────────────────────────────────────────────

  if (catLeft && catScroll) {
    catLeft.addEventListener("click",  () => catScroll.scrollBy({ left: -240, behavior: "smooth" }));
  }
  if (catRight && catScroll) {
    catRight.addEventListener("click", () => catScroll.scrollBy({ left:  240, behavior: "smooth" }));
  }

  syncChipsUI();
})();
