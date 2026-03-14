// static/js/stores_list.js
(() => {
  "use strict";

  const filtersForm = document.getElementById("storesFiltersForm");
  const searchInput = document.getElementById("searchInput");
  const catLeft     = document.getElementById("catLeft");
  const catRight    = document.getElementById("catRight");
  const catScroll   = document.getElementById("categoryFilters");

  if (!filtersForm) return;

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

  // ── htmx:configRequest: inject q + page reset + update push-url ──────────

  document.body.addEventListener("htmx:configRequest", (e) => {
    const elt = e.detail.elt;
    if (!elt || !elt.classList || !elt.classList.contains("category-chip")) return;

    // always send the current search value alongside chip filters
    if (searchInput) {
      e.detail.parameters.q = searchInput.value;
    }

    // reset pagination when filter changes
    if (elt.dataset.resetPage === "1") {
      e.detail.parameters.page = "1";
      delete elt.dataset.resetPage;
    }

    // keep browser URL in sync with selected state
    const selected = getSelectedCategories();
    const params   = new URLSearchParams();
    if (searchInput && searchInput.value) params.set("q", searchInput.value);
    selected.forEach(id => params.append("categories", id));
    const qs = params.toString();
    elt.setAttribute("hx-push-url", qs ? `${window.location.pathname}?${qs}` : window.location.pathname);
  });

  document.body.addEventListener("htmx:afterSwap", () => syncChipsUI());

  // ── search button: trigger HTMX on the input ──────────────────────────────

  const searchForm = document.getElementById("storesSearchForm");
  if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      if (window.htmx && searchInput) window.htmx.trigger(searchInput, "search");
    });
  }

  // ── arrow scroll ──────────────────────────────────────────────────────────

  if (catLeft && catScroll) {
    catLeft.addEventListener("click", () => catScroll.scrollBy({ left: -240, behavior: "smooth" }));
  }
  if (catRight && catScroll) {
    catRight.addEventListener("click", () => catScroll.scrollBy({ left: 240, behavior: "smooth" }));
  }

  syncChipsUI();
})();
